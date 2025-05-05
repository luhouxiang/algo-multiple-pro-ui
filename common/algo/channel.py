import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from sklearn.linear_model import LinearRegression


def identify_channel(data: pd.DataFrame,
                     lookback: int = 60,  # 回看周期（多少根K线）
                     prominence_ratio: float = 0.01,  # 峰谷点显著性（相对于价格范围）
                     slope_tolerance: float = 0.1,  # 斜率平行容忍度 (斜率差 / 平均绝对斜率)
                     horizontal_tolerance: float = 0.05,  # 水平通道斜率容忍度 (绝对值)
                     min_points: int = 3):  # 拟合直线所需的最少峰/谷点数
    """
    尝试识别K线数据中的通道模式。

    Args:
        data (pd.DataFrame): 包含 'High', 'Low', 'Close' 列的 K 线数据，索引应为时间序列。
        lookback (int): 用于识别通道的回看K线数量。
        prominence_ratio (float): 用于 find_peaks 的显著性参数，相对于回看期价格范围的比例。
        slope_tolerance (float): 两条线斜率差异容忍度，用于判断是否平行。
        horizontal_tolerance (float): 判断通道是否为水平的斜率绝对值上限。
        min_points (int): 拟合上轨线和下轨线所需的最小峰/谷点数。

    Returns:
        tuple: (channel_type, upper_line_params, lower_line_params, start_idx, end_idx)
               channel_type (str): "Ascending", "Descending", "Horizontal", "No Channel"
               upper_line_params (dict): {'slope': float, 'intercept': float, 'indices': list, 'values': list} or None
               lower_line_params (dict): {'slope': float, 'intercept': float, 'indices': list, 'values': list} or None
               start_idx (int): 通道的起始K线索引
               end_idx (int): 通道的结束K线索引
    """
    if len(data) < lookback:
        print(f"数据长度 {len(data)} 小于回看周期 {lookback}，无法分析。")
        return "No Channel", None, None, None, None

    df = data.iloc[-lookback:].copy()
    df['index_num'] = np.arange(len(df))  # 创建数值索引用于回归

    price_range = df['High'].max() - df['Low'].min()
    if price_range == 0:  # 避免除以零
        return "No Channel", None, None, None, None

    # 计算显著性阈值
    prominence_threshold = price_range * prominence_ratio

    # 1. 查找显著的高点 (Peaks) 和低点 (Troughs)
    peak_indices, _ = find_peaks(df['High'], prominence=prominence_threshold, distance=min_points)
    trough_indices, _ = find_peaks(-df['Low'], prominence=prominence_threshold, distance=min_points)  # 找负值的峰值即为原值的谷值

    # 筛选出在 lookback 周期内的有效峰谷点
    recent_peaks_idx = peak_indices
    recent_troughs_idx = trough_indices

    if len(recent_peaks_idx) < min_points or len(recent_troughs_idx) < min_points:
        return "No Channel", None, None, None, None

    # 准备回归数据
    X_peaks = df['index_num'].iloc[recent_peaks_idx].values.reshape(-1, 1)
    y_peaks = df['High'].iloc[recent_peaks_idx].values

    X_troughs = df['index_num'].iloc[recent_troughs_idx].values.reshape(-1, 1)
    y_troughs = df['Low'].iloc[recent_troughs_idx].values

    # 2. 线性回归拟合上下轨
    try:
        upper_reg = LinearRegression().fit(X_peaks, y_peaks)
        lower_reg = LinearRegression().fit(X_troughs, y_troughs)
    except ValueError as e:
        print(f"线性回归失败: {e}")
        return "No Channel", None, None, None, None

    upper_slope = upper_reg.coef_[0]
    upper_intercept = upper_reg.intercept_
    lower_slope = lower_reg.coef_[0]
    lower_intercept = lower_reg.intercept_

    # 3. 判断平行性和斜率
    avg_abs_slope = (abs(upper_slope) + abs(lower_slope)) / 2
    slope_diff = abs(upper_slope - lower_slope)

    # 检查是否足够平行
    is_parallel = False
    if avg_abs_slope > 1e-6:  # 避免除以非常小的数
        if slope_diff / avg_abs_slope < slope_tolerance:
            is_parallel = True
    elif slope_diff < slope_tolerance:
        is_parallel = True

    if not is_parallel:
        return "No Channel", None, None, None, None

    # 确定通道类型
    channel_type = "No Channel"
    avg_slope = (upper_slope + lower_slope) / 2

    if abs(avg_slope) < horizontal_tolerance:
        channel_type = "Horizontal"
    elif avg_slope > 0:
        channel_type = "Ascending"
    else:
        channel_type = "Descending"

    upper_params = {
        'slope': upper_slope, 'intercept': upper_intercept,
        'indices': X_peaks.flatten().tolist(), 'values': y_peaks.tolist()
    }
    lower_params = {
        'slope': lower_slope, 'intercept': lower_intercept,
        'indices': X_troughs.flatten().tolist(), 'values': y_troughs.tolist()
    }

    # 返回通道的起始和结束位置
    start_idx = df.index[recent_peaks_idx[0]]
    end_idx = df.index[recent_troughs_idx[-1]]

    return channel_type, upper_params, lower_params, start_idx, end_idx


