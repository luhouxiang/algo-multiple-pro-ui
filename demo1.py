from collections import namedtuple

# 定义K线结构
Kline = namedtuple('Kline', ['high', 'low'])

# 定义分型结构
Fenxing = namedtuple('Fenxing', ['index', 'type', 'kline'])

# 定义笔结构
class Bi:
    def __init__(self, start_fenxing, end_fenxing):
        self.start = start_fenxing  # 开始的分型
        self.end = end_fenxing      # 结束的分型

    def __repr__(self):
        return f"Bi({self.start.index}, {self.end.index})"

def calculate_bis(fenxings):
    """
    计算笔列表
    fenxings: 分型列表 (顶分型: type = 'top', 底分型: type = 'bottom')
    """

    # 第一步：过滤掉不符合标准的分型
    filtered_fenxings = []

    for i in range(len(fenxings)):
        if i > 0 and fenxings[i].type == fenxings[i-1].type:
            # 如果是相同类型的分型，对于顶，前面的低于后面的；对于底，前面的高于后面的，删除不符合的分型
            if fenxings[i].type == 'top' and fenxings[i].kline.high > fenxings[i-1].kline.high:
                filtered_fenxings[-1] = fenxings[i]
            elif fenxings[i].type == 'bottom' and fenxings[i].kline.low < fenxings[i-1].kline.low:
                filtered_fenxings[-1] = fenxings[i]
            else:
                continue  # 如果前一个点符合标准，就丢弃当前分型
        else:
            filtered_fenxings.append(fenxings[i])

    # 第二步：相邻的顶和底形成一笔
    bis = []
    i = 1

    while i < len(filtered_fenxings):
        # 确保顶和底之间至少有5根K线
        if filtered_fenxings[i].index - filtered_fenxings[i-1].index < 5:
            i += 1
            continue

        # 相邻的顶和底构成一笔
        if filtered_fenxings[i-1].type == 'bottom' and filtered_fenxings[i].type == 'top':
            # 确保笔的最低点在底分型，最高点在顶分型
            if filtered_fenxings[i].kline.high > filtered_fenxings[i-1].kline.low:
                bis.append(Bi(filtered_fenxings[i-1], filtered_fenxings[i]))
        elif filtered_fenxings[i-1].type == 'top' and filtered_fenxings[i].type == 'bottom':
            # 确保笔的最高点在顶分型，最低点在底分型
            if filtered_fenxings[i].kline.low < filtered_fenxings[i-1].kline.high:
                bis.append(Bi(filtered_fenxings[i-1], filtered_fenxings[i]))

        i += 1

    return bis


# 示例数据
fenxings = [
    Fenxing(0, 'bottom', Kline(100, 95)),
    Fenxing(1, 'top', Kline(105, 102)),
    Fenxing(6, 'bottom', Kline(98, 93)),
    Fenxing(11, 'top', Kline(110, 108)),
    Fenxing(17, 'bottom', Kline(101, 96)),
]

# 计算笔
bis = calculate_bis(fenxings)
for bi in bis:
    print(bi)
