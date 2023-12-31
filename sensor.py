import socket
import sys
import threading
import random
import time
from CONFIG import TEMPERATURE_SENSOR_HOST, TEMPERATURE_SENSOR_PORT, HUMIDITY_SENSOR_HOST, HUMIDITY_SENSOR_PORT


class TemperatureSensor(threading.Thread):
    def __init__(self, socket, gateway_socket):
        super().__init__()
        self.socket = socket
        self.gateway_socket = gateway_socket

    def run(self):
        while True:
            temperature = random.uniform(20, 30)
            timestamp = time.time()
            message = f'TEMPERATURE {temperature} {timestamp}'
            self.socket.send(message.encode())
            time.sleep(1)


class HumiditySensor(threading.Thread):
    def __init__(self, socket, gateway_socket, address):
        super().__init__()
        self.socket = socket
        self.gateway_socket = gateway_socket
        self.address = address

    def run(self):
        while True:
            humidity = random.uniform(40, 90)
            timestamp = time.time()

            if humidity > 80:
                message = f'HUMIDITY {humidity} {timestamp}'
                # Send the message to client
                self.socket.sendto(message.encode(), self.address)

            if int(timestamp) % 3 == 0:
                alive_message = 'ALIVE'
                self.socket.sendto(alive_message.encode(), self.address)

            time.sleep(1)


def handshake_tcp(socket):
    print("Handshaking TCP connection...")
    socket.send('CONNECT'.encode())
    if socket.recv(1024).decode() == 'OK':
        print("Connection established.")
        return True
    else:
        print("Connection failed.")
        return False


def handshake_udp(socket):
    print("Handshaking UDP connection...")
    data, address = socket.recvfrom(1024)
    if data.decode() == 'HELLO UDP SERVER':
        print("Connection established.")
        socket.sendto('HELLO UDP CLIENT'.encode(), address)
        return True, address


if __name__ == "__main__":
    # Create a TCP socket for the temperature sensor
    temperature_sensor_socket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)
    temperature_sensor_socket.bind(
        (TEMPERATURE_SENSOR_HOST, TEMPERATURE_SENSOR_PORT))
    temperature_sensor_socket.listen(1)
    temperature_sensor_socket, gateway_address_temperature = temperature_sensor_socket.accept()
    print(f"Connection from {gateway_address_temperature} established.")

    # Handshake with the gateway
    if handshake_tcp(temperature_sensor_socket):
        temperature_sensor_thread = TemperatureSensor(
            temperature_sensor_socket, None)

    # Create a UDP socket for the humidity sensor
    humidity_sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    humidity_sensor_socket.bind((HUMIDITY_SENSOR_HOST, HUMIDITY_SENSOR_PORT))

    # Handshake with the gateway
    handshake_result, gateway_address_humidity = handshake_udp(
        humidity_sensor_socket)
    if handshake_result:
        humidity_sensor_thread = HumiditySensor(
            humidity_sensor_socket, None, gateway_address_humidity)

    # Start the threads
    temperature_sensor_thread.start()
    humidity_sensor_thread.start()

    try:
        # Wait for the threads to finish
        temperature_sensor_thread.join()
        humidity_sensor_thread.join()
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Exiting...")
        temperature_sensor_socket.close()
        humidity_sensor_socket.close()
        sys.exit(0)
    finally:
        temperature_sensor_socket.close()
        humidity_sensor_socket.close()
        sys.exit(0)
