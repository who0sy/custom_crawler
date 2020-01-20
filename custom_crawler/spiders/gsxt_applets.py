# -*- coding: utf-8 -*-
import scrapy

from custom_crawler import config


class GsxtAppletsSpider(scrapy.Spider):
    name = 'gsxt_applets'
    allowed_domains = ['app.gsxt.gov.cn']
    start_urls = ["https://app.gsxt.gov.cn/gsxt/affiche-query-info-punish-app.html?"
                  "caseId=2c9781176f23dcfc016f7914d43a661d&sourceType=W"]

    custom_settings = config.xzcf_custom_settings

    def parse(self, response):
        print(response.text)
