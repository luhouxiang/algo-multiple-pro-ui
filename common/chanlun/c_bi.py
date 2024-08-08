# -*- coding: utf-8 -*-
"""
@author: <luhx>
@desc: 根据逻辑实现的缠论的笔
包含的处理：1 确定方向：如果第n根K线发生包含关系，找到第n-1根K线，此两根K线没有包含关系，且n-1及其之前的包含关系都处理完毕。
如果第n-1根K线到第n根K线，高点抬高，则方向为向上，反之，如果低点降低，则方向为向下。
2 合并K线：2根有包含关系的K线，如果方向向下，则取其中高点中的低点作为新K线高点，取其中低点中的低点作为新K线低点，由此合并出一根新K线。
如果方向向上，则取其中高点中的高点作为新K线高点，取其中低点中的高点作为新K线低点，由此合并出一根新K线。
"""
from common.model.kline import KLine, stCombineK, KSide
from typing import List, Any
from common.chanlun.float_compare import *
import copy
import logging
from datetime import datetime

def _Cal_MERGE(combs: List[stCombineK]) -> int:
    """
    合并K线逻辑,接受一个stCombineK类型的列表combs, 返回一个整数值表示独立K线的个数
    :param klines:
    :return:
    """
    size = len(combs)
    if len(combs) < 2:    # <=2时，返回本身的长度
        return size

    pBegin = 0      # 起始位置
    pLast = pBegin  # 最后一个独立K线的位置
    pPrev = pBegin  # 前一个独立K线的位置
    pCur = pBegin + 1           # 当前K线的位置
    pEnd = pBegin + size - 1    # 最后一个K线位置
    bUp = KSide.INITIAL         # 方向标志，初始化为 KSide.INITIAL

    def IndependentK(b_up: KSide):
        """用于处理独立K线的情况，更新标志和指针，并进行值的拷贝"""
        nonlocal bUp
        nonlocal pPrev
        nonlocal pLast
        bUp = b_up
        pPrev = pCur
        pLast += 1  # 每处理一根独立K线，pLast增加1
        combs[pLast] = copy.deepcopy(combs[pCur])    # 值的拷贝，而不是指针, 总是拷贝第一个
        combs[pLast].isUp = b_up
        return

    def ContainsK(low, high, index, pos_end):
        """用于处理包含K线的情况，更新K线的数据和位置"""
        nonlocal pPrev
        combs[pLast].data.low = low
        combs[pLast].data.high = high
        combs[pLast].pos_end = pos_end
        combs[pLast].pos_extreme = index
        combs[pLast].isUp = bUp     # 这个方向在独立K线时就已经更新，此处实际上不用更新了 note by luhx 2024-8-8

        pPrev = pLast
        return

    # 初始合并逻辑
    if greater_than_0(combs[pCur].data.high - combs[pPrev].data.high) and \
        greater_than_0(combs[pCur].data.low - combs[pPrev].data.low):
        # 高点升，低点也升, 向上
        IndependentK(KSide.UP)
    elif less_than_0(combs[pCur].data.high - combs[pPrev].data.high) and \
        less_than_0(combs[pCur].data.low - combs[pPrev].data.low):
        # 高点降，低点也降，向下
        IndependentK(KSide.DOWN)
    else:
        if greater_than_0(combs[pCur].data.high - combs[pPrev].data.high) or \
            less_than_0(combs[pCur].data.low - combs[pPrev].data.low):
            # 高点高于前 或是 低点低于前， 右包含，向上合并
            ContainsK(combs[pPrev].data.low, combs[pCur].data.high, combs[pCur].pos_begin, combs[pCur].pos_begin)
        else:   # 左包函，即低点高于前，高点低于前，也向上合并
            ContainsK(combs[pCur].data.low, combs[pPrev].data.high, combs[pPrev].pos_begin, combs[pCur].pos_begin)
    pCur += 1   # 当前pCur向后走一步

    while pCur <= pEnd:
        if greater_than_0(combs[pCur].data.high - combs[pPrev].data.high) and \
                greater_than_0(combs[pCur].data.low - combs[pPrev].data.low):
            IndependentK(KSide.UP)  # 独立K 向上
        elif less_than_0(combs[pCur].data.high - combs[pPrev].data.high) and \
                less_than_0(combs[pCur].data.low - combs[pPrev].data.low):
            IndependentK(KSide.DOWN)    # 独立K 向下
        else:
            # 包含
            if greater_than_0(combs[pCur].data.high - combs[pPrev].data.high) or \
                    less_than_0(combs[pCur].data.low - combs[pPrev].data.low):
                    # 右包含
                if bUp == KSide.UP:    # 向上，一样高取左极值，不一样高肯定是右高，取右值
                    pos_index = combs[pPrev].pos_extreme if equ_than_0(combs[pCur].data.high - combs[pPrev].data.high) \
                        else combs[pCur].pos_begin
                    ContainsK(combs[pPrev].data.low, combs[pCur].data.high, pos_index, combs[pCur].pos_begin)
                else:         # 向下，一样低取左极值，不一样低肯定是右低，取右值
                    pos_index = combs[pPrev].pos_extreme if equ_than_0(combs[pCur].data.low - combs[pPrev].data.low) \
                        else combs[pCur].pos_begin
                    ContainsK(combs[pCur].data.low, combs[pPrev].data.high, pos_index, combs[pCur].pos_begin)
            else:   # 左包含
                if bUp == KSide.UP:  # 向上，一样高取左极值，否则高肯定是右高，取右值
                    pos_index = combs[pPrev].pos_begin if combs[pPrev].pos_begin == combs[pPrev].pos_end \
                        else combs[pPrev].pos_extreme
                    ContainsK(combs[pCur].data.low, combs[pPrev].data.high, pos_index, combs[pCur].pos_begin)
                else:       # 向下，一样低取左极值，否则低肯定是右低，取右值
                    pos_index = combs[pPrev].pos_begin if combs[pPrev].pos_begin == combs[pPrev].pos_end \
                        else combs[pPrev].pos_extreme
                    ContainsK(combs[pPrev].data.low, combs[pCur].data.high, pos_index, combs[pCur].pos_begin)
        pCur += 1
    return pLast - pBegin + 1   # 得出独立K线的数量


