#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从通达信5分钟数据导出为本工程所需数据
"""
import os
import sys
work_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(work_dir)     # 设定指定目录为工作目录
sys.path.append(work_dir)
from common.logging_cfg import SysLogInit
from common.ui_main_window import MainWindow, app
import logging
from cfg import g_cfg
from common.http.httpserver import PyHttpServer
import pandas as pd
from datetime import date
file_name = "28#SRL9.txt"
csv_file = f"D:\\new_tdx\\T0002\\export\\{file_name}"
with open(csv_file, encoding='gbk') as file:
    file.readline()
    content = file.readline().replace('\t', ',').replace("\n", "")
    content = content.replace(' ', '')
columns = content.split(',')
print(content)
df = pd.read_csv(csv_file, encoding='gbk', skiprows=3, names=columns).replace("\n", "", regex=True)
df = df[:-1]
df['时间'] = df['时间'].fillna('').astype(int).astype(str)
df['时间'] = df['时间'].apply(lambda x: x.zfill(4) if x != '' else x)
df['dt'] = pd.to_datetime(df['日期'] + ' ' + df['时间'], format='%Y/%m/%d %H%M')
df = df[['dt'] + [col for col in df.columns if col not in ['日期', '时间', 'dt', '持仓量', '结算价']]]
df = df.rename(columns={'开盘': 'open', '最高': 'high', '最低': 'low', '收盘': 'close', '成交量': 'volume'})
file_name = f"./data/{date.today().strftime("%Y%m%d")}_{file_name}"
print(f"will save_file: {file_name}")
df.to_csv(file_name, index=False)
print(df)



if __name__ == '__main__':
    SysLogInit('a4_fen_xing', 'logs/a1_kline_chart/a3_fen_xing')
    g_cfg.load_yaml()   # 默认最先加载配置文件
    logging.info(f"...... ...... work begin... work_dir:{work_dir}")
    logging.error("abcd")
    logger = logging.getLogger(__name__)
    logger.info("color test...")
    # PyHttpServer().start()
    #
    # w = MainWindow(g_cfg.conf)
    # w.resize(1024, 768)
    # w.show()
    # app.exec()
