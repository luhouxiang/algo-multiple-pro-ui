from common.model.kline import KLine
from common.model.obj import Direction
from typing import List
from datetime import datetime
import math


class WeiBI:
    """微笔"""
    def __init__(self, symbol: str, direction: Direction, bars: List[KLine]):
        self.symbol = symbol
        self.direction: Direction = direction
        self.bars: List[KLine] = bars
        self._sdt = None
        self._edt = None

    @property
    def sdt(self):
        self._sdt = datetime.fromtimestamp(self.bars[0].time)
        return self._sdt

    @property
    def edt(self):
        self._edt = datetime.fromtimestamp(self.bars[-1].time)
        return self._edt

    def __str__(self):
        if self.direction == Direction.Up:
            return f"WeiBI(symbol={self.symbol}, sdt={self.sdt}, edt={self.edt}, " \
                   f"direction={self.direction}, low={self.low}, high={self.high})"
        else:
            return f"WeiBI(symbol={self.symbol}, sdt={self.sdt}, edt={self.edt}, " \
                   f"direction={self.direction}, high={self.high}, low={self.low})"

    def __repr__(self):
        return self.__str__()

    @property
    def high(self):
        if self.direction == Direction.Up:
            return self.bars[-1].high
        else:
            return self.bars[0].high

    @property
    def low(self):
        if self.direction == Direction.Up:
            return self.bars[0].low
        else:
            return self.bars[-1].low

    @property
    def low_close(self):
        return min([x.close for x in self.bars])

    @property
    def angle(self):  # 角度
        if self.direction == Direction.Up:
            return math.atan2(self.high - self.low_close, max(len(self.bars) - 1, 1)) / math.pi * 180
        else:
            return math.atan2(self.low_close - self.high, max(len(self.bars) - 1, 1)) / math.pi * 180


def get_weibi_list(ks: List[KLine], N=5) -> List[WeiBI]:
    hs, ls = [x.high for x in ks], [x.low for x in ks]
    sel = 0
    M = len(ks)
    tbs = []
    for i in range(M):
        mx = max(hs[max(i - N, 0):min(i + N, M)])
        mn = min(ls[max(i - N, 0):min(i + N, M)])
        if sel <= 0:  # 找到底后找顶
            if hs[i] == mx:
                if sel == 0:
                    tbs.append([0, -1])
                tbs.append([i, 1])  # 顶
                sel = 1
            if tbs and ls[i] == mn and ls[i] < ls[tbs[-1][0]]:  # 找到更低的底
                tbs[-1][0] = i
        if sel >= 0:
            if ls[i] == mn:
                if sel == 0:
                    tbs.append([0, 1])
                tbs.append([i, -1])
                sel = -1
            if tbs and hs[i] == mx and hs[i] > hs[tbs[-1][0]]:  #
                tbs[-1][0] = i

    bi_list: List[WeiBI] = []
    for i in range(len(tbs) - 1):
        line: List[KLine] = []
        for j in range(tbs[i][0], tbs[i + 1][0] + 1):
            line.append(ks[j])
        bi_list.append(
            WeiBI(symbol=ks[0].symbol, direction=Direction.Up if tbs[i][1] == -1 else Direction.Down, bars=line))
    line = []
    for j in ks[tbs[-1][0]:]:
        line.append(j)
    if line:
        bi_list.append(
            WeiBI(symbol=ks[0].symbol, direction=Direction.Up if tbs[-1][1] == -1 else Direction.Down, bars=line))

    return bi_list
