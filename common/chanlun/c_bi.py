# -*- coding: utf-8 -*-
"""
@author: <luhx>
@desc: 根据逻辑实现的缠论的笔
包含的处理：1 确定方向：如果第n根K线发生包含关系，找到第n-1根K线，此两根K线没有包含关系，且n-1及其之前的包含关系都处理完毕。
如果第n-1根K线到第n根K线，高点抬高，则方向为向上，反之，如果低点降低，则方向为向下。
2 合并K线：2根有包含关系的K线，如果方向向下，则取其中高点中的低点作为新K线高点，取其中低点中的低点作为新K线低点，由此合并出一根新K线。
如果方向向上，则取其中高点中的高点作为新K线高点，取其中低点中的高点作为新K线低点，由此合并出一根新K线。
"""
from common.model.kline import KLine, stCombineK, KSide, stFxK, stBiK, KExtreme, Segment, Pivot
from typing import List, Optional, Union
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
    for i in range(len(fractals)-1):
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
    # for item in old_:
    #     logging.info(f"[{item.index}]:{item.side}")
    bis = generate_bi(old_)
    return bis


def cal_independent_klines(pData: List[KLine]) -> List[stCombineK]:
    """
    计算出独立K线,返回独立K线对象列表
    """
    combs = _Cal_MERGE(pData)
    return combs


def find_first_segment(cur_pos: int, vtDisivion: List[stBiK], pData: List[KLine],
                       max_pos: int, min_pos: int, seg: Segment) -> bool:
    """
    线段一定被后一线段破坏、 且破坏前一线段
    由于第一根线段没有可破坏的线段，所以第一根线段 实际上是 从 第二根线段开始算
    """
    idx = vtDisivion[cur_pos].pos_begin
    if vtDisivion[cur_pos].side == KSide.UP:   # 向上
        max_idx = vtDisivion[max_pos].pos_begin
        if greater_than_0(pData[idx].high - pData[max_idx].high):
            max_pos = cur_pos
        if cur_pos - min_pos < 3:
            return False
        pre_idx = vtDisivion[cur_pos-2].pos_begin
        if greater_than_0(pData[idx].high - pData[pre_idx].high):
            idx = vtDisivion[cur_pos-1].pos_begin
            pre_idx = vtDisivion[cur_pos-3].pos_begin
            if greater_than_0(pData[idx].high - pData[pre_idx].high):
                # 暂时成段
                seg.start_index = min_pos
                seg.end_index = cur_pos
                seg.up = True
                return True
    else:
        # 第一段找最低的点作为向上段的起始点
        min_idx = vtDisivion[min_pos].pos_begin
        if less_than_0(pData[idx].low - pData[min_idx].low):
            min_pos = cur_pos
        if cur_pos - max_pos < 3:
            return False
        pre_idx = vtDisivion[cur_pos-2].pos_begin
        if less_than_0(pData[idx].low - pData[pre_idx].low):
            idx = vtDisivion[cur_pos-1].pos_begin
            pre_idx = vtDisivion[cur_pos-3].pos_begin
            if less_than_0(pData[idx].high - pData[pre_idx].high):
                seg.start_index = max_pos
                seg.end_index = cur_pos
                seg.up = False
                return True

    return False


def is_overlap(cur_pos: int, vtDisivion: List[stBiK], pData: List[KLine]) -> bool:
    if cur_pos < 3:
        return False
    # 判断连续三笔是否重叠
    idx = vtDisivion[cur_pos].pos_begin
    pre_idx = vtDisivion[cur_pos-3].pos_begin
    if vtDisivion[cur_pos].side == KSide.UP:    # 向下笔
        if less_than_0(pData[idx].high - pData[pre_idx].low):
            return False
    else:                                       # 向上笔
        if greater_than_0(pData[idx].low - pData[pre_idx].high):
            return False
    return True


