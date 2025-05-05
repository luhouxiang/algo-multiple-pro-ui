# -*- coding: utf-8 -*-
"""
Created on
@author: <NAME>
@file: call_back.py
@desc: 由配置文件回调过程
"""
from common.model.kline import KLine, KExtreme, KSide, stFxK, stCombineK, Segment, Pivot
from common.algo.formula import MA
from common.algo.channel import find_all_channels, find_all_channels2
from datetime import datetime
from common.algo.weibi import get_weibi_list
from typing import List, Any
from common.util import convert_kline_to_dataframe
from common.model.obj import Direction
from common.chanlun.c_bi import Cal_LOWER
from common.chanlun.c_bi import (Cal_UPPER, cal_independent_klines, calculate_bi, _NCHDUAN, compute_bi_pivots,
                                 compute_duan_pivots)
from typing import Dict
import logging
import json
import talib


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
        s_dt = datetime.fromtimestamp(klines[w.pos_begin].time)
        e_dt = datetime.fromtimestamp(klines[w.pos_end].time)
        if w.up:
            items.append([s_dt, w.lowest, e_dt, w.highest, 0, "yellow"])
        else:
            items.append([s_dt, w.highest, e_dt, w.lowest, 0, "yellow"])
    return items


def fn_calc_bi_pivot(klines: list[KLine]) -> List[Pivot]:
    """回调计算笔中枢"""
    lower: List[stFxK] = Cal_LOWER(klines)
    upper: List[stFxK] = Cal_UPPER(klines)
    combs = cal_independent_klines(klines)
    merges = init_merges(combs, klines)
    independents = init_independents(combs)

    bi_list = calculate_bi(lower, upper, merges, independents)
    pivots: List[Pivot] = compute_bi_pivots(bi_list)
    items = []
    for w in pivots:
        s_dt = datetime.fromtimestamp(klines[w.bg_pos_index].time)
        e_dt = datetime.fromtimestamp(klines[w.ed_pos_index].time)
        if w.up:
            color = "red"
        else:
            color = "green"
        items.append([s_dt, w.lowly_value, e_dt, w.lowly_value, 0, color])
        items.append([s_dt, w.highly_value, e_dt, w.highly_value, 0, color])
        items.append([s_dt, w.lowly_value, s_dt, w.highly_value, 0, color])
        items.append([e_dt, w.lowly_value, e_dt, w.highly_value, 0, color])
    return items


def fn_calc_duan_pivot(klines: list[KLine]) -> List[Pivot]:
    """回调计算中枢"""
    lower: List[stFxK] = Cal_LOWER(klines)
    upper: List[stFxK] = Cal_UPPER(klines)
    combs = cal_independent_klines(klines)
    merges = init_merges(combs, klines)
    independents = init_independents(combs)

    bi_list = calculate_bi(lower, upper, merges, independents)
    seg_list = _NCHDUAN(bi_list, klines)
    pivots: List[Pivot] = compute_duan_pivots(seg_list)
    items = []
    for w in pivots:
        s_dt = datetime.fromtimestamp(klines[w.bg_pos_index].time)
        e_dt = datetime.fromtimestamp(klines[w.ed_pos_index].time)
        # if w.up:
        #     color = "red"
        # else:
        #     color = "green"
        color = "yellow"
        items.append([s_dt, w.lowly_value, e_dt, w.lowly_value, 0, color])
        items.append([s_dt, w.highly_value, e_dt, w.highly_value, 0, color])
        items.append([s_dt, w.lowly_value, s_dt, w.highly_value, 0, color])
        items.append([e_dt, w.lowly_value, e_dt, w.highly_value, 0, color])
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

def fn_calc_channel(klines: List[KLine]):
    """计算通道"""
    fenxin = {}
    logging.info(f"fn_calc_channel begin...")
    datas = convert_kline_to_dataframe(klines)
    atr = talib.ATR(datas['High'], datas['Low'], datas['Close'], timeperiod=14)
    # 用第一个有效值填充前面的NaN
    first_valid_index = atr.first_valid_index()  # 找到第一个非NaN的索引
    if first_valid_index is not None:
        first_valid_value = atr[first_valid_index]  # 获取第一个有效值
        atr = atr.fillna(first_valid_value)  # 填充所有NaN
    else:
        atr = atr  # 如果没有有效值，保持原样
    # 将ATR添加到DataFrame
    datas['Atr'] = atr  # 关键操作：添加新列
    all_channels = find_all_channels2(datas, lookback=70)
    logging.info(f"all_channels_size = {len(all_channels)}")
    side = -1
    for item in all_channels:
        if item['type'] == 'Ascending':
            side = 1
        for i in range(item['start_idx'], item['end_idx']+1):
            dt = datetime.fromtimestamp(klines[i].time)
            fenxin[dt] = [dt, side]
    return fenxin


def fn_calc_atr(klines: list[KLine]):
    """计算atr"""
    bars = {}
    datas = convert_kline_to_dataframe(klines)
    atr = talib.ATR(datas['High'], datas['Low'], datas['Close'], timeperiod=20)
    first_valid_index = atr.first_valid_index()  # 找到第一个非NaN的索引
    if first_valid_index is not None:
        first_valid_value = atr[first_valid_index]  # 获取第一个有效值
        atr = atr.fillna(first_valid_value)  # 填充所有NaN
    else:
        atr = atr  # 如果没有有效值，保持原样
    for i, k in enumerate(klines):
        dt = datetime.fromtimestamp(k.time)
        bars[dt] = [dt, atr[i]]
    return bars


def fn_calc_feek(klines: List[KLine]):
    lower: List[stFxK] = Cal_LOWER(klines)
    upper: List[stFxK] = Cal_UPPER(klines)
    datas = convert_kline_to_dataframe(klines)
    fenxin = {}
    # logging.info(f"fn_calc_up_lower_upper begin.")
    # for i in range(len(lower)):
    #     dt = datetime.fromtimestamp(klines[i].time)
    #     if lower[i].side == KExtreme.BOTTOM:
    #         fenxin[dt] = [dt, -1]
    #         # logging.info(f"底的时间：[{dt.strftime('%Y-%m-%d %H:%M:%S')}]")
    # for i in range(len(upper)):
    #     dt = datetime.fromtimestamp(klines[i].time)
    #     if upper[i].side == KExtreme.TOP:
    #         fenxin[dt] = [dt, 1]
    #         # logging.info(f"顶的时间：[{dt.strftime('%Y-%m-%d %H:%M:%S')}]")
    # lower_count = sum(1 for value in fenxin.values() if value[-1] == 1)
    # upper_count = sum(1 for value in fenxin.values() if value[-1] == -1)
    # logging.info(f"fn_calc_up_lower_upper end.K线数量：{len(lower)}, 顶: {lower_count}, 底: {upper_count}")
    return fenxin