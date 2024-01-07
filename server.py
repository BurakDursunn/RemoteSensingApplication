import socket
import time
import threading
from CONFIG import SERVER_HOST, SERVER_PORT, WEB_SERVER_HOST, WEB_SERVER_PORT

# Global variables
humidity_global = []
temperature_global = []
last_humidity = {}
gateway_conn = None


def timestamp_to_date(timestamp):
    return time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(timestamp))


def log_data_to_file(sensor_type, data, timestamp, type):
    if type == 'Sent':
        with open(f'server_sent.txt', 'a') as f:
            f.write(f'{timestamp_to_date(timestamp)} - {sensor_type}: {data}\n')
    elif type == 'Received':
        with open(f'server_received.txt', 'a') as f:
            f.write(f'{timestamp_to_date(timestamp)} - {sensor_type}: {data}\n')


def parse_data(data):
    global humidity_global, temperature_global, last_humidity
    if data.startswith('TEMP'):
        data = data.split('|')
        log_data_to_file('temperature', data[1], float(data[2]), 'Received')
        data[1] = float(data[1])
        data[1] = round(data[1], 1)
        data[2] = float(data[2])
        data[2] = time.strftime('%d/%m/%Y %H:%M:%S',
                                time.localtime(data[2]))
        temperature_global.append(
            {'temperature': f"{data[1]} °C", 'timestamp': data[2]})
    elif data.startswith('HUMID'):
        data = data.split('|')
        log_data_to_file('humidity', data[1], float(data[2]), 'Received')
        data[1] = float(data[1])
        data[1] = round(data[1], 1)
        data[2] = float(data[2])
        data[2] = time.strftime('%d/%m/%Y %H:%M:%S',
                                time.localtime(data[2]))
        humidity_global.append(
            {'humidity': f"{data[1]} %", 'timestamp': data[2]})
    elif data.startswith('ALIVE'):
        data = data.split('|')
        log_data_to_file('humidity', 'ALIVE', float(data[1]), 'Received')
        data[1] = float(data[1])
        data[1] = time.strftime('%d/%m/%Y %H:%M:%S',
                                time.localtime(data[1]))
        humidity_global.append(
            {'humidity': 'ALIVE', 'timestamp': data[1]})
    elif data.startswith('LASTHUMID'):
        data = data.split('|')
        log_data_to_file('last_humidity', data[1], float(data[2]), 'Received')
        data[1] = float(data[1])
        data[1] = round(data[1], 1)
        data[2] = float(data[2])
        data[2] = time.strftime('%d/%m/%Y %H:%M:%S',
                                time.localtime(data[2]))
        last_humidity = {'humidity': f"{data[1]} %", 'timestamp': data[2]}
    else:
        print(f"Unknown data: {data}")


def server_listener():
    global gateway_conn
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((SERVER_HOST, SERVER_PORT))
            server_socket.listen()

            print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

            conn, _ = server_socket.accept()

            # Handshake
            handshake_request = conn.recv(1024).decode()
            if 'GATEWAY|HANDSHAKE' in handshake_request:
                conn.sendall("SERVER|CONNECT".encode())
                print("Handshake successful")
                gateway_conn = conn

            while True:
                data = conn.recv(1024)
                if not data:
                    print("Connection closed by gateway.")
                    break

                data = data.decode()
                print(f'Received: {data}')
                parse_data(data)

            conn.close()
    except KeyboardInterrupt:
        print("Exiting...")
        exit(0)


def log_web_request_to_file(addr, request_type, request_path, response_code=200):
    with open(f'web_requests.txt', 'a') as f:
        f.write(
            f'{addr[0]}:{addr[1]} - {request_type} {request_path} - {response_code}\n')


def handle_web_request(conn, addr):
    global last_humidity
    request_data = conn.recv(1024).decode('utf-8')

    # Parse the request
    request_lines = request_data.split('\n')
    request_line = request_lines[0].split(' ')
    request_type = request_line[0]
    request_path = request_line[1]

    # Send the response
    response = ''
    html_content = ''
    response_code = 200
    if request_type == 'GET':
        if request_path == '/humidity':
            # Send 200 OK response
            response = "HTTP/1.1 200 OK\n"
            html = import_html('humidity.html')
            html_content = replace_placeholder(
                html, humidity_global, '<!-- humidity-data on python -->', "humidity")
        elif request_path == '/temperature':
            # Send 200 OK response
            response = "HTTP/1.1 200 OK\n"
            html = import_html('temperature.html')
            html_content = replace_placeholder(
                html, temperature_global, '<!-- temperature-data on python -->', "temperature")
        elif request_path == '/gethumidity':
            # Request for last humidity from gateway
            gateway_conn.sendall('SERVER|GETHUMIDITY'.encode())
            print('Sent: SERVER|GETHUMIDITY')
            # Wait for data to be received from gateway
            while True:
                if last_humidity:
                    break
            # Send 200 OK response
            response = "HTTP/1.1 200 OK\n"
            html = import_html('last_humidity.html')
            row = ''
            row += f'<tr><td>{0}</td><td>{last_humidity["humidity"]}</td><td>{last_humidity["timestamp"]}</td></tr>'
            html_content = html.replace(
                '<!-- humidity-data on python -->', row)
            last_humidity = {}
        else:
            # Send 404 Not Found response
            response = "HTTP/1.1 404 Not Found\n"
            response_code = 404
            html_content = import_html('404.html')
    else:
        # Send 405 Method Not Allowed response
        response = "HTTP/1.1 405 Method Not Allowed\n"
        response_code = 405
        html_content = import_html('405.html')

    conn.sendall(response.encode())
    # Send the headers
    response += "Content-Type: text/html\n"
    response += "Connection: close\n\n"

    # Send the response
    conn.sendall(response.encode())
    conn.sendall(html_content.encode())

    # Log the request
    print(
        f"Website request from {addr[0]}:{addr[1]} - {request_type} {request_path} - {response_code}")
    log_web_request_to_file(addr, request_type, request_path, response_code)

    # Close the connection
    conn.close()


def import_html(file_name):
    with open(file_name, 'r') as file:
        html_content = file.read()
    return html_content


def replace_placeholder(html_content, data, placeholder_id, sensor_name):
    # Create a td tag for each data point
    rows = ''
    if sensor_name == 'humidity':
        i = 0
        for entry in data:
            rows += f'<tr><td>{i}</td><td>{entry["humidity"]}</td><td>{entry["timestamp"]}</td></tr>'
            i += 1
    elif sensor_name == 'temperature':
        i = 0
        for entry in data:
            rows += f'<tr><td>{i}</td><td>{entry["temperature"]}</td><td>{entry["timestamp"]}</td></tr>'
            i += 1

    # Replace the placeholder with the data
    html_content = html_content.replace(placeholder_id, rows)
    return html_content


if __name__ == "__main__":
    try:
        server_listener_thread = threading.Thread(target=server_listener)
        server_listener_thread.start()

        # Wait for data to be received
        while True:
            if humidity_global or temperature_global:
                break

        # Create a web server and listen for requests
        web_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        web_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        web_server_socket.bind((WEB_SERVER_HOST, WEB_SERVER_PORT))
        web_server_socket.listen()

        print(f"Web server listening on {WEB_SERVER_HOST}:{WEB_SERVER_PORT}")

        while True:
            # Accept a connection
            conn, addr = web_server_socket.accept()

            # Open thread to handle the request
            request_handler_thread = threading.Thread(
                target=handle_web_request, args=(conn, addr))
            request_handler_thread.start()

    except KeyboardInterrupt:
        print("Exiting...")
        exit(0)
