#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(f"------system begin...[root_path]: {root_path}")
sys.path.append(root_path)
from common.loggin_cfg import SysLogInit
import logging
from cfg import g_cfg


if __name__ == '__main__':
    SysLogInit('a1_kline_chart', 'logs/a1_kline_chart')
    g_cfg.load_yaml()   # 默认最先加载配置文件
    logging.info("work begin...")