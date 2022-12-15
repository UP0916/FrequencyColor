import sys
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QImage, QPixmap
import numpy as np

if __name__ == '__main__':
    app = QApplication(sys.argv)
    h, w = 300, 600
    im = np.random.randint(0, 255, [h, w, 3], np.uint8)
    a = QLabel()
    a.resize(w, h)
    # 注意下面QtGui.QImage的第四个参数，意思为图像每行有多少个字节，不设定时，图像有时会歪，所以一定要设定
    im = QImage(im.data, im.shape[1], im.shape[0], im.shape[1]*3, QImage.Format_RGB888)
    pix = QPixmap(im).scaled(a.width(), a.height())
    a.setPixmap(pix)
    a.show()
    exit(app.exec_())
