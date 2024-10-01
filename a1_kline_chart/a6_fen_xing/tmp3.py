def calculate_bi(fractals):
    # 第一步：排序分型集合
    fractals.sort(key=lambda x: x['index'])

    while True:
        changed = False
        # 步骤2：处理不同类型的相邻分型
        changed = deal_diff_type(changed, fractals, 0)

        # 步骤3：处理相同类型的相邻分型
        changed = deal_same_type(changed, fractals, 0)

        # 步骤4：检查是否有更改
        if not changed:
            break  # 没有更改，退出循环

    # 步骤5：生成笔
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


def deal_same_type(changed, fractals, i):
    while i < len(fractals) - 1:
        f1 = fractals[i]
        f2 = fractals[i + 1]
        if f1['type'] == f2['type']:
            if f1['type'] == 'top':
                if f1['high'] <= f2['high']:
                    # 删除前一个顶
                    del fractals[i]
                    changed = True
                    break  # 发生更改，跳出循环重新开始
                else:
                    # 删除后一个顶
                    del fractals[i + 1]
                    changed = True
                    break
            elif f1['type'] == 'bottom':
                if f1['low'] >= f2['low']:
                    # 删除前一个底
                    del fractals[i]
                    changed = True
                    break  # 发生更改，跳出循环重新开始
                else:
                    # 删除后一个底
                    del fractals[i + 1]
                    changed = True
                    break
        else:
            i += 1  # 类型不同，继续
    return changed


def deal_diff_type(changed, fractals, i):
    while i < len(fractals) - 1:
        f1 = fractals[i]
        f2 = fractals[i + 1]
        if f1['type'] != f2['type']:
            k_lines_included = f2['index'] - f1['index'] + 1
            if k_lines_included < 5:
                # 删除后一个分型
                del fractals[i + 1]
                changed = True
                break  # 发生更改，跳出循环重新开始
            else:
                i += 1
        else:
            i += 1  # 类型相同，先跳过，在步骤3处理
    return changed


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
