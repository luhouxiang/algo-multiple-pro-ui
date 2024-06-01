"""
z字型算法实现,通过gpt转换，还需用数据测试和验证，修正
"""
import numpy as np
from common.model.kline import KLine
# input parameters
InpDepth = 12
InpDeviation = 5
InpBackstep = 3
rates_total = 500  # 500根K线
_Point = 1  # 交易品种最小的价格单位，一般白糖为1

# indicator buffers
ZigZagBuffer = np.zeros(rates_total)
HighMapBuffer = np.zeros(rates_total)
LowMapBuffer = np.zeros(rates_total)

ExtRecalc = 3


# ZigZag calculation
def OnCalculate(k_arr: list[KLine]):
    """
    未完成状态，源自mt4的逻辑，暂先忽略
    """
    global ZigZagBuffer, HighMapBuffer, LowMapBuffer
    # rates_total, prev_calculated, time, open, high, low, close, tick_volume, volume, spread
    time = [k.time for k in k_arr]
    open = [k.open for k in k_arr]
    close = [k.close for k in k_arr]
    high = [k.high for k in k_arr]
    low = [k.low for k in k_arr]
    rates_total = prev_calculated = len(k_arr)
    if rates_total < 100:
        return 0

    start = 0
    extreme_counter = 0
    extreme_search = 0
    shift = 0
    back = 0
    last_high_pos = 0
    last_low_pos = 0
    curlow = 0
    curhigh = 0
    last_high = 0
    last_low = 0

    # if prev_calculated == 0:
    ZigZagBuffer = [0.0] * rates_total
    HighMapBuffer = [0.0] * rates_total
    LowMapBuffer = [0.0] * rates_total
    start = InpDepth

    if prev_calculated > 0:
        i = rates_total - 1
        while extreme_counter < ExtRecalc and i > rates_total - 100:
            res = ZigZagBuffer[i]
            if res != 0.0:
                extreme_counter += 1
            i -= 1
        i += 1
        start = i

        if LowMapBuffer[i] != 0.0:
            curlow = LowMapBuffer[i]
            extreme_search = 1
        else:
            curhigh = HighMapBuffer[i]
            extreme_search = -1

        for i in range(start + 1, rates_total):
            ZigZagBuffer[i] = 0.0
            LowMapBuffer[i] = 0.0
            HighMapBuffer[i] = 0.0

    for shift in range(start, rates_total):
        val = low[Lowest(low, InpDepth, shift)]
        if val == last_low:
            val = 0.0
        else:
            last_low = val
            if (low[shift] - val) > InpDeviation * _Point:
                val = 0.0
            else:
                for back in range(1, InpBackstep + 1):
                    res = LowMapBuffer[shift - back]
                    if (res != 0) and (res > val):
                        LowMapBuffer[shift - back] = 0.0
        if low[shift] == val:
            LowMapBuffer[shift] = val
        else:
            LowMapBuffer[shift] = 0.0

        val = high[Highest(high, InpDepth, shift)]
        if val == last_high:
            val = 0.0
        else:
            last_high = val
            if (val - high[shift]) > InpDeviation * _Point:
                val = 0.0
            else:
                for back in range(1, InpBackstep + 1):
                    res = HighMapBuffer[shift - back]
                    if (res != 0) and (res < val):
                        HighMapBuffer[shift - back] = 0.0
        if high[shift] == val:
            HighMapBuffer[shift] = val
        else:
            HighMapBuffer[shift] = 0.0

    if extreme_search == 0:
        last_low = 0.0
        last_high = 0.0
    else:
        last_low = curlow
        last_high = curhigh

    for shift in range(start, rates_total):
        res = 0.0
        if extreme_search == 0:
            if last_low == 0.0 and last_high == 0.0:
                if HighMapBuffer[shift] != 0:
                    last_high = high[shift]
                    last_high_pos = shift
                    extreme_search = -1
                    ZigZagBuffer[shift] = last_high
                    res = 1
                if LowMapBuffer[shift] != 0.0:
                    last_low = low[shift]
                    last_low_pos = shift
                    extreme_search = 1
                    ZigZagBuffer[shift] = last_low
                    res = 1
        elif extreme_search == 1:
            if LowMapBuffer[shift] != 0.0 and LowMapBuffer[shift] < last_low and HighMapBuffer[shift] == 0.0:
                ZigZagBuffer[last_low_pos] = 0.0
                last_low_pos = shift
                last_low = LowMapBuffer[shift]
                ZigZagBuffer[shift] = last_low
                res = 1
            if HighMapBuffer[shift] != 0.0 and LowMapBuffer[shift] == 0.0:
                last_high = HighMapBuffer[shift]
                last_high_pos = shift
                ZigZagBuffer[shift] = last_high
                extreme_search = -1
                res = 1
        elif extreme_search == -1:
            if HighMapBuffer[shift] != 0.0 and HighMapBuffer[shift] > last_high and LowMapBuffer[shift] == 0.0:
                ZigZagBuffer[last_high_pos] = 0.0
                last_high_pos = shift
                last_high = HighMapBuffer[shift]
                ZigZagBuffer[shift] = last_high
            if LowMapBuffer[shift] != 0.0 and HighMapBuffer[shift] == 0.0:
                last_low = LowMapBuffer[shift]
                last_low_pos = shift
                ZigZagBuffer[shift] = last_low
                extreme_search = 1
    return rates_total


# Search for the index of the highest bar
def Highest(array, depth, start):
    if start < 0:
        return 0

    max_val = array[start]
    index = start

    for i in range(start - 1, start - depth, -1):
        if array[i] > max_val:
            index = i
            max_val = array[i]

    return index


# Search for the index of the lowest bar
def Lowest(array, depth, start):
    if start < 0:
        return 0

    min_val = array[start]
    index = start

    for i in range(start - 1, start - depth, -1):
        if array[i] < min_val:
            index = i
            min_val = array[i]

    return index
