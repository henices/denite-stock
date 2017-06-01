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
    {'name': 'up', 'link': 'Float', 're': ' \(\d\|\.\)\+%'},
    {'name': 'down',  'link': 'String', 're': ' \-\(\d\|\.\)\+ %'}
]

class Source(Base):
    def __init__(self, vim):
        super().__init__(vim)
        self.name = 'stock'

    def on_init(self, context):
        context['http'] = urllib3.PoolManager()

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
        suggest_url = 'http://suggest3.sinajs.cn/suggest/type=&key=' + code
        r = context['http'].request('GET', suggest_url)
        c = r.data.decode('gb2312')
        items = re.search('"(.*)"', c).groups()[0].split(';')

        if len(items) == 1:
            context['stock_code'] = items[0].split(',')[3]

        prompt = ''
        if len(items) > 1:
            for i in range(0, len(items)):
                item = items[i]
                prompt += '%d: %s\n' % (i, item.split(',')[4])

            stock_idx = util.input(self.vim,
                    context, '\n' + prompt + 'Stock code index: ')
            context['stock_code'] = items[int(stock_idx)].split(',')[3]

    def get_hq(self, context):
        hq_url = 'http://hq.sinajs.cn/list=' + context['stock_code']
        r = context['http'].request('GET', hq_url)
        c = r.data.decode('gb2312')
        info = re.search('"(.*)"', c).groups()[0].split(',')

        candidates = []

        if len(info) < 32:
            return candidates

        up = (float(info[3]) - float(info[2]))*100/float(info[2])

        candidates.append({'word': "股票名称 : "  +  info[0]})
        candidates.append({'word': "股票代码 : "  +  context['stock_code']})
        candidates.append({'word': "当前日期 : "  +  info[30]})
        candidates.append({'word': "当前时间 : "  +  info[31]})
        candidates.append({'word': "今日开盘 : "  +  info[1]})
        candidates.append({'word': "昨日收盘 : "  +  info[2]})
        candidates.append({'word': "当前价格 : "  +  info[3]})
        candidates.append({'word' :"上涨幅度 : %.2f %%" % up})
        candidates.append({'word': "今日最高 : "  +  info[4]})
        candidates.append({'word': "今日最低 : "  +  info[5]})
        candidates.append({'word': "成交股票 : "  +  info[8]})
        candidates.append({'word': "成交金额 : "  +  info[9]})

        return candidates

    def gather_candidates(self, context):
        self.get_code(context)
        return self.get_hq(context)
