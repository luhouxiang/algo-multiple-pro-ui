# -*- coding: utf-8 -*-
"""
@author: <luhx>
@desc: 根据逻辑实现的缠论的笔
包含的处理：1 确定方向：如果第n根K线发生包含关系，找到第n-1根K线，此两根K线没有包含关系，且n-1及其之前的包含关系都处理完毕。
如果第n-1根K线到第n根K线，高点抬高，则方向为向上，反之，如果低点降低，则方向为向下。
2 合并K线：2根有包含关系的K线，如果方向向下，则取其中高点中的低点作为新K线高点，取其中低点中的低点作为新K线低点，由此合并出一根新K线。
如果方向向上，则取其中高点中的高点作为新K线高点，取其中低点中的高点作为新K线低点，由此合并出一根新K线。
"""
from common.model.kline import KLine, stCombineK, KSide, stFxK, stBiK, KExtreme
from typing import List, Any
from common.chanlun.float_compare import *
import copy
import logging
from datetime import datetime
from typing import Tuple, Dict


def _Cal_MERGE(pData: List[KLine]) -> int:
    """
    合并K线逻辑,接受一个stCombineK类型的列表combs, 返回一个整数值表示独立K线的个数
    :param klines:
    :return:
    """
    combs = [stCombineK(pData[i].low, pData[i].high, i, i, i, KSide.DOWN) for i in range(len(pData))]

    size = len(combs)
    if len(combs) < 2:    # <=2时，返回本身的长度
        return combs

    pBegin = 0      # 起始位置
    pLast = pBegin  # 最后一个独立K线的位置
    pPrev = pBegin  # 前一个独立K线的位置
    pCur = pBegin + 1           # 当前K线的位置
    pEnd = pBegin + size - 1    # 最后一个K线位置

    def IndependentK(b_up: KSide):
        """用于处理独立K线的情况，更新标志和指针，并进行值的拷贝"""
        nonlocal pPrev
        nonlocal pLast
        pPrev = pCur
        pLast += 1  # 每处理一根独立K线，pLast增加1
        combs[pLast] = copy.deepcopy(combs[pCur])    # 值的拷贝，而不是指针, 总是拷贝第一个
        combs[pLast].isUp = b_up
        return

    def ContainsK(low, high, index, pos_end):
        """用于处理包含K线的情况，更新K线的数据和位置"""
        nonlocal pPrev
        combs[pLast].range_low = low
        combs[pLast].range_high = high
        combs[pLast].pos_end = pos_end
        combs[pLast].pos_extreme = index
        pPrev = pLast
        return

    # 初始合并逻辑
    if greater_than_0(combs[pCur].range_high - combs[pPrev].range_high) and \
        greater_than_0(combs[pCur].range_low - combs[pPrev].range_low):
        # 高点升，低点也升, 向上
        IndependentK(KSide.UP)
    elif less_than_0(combs[pCur].range_high - combs[pPrev].range_high) and \
        less_than_0(combs[pCur].range_low - combs[pPrev].range_low):
        # 高点降，低点也降，向下
        IndependentK(KSide.DOWN)
    else:
        if greater_than_0(combs[pCur].range_high - combs[pPrev].range_high) or \
            less_than_0(combs[pCur].range_low - combs[pPrev].range_low):
            # 高点高于前 或是 低点低于前， 右包含，向上合并
            ContainsK(combs[pPrev].range_low, combs[pCur].range_high, combs[pCur].pos_begin, combs[pCur].pos_begin)
        else:   # 左包函，即低点高于前，高点低于前，也向上合并
            ContainsK(combs[pCur].range_low, combs[pPrev].range_high, combs[pPrev].pos_begin, combs[pCur].pos_begin)
    pCur += 1   # 当前pCur向后走一步

    while pCur <= pEnd:
        if greater_than_0(combs[pCur].range_high - combs[pPrev].range_high) and \
                greater_than_0(combs[pCur].range_low - combs[pPrev].range_low):
            IndependentK(KSide.UP)  # 独立K 向上
        elif less_than_0(combs[pCur].range_high - combs[pPrev].range_high) and \
                less_than_0(combs[pCur].range_low - combs[pPrev].range_low):
            IndependentK(KSide.DOWN)    # 独立K 向下
        else:
            # 包含
            if greater_than_0(combs[pCur].range_high - combs[pPrev].range_high) or \
                    less_than_0(combs[pCur].range_low - combs[pPrev].range_low):
                    # 右包含
                if combs[pLast].isUp == KSide.UP:    # 向上，一样高取左极值，不一样高肯定是右高，取右值
                    pos_index = combs[pPrev].pos_extreme if equ_than_0(combs[pCur].range_high - combs[pPrev].range_high) \
                        else combs[pCur].pos_begin
                    ContainsK(combs[pPrev].range_low, combs[pCur].range_high, pos_index, combs[pCur].pos_begin)
                else:         # 向下，一样低取左极值，不一样低肯定是右低，取右值
                    pos_index = combs[pPrev].pos_extreme if equ_than_0(combs[pCur].range_low - combs[pPrev].range_low) \
                        else combs[pCur].pos_begin
                    ContainsK(combs[pCur].range_low, combs[pPrev].range_high, pos_index, combs[pCur].pos_begin)
            else:   # 左包含
                if combs[pLast].isUp == KSide.UP:  # 向上，一样高取左极值，否则高肯定是右高，取右值
                    pos_index = combs[pPrev].pos_begin if combs[pPrev].pos_begin == combs[pPrev].pos_end \
                        else combs[pPrev].pos_extreme
                    ContainsK(combs[pCur].range_low, combs[pPrev].range_high, pos_index, combs[pCur].pos_begin)
                else:       # 向下，一样低取左极值，否则低肯定是右低，取右值
                    pos_index = combs[pPrev].pos_begin if combs[pPrev].pos_begin == combs[pPrev].pos_end \
                        else combs[pPrev].pos_extreme
                    ContainsK(combs[pPrev].range_low, combs[pCur].range_high, pos_index, combs[pCur].pos_begin)
        pCur += 1
    return combs[:pLast - pBegin + 1]


