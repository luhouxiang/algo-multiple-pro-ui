import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from scipy.stats import linregress
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


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


def find_channels_constrained(df, window=30, min_touches=2, slope_tolerance=0.1, proximity_threshold_pct=0.01,
                              min_duration=10, slope_req_tolerance=0.05):
    """
    在 K 线数据中识别价格通道，带有起始点限制。
    - 上升通道: 第一个低点必须是窗口起始K线的低点。
    - 下降通道: 第一个高点必须是窗口起始K线的高点。

    Args:
        df (pd.DataFrame): 包含 'High' 和 'Low' 列的 K 线数据。
        window (int): 滑动窗口大小。
        min_touches (int): 有效趋势线的最少触点数 (包括起始点)。
        slope_tolerance (float): 两条趋势线斜率允许的最大相对差异。
        proximity_threshold_pct (float): 点接触趋势线的距离阈值 (占价格百分比)。
        min_duration (int): 通道有效所需的最短 K 线数量。
        slope_req_tolerance(float): 允许斜率偏离理想方向(上/下)的容忍度
                                     (例如，允许上升通道斜率稍微为负)。

    Returns:
        list: 包含元组 (start_index, end_index, type) 的列表，
              type 为 'up' 或 'down'。
    """
    channels = []
    n = len(df)
    if n < window or n < min_duration:
        return channels

    # 使用整数索引进行计算
    original_index = df.index  # 保存原始索引
    df = df.reset_index(drop=True)  # 使用 0-based 整数索引
    time_indices = np.arange(n)

    for i in range(n - window + 1):
        end_window = i + window
        if end_window > n:  # 确保窗口不越界 (理论上不会，但保险起见)
            continue

        sub_df = df.iloc[i:end_window]
        sub_indices = time_indices[i:end_window]

        highs = sub_df['High'].values
        lows = sub_df['Low'].values
        current_avg_price = (highs.mean() + lows.mean()) / 2
        proximity_threshold = current_avg_price * proximity_threshold_pct

        # 找到窗口内所有显著的峰谷 (相对于窗口的局部索引)
        # prominence 选取需要调试
        peak_indices_local, _ = find_peaks(highs, prominence=highs.std() * 0.1)
        trough_indices_local, _ = find_peaks(-lows, prominence=lows.std() * 0.1)

        # --- 检查向上通道 ---
        # 条件1: 第一个K线的低点必须是支撑线的一部分
        # 将第一个点的索引(0)和价格加入到谷值点集合中用于拟合
        trough_indices_for_fit_local = np.unique(np.concatenate(([0], trough_indices_local)))

        if len(trough_indices_for_fit_local) >= min_touches and len(peak_indices_local) >= min_touches:
            trough_global_indices = sub_indices[trough_indices_for_fit_local]
            trough_prices = lows[trough_indices_for_fit_local]
            peak_global_indices = sub_indices[peak_indices_local]
            peak_prices = highs[peak_indices_local]

            try:
                sup_slope, sup_intercept, _, _, _ = linregress(trough_global_indices, trough_prices)
                res_slope, res_intercept, _, _, _ = linregress(peak_global_indices, peak_prices)
            except ValueError:
                sup_slope, res_slope = np.nan, np.nan  # 拟合失败

            # 检查向上通道的条件
            is_up_trend = sup_slope > -abs(slope_req_tolerance) and res_slope > -abs(slope_req_tolerance)  # 允许稍微负斜率
            is_parallel = False
            if not np.isnan(sup_slope) and not np.isnan(res_slope):
                if sup_slope == 0 and res_slope == 0:
                    is_parallel = True
                elif sup_slope != 0 or res_slope != 0:  # 避免 0/0
                    # 使用均值作为分母增加稳定性
                    denominator = (abs(res_slope) + abs(sup_slope)) / 2
                    if denominator > 1e-9:  # 防止除以非常小的值
                        slope_diff_rel = abs(res_slope - sup_slope) / denominator
                        is_parallel = slope_diff_rel <= slope_tolerance
                    elif abs(res_slope - sup_slope) < 1e-6:  # 如果斜率都接近0
                        is_parallel = True

            if is_up_trend and is_parallel and window >= min_duration:
                # (可选) 可以在此添加更严格的触点接近度和包含性检查
                # ... (参考上一个版本的检查逻辑) ...

                start_orig_idx = original_index[i]
                end_orig_idx = original_index[end_window - 1]
                channels.append((start_orig_idx, end_orig_idx, 'up'))

        # --- 检查向下通道 ---
        # 条件1: 第一个K线的高点必须是阻力线的一部分
        peak_indices_for_fit_local = np.unique(np.concatenate(([0], peak_indices_local)))

        if len(peak_indices_for_fit_local) >= min_touches and len(trough_indices_local) >= min_touches:
            peak_global_indices = sub_indices[peak_indices_for_fit_local]
            peak_prices = highs[peak_indices_for_fit_local]
            trough_global_indices = sub_indices[trough_indices_local]
            trough_prices = lows[trough_indices_local]

            try:
                res_slope, res_intercept, _, _, _ = linregress(peak_global_indices, peak_prices)
                sup_slope, sup_intercept, _, _, _ = linregress(trough_global_indices, trough_prices)
            except ValueError:
                res_slope, sup_slope = np.nan, np.nan  # 拟合失败

            # 检查向下通道的条件
            is_down_trend = res_slope < abs(slope_req_tolerance) and sup_slope < abs(slope_req_tolerance)  # 允许稍微正斜率
            is_parallel = False
            if not np.isnan(sup_slope) and not np.isnan(res_slope):
                if sup_slope == 0 and res_slope == 0:
                    is_parallel = True
                elif sup_slope != 0 or res_slope != 0:
                    denominator = (abs(res_slope) + abs(sup_slope)) / 2
                    if denominator > 1e-9:
                        slope_diff_rel = abs(res_slope - sup_slope) / denominator
                        is_parallel = slope_diff_rel <= slope_tolerance
                    elif abs(res_slope - sup_slope) < 1e-6:
                        is_parallel = True

            if is_down_trend and is_parallel and window >= min_duration:
                # (可选) 可以在此添加更严格的触点接近度和包含性检查
                # ... (参考上一个版本的检查逻辑) ...

                start_orig_idx = original_index[i]
                end_orig_idx = original_index[end_window - 1]
                channels.append((start_orig_idx, end_orig_idx, 'down'))

    # (可选) 合并重叠或相邻的同类型通道
    merged_channels = []
    if not channels:
        return []

    # 按起始时间排序，类型次之
    channels.sort(key=lambda x: (x[0], x[2]))

    current_start, current_end, current_type = channels[0]

    for i in range(1, len(channels)):
        next_start, next_end, next_type = channels[i]
        # 允许一天间隔合并 (假设是日线) 或重叠
        merge_candidate = False
        if isinstance(current_end, pd.Timestamp) and isinstance(next_start, pd.Timestamp):
            # 如果是时间戳索引
            # 允许的间隔，例如1天。如果是分钟线，可以设为 pd.Timedelta(minutes=1) 等
            allowed_gap = pd.Timedelta(days=1)
            merge_candidate = (next_start <= current_end + allowed_gap)
        else:
            # 如果是数字索引
            merge_candidate = (next_start <= current_end + 1)

        if next_type == current_type and merge_candidate:
            # 合并：扩展当前通道的结束点
            current_end = max(current_end, next_end)
        else:
            # 不合并：将当前通道存入结果，并开始新的通道
            merged_channels.append((current_start, current_end, current_type))
            current_start, current_end, current_type = next_start, next_end, next_type

    # 添加最后一个通道
    merged_channels.append((current_start, current_end, current_type))

    return merged_channels