def Cal_LOWER(pData: List[KLine], m_MinPoint, m_MaxPoint) -> List[bool]:
    """
    计算底分型
    """
    # m_pData = copy.deepcopy(pData)
    # combs: List[stCombineK] = []
    # for i in range(m_MinPoint, m_MaxPoint):
    #     data = stCombineK(m_pData[i], i, i, i, KSide.UP)
    #     combs.append(data)
    # nCount = _Cal_MERGE(combs)
    # ret = [False] * len(combs)
    #
    # if nCount <= 2:  # 小于等于2的，直接退出
    #     return ret
    ret = [False] * (m_MaxPoint-m_MinPoint)
    combs = cal_independent_klines(pData, m_MinPoint, m_MaxPoint)
    nCount = len(combs)
    if nCount <= 2:  # 小于等于2的，直接退出
        return ret
    pPrev = 0
    pCur = pPrev + 1
    pNext = pCur + 1
    pEnd = pPrev + nCount - 1

    while pNext <= pEnd:
        if (less_than_0(combs[pCur].data.high - combs[pPrev].data.high) and
                less_than_0(combs[pCur].data.high - combs[pNext].data.high) and
                less_than_0(combs[pCur].data.low - combs[pPrev].data.low) and
                less_than_0(combs[pCur].data.low - combs[pNext].data.low)):
            ret[combs[pCur].pos_extreme] = True
        pPrev += 1
        pCur += 1
        pNext += 1
    return ret

def cal_independent_klines(pData: List[KLine], m_MinPoint, m_MaxPoint) -> List[stCombineK]:
    m_pData = copy.deepcopy(pData)
    combs: List[stCombineK] = []
    for i in range(m_MinPoint, m_MaxPoint):
        data = stCombineK(m_pData[i], i, i, i, KSide.DOWN)
        combs.append(data)
    nCount = _Cal_MERGE(combs)
    if nCount <= 2:
        return []
    arr = combs[:nCount]
    logging.info(f"begin...{'*' * 80}")
    for i in arr:
        logging.info(f"{i.pos_begin},{i.pos_end},{i.pos_extreme},"
                     f"{i.isUp.value},{str(datetime.fromtimestamp(i.data.time))},"
                     f"o={i.data.open},h={i.data.high},l={i.data.low},c={i.data.close}")
    logging.info(f"end.{'*' * 80}")
    return arr

