# -*- coding: utf-8 -*-
from scrapy import cmdline


# 国家企业信用信息公示系统-部分维度数据抓取
# cmdline.execute('scrapy crawl gsxt_applets'.split())
# 百度企业信用-部分维度数据抓取
cmdline.execute('scrapy crawl baidu_xin'.split())