# -*- coding: utf-8 -*-
"""
笔
"""
from multipledispatch import dispatch   # 模拟C++函数重载功能
# from model.kline import KLine, stCombineK
from typing import List, Any, Tuple
from common.model.kline import KLine
from common.chanlun.float_compare import *
from common.model.kline import KLine, stCombineK, KSide


def getNode(base, temp: List[int], merge: List[KLine], type: Trait):
    up: bool = temp[base] > 0
    norm: int = 0
    baseline: int = 0
    match type:
        case Trait.NEWLY:
            norm = 0
            baseline = 5
        case Trait.OLDEN:
            norm = 5
            baseline = 0
        case Trait.OLDEN_EXACT:
            norm = 5
            baseline = 0

    def next_(base: int):
        for i in range(base, len(temp)):
            if temp[i]:
                return i
        return -1
    def counter(b: int, e: int):
        count = 0
        while b <= e:
            if merge[b].high == merge[b+1].high and merge[b].low == merge[b+1].low:
                pass
            else:
                count += 1
        return count
    def counter_nomerge(b: int, e: int):
        return (e - b + 1)
    def is_valid(i: int):
        bct = counter_nomerge(base, i)
        bmgt = counter(base, i)
        return not(bct<baseline or bmgt < norm)

def pre_(klines: List[Any], base: int):
    i = base
    while i > 0:
        if klines[i].high == klines[i - 1].high and klines[i - 1].low == klines[i].low:
            i -= 1
        else:
            return i - 1
    return -1


def Cal_MERGE(m_pData: List[KLine], m_MinPoint: int, m_MaxPoint: int):
    klines: List[KLine] = [m_pData[i] for i in range(m_MinPoint, m_MaxPoint)]
    for i in range(1, len(klines)):
        if ((klines[i].high >= klines[i - 1].high and klines[i].low <= klines[i-1].low) or
                (klines[i].high <= klines[i - 1].high and klines[i].low >= klines[i - 1].low)):
            if i == 1:  # 初始条件,首轮循环
                if klines[i].high > klines[i - 1].high:  # 全部取高的
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
                # 后包含 || 前包含 || 完全相等
                pre -= 1
                cur -= 1
                if pre < 0 or cur < 0:
                    break
            if pre < 0 or cur < 0:
                continue
            if ((klines[cur].high > klines[pre].high and klines[cur].low > klines[pre].low) or
                    (klines[cur].high == klines[pre].high and klines[cur].low > klines[pre].low)):
                # 高点低点都上移 || 高点不变，低点上移，up
                pre_index = pre_(klines, i-1)
                klines[i].high = klines[i-1].high = max(klines[i].high, klines[i-1].high)
                klines[i].low = klines[i-1].low = max(klines[i].low, klines[i-1].low)
                if pre_index < 0:
                    pass
                else:
                    for k in range(pre_index+1, i-1):
                        klines[k].high = klines[i].high
                        klines[k].low = klines[i].low
            elif ((klines[cur].high == klines[pre].high and klines[cur].low < klines[pre].low) or
                  (klines[cur].high) < klines[pre].high and klines[cur].low < klines[pre].low):
                # down
                pre_index = pre_(klines, i-1)
                klines[i].high = klines[i-1].high = min(klines[i].high, klines[i-1].high)
                klines[i].low = klines[i-1].low = min(klines[i].low, klines[i-1].low)
                if pre_index < 0:
                    pass
                else:
                    for k in range(pre_index+1, i-1):
                        klines[k].high = klines[i].high
                        klines[k].low = klines[i].low
    return klines