def make_sure_low_segment(segment: Segment, cur_pos: int, vtDisivion: List[stBiK], pData: List[KLine]) -> int:
    status = -1
    while True:
        cur_idx = vtDisivion[cur_pos].pos_begin
        low_idx = vtDisivion[segment.end_index].pos_begin
        if vtDisivion[cur_pos].side == KSide.DOWN:
            # 更低
            if less_than_0(pData[cur_idx].low - pData[low_idx].low):
                segment.end_index = cur_pos
            break
        if cur_pos - segment.end_index < 3:
            break
        i = segment.end_index + 3
        end_pos = segment.end_index + 1
        for i in range(segment.end_index + 3, cur_pos + 1, 2):
            if not greater_than_0(pData[vtDisivion[i].pos_begin].high - pData[vtDisivion[end_pos].pos_begin].high):
                end_pos = i
                continue
            # 判断是否需要合并K线
            fMaxPrice = pData[vtDisivion[segment.start_index + 2].pos_begin].high
            fMinPrice = pData[vtDisivion[segment.start_index + 1].pos_begin].low
            for k in range(segment.start_index + 3, segment.end_index, 2):
                if less_than_0(fMinPrice - pData[vtDisivion[k].pos_begin].low):
                    if less_than_0(fMaxPrice - pData[vtDisivion[k+1].pos_begin].high):
                        fMinPrice = pData[vtDisivion[k].pos_begin].low
                    fMaxPrice = pData[vtDisivion[k+1].pos_begin].high
                else:
                    fMinPrice = pData[vtDisivion[k].pos_begin].low
                    fMaxPrice = pData[vtDisivion[k+1].pos_begin].high

            if less_than_0(pData[vtDisivion[end_pos].pos_begin].high - fMinPrice):
                # 存在缺口
                status = 1
            else:
                status = 0
            break
        break   # 走到这一步，即退出
    return status


def make_sure_up_segment(segment: Segment, cur_pos: int, vtDisivion: List[stBiK], pData: List[KLine]) -> int:
    status = -1
    while True:
        cur_idx = vtDisivion[cur_pos].pos_begin
        end_idx = vtDisivion[segment.end_index].pos_begin
        if vtDisivion[cur_pos].side == KSide.UP:
            if greater_than_0(pData[cur_idx].high - pData[end_idx].high):
                segment.end_index = cur_pos
            break

        if cur_pos - segment.end_index < 3:
            break

        end_pos = segment.end_index + 1
        for i in range(segment.end_index + 3, cur_pos + 1, 2):
            if not less_than_0(pData[vtDisivion[i].pos_begin].low - pData[vtDisivion[end_pos].pos_begin].low):
                end_pos = i
                continue
            fMaxPrice = pData[vtDisivion[segment.start_index + 1].pos_begin].high
            fMinPrice = pData[vtDisivion[segment.start_index + 2].pos_begin].low
            for k in range(segment.start_index+3, segment.end_index, 2):
                if greater_than_0(fMaxPrice - pData[vtDisivion[k].pos_begin].high):
                    if greater_than_0(fMinPrice - pData[vtDisivion[k+1].pos_begin].low):
                        fMaxPrice = pData[vtDisivion[k].pos_begin].high
                    fMinPrice = pData[vtDisivion[k+1].pos_begin].low
                else:
                    fMaxPrice = pData[vtDisivion[k].pos_begin].high
                    fMinPrice = pData[vtDisivion[k+1].pos_begin].low

            if greater_than_0(pData[vtDisivion[end_pos].pos_begin].low - fMaxPrice):
                status = 1
            else:
                status = 0
            break
        break
    return status


def make_sure_segment(segment: Segment, cur_pos: int, vtDisivion: List[stBiK], pData: List[KLine]):
    if segment.up:
        return make_sure_up_segment(segment, cur_pos, vtDisivion, pData)
    return make_sure_low_segment(segment, cur_pos, vtDisivion, pData)


