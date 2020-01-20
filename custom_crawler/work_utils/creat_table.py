# -*- coding: utf-8 -*-
from datetime import datetime
import warnings

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from custom_crawler.settings import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, DB_CHARSET
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy import Column, Integer, String, TEXT, DATETIME, SMALLINT, ForeignKey

warnings.filterwarnings("ignore")
Base = declarative_base()
# 初始化数据库连接:
engine = create_engine(
    "mysql+pymysql://{username}:{password}@{host}:{port}/{db}?charset={charset}".format(username=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, db=DB_NAME, charset=DB_CHARSET),
    # echo=True,  # 打印过程
    # max_overflow=0,  # 超过连接池大小外最多创建的连接
    # pool_size=5,  # 连接池大小
    # pool_timeout=30,  # 池中没有线程最多等待的时间，否则报错
    # pool_recycle=-1  # 多久之后对线程池中的线程进行一次连接的回收(重置)
)


class BusinessCollection(Base):
    """ 百度企业信用-工商信息表 """
    __tablename__ = 'business_information'
    id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
    ent_name = Column(String(length=128), nullable=True, index=True, comment='企业名称')
    reg_capital = Column(String(length=64), nullable=True, comment='注册资本')
    real_capital = Column(String(length=64), nullable=True, comment='实缴资本')
    legal_person = Column(String(length=64), nullable=True, comment='法人')
    open_status = Column(String(length=32), nullable=True, comment='经营状态')
    prev_ent_name = Column(String(length=128), nullable=True, comment='曾用名')
    industry = Column(String(length=32), nullable=True, comment='所属行业')
    unified_code = Column(String(length=64), nullable=True, comment='统一社会信用代码')
    tax_number = Column(String(length=64), nullable=True, comment='纳税人识别号')
    reg_number = Column(String(length=64), nullable=True, comment='注册号')
    license_number = Column(String(length=64), nullable=True, comment='工商注册号')
    org_number = Column(String(length=64), nullable=True, comment='组织机构代码')
    authority = Column(String(length=64), nullable=True, comment='登记机关')
    estiblish_time = Column(String(length=16), nullable=True, comment='成立日期')
    ent_type = Column(String(length=32), nullable=True, comment='企业类型')
    open_time = Column(String(length=32), nullable=True, comment='营业期限开始')
    district = Column(String(length=128), nullable=True, comment='行政区划')
    annual_date = Column(String(length=16), nullable=True, comment='审核/年检日期')
    scope = Column(LONGTEXT, nullable=True, comment='经营范围')
    reg_addr = Column(String(length=256), nullable=True, comment='注册地址')
    telephone = Column(String(length=20), nullable=True, comment='电话')
    email = Column(String(length=32), nullable=True, comment='邮箱')
    description = Column(LONGTEXT, nullable=True, comment='公司简单描述')
    old_ent_name = Column(String(length=128), nullable=True, comment='曾用名')

    contents = Column(LONGTEXT, nullable=True, comment='数据字典')
    url = Column(String(length=128), nullable=False, comment='详情url')
    spider_time = Column(DATETIME, nullable=False, default=datetime.now, comment='抓取时间')
    xxly = Column(String(length=20), nullable=True, comment='数据来源')
    process_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    upload_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    alter_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')

    def __repr__(self):
        return "<BusinessCollection %r>" % self.ent_name


class ShareCollection(Base):
    """ 百度企业信用-股东信息表 """
    __tablename__ = 'share_information'
    id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
    ent_name = Column(String(length=128), nullable=True, index=True, comment='企业名称')
    gd_name = Column(String(length=128), nullable=True, comment='股东姓名')
    gd_type = Column(String(length=64), nullable=True, comment='股东类型')
    sub_rate = Column(String(length=64), nullable=True, comment='持股比例')
    sub_money = Column(String(length=128), nullable=True, comment='认缴出资额')
    paidin_money = Column(String(length=128), nullable=True, comment='实际出资额')

    contents = Column(LONGTEXT, nullable=True, comment='数据字典')
    url = Column(String(length=128), nullable=False, comment='详情url')
    spider_time = Column(DATETIME, nullable=False, default=datetime.now, comment='抓取时间')
    xxly = Column(String(length=20), nullable=True, comment='数据来源')
    process_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    upload_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    alter_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')

    def __repr__(self):
        return "<ShareCollection %r>" % self.ent_name


