import logging
import os
from common.utils.singleton import Singleton
from common.util import create_log_sub_path
from common.config import LOG_PATH
from logging import Filter
# pip install concurrent-log-handler
from concurrent_log_handler import ConcurrentRotatingFileHandler  # NOQA: F401

class ErrorFilter(Filter):
    def filter(self, record):
        return record.levelno == logging.ERROR


@Singleton
class SysLogInit(object):
    def __init__(self, name: str, path: str = '', type: int = 0):
        """
        name: 日志文件名称
        path: 日志文件存放路径 一般默认就好
        type: 日志存储类型
              0 - ConcurrentRotatingFileHandler
              1 - TimedRotatingFileHandler
              2 - FileHandler
        """
        if path != '':
            os.makedirs(path, exist_ok=True)
            file_path = f'{path}/{name}.log'
        else:
            file_path = os.path.join(create_log_sub_path(name), f"{name}.log")

        all_error_log_path = os.path.join(LOG_PATH, 'all_error.log')
        handler = logging.handlers.ConcurrentRotatingFileHandler(all_error_log_path, 'a', 5242880, 10)
        handler.addFilter(ErrorFilter())  # 添加过滤器

        log_handlers = [
            logging.StreamHandler(),
            handler
        ]

        if 0 == type:
            log_handlers.append(logging.handlers.ConcurrentRotatingFileHandler(file_path, 'a', 5242880, 10))
        elif 1 == type:
            log_handlers.append(logging.handlers.TimedRotatingFileHandler(file_path, 'd', 1, 10))
        elif 2 == type:
            log_handlers.append(logging.FileHandler(file_path, 'a'))

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s-%(filename)s:[%(lineno)d]-%(funcName)s-%(levelname)s - %(message)s',
            datefmt='%Y_%m_%d %H:%M:%S',
            handlers=log_handlers
        )
