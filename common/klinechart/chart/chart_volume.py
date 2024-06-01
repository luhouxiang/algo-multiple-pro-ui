from PySide6 import QtCore, QtGui
from common.klinechart.chart.object import DataItem
from .chart_base import ChartBase
from .base import BAR_WIDTH
from .manager import BarManager


class ChartVolume(ChartBase):
    """
    成交量图
    """

    def __init__(self, layout_index, chart_index, manager: BarManager):
        """"""
        super().__init__(layout_index, chart_index, manager)

    def _draw_bar_picture(self, ix: int, old_bar: DataItem, bar: DataItem) -> QtGui.QPicture:
        """"""
        # Create objects
        volume_picture = QtGui.QPicture()
        painter = QtGui.QPainter(volume_picture)

        # Set painter color
        # if bar.close_price >= bar.open_price:
        painter.setPen(self._yellow_pen)
        painter.setBrush(self._yellow_brush)
        # else:
        #     painter.setPen(self._down_pen)
        #     painter.setBrush(self._down_brush)

        # Draw volume body
        if bar:
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
            text = f"Volume {bar[1]}"
        else:
            text = ""

        return text

