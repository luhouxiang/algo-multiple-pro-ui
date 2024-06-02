# -*- coding: utf-8 -*-
"""
Created on
@author: <NAME>
@file: call_back.py
@desc: 由配置文件回调过程
"""
from common.model.kline import KLine
from common.algo.formula import MA
from datetime import datetime
from common.algo.weibi import get_weibi_list
from typing import List, Any
from common.model.obj import Direction
from common.chanlun.c_bi import Cal_LOWER
from common.chanlun.c_bi import Cal_UPPER
import logging

def fn_calc_ma20_60(klines: list[KLine]):
    """由配置文件回调ma20,ma60的计算过程"""
    bars = {}
    MA20, MA60 = MA(20), MA(60)
    for k in klines:
        dt = datetime.fromtimestamp(k.time)
        MA20.input(k.close)
        MA60.input(k.close)
        bars[dt] = [dt, MA20.ma, MA60.ma]
    return bars


def fn_calc_wei_bi(klines: list[KLine]) -> List[Any]:
    """回调计算过程"""
    wbs = get_weibi_list(klines, N=5)
    logging.info(wbs)
    items = []
    for w in wbs:
        p1 = w.low if w.direction == Direction.Up else w.high
        p2 = w.high if w.direction == Direction.Up else w.low
        items.append([w.sdt, p1, w.edt, p2, 0])
    return items


def fn_calc_signal(klines: list[KLine]) -> List[Any]:
    """生成一个整数5倍的signal"""
    bars = {}
    for i in range(len(klines)):
        if i % 10 == 0:
            dt = datetime.fromtimestamp(klines[i].time)
            bars[dt] = [dt, -(i % 3)]
    return bars


def fn_calc_volumes(klines: list[KLine]):
    """回調計算成交量"""
    bars = {}
    for k in klines:
        dt = datetime.fromtimestamp(k.time)
        bars[dt] = [dt, k.volume]
    return bars


def fn_calc_up_lower_upper(klines: List[KLine]):
    lower = Cal_LOWER(klines, 0, len(klines)-1)
    upper = Cal_UPPER(klines, 0, len(klines)-1)
    # upper = [0] * len(klines)
    merge = {}
    for i in range(len(lower)):
        dt = datetime.fromtimestamp(klines[i].time)
        if lower[i]:
            merge[dt] = [dt, -1]
        # elif upper[i]:
        #     merge[i] = [dt, 1]
    return merge



def fn_calc_bi(klines: list[KLine]) -> List[Any]:
    pass
    # Cal_OLD_TEST(klines)



