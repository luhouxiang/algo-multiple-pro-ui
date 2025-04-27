import pandas as pd
import numpy as np
from tslearn.metrics import dtw
from tslearn.preprocessing import TimeSeriesScalerMinMax
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def normalize_series(series):
    """
    对单个时间序列进行 Min-Max 规范化到 [0, 1] 区间。
    处理常数序列的情况。
    """
    min_val = np.min(series)
    max_val = np.max(series)
    if max_val == min_val:
        # 如果序列是常数，则返回全零或全0.5等，避免除以零
        # 返回全0.5可能比全0好，因为它在[0,1]的中间
        return np.full_like(series, 0.5, dtype=float)
    return (series - min_val) / (max_val - min_val)

def find_similar_segments_dtw(historical_data,
                              template_series,
                              column_to_use='Close',
                              dtw_threshold=5.0):
    """
    使用 DTW 在历史数据中寻找与模板序列形状相似的片段。

    Args:
        historical_data (pd.DataFrame): 包含时间序列数据的 DataFrame，
                                         需要有时间索引和指定的列 (column_to_use)。
        template_series (pd.Series or np.ndarray): 模板时间序列 (例如，收盘价)。
                                                  函数内部会对其进行规范化。
        column_to_use (str): historical_data 中用于比较的列名。
        dtw_threshold (float): DTW 距离阈值，低于此阈值的片段被认为是相似的。

    Returns:
        list: 包含匹配片段信息的列表，每个元素是一个字典：
              {'start_index', 'end_index', 'dtw_distance'}
              索引是 historical_data 的原始索引。
    """
    if not isinstance(historical_data.index, pd.DatetimeIndex):
         print("警告: historical_data 的索引不是 DatetimeIndex，绘图时可能出错。")

    if column_to_use not in historical_data.columns:
        raise ValueError(f"指定的列 '{column_to_use}' 不在 historical_data 中。")

    if template_series is None or len(template_series) == 0:
        raise ValueError("模板序列不能为空。")

    historical_series = historical_data[column_to_use].values
    template_len = len(template_series)

    if len(historical_series) < template_len:
        print("历史数据长度小于模板长度，无法匹配。")
        return []

    # 1. 规范化模板序列 (仅执行一次)
    normalized_template = normalize_series(np.array(template_series, dtype=float))

    matches = []
    n_historical = len(historical_series)

    print(f"模板长度: {template_len}")
    print(f"历史数据长度: {n_historical}")
    print(f"DTW 阈值: {dtw_threshold}")
    print(f"使用的列: {column_to_use}")
    print("开始扫描...")

    # 2. 使用滑动窗口遍历历史数据
    for i in range(n_historical - template_len + 1):
        # 提取当前窗口的序列
        window_series = historical_series[i : i + template_len]

        # 3. 规范化当前窗口序列
        normalized_window = normalize_series(window_series)

        # 4. 计算 DTW 距离
        # tslearn.metrics.dtw 需要 (n_timestamps, n_features) 格式，这里是1维数据
        # 需要 reshape 成 (template_len, 1)
        # 注意：直接使用numpy数组进行计算可能比TimeSeriesScalerMinMax更快，尤其是在循环内
        try:
            distance = dtw(normalized_window.reshape(-1, 1),
                           normalized_template.reshape(-1, 1))
        except Exception as e:
            print(f"警告: 在索引 {i} 计算 DTW 时出错: {e}")
            distance = np.inf # 出错则认为不匹配

        # 5. 检查是否低于阈值
        if distance < dtw_threshold:
            start_index = historical_data.index[i]
            end_index = historical_data.index[i + template_len - 1]
            match_info = {
                'start_index': start_index,
                'end_index': end_index,
                'dtw_distance': distance
            }
            matches.append(match_info)
            # print(f"  找到匹配: {start_index} 到 {end_index}, 距离: {distance:.4f}")

        # 简单的进度提示
        if (i + 1) % 100 == 0:
            print(f"  已扫描 {i + 1}/{n_historical - template_len + 1} 个窗口...")

    print(f"扫描完成。总共找到 {len(matches)} 个潜在匹配。")
    return matches


