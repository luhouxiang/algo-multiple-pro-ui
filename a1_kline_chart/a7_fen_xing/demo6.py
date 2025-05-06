import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
"""
平台检测可以换一种逻辑，高点接近水平线，低点逐渐上移，形成一个初始看起来像是矩形，渐次低点向上抬升走到矩形中上部样子，按此逻辑，使用python实现平台突破的代码

ChatGPT 说：
根据您提供的新的平台检测逻辑，我们可以将平台视为一个“矩形”区域，其中高点接近水平线，而低点逐渐上移，最终形成一个顶部接近水平的形态。这种模式类似于“上升三角形”或“矩形整理”形态。

新的逻辑：
高点接近水平线：计算一定时间窗口内的最大值，判断这些高点接近水平线。

低点逐渐上移：随着时间的推移，最低点应该逐渐上移，可以使用趋势检测方法来判断这一特性。

矩形平台形态：通过这两种特征来识别震荡平台。

代码实现思路：
计算每个时间窗口的高点和低点。

判断高点是否接近水平线，低点是否逐渐上升。

确定平台的开始和结束时间段。

Python代码实现：
代码解释：
is_horizontal函数：通过计算窗口内高点的标准差，如果标准差小于设定的阈值，则认为这些高点接近水平线。

is_ascending函数：检查低点是否逐渐上升。使用np.diff计算低点的变化，并确保每个低点都高于前一个低点。

detect_platform函数：通过滑动窗口，判断每个窗口是否符合平台形态的条件——即高点接近水平线且低点逐渐上升，同时价格波动幅度较小，符合震荡平台的特征。

突破检测和回踩检测：与前面的实现类似，基于价格突破和回踩条件来进行信号的判断。

可视化：
在最后，我们使用matplotlib对结果进行可视化。黄色区域表示检测到的平台，绿色虚线表示突破信号，红色虚线表示回踩信号。

调优：
您可以根据实际数据调整参数，例如threshold（用于判断高点接近水平线的标准差阈值）和price_range_threshold（用于限制震荡平台的价格波动幅度）。
"""

# 数据预处理
def preprocess_data(df):
    # 确保数据按日期排序
    df = df.sort_values(by='date')
    return df


# 判断高点是否接近水平线
def is_horizontal(highs, threshold=0.02):
    # 计算高点的标准差，若小于阈值，则认为是接近水平线
    return np.std(highs) < threshold


# 判断低点是否逐渐上移
def is_ascending(lows, threshold=0.02):
    # 计算低点的变化率，若变化率小于阈值，认为低点逐渐上升
    diffs = np.diff(lows)
    return np.all(diffs > threshold)  # 确保每个低点都高于前一个低点


# 确定平台的识别
def detect_platform(df, window_size=20, price_range_threshold=0.05, platform_duration=3):
    platforms = []
    for i in range(len(df) - window_size):
        window = df.iloc[i:i + window_size]
        highs = window['high'].values
        lows = window['low'].values
        mean_price = window['close'].mean()

        # 判断高点接近水平线，低点是否逐渐上升
        if is_horizontal(highs) and is_ascending(lows):
            # 计算价格波动幅度，若小于某个阈值，则认为是一个震荡平台
            price_range = (highs.max() - lows.min()) / mean_price
            if price_range < price_range_threshold:
                platforms.append((i, i + window_size))  # 记录平台起始和结束位置
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

# 可视化结果
plt.figure(figsize=(12, 6))
plt.plot(df['date'], df['close'], label='Close Price')
for platform in platforms:
    plt.axvspan(df['date'].iloc[platform[0]], df['date'].iloc[platform[1]], color='yellow', alpha=0.5)
for signal in breakout_signals:
    plt.axvline(df['date'].iloc[signal], color='green', linestyle='--', label='Breakout')
for signal in pullback_signals:
    plt.axvline(df['date'].iloc[signal], color='red', linestyle='--', label='Pullback')
plt.legend()
plt.show()