def identify_channel2(data: pd.DataFrame,
                     lookback: int = 60,  # 回看周期（多少根K线）
                     prominence_ratio: float = 0.01,  # 峰谷点显著性（相对于价格范围）
                     slope_tolerance: float = 0.1,  # 斜率平行容忍度 (斜率差 / 平均绝对斜率)
                     horizontal_tolerance: float = 0.05,  # 水平通道斜率容忍度 (绝对值)
                     min_points: int = 3):  # 拟合直线所需的最少峰/谷点数
    """
    尝试识别K线数据中的通道模式。

    Args:
        data (pd.DataFrame): 包含 'High', 'Low', 'Close' 列的 K 线数据，索引应为时间序列。
        lookback (int): 用于识别通道的回看K线数量。
        prominence_ratio (float): 用于 find_peaks 的显著性参数，相对于回看期价格范围的比例。
        slope_tolerance (float): 两条线斜率差异容忍度，用于判断是否平行。
        horizontal_tolerance (float): 判断通道是否为水平的斜率绝对值上限。
        min_points (int): 拟合上轨线和下轨线所需的最小峰/谷点数。

    Returns:
        tuple: (channel_type, upper_line_params, lower_line_params, start_idx, end_idx)
               channel_type (str): "Ascending", "Descending", "Horizontal", "No Channel"
               upper_line_params (dict): {'slope': float, 'intercept': float, 'indices': list, 'values': list} or None
               lower_line_params (dict): {'slope': float, 'intercept': float, 'indices': list, 'values': list} or None
               start_idx (int): 通道的起始K线索引
               end_idx (int): 通道的结束K线索引
    """
    if len(data) < lookback:
        print(f"数据长度 {len(data)} 小于回看周期 {lookback}，无法分析。")
        return "No Channel", None, None, None, None

    df = data.iloc[-lookback:].copy()
    df['index_num'] = np.arange(len(df))  # 创建数值索引用于回归

    price_range = df['High'].max() - df['Low'].min()
    if price_range == 0:  # 避免除以零
        return "No Channel", None, None, None, None

    # 计算显著性阈值
    prominence_threshold = price_range * prominence_ratio

    # 1. 查找显著的高点 (Peaks) 和低点 (Troughs)
    peak_indices, _ = find_peaks(df['High'], prominence=prominence_threshold, distance=min_points)
    trough_indices, _ = find_peaks(-df['Low'], prominence=prominence_threshold, distance=min_points)  # 找负值的峰值即为原值的谷值

    # 筛选出在 lookback 周期内的有效峰谷点
    recent_peaks_idx = peak_indices
    recent_troughs_idx = trough_indices

    if len(recent_peaks_idx) < min_points or len(recent_troughs_idx) < min_points:
        return "No Channel", None, None, None, None

    # 准备回归数据
    X_peaks = df['index_num'].iloc[recent_peaks_idx].values.reshape(-1, 1)
    y_peaks = df['High'].iloc[recent_peaks_idx].values

    X_troughs = df['index_num'].iloc[recent_troughs_idx].values.reshape(-1, 1)
    y_troughs = df['Low'].iloc[recent_troughs_idx].values

    # 2. 线性回归拟合上下轨
    try:
        upper_reg = LinearRegression().fit(X_peaks, y_peaks)
        lower_reg = LinearRegression().fit(X_troughs, y_troughs)
    except ValueError as e:
        print(f"线性回归失败: {e}")
        return "No Channel", None, None, None, None

    upper_slope = upper_reg.coef_[0]
    upper_intercept = upper_reg.intercept_
    lower_slope = lower_reg.coef_[0]
    lower_intercept = lower_reg.intercept_

    # 3. 判断平行性和斜率
    avg_abs_slope = (abs(upper_slope) + abs(lower_slope)) / 2
    slope_diff = abs(upper_slope - lower_slope)

    # 检查是否足够平行
    is_parallel = False
    if avg_abs_slope > 1e-6:  # 避免除以非常小的数
        if slope_diff / avg_abs_slope < slope_tolerance:
            is_parallel = True
    elif slope_diff < slope_tolerance:
        is_parallel = True

    if not is_parallel:
        return "No Channel", None, None, None, None

    # 确定通道类型
    channel_type = "No Channel"
    avg_slope = (upper_slope + lower_slope) / 2

    if abs(avg_slope) < horizontal_tolerance:
        channel_type = "Horizontal"
    elif avg_slope > 0:
        channel_type = "Ascending"
    else:
        channel_type = "Descending"

    upper_params = {
        'slope': upper_slope, 'intercept': upper_intercept,
        'indices': X_peaks.flatten().tolist(), 'values': y_peaks.tolist()
    }
    lower_params = {
        'slope': lower_slope, 'intercept': lower_intercept,
        'indices': X_troughs.flatten().tolist(), 'values': y_troughs.tolist()
    }

    # 返回通道的起始和结束位置
    start_idx = df.index[recent_peaks_idx[0]]
    end_idx = df.index[recent_troughs_idx[-1]]

    return channel_type, upper_params, lower_params, start_idx, end_idx


