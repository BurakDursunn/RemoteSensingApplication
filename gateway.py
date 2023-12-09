import socket
import threading
import time


def receive_temperature_data(tcp_socket):
    while True:
        data = tcp_socket.recv(1024).decode()
        print(f"Received Temperature Data: {data}")
        # Parse and send to server
        time.sleep(1)


def receive_humidity_data(udp_socket):
    while True:
        data, addr = udp_socket.recvfrom(1024)
        print(f"Received Humidity Data from {addr}: {data.decode()}")
        # Parse and send to server
        time.sleep(1)


if __name__ == "__main__":
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(('localhost', 5555))
    tcp_socket.listen(5)

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('localhost', 5556))

    temperature_thread = threading.Thread(target=receive_temperature_data, args=(tcp_socket,))
    humidity_thread = threading.Thread(target=receive_humidity_data, args=(udp_socket,))

    temperature_thread.start()
    humidity_thread.start()

    temperature_thread.join()
    humidity_thread.join()
