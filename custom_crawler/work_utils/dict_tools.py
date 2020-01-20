# -*- coding: utf-8 -*-
def iter_x(x):
    """ 遍历字典或者列表 """
    if isinstance(x, dict):
        for key, value in x.items():
            yield (key, value)
    elif isinstance(x, list):
        for index, value in enumerate(x):
            yield (index, value)


def flat(x):
    """ 压平字典 """
    for key, value in iter_x(x):
        if isinstance(value, (dict, list)):
            for k, v in flat(value):
                k = f'{key}_{k}'
                yield (k, v)
        else:
            yield (key, value)


if __name__ == '__main__':
    data = {'first_table': {'enforcement_number': '-', 'executed_court': '广东省深圳市中级人民法院', 'executed_matters': '-', 'executed_type': '企业法人营业执照(公司)', 'executed_number': '13000000005288', 'freeze_period_from': '2015年05月08日', 'freeze_period_end': '2018年05月07日', 'freeze_period': '-', 'publicity_date': '2015-05-08'}, 'second_table': {'invalid_data': '-', 'invalid_reason': '-'}}
    results = flat(data)
    print(dict(results))