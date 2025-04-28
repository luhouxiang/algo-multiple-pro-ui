import pandas as pd

# 读取文件，跳过前两行
data = pd.read_csv('28#SRL9.txt',
                   skiprows=2,
                   header=None,
                   encoding='gbk')
data = data.iloc[:-1]  # 或 data.drop(data.tail(1).index)
# 提取日期和时间，合并为 'Date' 列
data1 = data[1].astype(int).astype(str).str.zfill(4)
dates = data[0] + ' ' + data1  # 时间补齐为4位，如905变为0905
dates = pd.to_datetime(dates, format='%Y/%m/%d %H%M')

# 提取OHLC数据
open_price = data[2]
high = data[3]
low = data[4]
close = data[5]
volume = data[6]
cc = data[7]
# 创建DataFrame
ohlc_data = pd.DataFrame({
    'Date': dates,
    'Open': open_price,
    'High': high,
    'Low': low,
    'Close': close,
    'Volume': volume,
    "Cc": cc
})

# 打印结果
print(ohlc_data)