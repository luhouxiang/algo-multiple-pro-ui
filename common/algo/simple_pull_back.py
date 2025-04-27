"""简单回调"""
from typing import List, Optional
from common.model.kline import KLine, stBiK, KSide


def is_simple_pullback_after_strong(
    bi_list: List[stBiK],
    strong_bi_index: int,
    max_pullback_bi_count: int = 2,
    max_pullback_percent: float = 0.01
) -> bool:
    """
    检查在 strong_bi_index 之后的几笔，是否形成“简单回调”：
      - 回调笔数不超过 max_pullback_bi_count (如2笔)
      - 回调幅度不超过 max_pullback_percent (如1%)
      - 回调方向与强势笔相反
    返回 True/False
    """
    strong_bi = bi_list[strong_bi_index]
    # 强势笔方向
    if strong_bi.side == KSide.UP:
        # 回调就是向下
        pullback_side = KSide.DOWN
    else:
        pullback_side = KSide.UP

    # 拿到 strong_bi_index 后的笔
    next_bis = bi_list[strong_bi_index + 1:]
    if not next_bis:
        return False

    # 如果后面笔数多，则只取前若干笔看看
    # 例: 只允许最多2笔回调
    segment = next_bis[:max_pullback_bi_count]

    # 1) 确认这些笔都是相反方向
    for b in segment:
        if b.side != pullback_side:
            return False

    # 2) 检查回调幅度(简易定义):
    #    - 如果上一笔是UP, 强势涨幅参考 strong_bi 的lowest -> highest
    #    - 回调幅度看 segment中lowest -> highest
    #    - 你可以只看最末笔的最低点/最高点, 也可合并多笔.
    pull_low = min(b.lowest for b in segment)
    pull_high = max(b.highest for b in segment)

    if strong_bi.side == KSide.UP:
        # 强势笔涨幅
        up_range = (strong_bi.highest - strong_bi.lowest)
        # 回调差值(从 strong_bi.highest 到 pull_low)
        pull_range = strong_bi.highest - pull_low
        if pull_range / up_range > max_pullback_percent:
            return False
    else:
        # 强势笔下跌幅
        down_range = (strong_bi.highest - strong_bi.lowest)
        # 回调差值(从 strong_bi.lowest 到 pull_high)
        pull_range = pull_high - strong_bi.lowest
        if pull_range / down_range > max_pullback_percent:
            return False

    # 如果都符合, 认为出现了“简单回调”
    return True


def detect_strong_move_in_last_3(
        bi_list: List[stBiK],
        strong_percent_threshold: float = 0.02
) -> Optional[int]:
    """
    在bi_list的最近三笔(若不足3笔则取现有笔数)中,
    查找是否存在一笔“幅度”>= strong_percent_threshold(如2%)的强势运动;
    若找到, 返回其在 bi_list 中的索引; 否则返回 None.

    这里'幅度'的定义可随意:
      - 若是UP笔: (highest - lowest) / lowest >= strong_percent_threshold
      - 若是DOWN笔: (highest - lowest) / highest >= strong_percent_threshold
    """
    if not bi_list:
        return None

    start_idx = max(0, len(bi_list) - 3)
    segment = bi_list[start_idx:]  # 最近3笔

    # 从后往前搜索, 优先看最新笔
    for i in reversed(range(start_idx, len(bi_list))):
        bi = bi_list[i]
        if bi.side == KSide.UP:
            # 简易定义幅度
            if (bi.highest - bi.lowest) / (bi.lowest if bi.lowest != 0 else 1) >= strong_percent_threshold:
                return i
        elif bi.side == KSide.DOWN:
            if (bi.highest - bi.lowest) / (bi.highest if bi.highest != 0 else 1) >= strong_percent_threshold:
                return i

    return None



def check_simple_pullback_in_last_3_bi(bi_list: List[stBiK]) -> bool:
    """
    1) 检查最近三笔中是否有一笔非常强势(急速运动)
    2) 若找到, 再看后面那几笔是否形成简单回调
    3) 如都满足则返回 True, 否则 False
    """
    if len(bi_list) < 3:
        return False

    strong_bi_idx = detect_strong_move_in_last_3(bi_list, strong_percent_threshold=0.02)
    if strong_bi_idx is None:
        return False

    # 强笔后面是否出现简单回调?
    if is_simple_pullback_after_strong(bi_list, strong_bi_idx, max_pullback_bi_count=2, max_pullback_percent=0.01):
        return True

    return False
