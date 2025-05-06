import pandas as pd
import numpy as np
"""
您好！您描述的这种K线形态，通常被称为“平台突破回踩”或“旗形整理突破回踩”，是技术分析中一种较为经典的看涨信号。它通常包含以下几个阶段：

缓慢上涨阶段：股价或指数在一段时间内稳步上升，形成一个上升趋势。
震荡平台阶段：股价停止上涨，进入横盘整理，形成一个相对窄幅的震荡区间，这个区间就像旗杆上的旗帜，或者一个平台。这个阶段成交量通常会逐渐萎缩。
突破平台阶段：股价放量向上突破震荡平台的上轨。
回踩确认阶段：股价在突破后，可能会有一个向下跌破平台下轨的动作，测试平台下轨的支撑力度。如果平台下轨支撑有效，股价会再次反弹向上。
大涨阶段：如果回踩确认成功，股价通常会开启一轮新的上涨行情。
如何用算法识别震荡平台及平台回踩？

这是一个典型的模式识别问题，可以通过结合价格、成交量等数据，利用统计学和机器学习的方法来实现。以下是一些可能的算法思路：

一、识别震荡平台阶段：

基于价格波动率的识别：

标准差/方差：计算一段时间内收盘价的标准差或方差。当波动率显著低于前期上涨阶段，并且持续一段时间，可以初步判断为进入震荡平台。
布林带 (Bollinger Bands)：当布林带的上下轨之间的距离持续收窄，表明市场波动性降低，可能进入盘整阶段。
平均真实波幅 (ATR)：ATR指标衡量市场波动性。当ATR值持续走低，也可能意味着进入震荡平台。
基于价格区间的识别：

最高价/最低价通道：设定一个时间窗口（例如20个K线周期），计算窗口内的最高价和最低价。如果这些最高价和最低价在一段时间内变化不大，形成一个相对固定的区间，可以认为是震荡平台。
分位数回归：利用分位数回归来拟合一段时间内的价格上下轨，如果上下轨趋于水平，则可能是平台。
基于成交量的识别：

成交量萎缩：在震荡平台阶段，成交量通常会比之前的上涨阶段有所减少。可以计算移动平均成交量，观察其变化趋势。
结合指标：

ADX (Average Directional Index)：当ADX指标低于某个阈值（例如20或25）并且持续一段时间，表明市场处于无明显趋势的盘整状态。
动量指标 (Momentum)：例如ROC (Rate of Change)，当ROC在0轴附近小幅波动，也可能表示盘整。
算法实现步骤（以价格区间为例）：

数据预处理：获取K线数据（开盘价、收盘价、最高价、最低价、成交量）。
定义平台识别参数：
window_size：用于寻找平台的时间窗口大小。
platform_duration：平台持续的最小K线数量。
price_range_ratio_threshold：平台内价格波动幅度与平台均价的比率阈值（例如，（最高价-最低价）/均价 < 5%）。
滑动窗口检测：
在K线数据上滑动一个大小为 window_size 的窗口。
在每个窗口内，计算最高价 H 和最低价 L。
计算价格波动幅度 (H - L) 以及与均价的比率。
如果连续 platform_duration 个周期的窗口都满足 price_range_ratio_threshold 条件，并且最高价和最低价的变化不大，则可以初步判定为一个震荡平台。记录平台的上轨（近期高点）和下轨（近期低点）。
二、识别突破平台及回踩阶段：

识别突破：

当识别出震荡平台后，监测后续K线的收盘价。
如果某一根K线的收盘价 显著高于 平台定义的上轨（例如，上轨 + N倍ATR，或者价格高于上轨一定百分比），并且伴随 成交量放大（例如，成交量大于前N日平均成交量的M倍），则可以判断为向上突破。
识别回踩：

价格行为：在突破发生后，监测价格是否回落至前期平台的上轨附近或稍低于上轨。
支撑确认：观察价格在回踩到平台区域后，是否出现止跌企稳的信号，例如：
出现看涨的K线形态（如锤子线、启明之星等）。
成交量在下跌时缩小，在再次上涨时放大。
价格未能有效跌破平台下轨，或者跌破后迅速收回。
时间限制：回踩通常发生在突破后的几个交易日内，如果回踩时间过长，或者跌幅过深，则信号的有效性降低。
算法实现步骤（继续上面的例子）：

突破检测：
在平台形成后，监测后续K线。
如果 收盘价 > 平台高点 * (1 + breakthrough_margin) 并且 成交量 > 平均成交量 * volume_multiplier，则认为发生突破。
breakthrough_margin：突破幅度阈值。
volume_multiplier：成交量放大倍数阈值。
回踩检测：
突破后，监测价格是否回落到 平台高点 附近。
pullback_window：定义回踩发生的时间窗口。
在 pullback_window 内，如果 最低价 <= 平台高点 * (1 + pullback_tolerance) 并且 最低价 >= 平台高点 * (1 - pullback_tolerance) （其中 pullback_tolerance 是一个小的容忍范围），并且之后价格再次上涨，则认为回踩成功。
可以结合K线形态识别（例如，寻找在该区域出现的阳线或下影线）。
按此思路用python实现一个可用的平台突破回踩

ChatGPT 说：
要实现一个基于上述思路的平台突破回踩检测算法，首先需要以下几个步骤：数据预处理、震荡平台识别、突破检测、回踩检测。我们将逐步构建这个系统，下面给出Python代码的框架。

1. 数据预处理
首先，我们需要获取K线数据。假设我们已经有一个DataFrame（df）包含K线数据，包含open、close、high、low、volume等列。

2. 震荡平台检测
通过滑动窗口方法检测震荡平台，首先计算每个窗口的最高价、最低价，并判断价格波动幅度是否小于设定的阈值。

3. 突破检测
检测价格突破平台上轨时的情况，要求突破幅度和成交量放大。

4. 回踩检测
在突破后检测价格是否回踩至平台区间，并确认回踩支撑有效性。

代码实现
代码解释：
数据预处理：对K线数据按日期进行排序，确保时间顺序正确。

震荡平台检测：通过滑动窗口方法，计算每个窗口内的最高价和最低价，并判断其价格波动幅度是否符合震荡平台的特征。返回检测到的震荡平台区间。

突破检测：通过观察后续的K线，判断是否突破平台的上轨，且伴随成交量的放大。

回踩检测：在突破后，判断价格是否回踩至平台的上轨附近，并检查回踩是否有效（即是否出现支撑反弹的信号）。

调优：
可以调整window_size、price_range_ratio_threshold、breakthrough_margin、volume_multiplier等参数，来优化模型对于不同市场环境的适应性。

本例中的数据是随机生成的，在实际应用中，应使用真实的K线数据。

这种方法通过结合价格波动、成交量以及价格区间的变化来识别平台突破回踩模式，可以为技术分析和算法交易提供有力的支持。
"""

