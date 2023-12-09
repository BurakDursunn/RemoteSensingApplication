import socket
import random
import time


def generate_humidity():
    return random.uniform(40, 90)


def send_humidity_data(udp_socket):
    while True:
        humidity = generate_humidity()
        timestamp = time.time()

        if humidity > 80:
            message = f'HUMIDITY {humidity} {timestamp}'
            udp_socket.sendto(message.encode(), ('localhost', 5556))

        if int(timestamp) % 3 == 0:
            alive_message = 'ALIVE'
            udp_socket.sendto(alive_message.encode(), ('localhost', 5556))

        time.sleep(1)


if __name__ == "__main__":
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    send_humidity_data(udp_socket)