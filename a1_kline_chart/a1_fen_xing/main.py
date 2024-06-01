#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(root_path)     # 设定指定目录为工作目录
print(f"------system begin...[root_path]: {root_path}")
sys.path.append(root_path)
from common.loggin_cfg import SysLogInit
from common.ui_main_window import MainWindow, app
import logging
from cfg import g_cfg


if __name__ == '__main__':
    SysLogInit('a1_fen_xing', 'logs/a1_kline_chart/a1_fen_xing')
    g_cfg.load_yaml()   # 默认最先加载配置文件
    logging.info("work begin...")
    w = MainWindow(g_cfg.conf)
    w.resize(1024, 768)
    w.show()
    app.exec()