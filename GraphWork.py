from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMainWindow
from PyQt5.QtGui import QBitmap, QIcon, QImage, QIntValidator, QPainter, QPen, QBrush, QPixmap, QRegion
from PyQt5 import QtGui, QtWidgets, QtCore
import sys
import numpy as np
from numpy.core.numeric import cross
from GraphCut import *


Sigma = 30
Lambda = 2

def setSigma(value):
    global Sigma
    Sigma = value

def setLambda(value):
    global Lambda
    Lambda = value


class Canvas(QtWidgets.QLabel):

    def __init__(self):
        super().__init__()
        self.imageName = './images-320/grave-gr-320.jpg'
        self.imageSegmentaion = './image-segments-320/grave-320.jpg'
        self.sourceImage = QPixmap(self.imageName)
        pixmap = QPixmap(self.imageName)
        self.last_x, self.last_y = None, None
        self.pen_color = QtGui.QColor('#f45b7a')

        self.height = self.size().height()
        self.width = self.size().width()
        self.setPixmap(pixmap)
        
        img = self.sourceImage.toImage()
        s = img.bits().asstring(img.size().width() * img.size().height() * 4)
        self.image = np.frombuffer(s, dtype=np.uint8).reshape((img.size().height(), img.size().width(), 4)) 
    def set_pen_color(self, c):
        self.pen_color = QtGui.QColor(c)

    def mouseMoveEvent(self, e):
        if self.last_x is None: # First event.
            self.last_x = e.x()
            self.last_y = e.y()
            return # Ignore the first time.

        painter = QtGui.QPainter(self.pixmap())
        rect = self.contentsRect()
        pmRect = self.pixmap().rect()
        if rect != pmRect:
            # the pixmap rect is different from that available to the label
            align = self.alignment()
            if align & QtCore.Qt.AlignHCenter:
                # horizontally align the rectangle
                pmRect.moveLeft(int((rect.width() - pmRect.width()) / 2))
            elif align & QtCore.Qt.AlignRight:
                # align to bottom
                pmRect.moveRight(rect.right())
            if align & QtCore.Qt.AlignVCenter:
                # vertically align the rectangle
                pmRect.moveTop(int((rect.height() - pmRect.height()) / 2))
            elif align &  QtCore.Qt.AlignBottom:
                # align right
                pmRect.moveBottom(rect.bottom())
        p = painter.pen()
        p.setWidth(4)
        p.setColor(self.pen_color)
        painter.setPen(p)
        painter.translate(-pmRect.topLeft())
        painter.drawLine(self.last_x, self.last_y, e.x(), e.y())
        painter.end()
        self.update()
        self.last_x = e.x()
        self.last_y = e.y()

    def mouseReleaseEvent(self, e):
        self.last_x = None
        self.last_y = None

COLORS = ['#35E3E3','#F45B7A']
COLOR_NAMES = ['background', 'foreground']
class QPaletteButton(QtWidgets.QPushButton):

    def __init__(self, color, name):
        super().__init__(name)
        self.setFixedSize(QtCore.QSize(100,48))
        self.color = color
        self.setStyleSheet("background-color: %s;" % color)

class Input(QtWidgets.QLineEdit):

    def __init__(self):
        super().__init__()
        self.setValidator(QIntValidator())
        self.setMaxLength(3)
        self.setFixedSize(QtCore.QSize(100, 24))

class StartButton(QtWidgets.QPushButton):

    def __init__(self):
        super().__init__('start')
        self.setFixedSize(QtCore.QSize(100,48))
        self.color = '#ccc'
        self.setStyleSheet("background-color: %s;" % self.color)
    
