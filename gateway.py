import socket
import threading
import time
import signal
import sys

def receive_temperature_data(tcp_socket, server_socket):
    last_temperature_time = time.time()

    while not exit_signal.is_set():
        data = tcp_socket.recv(1024).decode()
        print(f"Received Temperature Data: {data}")
        # Parse and send to server
        server_socket.send(f"TEMP {data}".encode())
        last_temperature_time = time.time()
        time.sleep(1)

        # Check if temperature sensor is inactive
        if time.time() - last_temperature_time > 3:
            print("TEMP SENSOR OFF")
            server_socket.send("TEMP SENSOR OFF".encode())

def receive_humidity_data(udp_socket, server_socket):
    last_alive_time = time.time()

    while not exit_signal.is_set():
        data, addr = udp_socket.recvfrom(1024)
        print(f"Received Humidity Data from {addr}: {data.decode()}")
        # Parse and send to server
        server_socket.send(f"HUMIDITY {data.decode()}".encode())
        last_alive_time = time.time()
        time.sleep(1)

        # Check if humidity sensor is inactive
        if time.time() - last_alive_time > 7:
            print("HUMIDITY SENSOR OFF")
            server_socket.send("HUMIDITY SENSOR OFF".encode())

def signal_handler(sig, frame):
    print("Exiting...")
    exit_signal.set()

if __name__ == "__main__":
    exit_signal = threading.Event()
    signal.signal(signal.SIGINT, signal_handler)

    # Socket for receiving data from sensors
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(('localhost', 5555))
    tcp_socket.listen(5)

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('localhost', 5556))

    # Socket for sending data to the server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect(('localhost', 5557))  # Assuming server is running on port 5557

    temperature_thread = threading.Thread(target=receive_temperature_data, args=(tcp_socket, server_socket))
    humidity_thread = threading.Thread(target=receive_humidity_data, args=(udp_socket, server_socket))

    temperature_thread.start()
    humidity_thread.start()

    temperature_thread.join()
    humidity_thread.join()

    sys.exit(0)