class WenshuCollection(Base):
    """ 百度企业信用-裁判文书表 """
    __tablename__ = 'wenshu_information'
    id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
    ent_name = Column(String(length=128), nullable=True, index=True, comment='企业名称')
    legal_person = Column(String(length=64), nullable=True, comment='法人')
    open_status = Column(String(length=32), nullable=True, comment='经营状态')
    unified_code = Column(String(length=64), nullable=True, comment='统一社会信用代码')
    license_number = Column(String(length=64), nullable=True, comment='工商注册号')
    org_number = Column(String(length=64), nullable=True, comment='组织机构代码')
    reg_addr = Column(String(length=256), nullable=True, comment='注册地址')

    wenshu_name = Column(String(length=256), nullable=True, comment='案件名称')
    case_number = Column(String(length=256), nullable=True, comment='案号')
    role = Column(String(length=16), nullable=True, comment='案件身份')
    ws_type = Column(String(length=64), nullable=True, comment='文书类型')
    verdict_date = Column(String(length=20), nullable=True, comment='文书判决日期')
    procedure_name = Column(String(length=16), nullable=True, comment='第几次审判')
    replace_content = Column(String(length=16), nullable=True, comment='不确定意思')
    content_node = Column(LONGTEXT, nullable=True, comment='文本带节点')

    contents = Column(LONGTEXT, nullable=True, comment='文本内容')
    url = Column(String(length=128), nullable=False, comment='详情url')
    spider_time = Column(DATETIME, nullable=False, default=datetime.now, comment='抓取时间')
    xxly = Column(String(length=20), nullable=True, comment='数据来源')
    process_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    upload_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    alter_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')

    def __repr__(self):
        return "<WenshuCollection %r>" % self.ent_name


class DiscreditCollection(Base):
    """ 百度企业信用-失信被执行人表 """
    __tablename__ = 'discredit_information'
    id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
    ent_name = Column(String(length=128), nullable=True, index=True, comment='企业名称')
    legal_person = Column(String(length=64), nullable=True, comment='法人')
    open_status = Column(String(length=32), nullable=True, comment='经营状态')
    unified_code = Column(String(length=64), nullable=True, comment='统一社会信用代码')
    license_number = Column(String(length=64), nullable=True, comment='工商注册号')
    org_number = Column(String(length=64), nullable=True, comment='组织机构代码')
    reg_addr = Column(String(length=256), nullable=True, comment='注册地址')

    fb_rq = Column(String(length=16), nullable=True, comment='发布时间')
    cf_xzjg = Column(String(length=64), nullable=True, comment='做出执行依据单位')
    pname = Column(String(length=64), nullable=True, comment='详情页-法人代表')
    verdict_number = Column(String(length=64), nullable=True, comment='执行依据文号')
    org_number_info = Column(String(length=64), nullable=True, comment='详情页-组织机构代码')
    verdict_date = Column(String(length=16), nullable=True, comment='立案时间')
    province = Column(String(length=16), nullable=True, comment='省份')
    implement_number = Column(String(length=64), nullable=True, comment='执行案号')
    implement_court = Column(String(length=64), nullable=True, comment='执行法院')
    perform_status = Column(TEXT, nullable=True, comment='被执行人履行情况')
    perform_situation = Column(TEXT, nullable=True, comment='失信人被执行人行为具体情形')
    duty = Column(TEXT, nullable=True, comment='生效文书确定义务')
    perform_content = Column(TEXT, nullable=True, comment='已履行内容')
    unperform_content = Column(TEXT, nullable=True, comment='未履行内容')

    url = Column(String(length=128), nullable=False, comment='详情url')
    spider_time = Column(DATETIME, nullable=False, default=datetime.now, comment='抓取时间')
    xxly = Column(String(length=20), nullable=True, comment='数据来源')
    process_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    upload_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    alter_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')

    def __repr__(self):
        return "<DiscreditCollection %r>" % self.ent_name


