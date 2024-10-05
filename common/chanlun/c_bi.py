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


def _Cal_MERGE_COUNT(combs: List[stCombineK]) -> int:
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
    return pLast - pBegin + 1   # 得出独立K线的数量


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



def sort_fractal(lower: List[stFxK], upper: List[stFxK]):
    """将顶分型和底分型合并成分型列表，并按索引升序排序"""
    merged_list = lower + upper
    merged_list = [i for i in merged_list if i.side != KExtreme.NORMAL]
    merged_list.sort(key=lambda x: x.index)
    return merged_list


def select_stronger_fractal(f1: stFxK, f2: stFxK):
    """
    选择更强的分型：
    - 对于顶分型，选择较高的 high 值
    - 对于底分型，选择较低的 low 值
    """
    if f1.side == KExtreme.TOP:
        return f1 if f1.highest > f2.highest else f2
    elif f1.side == KExtreme.BOTTOM:
        return f1 if f1.lowest < f2.lowest else f2
    else:
        return f1  # 如果类型不明，保留第一个


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

def process_fractal(fractals: List[stFxK], combs: List[stCombineK]) -> List[stFxK]:
    """
    处理分型列表，消除不符合条件的分型，返回处理后的分型列表
    """
    if not fractals:
        return []
    independents: Dict[int, int] = {}
    for i in range(len(combs)):
        for j in range(combs[i].pos_begin, combs[i].pos_end+1):
            independents[j] = i  # 表达出索引pos_begin至pos_end实际上是第i根独立K线

    processed = [fractals[0]]  # 初始化处理后的分型列表
    for next_fractal in fractals[1:]:
        last_fractal = processed[-1]
        if next_fractal.side == last_fractal.side:
            # 处理相同类型的相邻分型
            stronger_fractal = select_stronger_fractal(last_fractal, next_fractal)
            processed[-1] = stronger_fractal
        else:
            # 处理不同类型的相邻分型
            if is_valid_fx(independents, last_fractal.index, next_fractal.index):
                processed.append(next_fractal)
            else:
                continue    # 跳过不符合条件的分型
    return processed



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




def calculate_bi2(lower: List[stFxK], upper: List[stFxK], combs: List[stCombineK]) -> List[stBiK]:
    """计算笔"""
    merged_fractals = sort_fractal(lower, upper)
    processed_fractals = process_fractal(merged_fractals, combs)
    bis = generate_bi(processed_fractals)
    return bis
    # print(bis)


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


def counter_merge(b, e, merge: List[stCombineK]):
    """计算出独立K线的根数"""
    count = 0
    while b <= e:
        if merge[b].range_high == merge[e].range_high and merge[b].range_low == merge[e].range_low:
            pass
        else:
            count += 1
        b += 1
    return count


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
    # for i in range(len(temp)):
    #
    # merged_fractals = sort_fractal(lower, upper)
    # processed_fractals = process_fractal(merged_fractals, combs)
    # bis = generate_bi(processed_fractals)
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
    combs = [stCombineK(pData[i].low, pData[i].high, i, i, i, KSide.DOWN) for i in range(len(pData))]
    nCount = _Cal_MERGE_COUNT(combs)
    if nCount <= 2:
        return combs[:nCount]
    arr = combs[:nCount]
    # logging.info(f"begin...{'*' * 80}")
    # for i in arr:
    #     logging.info(f"{i.pos_begin},{i.pos_end},{i.pos_extreme},"
    #                  f"{i.isUp.value},{str(datetime.fromtimestamp(i.data.time))},"
    #                  f"o={i.data.open},h={i.data.high},l={i.data.low},c={i.data.close}")
    # logging.info(f"end.{'*' * 80}")
    return arr


# def Cal_Merge(pData: List[KLine]) -> List[stCombineK]:
#     """
#     计算出独立K线,返回独立K线对象列表
#     """
#     combs = [stCombineK(pData[i].low, pData[i].high, i, i, i, KSide.DOWN) for i in range(len(pData))]
#     nCount = _Cal_MERGE(combs)
#     if nCount <= 2:
#         return combs[:nCount]
#     arr = combs[:nCount]
#
#     rel = [stCombineK(0, 0, i, i, i, KSide.Init) for i in range(len(pData))]
#
#     for i in arr:
#         rel[i.pos_extreme] = i
#     return rel



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
















