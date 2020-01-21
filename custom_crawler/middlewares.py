# -*- coding: utf-8 -*-
import time

import redis
import logging
from fake_useragent import UserAgent
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.python import global_object_name
from scrapy.utils.response import response_status_message

from custom_crawler import settings

logger = logging.getLogger(__name__)


class RandomUserAgentMiddleware(object):
    """ 利用fake_useragent生成随机请求头 """
    def __init__(self, ua_type):
        self.ua_type = ua_type
        self.ua = UserAgent()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            ua_type=crawler.settings.get('RANDOM_UA_TYPE', 'random')
        )

    def process_request(self, request, spider):
        def get_user_agent():
            return getattr(self.ua, self.ua_type)
        request.headers.setdefault(b'User-Agent', get_user_agent())


class RandomProxyMiddlerware(object):
    """ 拨号代理池 """
    def __init__(self, proxy_redis_host, proxy_redis_port, proxy_redis_password, proxy_redis_db):
        self.redis_proxy = redis.StrictRedis(host=proxy_redis_host, port=proxy_redis_port, password=proxy_redis_password, db=proxy_redis_db)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            proxy_redis_host=crawler.settings.get('REDIS_PROXIES_HOST'),
            proxy_redis_port=crawler.settings.get('REDIS_PROXIES_PORT'),
            proxy_redis_password=crawler.settings.get('REDIS_PROXIES_PASSWORD'),
            proxy_redis_db=crawler.settings.get('REDIS_PROXIES_DB'),
        )

    def process_request(self, request, spider):
        ip_port = self.redis_proxy.srandmember('proxies')
        if ip_port:
            proxies = {
                'http': 'http://{}'.format(ip_port.decode('utf-8')),
                'https': 'https://{}'.format(ip_port.decode('utf-8')),
            }
            if request.url.startswith('http://'):
                request.meta['proxy'] = proxies.get("http")
                logger.debug('http链接,ip:{}'.format(request.meta.get('proxy')))
            else:
                request.meta['proxy'] = proxies.get('https')
                logger.debug('https链接,ip:{}'.format(request.meta.get('proxy')))
        else:
            logger.info('代理池枯竭--IP数量不足--等待重新拨号')
            time.sleep(10)


