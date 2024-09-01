from typing import Tuple
from PySide6 import QtCore, QtGui
from common.klinechart.chart.object import DataItem
from .chart_base import ChartBase
from .base import BAR_WIDTH
from .manager import BarManager
import logging

class ChartSignal(ChartBase):
    """
    信号附图
    """

    def __init__(self, layout_index, chart_index, manager: BarManager):
        """"""
        super().__init__(layout_index, chart_index, manager)

    # def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
    #     """
    #     Get range of y-axis with given x-axis range.
    #
    #     If min_ix and max_ix not specified, then return range with whole data set.
    #     """
    #     min_value, max_value = self._manager.get_layout_range(self._layout_index, min_ix, max_ix)
    #     return min_value, max_value
    def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """
        Get range of y-axis with given x-axis range.

        If min_ix and max_ix not specified, then return range with whole data set.
        """
        min_value, max_value = self._manager.get_layout_range(self._layout_index, min_ix, max_ix)
        # logging.info("get_y_range::min_max_value:【{}，{}】".format(min_value, max_value))
        return min_value, max_value
    def _draw_bar_picture(self, ix: int, old_bar: DataItem, bar: DataItem) -> QtGui.QPicture:
        """"""
        # Create objects
        volume_picture = QtGui.QPicture()
        painter = QtGui.QPainter(volume_picture)

        # Set painter color
        # if bar.close_price >= bar.open_price:
        if bar:
            if bar[1] > 0:
                painter.setPen(self._up_pen)
                painter.setBrush(self._up_brush)
            else:
                painter.setPen(self._down_pen)
                painter.setBrush(self._down_brush)
            if bar[1]:
                rect = QtCore.QRectF(
                    ix - BAR_WIDTH,
                    0,
                    BAR_WIDTH * 2,
                    bar[1]
                )
                painter.drawRect(rect)
        # Finish
        painter.end()
        return volume_picture

    def get_info_text(self, ix: int) -> str:
        """
        Get information text to show by cursor.
        """
        bar = self.get_bar_from_index(ix)

        if bar:
            text = f"signal: {bar[1]}"
            # logging.info(f"signal: {bar[1]}")
        else:
            text = "signal: -"

        return text