def update_segment(cur_pos: int, seg: Segment, tmp_seg: Segment, vtDisivion: List[stBiK], ret: List[Segment], pData: List[KLine]):
    if tmp_seg.start_index == tmp_seg.end_index:
        status = make_sure_segment(seg, cur_pos, vtDisivion, pData)
        if status == -1:
            return
        if status == 0:
            # 不存在缺口
            seg.is_sure = True
            ret.append(copy.deepcopy(seg))

            seg.start_index = seg.end_index
            seg.end_index = cur_pos
            seg.is_sure = False
            seg.up = not seg.up
        elif status == 1:
            # 存在缺口
            tmp_seg.start_index = seg.end_index
            tmp_seg.end_index = cur_pos
            tmp_seg.is_sure = False
            tmp_seg.up = not seg.up
    else:
        status = make_sure_segment(tmp_seg, cur_pos, vtDisivion, pData)
        if status == -1:
            if vtDisivion[cur_pos].side == KSide.UP and not tmp_seg.up:
                if not tmp_seg.up:  # 这儿是否有逻辑漏洞？？？
                    if greater_than_0(pData[vtDisivion[cur_pos].pos_begin].high -
                                      pData[vtDisivion[tmp_seg.start_index].pos_begin].high):
                        seg.end_index = cur_pos
                        tmp_seg.start_index = tmp_seg.end_index = 0
            else:
                if tmp_seg.up:
                    if less_than_0(pData[vtDisivion[cur_pos].pos_begin].low -
                                   pData[vtDisivion[tmp_seg.start_index].pos_begin].low):
                        seg.end_index = cur_pos
                        tmp_seg.start_index = tmp_seg.end_index = 0
            return

        seg.is_sure = True
        ret.append(copy.deepcopy(seg))

        seg.is_sure = False
        if status == 0:
            # 不存在缺口
            tmp_seg.is_sure = True
            ret.append(copy.deepcopy(tmp_seg))

            seg.start_index = tmp_seg.end_index
            seg.end_index = cur_pos
            seg.is_sure = False
            seg.up = not tmp_seg.up

            tmp_seg.start_index = tmp_seg.end_index = 0
        elif status == 1:
            # 存在缺口
            seg.start_index = tmp_seg.start_index
            seg.end_index = tmp_seg.end_index
            seg.up = tmp_seg.up

            tmp_seg.start_index = seg.end_index
            tmp_seg.end_index = cur_pos
            tmp_seg.up = not seg.up


def _NCHDUAN(vtDisivion: List[stBiK], pData: List[KLine]) -> List[Segment]:
    # vtDisivion = copy.deepcopy(tDisivion)
    """计算线段"""
    for item in vtDisivion:
        item.side = KSide.UP if item.side == KSide.DOWN else KSide.DOWN
    ret: List[Segment] = []
    min_pos = -1
    max_pos = -1
    seg, tmp_seg = Segment(), Segment()
    status = 0
    nSize = len(vtDisivion)
    for i in range(3, nSize):
        if status == 0:
            if not is_overlap(i, vtDisivion, pData):
                min_pos = max_pos = -1
                continue
            if min_pos == -1:
                min_pos = max_pos = i - 3
                for k in range(i-2, i):
                    if greater_than_0(pData[vtDisivion[k].pos_begin].high - pData[vtDisivion[max_pos].pos_begin].high):
                        max_pos = k
                    if less_than_0(pData[vtDisivion[k].pos_begin].low - pData[vtDisivion[min_pos].pos_begin].low):
                        min_pos = k
            if not find_first_segment(i, vtDisivion, pData, max_pos, min_pos, seg):
                continue

            status = 1
            min_pos = max_pos = 1
            continue
        update_segment(i, seg, tmp_seg, vtDisivion, ret, pData)

    if seg.start_index != seg.end_index:
        ret.append(copy.deepcopy(seg))
    if tmp_seg.start_index != tmp_seg.end_index:
        ret.append(copy.deepcopy(tmp_seg))

    for iter in ret:
        if iter.up:
            iter.lowest = vtDisivion[iter.start_index].lowest
            iter.highest = vtDisivion[iter.end_index].highest
        else:
            iter.lowest = vtDisivion[iter.end_index].lowest
            iter.highest = vtDisivion[iter.start_index].highest

        iter.pos_begin = vtDisivion[iter.start_index].pos_begin
        iter.pos_end = vtDisivion[iter.end_index].pos_begin


    if len(ret) > 0:
        ret.pop(0)

    return ret


def get_anchors(seg: Segment, bi_list: List[stBiK]) -> List[int]:
    """获取线段内的笔索引列表"""
    anchors = []
    for i, bi in enumerate(bi_list):
        if bi.pos_begin >= seg.start_index and bi.pos_end <= seg.end_index:
            anchors.append(i)
    return anchors


