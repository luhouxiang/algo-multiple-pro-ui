import os, sys, re
from PySide6 import QtCore, QtWidgets
if "PyQt5" in sys.modules:
    del sys.modules["PyQt5"]

from common.klinechart.chart import ChartWidget, ChartVolume, ChartCandle, ChartMacd,\
    ChartArrow, ChartLine, ChartStraight, ChartSignal, ItemIndex, ChartShadow
from common.klinechart.chart.object import DataItem
from common.klinechart.chart import PlotIndex, BarDict, PlotItemInfo, ChartItemInfo
from common.utils import file_txt
from common.algo.zigzag import OnCalculate
from common.algo.weibi import get_weibi_list
from common.callback.call_back import *
from common.klinechart.chart.keyboard_genie_window import KeyboardGenieWindow
from common.utils.pinyin_util import get_pinyin_first_letters


def calc_zig_zag(klines: List[KLine]):
    zig_zag = OnCalculate(klines)
    return zig_zag


def obtain_data_from_algo(klines: list[KLine], data: Dict[PlotIndex, PlotItemInfo]):
    calc_zig_zag(klines)
    for plot_index in data.keys():
        plot_item_info:PlotItemInfo = data[plot_index]
        for item_index in plot_item_info:
            info: ChartItemInfo = plot_item_info[item_index]
            if not info.bars and info.func_name:
                if info.type == "Straight":
                    info.discrete_list = globals()[info.func_name](klines)
                else:
                    info.bars = globals()[info.func_name](klines)


def load_data_from_conf(conf: Dict[str, any]) -> Dict[PlotIndex, PlotItemInfo]:  # 从文件中读取数据
    """
    返回以layout_index, index为key的各item的kl_data_list
    """
    local_data: Dict[PlotIndex, PlotItemInfo] = {}
    plots = conf["plots"]
    for plot_index, plot in enumerate(plots):
        plot_info: PlotItemInfo = {}
        for item_index, item in enumerate(plot["chart_item"]):
            item_info: ChartItemInfo = ChartItemInfo()
            item_info.type = item["type"]
            item_info.params = item["params"] if "params" in item else []
            item_info.func_name = item["func_name"] if "func_name" in item else ""
            item_info.data_type = item["data_type"] if "data_type" in item else []
            file_name = item["file_name"]
            base_path = conf["conf"]["base_path"]
            if file_name:   # 存在则读取文件
                kline_count = conf["conf"]["kline_count"] if conf["conf"]["kline_count"] else 1000
                file_list = file_txt.list_only_files(base_path)
                file_name = file_txt.find_first_file(file_name, file_list)
                start_dt = conf["conf"]["start_dt"] if "start_dt" in conf["conf"] else ""
                end_dt = conf["conf"]["end_dt"] if "end_dt" in conf["conf"] else ""
                data_list = file_txt.tail_kline(f'{base_path}/{file_name}', kline_count, start_dt, end_dt)
            else:
                data_list = []  # 否则直接返回空列表
            bar_dict: BarDict = calc_bars(data_list, item_info.data_type)
            item_info.bars = bar_dict
            plot_info[ItemIndex(item_index)] = item_info
            logging.info(F"file_name: {file_name}")
            logging.info(F"plot_index:{plot_index}, item_index:{item_index}, len(bar_dict)={len(bar_dict)}")
        local_data[PlotIndex(plot_index)] = plot_info

    return local_data