class LocalRetryMiddlerware(RetryMiddleware):
    """  百度企业信用--重新定义重试中间件--搭配拨号代理  """
    redis_client = redis.StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
    )
    redis_proxy = redis.StrictRedis(
        host=settings.REDIS_PROXIES_HOST,
        port=settings.REDIS_PROXIES_PORT,
        password=settings.REDIS_PROXIES_PASSWORD,
        db=settings.REDIS_PROXIES_DB,
    )

    def delete_proxy(self, proxy):
        """ 删除代理，公司拨号代理是set """
        self.redis_proxy.srem("proxies", proxy)

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        if response.status in [302, 403]:
            """  单独处理封IP的情况，删除代理重新请求  """
            proxy_spider = request.meta.get('proxy')
            proxy_redis = proxy_spider.split("//")[1]
            time.sleep(1)
            self.delete_proxy(proxy_redis)
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response

        return response

    def _retry(self, request, reason, spider):
        retries = request.meta.get('retry_times', 0) + 1

        retry_times = self.max_retry_times

        if 'max_retry_times' in request.meta:
            retry_times = request.meta['max_retry_times']

        stats = spider.crawler.stats
        if retries <= retry_times:
            logger.debug("Retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                         extra={'spider': spider})
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.dont_filter = True
            retryreq.priority = request.priority + self.priority_adjust

            if isinstance(reason, Exception):
                reason = global_object_name(reason.__class__)

            stats.inc_value('retry/count')
            stats.inc_value('retry/reason_count/%s' % reason)
            return retryreq
        else:
            # 全部重试错误，要保存错误的url和参数 - start
            error_request = spider.name + ":error_urls"
            self.redis_client.sadd(error_request, request.url)
            # 全部重试错误，要保存错误的url和参数 - en
            stats.inc_value('retry/max_reached')
            logger.debug("Gave up retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                         extra={'spider': spider})

    def process_exception(self, request, exception, spider):
        if "ConnectionRefusedError" in repr(exception):
            proxy_spider = request.meta.get('proxy')
            proxy_redis = proxy_spider.split("//")[1]
            self.delete_proxy(proxy_redis)
            logger.info('目标计算机积极拒绝，删除代理-{}-请求url-{}开始重新请求'.format(proxy_redis, request.url))
            return request

        elif "TCPTimedOutError" in repr(exception):
            logger.debug('连接方在一段时间后没有正确答复或连接的主机没有反应')
            return request

        elif "ConnectionError" in repr(exception):
            logger.debug("连接出错，无网络")
            return request

        elif "TimeoutError" in repr(exception):
            logger.debug('请求超时-请求url-{}-重新请求'.format(request.url))
            return request

        elif "ConnectionResetError" in repr(exception):
            logger.debug('远程主机强迫关闭了一个现有的连接')
            return request

        elif "ResponseNeverReceived" in repr(exception):
            logger.debug('可能是请求头无法使用，没有正确的响应内容')
            return request

        else:
            logger.error('出现其他异常:{}--等待处理'.format(repr(exception)))


class GsxcxRetryMiddlerware(RetryMiddleware):
    """  国家企业公示系统--重试中间件 """
    redis_client = redis.StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
    )
    redis_proxy = redis.StrictRedis(
        host=settings.REDIS_PROXIES_HOST,
        port=settings.REDIS_PROXIES_PORT,
        password=settings.REDIS_PROXIES_PASSWORD,
        db=settings.REDIS_PROXIES_DB,
    )

    def delete_proxy(self, proxy):
        """ 删除代理，公司拨号代理是set """
        self.redis_proxy.srem("proxies", proxy)

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        if response.status in [403, 569, 565]:
            """  单独处理封IP的情况，删除代理重新请求  """
            proxy_spider = request.meta.get('proxy')
            proxy_redis = proxy_spider.split("//")[1]
            time.sleep(1)
            self.delete_proxy(proxy_redis)
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response

        return response

    def _retry(self, request, reason, spider):
        retries = request.meta.get('retry_times', 0) + 1

        retry_times = self.max_retry_times

        if 'max_retry_times' in request.meta:
            retry_times = request.meta['max_retry_times']

        stats = spider.crawler.stats
        if retries <= retry_times:
            logger.debug("Retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                         extra={'spider': spider})
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.dont_filter = True
            retryreq.priority = request.priority + self.priority_adjust

            if isinstance(reason, Exception):
                reason = global_object_name(reason.__class__)

            stats.inc_value('retry/count')
            stats.inc_value('retry/reason_count/%s' % reason)
            return retryreq
        else:
            # 全部重试错误，要保存错误的url和参数 - start
            error_request = spider.name + ":error_urls"
            self.redis_client.sadd(error_request, request.url)
            # 全部重试错误，要保存错误的url和参数 - en
            stats.inc_value('retry/max_reached')
            logger.debug("Gave up retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                         extra={'spider': spider})

    def process_exception(self, request, exception, spider):
        if "ConnectionRefusedError" in repr(exception):
            proxy_spider = request.meta.get('proxy')
            proxy_redis = proxy_spider.split("//")[1]
            self.delete_proxy(proxy_redis)
            logger.info('目标计算机积极拒绝，删除代理-{}-请求url-{}开始重新请求'.format(proxy_redis, request.url))
            return request

        elif "TCPTimedOutError" in repr(exception):
            logger.debug('连接方在一段时间后没有正确答复或连接的主机没有反应')
            return request

        elif "ConnectionError" in repr(exception):
            logger.debug("连接出错，无网络")
            return request

        elif "TimeoutError" in repr(exception):
            logger.debug('请求超时-请求url-{}-重新请求'.format(request.url))
            return request

        elif "ConnectionResetError" in repr(exception):
            logger.debug('远程主机强迫关闭了一个现有的连接')
            return request

        elif "ResponseNeverReceived" in repr(exception):
            logger.debug('可能是请求头无法使用，没有正确的响应内容')
            return request

        else:
            logger.error('出现其他异常:{}--等待处理'.format(repr(exception)))