import os
import sys
import string
import itertools
import numpy as np
from src import GUI
from PIL import Image
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox, QHeaderView


class Main(QMainWindow, GUI.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setAcceptDrops(True)
        self.plainTextEdit.setAcceptDrops(False)

        self.setWindowIcon(QtGui.QIcon("./images/Logo.ico")) # 设置软件图标
        self.setFixedSize(self.width(), self.height()) # 禁止窗口最大化
        self.tableWidget.verticalHeader().setVisible(False) # 表格不显示表头

        # 信号
        self.img = None
        self.character = f"{string.digits}, "
        self.pushButton.clicked.connect(self.show_info)
        self.pushButton_2.clicked.connect(self.save_img)

    def get_text(self):
        if (text := self.plainTextEdit.toPlainText()) == "":
            QMessageBox.information(self, "温馨提示", "您输入的内容为空!", QMessageBox.Yes)
        elif all(i in self.character for i in text):
            return text
        else:
            QMessageBox.information(self, "温馨提示", "您输入的内容不符合标准!", QMessageBox.Yes)

    def get_radioButtonState(self):
        if self.radioButton.isChecked():
            return 1
        elif self.radioButton_2.isChecked():
            return 2

    def get_frequency(self):
        if self.img is not None:
            dic = {}
            for y, x in itertools.product(range(self.img.height), range(self.img.width)):
                color = self.img.getpixel((x, y))
                if dic.get(color, None):
                    dic[color] += 1
                else:
                    dic[color] = 1

            # 从大到小排序
            sort_info = sorted(dic.items(), key=lambda i:i[1], reverse=True) # [('e', 39915), ... ('z', 264)]

            # 获取总颜色数量
            number = sum(num for _, num in sort_info)

            # 添加频率
            table_info = []
            for index, (character, num) in enumerate(sort_info):
                if num != 0:
                    frequency = round((num / number) * 100, 4)
                    table_info.append((index + 1, character, num, frequency))
            return table_info
        else:
            QMessageBox.information(self, "温馨提示", "您没有拖入图片!", QMessageBox.Yes)

    def show_info(self):
        if (table_info := self.get_frequency()) is None:
            return
        self.tableWidget.setRowCount(len(table_info))
        for x in range(self.tableWidget.rowCount()):
            for y in range(self.tableWidget.columnCount()):
                item = QTableWidgetItem(str(table_info[x][y]))
                if y == 1:
                    # item = QTableWidgetItem('#' + ''.join(hex(i)[2:].zfill(2) for i in table_info[x][y]))
                    im = np.zeros((100, 100, 3))
                    im += table_info[x][y]
                    im = im.astype(np.uint8)
                    im = QtGui.QImage(im.data, im.shape[1], im.shape[0], im.shape[1]*3, QtGui.QImage.Format_RGB888)
                    pix = QtGui.QPixmap(im)
                    item.setIcon(QtGui.QIcon(pix))
                item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter) # 每列设置水平垂直居中
                self.tableWidget.setItem(x, y, item)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # 第2列自适应列宽

    def save_img(self):
        if (table_info := self.get_frequency()) is not None and (text := self.get_text()) is not None:
            lis = text.split(",")
            if " " in lis:
                lis.remove(" ")
            elif "" in lis:
                lis.remove("")
            all_i = [int(i.strip()) for i in lis]
            colors = [table_info[i - 1][1] for i in all_i]

            self.workThread = WorkThread(colors, choice=self.get_radioButtonState())
            # self.workThread.end.connect(lambda x: self.pushButton_2.setEnabled(x))
            self.workThread.start()

    def dragEnterEvent(self, e: QtGui.QDragEnterEvent) -> None:
        super().dragEnterEvent(e)
        self.file_path = e.mimeData().text().replace('file:///', '')
        self.base_dir = os.path.dirname(self.file_path)
        self.file_name = self.file_path.split("/")[-1]
        if self.file_path.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tif', '.gif')):
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e: QtGui.QDropEvent) -> None:
        super().dropEvent(e)
        if os.path.exists(self.file_path):
            self.img = Image.open(self.file_path).convert('RGB')
            self.label.setPixmap(QtGui.QPixmap(self.file_path).scaled(self.label.width(), self.label.height()))
        else:
            QMessageBox.critical(self, "温馨提示", "文件不存在!", QMessageBox.Yes)

class WorkThread(QtCore.QThread):
    # end = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, colors, choice) -> None:
        super().__init__()
        self.colors = colors
        self.choice = choice

    def run(self):
        if self.choice == 1:
            new_img = Image.new("RGB", (ui.img.width, ui.img.height), color=(255, 255, 255))
            for y, x in itertools.product(range(ui.img.height), range(ui.img.width)):
                color = ui.img.getpixel((x, y))
                if color in self.colors:
                    new_img.putpixel((x, y), color)
            new_img.save(os.path.join(ui.base_dir, f"RGB_{ui.file_name}"))
        elif self.choice == 2:
            new_img = Image.new("RGB", (ui.img.width, ui.img.height), color=(255, 255, 255))
            for y, x in itertools.product(range(ui.img.height), range(ui.img.width)):
                color = ui.img.getpixel((x, y))
                if color in self.colors:
                    new_img.putpixel((x, y), (0, 0, 0))
            new_img.save(os.path.join(ui.base_dir, f"BLACK_{ui.file_name}"))
            # self.end.emit(True)
        im = np.array(new_img, dtype=np.uint8)
        im = QtGui.QImage(im.data, im.shape[1], im.shape[0], im.shape[1]*3, QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap(im)
        ui.label_2.setPixmap(pix.scaled(ui.label_2.width(), ui.label_2.height()))

if __name__ == "__main__":
    # QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling) # DPI自适应
    app = QApplication(sys.argv)
    ui = Main()
    ui.show()
    sys.exit(app.exec_())