def find_all_channels(data: pd.DataFrame, lookback: int = 60):
    """
    在K线数据中查找所有可能的通道段

    Args:
        data (pd.DataFrame): 包含 'High', 'Low', 'Close' 列的 K 线数据，索引应为时间序列。
        lookback (int): 用于识别通道的回看K线数量。

    Returns:
        list: 每个通道段的起始和结束位置及其类型
    """
    all_channels = []
    start_idx = 0
    while start_idx + lookback <= len(data):
        end_idx = start_idx + lookback
        segment = data.iloc[start_idx:end_idx]
        channel_type, upper_params, lower_params, segment_start, segment_end = identify_channel(segment, lookback)
        if channel_type != "No Channel":
            all_channels.append({
                'type': channel_type,
                'start_idx': segment_start,
                'end_idx': segment_end
            })
        start_idx = end_idx - 1  # 可以覆盖重叠窗口以捕捉更细致的通道形态
        # start_idx += 1
    return all_channels


def find_all_channels2(data: pd.DataFrame, lookback: int = 60):
    """
    在K线数据中查找所有可能的通道段

    Args:
        data (pd.DataFrame): 包含 'High', 'Low', 'Close' 列的 K 线数据，索引应为时间序列。
        lookback (int): 用于识别通道的回看K线数量。

    Returns:
        list: 每个通道段的起始和结束位置及其类型
    """
    all_channels = []
    start_idx = 0
    while start_idx + lookback <= len(data):
        end_idx = start_idx + lookback
        segment = data.iloc[start_idx:end_idx]
        channel_type, upper_params, lower_params, segment_start, segment_end = identify_channel(segment, lookback)
        if channel_type != "No Channel":
            all_channels.append({
                'type': channel_type,
                'start_idx': segment_start,
                'end_idx': segment_end
            })
        start_idx = end_idx - 1  # 可以覆盖重叠窗口以捕捉更细致的通道形态
        # start_idx += 1
    return all_channels


def find_all_channels2(data: pd.DataFrame, lookback: int = 60):
    """
    在K线数据中查找所有可能的通道段

    Args:
        data (pd.DataFrame): 包含 'High', 'Low', 'Close' 列的 K 线数据，索引应为时间序列。
        lookback (int): 用于识别通道的回看K线数量。

    Returns:
        list: 每个通道段的起始和结束位置及其类型
    """
    all_channels = []
    start_idx = 0
    while start_idx + lookback <= len(data):
        end_idx = start_idx + lookback
        segment = data.iloc[start_idx:end_idx]
        channel_type, upper_params, lower_params, segment_start, segment_end = identify_channel2(segment, lookback)
        if channel_type != "No Channel":
            all_channels.append({
                'type': channel_type,
                'start_idx': segment_start,
                'end_idx': segment_end
            })
        start_idx = end_idx - 1  # 可以覆盖重叠窗口以捕捉更细致的通道形态
    return all_channels