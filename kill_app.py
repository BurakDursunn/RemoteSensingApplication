# kill_app.py
import subprocess
import time
from CONFIG import TEMPERATURE_SENSOR_PORT, HUMIDITY_SENSOR_PORT, GATEWAY_SOCKET_PORT, WEB_SERVER_PORT


def find_pid_with_port(port):
    pid = subprocess.check_output(['lsof', '-t', f'-i:{port}'])
    return pid.decode().strip()


pids = []

for port in [TEMPERATURE_SENSOR_PORT, HUMIDITY_SENSOR_PORT, GATEWAY_SOCKET_PORT, WEB_SERVER_PORT]:
    pid = find_pid_with_port(port)
    pids.append(pid)

pid = pids[0].split('\n')
pids[0] = pid[0]
pids.append(pid[1])

print("Killing processes...")
for pid in pids:
    print(f"Killing process with pid {pid}")
    time.sleep(1)
    subprocess.run(['kill', pid])
    time.sleep(1)
    print("Done for this process")
print("Done")
