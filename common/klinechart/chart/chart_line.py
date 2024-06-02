from PySide6 import QtCore, QtGui
from common.klinechart.chart.object import DataItem
from .chart_base import ChartBase
from .manager import BarManager


class ChartLine(ChartBase):
    """
    曲线图
    """

    def __init__(self, layout_index, chart_index, manager: BarManager):
        """"""
        super().__init__(layout_index, chart_index, manager)

    def _draw_bar_picture(self, ix: int, old_bar: DataItem, bar: DataItem) -> QtGui.QPicture:
        """"""
        # Create objects
        line_picture = QtGui.QPicture()
        painter = QtGui.QPainter(line_picture)
        if bar:
            for i in range(1, len(bar)):
                if i < len(self._pens) + 1:
                    painter.setPen(self._pens[i - 1])
                else:
                    painter.setPen(self._up_pen)
                if old_bar[i] == 0 and bar[i] == 0:
                    continue
                painter.drawLine(
                    QtCore.QPointF(ix - 1, old_bar[i]),
                    QtCore.QPointF(ix, bar[i])
                )

        # Finish
        painter.end()
        return line_picture

    def get_info_text(self, ix: int) -> str:
        """
        Get information text to show by cursor.
        """
        bar = self.get_bar_from_index(ix)

        if bar:
            text = ""
            for i in range(1, len(bar) - 1):
                if len(self._params) >= i:
                    text += "{}:".format(self._params[i - 1])
                text += "{:.2f}, ".format(bar[i])  # f"{(bar[i])}, "
                # if i % 2 == 0:
                text += "\n"
            if len(self._params) >= len(bar) - 1:
                text += "{}:".format(self._params[len(bar) - 1 - 1])
            text += "{:.2f}".format(bar[-1])  # f"{(bar[-1])}"
        else:
            text = ""

        return text

