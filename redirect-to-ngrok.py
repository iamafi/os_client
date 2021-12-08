""" Supposed to be used only for testing """

import socket
import sys


JSON_SIZE = 32768


def run():
    # Create localhost:8080 socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 8080))
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Connect to ngrok
    ngrok_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ngrok_socket.connect((ngrok_address, ngrok_port))
    print('Connected to ngrok')

    # Listen to connection from localhost:8080
    server_socket.listen()
    print('Listening to local port 8080\n')

    while True:
        client_connection(server_socket, ngrok_socket)


def client_connection(server_socket, ngrok_socket):
    print('Waiting for your program to connect')
    client_socket, address = server_socket.accept()
    print('Connection accepted\n')

    while True:
        request = client_socket.recv(JSON_SIZE)
        if not request:  # Client has disconnected
            print('Client has disconnected')
            break
        ngrok_socket.sendall(request)
        print('-- Received local request, forwarded it to ngrok')

        response = ngrok_socket.recv(JSON_SIZE)
        client_socket.send(response)
        print('-- Received ngrok response, forwarded it to client\n')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        raise ValueError(f'Script requires 2 command line args (ngrok IP, ngrok port), {len(sys.argv)} were given')
    else:
        ngrok_address, ngrok_port = str(sys.argv[1]), int(sys.argv[2])

    run()
