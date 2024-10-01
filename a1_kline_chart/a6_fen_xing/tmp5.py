def calculate_bi(fractals):
    # 第一步：按照 index 升序排序分型集合
    fractals.sort(key=lambda x: x['index'])

    # 第二步：处理分型集合
    processed_fractals = process_fractals(fractals)

    # 第三步：生成笔
    bi_list = generate_bi(processed_fractals)
    return bi_list


def process_fractals(fractals):
    """
    处理分型列表，消除不符合条件的分型，返回处理后的分型列表
    """
    if not fractals:
        return []

    processed = [fractals[0]]  # 初始化处理后的分型列表
    for next_fractal in fractals[1:]:
        last_fractal = processed[-1]
        if next_fractal['type'] == last_fractal['type']:
            # 处理相同类型的相邻分型
            stronger_fractal = select_stronger_fractal(last_fractal, next_fractal)
            processed[-1] = stronger_fractal
        else:
            # 处理不同类型的相邻分型
            if is_valid_transition(last_fractal, next_fractal):
                processed.append(next_fractal)
            else:
                continue  # 跳过不符合条件的分型
    return processed


def select_stronger_fractal(f1, f2):
    """
    选择更强的分型：
    - 对于顶分型，选择较高的 high 值
    - 对于底分型，选择较低的 low 值
    """
    if f1['type'] == 'top':
        return f1 if f1['high'] > f2['high'] else f2
    elif f1['type'] == 'bottom':
        return f1 if f1['low'] < f2['low'] else f2
    else:
        return f1  # 如果类型不明，保留第一个


def is_valid_transition(f1, f2):
    """
    判断两个不同类型的分型之间是否满足条件：
    - 相邻分型之间的 K 线数量应不少于 5
    """
    k_lines_included = f2['index'] - f1['index'] + 1
    return k_lines_included >= 5


def generate_bi(fractals):
    bi_list = []
    for i in range(len(fractals) - 1):
        f1 = fractals[i]
        f2 = fractals[i + 1]
        if f1['type'] != f2['type']:
            bi = {
                'start_index': f1['index'],
                'end_index': f2['index'],
                'start_type': f1['type'],
                'end_type': f2['type'],
            }
            bi_list.append(bi)
    return bi_list




def read_top_bottom():
    import json
    path = r"E:\work\py\algo-multiple-pro-ui\data\top_bottom.json"
    fractals = []
    with open(path, 'r') as file:
        fractals = json.load(file)
    return fractals
# 测试数据

fractals = read_top_bottom()
# 测试数据：
# fractals = [
#     {'type': 'bottom', 'index': 2, 'high': 5576, 'low': 5568},
#     {'type': 'top', 'index': 3, 'high': 5579, 'low': 5574},
#     {'type': 'bottom', 'index': 4, 'high': 5575, 'low': 5561},
#     {'type': 'top', 'index': 8, 'high': 5602, 'low': 5593},
#     {'type': 'bottom', 'index': 10, 'high': 5593, 'low': 5584},
#     {'type': 'top', 'index': 12, 'high': 5610, 'low': 5597},
#     {'type': 'bottom', 'index': 16, 'high': 5594, 'low': 5580},
#     {'type': 'top', 'index': 18, 'high': 5600, 'low': 5597},
#     {'type': 'bottom', 'index': 22, 'high': 5584, 'low': 5577},
#     {'type': 'top', 'index': 23, 'high': 5587, 'low': 5582},
#     {'type': 'bottom', 'index': 24, 'high': 5584, 'low': 5579},
#     {'type': 'top', 'index': 25, 'high': 5598, 'low': 5589},
#     {'type': 'bottom', 'index': 27, 'high': 5591, 'low': 5580},
#     {'type': 'top', 'index': 30, 'high': 5605, 'low': 5596},
# ]



bi_list = calculate_bi(fractals)
for bi in bi_list:
    print(bi)
