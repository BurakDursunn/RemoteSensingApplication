import socket
import threading
import random
import time

class TemperatureSensor(threading.Thread):
    def __init__(self, tcp_ip, tcp_port):
        threading.Thread.__init__(self)
        self.tcp_ip = tcp_ip
        self.tcp_port = tcp_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.tcp_ip, self.tcp_port))

    def run(self):
        while True:
            temperature = random.uniform(20, 30)
            timestamp = time.time()
            message = f'TEMP|{temperature}|{timestamp}'
            self.sock.send(message.encode())
            time.sleep(1)

class HumiditySensor(threading.Thread):
    def __init__(self, udp_ip, udp_port):
        threading.Thread.__init__(self)
        self.udp_ip = udp_ip
        self.udp_port = udp_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run(self):
        while True:
            humidity = random.randint(40, 90)
            timestamp = time.time()
            
            if humidity > 80:
                message = f'HUMID|{humidity}|{timestamp}'
                self.sock.sendto(message.encode(), (self.udp_ip, self.udp_port))
                
            if int(timestamp) % 3 == 0:
                alive_msg = 'ALIVE'
                self.sock.sendto(alive_msg.encode(), (self.udp_ip, self.udp_port))
            
            time.sleep(1)

def main():
    TCP_IP = '127.0.0.1'
    TCP_PORT = 6000
    UDP_IP = '127.0.0.1'
    UDP_PORT = 7000

    temp_sensor = TemperatureSensor(TCP_IP, TCP_PORT)
    humid_sensor = HumiditySensor(UDP_IP, UDP_PORT)

    temp_sensor.start()
    humid_sensor.start()

if __name__ == "__main__":
    main()
