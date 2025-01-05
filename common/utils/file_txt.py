import os
from typing import List
import logging
from datetime import datetime
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


def _read_in_reverse(file_path: str, block_size: int, n: int, end_dt) -> list[bytes]:
    """
    从文件末尾，逆向分块读取，直到获取到至少n行(按 b'\n' 分割)或读取到文件开头。
    返回分割后的“行”字节串列表（从最前到最后的顺序）。
    注意：在本函数中，这些“行”还未解码，只是字节级split。
    """
    if end_dt:
        end_dt = datetime.strptime(end_dt, '%Y-%m-%d %H:%M:%S')
    data_lines = []
    with open(file_path, 'rb') as f:
        # 移动到文件尾部
        f.seek(0, 2)
        file_size = f.tell()

        if file_size == 0:
            return []

        partial_line = b''

        while len(data_lines) <= n and file_size > 0:
            read_start = max(file_size - block_size, 0)
            f.seek(read_start)
            chunk = f.read(file_size - read_start)

            # 更新下次读取起点(更前)
            file_size = read_start

            # 将本次读取的数据拼到buffer前面（逆向）
            new_buffer = chunk + partial_line
            lines = new_buffer .split(b'\n')
            partial_line = lines[0]
            complete_lines = lines[1:]
            complete_lines = _decode_last_n_lines(complete_lines, len(complete_lines), "gb2312")
            if not end_dt:
                data_lines = complete_lines + data_lines
            else:
                if not data_lines:
                    for index,item in reversed(list(enumerate(complete_lines))):
                        code = item.split(',')
                        if len(code) == 9:
                            dt = datetime.strptime(code[0]+code[1], '%Y/%m/%d%H%M')
                            if end_dt >= dt:
                                complete_lines = complete_lines[:index+1]
                                data_lines = complete_lines + data_lines
                else:
                    data_lines = complete_lines + data_lines

        if partial_line:
            code = _decode_last_n_lines([partial_line], 1, "gb2312")
            if len(code[0].split(",")) == 9:
                data_lines = code + data_lines
    return data_lines

#
# def _read_in_reverse(file_path: str, block_size: int, n: int) -> list[bytes]:
#     """
#     从文件末尾，逆向分块读取，直到获取到至少n行(按 b'\n' 分割)或读取到文件开头。
#     返回分割后的“行”字节串列表（从最前到最后的顺序）。
#     注意：在本函数中，这些“行”还未解码，只是字节级split。
#     """
#     raw_lines = []
#     with open(file_path, 'rb') as f:
#         # 移动到文件尾部
#         f.seek(0, 2)
#         file_size = f.tell()
#
#         if file_size == 0:
#             return []
#
#         buffer = b''
#         while len(raw_lines) <= n and file_size > 0:
#             read_start = max(file_size - block_size, 0)
#             f.seek(read_start)
#             chunk = f.read(file_size - read_start)
#
#             # 更新下次读取起点(更前)
#             file_size = read_start
#
#             # 将本次读取的数据拼到buffer前面（逆向）
#             buffer = chunk + buffer
#             raw_lines = buffer.split(b'\n')
#
#     return raw_lines
#

#
# def _read_in_reverse(file_path: str, block_size: int, n: int) -> list[bytes]:
#     """
#     从文件末尾逆向分块读取，直到获取到至少 n 行(按 b'\n' 分割)
#     或到达文件开头为止，返回字节串形式的行列表（从最旧 -> 最新）。
#     """
#     raw_lines = []         # 用于存放最终行
#     partial_line = b''     # 用于存放不完整的行片段
#
#     with open(file_path, 'rb') as f:
#         # 移动到文件尾部，获取文件大小
#         f.seek(0, 2)
#         file_size = f.tell()
#
#         if file_size == 0:
#             return []
#
#         while len(raw_lines) < n and file_size > 0:
#             # 计算本次要读取的区段
#             read_start = max(file_size - block_size, 0)
#             f.seek(read_start)
#             chunk = f.read(file_size - read_start)
#
#             # 更新下一次“向前”读取的位置
#             file_size = read_start
#
#             # 将本次读到的 chunk 与上一次剩余的 partial_line 拼接
#             # 注意：由于 chunk 来自更早的数据，所以要放在 partial_line 前面
#             chunk = chunk + partial_line
#
#             # 按 b'\n' 拆分
#             lines = chunk.split(b'\n')
#
#             # 最后一段可能是新的“部分行”
#             # lines[:-1] 是本次提取到的“完整行”
#             partial_line = lines[-1]
#             complete_lines = lines[:-1]
#
#             # 这些“完整行”比原来 raw_lines 中的行更早，因此将它们放到 raw_lines 前面
#             raw_lines = complete_lines + raw_lines
#
#         # 读完后，如果 partial_line 里还有内容，就代表还剩最后一行未被换行符截断
#         if partial_line:
#             raw_lines = [partial_line] + raw_lines
#
#     return raw_lines
#

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


def tail(file_path: str, n: int = 1000, end_dt="", encoding: str = 'gb2312') -> list[str]:
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
    decoded_lines = _read_in_reverse(file_path, block_size, n, end_dt)

    if not decoded_lines:
        return []

    # 3) 解码并取最后 n 行
    # decoded_lines = _decode_last_n_lines(raw_lines, n+2, encoding)

    # if not decoded_lines:
    #     return []

    # 4) 特殊行过滤
    filtered = _filter_special_lines(decoded_lines)

    # 5) 返回结果
    return filtered

#
# def tail(file_path, n=1000, encoding='gb2312'):
#     lines = []
#     logging.info(f"read_file: {file_path}")
#     if not os.path.exists(file_path):
#         return lines
#     if not os.path.isfile(file_path):
#         return lines
#
#     with open(file_path, 'rb') as f:
#         # 移动到文件尾部
#         f.seek(0, 2)
#         file_size = f.tell()
#
#         # 若文件为空，直接返回空列表
#         if file_size == 0:
#             return []
#
#         lines = []
#         block_size = 1024
#         buffer = b''
#
#         # 反复从文件末尾向前读取，直到获取到 n 行
#         while len(lines) <= n and file_size > 0:
#             # 计算本次读取的起点位置
#             read_start = max(file_size - block_size, 0)
#             f.seek(read_start)
#             chunk = f.read(file_size - read_start)
#
#             # 更新文件当前位置（下次向更前读取）
#             file_size = read_start
#
#             # 将本次读取数据添加到缓冲区前面（因为是逆向读取）
#             buffer = chunk + buffer
#             # 按行切割
#             lines = buffer.split(b'\n')
#
#         # lines的最后n行即为所需要的数据，但由于lines最后一块split可能比n多，需要只取最后n行
#         # 同时需要滤除可能出现的空行
#         final_lines = [line.decode(encoding).strip() for line in lines[-n:] if line.strip()]
#         if "通达信" in final_lines[-1]:
#             final_lines = final_lines[:-1]
#         if "不复权" in final_lines[0]:
#             final_lines = final_lines[2:]
#         if "成交量" in final_lines[0]:
#             final_lines = final_lines[1:]
#
#         return final_lines


# base_path = "D:/new_tdx/T0002/export"
# # 使用示例
# file_path = "29#ML9.txt"  # 替换为你的文件路径
# last_five_lines = tail(f"{base_path}/{file_path}", n=1000)
# for line in last_five_lines:
#     print(line)


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