# --- 使用示例 (使用之前的示例数据) ---
# 假设 klines_df 存在且已定义 (如上一个回答中)

# # 设置参数并寻找通道
# detected_channels_constrained = find_channels_constrained(
#     klines_df,
#     window=25,
#     min_touches=2,
#     slope_tolerance=0.4,  # 放宽一点平行度容忍
#     proximity_threshold_pct=0.02,  # 放宽一点接近度
#     min_duration=12,
#     slope_req_tolerance=0.1  # 允许斜率有10%的偏差
# )
#
# print("\nDetected Constrained Channels (Start Index, End Index, Type):")
# print(detected_channels_constrained)

# --- 可视化 (可选) ---
# plt.figure(figsize=(14, 7))
# # 绘制K线 (简单示例，只画收盘价和高低)
# plt.plot(klines_df.index, klines_df['High'], color='lightgray', linewidth=0.7, label='_nolegend_')
# plt.plot(klines_df.index, klines_df['Low'], color='lightgray', linewidth=0.7, label='_nolegend_')
# plt.plot(klines_df.index, klines_df['Close'], label='Close', color='black', alpha=0.8, linewidth=1)
#
# colors = {'up': 'green', 'down': 'red'}
# linestyles = {'up': '--', 'down': ':'}
#
# if detected_channels_constrained:
#     for start, end, channel_type in detected_channels_constrained:
#         channel_data = klines_df.loc[start:end]
#         if len(channel_data) < 2: continue  # 需要至少2个点来画线
#
#         time_indices_num = np.arange(len(channel_data))  # 使用数字索引绘图
#
#         # 基于通道数据重新拟合线用于绘图 (更精确地显示检测到的线)
#         highs_ch = channel_data['High'].values
#         lows_ch = channel_data['Low'].values
#         peak_indices_ch_local, _ = find_peaks(highs_ch, prominence=highs_ch.std() * 0.05)
#         trough_indices_ch_local, _ = find_peaks(-lows_ch, prominence=lows_ch.std() * 0.05)
#
#         res_slope, res_intercept = np.nan, np.nan
#         sup_slope, sup_intercept = np.nan, np.nan
#
#         # 向上通道绘图线
#         if channel_type == 'up':
#             trough_fit_idx = np.unique(np.concatenate(([0], trough_indices_ch_local)))
#             peak_fit_idx = peak_indices_ch_local
#             if len(trough_fit_idx) >= 2:
#                 sup_slope, sup_intercept, _, _, _ = linregress(time_indices_num[trough_fit_idx],
#                                                                lows_ch[trough_fit_idx])
#             if len(peak_fit_idx) >= 2:
#                 res_slope, res_intercept, _, _, _ = linregress(time_indices_num[peak_fit_idx], highs_ch[peak_fit_idx])
#
#         # 向下通道绘图线
#         elif channel_type == 'down':
#             peak_fit_idx = np.unique(np.concatenate(([0], peak_indices_ch_local)))
#             trough_fit_idx = trough_indices_ch_local
#             if len(peak_fit_idx) >= 2:
#                 res_slope, res_intercept, _, _, _ = linregress(time_indices_num[peak_fit_idx], highs_ch[peak_fit_idx])
#             if len(trough_fit_idx) >= 2:
#                 sup_slope, sup_intercept, _, _, _ = linregress(time_indices_num[trough_fit_idx],
#                                                                lows_ch[trough_fit_idx])
#
#         # 绘制趋势线段
#         if not np.isnan(res_slope):
#             plt.plot(channel_data.index, res_slope * time_indices_num + res_intercept, color=colors[channel_type],
#                      linestyle=linestyles[channel_type], linewidth=1.5)
#         if not np.isnan(sup_slope):
#             plt.plot(channel_data.index, sup_slope * time_indices_num + sup_intercept, color=colors[channel_type],
#                      linestyle=linestyles[channel_type], linewidth=1.5)
#
#         # 标记通道区域
#         plt.axvspan(start, end, color=colors[channel_type], alpha=0.1,
#                     label=f'{channel_type.capitalize()} Channel {start}-{end}')
#
#     plt.title('K-Line Chart with Detected Constrained Channels')
#     plt.xlabel('Date/Index')
#     plt.ylabel('Price')
#     # plt.legend() # 图例可能过多，可以注释掉
#     plt.grid(True, linestyle=':', alpha=0.5)
#     plt.tight_layout()
#     plt.show()
# else:
#     print("No constrained channels detected with the given parameters.")




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
    return all_channels


