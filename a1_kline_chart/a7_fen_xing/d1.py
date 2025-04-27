import re

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


if __name__ == '__main__':
    sample_string = """8、左心
9.abc
10.ddd"""
    result = extract_numbers(sample_string)
    print("提取到的数字：", result)
