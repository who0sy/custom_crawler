# -*- coding: utf-8 -*-
import json
import time

import pymongo
import pymysql
import redis
import logging
from scrapy.exceptions import DropItem
from twisted.enterprise import adbapi

from custom_crawler import settings

logger = logging.getLogger(__name__)


class CustomCrawlerPipeline(object):
    """ 简单数据清洗-添加必要字段 """
    def process_item(self, item, spider):
        # 抓取时间
        item['spider_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        item['process_status'] = 0
        item['upload_status'] = 0
        item['alter_status'] = 0
        return item


class MysqlTwistedPipeline(object):
    """ 异步存储到MySQL """
    def __init__(self, dbpool):
        self.dbpool = dbpool
        self.redis_client = redis.StrictRedis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
        )

    @classmethod
    def from_crawler(cls, crawler):
        dbparms = dict(
            host=crawler.settings.get('DB_HOST'),
            db=crawler.settings.get('DB_NAME'),
            user=crawler.settings.get('DB_USER'),
            passwd=crawler.settings.get('DB_PASSWORD'),
            charset=crawler.settings.get('DB_CHARSET'),
            cursorclass=pymysql.cursors.Cursor,
            use_unicode=True,
            connect_timeout=600,  # 分钟，默认十分钟不操作断开
        )
        dbpool = adbapi.ConnectionPool('pymysql', **dbparms)  # 连接
        return cls(dbpool)

    def process_item(self, item, spider):
        self.dbpool.runInteraction(self.do_insert, item)  # 调用twisted进行异步的插入操作

    def do_insert(self, cursor, item):
        table = item.get('collection')
        item.pop('collection')
        fields = ", ".join(list(item.keys()))
        sub_char = ", ".join(["%s"] * len(item))
        values = tuple(list(item.values()))
        sql = "insert into {}({}) values ({})".format(table, fields, sub_char)
        # sql = "insert into %s(%s) values (%s)" % (table, fields, sub_char)
        try:
            cursor.execute(sql, values)
            logger.debug('插入成功')
        except Exception as e:
            if "Duplicate" in repr(e):
                logger.info("数据重复--删除")
                DropItem(item)
            else:
                logger.info('插入失败--{}'.format(repr(e)))
                self.redis_client.sadd("baidu_xin:error_items", json.dumps(dict(item), ensure_ascii=False))


class MongodbIndexPipeline(object):
    """ 存储到mongodb数据库并且创建索引 """
    def __init__(self, mongo_uri, mongo_db):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[mongo_db]

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATA_BASE')
        )

    def process_item(self, item, spider):
        collection_name = item.get('collection')
        collection = self.db[collection_name]
        collection.create_index([('ent_name', 1), ('spider_time', -1)])  # 1表示升序，-1降序
        try:
            item.pop('collection')
            collection.insert(dict(item))
        except:
            from scrapy import log
            log.msg(message="dup key: {}".format(item["url"]), level=log.INFO)
        return item