# def compute_pivots_in_segment(seg: Segment, anchors: List[int], bi_list: List[stBiK]) -> List[Pivot]:
#     """在单个线段内计算标准中枢"""
#     pivots = []
#     # 至少需要5个锚点才能形成一个中枢
#     if len(anchors) > 4:
#         base = 1  # 从第二个锚点开始
#         while base < len(anchors) - 2:
#             pivot = Pivot()
#             if not seg.up:
#                 # 向下线段
#                 # 检查当前锚点是否为底分型（即笔的方向为向下）
#                 if bi_list[anchors[base]].side == KSide.DOWN:
#                     # 检查重叠条件：第二个顶 > 第一个底
#                     if base + 3 < len(anchors) and bi_list[anchors[base + 3]].highest > bi_list[anchors[base]].lowest:
#                         # 起点：第一个底
#                         pivot.bg = anchors[base]
#                         # 最高点：第一个顶与第二个顶的较低者
#                         first_top = bi_list[anchors[base + 1]]
#                         second_top = bi_list[anchors[base + 3]]
#                         pivot.highly = anchors[base + 1] if first_top.highest < second_top.highest else anchors[base + 3]
#                         # 最低点：第一个底与第二个底的较高者
#                         first_bottom = bi_list[anchors[base]]
#                         second_bottom = bi_list[anchors[base + 2]]
#                         pivot.lowly = anchors[base] if first_bottom.lowest > second_bottom.lowest else anchors[base + 2]
#                         # 终点：寻找第N个顶，当其低于第一个底时，终点为第(N-1)个顶
#                         pivot.ed = anchors[base + 3]
#                         bFindEnd = False
#                         i = base + 5
#                         while i < len(anchors):
#                             if bi_list[anchors[i]].highest < bi_list[anchors[base]].lowest:
#                                 pivot.ed = anchors[i - 2]
#                                 base = i - 1
#                                 bFindEnd = True
#                                 break
#                             i += 2
#                         if not bFindEnd:
#                             pivot.ed = anchors[-2]
#                         pivot.up = False
#                         pivots.append(pivot)
#                         if not bFindEnd:
#                             break  # 未找到终点，退出
#                     else:
#                         base += 2  # 找下一个底分型
#                 else:
#                     break  # 非底分型，无法继续
#             else:
#                 # 向上线段
#                 # 检查当前锚点是否为顶分型（即笔的方向为向上）
#                 if bi_list[anchors[base]].side == KSide.UP:
#                     # 检查重叠条件：第二个底 < 第一个顶
#                     if base + 3 < len(anchors) and bi_list[anchors[base + 3]].lowest < bi_list[anchors[base]].highest:
#                         # 起点：第一个顶
#                         pivot.bg = anchors[base]
#                         # 最高点：第一个顶与第二个顶的较低者
#                         first_top = bi_list[anchors[base]]
#                         second_top = bi_list[anchors[base + 2]]
#                         pivot.highly = anchors[base] if first_top.highest < second_top.highest else anchors[base + 2]
#                         # 最低点：第一个底与第二个底的较高者
#                         first_bottom = bi_list[anchors[base + 1]]
#                         second_bottom = bi_list[anchors[base + 3]]
#                         pivot.lowly = anchors[base + 1] if first_bottom.lowest > second_bottom.lowest else anchors[base + 3]
#                         # 终点：寻找第N个底，当其高于第一个顶时，终点为第(N-1)个底
#                         pivot.ed = anchors[base + 3]
#                         bFindEnd = False
#                         i = base + 5
#                         while i < len(anchors):
#                             if bi_list[anchors[i]].lowest > bi_list[anchors[base]].highest:
#                                 pivot.ed = anchors[i - 2]
#                                 base = i - 1
#                                 bFindEnd = True
#                                 break
#                             i += 2
#                         if not bFindEnd:
#                             pivot.ed = anchors[-2]
#                         pivot.up = True
#                         pivots.append(pivot)
#                         if not bFindEnd:
#                             break  # 未找到终点，退出
#                     else:
#                         base += 2  # 找下一个顶分型
#                 else:
#                     break  # 非顶分型，无法继续
#             base += 1
#     return pivots
def process_down_segment(base: int, anchors: List[int], bi_list: List[stBiK]) -> Tuple[Optional[Pivot], int, bool]:
    """处理向下线段内的中枢计算。
    """
    pivot = Pivot()
    # 检查当前锚点是否为底分型（即笔的方向为向下）
    if bi_list[anchors[base]].side == KSide.DOWN:
        # 检查重叠条件：第二个顶 > 第一个底
        if base + 3 < len(anchors) and bi_list[anchors[base + 3]].highest > bi_list[anchors[base]].lowest:
            # 起点：第一个底
            pivot.highly_value = min(bi_list[anchors[base + 1]].highest, bi_list[anchors[base + 3]].highest)
            pivot.lowly_value = max(bi_list[anchors[base]].lowest, bi_list[anchors[base + 2]].lowest)
            # 初始化终点为第二个顶
            pivot.bg_pos_index = bi_list[anchors[base]].pos_begin
            pivot.ed_pos_index = bi_list[anchors[base + 3]].pos_end
            bFindEnd = False
            i = base + 5
            # 寻找中枢的终点
            while i < len(anchors):
                # 当第N个顶的最高点低于第一个底的最低点时，终点为第(N-1)个顶
                if bi_list[anchors[i]].highest < bi_list[anchors[base]].lowest:
                    pivot.ed_pos_index = bi_list[anchors[i - 2]].pos_end
                    base = i - 1  # 更新基准点为上一个底分型
                    bFindEnd = True
                    break
                i += 2  # 只需检查顶分型
            if not bFindEnd:
                pivot.ed_pos_index = bi_list[anchors[-2]].pos_end  # 未找到终点，终点为倒数第二个锚点
            pivot.up = False
            return pivot, base, not bFindEnd
        else:
            base += 2  # 移动到下一个底分型
            return None, base, True
    else:
        # 当前锚点不是底分型，无法继续
        return None, base, False


