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
    """ 国家企业公示系统-工商信息表 """
    __tablename__ = 'gsxt_business_information'
    id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
    ent_name = Column(String(length=128), nullable=True, index=True, comment='企业名称')
    unified_code = Column(String(length=64), nullable=True, comment='统一社会信用代码')
    ent_type = Column(String(length=32), nullable=True, comment='企业类型')
    legal_person = Column(String(length=64), nullable=True, comment='法人')
    estiblish_time = Column(String(length=16), nullable=True, comment='成立日期')
    operate_from = Column(String(length=32), nullable=True, comment='营业期限开始')
    operate_to = Column(String(length=32), nullable=True, comment='营业期限截止')
    authority = Column(String(length=64), nullable=True, comment='登记机关')
    approve_date = Column(String(length=16), nullable=True, comment='核准日期')
    open_status = Column(String(length=32), nullable=True, comment='登记状态')
    reg_addr = Column(String(length=256), nullable=True, comment='注册地址')
    scope = Column(LONGTEXT, nullable=True, comment='经营范围')
    reg_capital = Column(String(length=64), nullable=True, comment='注册资本')
    reg_capital_unit = Column(String(length=64), nullable=True, comment='注册资本单位')
    reg_cap = Column(String(length=64), nullable=True, comment='注册资本大写')

    contents = Column(LONGTEXT, nullable=True, comment='数据字典')
    url = Column(String(length=512), nullable=False, comment='详情url')
    spider_time = Column(DATETIME, nullable=False, default=datetime.now, comment='抓取时间')
    xxly = Column(String(length=20), nullable=True, comment='数据来源')
    process_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    upload_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    alter_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')

    def __repr__(self):
        return "<BusinessCollection %r>" % self.ent_name


class AbnormalCollection(Base):
    """ 国家企业公示系统-经营异常表 """
    __tablename__ = 'gsxt_abnormal_information'
    id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
    ent_name = Column(String(length=128), nullable=True, index=True, comment='企业名称')
    unified_code = Column(String(length=64), nullable=True, comment='统一社会信用代码')
    legal_person = Column(String(length=64), nullable=True, comment='法人')
    reg_addr = Column(String(length=256), nullable=True, comment='注册地址')

    enter_reason = Column(TEXT, nullable=True, comment='列入经营异常名录原因')
    authority = Column(String(length=64), nullable=True, comment='列入决定机关')
    enter_date = Column(String(length=16), nullable=True, comment='列入日期')
    leave_reason = Column(TEXT, nullable=True, comment='移出经营异常名录原因')
    leave_authority = Column(String(length=64), nullable=True, comment='移出决定机关')
    leave_date = Column(String(length=16), nullable=True, comment='移出日期')

    contents = Column(LONGTEXT, nullable=True, comment='文本内容')
    url = Column(String(length=128), nullable=False, comment='详情url')
    spider_time = Column(DATETIME, nullable=False, default=datetime.now, comment='抓取时间')
    xxly = Column(String(length=20), nullable=True, comment='数据来源')
    process_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    upload_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')
    alter_status = Column(Integer, default=0, nullable=True, onupdate=1, comment='状态')

    def __repr__(self):
        return "<AbnormalCollection %r>" % self.ent_name


if __name__ == '__main__':
    Base.metadata.create_all(engine)  # 新建表
    # Base.metadata.drop_all(engine)  # 删除表
