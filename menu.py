import sys
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QWidget, QLabel, QPushButton, QLineEdit, QTextEdit
from PyQt5.QtCore import QCoreApplication

class MyApp(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        clientTitle = QHBoxLayout()
        clientTitle.addWidget(QLabel('Connected Clients'))

        clientDetails = QHBoxLayout()
        clientDetails.addWidget(QTextEdit())
        clientDetails.addWidget(QPushButton('1:1 Chat'))

        roomTitle = QHBoxLayout()
        roomTitle.addWidget(QLabel('Chat rooms (Group chat)'))

        roomDetails = QHBoxLayout()
        roomDetails.addWidget(QTextEdit())

        roomButtons = QVBoxLayout()
        roomButtons.addWidget(QPushButton('Create'))
        roomButtons.addWidget(QPushButton('Join'))

        roomDetails.addLayout(roomButtons)

        closeOption = QHBoxLayout()
        closeButton = QPushButton('Close')
        closeButton.clicked.connect(QCoreApplication.instance().quit)
        closeOption.addWidget(closeButton)

        overallVbox = QVBoxLayout()
        overallVbox.addLayout(clientTitle)
        overallVbox.addLayout(clientDetails)
        overallVbox.addLayout(roomTitle)
        overallVbox.addLayout(roomDetails)
        overallVbox.addLayout(closeOption)


        self.setLayout(overallVbox)
        self.setWindowTitle('Chat Menu')
        self.resize(500, 400)
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())