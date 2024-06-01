#! -*- coding: utf-8 -*-
import yaml


conf = dict()


def load_yaml(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        # config = yaml.load(f, Loader=yaml.FullLoader)
        # config = yaml.load(f.read(), Loader=yaml.FullLoader)
        # yaml.dump(data, f, default_flow_style=False, encoding='utf-8', allow_unicode=True)
    return config


conf = load_yaml("../etc/config.yaml")
