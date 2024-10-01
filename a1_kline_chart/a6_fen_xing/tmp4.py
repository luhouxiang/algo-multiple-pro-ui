def calculate_bi(fractals):
    # 第一步：按照 index 升序排序分型集合
    fractals.sort(key=lambda x: x['index'])

    # 第二步：合并处理相邻的分型
    fractals = process_fractals(fractals)

    # 第三步：生成笔
    bi_list = generate_bi(fractals)
    return bi_list



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


def process_fractals(fractals):
    i = 0
    length = len(fractals)
    result = []

    while i < length:
        current = fractals[i]
        result.append(current)
        j = i + 1

        while j < length:
            next_fractal = fractals[j]

            if current['type'] != next_fractal['type']:
                if should_skip_different_type(current, next_fractal):
                    j += 1
                else:
                    break  # 满足条件，处理下一个分型
            else:
                # 处理相同类型的相邻分型
                current = update_current_fractal(current, next_fractal)
                result[-1] = current
                j += 1

            i = j  # 更新外层循环的索引

        else:
            i = j  # 内层循环没有 break，更新 i

    return result

def should_skip_different_type(current, next_fractal):
    """
    判断不同类型的相邻分型之间是否需要跳过
    """
    k_lines_included = next_fractal['index'] - current['index'] + 1
    if k_lines_included < 5:
        # 如果包含的 K 线数量少于 5，跳过 next_fractal
        return True
    else:
        # 满足条件，不跳过
        return False

def update_current_fractal(current, next_fractal):
    """
    处理相同类型的相邻分型，更新 current 分型
    """
    if current['type'] == 'top':
        if current['high'] <= next_fractal['high']:
            # 更新为更高的顶
            return next_fractal
        else:
            # 保持 current 不变
            return current
    elif current['type'] == 'bottom':
        if current['low'] >= next_fractal['low']:
            # 更新为更低的底
            return next_fractal
        else:
            # 保持 current 不变
            return current
    else:
        # 如果类型既不是 top 也不是 bottom，保持不变
        return current


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
