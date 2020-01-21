# -*- coding: utf-8 -*-
import scrapy

from custom_crawler.config import xzcf_custom_settings


class GsxtXzcfAppletsSpider(scrapy.Spider):
    name = 'gsxt_xzcf_applets'
    allowed_domains = ['app.gsxt.gov.cn']
    custom_settings = xzcf_custom_settings

    def start_requests(self):
        search_url = 'https://app.gsxt.gov.cn/gsxt/corp-query-app-search-1.html'
        keyword = '小米'
        payload = 'conditions=%7B%22excep_tab%22%3A%220%22%2C%22ill_tab%22%3A%220%22%2C%22area%22%3A%220%22%2C%22cStatus%22%3A%220%22%2C%22xzxk%22%3A%220%22%2C%22xzcf%22%3A%220%22%2C%22dydj%22%3A%220%22%7D&searchword={}&sourceType=W'.format(keyword)
        yield scrapy.Request(
            url=search_url,
            body=payload,
            method='POST',
            callback=self.parse_index,
        )

    def parse_index(self, response):
        """ 解析搜索列表 """
        print(response.text)

    def parse(self, response):
        pass