# 数据预处理
def preprocess_data(df):
    # 确保数据按日期排序
    # df = df.sort_values(by='date')
    return df


# 震荡平台检测
def detect_platform(df, window_size=20, price_range_ratio_threshold=0.05, platform_duration=3):
    platforms = []
    for i in range(len(df) - window_size):
        window = df.iloc[i:i + window_size]
        high = window['high'].max()
        low = window['low'].min()
        mean_price = window['close'].mean()
        price_range_ratio = (high - low) / mean_price

        if price_range_ratio < price_range_ratio_threshold:
            # 判断平台持续的时间
            if len(platforms) == 0 or (platforms[-1][1] + 1 == i):
                platforms.append((i, i + window_size))  # 记录平台起始和结束位置
            else:
                platforms[-1] = (platforms[-1][0], i + window_size)  # 延长平台
    return platforms


# 突破检测
def detect_breakout(df, platforms, breakthrough_margin=0.01, volume_multiplier=2):
    breakout_signals = []
    for platform in platforms:
        platform_data = df.iloc[platform[0]:platform[1]]
        platform_high = platform_data['high'].max()
        avg_volume = platform_data['volume'].mean()

        # 检测突破
        for i in range(platform[1], len(df)):
            if df.iloc[i]['close'] > platform_high * (1 + breakthrough_margin) and df.iloc[i][
                'volume'] > avg_volume * volume_multiplier:
                breakout_signals.append(i)
                break  # 只检测一次突破
    return breakout_signals


# 回踩检测
def detect_pullback(df, breakout_signals, pullback_window=5, pullback_tolerance=0.02):
    pullback_signals = []
    for signal in breakout_signals:
        breakout_price = df.iloc[signal]['close']
        platform_high = df.iloc[signal - 1]['high']  # 假设回踩是在突破前一天的高点回踩

        # 回踩检测
        for i in range(signal, min(signal + pullback_window, len(df))):
            if df.iloc[i]['low'] <= platform_high * (1 + pullback_tolerance) and df.iloc[i]['low'] >= platform_high * (
                    1 - pullback_tolerance):
                if df.iloc[i]['close'] > breakout_price:
                    pullback_signals.append(i)
                    break  # 只检测一次回踩
    return pullback_signals


# 主函数
def platform_breakout_pullback(df):
    df = preprocess_data(df)

    # 震荡平台检测
    platforms = detect_platform(df)
    print(f"Detected platforms: {platforms}")

    # 突破检测
    breakout_signals = detect_breakout(df, platforms)
    print(f"Breakout signals: {breakout_signals}")

    # 回踩检测
    pullback_signals = detect_pullback(df, breakout_signals)
    print(f"Pullback signals: {pullback_signals}")

    return platforms, breakout_signals, pullback_signals


# 示例数据加载
# 假设我们有一组K线数据
data = {
    'date': pd.date_range(start='2023-01-01', periods=100, freq='D'),
    'open': np.random.rand(100) * 100,
    'close': np.random.rand(100) * 100,
    'high': np.random.rand(100) * 100,
    'low': np.random.rand(100) * 100,
    'volume': np.random.rand(100) * 1000
}
df = pd.DataFrame(data)

# 运行主函数
platforms, breakout_signals, pullback_signals = platform_breakout_pullback(df)