# 示例使用
if __name__ == "__main__":
    # 假设你有一个 CSV 文件包含K线数据
    # 数据需要包含 'Date', 'Open', 'High', 'Low', 'Close' 列
    # 'Date' 列需要能被 pandas 解析为日期时间格式
    dates = pd.date_range(start='2024-01-01', periods=300, freq='30T')
    price = np.linspace(100, 150, 300)
    noise = np.random.normal(0, 2, 300)
    high = price + np.abs(noise) + np.random.uniform(0, 3, 300)
    low = price - np.abs(noise) - np.random.uniform(0, 3, 300)
    close = price + noise / 2
    open_price = close.shift(1)  # 简化处理
    open_price.iloc[0] = price[0]

    ohlc_data = pd.DataFrame({
        'Date': dates,
        'Open': open_price,
        'High': high,
        'Low': low,
        'Close': close
    })
    ohlc_data = ohlc_data.set_index('Date')

    # 查找通道段
    all_channels = find_all_channels(ohlc_data, lookback=60)

    if not all_channels:
        print("没有识别到任何通道形态。")
    else:
        for i, channel in enumerate(all_channels):
            print(
                f"通道 {i + 1}: 类型={channel['type']}, 起始时间={channel['start_idx']}, 结束时间={channel['end_idx']}")
