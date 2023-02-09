import os
import re
import sys
import string
import numpy as np
from src import GUI
from PIL import Image
import matplotlib.pyplot as plt
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox, QHeaderView, QFileDialog


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
        self.character = f"{string.digits} "
        self.pushButton.clicked.connect(self.show_info)
        self.pushButton_2.clicked.connect(self.save_img)
        self.pushButton_3.clicked.connect(self.show_img)
        self.pushButton_4.clicked.connect(self.open_img)

    def get_text(self):
        if (text := self.plainTextEdit.toPlainText()) == "":
            QMessageBox.information(self, "温馨提示", "您输入的内容为空!", QMessageBox.Yes)
        elif all(i in self.character for i in text):
            return text
        else:
            QMessageBox.information(self, "温馨提示", "您输入的内容不符合标准!", QMessageBox.Yes)

    def get_ColorMode(self):
        if self.radioButton.isChecked():
            return 1
        elif self.radioButton_2.isChecked():
            return 2

    def get_radioButtonState(self):
        if self.radioButton_3.isChecked():
            return 1
        elif self.radioButton_4.isChecked():
            return 2

    def get_frequency(self):
        if self.img is not None:
            img_2d = self.np_img.reshape(-1, 3)
            unique_img, count = np.unique(img_2d, return_counts=True, axis=0)
            number = img_2d.size // 3
            table_info = [
                [tuple(unique_img[i]), count[i], round(count[i] / number * 100, 4)] for i in range(len(unique_img))
            ]
            table_info.sort(key=lambda x: x[2], reverse=True)

            # 添加序号列
            for i in range(len(table_info)):
                table_info[i].insert(0, i + 1)
            return table_info
        else:
            QMessageBox.information(self, "温馨提示", "您没有拖入图片!", QMessageBox.Yes)

    def open_img(self):
        filename = QFileDialog.getOpenFileNames(self, '选择图像', os.getcwd(), "Image Files(*.png;*.jpg;*.jpeg;*.bmp;*.webp;*.tif';*.gif);;All Files(*)")
        if filename[0] != []:
            self.read_img(filename[0][0])

    def set_item(self, x, y, item):
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # 第二列自适应列宽
        self.tableWidget.setItem(x, y, item)

    def show_info(self):
        if (table_info := self.get_frequency()) is None:
            self.dropEvent()

        if self.get_radioButtonState() == 1:
            table_info = table_info[:200]

        self.pushButton.setEnabled(False)
        self.tableWidget.setRowCount(len(table_info))
        for x in range(ui.tableWidget.rowCount()):
            for y in range(ui.tableWidget.columnCount()):
                item = QTableWidgetItem(str(table_info[x][y]))
                item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter) # 每列设置水平垂直居中

                if y == 1:
                    im = np.zeros((100, 100, 3))
                    im += table_info[x][y]
                    im = im.astype(np.uint8)
                    im = QtGui.QImage(im.data, im.shape[1], im.shape[0], im.shape[1]*3, QtGui.QImage.Format_RGB888)
                    pix = QtGui.QPixmap(im)
                    item.setIcon(QtGui.QIcon(pix))
                self.set_item(x, y, item)
        self.pushButton.setEnabled(True)
    
    def get_colors(self):
        if (table_info := self.get_frequency()) is not None and (text := self.get_text()) is not None:
            lis = re.findall("\d{1,}", text)
            lis = list(set(lis)) # 去重
            all_i = [int(i) for i in lis]
            try:
                return [table_info[i - 1][1] for i in all_i]
            except IndexError:
                QMessageBox.warning(self, "温馨提示", "颜色序号输入有误, 请检查是否输入了不存的序号!", QMessageBox.Yes)

    def plt_show(self, img, *args):
        plt.xticks([]), plt.yticks([])
        plt.imshow(img)
        plt.show()
        self.pushButton_3.setEnabled(True)

    def show_img(self):
        if (colors := self.get_colors()):
            self.pushButton_3.setEnabled(False)
            self.workThread = WorkThread(colors, self.get_ColorMode(), reverse=self.checkBox.checkState())
            self.workThread.end.connect(self.plt_show)
            self.workThread.start()

    def plt_save(self, new_img: np.ndarray, choice, reverse):
        new_img = Image.fromarray(new_img)
        if choice == 1:
            new_img.save(os.path.join(ui.base_dir, f"RGB_REVERSE_{ui.file_name}")) if reverse else new_img.save(os.path.join(ui.base_dir, f"RGB_{ui.file_name}"))
        elif choice == 2:
            new_img.save(os.path.join(ui.base_dir, f"BLACK_REVERSE_{ui.file_name}")) if reverse else new_img.save(os.path.join(ui.base_dir, f"BLACK_{ui.file_name}"))
        self.pushButton_2.setEnabled(True)

    def save_img(self):
        if (colors := self.get_colors()):
            self.pushButton_2.setEnabled(False)
            self.workThread = WorkThread(colors, self.get_ColorMode(), reverse=self.checkBox.checkState())
            self.workThread.end.connect(self.plt_save)
            self.workThread.start()

    def read_img(self, file_path):
        if os.path.exists(file_path):
            self.img = Image.open(file_path).convert('RGB')
            self.np_img = np.array(self.img, dtype=np.uint8)
            self.label.setPixmap(QtGui.QPixmap(file_path).scaled(self.label.width(), self.label.height()))
        else:
            QMessageBox.critical(self, "温馨提示", "文件不存在!", QMessageBox.Yes)

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
        self.read_img(self.file_path)

class WorkThread(QtCore.QThread):
    end = QtCore.pyqtSignal(np.ndarray, int, bool)

    def __init__(self, colors, choice, reverse) -> None:
        super().__init__()
        self.colors = colors
        self.choice = choice
        self.reverse = reverse

    def get_bool_index(self, img, colors):
        index = None
        for color in colors:
            if index is None:
                index = (img[:, :, 0] == color[0]) & (img[:, :, 1] == color[1]) & (img[:, :, 2] == color[2])
            else:
                index |= (img[:, :, 0] == color[0]) & (img[:, :, 1] == color[1]) & (img[:, :, 2] == color[2])
        return index

    def run(self):
        new_img = ui.np_img.copy()
        index = self.get_bool_index(new_img, self.colors)
        if self.choice == 1:
            if not self.reverse:
                new_img[~index] = (255, 255, 255)
            else:
                new_img[index] = (255, 255, 255)
        elif self.choice == 2:
            if not self.reverse:
                new_img[index] = (0, 0, 0)
                new_img[~index] = (255, 255, 255)
            else:
                new_img[index] = (255, 255, 255)
                new_img[~index] = (0, 0, 0)
        self.end.emit(new_img, self.choice, self.reverse)

if __name__ == "__main__":
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling) # DPI自适应
    app = QApplication(sys.argv)
    ui = Main()
    ui.show()
    sys.exit(app.exec_())