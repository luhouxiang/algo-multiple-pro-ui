def tail(file_path, n=5, encoding='gb2312'):
    with open(file_path, 'rb') as f:
        # 移动到文件尾部
        f.seek(0, 2)
        file_size = f.tell()

        # 若文件为空，直接返回空列表
        if file_size == 0:
            return []

        lines = []
        block_size = 1024
        buffer = b''

        # 反复从文件末尾向前读取，直到获取到 n 行
        while len(lines) <= n and file_size > 0:
            # 计算本次读取的起点位置
            read_start = max(file_size - block_size, 0)
            f.seek(read_start)
            chunk = f.read(file_size - read_start)

            # 更新文件当前位置（下次向更前读取）
            file_size = read_start

            # 将本次读取数据添加到缓冲区前面（因为是逆向读取）
            buffer = chunk + buffer
            # 按行切割
            lines = buffer.split(b'\n')

        # lines的最后n行即为所需要的数据，但由于lines最后一块split可能比n多，需要只取最后n行
        # 同时需要滤除可能出现的空行
        final_lines = [line.decode(encoding).strip() for line in lines[-n:] if line.strip()]
        if "通达信" in final_lines[-1]:
            final_lines = final_lines[:-1]
        if "不复权" in final_lines[0]:
            final_lines = final_lines[2:]
        if "成交量" in final_lines[0]:
            final_lines = final_lines[1:]

        return final_lines


base_path = "D:/new_tdx/T0002/export"
# 使用示例
file_path = "29#ML9.txt"  # 替换为你的文件路径
last_five_lines = tail(f"{base_path}/{file_path}", n=1000)
for line in last_five_lines:
    print(line)
