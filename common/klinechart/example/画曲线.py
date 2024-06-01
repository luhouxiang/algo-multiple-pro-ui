# -*- coding: utf-8 -*-
""" 画曲线的示意代码
"""
from PySide6.QtWidgets import QApplication, QMainWindow
import pyqtgraph as pg
import sys


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

        hour = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        temperature = [30, 32, 34, 32, 33, 31, 29, 32, 35, 45]
        temperature2 = [31, 33, 35, 33, 34, 32, 32, 35, 38, 49]

        # plot data: x, y values
        self.graphWidget.plotItem(hour, temperature, temperature2)
        # self.graphWidget.plot(hour, temperature2)


app = QApplication(sys.argv)
w = MainWindow()
w.show()
app.exec_()