def Cal_LOWER(pData: List[KLine]) -> List[stFxK]:
    """
    计算底分型
    """
    combs = cal_independent_klines(pData)
    ret = [stFxK(index=i, side=KExtreme.NORMAL, low=0.0, high=0.0) for i in range(len(pData))]

    nCount = len(combs)
    if nCount <= 2:  # 小于等于2的，直接退出
        return ret
    pPrev = 0
    pCur = pPrev + 1
    pNext = pCur + 1
    pEnd = pPrev + nCount - 1

    while pNext <= pEnd:
        if (less_than_0(combs[pCur].range_high - combs[pPrev].range_high) and
                less_than_0(combs[pCur].range_high - combs[pNext].range_high) and
                less_than_0(combs[pCur].range_low - combs[pPrev].range_low) and
                less_than_0(combs[pCur].range_low - combs[pNext].range_low)):
            # ret[combs[pCur].pos_extreme] = [True, combs[pCur].data.low, combs[pCur].data.high]
            ret[combs[pCur].pos_extreme] = stFxK(index=combs[pCur].pos_extreme, side=KExtreme.BOTTOM,
                                                 low=combs[pCur].range_low, high=combs[pCur].range_high)
            ret[combs[pCur].pos_extreme].left = combs[pPrev]
            ret[combs[pCur].pos_extreme].right = combs[pNext]
            ret[combs[pCur].pos_extreme].extremal = combs[pCur]
            # ret[combs[pCur].pos_extreme].highest = max(combs[pPrev].range_high, combs[pNext].range_high)
        pPrev += 1
        pCur += 1
        pNext += 1
    return ret


def Cal_UPPER(pData: List[KLine]) -> List[stFxK]:
    """计算顶分型"""
    combs = cal_independent_klines(pData)   # combs是实际的独立K线的集合
    ret = [stFxK(index=i, side=KExtreme.NORMAL, low=0.0, high=0.0) for i in range(len(pData))]
    nCount = len(combs)

    if nCount <= 2:
        return ret

    pPrev = 0
    pCur = pPrev + 1
    pNext = pCur + 1
    pEnd = pPrev + nCount - 1
    while pNext <= pEnd:
        if (greater_than_0(combs[pCur].range_high - combs[pPrev].range_high) and
                greater_than_0(combs[pCur].range_high - combs[pNext].range_high) and
                greater_than_0(combs[pCur].range_low - combs[pPrev].range_low) and
                greater_than_0(combs[pCur].range_low - combs[pNext].range_low)):
            ret[combs[pCur].pos_extreme] = stFxK(index=combs[pCur].pos_extreme, side=KExtreme.TOP,
                                                 low=combs[pCur].range_low, high=combs[pCur].range_high)
            ret[combs[pCur].pos_extreme].left = combs[pPrev]
            ret[combs[pCur].pos_extreme].right = combs[pNext]
            ret[combs[pCur].pos_extreme].extremal = combs[pCur]
            # ret[combs[pCur].pos_extreme].lowest = min(combs[pPrev].range_low, combs[pNext].range_low)

        pPrev += 1
        pCur += 1
        pNext += 1
    return ret


def Cal_Fx(lower: List[stFxK], upper: List[stFxK]):
    """返回顶底分型的合集"""
    temp = [i for i in lower]
    for i in range(len(lower)):
        if upper[i].side != KExtreme.NORMAL:
            temp[i] = upper[i]
    return temp


def count_independent_kline(independents: Dict[int, int], b: int, e: int) -> int:
    """计算独立K线数"""
    return independents[e] - independents[b] + 1


def is_valid_fx(independents: Dict[int, int], b: int, e: int):
    bmgt = count_independent_kline(independents, b, e)
    return bmgt >= 5


def get_independents(combs: List[stCombineK]):
    independents: Dict[int, int] = {}
    for i in range(len(combs)):
        for j in range(combs[i].pos_begin, combs[i].pos_end+1):
            independents[j] = i  # 表达出索引pos_begin至pos_end实际上是第i根独立K线


