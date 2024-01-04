import socket
import random
import time
import threading
from CONFIG import TEMPERATURE_SENSOR_HOST, TEMPERATURE_SENSOR_PORT, HUMIDITY_SENSOR_HOST, HUMIDITY_SENSOR_PORT

server_off = False


def timestamp_to_date(timestamp):
    return time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(timestamp))


def log_data_to_file(sensor_type, data, timestamp):
    with open(f'{sensor_type}_sensor.txt', 'a') as f:
        f.write(f'{timestamp_to_date(timestamp)} - {sensor_type}: {data}\n')


def temperature_sensor():
    global server_off
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TEMPERATURE_SENSOR_HOST, TEMPERATURE_SENSOR_PORT))
        try:
            while True:
                temperature = random.uniform(20, 30)
                timestamp = time.time()
                message = f'TEMP|{temperature}|{timestamp}'
                s.sendall(message.encode())
                print(f'Sent: {message}')
                log_data_to_file('temprature', temperature, timestamp)
                time.sleep(1)
        except socket.error:
            print("Server is off")
            server_off = True
            exit(0)


def humidity_sensor():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        last_alive = 0

        try:
            while True:
                humidity = random.uniform(40, 90)
                timestamp = time.time()

                if server_off:
                    break

                if humidity > 80:
                    message = f'HUMID|{humidity}|{timestamp}'
                    s.sendto(message.encode(),
                             (HUMIDITY_SENSOR_HOST, HUMIDITY_SENSOR_PORT))
                    print(f'Sent: {message}')
                    log_data_to_file('humidity', humidity, timestamp)
                    last_alive = 0

                if last_alive == 2:
                    message = f'ALIVE|{timestamp}'
                    s.sendto(message.encode(),
                             (HUMIDITY_SENSOR_HOST, HUMIDITY_SENSOR_PORT))
                    print(f'Sent: {message}')
                    log_data_to_file('humidity', 'ALIVE', timestamp)
                    last_alive = 0
                else:
                    last_alive += 1
                time.sleep(1)
        except socket.error:
            print("Gateway is off")
            exit(0)


if __name__ == "__main__":
    try:
        thread_temprature = threading.Thread(target=temperature_sensor)
        thread_humidity = threading.Thread(target=humidity_sensor)

        thread_temprature.start()
        thread_humidity.start()

        thread_temprature.join()
        thread_humidity.join()
    except KeyboardInterrupt:
        print("Exiting...")
        exit(0)
