import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
import yfinance as yf

# 设置中文字体和负号正常显示（根据环境可更换字体）
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 获取真实股票数据，这里以2021年全年的AAPL数据为例
data = yf.download("AAPL", start="2023-01-01", end="2023-12-31")
# 设置显示所有列
pd.set_option('display.max_columns', None)
# 设置每列的最大宽度（可选）
pd.set_option('display.max_colwidth', None)
print(data.head())
# 将数据的列转化为float类型，确保无类型问题
data = data.astype(float)

##################<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
data_cleaned = data[['Open', 'High', 'Low', 'Close', 'Volume']]  # 提取我们需要的列

# 如果列名称有其他需要修改的地方，可以重新命名
data_cleaned.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

# 由于 'mplfinance' 需要使用时间索引（如日期），确保数据的索引为日期类型
# data_cleaned.index = pd.to_datetime(data_cleaned.index)

# 转换为float64类型确保mplfinance可以识别
data_cleaned = data_cleaned.astype(float)
data = data_cleaned
################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


# 计算MACD指标(12,26,9)
def MACD(close, short=12, long=26, signal=9):
    ema_short = close.ewm(span=short).mean()
    ema_long = close.ewm(span=long).mean()
    macd_line = ema_short - ema_long
    signal_line = macd_line.ewm(span=signal).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

macd_line, signal_line, macd_hist = MACD(data['Close'])

close_prices = data['Close'].values
hist_values = macd_hist.values

# 寻找一类买点(底背驰简化逻辑)
one_buy_idx = None
prev_low_idx = None
prev_low_price = None
prev_low_hist = None

for i in range(2, len(close_prices)-2):
    if close_prices[i] < close_prices[i-1] and close_prices[i] < close_prices[i+1]:
        if prev_low_idx is not None:
            if close_prices[i] < prev_low_price and hist_values[i] > prev_low_hist:
                one_buy_idx = i
                break
        prev_low_idx = i
        prev_low_price = close_prices[i]
        prev_low_hist = hist_values[i]

# 寻找二类买点(中枢突破简化逻辑)
two_buy_idx = None
if one_buy_idx is not None:
    start_search = one_buy_idx + 5
    end_search = len(close_prices) - 5
    if start_search < end_search:
        window_size = 20
        for start_i in range(start_search, end_search - window_size):
            segment = close_prices[start_i:start_i+window_size]
            seg_high = np.max(segment)
            seg_low = np.min(segment)
            PRICE_FLUCTUATION_THRESHOLD = 0.05
            if (seg_high - seg_low) / seg_low < PRICE_FLUCTUATION_THRESHOLD:  # 简单模拟中枢
                for j in range(start_i+window_size, min(start_i+window_size+20, len(close_prices))):
                    if close_prices[j] > seg_high:
                        two_buy_idx = j
                        break
                if two_buy_idx is not None:
                    break

fig = plt.figure(figsize=(12,8))
ax1 = plt.subplot2grid((3,1),(0,0),rowspan=2)
ax2 = plt.subplot2grid((3,1),(2,0),sharex=ax1)




print(data.head())
# 绘制K线图
mpf.plot(data, type='candle', ax=ax1, volume=False, show_nontrading=True)

# 标注一类买点
if one_buy_idx is not None:
    ax1.annotate('一类买点(底背驰)',
                 xy=(data.index[one_buy_idx], close_prices[one_buy_idx]),
                 xytext=(data.index[one_buy_idx], close_prices[one_buy_idx]*1.05),
                 arrowprops=dict(facecolor='green', shrink=0.05),
                 fontsize=12, color='green', ha='center')

# 标注二类买点
if two_buy_idx is not None:
    ax1.annotate('二类买点(中枢突破)',
                 xy=(data.index[two_buy_idx], close_prices[two_buy_idx]),
                 xytext=(data.index[two_buy_idx], close_prices[two_buy_idx]*1.05),
                 arrowprops=dict(facecolor='blue', shrink=0.05),
                 fontsize=12, color='blue', ha='center')

# 绘制MACD
ax2.plot(data.index, macd_line, label='MACD线', color='black')
ax2.plot(data.index, signal_line, label='信号线', color='orange')
ax2.bar(data.index, macd_hist, color=['green' if v>=0 else 'red' for v in macd_hist], alpha=0.5)
ax2.axhline(0, color='gray', linewidth=1)
ax2.legend(loc='upper left')

plt.tight_layout()
plt.show()
