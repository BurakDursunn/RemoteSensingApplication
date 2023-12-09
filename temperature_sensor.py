import socket
import random
import time


def generate_temperature():
    return random.uniform(20, 30)


def send_temperature_data(tcp_socket):
    while True:
        temperature = generate_temperature()
        timestamp = time.time()
        message = f'TEMPERATURE {temperature} {timestamp}'
        tcp_socket.send(message.encode())
        time.sleep(1)


if __name__ == "__main__":
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect(('localhost', 5555))
    send_temperature_data(tcp_socket)