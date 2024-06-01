from PySide6 import  QtGui
from common.klinechart.chart.object import DataItem
from .chart_base import ChartBase
from .base import BAR_WIDTH
from .manager import BarManager
from .object import Offset


class ChartArrow(ChartBase):
    """
    箭头图
    """

    def __init__(self, layout_index, chart_index, manager: BarManager):
        """"""
        super().__init__(layout_index, chart_index, manager)

    def _draw_bar_picture(self, ix: int, old_bar: DataItem, bar: DataItem) -> QtGui.QPicture:
        from PySide6.QtCore import QPointF
        from PySide6.QtGui import QPolygonF
        """"""
        # Create objects
        volume_picture = QtGui.QPicture()
        if bar is None:
            return volume_picture

        painter = QtGui.QPainter(volume_picture)

        # Set painter color
        # if bar.close_price >= bar.open_price:
        if bar[2] == Offset.OPEN.value and bar[1] > 0:
            painter.setPen(self._up_pen)
            painter.setBrush(self._up_brush)
        else:
            painter.setPen(self._down_pen)
            painter.setBrush(self._down_brush)
        # Draw volume body

        min_value, max_value = self.get_y_range(self._rect_area[0], self._rect_area[1])
        if bar[2] == Offset.OPEN.value:
            points = QPolygonF([
                QPointF(ix, min_value + (max_value - min_value) * 0.03),
                QPointF(ix - BAR_WIDTH, min_value),
                QPointF(ix + BAR_WIDTH, min_value)
            ])
        else:
            points = QPolygonF([
                QPointF(ix, min_value),
                QPointF(ix - BAR_WIDTH, min_value + (max_value - min_value) * 0.03),
                QPointF(ix + BAR_WIDTH, min_value + (max_value - min_value) * 0.03)
            ])

        painter.drawPolygon(points)
        painter.end()

        return volume_picture

    def get_info_text(self, ix: int) -> str:
        """
        Get information text to show by cursor.
        """
        bar = self.get_bar_from_index(ix)

        if bar:
            text = f"Arrow {bar[1]}"
        else:
            text = ""

        return text

