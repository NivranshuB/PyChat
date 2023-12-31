import os
import socket
import sys
import time
import ssl
import select
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QWidget, QLabel, QPushButton, \
    QLineEdit, QTextEdit, QRadioButton, QDialog, QInputDialog, QMessageBox
from PyQt5.QtCore import QCoreApplication, QTimer, QThread, pyqtSignal
from utils import *
import threading

SERVER_HOST = 'localhost'

stop_thread = False

def get_and_send(client):
    while not stop_thread:
        data = sys.stdin.readline().strip()
        if data:
            send(client.sock, data)

class Client(QWidget):

    def __init__(self):
        super().__init__()
        self.pairChatMap = {}
        self.groupChatMap = {}
        self.pairChats = []
        self.groupChats = []
        self.connectedClients = []
        self.menuWindow = MenuWindow()
        self.fullName = ''

        self.context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

        self.pairChatsCounter = 0
        self.groupChatsCounter = 0

        for i in range(10):
            newPairChatWindow = PairChatWindow()
            newPairChatWindow.setClient(self)
            self.pairChats.append(newPairChatWindow)

        for i in range(10):
            newGroupChatWindow = GroupChatWindow()
            newGroupChatWindow.setClient(self)
            self.groupChats.append(newGroupChatWindow)

        self.initUI()

    def initUI(self):

        self.menuWindow.hide()

        inputGrid = QGridLayout()
        inputGrid.addWidget(QLabel('IP Address:'), 0, 0)
        inputGrid.addWidget(QLabel('Port:'), 1, 0)
        inputGrid.addWidget(QLabel('Nick Name:'), 2, 0)

        self.ipaddress = QLineEdit(self)
        self.port = QLineEdit(self)
        self.nickname = QLineEdit(self)

        inputGrid.addWidget(self.ipaddress, 0, 1)
        inputGrid.addWidget(self.port, 1, 1)
        inputGrid.addWidget(self.nickname, 2, 1)

        confirmButton = QPushButton('Connect', self)
        confirmButton.resize(confirmButton.sizeHint())
        confirmButton.clicked.connect(self.connectPressed)

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

    def closeEverything(self):
        for chat in self.pairChats:
            chat.close()

        for chat in self.groupChats:
            chat.close()

        global stop_thread

        stop_thread = True

        self.menuWindow.close()
        self.pauseTimer()
        self.sock.close()
        self.close()
        app.quit()
        os._exit(0)

    def connectPressed(self):
        ipaddress = self.ipaddress.text()
        port = self.port.text()
        nickname = self.nickname.text()

        # Connect to server at port
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock = self.context.wrap_socket(
                self.sock, server_hostname=port)
            self.sock.connect((SERVER_HOST, int(port)))
            self.menuWindow.addSocket(self.sock)
            self.menuWindow.addPairChatMap(self.pairChatMap)
            self.menuWindow.addGroupChatMap(self.groupChatMap)
            self.menuWindow.addClient(self)

            self.connected = True

            # Send my name...
            send(self.sock, 'NAME: ' + nickname)
            data = receive(self.sock)
            self.menuWindow.setName(nickname)

            # Contains client address, set it
            self.fullName = data

            threading.Thread(target=get_and_send, args=(self,)).start()

            self.hide()
            self.menuWindow.show()

            #receive the list of all client names
            data = receive(self.sock)

            #set the client names in the menuWindow

            clientNames = data.split("|")

            for name in clientNames:
                if name != '':
                    self.connectedClients.append(name)
                    self.menuWindow.addMember(name)

            roomdata = receive(self.sock)

            roomNames = roomdata.split("|")

            for name in roomNames:
                if name not in self.groupChatMap and name != '':
                    self.menuWindow.add_new_room(name)

            self.startTimer()


        except socket.error as e:
            print('Failed to connect to server: Invalid Port number or IP address')
            sys.exit(1)

    def receive_data(self):

        try:
            # Wait for input from stdin and socket
            # readable, writeable, exceptional = select.select([0, self.sock], [], [])
            readable, writeable, exceptional = select.select(
                [self.sock], [], [], 0.1)

            for sock in readable:
                # if sock == 0:
                #     data = sys.stdin.readline().strip()
                #     if data:
                #         send(self.sock, data)
                if sock == self.sock:
                    data = receive(self.sock)
                    if not data:
                        self.connected = False
                        break
                    else:
                        splitMessage = data.split(':')
                        if splitMessage[0] == 'Connected':
                            self.menuWindow.addMember(splitMessage[1])
                            self.connectedClients.append(splitMessage[1])
                        elif splitMessage[0] == 'Single':
                            senderName = splitMessage[1]
                            if senderName in self.pairChatMap:
                                pairChat = self.pairChats[self.pairChatMap[senderName]]
                                pairChat.addMessage(splitMessage[2])
                                pairChat.show()
                            else:
                                self.pairChatMap[senderName] = self.getPairChatsCounter()
                                pairChat = self.pairChats[self.getPairChatsCounter()]
                                self.incrementPairChatsCounter()
                                pairChat.setName(senderName)
                                pairChat.addMessage(splitMessage[2])
                                pairChat.show()
                        elif splitMessage[0] == 'Create':
                            newRoomName = splitMessage[1]
                            if newRoomName not in self.groupChatMap:
                                self.menuWindow.add_new_room(newRoomName)

                        elif splitMessage[0] == 'Join':
                            groupName = splitMessage[2]
                            newMemberName = splitMessage[1]
                            groupChat = self.groupChats[self.groupChatMap[groupName]]
                            groupChat.addMember(newMemberName)

                        elif splitMessage[0] == 'Group':
                            senderName = splitMessage[2]
                            groupName = splitMessage[1]
                            groupChat = self.groupChats[self.groupChatMap[groupName]]
                            groupChat.addMessage(senderName.split("@")[0] + ": " + splitMessage[3])

                        elif splitMessage[0] == 'Invite':
                            self.menuWindow.inviteConfirmBox(data)

                        sys.stdout.flush()

        except KeyboardInterrupt:
            print(" Client interrupted. " "")
            stop_thread = True
            self.cleanup()


    def sendMessage(self, text):
        message = 'Single:' + text
        send(self.sock, message)

    def sendNewRoomMessage(self, text):
        message = 'Create:' + text
        send(self.sock, message)

    def sendJoinMessage(self, text):
        message = 'Join:' + text
        send(self.sock, message)

    def sendGroupMessage(self, text):
        splitMessage = text.split(':')
        message = 'Group:' + splitMessage[0] + ":" + self.nickname.text() + ":" + splitMessage[1]
        send(self.sock, message)

    def sendInviteMessage(self, text):
        message = 'Invite:' + text
        send(self.sock, message)

    def cleanup(self):
        """Close the connection and wait for the thread to terminate."""
        self.sock.close()

    def startTimer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(ex.receive_data)
        self.timer.start(1000)

    def pauseTimer(self):
        self.timer.stop()

    def getPairChatsCounter(self):
        return self.pairChatsCounter

    def getGroupChatsCounter(self):
        return self.groupChatsCounter

    def incrementPairChatsCounter(self):
        self.pairChatsCounter += 1

    def incrementGroupChatsCounter(self):
        self.groupChatsCounter += 1

    def getNonConnectedClients(self, groupMembers):
        unconnectedGroupMembers = []
        for member in self.connectedClients:
            if member not in groupMembers:
                unconnectedGroupMembers.append(member)

        return unconnectedGroupMembers


class MenuWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    def __init__(self):
        super().__init__()

        clientDetails = QHBoxLayout()

        #Show the name of all available clients
        self.clientList = QVBoxLayout()
        self.clientList.addWidget(QLabel('Connected Clients: '))

        #Area to select client for 1:1 chat
        self.singleClientChat = QVBoxLayout()
        self.clientSelected = QLabel('None')
        self.singleClientChat.addWidget(self.clientSelected)
        self.singleChatButton = QPushButton('1:1 Chat')
        self.singleChatButton.clicked.connect(self.newPairChatPressed)
        self.singleClientChat.addWidget(self.singleChatButton)

        clientDetails.addLayout(self.clientList)
        clientDetails.addLayout(self.singleClientChat)

        roomTitle = QHBoxLayout()
        roomTitle.addWidget(QLabel('Chat rooms (Group chat)'))

        groupRoomArea = QWidget()
        self.roomList = QVBoxLayout()
        groupRoomArea.setLayout(self.roomList)
        groupRoomArea.setMinimumWidth(200)

        roomDetails = QHBoxLayout()
        roomDetails.addWidget(groupRoomArea)

        roomButtons = QVBoxLayout()
        self.groupSelected = QLabel('None')
        roomButtons.addWidget(self.groupSelected)
        createButton = QPushButton('Create')
        createButton.clicked.connect(self.create_button_pressed)
        roomButtons.addWidget(createButton)
        joinButton = QPushButton('Join')
        joinButton.clicked.connect(self.join_button_pressed)
        roomButtons.addWidget(joinButton)

        roomDetails.addLayout(roomButtons)

        menu = QVBoxLayout()
        menu.addLayout(clientDetails)
        menu.addLayout(roomTitle)
        menu.addLayout(roomDetails)

        self.setLayout(menu)

        self.setWindowTitle('Chat Menu')

        self.resize(500, 400)
        self.show()

    def create_button_pressed(self):
        parent_window = self #probably..., depends on your code
        default_value = "Chatroom-" + str(self.client.getGroupChatsCounter())
        title = "New room"
        message = "Select the name of new Chat room"
        room_name, ok = QInputDialog.getText(parent_window, title, message, QLineEdit.Normal, default_value)
        if room_name != "":
            self.create_new_room(room_name)

    def create_new_room(self, text):
        newRoomName = text
        newGroupChatButton = QRadioButton(newRoomName, self)
        newGroupChatButton.clicked.connect(lambda: self.newGroupSelected(newRoomName, newGroupChatButton.isChecked()))
        self.roomList.addWidget(newGroupChatButton)

        self.groupChatMap[newRoomName] = self.client.getGroupChatsCounter()
        groupChat = self.client.groupChats[self.client.getGroupChatsCounter()]
        groupChat.setName(newRoomName)
        self.client.incrementGroupChatsCounter()
        self.client.sendNewRoomMessage(newRoomName)

    def join_button_pressed(self):
        groupChatSelected = self.groupSelected.text()
        if groupChatSelected in self.client.groupChatMap:
            groupChat = self.client.groupChats[self.groupChatMap[groupChatSelected]]
            groupChat.addMember(self.client.fullName)
            groupChat.show()
            self.client.sendJoinMessage(groupChatSelected + ':' + self.name)

    def add_new_room(self, text):
        newRoomName = text
        newGroupChatButton = QRadioButton(newRoomName, self)
        newGroupChatButton.clicked.connect(lambda: self.newGroupSelected(newRoomName, newGroupChatButton.isChecked()))
        self.roomList.addWidget(newGroupChatButton)

        self.groupChatMap[newRoomName] = self.client.getGroupChatsCounter()
        groupChat = self.client.groupChats[self.client.getGroupChatsCounter()]
        groupChat.setName(newRoomName)
        #pairChat.show()
        self.client.incrementGroupChatsCounter()

    def newGroupSelected(self, text, checkStatus):
        if checkStatus:
            self.groupSelected.setText(text)
        else:
            self.groupSelected.setText('None')

    def addSocket(self, socket):
        self.sock = socket

    def addPairChatMap(self, pairMap):
        self.pairChatMap = pairMap

    def addGroupChatMap(self, groupMap):
        self.groupChatMap = groupMap

    def addClient(self, client):
        self.client = client


    def addMember(self, text):
        newClientChatButton = QRadioButton(text, self)
        newClientChatButton.clicked.connect(lambda: self.newClientSelected(text, newClientChatButton.isChecked()))
        self.clientList.addWidget(newClientChatButton)

    def newClientSelected(self, text, checkStatus):
        if checkStatus:
            self.clientSelected.setText(text)
        else:
            self.clientSelected.setText('None')

    def newPairChatPressed(self):
        pairChatClient = self.clientSelected.text()

        if pairChatClient in self.pairChatMap:
            pairChat = self.client.pairChats[self.pairChatMap[pairChatClient]]
            pairChat.show()
        elif pairChatClient != 'None':
            self.pairChatMap[pairChatClient] = self.client.getPairChatsCounter()
            pairChat = self.client.pairChats[self.client.getPairChatsCounter()]
            pairChat.setName(pairChatClient)
            pairChat.show()
            self.client.incrementPairChatsCounter()

    def setName(self, text):
        self.name = text
        self.setWindowTitle(text)

    def inviteConfirmBox(self, text):
        splitMessage = text.split(':')
        reply = QMessageBox.question(self, 'Invite to ' + splitMessage[1], splitMessage[2] + ' sent you an invite to '
                    'join group, do you accept?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            groupChatSelected = splitMessage[1]

            if groupChatSelected in self.client.groupChatMap:
                groupChat = self.client.groupChats[self.groupChatMap[groupChatSelected]]
                groupChat.addMember(self.client.fullName)
                groupChat.show()
                self.client.sendJoinMessage(groupChatSelected + ':' + self.name)

    def closeEvent(self, event):
        self.client.closeEverything()

class PairChatWindow(QDialog):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        chatTitle = QHBoxLayout()
        self.titleLabel = QLabel('Chat with ...')
        chatTitle.addWidget(self.titleLabel)

        self.chatBox = QTextEdit('')
        self.chatBox.setReadOnly(True)

        messageArea = QHBoxLayout()
        self.textMessage = QLineEdit()
        messageArea.addWidget(self.textMessage)
        sendButton = QPushButton('Send')
        sendButton.clicked.connect(self.sendButtonPressed)
        messageArea.addWidget(sendButton)

        overallVbox = QVBoxLayout()
        overallVbox.addLayout(chatTitle)
        overallVbox.addWidget(self.chatBox)
        overallVbox.addLayout(messageArea)

        self.setLayout(overallVbox)
        self.setWindowTitle('1:1 Chat')
        self.resize(500, 400)
        #self.show()

    def setName(self, text):
        self.name = text
        self.setWindowTitle('[' + self.client.nickname.text() + '] ' + '1:1 chat')
        self.titleLabel.setText('Chat with ' + text)

    def addMessage(self, text):
        senderName = self.name.split('@')
        self.chatBox.append(senderName[0] + ': ' + text)

    def sendButtonPressed(self):
        messageSent = self.textMessage.text()
        self.textMessage.setText('')
        self.chatBox.append(self.client.nickname.text() + ': ' + messageSent)
        self.client.sendMessage(self.name + ':' + messageSent)

    def setClient(self, client):
        self.client = client

class GroupChatWindow(QDialog):

    def __init__(self):
        super().__init__()
        self.initUI()
        self.memberList = []

    def initUI(self):

        headers = QHBoxLayout()
        self.roomtitle = QLabel('Room 1 by ...')
        headers.addWidget(self.roomtitle)
        headers.addWidget(QLabel('Members'))

        content = QHBoxLayout()
        messageBox = QVBoxLayout()
        self.messageArea = QTextEdit('')
        self.messageArea.setReadOnly(True)
        self.messageArea.setMaximumWidth(200)
        messageBox.addWidget(self.messageArea)

        messageSend = QHBoxLayout()
        self.messageInput = QLineEdit()
        messageSend.addWidget(self.messageInput)
        sendButton = QPushButton('Send')
        sendButton.clicked.connect(self.sendButtonPressed)
        messageSend.addWidget(sendButton)

        messageBox.addLayout(messageSend)

        content.addLayout(messageBox)
        self.members = QVBoxLayout()
        content.addLayout(self.members)

        footers = QHBoxLayout()

        inviteButton = QPushButton('Invite')
        inviteButton.clicked.connect(self.invite_button_pressed)
        footers.addWidget(inviteButton)

        overallVbox = QVBoxLayout()
        overallVbox.addLayout(headers)
        overallVbox.addLayout(content)
        overallVbox.addLayout(footers)

        self.setLayout(overallVbox)
        self.setWindowTitle('Group Chat')
        self.resize(500, 400)

    def setName(self, text):
        self.name = text
        self.roomtitle.setText(text)
        self.setWindowTitle('[' + self.client.nickname.text() + '] ' + text + " (Group Chat)")

    def setClient(self, client):
        self.client = client

    def addMember(self, text):
        notMemberYet = True
        for member in self.memberList:
            if member == text:
                notMemberYet = False

        if notMemberYet:
            newMemberLabel = text
            self.members.addWidget(QLabel(newMemberLabel))
            self.memberList.append(newMemberLabel)


    def sendButtonPressed(self):
        messageSent = self.messageInput.text()
        self.messageInput.setText('')
        self.messageArea.append(self.client.nickname.text() + ': ' + messageSent)
        self.client.sendGroupMessage(self.name + ':' + messageSent)

    def invite_button_pressed(self):
        items = self.client.getNonConnectedClients(self.memberList)
        item, ok = QInputDialog.getItem(self, "Select member to invite: ",
                                        "Unconnected members", items, 0, False)
        self.client.sendInviteMessage(self.name + ':' + self.client.fullName + ':' + item)

    def addMessage(self, text):
        self.messageArea.append(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Client()
    sys.exit(app.exec_())