# --- 示例用法 ---
if __name__ == '__main__':
    # 1. 创建一个模拟的“杯柄”模板 (例如，一个U形后跟一个小回调)
    # 这只是一个非常简化的示意，真实模板应来自实际数据或更精确的构造
    cup_len = 50
    handle_len = 15
    template_len = cup_len + handle_len
    # U 形杯身
    cup_part = 0.5 * (1 - np.cos(np.linspace(0, np.pi, cup_len)))**2
    # 小幅下降的杯柄
    handle_part = cup_part[-1] - np.linspace(0, 0.15, handle_len)**2
    # 拼接并添加一点噪音
    template_raw = np.concatenate([cup_part, handle_part])
    template_raw += np.random.normal(0, 0.03, template_len) # 加噪音
    # 使用 Series 方便绘图
    template_series = pd.Series(template_raw)

    # 2. 创建模拟的历史数据 (例如，包含多个类似形态和噪音)
    total_len = 500
    time_index = pd.date_range(start='2024-01-01', periods=total_len, freq='D')
    historical_values = np.random.rand(total_len) * 0.5 # 基础噪音

    # 在历史数据中嵌入几个类似模板的形态
    positions = [100, 300] # 形态开始的位置
    for pos in positions:
        if pos + template_len <= total_len:
            # 随机缩放和平移嵌入的形态
            scale = np.random.uniform(0.8, 1.5)
            shift = np.random.uniform(-0.1, 0.1)
            segment_to_insert = template_raw * scale + shift
            historical_values[pos : pos + template_len] = segment_to_insert

    historical_df = pd.DataFrame({'Close': historical_values}, index=time_index)

    # 3. 设置参数并执行 DTW 搜索
    # DTW 阈值需要根据模板和数据的规范化方式、噪音水平等进行调整
    # 初始可以设一个较宽松的值，然后根据结果收紧
    DTW_THRESHOLD = 3.5 # !!! 这个值需要仔细调整 !!!

    matched_segments = find_similar_segments_dtw(
        historical_data=historical_df,
        template_series=template_series, # 传入原始模板，函数内部规范化
        column_to_use='Close',
        dtw_threshold=DTW_THRESHOLD
    )

    # 4. 打印结果
    print("\n找到的相似片段:")
    if not matched_segments:
        print("未找到符合阈值的相似片段。")
    else:
        for match in matched_segments:
            print(f"  开始: {match['start_index'].strftime('%Y-%m-%d')}, "
                  f"结束: {match['end_index'].strftime('%Y-%m-%d')}, "
                  f"DTW 距离: {match['dtw_distance']:.4f}")

    # 5. (可选) 绘制结果图
    plt.style.use('seaborn-v0_8-darkgrid') # 使用好看的样式
    fig, axes = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

    # 绘制历史数据和找到的匹配区域
    axes[0].plot(historical_df.index, historical_df['Close'], label='历史收盘价', color='lightblue', linewidth=1.5)
    for match in matched_segments:
        match_segment_data = historical_df.loc[match['start_index']:match['end_index'], 'Close']
        axes[0].plot(match_segment_data.index, match_segment_data.values,
                     label=f"匹配 (DTW={match['dtw_distance']:.2f})", linewidth=2.5)
    axes[0].set_title(f"历史数据与找到的相似片段 (DTW 阈值 = {DTW_THRESHOLD})")
    axes[0].legend(loc='upper left', fontsize='small')
    axes[0].set_ylabel("价格 (原始)")

    # 绘制模板（为了比较，将其绘制在第一个匹配的旁边，需要对齐Y轴）
    if matched_segments:
        first_match_start = matched_segments[0]['start_index']
        template_plot_index = pd.date_range(start=first_match_start, periods=template_len, freq='D')

        # 为了在同一图上比较形状，对模板进行缩放和平移以匹配第一个找到的片段的范围
        first_match_values = historical_df.loc[first_match_start:matched_segments[0]['end_index'], 'Close'].values
        scale_factor = (np.max(first_match_values) - np.min(first_match_values)) / (np.max(template_raw) - np.min(template_raw))
        shift_factor = np.min(first_match_values) - np.min(template_raw) * scale_factor
        scaled_template = template_raw * scale_factor + shift_factor

        axes[0].plot(template_plot_index, scaled_template, label='模板 (缩放/平移后)', color='grey', linestyle='--', linewidth=1.5)
        axes[0].legend(loc='upper left', fontsize='small') # 更新图例

    # 单独绘制原始模板形状
    axes[1].plot(range(template_len), template_series, label='原始模板序列', color='black')
    axes[1].set_title("用于匹配的模板序列 (原始)")
    axes[1].set_ylabel("值 (原始)")
    axes[1].set_xlabel("模板内的时间点")
    axes[1].legend()

    # 格式化X轴日期
    locator = mdates.AutoDateLocator(minticks=5, maxticks=15)
    formatter = mdates.ConciseDateFormatter(locator)
    axes[0].xaxis.set_major_locator(locator)
    axes[0].xaxis.set_major_formatter(formatter)

    plt.tight_layout()
    plt.show()
