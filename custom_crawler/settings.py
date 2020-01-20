# -*- coding: utf-8 -*-


BOT_NAME = 'custom_crawler'

SPIDER_MODULES = ['custom_crawler.spiders']
NEWSPIDER_MODULE = 'custom_crawler.spiders'

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
scrapy 基本配置
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
ROBOTSTXT_OBEY = False
LOG_LEVEL = 'INFO'

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
数据存储 相关配置
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
# 存储到mongodb
MONGO_URI = '127.0.0.1'
MONGO_DATA_BASE = 'custom_crawler'
# 存储到MySQL
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = '123456'
DB_NAME = 'custom_crawler'
DB_CHARSET = 'utf8'

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
redis 相关配置
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
# redis 基础配置
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PASSWORD = ""
REDIS_DB = 4
REDIS_PARAMS = {
    "password": "",
    "db": 4,
}
# redis 代理池配置
REDIS_PROXIES_HOST = '117.78.35.12'
REDIS_PROXIES_PORT = 6379
REDIS_PROXIES_PASSWORD = ''
REDIS_PROXIES_DB = 15