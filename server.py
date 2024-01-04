import socket
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from CONFIG import SERVER_HOST, SERVER_PORT

# Global variables
humidity_global = []
temperature_global = []
last_humidity = {}


class RemoteSensingWebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        global humidity_global, temperature_global
        if self.path == '/humidity':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Import and modify HTML for humidity
            html = self.import_html('humidity.html')
            html_content = self.replace_placeholder(
                html, humidity_global, '<!-- humidity-data on python -->', "humidity")

            # Send the HTML
            self.wfile.write(bytes(html_content, 'utf8'))
        elif self.path == '/temperature':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Import and modify HTML for temperature
            html = self.import_html('temperature.html')
            html_content = self.replace_placeholder(
                html, temperature_global, '<!-- temperature-data on python -->', "temperature")

            # Send the HTML
            self.wfile.write(bytes(html_content, 'utf8'))
        elif self.path == '/gethumidity':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # if last_humidity is empty
            if not last_humidity:
                # Import and modify HTML for humidity
                html = self.import_html('last_humidity.html')
                row = f'<tr><td>No data</td><td>No data</td><td>No data</td></tr>'
                html_content = html.replace(
                    '<!-- humidity-data on python -->', row)

                # Send the HTML
                self.wfile.write(bytes(html_content, 'utf8'))
            else:
                # Import and modify HTML for humidity
                html = self.import_html('last_humidity.html')
                row = ''
                row += f'<tr><td>{0}</td><td>{last_humidity["humidity"]}</td><td>{last_humidity["timestamp"]}</td></tr>'
                html_content = html.replace(
                    '<!-- humidity-data on python -->', row)

                # Send the HTML
                self.wfile.write(bytes(html_content, 'utf8'))

    def import_html(self, file_name):
        with open(file_name, 'r') as file:
            html_content = file.read()
        return html_content

    def replace_placeholder(self, html_content, data, placeholder_id, sensor_name):
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
        last_humidity = {'humidity': f"{data[1]} %", 'timestamp': data[2]}
    elif data.startswith('ALIVE'):
        data = data.split('|')
        log_data_to_file('humidity', 'ALIVE', float(data[1]), 'Received')
        data[1] = float(data[1])
        data[1] = time.strftime('%d/%m/%Y %H:%M:%S',
                                time.localtime(data[1]))
        humidity_global.append(
            {'humidity': 'ALIVE', 'timestamp': data[1]})


def server_listener():
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


if __name__ == "__main__":
    try:
        server_listener_thread = threading.Thread(target=server_listener)
        server_listener_thread.start()

        web_server = HTTPServer(('localhost', 8080), RemoteSensingWebServer)
        print("Web server listening on localhost:8080")
        web_server.serve_forever()

        server_listener_thread.join()
    except KeyboardInterrupt:
        print("Exiting...")
        exit(0)
