import os
from typing import List
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

import copy
def read_file(file_name) -> List[str]:
    """
    读取文本文件，返回list[str]
    """
    lines = []
    abs_path = os.path.abspath(file_name)
    logging.info(f"read_file: {abs_path}")
    if not os.path.exists(file_name):
        return lines
    with open(file_name, 'r') as f:
        f.readline()
        while line := f.readline():
            # print(line[:-1])
            lines.append(line[:-1])
    return lines


import os
import logging

def _check_file_validity(file_path: str) -> bool:
    """
    检查文件有效性：存在且为常规文件。
    """
    if not os.path.exists(file_path):
        return False
    if not os.path.isfile(file_path):
        return False
    return True


def _init_file_pos(f):
    """
    移动到文件尾部, 返回文件大小.
    若文件大小为0, 表示空文件.
    """
    f.seek(0, 2)
    file_size = f.tell()
    return file_size


def _read_block(f, file_size, block_size):
    """
    从 file_size 向前 block_size 个字节(或直到文件头)读取一块数据.
    返回 (chunk, new_file_size).
    """
    read_start = max(file_size - block_size, 0)
    f.seek(read_start)
    chunk = f.read(file_size - read_start)
    new_file_size = read_start
    return chunk, new_file_size


def _split_lines_preserve_partial(chunk, partial_line):
    """
    将 chunk + partial_line 合并并 split.
    保持 `partial_line = lines[0]` 不动的逻辑:
      - lines[0] 被视作不完整行, 存入 partial_line
      - lines[1:] 才是完整行.

    返回 (new_partial_line, complete_lines)
    """
    new_buffer = chunk + partial_line
    lines = new_buffer.split(b'\n')
    # 根据你的需求: lines[0] => new_partial_line, lines[1:] => complete_lines
    new_partial_line = lines[0]
    complete_lines = lines[1:]
    return new_partial_line, complete_lines


def _decode_lines(raw_lines, encoding="gb2312"):
    """
    解码原始字节行, 并去除空行.
    """
    decoded = []
    for b_line in raw_lines:
        if not b_line:
            continue
        line_str = b_line.decode(encoding, errors='ignore').strip()
        if line_str:
            decoded.append(line_str)
    return decoded


def _parse_time_if_possible(line):
    """
    按照你目前的行格式, 假设:
        code = line.split(',')
        if len(code) == 9:
            dt = datetime.strptime(code[0]+code[1], '%Y/%m/%d%H%M')
    若无法解析或格式不符, 返回 None
    """
    parts = line.split(',')
    if len(parts) == 9:
        try:
            dt = datetime.strptime(parts[0] + parts[1], '%Y/%m/%d%H%M')
            return dt
        except:
            return None
    return None

@dataclass
class DataLines:
    count: int
    lines: List[List[str]]


def _merge_lines_with_time_check(data_lines: DataLines, new_lines: List[str], end_dt) -> int:
    """
    如果 end_dt 不为空, 从 new_lines(已解码)里找 <= end_dt 的行并拼接到 data_lines.
    若 data_lines 还为空时, 要把 "从后往前" 读到的第一批 lines 里,
    找到最后一个 <= end_dt 的位置后再截断.
    否则, 直接全部拼接.

    data_lines, new_lines 均为 "从前到后" 或 "从后到前" 的列表,
    这里你原代码对顺序要求: data_lines = complete_lines + data_lines
    """
    if not end_dt:
        # 不做时间判断, 直接拼接
        data_lines.count += len(new_lines)
        data_lines.lines.append(new_lines)
        return data_lines.count

    if data_lines.count == 0:
        # data_lines为空时, 需要找最后一个 <= end_dt 的行
        # new_lines现在顺序不明, 但你写的是: data_lines = new_lines + data_lines
        # => new_lines更老? 还是更新? 根据你原有逻辑是 "chunk + partial_line" 逆向.
        # 这里跟你之前“reversed(enumerate(new_lines))”类似:
        cut_idx = -1
        for idx in reversed(range(len(new_lines))):
            line = new_lines[idx]
            dt = _parse_time_if_possible(line)
            if dt and dt <= end_dt:
                cut_idx = idx
                break
        # 如果找到了 cut_idx
        if cut_idx != -1:
            # 保留 new_lines[:cut_idx+1], 拼到 data_lines
            new_lines = new_lines[:cut_idx+1]
            data_lines.count += len(new_lines)
            data_lines.lines.append(new_lines)
            return data_lines.count
        else:
            # 没有任何行 <= end_dt, 返回原data_lines(还是空)
            return data_lines.count
    else:
        # data_lines不为空, 说明之前已经加过一些行了
        data_lines.count += len(new_lines)
        data_lines.lines.append(new_lines)
        return data_lines.count


