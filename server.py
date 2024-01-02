# server.py
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import time
import sys
from CONFIG import GATEWAY_SOCKET_HOST, GATEWAY_SOCKET_PORT, WEB_SERVER_HOST, WEB_SERVER_PORT

# Global variables
humidity_global = []
temperature_global = []
last_humidity = {}
temperature_sensor_alive = False
humidity_sensor_alive = False
shutdown_event = threading.Event()


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


class GatewayDataReceiverServerHTTP(BaseHTTPRequestHandler):
    def check_sensors_alive(self):
        global temperature_sensor_alive, humidity_sensor_alive
        if not temperature_sensor_alive and not humidity_sensor_alive:
            print('ALL SENSORS OFF')
            shutdown_event.set()

    def do_POST(self):
        global temperature_sensor_alive, humidity_sensor_alive
        if self.path == '/humidity':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            # Get the data from the request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode()
            # Parse the data
            data = body.split()
            humidity = data[1]
            if humidity == 'OFF':
                timestamp = data[2]
                timestamp = float(timestamp)
                # timestamp to string, format: dd/mm/yyyy hh:mm:ss
                timestamp = time.strftime(
                    '%d/%m/%Y %H:%M:%S', time.localtime(timestamp))
                print('HUMIDITY SENSOR OFF AT', timestamp)
                humidity_sensor_alive = False
                # Add the data to the global variable
                humidity_global.append(
                    {'humidity': "HUMIDITY SENSOR OFF", 'timestamp': timestamp})
            elif humidity == 'ALIVE':
                timestamp = data[2]
                timestamp = float(timestamp)
                # timestamp to string
                timestamp = time.strftime(
                    '%d/%m/%Y %H:%M:%S', time.localtime(timestamp))
                print('HUMIDITY SENSOR ALIVE AT', timestamp)
                humidity_sensor_alive = True
                # Add the data to the global variable
                humidity_global.append(
                    {'humidity': "HUMIDITY SENSOR ALIVE", 'timestamp': timestamp})
            else:
                timestamp = data[2]
                # str to float
                humidity = float(humidity)
                humidity = round(humidity, 1)
                # str to timestamp
                timestamp = float(timestamp)
                # timestamp to string
                timestamp = time.strftime(
                    '%d/%m/%Y %H:%M:%S', time.localtime(timestamp))
                # Display the data
                print(f'Humidity: {humidity} % at {timestamp}')
                humidity_sensor_alive = True
                # Add the data to the global variable
                humidity_global.append(
                    {'humidity': f"{humidity} %", 'timestamp': timestamp})
                # Update the last humidity
                last_humidity['humidity'] = f"{humidity} %"
                last_humidity['timestamp'] = timestamp
        elif self.path == '/temperature':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            # Get the data from the request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode()
            # Parse the data
            data = body.split()
            temperature = data[1]
            if temperature == 'OFF':
                timestamp = data[2]
                timestamp = float(timestamp)
                # timestamp to string
                timestamp = time.strftime(
                    '%d/%m/%Y %H:%M:%S', time.localtime(timestamp))
                print('TEMPERATURE SENSOR OFF AT', timestamp)
                temperature_sensor_alive = False
                # Add the data to the global variable
                temperature_global.append(
                    {'temperature': "TEMPERATURE SENSOR OFF", 'timestamp': timestamp})
            else:
                timestamp = data[2]
                # str to float
                temperature = float(temperature)
                temperature = round(temperature, 1)
                # str to timestamp
                timestamp = float(timestamp)
                # timestamp to string
                timestamp = time.strftime(
                    '%d/%m/%Y %H:%M:%S', time.localtime(timestamp))
                # Display the data
                print(f'Temperature: {temperature} C at {timestamp}')
                temperature_sensor_alive = True
                # Add the data to the global variable
                temperature_global.append(
                    {'temperature': f"{temperature} °C", 'timestamp': timestamp})
        self.check_sensors_alive()


if __name__ == '__main__':
    # Create a HTTP backend server to receive data from the gateway
    gateway_server = HTTPServer(
        (GATEWAY_SOCKET_HOST, GATEWAY_SOCKET_PORT), GatewayDataReceiverServerHTTP)
    print(
        f"Gateway data receiver server running on {GATEWAY_SOCKET_HOST}:{GATEWAY_SOCKET_PORT}")

    # Create a HTTP server to display data from the sensors
    server = HTTPServer((WEB_SERVER_HOST, WEB_SERVER_PORT),
                        RemoteSensingWebServer)
    print(f"Web server running on {WEB_SERVER_HOST}:{WEB_SERVER_PORT}")

    # Start server
    try:
        gateway_thread = threading.Thread(target=gateway_server.serve_forever)
        web_thread = threading.Thread(target=server.serve_forever)

        gateway_thread.start()
        web_thread.start()

        while True:
            if shutdown_event.is_set():
                print('\nStopping server')
                gateway_server.shutdown()
                server.shutdown()
                sys.exit(0)
            time.sleep(1)
    except KeyboardInterrupt:
        print('\nStopping server')
        gateway_server.shutdown()
        server.shutdown()
        sys.exit(0)
