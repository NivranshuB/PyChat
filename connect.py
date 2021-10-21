import socket
import sys
import time
import ssl
import select
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

    def connectPressed(self):
        ipaddress = self.ipaddress.text()
        port = self.port.text()
        nickname = self.nickname.text()

        print('IP address is: ' + ipaddress)
        print('Port is: ' + port)
        print('Client name is: ' + nickname)

        # Connect to server at port
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock = self.context.wrap_socket(
                self.sock, server_hostname=port)
            self.sock.connect((SERVER_HOST, int(port)))
            print(f'Now connected to chat server@ port {port}')
            self.menuWindow.addSocket(self.sock)
            self.menuWindow.addPairChatMap(self.pairChatMap)
            self.menuWindow.addGroupChatMap(self.groupChatMap)
            self.menuWindow.addClient(self)

            self.connected = True

            # Send my name...
            send(self.sock, 'NAME: ' + nickname)
            data = receive(self.sock)
            self.menuWindow.setName(nickname)

            print('Data recieved ' + data)

            # Contains client address, set it
            self.fullName = data

            threading.Thread(target=get_and_send, args=(self,)).start()

            self.hide()
            self.menuWindow.show()

            #receive the list of all client names
            data = receive(self.sock)

            #set the client names in the menuWindow
            print('Clients connected are: ' + data)

            clientNames = data.split("|")

            print('Number of clients are ' + str(len(clientNames)))

            for name in clientNames:
                if name != '':
                    print('Client name: ' + name)
                    self.connectedClients.append(name)
                    self.menuWindow.addMember(name)

            self.startTimer()


        except socket.error as e:
            print(f'Failed to connect to chat server @ port {self.port}')
            sys.exit(1)

    def receive_data(self):
        #print('Another 1sec bites the dust')

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
                        print('Client shutting down.')
                        self.connected = False
                        break
                    else:
                        splitMessage = data.split(':')
                        if splitMessage[0] == 'Connected':
                            self.menuWindow.addMember(splitMessage[1])
                            self.connectedClients.append(splitMessage[1])
                            print('Adding new member ' + splitMessage[1])
                        elif splitMessage[0] == 'Single':
                            senderName = splitMessage[1]
                            if senderName in self.pairChatMap:
                                print('Opening previous chat with ' + senderName)
                                pairChat = self.pairChats[self.pairChatMap[senderName]]
                                pairChat.addMessage(splitMessage[2])
                                pairChat.show()
                            else:
                                print('Creating new chat between us ' + self.nickname.text() + " and " + senderName)
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


                        sys.stdout.write('Data received was: ' + data + '\n')
                        sys.stdout.flush()

        except KeyboardInterrupt:
            print(" Client interrupted. " "")
            stop_thread = True
            self.cleanup()


    def sendMessage(self, text):
        message = 'Single:' + text
        print('Sending the following message to server: ' + message)
        send(self.sock, message)

    def sendNewRoomMessage(self, text):
        message = 'Create:' + text
        print('Sending the following message to server: ' + message)
        send(self.sock, message)

    def sendJoinMessage(self, text):
        message = 'Join:' + text
        print('Sending the following message to server: ' + message)
        send(self.sock, message)

    def sendGroupMessage(self, text):
        splitMessage = text.split(':')
        message = 'Group:' + splitMessage[0] + ":" + self.nickname.text() + ":" + splitMessage[1]
        print('Sending the following message to server: ' + message)
        send(self.sock, message)

    def sendInviteMessage(self, text):
        message = 'Invite:' + text
        print('Sending the following message to server: ' + message)
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
            print('Checking status of member ' + member)
            if member not in groupMembers:
                print('Member ' + member + ' is not in group')
                unconnectedGroupMembers.append(member)

        return unconnectedGroupMembers


class MenuWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    def __init__(self):
        super().__init__()
        print('Another window created')

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

        closeOption = QHBoxLayout()
        closeButton = QPushButton('Close')
        closeButton.clicked.connect(QCoreApplication.instance().quit)
        closeOption.addWidget(closeButton)

        menu = QVBoxLayout()
        menu.addLayout(clientDetails)
        menu.addLayout(roomTitle)
        menu.addLayout(roomDetails)
        menu.addLayout(closeOption)

        self.setLayout(menu)

        self.setWindowTitle('Chat Menu')

        self.resize(500, 400)
        self.show()

        print('Menu gets shown')

    def create_button_pressed(self):
        parent_window = self #probably..., depends on your code
        default_value = "Chatroom-" + str(self.client.getGroupChatsCounter())
        title = "New room"
        message = "Select the name of new Chat room"
        room_name, ok = QInputDialog.getText(parent_window, title, message, QLineEdit.Normal, default_value)
        print('New room name is ' + room_name)
        self.create_new_room(room_name)

    def create_new_room(self, text):
        newRoomName = text
        newGroupChatButton = QRadioButton(newRoomName, self)
        newGroupChatButton.clicked.connect(lambda: self.newGroupSelected(newRoomName, newGroupChatButton.isChecked()))
        self.roomList.addWidget(newGroupChatButton)

        print('Creating a new chat room window...')
        self.groupChatMap[newRoomName] = self.client.getGroupChatsCounter()
        groupChat = self.client.groupChats[self.client.getGroupChatsCounter()]
        groupChat.setName(newRoomName)
        self.client.incrementGroupChatsCounter()
        self.client.sendNewRoomMessage(newRoomName)

    def join_button_pressed(self):
        print('join button pressed')
        groupChatSelected = self.groupSelected.text()
        print('The group selected is: ' + groupChatSelected)
        if groupChatSelected in self.client.groupChatMap:
            print('The group selected is: ' + groupChatSelected)
            print('Opening group chat window...')
            groupChat = self.client.groupChats[self.groupChatMap[groupChatSelected]]
            groupChat.addMember(self.client.fullName)
            groupChat.show()
            self.client.sendJoinMessage(groupChatSelected + ':' + self.name)

    def add_new_room(self, text):
        newRoomName = text
        newGroupChatButton = QRadioButton(newRoomName, self)
        newGroupChatButton.clicked.connect(lambda: self.newGroupSelected(newRoomName, newGroupChatButton.isChecked()))
        self.roomList.addWidget(newGroupChatButton)

        print('Creating a new chat room window...')
        self.groupChatMap[newRoomName] = self.client.getGroupChatsCounter()
        groupChat = self.client.groupChats[self.client.getGroupChatsCounter()]
        groupChat.setName(newRoomName)
        #pairChat.show()
        self.client.incrementGroupChatsCounter()

    def newGroupSelected(self, text, checkStatus):
        if checkStatus:
            print('New group selected: ' + text)
            self.groupSelected.setText(text)
        else:
            print('Group deselected')
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
            print('Invite accepted')
            groupChatSelected = splitMessage[1]

            print('The group selected is: ' + groupChatSelected)
            if groupChatSelected in self.client.groupChatMap:
                print('The group selected is: ' + groupChatSelected)
                print('Opening group chat window...')
                groupChat = self.client.groupChats[self.groupChatMap[groupChatSelected]]
                groupChat.addMember(self.client.fullName)
                groupChat.show()
                self.client.sendJoinMessage(groupChatSelected + ':' + self.name)


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

        closeButton = QPushButton('Close')
        closeButton.clicked.connect(QCoreApplication.instance().quit)

        overallVbox = QVBoxLayout()
        overallVbox.addLayout(chatTitle)
        overallVbox.addWidget(self.chatBox)
        overallVbox.addLayout(messageArea)
        overallVbox.addWidget(closeButton)

        self.setLayout(overallVbox)
        self.setWindowTitle('1:1 Chat')
        self.resize(500, 400)
        #self.show()

    def setName(self, text):
        self.name = text
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
        headers.addWidget(QLabel('Room 1 by ...'))
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

        closeButton = QPushButton('Close')
        closeButton.clicked.connect(QCoreApplication.instance().quit)

        footers.addWidget(closeButton)
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
        self.setWindowTitle(text + " (Group Chat)")

    def setClient(self, client):
        self.client = client

    def addMember(self, text):
        notMemberYet = True
        for member in self.memberList:
            if member == text:
                notMemberYet = False

        if notMemberYet:
            print('Adding new member ' + text + ' to the group chat room ' + self.name)
            newMemberLabel = text
            self.members.addWidget(QLabel(newMemberLabel))
            self.memberList.append(newMemberLabel)


    def sendButtonPressed(self):
        print('Send button pressed')
        messageSent = self.messageInput.text()
        self.messageInput.setText('')
        self.messageArea.append(self.client.nickname.text() + ': ' + messageSent)
        self.client.sendGroupMessage(self.name + ':' + messageSent)

    def invite_button_pressed(self):
        print('Invite button pressed!')
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