def count_klines(data_lines):
    s = 0
    for k in data_lines:
        s += len(k)
    return s


def _read_in_reverse(file_path: str, block_size: int, n: int, end_dt) -> list[str]:
    """
    主函数: 从文件末尾逆向分块读取, 保持 partial_line = lines[0].
    拼装到 data_lines(从你原代码看, 最后返回从最前到最后的顺序).

    1) 若 end_dt 有值, 解析成 datetime
    2) 循环读块, split -> partial_line + complete_lines
    3) complete_lines 解码后, 做时间检查与拼接
    4) 直到 data_lines数>=n 或到文件开头
    5) 最后处理 partial_line
    6) 返回 data_lines
    """
    # 1) 处理 end_dt
    dt_end = None
    if end_dt:
        dt_end = datetime.strptime(end_dt, '%Y-%m-%d %H:%M:%S')

    data_lines = DataLines(count=0, lines=[])
    with open(file_path, 'rb') as f:
        # 初始化文件大小
        file_size = _init_file_pos(f)
        if file_size == 0:
            return []

        partial_line = b''

        # 2) 循环读取, 直到 data_lines >= n 或 file_size = 0
        while data_lines.count <= n and file_size > 0:
            chunk, file_size = _read_block(f, file_size, block_size)

            # 把 chunk + partial_line 做 split, 并保留 partial_line = lines[0] 逻辑
            partial_line, complete_raw_lines = _split_lines_preserve_partial(chunk, partial_line)

            # 解码
            complete_lines_decoded = _decode_lines(complete_raw_lines, encoding="gb2312")

            # 时间检查 + 拼接
            _merge_lines_with_time_check(data_lines, complete_lines_decoded, dt_end)

        # 3) 最后若 partial_line 还有内容, 尝试解码并拼接(看格式是否匹配9列)
        if partial_line:
            partial_decoded = _decode_lines([partial_line], encoding="gb2312")
            if partial_decoded:
                # 检查是否9列
                code = partial_decoded[0].split(",")
                if len(code) == 9 and len(code[0]) == 10:
                    # 若 end_dt 存在, 同样做一次时间检查后再拼
                    _merge_lines_with_time_check(data_lines, partial_decoded, dt_end)
    items = []
    for item in reversed(data_lines.lines):
        items.extend(item)
    return items


def _read_between_dates(file_path, block_size, dt_start, dt_end):
    lines_in_range = []
    with open(file_path, 'r', encoding='gb2312') as file:
        # 跳过文件的头两行
        next(file)
        next(file)
        for line in file:
            arr = line.split(',')
            line_dt_str = arr[0] + ' ' + arr[1]
            line_dt = datetime.strptime(line_dt_str, '%Y/%m/%d %H%M')
            if line_dt.hour > 17 or line_dt.hour < 7:
                line_dt -= timedelta(days=1)
            if dt_start <= line_dt <= dt_end:
                lines_in_range.append(line.strip())
            elif line_dt > dt_end:
                break

    return lines_in_range


def _read_from_start(file_path, block_size, dt_start, n):
    lines_from_start = []
    with open(file_path, 'r', encoding='gb2312') as file:
        # 跳过文件的头两行
        next(file)
        next(file)
        for line in file:
            line_dt_str = line.split(',')[0]
            line_dt = datetime.strptime(line_dt_str, '%Y-%m-%d %H:%M:%S')
            if line_dt.hour > 17 or line_dt.hour < 7:
                line_dt -= timedelta(days=1)
            if line_dt >= dt_start:
                lines_from_start.append(line.strip())
                if len(lines_from_start) >= n:
                    break

    return lines_from_start


