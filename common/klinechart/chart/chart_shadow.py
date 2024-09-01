# -*- coding: utf-8 -*-
"""
@author: luhx
@desc: 在原有candle的基础上针对每一个K线加上阴影
"""

from PySide6 import QtCore, QtGui
from common.klinechart.chart.object import DataItem
from .chart_base import ChartBase
from .base import BAR_WIDTH
from .manager import BarManager


class ChartShadow(ChartBase):
    """
    K线图
    """

    def __init__(self, layout_index, chart_index, manager: BarManager):
        """"""
        super().__init__(layout_index, chart_index, manager)
        self._shadow_brush_up = QtGui.QBrush(QtGui.QColor(255, 125, 125, 120))  # 半透明红色
        self._shadow_brush_down = QtGui.QBrush(QtGui.QColor(0, 200, 255, 120))  # 半透明绿色

        """
        UP_COLOR = (255, 75, 75)
        DOWN_COLOR = (0, 255, 255)
        """
    def _draw_bar_picture(self, ix: int, old_bar: DataItem, bar: DataItem) -> QtGui.QPicture:
        """
        DataItem: bar[0]存时间，bar[1]存最低， bar[2]存最高
        """
        # Create objects
        candle_picture = QtGui.QPicture()
        painter = QtGui.QPainter(candle_picture)

        # Draw the semi-transparent yellow rectangle shadow
        if bar:
            cur_shadow_brush = self._shadow_brush_up if bar[-1] == 1 else self._shadow_brush_down
            count = bar[4] - bar[3] + 1
            for i in range(count):
                if i == 0:
                    shadow_rect = QtCore.QRectF(
                        ix + i - (BAR_WIDTH + 0.1),
                        bar[1],  # Lowest price
                        (BAR_WIDTH + 0.1) * 2,
                        bar[2] - bar[1]
                    )
                else:
                    shadow_rect = QtCore.QRectF(
                        ix + i - (BAR_WIDTH + 0.1 + 0.1 + 0.1),
                        bar[1],  # Lowest price
                        (BAR_WIDTH + 0.2) * 2,
                        bar[2] - bar[1]
                    )
                painter.fillRect(shadow_rect, cur_shadow_brush)

        # Finish
        painter.end()
        return candle_picture
    # def _draw_item_picture(self, min_ix: int, max_ix: int) -> None:
    #     """
    #     Draw the picture of item in specific range.
    #     """
    #     if min_ix is None or max_ix is None:
    #         return
    #     """
    #     Draw the picture of item in specific range.
    #     """
    #     self._item_picuture = QtGui.QPicture()
    #     painter = QtGui.QPainter(self._item_picuture)
    #     if min_ix > 0:
    #         old_bar = self.get_bar_from_index(min_ix - 1)
    #     else:
    #         old_bar = self.get_bar_from_index(min_ix)
    #     for ix in range(min_ix, max_ix):
    #         bar_picture = self._bar_picutures[ix]
    #
    #         if bar_picture is None:
    #             cur_bar = self.get_bar_from_index(ix)
    #             bar_picture = self._draw_bar_picture(ix, old_bar, cur_bar)
    #             self._bar_picutures[ix] = bar_picture
    #             old_bar = cur_bar
    #
    #         bar_picture.play(painter)
    #
    #     painter.end()
        #
        # self._item_picuture = QtGui.QPicture()
        # painter = QtGui.QPainter(self._item_picuture)
        # # if not self._discrete_list:
        # #     return
        # # for item in self._discrete_list:
        # #     x1 = self.get_index(item[0])
        # #     if x1 is None:
        # #         print("********item[0]:{}".format(item[0]))
        # #     y1 = item[1]
        # #     x2 = self.get_index(item[2])
        # #     if x2 is None:
        # #         print("********item[2]:{}".format(item[2]))
        # #     y2 = item[3]
        # #     p = 0
        # #     if x2 == x1:
        # #         p = 0
        # #     else:
        # #         p = (y2 - y1) / (x2 - x1)
        # #
        # #     if item[4] == 0:
        # #         pass  # 线段
        # #     elif item[4] == 2:  # 直线
        # #         x1 = min_ix
        # #         y1 = y2 - p * (x2 - x1)
        # #         x2 = max_ix
        # #         y2 = p * (x2 - x1) + y1
        # #     elif item[4] == 1:  # 射线
        # #         x2 = max_ix
        # #         y2 = p * (x2 - x1) + y1
        # #     bar_picture = self._draw_bar_picture(x1, y1, x2, y2)
        # #     bar_picture.play(painter)
        # painter.end()

    # def _draw_bar_picture(self, x1: int, y1: float, x2: int, y2: float) -> QtGui.QPicture:
    #     """"""
    #     # Create objects
    #     line_picture = QtGui.QPicture()
    #     painter = QtGui.QPainter(line_picture)
    #
    #     painter.setPen(self._pens[-1])
    #     painter.drawLine(
    #         QtCore.QPointF(x1, y1),
    #         QtCore.QPointF(x2, y2)
    #     )
    #     # Finish
    #     painter.end()
    #     return line_picture
    # def _draw_bar_picture(self, ix: int, old_bar: DataItem, bar: DataItem) -> QtGui.QPicture:
    #     """"""
    #     # Create objects
    #     volume_picture = QtGui.QPicture()
    #     painter = QtGui.QPainter(volume_picture)
    #
    #     # Set painter color
    #     # if bar.close_price >= bar.open_price:
    #     if bar:
    #         # if bar[1] > 0:
    #         #     painter.setPen(self._up_pen)
    #         #     painter.setBrush(self._up_brush)
    #         # else:
    #         painter.setPen(self._down_pen)
    #         painter.setBrush(self._down_brush)
    #         if bar[1]:
    #             rect = QtCore.QRectF(
    #                 ix - BAR_WIDTH,
    #                 0,
    #                 BAR_WIDTH * 2,
    #                 bar[1]
    #             )
    #             painter.drawRect(rect)
    #     # Finish
    #     painter.end()
    #     return volume_picture

    def get_info_text(self, ix: int) -> str:
        """
        Get information text to show by cursor.
        """
        # bar = self.get_bar_from_index(ix)
        # if not bar:
        #     text = ""
        # else:
        #     if self.__class__.__name__ == "ChartShadow":
        #         words = [f'Date:{bar[0].strftime("%Y-%m-%d")}', f'Time:{bar[0].strftime("%H:%M")}',
        #                  f'Open:{str(bar[1])}', f'High :{str(bar[2])}', f"low   :{str(bar[3])}",
        #                  f"close:{str(bar[4])}", f'index:{str(ix)}']
        #     else:
        #         words = [str(bar[i]) for i in range(1, len(bar))]
        #     text = "\n".join(words)
        # return text
        return ""
