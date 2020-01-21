# -*- coding: utf-8 -*-
import json
from json import JSONDecodeError

import jsonpath
import scrapy
import logging

from custom_crawler import config

logger = logging.getLogger(__name__)


class GsxtAppletsSpider(scrapy.Spider):
    name = 'gsxt_search_applets'
    allowed_domains = ['app.gsxt.gov.cn']
    start_urls = ['https://app.gsxt.gov.cn/gsxt/corp-query-entprise-info-punishmentdetail-D91EFFF2D70336001A2F222E340110480004A604A6044C48EA48EA48EA48EA484CE24061FE5C585C7DDF7DDF8D9B-1558624663369.html?nodeNum=430000&entType=1&sourceType=W']

    custom_settings = config.search_custom_settings

    def parse(self, response):
        """ 请求搜索接口 """
        search_url = 'https://app.gsxt.gov.cn/gsxt/corp-query-app-search-1.html'
        keyword = '小米'
        # keyword = '深圳市伟雄奥展运输有限公司'
        payload = 'conditions=%7B%22excep_tab%22%3A%220%22%2C%22ill_tab%22%3A%220%22%2C%22area%22%3A%220%22%2C%22cStatus%22%3A%220%22%2C%22xzxk%22%3A%220%22%2C%22xzcf%22%3A%220%22%2C%22dydj%22%3A%220%22%7D&searchword={}&sourceType=W'.format(keyword)
        yield scrapy.Request(
            url=search_url,
            body=payload,
            method='POST',
            callback=self.parse_index,
            meta={'keyword': keyword},
        )

    def parse_index(self, response):
        """ 解析搜索列表 """
        keyword = response.meta.get('keyword')
        # 列表解析
        try:
            results = json.loads(response.text)
            # 判断搜素结果是否有数据
            result_list = results.get('data')
            if result_list:
                result_list = result_list.get('result').get('data')
            else:
                result_list = {}
            if not result_list:
                return
            # 列表解析--请求详情
            for data in result_list:
                # entName = data.get("entName").replace("<font color=red>", "").replace("</font>", "").replace("&nbsp;", "").strip()
                entType = data.get('entType')  # 必要参数
                nodeNum = data.get('nodeNum')  # 必要参数
                pripid = data.get('pripid')  # 公司唯一参数
                url = 'https://app.gsxt.gov.cn/gsxt/corp-query-entprise-info-primaryinfoapp-entbaseInfo-{}.html?nodeNum={}&entType={}&sourceType=W'.format(pripid, nodeNum, entType)
                yield scrapy.Request(url=url, callback=self.parse_business_detail, priority=5)

            # 列表翻页请求
            is_first = response.meta.get('is_first', True)
            totalPage = jsonpath.jsonpath(results, expr=r'$..totalPage')
            if is_first:
                if int(totalPage[0]) > 1:
                    for page in range(2, int(totalPage[0]) + 1):
                        url = 'https://app.gsxt.gov.cn/gsxt/corp-query-app-search-{}.html'.format(page)
                        payload = 'conditions=%7B%22excep_tab%22%3A%220%22%2C%22ill_tab%22%3A%220%22%2C%22area%22%3A%220%22%2C%22cStatus%22%3A%220%22%2C%22xzxk%22%3A%220%22%2C%22xzcf%22%3A%220%22%2C%22dydj%22%3A%220%22%7D&searchword={}&sourceType=W'.format(keyword)
                        yield scrapy.Request(
                            url=url,
                            body=payload,
                            method='POST',
                            meta={'keyword': keyword, 'is_first': False},
                            callback=self.parse_index,
                            priority=3,
                        )
        except JSONDecodeError:
            # logger.info(f'搜素结果不是json数据--{response.text}--IP不行')
            logger.info(f'搜素结果不是json数据----IP不行')

    def parse_business_detail(self, response):
        """ 解析工商信息详情 """
        # 解析工商数据
        try:
            results = json.loads(response.text)
            result = results.get('result')
            if not result:
                return
            entName = result.get('entName', '')  # 企业名称
            uniscId = result.get('uniscId', '')  # 统一社会信用代码
            entType_CN = result.get('entType_CN', '')  # 类型
            name = result.get('name', '')  # 法定代表人
            estDate = result.get('estDate', '')  # 成立日期
            opFrom = result.get('opFrom', '')  # 营业期限自
            opTo = result.get('opTo', '')  # 营业期限至
            regOrg_CN = result.get('regOrg_CN', '')  # 登记机关
            apprDate = result.get('apprDate', '')  # 核准日期
            regState_CN = result.get('regState_CN', '')  # 登记状态
            dom = result.get('dom', '')  # 住所
            opScope = result.get('opScope', '')  # 经营范围
            # regCap = result.get('regCap')  # 注册资本

            regCaption = results.get('regCaption', '')  # 注册资本
            regCapCurCN = results.get('regCapCurCN', '')  # 注册资本单位
            regCap = results.get('regCap', '')  # 注册资本大写
            first_item = dict(
                ent_name=entName, unified_code=uniscId, ent_type=entType_CN, legal_person=name,
                estiblish_time=estDate, operate_from=opFrom, operate_to=opTo, authority=regOrg_CN,
                approve_date=apprDate, open_status=regState_CN, reg_addr=dom, scope=opScope,
                reg_capital=regCaption, reg_capital_unit=regCapCurCN, reg_cap=regCap,
                url=response.url, contents=json.dumps(result, ensure_ascii=False),
                collection='gsxt_business_information',
            )
            # print(first_item)
            yield first_item
            pripId = result.get('pripId')
            nodeNum = result.get('nodeNum')
            entType = result.get('entType')
            meta_data = {'ent_name': entName, 'unified_code': uniscId, 'legal_person': name, 'reg_addr': dom}
            # 行政处罚
            xzcf_url = 'https://app.gsxt.gov.cn/gsxt/corp-query-entprise-info-punishmentdetail-{}.html?nodeNum={}&entType={}&sourceType=W'.format(pripId, nodeNum, entType)
            print(f'行政处罚url:{xzcf_url}')
            yield scrapy.Request(url=xzcf_url, callback=self.parse_punishment, meta={'base_item': meta_data}, priority=7)
            # 经营异常
            jyyc_url = 'https://app.gsxt.gov.cn/gsxt/corp-query-entprise-info-entBusExcep-{}.html?nodeNum={}&entType={}&sourceType=W'.format(pripId, nodeNum, entType)
            yield scrapy.Request(url=jyyc_url, callback=self.parse_abnormal, meta={'base_item': meta_data}, priority=7)
            # 严重违法失信黑名单
            yzwf_url = 'https://app.gsxt.gov.cn/gsxt/corp-query-entprise-info-illInfo-{}.html?nodeNum={}&entType={}&sourceType=W'.format(pripId, nodeNum, entType)
            # yield scrapy.Request(url=yzwf_url, callback=self.parse_serious_violation, meta={'base_item': meta_data}, priority=7)
        except JSONDecodeError:
            # logger.info(f'工商详情请求出错--响应结果不是json--{response.text}')
            logger.info(f'工商详情请求出错--响应结果不是json--IP坏了')

    def parse_punishment(self, response):
        """ 解析行政处罚 """
        base_item = response.meta.get('base_item')
        # 解析数据
        results = json.loads(response.text)
        recordsTotal = results.get('recordsTotal')
        if int(recordsTotal) >= 1:
            data = results.get('data')
            if not data:
                return
            # for item in data:
            #     penDecNo = item.get('penDecNo')  # 决定书文号
            #     illegActType = item.get('illegActType')  # 决定书文号
            #     penDecNo = item.get('penDecNo')  # 决定书文号
            #     penDecNo = item.get('penDecNo')  # 决定书文号

    def parse_abnormal(self, response):
        """ 解析经营异常 """
        base_item = response.meta.get('base_item')
        # 解析数据
        results = json.loads(response.text)
        recordsTotal = results.get('recordsTotal')
        if int(recordsTotal) >= 1:
            data = results.get('data')
            if not data:
                return
            for item in data:
                speCause_CN = item.get('speCause_CN')  # 列入经营异常名录原因
                abntime = item.get('abntime')  # 列入日期
                decOrg_CN = item.get('decOrg_CN')  # 作出决定机关(列入)
                remExcpRes_CN = item.get('remExcpRes_CN')  # 移出经营异常名录原因
                remDate = item.get('remDate')  # 移出日期
                reDecOrg_CN = item.get('reDecOrg_CN')  # 作出决定机关(移出)
                abnormal_item = dict(
                    enter_reason=speCause_CN, enter_date=abntime, authority=decOrg_CN,
                    leave_reason=remExcpRes_CN, leave_date=remDate, leave_authority=reDecOrg_CN,
                    url=response.url, collection='gsxt_abnormal_information',
                )
                item = {**base_item, **abnormal_item}
                # print(item)
                yield item

            # 翻页请求
            is_first = response.meta.get('is_first', True)
            totalPage = jsonpath.jsonpath(results, expr=r'$..totalPage')
            if is_first:
                if int(totalPage[0]) > 1:
                    for page in range(1, int(totalPage[0]) + 1):
                        url = response.url + '&start={}'.format(5*page)
        else:
            logger.debug('无经营异常数据')

    def parse_serious_violation(self, response):
        """ 解析严重违法失信黑名单 """