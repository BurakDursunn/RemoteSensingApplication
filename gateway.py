import socket
import threading
import time
import select
from CONFIG import TEMPERATURE_SENSOR_HOST, TEMPERATURE_SENSOR_PORT, HUMIDITY_SENSOR_HOST, HUMIDITY_SENSOR_PORT, SERVER_HOST, SERVER_PORT

TEMPERATURE_SENSOR_OFF_INTERVAL = 3
HUMIDITY_SENSOR_OFF_INTERVAL = 7
CONNECTION_TIMEOUT = 15

# Define locks
log_lock = threading.Lock()
server_socket_lock = threading.Lock()


def timestamp_to_date(timestamp):
    return time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(timestamp))


def log_data_to_file(sensor_type, data, timestamp, type):
    with log_lock:
        if type == 'Sent':
            with open(f'gateway_sent.txt', 'a') as f:
                f.write(
                    f'{timestamp_to_date(timestamp)} - {sensor_type}: {data}\n')
        elif type == 'Received':
            with open(f'gateway_received.txt', 'a') as f:
                f.write(
                    f'{timestamp_to_date(timestamp)} - {sensor_type}: {data}\n')


def handle_temperature_data(data, server_socket):
    try:
        temperature, timestamp = data.split('|')[1:]
        message = f'TEMP|{temperature}|{timestamp}'
        server_socket.sendall(message.encode())
        print(f'Sent: {message}')
        log_data_to_file('temperature', temperature, float(timestamp), 'Sent')
    except ValueError as e:
        print(f"Error handling temperature data: {e}")


def handle_humidity_data(data, server_socket):
    try:
        humidity, timestamp = data.split('|')[1:]
        message = f'HUMID|{humidity}|{timestamp}'
        server_socket.sendall(message.encode())
        print(f'Sent: {message}')
        log_data_to_file('humidity', humidity, float(timestamp), 'Sent')
    except ValueError as e:
        print(f"Error handling humidity data: {e}")


def handle_alive_message(server_socket, data):
    try:
        timestamp = data.split('|')[1]
        message = f'ALIVE|{timestamp}'
        server_socket.sendall(message.encode())
        print(f'Sent: {message}')
        log_data_to_file('humidity', 'ALIVE', float(timestamp), 'Sent')
    except ValueError as e:
        print(f"Error handling alive message: {e}")


def handle_data(data, server_socket):
    if data.startswith('TEMP'):
        with server_socket_lock:
            handle_temperature_data(data, server_socket)
    elif data.startswith('HUMID'):
        with server_socket_lock:
            handle_humidity_data(data, server_socket)
    elif data.startswith('ALIVE'):
        with server_socket_lock:
            handle_alive_message(server_socket, data)


def temperature_sensor_listener(server_socket):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_temp:
        s_temp.bind((TEMPERATURE_SENSOR_HOST, TEMPERATURE_SENSOR_PORT))
        s_temp.listen()
        temp_conn, _ = s_temp.accept()

        last_alive_time = time.time()
        while True:
            data = temp_conn.recv(1024)
            if data:
                last_alive_time = time.time()
                data = data.decode()
                print(f'Received: {data}')
                log_data_to_file('temperature', data, time.time(), 'Received')
                handle_data(data, server_socket)
            else:
                if time.time() - last_alive_time >= TEMPERATURE_SENSOR_OFF_INTERVAL:
                    print("Temperature sensor is off")
                    break

            time.sleep(1)
        temp_conn.close()


def humidity_sensor_listener(server_socket):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s_hum:
        s_hum.bind((HUMIDITY_SENSOR_HOST, HUMIDITY_SENSOR_PORT))
        while True:
            ready_sockets, _, _ = select.select(
                [s_hum], [], [], HUMIDITY_SENSOR_OFF_INTERVAL)

            if ready_sockets:
                data, _ = s_hum.recvfrom(1024)
                data = data.decode()
                print(f'Received: {data}')
                log_data_to_file('humidity', data, time.time(), 'Received')
                handle_data(data, server_socket)
            else:
                print("Humidity sensor is off")
                break
            time.sleep(1)
        s_hum.close()


if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.settimeout(CONNECTION_TIMEOUT)
        try:
            server_socket.connect((SERVER_HOST, SERVER_PORT))

            # Handshake
            server_socket.sendall('GATEWAY|HANDSHAKE'.encode())
            handshake_response = server_socket.recv(1024).decode()
            print(f"Handshake successful: {handshake_response}")

            # Start listening to sensors
            thread_temperature = threading.Thread(
                target=temperature_sensor_listener, args=(server_socket,))
            thread_humidity = threading.Thread(
                target=humidity_sensor_listener, args=(server_socket,))

            thread_temperature.start()
            thread_humidity.start()

            thread_temperature.join()
            thread_humidity.join()
        except KeyboardInterrupt:
            print("Exiting...")
            exit(0)
        except socket.timeout:
            print("Server is not responding")
            exit(0)
