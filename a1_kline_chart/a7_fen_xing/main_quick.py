#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import xlwings as xw
import re
from typing import Dict
import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler  # NOQA: F401
import stat


def extract_numbers(line):
    """
    提取开头的数字，并返回这个数字，如果没有提取到，则返回空字符串。
    参数:
        input_string (str): 字符串，每行以数字开头，后跟非数字字符。
    返回:
        rel: 提取到的数字
    """
    rel = ""
    # 匹配每行开头连续的数字
    match = re.match(r'\s*(\d+)', line)
    if match:
        rel = match.group(1)
    return rel


def get_template_files(input_dir) -> Dict[str, str]:
    files = {}
    try:
        # 遍历目录下所有文件
        for filename in os.listdir(input_dir):
            if filename.lower().endswith('.xlsx'):
                file_path = os.path.join(input_dir, filename)
                shu_zi = extract_numbers(filename)
                if shu_zi:
                    if shu_zi == "0":
                        continue
                    files[shu_zi] = file_path
    finally:
        # 退出 Excel 应用
        pass
    logging.info("模板数：{}".format(len(files)))
    for k, v in files.items():
        logging.info("template_files:[{}]: {}".format(k, v))
        make_file_writable(v)
    logging.info("get_template_files end.\n\n")
    return files


def list_all_files(directory, templates: Dict[str, str]):
    """
    遍历指定目录下的所有文件，并返回包含文件完整路径的列表。
    参数:
        directory (str): 目标目录的路径。
    返回:
        list: 包含所有文件完整路径的列表。
    """
    file_dic_list = {}
    logging.info("list_all_files begin...")

    def traverse(current_dir):
        """
        递归遍历当前目录下的所有文件和子目录，将文件路径添加到 file_list 中。
        参数:
            current_dir (str): 当前遍历的目录路径。
        """
        try:
            for entry in os.listdir(current_dir):
                full_path = os.path.join(current_dir, entry)
                if os.path.isdir(full_path):
                    traverse(full_path)
                else:
                    shu_zi = extract_numbers(entry)
                    if shu_zi and shu_zi in templates:
                        if shu_zi not in file_dic_list:
                            file_dic_list[shu_zi] = []
                        file_dic_list[shu_zi].append(full_path)
        except Exception as e:
            logging.error(f"访问目录 {current_dir} 时出错: {e}")
    traverse(directory)
    for k, v in file_dic_list.items():
        for v1 in v:
            logging.info("[{}]: {}".format(k, v1))
    logging.info("list_all_files end.\n\n")
    return file_dic_list


def is_integer(s):
    """
    判断字符串是否为整型数字。

    参数:
        s (str): 待判断的字符串。

    返回:
        bool: 如果 s 表示整型数字，则返回 True；否则返回 False。
    """
    try:
        # 尝试将字符串转换为整型
        int(s)
        return True
    except ValueError:
        return False


def open_excel_file_2(k, file_path, app):
    datas = {}
    logging.info(f"open_file: {file_path}")
    wb = app.books.open(file_path)
    sheet = wb.sheets[0]
    # 获取工作表中使用的区域
    used_range = sheet.used_range
    last_row = used_range.last_cell.row
    for row in range(1, last_row + 1):
        # 获取当前行的前四列数据（A、B、C、D 列）
        row_values = sheet.range((row, 1), (row, 4)).value
        if len(row_values) and row_values[0] and is_integer(row_values[0]):
            # logging.info(f"规则[{k}]第[{row}]行的前四列数据：{row_values[0]},{row_values[1]},{row_values[2]},{row_values[3]}")
            datas[int(row_values[0])] = row_values
    logging.info(f"规则[{k}],有[{len(datas)}]行数据")
    wb.close()
    return datas


def open_excel_file(k, file_path, app):
    """
    批量读取 Excel 文件中 A-D 列的数据，
    返回一个字典，key 为第一列数字，value 为整行数据。
    """
    logging.info(f"open_file: {file_path}")
    wb = app.books.open(file_path)
    sheet = wb.sheets[0]
    used_range = sheet.used_range
    last_row = used_range.last_cell.row
    # 批量读取A-D区域
    data_range = sheet.range((1, 1), (last_row, 4)).value
    datas = {}
    # data_range 为列表形式，每个元素为一行数据
    for row in data_range:
        if row and len(row) >= 1 and row[0] and is_integer(row[0]):
            datas[int(row[0])] = row
    logging.info(f"规则[{k}],有[{len(datas)}]行数据")
    wb.close()
    return datas


def sync_excel_file(sync_path, datas, app):
    """
    批量写入数据到 Excel 文件中，
    根据第一列匹配，如果存在则更新该行 B、C、D 三列的数据。
    """
    logging.info(f"sync_file begin: data_len: {len(datas):05}, {sync_path}")
    wb = app.books.open(sync_path)
    sheet = wb.sheets[0]
    used_range = sheet.used_range
    last_row = used_range.last_cell.row
    # 批量读取A-D区域
    data_range = sheet.range((1, 1), (last_row, 4)).value
    # 遍历内存中的数据，根据第一列更新相应的行
    for idx, row in enumerate(data_range):
        if row and len(row) >= 4 and row[0] and is_integer(row[0]):
            key = int(row[0])
            if key in datas:
                # 更新B, C, D列数据
                row[1] = datas[key][1]
                row[2] = datas[key][2]
                row[3] = datas[key][3]
                # data_range[idx] 已更新
    # 批量写回更新后的数据区域
    sheet.range((1, 1), (last_row, 4)).value = data_range
    wb.save(sync_path)
    wb.close()
    logging.info(f"sync_file end: data_len: {len(datas):05}, {sync_path}")

def make_file_writable(file_path):
    """
    将指定的文件设置为可写（取消只读属性）。

    参数:
        file_path (str): 文件的路径。
    """
    # 获取文件当前的权限属性
    file_attrs = os.stat(file_path).st_mode
    # 通过按位或操作，添加写权限（S_IWRITE），使其可写
    os.chmod(file_path, file_attrs | stat.S_IWRITE)


record_format = '[%(asctime)s][%(levelname)s][%(filename)s][%(lineno)03d] %(message)s'
date_format = '%m%d %H:%M:%S'
handler = logging.handlers.ConcurrentRotatingFileHandler(os.path.join(os.getcwd(), 'app.log'), 'a', 20242880, 10)
log_handlers = [
    logging.StreamHandler(),
    handler
]
logging.basicConfig(
    level=logging.INFO,
    format=record_format,
    datefmt=date_format,
    handlers=log_handlers
)
logger = logging.getLogger(__name__)


# 设置全局异常处理函数，确保未捕获的异常也能写入日志
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        # 对于键盘中断，保持默认处理
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("未捕获的异常：", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception


if __name__ == '__main__':
    logger.info("work begin...")
    try:
        templates = get_template_files(r"D:\22\0320数据发（已有模版）")
        all_files = list_all_files(r"D:\22\3-回收科室数据（包含第一批和第二批）", templates)
        app = xw.App(visible=False)
        try:
            for k, v in all_files.items():
                all_datas = {}
                for v1 in v:
                    datas = open_excel_file(k, v1, app)
                    all_datas.update(datas)
                    # break   # TODO: 临时 一遍， 稍后得删除此行代码
                sync_excel_file(templates[k], all_datas, app)
                # break   # TODO: 临时 一遍， 稍后得删除此行代码
        finally:
            app.quit()
    except Exception as e:
        # 捕获异常后记录详细异常信息
        logger.exception("执行过程中发生异常")
        raise  # 记录后重新抛出异常
    logger.info("work end.")
    input("按任意键退出...")