def process_up_segment(base: int, anchors: List[int], bi_list: List[stBiK]) -> Tuple[Optional[Pivot], int, bool]:
    """处理向上线段内的中枢计算。

    Args:
        base (int): 当前基准锚点索引。
        anchors (List[int]): 锚点列表。
        bi_list (List[stBiK]): 笔列表。

    Returns:
        Tuple[Optional[Pivot], int, bool]: 返回元组 (pivot, updated_base, should_continue)。
            - pivot: 如果找到中枢，则为 Pivot 对象；否则为 None。
            - updated_base: 更新后的基准锚点索引。
            - should_continue: 是否继续主循环。
    """
    pivot = Pivot()
    # 检查当前锚点是否为顶分型（即笔的方向为向上）
    if bi_list[anchors[base]].side == KSide.UP:
        # 检查重叠条件：第二个底 < 第一个顶
        if base + 3 < len(anchors) and bi_list[anchors[base + 3]].lowest < bi_list[anchors[base]].highest:
            pivot.highly_value = min(bi_list[anchors[base]].highest, bi_list[anchors[base + 2]].highest)
            pivot.lowly_value = max(bi_list[anchors[base + 1]].lowest, bi_list[anchors[base + 3]].lowest)

            pivot.bg_pos_index = bi_list[anchors[base]].pos_begin
            pivot.ed_pos_index = bi_list[anchors[base+3]].pos_end
            bFindEnd = False
            i = base + 5
            # 寻找中枢的终点
            while i < len(anchors):
                # 当第N个底的最低点高于第一个顶的最高点时，终点为第(N-1)个底
                if bi_list[anchors[i]].lowest > bi_list[anchors[base]].highest:
                    pivot.ed_pos_index = bi_list[anchors[i - 2]].pos_end
                    base = i - 1  # 更新基准点为上一个顶分型
                    bFindEnd = True
                    break
                i += 2  # 只需检查底分型
            if not bFindEnd:
                pivot.ed_pos_index = bi_list[anchors[-2]].pos_end  # 未找到终点，终点为倒数第二个锚点
            pivot.up = True
            return pivot, base, not bFindEnd
        else:
            base += 2  # 移动到下一个顶分型
            return None, base, True
    else:
        # 当前锚点不是顶分型，无法继续
        return None, base, False


def intervals_overlap(a, b, c, d):
    """要判断两个区间 [a, b] 和 [c, d] 是否有重叠"""
    return max(a, c) <= min(b, d)


def three_intervals_overlap(a, b, c, d, e, f):
    # 检查三个区间中任意两个区间是否有重叠
    return intervals_overlap(a, b, c, d) and intervals_overlap(a, b, e, f) and intervals_overlap(c, d, e, f)