def Cal_UPPER(pData: List[KLine], m_MinPoint, m_MaxPoint) -> List[bool]:
    """计算顶分型"""
    m_pData = copy.deepcopy(pData)
    combs: List[stCombineK] = []
    for i in range(m_MinPoint, m_MaxPoint):
        data = stCombineK(m_pData[i], i, i, i, KSide.DOWN)
        combs.append(data)
    nCount = _Cal_MERGE(combs)
    ret = [False] * len(combs)
    if nCount <= 2:
        return ret

    pPrev = 0
    pCur = pPrev + 1
    pNext = pCur + 1
    pEnd = pPrev + nCount - 1
    while pNext <= pEnd:
        if (greater_than_0(combs[pCur].data.high - combs[pPrev].data.high) and
                greater_than_0(combs[pCur].data.high - combs[pNext].data.high) and
                greater_than_0(combs[pCur].data.low - combs[pPrev].data.low) and
                greater_than_0(combs[pCur].data.low - combs[pNext].data.low)):
            ret[combs[pCur].pos_extreme] = True     # 顶分型
        pPrev += 1
        pCur += 1
        pNext += 1
    return ret


def pre_(klines: List[KLine], base: int) -> int:
    """向前查找不相等的，返回左边的那个索引，若找不到，返回-1"""
    for i in range(base, 0, -1):
        if klines[i].high == klines[i-1].high and klines[i-1].low == klines[i].low:  # 完全相等，往回走
            pass
        else:
            return i-1
    return -1


def Cal_MERGE(m_pData: List[KLine], m_MinPoint, m_MaxPoint):
    """合并最后返回对应的K线"""
    klines: List[KLine] = []
    for i in range(m_MinPoint, m_MaxPoint):
        klines.append(copy.deepcopy(m_pData[i]))

    for i in range(1, len(klines)):
        contain_flag = ((klines[i].high >= klines[i-1].high and klines[i].low <= klines[i-1].low) or  # 右包含
                        (klines[i].high <= klines[i-1].high and klines[i].low >= klines[i-1].low))    # 左包含
        if not contain_flag:
            continue

        if i == 1:  # 第一根线,右包含向上取,左包含向下取
            if klines[i].high > klines[i-1].high:   # 如果是右包含，高中取高，低中取高
                klines[i].high = klines[i-1].high = max(klines[i].high, klines[i-1].high)
                klines[i].low = klines[i-1].low = max(klines[i].low, klines[i-1].low)
            else:
                klines[i].high = klines[i-1].high = min(klines[i].high, klines[i-1].high)
                klines[i].low = klines[i-1].low = min(klines[i].low, klines[i-1].low)
            continue

        pre = i - 2
        cur = i - 1
        if pre < 0:
            continue
        while ((klines[cur].high > klines[pre].high and klines[cur].low < klines[pre].low) or
               (klines[cur].high < klines[pre].high and klines[cur].low > klines[pre].low) or
               (klines[cur].high == klines[pre].high and klines[cur].low == klines[pre].low)):
            # 右包含，左包含，完全相等三种情况，回退一格,一直回退到没有包含的情况
            pre -= 1
            cur -= 1
            if pre < 0 or cur < 0:
                break
        if pre < 0 or cur < 0:
            continue

        if ((klines[cur].high > klines[pre].high and klines[cur].low > klines[pre].low) or
                (klines[cur].high == klines[pre].high and klines[cur].low > klines[pre].low)):
            # 看起来有一个低点相等的条件没有考虑，不过也可以不考虑，因为这实际上是包含 TODO: 其实是包含，应该被合并
            # 往前找到一个pre低，当前高的, 即up, 向上合并
            pre_kline = pre_(klines, i - 1)
            klines[i].high = klines[i-1].high = max(klines[i].high, klines[i-1].high)
            klines[i].low = klines[i-1].low = max(klines[i].low, klines[i-1].low)
            if pre_kline < 0:
                pass
            else:
                for k in range(pre_kline+1, i-1):
                    klines[k].high = klines[i].high
                    klines[k].low = klines[i].low
        elif ((klines[cur].high < klines[pre].high and klines[cur].low < klines[pre].low) or
              (klines[cur].high == klines[pre].high and klines[cur].low < klines[pre].low)):
            # 往前找到一个pre高，当前低的，即down，向下合并
            pre_kline = pre_(klines, i-1)
            klines[i].high = klines[i-1].high = min(klines[i].high, klines[i-1].high)
            klines[i].low = klines[i-1].low = min(klines[i].low, klines[i-1].low)
            if pre_kline < 0:
                pass
            else:
                for k in range(pre_kline+1, i-1):
                    klines[k].high = klines[i].high
                    klines[k].low = klines[i].low
    return klines
















