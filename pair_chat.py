import sys
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QWidget, QLabel, QPushButton, QLineEdit, QTextEdit
from PyQt5.QtCore import QCoreApplication

class MyApp(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        chatTitle = QHBoxLayout()
        chatTitle.addWidget(QLabel('Chat with ...'))

        chatBox = QTextEdit('Hi mate!')

        messageArea = QHBoxLayout()
        messageArea.addWidget(QLineEdit())
        messageArea.addWidget(QPushButton('Send'))

        closeButton = QPushButton('Close')
        closeButton.clicked.connect(QCoreApplication.instance().quit)

        overallVbox = QVBoxLayout()
        overallVbox.addLayout(chatTitle)
        overallVbox.addWidget(chatBox)
        overallVbox.addLayout(messageArea)
        overallVbox.addWidget(closeButton)

        self.setLayout(overallVbox)
        self.setWindowTitle('1:1 Chat')
        self.resize(500, 400)
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())