def process_down_up(base: int, bis: Union[List[stBiK], List[Segment]]) -> Tuple[Optional[Pivot], int]:
    """
    尝试从 base 开始识别一个中枢，要求至少三笔重叠。
    注：中枢的方向由第一笔的方向决定。

    步骤：
    1. 检查 base 与 base+2 的笔是否有重叠，如果无重叠，直接跳过。
    2. 若三笔重叠成功，则把这三笔的重叠区间确定为中枢初始区间，然后尝试继续向后扩展。
    3. 在扩展过程中，每新增一笔（顶或底）必须与中枢区间重叠，否则终止扩展。
    4. 最后根据第一笔的方向确定中枢方向。
    """
    def shift_base_by_2(b: int) -> Tuple[Optional[Pivot], int]:
        """向后移动 base 并返回通用三元组。"""
        new_base = b + 2
        if new_base >= len(bis):
            return None, len(bis)
        return None, new_base

    # 若不满足至少 base+2，无法形成三笔
    if base + 2 >= len(bis):
        return None, len(bis)

    # 1) 检查第一与第三笔 (base, base+2) 是否重叠
    if not intervals_overlap(bis[base].lowest, bis[base].highest,
                             bis[base+2].lowest, bis[base+2].highest):
        return shift_base_by_2(base)  # 重叠失败，移动 base 到下一个可能位置

    # 第一组重叠区间
    low_val = max(bis[base].lowest,  bis[base+2].lowest)
    high_val = min(bis[base].highest, bis[base+2].highest)

    pivot = Pivot()
    # 根据第一笔的方向确定中枢的方向
    pivot.up = (bis[base].side == KSide.UP)

    pivot.lowly_value = low_val
    pivot.highly_value = high_val
    pivot.bg_pos_index = bis[base].pos_begin
    pivot.ed_pos_index = bis[base+2].pos_end

    # 从 base+4 开始继续扩展
    i = base + 4
    while i < len(bis):
        if not intervals_overlap(pivot.lowly_value, pivot.highly_value, bis[i].lowest, bis[i].highest):
            break
        pivot.ed_pos_index = bis[i].pos_end
        # pivot.lowly_value = max(pivot.lowly_value, bis[i].lowest)
        # pivot.highly_value = min(pivot.highly_value, bis[i].highest)
        i += 2  # 跳过下一笔（底、顶交替）

    # 更新 base 为中枢结束后的位置
    base = i

    return pivot, base



def compute_bi_pivots(bi_list: List[stBiK]) -> List[Pivot]:
    """
    计算笔中枢：
    要求至少三笔形成重叠才能称为中枢。
    """
    pivots = []
    # 至少需要足够的笔长度（判断3笔重叠最少需要3根笔：base, base+2）
    if len(bi_list) < 5:
        return pivots

    base = 1  # 从第二个锚点开始尝试
    while base < len(bi_list) - 2:  # 至少留足够空间检查 base+4
        pivot, new_base = process_down_up(base, bi_list)
        if pivot:
            pivots.append(pivot)
        if base == new_base - 2:
            base = new_base - 1
        else:
            base = new_base - 2

    return pivots


def compute_duan_pivots(seg_list: List[Segment]) -> List[Pivot]:
    """
    计算段中枢：
    要求至少三笔形成重叠才能称为中枢。
    """
    pivots = []
    # 至少需要足够的笔长度（判断3笔重叠最少需要3根笔：base, base+2）
    if len(seg_list) < 5:
        return pivots

    base = 1  # 从第二个锚点开始尝试
    while base < len(seg_list) - 2:  # 至少留足够空间检查 base+4
        pivot, new_base = process_down_up(base, seg_list)
        if pivot:
            pivots.append(pivot)
        if base == new_base - 2:
            base = new_base - 1
        else:
            base = new_base - 2

    return pivots



def compute_pivots_in_segment(seg: Segment, anchors: List[int], bi_list: List[stBiK]) -> List[Pivot]:
    """计算单个线段内的标准中枢。"""
    pivots = []
    # 至少需要5个锚点才能形成一个中枢
    if len(anchors) > 4:
        base = 1  # 从第二个锚点开始
        while base < len(anchors) - 2:
            if not seg.up:
                # 处理向下线段
                pivot, base, should_continue = process_down_segment(base, anchors, bi_list)
                if pivot:
                    pivots.append(pivot)
                if not should_continue:
                    break  # 未找到终点，退出循环
                base += 1  # 移动到下一个锚点
            else:
                # 处理向上线段
                pivot, base, should_continue = process_up_segment(base, anchors, bi_list)
                if pivot:
                    pivots.append(pivot)
                if not should_continue:
                    break  # 未找到终点，退出循环
                base += 1  # 移动到下一个锚点
    return pivots





