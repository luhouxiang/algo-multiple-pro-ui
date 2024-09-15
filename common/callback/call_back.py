# -*- coding: utf-8 -*-
"""
Created on
@author: <NAME>
@file: call_back.py
@desc: 由配置文件回调过程
"""
from common.model.kline import KLine, KExtreme
from common.algo.formula import MA
from datetime import datetime
from common.algo.weibi import get_weibi_list
from typing import List, Any
from common.model.obj import Direction
from common.chanlun.c_bi import Cal_LOWER
from common.chanlun.c_bi import Cal_UPPER, cal_independent_klines
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
    # logging.info(wbs)
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
    lower = Cal_LOWER(klines)
    upper = Cal_UPPER(klines)
    # upper = [0] * len(klines)
    fenxin = {}
    logging.info(f"分型,顶底数量: {len(lower)}")
    for i in range(len(lower)):
        dt = datetime.fromtimestamp(klines[i].time)
        if lower[i].side == KExtreme.BOTTOM:
            fenxin[dt] = [dt, -1]
            logging.info(f"底的时间：[{dt.strftime('%Y-%m-%d %H:%M:%S')}]")
    for i in range(len(upper)):
        dt = datetime.fromtimestamp(klines[i].time)
        if upper[i].side == KExtreme.TOP:
            fenxin[dt] = [dt, 1]
            logging.info(f"顶的时间：[{dt.strftime('%Y-%m-%d %H:%M:%S')}]")

    return fenxin


def fn_calc_independent_klines(klines: list[KLine]):
    """计算独立K线数量"""
    combs = cal_independent_klines(klines)
    independents = {}
    for i in range(len(combs)):
        dt = datetime.fromtimestamp(combs[i].data.time)
        independents[dt] = [dt, combs[i].data.low, combs[i].data.high, combs[i].pos_begin, combs[i].pos_end, combs[i].pos_extreme, combs[i].isUp.value]
    return independents


def fn_calc_bi(klines: list[KLine]) -> List[Any]:
    pass
    # Cal_OLD_TEST(klines)



