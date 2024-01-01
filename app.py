# app.py
import subprocess
import webbrowser
import time
from CONFIG import TEMPERATURE_SENSOR_PORT, HUMIDITY_SENSOR_PORT, GATEWAY_SOCKET_PORT, WEB_SERVER_PORT

# Start the processes
sensor_process = subprocess.Popen(['python3', 'sensor.py'])
time.sleep(1)
gateway_process = subprocess.Popen(['python3', 'gateway.py'])
time.sleep(1)
server_process = subprocess.Popen(['python3', 'server.py'])

# Open the web browser
time.sleep(1)
webbrowser.open_new_tab('http://localhost:8080/temperature')
time.sleep(1)
webbrowser.open_new_tab('http://localhost:8080/humidity')
time.sleep(1)
webbrowser.open_new_tab('http://localhost:8080/gethumidity')

# Wait for the processes to finish
sensor_process.wait()
gateway_process.wait()
server_process.wait()
