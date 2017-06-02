#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .base import Base
from denite import util, process
import glob
import itertools
import os
import urllib3
import re

STOCK_HIGHLIGHT_SYNTAX = [
    {'name': 'keyword', 'link': 'Identifier', 're': ':\|\*'},
    {'name': 'up', 'link': 'Float', 're': ' \(\d\|\.\)\+ %'},
    {'name': 'down',  'link': 'String', 're': ' \-\(\d\|\.\)\+ %'}
]

class Source(Base):
    def __init__(self, vim):
        super().__init__(vim)
        self.name = 'stock'
        self.kind = 'word'

    def on_init(self, context):
        user_agent = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.7 Safari/537.36'}
        context['http'] = urllib3.PoolManager(10, headers=user_agent)

    def on_close(self, context):
        pass

    def highlight(self):
        for syn in STOCK_HIGHLIGHT_SYNTAX:
            self.vim.command(
                'syntax match {0}_{1} /{2}/ contained containedin={0}'.format(
                    self.syntax_name, syn['name'], syn['re']))
            self.vim.command('highlight default link {0}_{1} {2}'.format(
                    self.syntax_name, syn['name'], syn['link']))

    def get_code(self, context):
        code  = util.input(self.vim, context, 'Stock code: ')
        suggest_url = 'http://smartbox.gtimg.cn/s3/?v=2&q=%s&t=all' % code
        r = context['http'].request('GET', suggest_url, timeout=3.0)
        c = r.data.decode('utf-8')
        items = re.search('"(.*)"', c).groups()[0].split('^')

        if len(items) == 1:
            info = items[0].split('~')
            context['stock_code'] = info[0] + info[1]

        prompt = ''
        if len(items) > 1:
            for i in range(0, len(items)):
                item = items[i]
                info = item.split('~')
                prompt += '%d: %s\n' % \
                        (i, info[2].encode('utf-8').decode('unicode_escape'))

            stock_idx = util.input(self.vim,
                    context, '\n' + prompt + 'Stock code index: ')
            context['stock_code'] = \
                    ''.join(items[int(stock_idx)].split('~')[:2])

    def get_hq(self, context):
        hq_url = 'http://qt.gtimg.cn/q=' + context['stock_code']
        r = context['http'].request('GET', hq_url, timeout=2.0)
        c = r.data.decode('gb2312')
        print(c)

        info = re.search('"(.*)"', c).groups()[0].split('~')
        print(info)

        candidates = []

        if len(info) < 32:
            return candidates

        """
        0: 未知
        1: 名字
        2: 代码
        3: 当前价格
        4: 昨收
        5: 今开
        6: 成交量（手）
        7: 外盘
        8: 内盘
        9: 买一
        10: 买一量（手）
        11-18: 买二 买五
        19: 卖一
        20: 卖一量
        21-28: 卖二 卖五
        29: 最近逐笔成交
        30: 时间
        31: 涨跌
        32: 涨跌%
        33: 最高
        34: 最低
        35: 价格/成交量（手）/成交额
        36: 成交量（手）
        37: 成交额（万）
        38: 换手率
        39: 市盈率
        40:
        41: 最高
        42: 最低
        43: 振幅
        44: 流通市值
        45: 总市值
        46: 市净率
        47: 涨停价
        48: 跌停价
        """

        candidates.append({'word': "名称 : "  + info[1]})
        #candidates.append({'word': "代码 : "  +  info[2]})
        #candidates.append({'word': "时间 : "  +  info[30]})
        candidates.append({'word': "今开 : "  + info[5]})
        candidates.append({'word': "昨收 : "  +  info[4]})
        candidates.append({'word': "价格 : "  + info[3]})
        candidates.append({'word' :"上涨 : %s %%"  %  info[32]})
        candidates.append({'word': "最高 : "  + info[33]})
        candidates.append({'word': "最低 : "  + info[34]})
        candidates.append({'word': "换手 : "  + info[38]})
        #candidates.append({'word': "流通 : "  + info[44]})
        #candidates.append({'word': "市值 : "  + info[45]})
        #candidates.append({'word': "P/E  : "  + info[39]})
        #candidates.append({'word': '成交 : '  + info[29]})
        candidates.append({'word': '--------------------'})
        candidates.append({'word': '卖5  : ' + info[28]})
        candidates.append({'word': '卖4  : ' + info[26]})
        candidates.append({'word': '卖3  : ' + info[24]})
        candidates.append({'word': '卖2  : ' + info[22]})
        candidates.append({'word': '卖1  : ' + info[20]})
        candidates.append({'word': '--------------------'})
        candidates.append({'word': '买1  : ' + info[10]})
        candidates.append({'word': '买2  : ' + info[12]})
        candidates.append({'word': '买3  : ' + info[14]})
        candidates.append({'word': '买4  : ' + info[16]})
        candidates.append({'word': '买5  : ' + info[18]})

        return candidates

    def gather_candidates(self, context):
        self.get_code(context)
        return self.get_hq(context)