def _Cal_MERGE(combs: List[stCombineK]) -> int:
    """
    合并K线逻辑
    :param klines:
    :return:
    """
    size = len(combs)
    if len(combs) < 2:    # <=2时，返回本身的长度
        return size

    pBegin = 0
    pLast = pBegin
    pPrev = pBegin
    pCur = pBegin + 1
    pEnd = pBegin + size - 1

    bUp = True

    def IndependentK(combs: List[stCombineK], pCur: int, b_up: bool):
        """独立K线"""
        nonlocal bUp
        nonlocal pPrev
        nonlocal pLast
        bUp = b_up
        pPrev = pCur
        pLast += 1
        combs[pLast] = combs[pCur]
        return

    def ContainsK(combs: List[stCombineK], low, high, index, pos_end):
        """包含K线"""
        nonlocal pPrev
        combs[pLast].data.low = low
        combs[pLast].data.high = high
        combs[pLast].pos_end = pos_end
        combs[pLast].pos_extreme = index

        pPrev = pLast
        return

    if (greater_than_0(combs[pCur].data.high - combs[pPrev].data.high) and
            greater_than_0(combs[pCur].data.low - combs[pPrev].data.low)):
        IndependentK(combs, pCur, True)   # 独立K向上
    elif (less_than_0(combs[pCur].data.high - combs[pPrev].data.high) and
          less_than_0(combs[pCur].data.low - combs[pPrev].data.low)):
        IndependentK(combs, pCur, False)  # 独立K向下
    else:
        if (greater_than_0(combs[pCur].data.high - combs[pPrev].data.high) or
                less_than_0(combs[pCur].data.low - combs[pPrev].data.low)):
            ContainsK(combs, combs[pPrev].data.low, combs[pCur].data.high,
                      combs[pCur].pos_begin, combs[pCur].pos_begin)
        else:
            ContainsK(combs, combs[pCur].data.low, combs[pPrev].data.high,
                      combs[pPrev].pos_begin, combs[pCur].pos_begin)
    pCur += 1   # 当前索引+1

    while pCur <= pEnd:
        if greater_than_0(combs[pCur].data.high - combs[pPrev].data.high) and greater_than_0(combs[pCur].data.low - combs[pPrev].data.low):
            IndependentK(combs, pCur, True)   # 向上独立
        elif less_than_0(combs[pCur].data.high-combs[pPrev].data.high) and less_than_0(combs[pCur].data.low - combs[pPrev].data.low):
            IndependentK(combs, pCur, False)
        else:
            if greater_than_0(combs[pCur].data.high - combs[pPrev].data) or less_than_0(combs[pCur].data.low - combs[pPrev].data.low):
                if bUp:  # 右包含
                    index = combs[pPrev].pos_extreme if equ_than_0(combs[pCur].data.high - combs[pPrev].data.high) else combs[pCur].pos_begin
                    ContainsK(combs, combs[pCur].data.low, combs[pPrev].data.high, index, combs[pCur].pos_begin)
                else:
                    index = combs[pPrev].pos_extreme if equ_than_0(combs[combs[pCur].data.low - combs[pPrev].data.low]) else combs[pCur].pos_begin
                    ContainsK(combs, combs[pCur].data.low, combs[pPrev].data.high, index, combs[pCur].pos_begin)
            else:
                if bUp:  # 左包含
                    index = combs[pPrev].pos_begin if combs[pPrev].pos_begin == combs[pPrev].pos_end else combs[pPrev].pos_extreme
                    ContainsK(combs, combs[pCur].data.low, combs[pPrev].data.high, index, combs[pCur].pos_begin)
                else:
                    index = combs[pPrev].pos_begin if combs[pPrev].pos_begin == combs[pPrev].pos_end else combs[pPrev].pos_extreme
                    ContainsK(combs, combs[pPrev].data.low, combs[pCur].data.high, index, combs[pCur].pos_begin)
        pCur += 1

    return pLast - pBegin + 1


