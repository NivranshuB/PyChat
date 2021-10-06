import sys
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QWidget, QLabel, QPushButton, QLineEdit, QTextEdit
from PyQt5.QtCore import QCoreApplication

class MyApp(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        inputGrid = QGridLayout()

        inputGrid.addWidget(QLabel('IP Address:'), 0, 0)
        inputGrid.addWidget(QLabel('Port:'), 1, 0)
        inputGrid.addWidget(QLabel('Nick Name:'), 2, 0)

        inputGrid.addWidget(QLineEdit(), 0, 1)
        inputGrid.addWidget(QLineEdit(), 1, 1)
        inputGrid.addWidget(QLineEdit(), 2, 1)

        confirmButton = QPushButton('Connect', self)
        confirmButton.resize(confirmButton.sizeHint())   

        cancelButton = QPushButton('Cancel', self)
        cancelButton.resize(cancelButton.sizeHint())
        cancelButton.clicked.connect(QCoreApplication.instance().quit)

        hbox = QHBoxLayout()
        hbox.addStretch(6)
        hbox.addWidget(confirmButton)
        hbox.addWidget(cancelButton)

        vbox = QVBoxLayout()
        vbox.addStretch(10)
        vbox.addLayout(hbox)
        
        overallVbox = QVBoxLayout()
        overallVbox.addStretch(1)
        overallVbox.addLayout(inputGrid)
        overallVbox.addStretch(6)
        overallVbox.addLayout(vbox)

        self.setLayout(overallVbox)
        self.setWindowTitle('Connect to Server')
        self.resize(500, 400)
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())