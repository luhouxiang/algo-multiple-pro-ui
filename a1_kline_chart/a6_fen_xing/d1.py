import os
import re

# 指定要搜索的目录
directory = r'D:\new_tdx\T0002\export'

# 列出目录中的所有文件和文件夹
all_items = os.listdir(directory)

# 定义正则表达式模式，匹配包含 '#'，并以 'L9.txt' 结尾的文件名
pattern = re.compile(r'.+#.+L9\.txt$')

# 筛选符合条件的文件名
matching_files = [item for item in all_items if pattern.match(item) and os.path.isfile(os.path.join(directory, item))]

# 打印符合条件的文件的完整路径
for file_name in matching_files:
    full_path = os.path.join(directory, file_name)
    print(full_path)