def calc_bars(data_list, data_type: List[str]) -> BarDict:
    bar_dict: BarDict = {}
    for data_index, txt in enumerate(data_list):
        # logging.info(F"txt:{txt}")
        bar = DataItem(txt, data_type)
        if bar:
            bar_dict[bar[0]] = bar
    return bar_dict


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, conf):
        super().__init__()
        self.conf = conf
        self.widget = ChartWidget(self)

        self.add_chart_item(conf["plots"], self.widget)

        self.widget.add_cursor()

        # datas: Dict[PlotIndex, PlotItemInfo] = load_data_from_conf(self.conf)
        # self.widget.update_all_history_data(datas, obtain_data_from_algo)
        self.load_data_from_file_name()

        self.setCentralWidget(self.widget)

        # 加载股票代码和名称列表
        self.code_name_list, self.code_file_dic = self.load_keyboard_sprite_data()

        # 创建键盘精灵窗口

        self.keyboard_genie = KeyboardGenieWindow(self)
        self.keyboard_genie.funcs = self.load_data_from_file_name


    def load_data_from_file_name(self, code=""):
        self.widget.clear_all()
        if code:
            file_name = self.code_file_dic[code]
            # print(self.conf["plots"])
            self.conf["plots"][0]["chart_item"][0]["file_name"] = file_name
        datas: Dict[PlotIndex, PlotItemInfo] = load_data_from_conf(self.conf)
        self.widget.update_all_history_data(datas, obtain_data_from_algo)
        file_name = self.conf["plots"][0]["chart_item"][0]["file_name"]
        print("file_name: ", file_name)
        # 将 file_name 设置到窗口标题中
        if code:
            self.setWindowTitle(code)
        else:
            self.setWindowTitle(file_name)

        self.widget.update_all_view()
        self.widget._update_y_range()
        self.widget.scene().update()  # 请求QGraphicsScene更新绘制
        self.widget.viewport().update()  # 请求QGraphicsView更新

    def add_chart_item(self, plots: List[Any], widget: ChartWidget):
        for plot_index, plot in enumerate(plots):
            if plot_index != len(plots) - 1:
                axis = True
            else:
                axis = False
            widget.add_plot(hide_x_axis=axis, maximum_height=plots[plot_index]["max_height"])  # plot
            for index, chart_item in enumerate(plot["chart_item"]):
                if chart_item["type"] == "Candle":
                    widget.add_item(plot_index, ChartCandle)
                elif chart_item["type"] == "Volume":
                    widget.add_item(plot_index, ChartVolume)
                elif chart_item["type"] == "Line":  # 曲线
                    widget.add_item(plot_index, ChartLine)
                elif chart_item["type"] == "Macd":
                    widget.add_item(plot_index, ChartMacd)
                elif chart_item["type"] == "Arrow":
                    widget.add_item(plot_index, ChartArrow)
                elif chart_item["type"] == "Straight":  # 直线
                    widget.add_item(plot_index, ChartStraight)
                elif chart_item["type"] == "Signal":
                    widget.add_item(plot_index, ChartSignal)
                elif chart_item["type"] == "Shadow":
                    widget.add_item(plot_index, ChartShadow)
                else:
                    raise "not match item"


    def load_keyboard_sprite_data(self):
        base_path = self.conf["conf"]["base_path"]
        # 示例：从文件或数据库加载股票列表
        # 此处使用简单的列表作为示例
        # 定义文件名匹配的正则表达式
        # ^\d+ 表示文件名以数字开头
        # # 表示紧跟一个井号
        # .* 表示任意字符（中间部分可有多种形式）
        # L9\.txt$ 以 L9.txt 结尾

        pattern = re.compile(r'^\d+#[^#]*L9\.txt$')
        items = []
        dic: Dict[str, str] = {}
        for file_name in os.listdir(base_path):
            if pattern.match(file_name):
                file_path = os.path.join(base_path, file_name)
                with open(file_path, 'r', encoding='gb2312') as f:
                    first_line = f.readline().strip()
                    fields = first_line.split()
                    if len(fields) >= 2:
                        code = fields[0].strip()
                        name = fields[1].strip()
                        pinyin = get_pinyin_first_letters(name)
                        items.append({'code': code, 'name': name, 'pinyin': pinyin})
                        dic[code] = file_name
        return items, dic
        #
        # items = [
        #     {'code': '600519', 'name': '贵州茅台'},
        #     {'code': '000001', 'name': '平安银行'},
        #     {'code': '000002', 'name': '万科A'},
        #     {'code': '600036', 'name': '招商银行'},
        #     {'code': '600837', 'name': '海通证券'},
        #     # ... 更多股票代码和名称 ...
        # ]
        # return items, []

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Escape:
            self.stock_list = []
            self.keyboard_genie.hide()
        else:
            text = event.text()
            if text.isalnum() or text.isalpha() or text.isdigit():
                if not self.keyboard_genie.isVisible():
                    self.keyboard_genie.show()
                    self.update_keyboard_genie_position()
                    # 激活键盘精灵窗口并提升到最前
                    self.keyboard_genie.activateWindow()
                    self.keyboard_genie.raise_()
                    # 将焦点设置到键盘精灵的输入框
                    self.keyboard_genie.input_line_edit.setFocus()
                    # 清空输入框并设置初始值
                    self.keyboard_genie.input_line_edit.clear()
                    self.keyboard_genie.input_line_edit.setText(text)

                # # 将焦点设置到键盘精灵的输入框，并添加按下的字符
                # self.keyboard_genie.input_line_edit.setFocus()
                # current_text = self.keyboard_genie.input_line_edit.text()
                # self.keyboard_genie.input_line_edit.setText(current_text + text)
            else:
                super().keyPressEvent(event)

    def moveEvent(self, event):
        super().moveEvent(event)
        self.update_keyboard_genie_position()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_keyboard_genie_position()

    def update_keyboard_genie_position(self):
        if self.keyboard_genie.isVisible():
            # 获取主窗口的全局位置
            main_window_pos = self.mapToGlobal(QtCore.QPoint(0, 0))
            main_window_size = self.size()
            genie_size = self.keyboard_genie.sizeHint()
            x = main_window_pos.x() + main_window_size.width() - genie_size.width()
            y = main_window_pos.y() + main_window_size.height() - genie_size.height()
            self.keyboard_genie.move(x, y)

    # def on_input_text_changed(self, text):
    #     self.update_matching_list(text)
    #
    # def on_item_double_clicked(self, item):
    #     selected_stock_code = item.data(QtCore.Qt.UserRole)
    #     print(f"选中股票代码：{selected_stock_code}")
    #     # 在这里加载股票数据并更新图表
    #     self.keyboard_genie.close()

    def update_matching_list(self, input_text):
        matching_stocks = []
        input_upper = input_text.strip().upper()
        if input_upper:
            for stock in self.code_name_list:
                if input_upper in stock['code'] or input_upper in stock['pinyin'].upper():
                    matching_stocks.append(stock)

        self.keyboard_genie.matching_list_widget.clear()
        for stock in matching_stocks:
            item_text = f"{stock['code']} - {stock['name']}"
            item = QtWidgets.QListWidgetItem(item_text)
            item.setData(QtCore.Qt.UserRole, stock['code'])
            self.keyboard_genie.matching_list_widget.addItem(item)

        if matching_stocks:
            self.keyboard_genie.matching_list_widget.setCurrentRow(0)
        else:
            pass


app = QtWidgets.QApplication(sys.argv)

