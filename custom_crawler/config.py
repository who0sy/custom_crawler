# -*- coding: utf-8 -*-


# 百度企业信用-通用配置
baidu_custom_settings = {
    "REDIRECT_ENABLED": False,  # 禁止重定向
    "RETRY_ENABLED": True,  # 自定义重试
    "RETRY_TIMES": 19,
    "DOWNLOAD_TIMEOUT": 25,
    # "COOKIES_ENABLED": False,  # 设置False，在headers里面传递cookie

    "ITEM_PIPELINES": {
        "custom_crawler.pipelines.CustomCrawlerPipeline": 300,
        "custom_crawler.pipelines.MysqlTwistedPipeline": 340,
        # "custom_crawler.pipelines.MongodbIndexPipeline": 380,
    },

    "DOWNLOADER_MIDDLEWARES": {
        "custom_crawler.middlewares.RandomUserAgentMiddleware": 400,
        'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,  # 禁用默认的代理
        "custom_crawler.middlewares.RandomProxyMiddlerware": 410,
        "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
        "custom_crawler.middlewares.LocalRetryMiddlerware": 420,
    },

    "SCHEDULER": "scrapy_redis.scheduler.Scheduler",
    "DUPEFILTER_CLASS": "scrapy_redis.dupefilter.RFPDupeFilter",
    "SCHEDULER_QUEUE_CLASS": "scrapy_redis.queue.SpiderPriorityQueue",
    "SCHEDULER_PERSIST": True,
}


# 国家企业信用信息公示系统-搜索接口
search_custom_settings = {
    "COOKIES_ENABLED": False,  # 禁用cookie
    # "CONCURRENT_REQUESTS": 8,   # 并发设置
    # "DOWNLOAD_DELAY": 0.3,  # 下载延迟
    "RETRY_ENABLED": True,
    "RETRY_TIMES": '9',
    "DOWNLOAD_TIMEOUT": '20',

    "ITEM_PIPELINES": {
        "custom_crawler.pipelines.CustomCrawlerPipeline": 300,
        "custom_crawler.pipelines.MysqlTwistedPipeline": 340,
    },

    "DOWNLOADER_MIDDLEWARES": {
        "custom_crawler.middlewares.RandomUserAgentMiddleware": 400,
        "custom_crawler.middlewares.RandomProxyMiddlerware": 410,
        "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
        "custom_crawler.middlewares.GsxcxRetryMiddlerware": 420,
    },

    "DEFAULT_REQUEST_HEADERS": {
        "charset": "utf-8",
        "accept": "application/json",
        "referer": "https://servicewechat.com/wx5b0ed3b8c0499950/7/page-frame.html",
        "content-type": "application/x-www-form-urlencoded",
        "Host": "app.gsxt.gov.cn"
    }
}


# 国家企业信用信息公示系统-行政处罚接口
xzcf_custom_settings = {
    "COOKIES_ENABLED": False,  # 禁用cookie
    # "CONCURRENT_REQUESTS": 8,   # 并发设置
    # "DOWNLOAD_DELAY": 0.3,  # 下载延迟
    "RETRY_ENABLED": True,
    "RETRY_TIMES": '9',
    "DOWNLOAD_TIMEOUT": '25',

    # "ITEM_PIPELINES": {
    #     "custom_crawler.pipelines.GsxtXcxByDayPipeline": 300
    # },

    "DOWNLOADER_MIDDLEWARES": {
        "custom_crawler.middlewares.RandomUserAgentMiddleware": 400,
        "custom_crawler.middlewares.RandomProxyMiddlerware": 410,
        # "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
        # "custom_crawler.middlewares.LocalRetryDownloaderMiddleware": 420,
    },

    "DEFAULT_REQUEST_HEADERS": {
        "charset": "utf-8",
        "accept": "application/json",
        "referer": "https://servicewechat.com/wx5b0ed3b8c0499950/7/page-frame.html",
        "content-type": "application/x-www-form-urlencoded",
        "Host": "app.gsxt.gov.cn"
    }
}