def generate_bi(fractals: List[stFxK]) -> List[stBiK]:
    bi_list = []
    for i in  range(len(fractals)-1):
        f1: stFxK = fractals[i]
        f2: stFxK = fractals[i+1]
        if f1.side == f2.side:
            continue
        bi = stBiK()
        bi.side = KSide.UP if f1.side == KExtreme.BOTTOM else KSide.DOWN
        bi.top = f1 if f1.side == KExtreme.TOP else f2
        bi.bottom = f2 if f2.side == KExtreme.BOTTOM else f1
        bi.lowest = bi.bottom.lowest
        bi.highest = bi.top.highest
        bi.pos_begin = bi.bottom.index if bi.side == KSide.UP else bi.top.index
        bi.pos_end = bi.top.index if bi.side == KSide.UP else bi.bottom.index
        bi_list.append(bi)
    return bi_list


def deal_same_top_bottom(next: int, temp: List[stFxK], base: int, up: bool, merge: List[KLine], c1: int) -> (int, int):
    """处理相同顶底的情况"""
    while next > 0 and temp[next].side == temp[base].side:
        next = next_(next + 1, temp)
        if next < 0:
            break
        if up:
            if merge[next].low < merge[c1].low:
                c1 = next
        else:
            if merge[next].high > merge[c1].high:
                c1 = next
    return next, c1


def deal_not_last(next: int, c1: int, base: int, ind: Dict[int, int]) -> (int, int):
    if next > 0 and c1 > 0:
        if is_valid_fx(ind, next, base) and not is_valid_fx(ind, c1, base):
            pass
    elif is_valid_fx(ind, next, base) and is_valid_fx(ind, c1, base):
        next = c1
    return next


def satisfy_the_number(next: int, temp: List[stFxK], up: bool, merge: List[KLine], ind: Dict[int, int]) -> (int, int):
    bs = next
    bs_next = next
    while True:
        bs_next = next_(bs_next+1, temp)
        if bs_next < 0:
            return -next, next    # 寻到末尾了，返回前一个，且以负数返回，表示已经到最后了
        if temp[bs_next].side == temp[next].side:   # 同方向的，即同底分型或是同顶分型
            if up:
                if merge[bs_next].low < merge[next].low:
                    next = bs_next
                    bs = next
                    bs_next = next
                    continue
            else:   # up 在同一级别
                if merge[bs_next].high > merge[next].high:
                    next = bs_next
                    bs = next
                    bs_next = next
            continue
        bmgt = count_independent_kline(ind, bs, bs_next)
        if bmgt < 5:
            continue
        else:
            if up:
                if merge[bs_next].high < merge[next].high or (not merge[bs_next].low > merge[next].high):
                    continue
            else:
                if merge[bs_next].low > merge[next].low or (not merge[bs_next].high < merge[next].low):
                    continue
            break
    return 0, next


def get_node(base: int, temp: List[stFxK], merge: List[KLine], ind: Dict[int, int]):
    norm = 5
    up = temp[base].side == KExtreme.TOP
    next = go_util_difference_fx(base, temp)

    while next > 0:
        mgt = count_independent_kline(ind, base, next)  # 计算独立K线的数量
        if mgt < norm:
            next = next_(next+1, temp)
            c1 = next
            next, c1 = deal_same_top_bottom(next, temp, base, up, merge, c1)
            next = deal_not_last(next, c1, base, ind)
            if next < 0:
                break
        else:   # 满足笔的K线数量的要求
            rel, next = satisfy_the_number(next, temp, up, merge, ind)
            if rel == 0:
                break
            else:
                return rel
    return next


def go_util_difference_fx(base, temp):
    """往下走，相同的分型就一直走，一直走到遇到不同的分开为止"""
    next = next_(base + 1, temp)
    while next > 0 and temp[next].side == temp[base].side:  # 相同的顶或底，再往下走
        if next > 0:
            next = next_(base + 1, temp)
        else:
            break
    return next


def next_(base: int, temp: List[stFxK]):
    for i in range(base, len(temp)):
        if temp[i].side != KExtreme.NORMAL:
            return i
    return -1


def calculate_bi(lower: List[stFxK], upper: List[stFxK], merge: List[KLine], ind: Dict[int, int]) -> List[stBiK]:
    """计算笔"""
    temp = Cal_Fx(lower, upper)
    old_: List[stFxK] = []
    i = 0
    while i < len(temp):
        if temp[i].side != KExtreme.NORMAL:
            right = get_node(i, temp, merge, ind)
            if right < 0:
                if right < -1:
                    old_.append(temp[-right])
                break
            if not old_:
                old_.append(temp[i])
            old_.append(temp[right])
            i = right - 1
        i += 1
    for item in old_:
        logging.info(f"[{item.index}]:{item.side}")
    bis = generate_bi(old_)
    return bis


def cal_independent_klines(pData: List[KLine]) -> List[stCombineK]:
    """
    计算出独立K线,返回独立K线对象列表
    """
    combs = _Cal_MERGE(pData)
    return combs













