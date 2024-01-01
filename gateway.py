import socket
import threading
import time
import sys
import http.client
from CONFIG import GATEWAY_SOCKET_HOST, GATEWAY_SOCKET_PORT, TEMPERATURE_SENSOR_HOST, TEMPERATURE_SENSOR_PORT, HUMIDITY_SENSOR_HOST, HUMIDITY_SENSOR_PORT

temperature_lock = threading.Lock()
humidity_lock = threading.Lock()


class TemperatureSensorReciever(threading.Thread):
    def __init__(self, temperature_sensor_socket):
        super().__init__()
        self.temperature_sensor_socket = temperature_sensor_socket
        self.last_alive = 0

    def send_data_to_gateway(self, temperature, timestamp):
        # Send the data to server
        connection = http.client.HTTPConnection(
            GATEWAY_SOCKET_HOST, GATEWAY_SOCKET_PORT)
        headers = {'Content-type': 'text/plain'}
        path = '/temperature'
        data = f"temperature {temperature} {timestamp}"

        try:
            connection.request('POST', path, data, headers)
            response = connection.getresponse()
            print(
                f'Temperature data sent successfully. Response: {response.status}, {response.reason}')
        except Exception as e:
            print(f'Error while sending temperature data: {e}')
            connection.close()
        finally:
            connection.close()

    def parse_data(self, data):
        # Parse the data
        data = data.split()
        temperature = data[1]
        timestamp = data[2]
        # str to float
        temperature = float(temperature)
        # str to timestamp
        timestamp = float(timestamp)

        # Send the data to gateway
        self.send_data_to_gateway(temperature, timestamp)

    def run(self):
        self.last_alive = 0
        while True:
            data = self.temperature_sensor_socket.recv(1024).decode()
            if data:
                self.last_alive = 0
                with temperature_lock:
                    self.parse_data(data)
            else:
                if self.last_alive > 3:
                    print("TEMP SENSOR OFF")
                    with temperature_lock:
                        self.send_data_to_gateway(
                            "OFF", time.time())
                    break
                self.last_alive += 1
                time.sleep(1)


class HumiditySensorReciever(threading.Thread):
    def __init__(self, humidity_sensor_socket):
        super().__init__()
        self.humidity_sensor_socket = humidity_sensor_socket

    def send_data_to_gateway(self, humidity, timestamp):
        # Send the data to server
        connection = http.client.HTTPConnection(
            GATEWAY_SOCKET_HOST, GATEWAY_SOCKET_PORT)
        headers = {'Content-type': 'text/plain'}
        path = '/humidity'
        data = f"humidity {humidity} {timestamp}"

        try:
            connection.request('POST', path, data, headers)
            response = connection.getresponse()
            print(
                f'Humidity data sent successfully. Response: {response.status}, {response.reason}')
        except Exception as e:
            print(f'Error while sending humidity data: {e}')
            connection.close()
        finally:
            connection.close()

    def parse_data(self, data):
        # Parse the data
        data = data.split()
        humidity = data[1]
        timestamp = data[2]
        # str to float
        humidity = float(humidity)
        # str to timestamp
        timestamp = float(timestamp)

        # Send the data to gateway
        self.send_data_to_gateway(humidity, timestamp)

    def run(self):
        while True:
            try:
                data, address = self.humidity_sensor_socket.recvfrom(1024)
                if data:
                    # if data is ALIVE, print it, else parse it
                    if data.decode() == "ALIVE":
                        with humidity_lock:
                            # Send the data to server
                            self.send_data_to_gateway(
                                "ALIVE", time.time())
                    else:
                        with humidity_lock:
                            self.parse_data(data.decode())
            except socket.timeout:
                print("HUMIDITY SENSOR OFF")
                with humidity_lock:
                    # Send the data to server
                    self.send_data_to_gateway(
                        "OFF", time.time())
                break


def handshake_tcp(socket):
    if socket.recv(1024).decode() == 'CONNECT':
        print("Connection established.")
        socket.send('OK'.encode())
        return True


def handshake_udp(socket):
    print("Handshaking UDP connection...")
    socket.sendto('HELLO UDP SERVER'.encode(),
                  (HUMIDITY_SENSOR_HOST, HUMIDITY_SENSOR_PORT))
    if socket.recv(1024).decode() == 'HELLO UDP CLIENT':
        print("Connection established.")
        return True


if __name__ == "__main__":
    # Connect to sensors
    # Create a TCP socket for the temperature sensor
    temperature_sensor_socket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the temperature sensor
    temperature_sensor_socket.connect(
        (TEMPERATURE_SENSOR_HOST, TEMPERATURE_SENSOR_PORT))

    # Handshake with the temperature sensor
    if handshake_tcp(temperature_sensor_socket):
        temperature_sensor_reciever = TemperatureSensorReciever(
            temperature_sensor_socket)

    # Create a UDP socket for the humidity sensor
    humidity_sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    humidity_sensor_socket.settimeout(7)

    # Handshake with the humidity sensor
    if handshake_udp(humidity_sensor_socket):
        humidity_sensor_reciever = HumiditySensorReciever(
            humidity_sensor_socket)

    # Start the threads
    temperature_sensor_reciever.start()
    humidity_sensor_reciever.start()

    try:
        # Wait for the threads to finish
        temperature_sensor_reciever.join()
        humidity_sensor_reciever.join()
    except KeyboardInterrupt:
        # Close the sockets
        temperature_sensor_socket.close()
        humidity_sensor_socket.close()
        sys.exit(0)
    finally:
        # Close the sockets
        temperature_sensor_socket.close()
        humidity_sensor_socket.close()
        sys.exit(0)
