# -*- coding: utf-8 -*-
"""
Created on
@author: <NAME>
@file: call_back.py
@desc: 由配置文件回调过程
"""
from common.model.kline import KLine, KExtreme, KSide, stFxK, stCombineK, Segment
from common.algo.formula import MA
from datetime import datetime
from common.algo.weibi import get_weibi_list
from typing import List, Any
from common.model.obj import Direction
from common.chanlun.c_bi import Cal_LOWER
from common.chanlun.c_bi import Cal_UPPER, cal_independent_klines, calculate_bi, _NCHDUAN
from typing import Dict
import logging
import json


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


def write_extremes_to_file(fx_list, filename):
    data_to_write = []
    for fx in fx_list:
        if fx.side in (KExtreme.TOP, KExtreme.BOTTOM):
            type_str = 'top' if fx.side == KExtreme.TOP else 'bottom'
            data_to_write.append({
                'type': type_str,
                'index': fx.index,
                'high': fx.highest,
                'low': fx.lowest
            })
    with open(filename, 'w') as f:
        json.dump(data_to_write, f, indent=4)


def fn_calc_up_lower_upper(klines: List[KLine]):
    lower: List[stFxK] = Cal_LOWER(klines)
    upper: List[stFxK] = Cal_UPPER(klines)
    fenxin = {}
    logging.info(f"fn_calc_up_lower_upper begin.")
    for i in range(len(lower)):
        dt = datetime.fromtimestamp(klines[i].time)
        if lower[i].side == KExtreme.BOTTOM:
            fenxin[dt] = [dt, -1]
            # logging.info(f"底的时间：[{dt.strftime('%Y-%m-%d %H:%M:%S')}]")
    for i in range(len(upper)):
        dt = datetime.fromtimestamp(klines[i].time)
        if upper[i].side == KExtreme.TOP:
            fenxin[dt] = [dt, 1]
            # logging.info(f"顶的时间：[{dt.strftime('%Y-%m-%d %H:%M:%S')}]")
    lower_count = sum(1 for value in fenxin.values() if value[-1] == 1)
    upper_count = sum(1 for value in fenxin.values() if value[-1] == -1)
    logging.info(f"fn_calc_up_lower_upper end.K线数量：{len(lower)}, 顶: {lower_count}, 底: {upper_count}")
    return fenxin


def init_independents(combs: List[stCombineK]):
    """初始化K线索引和独立K线索引的映射关系"""
    independents: Dict[int, int] = {}
    for i in range(len(combs)):
        for j in range(combs[i].pos_begin, combs[i].pos_end+1):
            independents[j] = i  # 表达出索引pos_begin至pos_end实际上是第i根独立K线
    return independents


def fn_calc_bi(klines: list[KLine]) -> List[Any]:
    """回调计算过程笔"""
    lower: List[stFxK] = Cal_LOWER(klines)
    upper: List[stFxK] = Cal_UPPER(klines)
    combs = cal_independent_klines(klines)
    merges = init_merges(combs, klines)
    independents = init_independents(combs)

    bi_list = calculate_bi(lower, upper, merges, independents)

    items = []
    for w in bi_list:
        s_dt = datetime.fromtimestamp(klines[w.pos_begin].time)
        e_dt = datetime.fromtimestamp(klines[w.pos_end].time)
        if w.side == KSide.UP:
            items.append([s_dt, w.lowest, e_dt, w.highest, 0, "red"])
        else:
            items.append([s_dt, w.highest, e_dt, w.lowest, 0, "red"])
    return items


def fn_calc_seg(klines: list[KLine]) -> List[Segment]:
    """回调计算段"""
    lower: List[stFxK] = Cal_LOWER(klines)
    upper: List[stFxK] = Cal_UPPER(klines)
    combs = cal_independent_klines(klines)
    merges = init_merges(combs, klines)
    independents = init_independents(combs)

    bi_list = calculate_bi(lower, upper, merges, independents)
    seg_list: List[Segment] = _NCHDUAN(bi_list, klines)
    items = []
    for w in seg_list:
        s_dt = datetime.fromtimestamp(klines[w.start_index].time)
        e_dt = datetime.fromtimestamp(klines[w.end_index].time)
        if w.up:
            items.append([s_dt, w.lowest, e_dt, w.highest, 0, "blue"])
        else:
            items.append([s_dt, w.highest, e_dt, w.lowest, 0, "blue"])
    return items


def init_merges(combs, klines) -> List[KLine]:
    merges = [k for k in klines]
    for item in combs:
        for i in range(item.pos_begin, item.pos_end + 1):
            merges[i].low, merges[i].high = item.range_low, item.range_high
    return merges


def fn_calc_independent_klines(klines: list[KLine]):
    """计算独立K线数量"""
    combs = cal_independent_klines(klines)
    independents = {}
    p = klines
    for i in range(len(combs)):
        dt = datetime.fromtimestamp(p[combs[i].pos_begin].time)
        independents[dt] = [dt, combs[i].range_low, combs[i].range_high, combs[i].pos_begin, combs[i].pos_end,
                            combs[i].pos_extreme, combs[i].isUp.value]
    return independents


# def fn_calc_bi(klines: list[KLine]) -> List[Any]:
#     pass
#     # Cal_OLD_TEST(klines)



