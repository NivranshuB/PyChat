import os

import select
import socket
import sys
import signal
import argparse
import ssl

from utils import *

SERVER_HOST = 'localhost'


class ChatServer(object):
    """ An example chat server using select """

    def __init__(self, port, backlog=5):
        self.clients = 0
        self.clientmap = {}
        self.outputs = []  # list output sockets
        self.rooms = []

        self.context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        self.context.load_cert_chain(certfile="cert.pem", keyfile="cert.pem")
        self.context.load_verify_locations('cert.pem')
        self.context.set_ciphers('AES128-SHA')

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((SERVER_HOST, port))
        self.server.listen(backlog)
        self.server = self.context.wrap_socket(self.server, server_side=True)

        # Catch keyboard interrupts
        signal.signal(signal.SIGINT, self.sighandler)

        print(f'Server listening to port: {port} ...')

    def sighandler(self, signum, frame):
        """ Clean up client outputs"""
        print('Shutting down server...')

        # Close existing client sockets
        for output in self.outputs:
            output.close()

        self.server.close()
        self.server.shutdown(socket.SHUT_RDWR);
        os._exit(0)

    def get_client_name(self, client):
        """ Return the name of the client """
        info = self.clientmap[client]
        host, name = info[0][0], info[1]
        return '@'.join((name, host))

    def run(self):
        # inputs = [self.server, sys.stdin]
        inputs = [self.server]
        self.outputs = []
        running = True
        while running:
            try:
                readable, writeable, exceptional = select.select(
                    inputs, self.outputs, [])
            except select.error as e:
                break

            for sock in readable:
                sys.stdout.flush()
                if sock == self.server:
                    # handle the server socket
                    client, address = self.server.accept()
                    print(
                        f'Chat server: got connection {client.fileno()} from {address}')
                    # Read the login name
                    cname = receive(client).split('NAME: ')[1]

                    # Compute client name and send back
                    self.clients += 1
                    inputs.append(client)

                    self.clientmap[client] = (address, cname)

                    #Send their full name to client
                    send(client, self.get_client_name(client))

                    # Send joining information to other clients
                    msg = f'Connected:{self.get_client_name(client)}'

                    for output in self.outputs:
                        send(output, msg)

                    # Send as new client's message...
                    msg = ''

                    for output in self.outputs:
                        msg += f'{self.get_client_name(output)}|'

                    self.outputs.append(client)

                    # Send all the client names to that particular client
                    #send(client, f'\nServer> Sending a list of clients to [{self.get_client_name(client)}]')
                    send(client, msg)

                    roomMessage = ''

                    for room in self.rooms:
                        roomMessage += f'{room}|'

                    send(client, roomMessage)

                else:
                    # handle all other sockets
                    try:
                        data = receive(sock)
                        if data:
                            dataSplit = data.split(':')

                            if dataSplit[0] == 'Single':
                                for output in self.outputs:
                                    if self.get_client_name(output) == dataSplit[1]:
                                        senderName = self.get_client_name(sock)
                                        send(output, 'Single:' + senderName + ":" + dataSplit[2])

                            elif dataSplit[0] == 'Create':
                                self.rooms.append(dataSplit[1])

                                for output in self.outputs:
                                    send(output, data)

                            elif dataSplit[0] == 'Join':
                                username = self.get_client_name(sock)

                                for output in self.outputs:
                                    message = 'Join:' + username + ':' + dataSplit[1]
                                    send(output, message)

                            elif dataSplit[0] == 'Group':
                                for output in self.outputs:
                                    senderName = self.get_client_name(sock)
                                    if self.get_client_name(output) != senderName:
                                        send(output, 'Group:' + dataSplit[1] + ":" + senderName + ":" + dataSplit[3])

                            elif dataSplit[0] == 'Invite':
                                senderName = self.get_client_name(sock)
                                for output in self.outputs:
                                    if self.get_client_name(output) == dataSplit[3]:
                                        send(output, 'Invite:' + dataSplit[1] + ':' + senderName)

                            else:
                                # Send as new client's message...
                                msg = f'\n#[{self.get_client_name(sock)}]>> {data}'

                                # Send data to all except ourself
                                for output in self.outputs:
                                    if output != sock:
                                        send(output, msg)
                        else:
                            self.clients -= 1
                            sock.close()
                            inputs.remove(sock)
                            self.outputs.remove(sock)

                            # Sending client leaving information to others
                            msg = f'Disconnected:{self.get_client_name(sock)}'

                            for output in self.outputs:
                                send(output, msg)
                    except socket.error as e:
                        # Remove
                        inputs.remove(sock)
                        self.outputs.remove(sock)

        self.server.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Socket Server Example with Select')
    parser.add_argument('--name', action="store", dest="name", required=True)
    parser.add_argument('--port', action="store",
                        dest="port", type=int, required=True)
    given_args = parser.parse_args()
    port = given_args.port
    name = given_args.name

    server = ChatServer(port)
    server.run()