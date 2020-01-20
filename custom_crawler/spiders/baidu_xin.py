# -*- coding: utf-8 -*-
import json
import re
from functools import reduce
from urllib.parse import quote

import jsonpath
import redis
import scrapy
import logging

from custom_crawler import config, settings
from custom_crawler.utils.redis_bloomfilter import BloomFilter

logger = logging.getLogger(__name__)


class BaiduXinSpider(scrapy.Spider):
    name = 'baidu_xin'
    allowed_domains = ['xin.baidu.com']

    custom_settings = config.baidu_custom_settings
    province_list = ['北京', '山东', '江苏', '江西', '河北', '湖北', '山西', '新疆', '安徽', '辽宁', '河南', '西藏', '陕西', '广东', '云南', '吉林',
                     '四川', '黑龙江', '天津', '宁夏', '贵州', '内蒙', '广西', '福建', '浙江', '湖南', '海南', '上海', '重庆', '甘肃', '青海']
    # redis 搜索关键词
    redis_keyword = redis.StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB
    )
    reids_name = name + ':keywords'

    # 布隆过滤器-用来过滤关键词(该关键词没有搜索结果，可以抛弃)
    bloomfilter_client = BloomFilter(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
        blockNum=1,
        key=name + ":bloomfilter"
    )

    base_item = {
        'xxly': '百度企业信用-信息查询系统-数据补充'
    }

    def start_requests(self):
        """ 关键词搜索入口 """
        # keyword = '深圳市明星康桥投资有限公司'
        while True:
            keyword = self.redis_keyword.rpop(self.reids_name)
            if not keyword:
                break
            keyword = keyword.decode()
            url = 'https://xin.baidu.com/s/l?q={}&t=0&p=1&s=10&o=0&f=undefined&fl=1&castk=LTE%3d'.format(keyword)
            yield scrapy.Request(
                url=url,
                meta={'keyword': keyword},
            )

    def parse(self, response):
        """ 解析搜索列表页 """
        # 基础信息
        keyword = response.meta.get('keyword')
        base_url = 'https://xin.baidu.com/s/l?q={}&t=0&p={}&s=10&o=0&f={}&fl=1&castk=LTE%3d'
        results = json.loads(response.text)

        # 列表页解析--请求详情页
        resultList = results.get('data').get('resultList')
        if not resultList:
            return
        for result in resultList:
            pid = result.get('pid')  # 详情页参数
            detail_url = "https://xin.baidu.com/detail/basicAjax?pid={}&fl=1&castk=LTE%3D".format(pid)
            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_details,
                meta={'pid': pid},
                priority=3,
            )

        # 添加搜索关键词
        msg = results.get('msg', '')
        if msg and '+' not in msg and '搜索词过于宽泛' in msg:
            for province in self.province_list:
                new_keyword = province + '+' + keyword
                url = base_url.format(new_keyword, 1, 'undefined')
                yield scrapy.Request(
                    url=url,
                    meta={'keyword': new_keyword},
                    priority=1,
                )

        # 翻页请求--最大翻页只能是100页
        filter_condition = response.meta.get('filter_condition', {})  # 用来添加过滤条件使用

        totalNumFound = jsonpath.jsonpath(results, expr='$..data.totalNumFound')  # 搜索词总结果数
        total_count = totalNumFound[0] if totalNumFound else 0
        if total_count <= 0:
            # 把搜索词添加到bloomfilter过滤掉
            if self.bloomfilter_client.is_exist(keyword):
                logger.info(f"{keyword}--- 被过滤了")
            else:
                logger.info(f"该搜索词没有搜索结果--{keyword}--添加到布隆过滤器")
                self.bloomfilter_client.add(keyword)
            return
        else:
            # 翻页页码总数--如果总页数不大于100直接翻页完成--大于100继续添加条件
            totalPageNum = results.get('data').get('totalPageNum')
            if totalPageNum:
                for page in range(2, int(totalPageNum) + 1):
                    if filter_condition:
                        url = base_url.format(keyword, page, quote(json.dumps(filter_condition)))
                    else:
                        url = base_url.format(keyword, page, 'undefined')

                    yield scrapy.Request(
                        url=url,
                        meta={'keyword': keyword},
                        priority=2,
                    )
            # 添加搜索条件
            if total_count > 100:
                # logger.debug(f'信息总数超过100条--查询关键词:{keyword}')
                filter_dict = results.get('data').get('facets')
                if filter_dict:
                    for key, value in filter_dict.items():
                        filter_value_list = value.get('values')
                        for filter_value_dict in filter_value_list:
                            filter_condition[key] = filter_value_dict.get("value")
                            url = base_url.format(keyword, 1, quote(json.dumps(filter_condition)))
                            meta_data = {'keyword': keyword, 'filter_condition': filter_condition}
                            yield scrapy.Request(
                                url=url,
                                meta=meta_data,
                            )
                        break

    def parse_details(self, response):
        """ 解析搜索详情页 """
        meta = response.meta
        pid = meta.get('pid')
        # 解析基本工商信息
        results = json.loads(response.text)
        all_data = results.get('data')
        # 携带基本信息
        base_info = {}
        if all_data:
            entName = all_data.get('entName', '').replace("-", "")  # 企业名称
            regCapital = all_data.get('regCapital', '').replace("-", "")  # 注册资本
            realCapital = all_data.get('realCapital', '').replace("-", "")  # 实缴资本
            legalPerson = all_data.get('legalPerson', '').replace("-", "")  # 法定代表人
            openStatus = all_data.get('openStatus', '').replace("-", "")  # 经营状态
            prevEntName = all_data.get('prevEntName', '').replace("-", "")  # 曾用名
            industry = all_data.get("industry", "").replace("-", "")  # 所属行业
            unifiedCode = all_data.get("unifiedCode", "").replace("-", "")  # 统一社会信用代码
            taxNo = all_data.get("taxNo", "").replace("-", "")  # 纳税人识别号
            regNo = all_data.get("regNo", "").replace("-", "")  # 注册号(不是很确定是啥)
            licenseNumber = all_data.get("licenseNumber", "").replace("-", "")  # 工商注册号
            orgNo = all_data.get("orgNo", "").replace("-", "")  # 组织机构代码
            authority = all_data.get("authority", "").replace("-", "")  # 登记机关
            startDate = all_data.get("startDate", "")  # 成立日期
            entType = all_data.get("entType", "").replace("-", "")    # 企业类型
            openTime = all_data.get("openTime", "")    # 营业期限
            district = all_data.get("district", "").replace("-", "")  # 行政区划
            annualDate = all_data.get("annualDate", "").replace("-", "")  # 审核/年检日期
            scope = all_data.get("scope", "").replace("-", "")  # 经营范围
            regAddr = all_data.get("regAddr", "").replace("-", "")  # 注册地址

            oldEntName = all_data.get('oldEntName', '').replace("-", "")  # 旧名称
            email = all_data.get("email", "").replace("-", "")  # 邮箱
            telephone = all_data.get("telephone", "").replace("-", "")  # 电话
            description = all_data.get("describe", "").replace("-", "")  # 公司简介
            # website = all_data.get('website', '')  # 网站地址
            # basic_anchor = all_data.get('basic_anchor')  # 对应基本信息模块下子类别的数目

            business_item = dict(
                ent_name=entName, reg_capital=regCapital, real_capital=realCapital, legal_person=legalPerson,
                open_status=openStatus, prev_ent_name=prevEntName, industry=industry, unified_code=unifiedCode,
                tax_number=taxNo, reg_number=regNo, license_number=licenseNumber, org_number=orgNo,
                authority=authority, estiblish_time=startDate, ent_type=entType, open_time=openTime,
                district=district, annual_date=annualDate, scope=scope, reg_addr=regAddr, email=email,
                telephone=telephone, description=description, old_ent_name=oldEntName, url=response.url,
                contents=json.dumps(all_data, ensure_ascii=False), collection='business_information',
            )
            base_item = {**business_item, **self.base_item}
            # print(f'基本工商:{base_item}')
            yield base_item

            # 解析股东信息
            share_info = {}
            shares_list = all_data.get('shares')  # 股东
            if shares_list:
                for share in shares_list:
                    share_item = {
                        'ent_name': entName,  # 企业名称
                        'gd_name': share.get('name'),  # 股东姓名
                        'gd_type': share.get('type'),  # 类型
                    }
                    share_info[share.get("name", "")] = share_item
            # 请求股东信息页
            gd_url = "https://xin.baidu.com/detail/sharesAjax?pid={}&p=1&fl=1&castk=LTE%3D".format(pid)
            yield scrapy.Request(url=gd_url, callback=self.parse_shares, meta={'share_info': share_info}, priority=3)
            # 变更信息

            # print(f'详情url:{response.url}--公司名:{entName}')
            base_info = dict(ent_name=entName, legal_person=legalPerson, open_status=openStatus, unified_code=unifiedCode, license_number=licenseNumber, org_number=orgNo, reg_addr=regAddr)
        else:
            logger.info(f'获取基本工商信息失败--{results}')

        # 请求行政处罚-经营异常-裁判文书信息
        meta['base_info'] = base_info
        # 裁判文书
        cpws_url = "https://xin.baidu.com/detail/lawWenshuAjax?pid={}&p=1&&fl=1&castk=LTE%3D".format(pid)
        # print(f'裁判文书:{cpws_url}')
        yield scrapy.Request(url=cpws_url, callback=self.parse_wenshu_list, meta=meta, priority=7)
        # 失信被执行人
        sx_url = "https://xin.baidu.com/detail/discreditAjax?pid={}&p=1&fl=1&castk=LTE%3D".format(pid)
        # print(f'失信被执行人:{sx_url}')
        yield scrapy.Request(url=sx_url, callback=self.parse_discredit, meta=meta, priority=7)
        # 经营异常url
        jyyc_url = "https://xin.baidu.com/detail/abnormalAjax?pid={}&p=1&fl=1&castk=LTE%3D".format(pid)
        # print(f'经营异常:{jyyc_url}')
        yield scrapy.Request(url=jyyc_url, callback=self.parse_abnormal, meta=meta, priority=7)
        # 行政处罚url
        xzcf_url = "https://xin.baidu.com/detail/penaltiesAjax?pid={}&p=1&fl=1&castk=LTE%3D".format(pid)
        # print(f'行政处罚:{xzcf_url}')
        yield scrapy.Request(url=xzcf_url, callback=self.parse_penalties, meta=meta, priority=7)
        # 知识产权出质
        # zscq_url = "https://xin.baidu.com/detail/KnowledgePledgeAjax?pid={}&p=1&fl=1&castk=LTE%3D".format(pid)
        # print(f'知识产权出质:{zscq_url}')
        # yield scrapy.Request(url=zscq_url, callback=self.parse_knowledge, meta=meta, priority=7)
        # 股权冻结
        gqdj_url = "https://xin.baidu.com/Stockfreeze/stockFreezeAjax?pid={}&p=1&fl=1&castk=LTE%3D".format(pid)
        # print(f'股权出质:{gqdj_url}')
        yield scrapy.Request(url=gqdj_url, callback=self.parse_stock_freeze, meta=meta, priority=7)
        # 严重违法
        yzwf_url = "https://xin.baidu.com/detail/illegalAjax?pid={}&p=1&fl=1&castk=LTE%3D".format(pid)
        # print(f'严重违法:{yzwf_url}')
        yield scrapy.Request(url=yzwf_url, callback=self.parse_illegal, meta=meta, priority=7)

    def parse_shares(self, response):
        """ 解析股东信息 """
        share_info = response.meta.get('share_info', {})
        # 解析股东详情信息
        results = json.loads(response.text)
        gd_list = results.get('data').get('list')
        if gd_list:
            for data in gd_list:
                gd_name = data.get('name', '')
                gd_item = {
                    "gd_name": gd_name,  # 股东姓名
                    "sub_rate": data.get("subRate", "").replace("-", ""),  # 持股比例
                    "sub_money": data.get("subMoney", "").replace("-", ""),  # 认缴出资额
                    "paidin_money": data.get("paidinMoney", "").replace("-", ""),  # 实际出资额
                    "url": response.url,
                    'contents': json.dumps(data, ensure_ascii=False),
                    "collection": "share_information"
                }
                gd_last_item = {**share_info.get(gd_name), **gd_item, **self.base_item}
                # print(f'基本股东:{gd_last_item}')
                yield gd_last_item

    def parse_wenshu_list(self, response):
        """ 解析裁判文书列表页 """
        base_info = response.meta.get('base_info', {})
        pid = response.meta.get('pid')
        # 列表解析
        results = json.loads(response.text)
        wenshu_list = results.get('data').get('list')
        if not wenshu_list:
            return
        for data in wenshu_list:
            ws_type = data.get('type', '')  # 文书类型
            verdict_date = data.get('verdictDate', '')  # 文书判决日期
            case_number = data.get('caseNo', '').strip()  # 案号
            role = data.get('role', '')  # 案件身份
            wenshu_name = data.get('wenshuName', '')  # 案件名称
            replace_content = data.get("replaceContent", "").replace("-", "")
            procedure_name = data.get('procedure', '')  # MySQL关键字
            wenshu_list_item = dict(
                ws_type=ws_type,
                verdict_date=verdict_date,
                case_number=case_number,
                role=role,
                wenshu_name=wenshu_name,
                replace_content=replace_content,
                procedure_name=procedure_name,
            )
            last_wenshu = {**base_info, **wenshu_list_item}

            wenshuId = data.get('wenshuId')  # 详情ID
            wenshu_url = "https://xin.baidu.com/wenshu?wenshuId={}&fl=1&castk=LTE%3D".format(wenshuId)
            yield scrapy.Request(url=wenshu_url, callback=self.parse_wenshu_detail, meta={"wenshu": last_wenshu}, priority=9)

        # 翻页请求
        is_first = response.meta.get("is_first", True)
        if is_first:
            max_page_count = results.get('data').get("pageCount", 1)
            if max_page_count > 1:
                max_page_count = 1000 if max_page_count > 1000 else max_page_count
                for page in range(2, int(max_page_count) + 1):
                    url = "https://xin.baidu.com/detail/lawWenshuAjax?pid={}&p={}&fl=1&castk=LTE%3D".format(pid, page)
                    meta_data = {'pid': pid, 'is_first': False, "base_info": base_info}
                    yield scrapy.Request(url=url, callback=self.parse_wenshu_list, meta=meta_data, priority=5)

    def parse_wenshu_detail(self, response):
        """ 解析裁判文书详情页 """
        wenshu = response.meta.get('wenshu')
        # 详情页解析
        selector = scrapy.Selector(text=response.text)
        re_com = re.compile(r'\r|\n|\t|\s')
        content_list = selector.xpath('//div[@class="zx-content"]//text()').getall()
        contents = reduce(lambda x, y: x + y, [re_com.sub('', i) for i in content_list])
        wenshu['contents'] = contents
        wenshu['url'] = response.url
        wenshu['content_node'] = selector.css('div[class=wenshu-article]').get('').replace('\n', '')
        wenshu['collection'] = 'wenshu_information'
        wenshu_item = {**wenshu, **self.base_item}
        # print(f'裁判文书信息:{wenshu_item}')
        yield wenshu_item

    def parse_discredit(self, response):
        """ 解析失信被执行人列表页 """
        base_info = response.meta.get('base_info', {})
        pid = response.meta.get('pid')
        # 列表页解析，请求详情
        results = json.loads(response.text)
        discred_list = results.get('data').get('list')
        if not discred_list:
            return
        for data in discred_list:
            discreditId = data.get('discreditId')  # 详情页参数
            detail_url = 'https://xin.baidu.com/discredit?discreditid={}&fl=1&castk=LTE%3D'.format(discreditId)
            yield scrapy.Request(url=detail_url, callback=self.parse_discredit_detail, meta={"shixin": base_info}, priority=9)

        # 翻页请求
        is_first = response.meta.get("is_first", True)
        if is_first:
            max_page_count = results.get('data').get("pageCount", 1)
            if max_page_count > 1:
                for page in range(2, int(max_page_count) + 1):
                    url = 'https://xin.baidu.com/detail/discreditAjax?pid={}&p={}&fl=1&castk=LTE%3D'.format(pid, page)
                    meta_data = {'pid': pid, 'is_first': False, 'base_info': base_info}
                    yield scrapy.Request(url=url, callback=self.parse_discredit, meta=meta_data, priority=7)

    def parse_discredit_detail(self, response):
        """ 解析失信被执行人详情页 """
        shixin = response.meta.get('shixin')
        # 解析详情
        selector = scrapy.Selector(text=response.text)
        table = selector.css('table[class=discredit-list]')
        for td in table:
            fb_rq = td.css('tr:nth-child(1) td:nth-child(2) span::text').get('')  # 发布时间
            cf_xzjg = td.css('tr:nth-child(1) td:last-child span::text').get('')  # 做出执行依据单位
            pname = td.css('tr:nth-child(2) td:nth-child(2) span::text').get('')  # 法人代表
            verdict_number = td.css('tr:nth-child(2) td:last-child span::text').get('')  # 执行依据文号
            org_number_info = td.css('tr:nth-child(3) td:nth-child(2) span::text').get('')  # 组织机构代码
            verdict_date = td.css('tr:nth-child(3) td:last-child span::text').get('')  # 立案时间
            province = td.css('tr:nth-child(4) td:nth-child(2) span::text').get('')  # 省份
            implement_number = td.css('tr:nth-child(4) td:last-child span::text').get('')  # 执行案号
            implement_court = td.css('tr:nth-child(5) td:nth-child(2) span::text').get('')  # 执行法院
            perform_status = td.css('tr:nth-child(5) td:last-child span::text').get('')  # 被执行人履行情况
            perform_situation = td.css('tr:nth-child(6) td:nth-child(2) span::text').get('')  # 失信人被执行人行为具体情形
            duty = td.css('tr:nth-child(6) td:last-child span::text').get('')  # 生效文书确定义务
            perform_content = td.css('tr:last-child td:nth-child(2) span::text').get('')  # 已履行内容
            unperform_content = td.css('tr:last-child td:last-child span::text').get('')  # 未履行内容
            shixin_info = dict(
                fb_rq=fb_rq, cf_xzjg=cf_xzjg, pname=pname, verdict_number=verdict_number,
                org_number_info=org_number_info, verdict_date=verdict_date, province=province,
                implement_number=implement_number, implement_court=implement_court,
                perform_status=perform_status, perform_situation=perform_situation, duty=duty,
                perform_content=perform_content, unperform_content=unperform_content,
                url=response.url, collection='discredit_information',
                               )
            last_item_shixin = {**shixin, **shixin_info, **self.base_item}
            # print(f'失信被执行人:{last_item_shixin}')
            yield last_item_shixin

    def parse_abnormal(self, response):
        """ 解析经营异常列表页 """
        base_info = response.meta.get('base_info', {})
        pid = response.meta.get('pid')
        # 列表解析
        results = json.loads(response.text)
        discred_list = results.get('data').get('list')
        if not discred_list:
            return
        for data in discred_list:
            enterDate = data.get('enterDate')  # 列入日期
            enterReason = data.get('enterReason')  # 列入经营异常名录原因
            authority = data.get('authority')  # 列入决定机关
            leaveDate = data.get('leaveDate')  # 移出日期
            leaveReason = data.get('leaveReason')  # 移出经营异常名录原因
            leaveAuthority = data.get('leaveAuthority')  # 移出决定机关
            abnormal_item = dict(
                enter_date=enterDate, enter_reason=enterReason, authority=authority,
                leave_date=leaveDate, leave_reason=leaveReason, leave_authority=leaveAuthority,
                url=response.url, contents=json.dumps(data, ensure_ascii=False),
                collection='abnormal_information',
            )
            abnormal_last_data = {**base_info, **abnormal_item, **self.base_item}
            # print(f'经营异常:{abnormal_last_data}')
            yield abnormal_last_data

        # 列表翻页
        is_first = response.meta.get("is_first", True)
        if is_first:
            max_page_count = results.get('data').get("pageCount", 1)
            if max_page_count > 1:
                for page in range(2, int(max_page_count) + 1):
                    url = 'https://xin.baidu.com/detail/abnormalAjax?pid={}&p={}&fl=1&castk=LTE%3D'.format(pid, page)
                    meta_data = {'pid': pid, 'is_first': False, 'base_info': base_info}
                    yield scrapy.Request(url=url, callback=self.parse_abnormal, meta=meta_data, priority=7)

    def parse_penalties(self, response):
        """ 解析行政处罚列表页 """
        base_info = response.meta.get('base_info', {})
        pid = response.meta.get('pid')
        # 列表解析
        results = json.loads(response.text)
        xzcf_list = results.get('data').get('list')
        if not xzcf_list:
            return
        for data in xzcf_list:
            penaltiesId = data.get('penaltiesId')  # 详情页参数
            url = 'https://xin.baidu.com/penalty?penaltyid={}&fl=1&castk=LTE%3D'.format(penaltiesId)
            yield scrapy.Request(url=url, callback=self.parse_penalties_detail, meta={"xzcf": base_info}, priority=9)

        # 列表翻页
        is_first = response.meta.get("is_first", True)
        if is_first:
            max_page_count = results.get('data').get("pageCount", 1)
            if max_page_count > 1:
                for page in range(2, int(max_page_count) + 1):
                    url = 'https://xin.baidu.com/detail/penaltiesAjax?pid={}&p={}&fl=1&castk=LTE%3D'.format(pid, page)
                    meta_data = {'pid': pid, 'is_first': False, "base_info": base_info}
                    yield scrapy.Request(
                        url=url,
                        callback=self.parse_penalties,
                        meta=meta_data,
                        priority=5,
                    )

    def parse_penalties_detail(self, response):
        """ 解析行政处罚详情页 """
        xzcf = response.meta.get('xzcf')
        # 详情页解析
        selector = scrapy.Selector(text=response.text)
        table = selector.css('table[class=penalty-list]')
        for data in table:
            oname = data.css('tr:first-child td:nth-child(2) span::text').get('')  # 处罚主体名称
            cf_wsh = data.css('tr:nth-child(2) td:nth-child(2) span::text').get('').strip().replace("\n", "").replace(" ", "")  # 决定书文号
            cf_type = data.css('tr:nth-child(3) td:nth-child(2) span::text').get('')  # 处罚种类
            cf_sy = data.css('tr:nth-child(4) td:nth-child(2) span::text').get('')  # 处罚事由
            cf_yj = data.css('tr:nth-child(5) td:nth-child(2) span::text').get('')  # 处罚依据
            cf_jg = data.css('tr:nth-child(6) td:nth-child(2) span::text').get('')  # 处罚结果
            cf_jdrq = data.css('tr:nth-child(7) td:nth-child(2) span::text').get('')  # 处罚决定日期
            fb_rq = data.css('tr:nth-child(8) td:nth-child(2) span::text').get('')  # 处罚公开日期
            cf_status = data.css('tr:nth-child(9) td:nth-child(2) span::text').get('')  # 处罚状态
            cf_xzjg = data.css('tr:last-child td:nth-child(2) span::text').get('')  # 处罚机关
            xzcf_item = dict(
                oname=oname, cf_wsh=cf_wsh, cf_type=cf_type, cf_sy=cf_sy, cf_yj=cf_yj, cf_jg=cf_jg,
                cf_jdrq=cf_jdrq, fb_rq=fb_rq, cf_status=cf_status, cf_xzjg=cf_xzjg, url=response.url,
                collection='penalties_information',
            )
            last_item = {**xzcf, **xzcf_item, **self.base_item}
            # print(last_item)
            yield last_item

    def parse_stock_freeze(self, response):
        """ 解析股权冻结列表页 """
        base_info = response.meta.get('base_info', {})
        pid = response.meta.get('pid')
        # 列表解析
        results = json.loads(response.text)
        stock_list = results.get('data').get('list')
        if not stock_list:
            return
        for data in stock_list:
            beExecutedPerson = data.get('beExecutedPerson', '')  # 被执行人
            equalityAmount = data.get('equalityAmount', '')  # 股权数额
            notificationNumber = data.get('notificationNumber', '')  # 执行通知文书号
            typeAndStatus = data.get('typeAndStatus', '')  # 类型/状态
            stockFreezeKey = data.get('stockFreezeKey')  # 详情页参数
            detail_url = 'https://xin.baidu.com/Stockfreeze?stockFreezeKey={}&pid={}'.format(stockFreezeKey, pid)
            list_info = dict(
                executed_person=beExecutedPerson, equality_amount=equalityAmount,
                notification_number=notificationNumber, type_and_status=typeAndStatus,
            )
            base_item = {**list_info, **base_info}
            yield scrapy.Request(url=detail_url, callback=self.parse_stock_freeze_detail, meta={"stock_freeze": base_item}, priority=9)

        # 翻页请求
        is_first = response.meta.get("is_first", True)
        if is_first:
            max_page_count = results.get('data').get("pageCount", 1)
            if max_page_count > 1:
                for page in range(2, int(max_page_count) + 1):
                    url = 'https://xin.baidu.com/Stockfreeze/stockFreezeAjax?pid={}&p={}&fl=1&castk=LTE%3D'.format(pid, page)
                    meta_data = {'pid': pid, 'is_first': False, "base_info": base_info}
                    yield scrapy.Request(
                        url=url,
                        callback=self.parse_stock_freeze,
                        meta=meta_data,
                        priority=5,
                    )

    def parse_stock_freeze_detail(self, response):
        """ 解析股权冻结详情页 """
        stock_freeze = response.meta.get('stock_freeze')
        # 详情页解析
        item = {}
        selector = scrapy.Selector(text=response.text)
        table_first = selector.xpath('//table[@class="stockfreeze-list"][1]')
        for data in table_first:
            enforcement_number = data.css('tr:first-child td:nth-child(2) span::text').get('')  # 执行裁定文书号
            # notification_number = data.css('tr:first-child td:nth-child(4) span::text').get('')  # 执行通知文书号
            executed_court = data.css('tr:nth-child(2) td:nth-child(2) span::text').get('')  # 执行法院
            executed_matters = data.css('tr:nth-child(2) td:nth-child(4) span::text').get('')  # 执行事项
            # executed_person = data.css('tr:nth-child(3) td:nth-child(2) span::text').get('')  # 被执行人
            # equality_amount = data.css('tr:nth-child(3) td:nth-child(4) span::text').get('')  # 被执行人持有股权、其他投资权益的数额
            executed_type = data.css('tr:nth-child(4) td:nth-child(2) span::text').get('')  # 被执行人证件种类
            executed_number = data.css('tr:nth-child(4) td:nth-child(4) span::text').get('')  # 被执行人证件号码
            freeze_period_from = data.css('tr:nth-child(5) td:nth-child(2) span::text').get('')  # 冻结期限自
            freeze_period_end = data.css('tr:nth-child(5) td:nth-child(4) span::text').get('')  # 冻结期限至
            freeze_period = data.css('tr:last-child td:nth-child(2) span::text').get('')  # 冻结期限
            publicity_date = data.css('tr:last-child td:nth-child(4) span::text').get('')  # 公示日期
            first_table = dict(
                enforcement_number=enforcement_number, executed_court=executed_court, executed_matters=executed_matters,
                executed_type=executed_type, executed_number=executed_number, freeze_period_from=freeze_period_from,
                freeze_period_end=freeze_period_end, freeze_period=freeze_period, publicity_date=publicity_date,
            )
            # print(f'第一张表:{first_table}')
            item['first_table'] = first_table
        # 解冻情况
        unfreeze = selector.xpath('//h4[contains(.,"解冻情况")]/following-sibling::p[1]/text()').get('')
        # 续行冻结情况
        continuation_freeze = selector.xpath('//h4[contains(.,"续行冻结情况")]/following-sibling::p[1]/text()').get('')

        table_second = selector.css('table[class=stockfreeze-list]:last-child')
        for shixiao in table_second:
            invalid_date = shixiao.css('tr:first-child td:nth-child(2) span::text').get('')  # 失效时间
            invalid_reason = shixiao.css('tr:first-child td:nth-child(4) span::text').get('')  # 失效原因
            second_table = dict(invalid_date=invalid_date, invalid_reason=invalid_reason)
            # print(f'第二张表:{second_table}')
            item['second_table'] = second_table

        first_dict = item.get('first_table')
        second_dict = item.get('second_table')
        third_dict = dict(unfreeze=unfreeze, continuation_freeze=continuation_freeze, url=response.url, collection='freeze_infomation')
        last_dict = {**stock_freeze, **first_dict, **second_dict, **third_dict, **self.base_item}
        # print(last_dict)
        yield last_dict

    def parse_illegal(self, response):
        """ 解析严重违法列表页 """
        base_info = response.meta.get('base_info', {})
        pid = response.meta.get('pid')
        # 列表解析
        results = json.loads(response.text)
        illegal_list = results.get('data').get('list')
        if not illegal_list:
            return
        for data in illegal_list:
            enterDate = data.get('enterDate')  # 列入日期
            enterReason = data.get('enterReason')  # 列入严重违法名录原因
            leaveDate = data.get('leaveDate')  # 移出日期
            leaveReason = data.get('leaveReason')  # 移出严重违法名录原因
            authority = data.get('authority')  # 列入决定机关
            leaveAuthority = data.get('leaveAuthority')  # 移出决定机关
            illegal_item = dict(
                enter_date=enterDate,
                enter_reason=enterReason,
                authority=authority,
                leave_date=leaveDate,
                leave_reason=leaveReason,
                leave_authority=leaveAuthority,
                contents=json.dumps(data, ensure_ascii=False),
                url=response.url,
                collection='illegal_infomation',
            )
            illegal_info = {**base_info, **illegal_item, **self.base_item}
            # print(illegal_info)
            yield illegal_info

        # 翻页请求
        is_first = response.meta.get("is_first", True)
        if is_first:
            max_page_count = results.get('data').get("pageCount", 1)
            if max_page_count > 1:
                for page in range(2, int(max_page_count) + 1):
                    url = 'https://xin.baidu.com/detail/illegalAjax?pid={}&p={}&fl=1&castk=LTE%3D'.format(pid, page)
                    meta_data = {'pid': pid, 'is_first': False, 'base_info': base_info}
                    yield scrapy.Request(
                        url=url,
                        callback=self.parse_illegal,
                        meta=meta_data,
                        priority=7,
                    )