class AbnormalCollection(Base):
    """ 百度企业信用-经营异常表 """
    __tablename__ = 'abnormal_information'
    id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
    ent_name = Column(String(length=128), nullable=True, index=True, comment='企业名称')
    legal_person = Column(String(length=64), nullable=True, comment='法人')
    open_status = Column(String(length=32), nullable=True, comment='经营状态')
    unified_code = Column(String(length=64), nullable=True, comment='统一社会信用代码')
    license_number = Column(String(length=64), nullable=True, comment='工商注册号')
    org_number = Column(String(length=64), nullable=True, comment='组织机构代码')
    reg_addr = Column(String(length=256), nullable=True, comment='注册地址')

    enter_date = Column(String(length=16), nullable=True, comment='列入日期')
    enter_reason = Column(TEXT, nullable=True, comment='列入经营异常名录原因')
    authority = Column(String(length=64), nullable=True, comment='列入决定机关')
    leave_date = Column(String(length=16), nullable=True, comment='移出日期')
    leave_reason = Column(TEXT, nullable=True, comment='移出经营异常名录原因')
    leave_authority = Column(String(length=64), nullable=True, comment='移出决定机关')

    contents = Column(LONGTEXT, nullable=True, comment='文本内容')
    url = Column(String(length=128), nullable=False, comment='详情url')
    spider_time = Column(DATETIME, nullable=False, default=datetime.now, comment='抓取时间')
    xxly = Column(String(length=20), nullable=True, comment='数据来源')
    process_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    upload_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    alter_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')

    def __repr__(self):
        return "<AbnormalCollection %r>" % self.ent_name


class PenaltiesCollection(Base):
    """ 百度企业信用-行政处罚表 """
    __tablename__ = 'penalties_information'
    id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
    ent_name = Column(String(length=128), nullable=True, index=True, comment='企业名称')
    legal_person = Column(String(length=64), nullable=True, comment='法人')
    open_status = Column(String(length=32), nullable=True, comment='经营状态')
    unified_code = Column(String(length=64), nullable=True, comment='统一社会信用代码')
    license_number = Column(String(length=64), nullable=True, comment='工商注册号')
    org_number = Column(String(length=64), nullable=True, comment='组织机构代码')
    reg_addr = Column(String(length=256), nullable=True, comment='注册地址')

    oname = Column(String(length=128), nullable=True, comment='处罚主体名称')
    cf_wsh = Column(String(length=64), nullable=True, comment='决定书文号')
    cf_type = Column(String(length=64), nullable=True, comment='处罚种类')
    cf_sy = Column(TEXT, nullable=True, comment='处罚事由')
    cf_yj = Column(TEXT, nullable=True, comment='处罚依据')
    cf_jg = Column(TEXT, nullable=True, comment='处罚结果')
    cf_jdrq = Column(String(length=16), nullable=True, comment='处罚决定日期')
    fb_rq = Column(String(length=16), nullable=True, comment='处罚公开日期')
    cf_status = Column(String(length=32), nullable=True, comment='处罚状态')
    cf_xzjg = Column(String(length=64), nullable=True, comment='处罚机关')

    contents = Column(LONGTEXT, nullable=True, comment='文本内容')
    url = Column(String(length=128), nullable=False, comment='详情url')
    spider_time = Column(DATETIME, nullable=False, default=datetime.now, comment='抓取时间')
    xxly = Column(String(length=20), nullable=True, comment='数据来源')
    process_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    upload_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    alter_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')

    def __repr__(self):
        return "<PenaltiesCollection %r>" % self.ent_name


