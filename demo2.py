import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf

# 设置中文字体和负号正常显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 将字体设置为黑体等系统已有中文字体
plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号

# 随机构造一组虚拟价格数据（仅用于示意）
np.random.seed(42)
dates = pd.date_range('2020-01-01', periods=100)
prices = np.linspace(20, 10, 50).tolist() + np.linspace(10, 20, 50).tolist()
# 加一些随机扰动
prices = np.array(prices) + np.random.normal(0,1,100)

# 构造ohlc数据(仅简单处理开高低收，模拟K线)
openp = prices + np.random.normal(0,0.5,100)
closep = prices
highp = np.maximum(openp, closep) + np.random.uniform(0.3,0.7,100)
lowp = np.minimum(openp, closep) - np.random.uniform(0.3,0.7,100)

data = pd.DataFrame({
    'Open': openp,
    'High': highp,
    'Low': lowp,
    'Close': closep,
}, index=dates)

# 简单计算MACD指标(12,26,9)
def MACD(close, short=12, long=26, signal=9):
    ema_short = close.ewm(span=short).mean()
    ema_long = close.ewm(span=long).mean()
    macd_line = ema_short - ema_long
    signal_line = macd_line.ewm(span=signal).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

macd_line, signal_line, macd_hist = MACD(data['Close'])

# 人为设定一类买点和二类买点位置(索引)
buy_point_1 = 50   # 在价格最低附近假设的一类买点
buy_point_2 = 70   # 假设的二类买点

fig = plt.figure(figsize=(10,8))
ax1 = plt.subplot2grid((3,1),(0,0),rowspan=2)
ax2 = plt.subplot2grid((3,1),(2,0),sharex=ax1)

# 绘制K线图
mpf.plot(data, type='candle', ax=ax1, volume=False, show_nontrading=True)

# 在价格图上标注一类、二类买点
ax1.annotate('一类买点(底背驰)',
             xy=(data.index[buy_point_1], data['Close'].iloc[buy_point_1]),
             xytext=(data.index[buy_point_1], data['Close'].iloc[buy_point_1]+2),
             arrowprops=dict(facecolor='green', shrink=0.05),
             fontsize=12, color='green', ha='center')

ax1.annotate('二类买点(中枢突破)',
             xy=(data.index[buy_point_2], data['Close'].iloc[buy_point_2]),
             xytext=(data.index[buy_point_2], data['Close'].iloc[buy_point_2]+2),
             arrowprops=dict(facecolor='blue', shrink=0.05),
             fontsize=12, color='blue', ha='center')

# 绘制MACD线与柱状图
ax2.plot(data.index, macd_line, label='MACD线', color='black')
ax2.plot(data.index, signal_line, label='信号线', color='orange')
ax2.bar(data.index, macd_hist, color=['green' if v>=0 else 'red' for v in macd_hist], alpha=0.5)

ax2.axhline(0, color='gray', linewidth=1)
ax2.legend(loc='upper left')

plt.tight_layout()
plt.show()

# 如需保存图片，请取消下行注释
# plt.savefig('candlestick_macd_example.png', dpi=150)