def Cal_UPPER(m_pData: List[KLine], m_MinPoint, m_MaxPoint) -> List[Tuple[bool,float,float]]:
    combs: List[stCombineK] = []
    for i in range(m_MinPoint, m_MaxPoint):
        data = stCombineK(m_pData[i], i, i, i, False)
        combs.append(data)

    nCount = _Cal_MERGE(combs)
    ret = [False] * len(combs)
    if nCount > 2:
        pPrevKline = combs[0]
        pCurKline = combs[1]
        pNextKline = combs[2]
        pEndKline = combs[-1]

        while pNextKline <= pEndKline:
            if pCurKline.data.high > pPrevKline.data.high and pCurKline.data.high > pNextKline.data.high and \
               pCurKline.data.low > pPrevKline.data.low and pCurKline.data.low > pNextKline.data.low:
                ret[pCurKline.pos_extreme] = True

            pPrevKline = pCurKline
            pCurKline = pNextKline
            pNextKline += 1

    return ret


def Cal_LOWER(m_pData: List[KLine], m_MinPoint, m_MaxPoint) -> List[bool]:
    klines: List[stCombineK] = []
    for i in range(m_MinPoint, m_MaxPoint):
        data = stCombineK(m_pData[i], i, i, i, True)
        klines.append(data)

    nCount = _Cal_MERGE(klines)
    ret = [False] * len(klines)
    if nCount > 2:
        pPrevKline = klines[0]
        pCurKline = klines[1]
        pNextKline = klines[2]
        pEndKline = klines[-1]

        while pNextKline <= pEndKline:
            if pCurKline.data.high < pPrevKline.data.high and pCurKline.data.high < pNextKline.data.high and \
               pCurKline.data.low < pPrevKline.data.low and pCurKline.data.low < pNextKline.data.low:
                ret[pCurKline.pos_extreme] = True

            pPrevKline = pCurKline
            pCurKline = pNextKline
            pNextKline += 1

    return ret


def Cal_OLDEN(m_pData: List[KLine]):
    lower = Cal_LOWER(m_pData)
    upper = Cal_UPPER(m_pData)
    merge = Cal_MERGE(m_pData)
    old_ = []
    temp = [0] * len(merge)

    # Function to find the highest point within the range of the same merge point
    def highly(base):
        max_ = base
        i = base - 1
        while i >= 0 and (merge[i].high == merge[base].high and merge[i].low == merge[base].low):
            max_ = i if m_pData[i].high > m_pData[max_].high else max_
            i -= 1

        i = base + 1
        while i < len(merge) and (merge[i].high == merge[base].high and merge[i].low == merge[base].low):
            max_ = i if m_pData[i].high > m_pData[max_].high else max_
            i += 1

        return max_

    # Function to find the lowest point within the range of the same merge point
    def lowly(base):
        min_ = base
        i = base - 1
        while i >= 0 and (merge[i].high == merge[base].high and merge[i].low == merge[base].low):
            min_ = i if m_pData[i].low < m_pData[min_].low else min_
            i -= 1

        i = base + 1
        while i < len(merge) and (merge[i].high == merge[base].high and merge[i].low == merge[base].low):
            min_ = i if m_pData[i].low < m_pData[min_].low else min_
            i += 1

        return min_

    # Function to convert index to the highest or lowest point
    def convert(i):
        if temp[i] < 0:
            return lowly(i)
        elif temp[i] > 0:
            return highly(i)
        else:
            return -1

    for i in range(len(temp)):
        if temp[i]:
            right = getNode(i, temp, merge, Trait.OLDEN)
            if right < 0:
                if right < -1:
                    old_.append((convert(right * -1), -2 if temp[i] > 0 else 2))
                break
            if not old_:
                ct = convert(i)
                if ct >= 0:
                    old_.append((ct, temp[i]))
                else:
                    break
            ct = convert(right)
            if ct >= 0:
                old_.append((convert(right), temp[right]))
            else:
                break
            i = right - 1

    return old_


def Cal_OLD_TEST(m_pData: List[KLine]):
    lower = Cal_LOWER(m_pData, 0, len(m_pData) - 1)