class FreezeCollection(Base):
    """ 百度企业信用-股权冻结表 """
    __tablename__ = 'freeze_infomation'
    id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
    ent_name = Column(String(length=128), nullable=True, index=True, comment='企业名称')
    legal_person = Column(String(length=64), nullable=True, comment='法人')
    open_status = Column(String(length=32), nullable=True, comment='经营状态')
    unified_code = Column(String(length=64), nullable=True, comment='统一社会信用代码')
    license_number = Column(String(length=64), nullable=True, comment='工商注册号')
    org_number = Column(String(length=64), nullable=True, comment='组织机构代码')
    reg_addr = Column(String(length=256), nullable=True, comment='注册地址')

    executed_person = Column(String(length=256), nullable=True, comment='被执行人')
    equality_amount = Column(String(length=128), nullable=True, comment='股权数额')
    notification_number = Column(String(length=64), nullable=True, comment='执行通知文书号')
    type_and_status = Column(String(length=64), nullable=True, comment='类型/状态')
    enforcement_number = Column(String(length=64), nullable=True, comment='执行裁定文书号')
    executed_court = Column(String(length=64), nullable=True, comment='执行法院')
    executed_matters = Column(String(length=256), nullable=True, comment='执行事项')
    executed_type = Column(String(length=64), nullable=True, comment='被执行人证件种类')
    executed_number = Column(String(length=128), nullable=True, comment='被执行人证件号码')
    freeze_period_from = Column(String(length=32), nullable=True, comment='冻结期限自')
    freeze_period_end = Column(String(length=32), nullable=True, comment='冻结期限至')
    freeze_period = Column(String(length=32), nullable=True, comment='冻结期限')
    publicity_date = Column(String(length=32), nullable=True, comment='公示日期')
    invalid_date = Column(String(length=16), nullable=True, comment='失效时间')
    invalid_reason = Column(TEXT, nullable=True, comment='失效原因')
    unfreeze = Column(String(length=256), nullable=True, comment='解冻情况')
    continuation_freeze = Column(String(length=256), nullable=True, comment='续行冻结情况')

    url = Column(String(length=128), nullable=False, comment='详情url')
    spider_time = Column(DATETIME, nullable=False, default=datetime.now, comment='抓取时间')
    xxly = Column(String(length=20), nullable=True, comment='数据来源')
    process_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    upload_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    alter_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')

    def __repr__(self):
        return "<FreezeCollection %r>" % self.ent_name


class IllegalCollection(Base):
    """ 百度企业信用-严重违法表 """
    __tablename__ = 'illegal_infomation'
    id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
    ent_name = Column(String(length=128), nullable=True, index=True, comment='企业名称')
    legal_person = Column(String(length=64), nullable=True, comment='法人')
    open_status = Column(String(length=32), nullable=True, comment='经营状态')
    unified_code = Column(String(length=64), nullable=True, comment='统一社会信用代码')
    license_number = Column(String(length=64), nullable=True, comment='工商注册号')
    org_number = Column(String(length=64), nullable=True, comment='组织机构代码')
    reg_addr = Column(String(length=256), nullable=True, comment='注册地址')

    enter_date = Column(String(length=16), nullable=True, comment='列入日期')
    enter_reason = Column(TEXT, nullable=True, comment='列入严重违法名录原因')
    authority = Column(String(length=64), nullable=True, comment='列入决定机关')
    leave_date = Column(String(length=16), nullable=True, comment='移出日期')
    leave_reason = Column(TEXT, nullable=True, comment='移出严重违法名录原因')
    leave_authority = Column(String(length=64), nullable=True, comment='移出决定机关')

    contents = Column(LONGTEXT, nullable=True, comment='文本内容')
    url = Column(String(length=128), nullable=False, comment='详情url')
    spider_time = Column(DATETIME, nullable=False, default=datetime.now, comment='抓取时间')
    xxly = Column(String(length=20), nullable=True, comment='数据来源')
    process_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    upload_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    alter_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')

    def __repr__(self):
        return "<IllegalCollection %r>" % self.ent_name


if __name__ == '__main__':
    Base.metadata.create_all(engine)  # 新建表
    # Base.metadata.drop_all(engine)  # 删除表
