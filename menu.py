import subprocess

print("Hello Welcome to Remote Sensing Application")
print("Starting the application...")
# Start the processes without output
sensor_process = subprocess.Popen(['python3', 'app.py'],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Application started.")
# Wait a kill command from the user to kill the processes
while True:
    command = input("Enter a command: ")
    if command == 'kill':
        print("Killing the application...")
        subprocess.run(['python3', 'kill_app.py'])
        break
    else:
        print("Invalid command.")
print("Application killed.")
print("Goodbye.")
