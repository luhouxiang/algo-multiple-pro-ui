#! -*- coding: utf-8 -*-
import yaml
from common.util import singleton
from common.config import CONF_PATH
import logging
import os

CFG_FN = os.path.join(CONF_PATH, 'a1_kline_chart', 'a1_kline_chart.yaml')

@singleton
class Cfg():
    def __init__(self):
        self._cfg = {}

    def load_yaml(self):
        path = CFG_FN
        logging.info(f"conf_path: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            self._cfg = yaml.safe_load(f)
            # config = yaml.load(f, Loader=yaml.FullLoader)
            # config = yaml.load(f.read(), Loader=yaml.FullLoader)
            # yaml.dump(data, f, default_flow_style=False, encoding='utf-8', allow_unicode=True)

        return self._cfg


g_cfg = Cfg()
