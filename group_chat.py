import sys
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QWidget, QLabel, QPushButton, QLineEdit, QTextEdit
from PyQt5.QtCore import QCoreApplication

class MyApp(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        headers = QHBoxLayout()
        headers.addWidget(QLabel('Room 1 by ...'))
        headers.addWidget(QLabel('Members'))

        content = QHBoxLayout()
        messageBox = QVBoxLayout()
        messageBox.addWidget(QTextEdit('Group messages go here...'))

        messageSend = QHBoxLayout()
        messageSend.addWidget(QLineEdit())
        messageSend.addWidget(QPushButton('Send'))

        messageBox.addLayout(messageSend)

        content.addLayout(messageBox)
        content.addWidget(QTextEdit())

        footers = QHBoxLayout()

        closeButton = QPushButton('Close')
        closeButton.clicked.connect(QCoreApplication.instance().quit)

        footers.addWidget(closeButton)
        footers.addWidget(QPushButton('Inviter'))

        overallVbox = QVBoxLayout()
        overallVbox.addLayout(headers)
        overallVbox.addLayout(content)
        overallVbox.addLayout(footers)

        self.setLayout(overallVbox)
        self.setWindowTitle('1:1 Chat')
        self.resize(500, 400)
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())