def _decode_last_n_lines(raw_lines: list[bytes], n: int, encoding: str) -> list[str]:
    """
    对原始字节行进行解码并截取最后n行，过滤空行。
    返回解码后的字符串列表(保持顺序:从最前到最后)。
    """
    # 只取最后 n 行
    last_n = raw_lines[-n:]
    # 解码并去除空行
    decoded = [line.decode(encoding, errors='ignore').strip()
               for line in last_n if line.strip()]
    return decoded


def _filter_special_lines(lines: list[str]) -> list[str]:
    """
    根据题意，对lines进行:
      - 若末行含"通达信", 剔除该行
      - 若首行含"不复权", 去掉前2行
      - 若首行含"成交量", 去掉前1行
    """
    if not lines:
        return []

    # 若最后一行含"通达信"
    if "通达信" in lines[-1]:
        lines = lines[:-1]

    # 若第一行含"不复权"
    if lines and "不复权" in lines[0]:
        lines = lines[2:] if len(lines) > 2 else []

    # 若第一行含"成交量"
    if lines and "成交量" in lines[0]:
        lines = lines[1:] if len(lines) > 1 else []

    return lines


def tail_kline(file_path: str, n: int = 1000, start_dt="", end_dt="", encoding: str = 'gb2312') -> list[str]:
    """
    主函数：返回文件末尾 n 行(经过简单过滤)。
    具体步骤:
      1) 检查文件有效性
      2) 逆向读取至少 n 行的字节数据
      3) 解码并截取最后 n 行(去空行)
      4) 进行"通达信、不复权、成交量"过滤
      5) 返回结果
    """
    logging.info(f"read_file: {file_path}")
    # 1) 检查文件有效性
    if not _check_file_validity(file_path):
        return []

    # 2) 逆向分块读取到至少 n+1 行(字节串)
    block_size = 1024
    # 检查start_dt和end_dt是否存在
    dt_start = datetime.strptime(start_dt, '%Y-%m-%d %H:%M:%S') if start_dt else None
    dt_end = datetime.strptime(end_dt, '%Y-%m-%d %H:%M:%S') if end_dt else None

    # 根据不同情况调用读取逻辑
    if dt_start and dt_end:
        # 同时存在start和end，忽略n，取两个时间之间的数据
        decoded_lines = _read_between_dates(file_path, block_size, dt_start, dt_end)
    elif dt_start:
        # 只有start，取start开始的n条数据
        decoded_lines = _read_from_start(file_path, block_size, dt_start, n)
    else:
        # 原逻辑：以end_dt为终点，向前取n条数据
        decoded_lines = _read_in_reverse(file_path, block_size, n, end_dt)


    # decoded_lines = _read_in_reverse(file_path, block_size, n, end_dt)

    if not decoded_lines:
        return []

    # 3) 特殊行过滤
    filtered = _filter_special_lines(decoded_lines)

    # 4) 返回结果
    return filtered


def write_file(file_name, lines: List[str], append: bool):
    """
    写文件， append为True表示追加，否则重新创新
    """
    if append:
        with open(file_name, 'a') as f:
            for line in lines:
                f.write(F"{line}\n")
            f.flush()
    else:
        with open(file_name, 'w') as f:
            for line in lines:
                f.write(F"{line}\n")
            f.flush()


def list_only_files(directory) -> list[str]:
    files: list[str] = []
    """只列出目录中的文件，不包括子文件夹"""
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            files.append(item)
    return files


def find_first_file(target: str, files: list[str]) -> str:
    """返回第一个包含 'rbL9'（不区分大小写）的文件名

    Args:
        files: 文件名字符串列表

    Returns:
        第一个匹配的文件名（保留原始大小写），如果没有则返回空字符串
    """
    # target = 'rbL9'
    return next((f for f in files if target.lower() in f.lower()), "")