class GraphGUI(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.width = 800
        self.height = 600
        self.initUI()

    
    def initUI(self):
        self.setFixedSize(self.width, self.height)
        self.move(300, 300)
        self.setWindowTitle('Graph cut')
        self.canvas = Canvas()
        self.w = QtWidgets.QWidget()
        self.l = QtWidgets.QHBoxLayout()
        self.w.setLayout(self.l)
        self.l.addWidget(self.canvas)

        controls = QtWidgets.QVBoxLayout()
        controls.addSpacing(50)
        self.add_palette_buttons(controls)
        controls.addSpacing(25)
      
        inputLambda = Input()    
        inputLambda.setText(str(Lambda))
        inputSigma = Input()
        inputSigma.setText(str(Sigma))
        controls.addWidget(QLabel('Lambda: '))
        controls.addWidget(inputLambda)
        controls.addSpacing(10)
        controls.addWidget(QLabel('Sigma: '))
        controls.addWidget(inputSigma)
        inputLambda.textChanged.connect(setLambda)
        inputSigma.textChanged.connect(setSigma)
        controls.addSpacing(50)

        startButton = StartButton()
        controls.addWidget(startButton)
        startButton.clicked.connect(self.start)

        controls.addStretch()
        self.l.addLayout(controls)

        self.setCentralWidget(self.w)
        self.show()
    
    def getObjAndBack(self):
        img = self.canvas.pixmap().toImage()
        s = img.bits().asstring(img.size().width() * img.size().height() * 4)
        paintedImage = np.frombuffer(s, dtype=np.uint8).reshape((img.size().height(), img.size().width(), 4)) 
        background = []
        foreground = []
        for i in range(paintedImage.shape[0]):
            for j in range(paintedImage.shape[1]):
                if(paintedImage[i][j][2]==53 and paintedImage[i][j][1]==227 and paintedImage[i][j][0]==227):
                    background.append(i * img.size().width() + j)
                if(paintedImage[i][j][2]==244 and paintedImage[i][j][1]==91 and paintedImage[i][j][0]==122):
                    foreground.append(i * img.size().width() + j)
        return background, foreground


    def start(self):
        print(Lambda, Sigma)
        print("Start calculate image segmentation-------------------->")
        background, foreground = self.getObjAndBack()
        print('Count of pixels: ', len(background) + len(foreground))
        pixelsImage = self.canvas.image
        greyImage = np.array(pixelsImage)
        for i, row in enumerate(pixelsImage):
            for j, pixel in enumerate(row):
                greyImage[i][j] = rgba2gray(pixel)
        createGraph(greyImage, background, foreground, int(Lambda), int(Sigma))

        qimage = QImage(greyImage, greyImage.shape[1], greyImage.shape[0],                                                                                                                                                 
                    QImage.Format_RGB32)   
        maskImageLabel = QLabel()
        maskImageLabel.setPixmap(QPixmap.fromImage(qimage))
        maskImageLabel.setParent(self.canvas)
        maskImageLabel.move(self.canvas.sourceImage.width(), int((self.height - self.canvas.sourceImage.height()) / 2) - 10)
        maskImageLabel.show()
        qimage.save('my.png')
        print("Segmentation succesfully-------------------->")

        templateImage = QImage(self.canvas.imageSegmentaion)
        s = templateImage.bits().asstring(templateImage.size().width() * templateImage.size().height() * 4)
        templateArray = np.frombuffer(s, dtype=np.uint8).reshape((templateImage.size().height(), templateImage.size().width(), 4)) 
        metrika = self.correctPixelRatio(templateArray, greyImage)
        print("Correct pixels ratio: ", metrika[0] / (metrika[0] + metrika[1]))
        jaccard = self.jaccard(templateArray, greyImage)
        print("Jaccard ratio: ", jaccard[0] / jaccard[1])
    def add_palette_buttons(self, layout):
        for i in range(len(COLORS)):
            b = QPaletteButton(COLORS[i], COLOR_NAMES[i])
            b.pressed.connect(lambda c=COLORS[i]: self.canvas.set_pen_color(c))
            layout.addWidget(b)

    def correctPixelRatio(self, templateImage, calcImage):
        correctPixels = 0
        incorrectPixels = 0
        for i, row in enumerate(templateImage):
            for j, pixel in enumerate(row):
                if templateImage[i][j][0] == calcImage[i][j][0]:
                    correctPixels += 1
                else:
                    incorrectPixels += 1
        return correctPixels, incorrectPixels

    def jaccard(self, templateImage, calcImage):
        association = 0 #Объединение
        crossing = 0 #Пересечение
        for i, row in enumerate(templateImage):
            for j, pixel in enumerate(row):
                if templateImage[i][j][0] == 255 and calcImage[i][j][0] == 255:
                    crossing += 1
                if templateImage[i][j][0] == 255 or calcImage[i][j][0] == 255:
                    association += 1
        return crossing, association

    
def startApp():
    app = QApplication(sys.argv)
    ui = GraphGUI()
    return {'app': app, 'ui': ui}
def closeApp(app):
    sys.exit(app.exec_())

def rgba2gray(rgba):
    grey = np.dot(rgba[...,:3], [0.2989, 0.5870, 0.1140])
    return np.array([grey, grey, grey, rgba[3]])

if __name__ == '__main__':
    app = startApp()
    closeApp(app['app'])


