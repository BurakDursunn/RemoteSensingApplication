# RemoteSensingApplication

## Description

The RemoteSensingApplication is a system designed to collect and display temperature and humidity data from sensors. It consists of three main components: sensor modules (`sensor.py`), a gateway module (`gateway.py`), and a web server module (`server.py`). Additionally, there is a utility script (`kill_app.py`) provided to terminate the running processes.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)

## Installation

To install and set up the RemoteSensingApplication, follow these steps:

1. **Clone the Repository:**

   ```bash
   git clone [repository_url]
   cd RemoteSensingApplication
   ```

2. **Configuration:**
   Open the `CONFIG.py` file and modify the configuration parameters according to your setup.

## Usage

Follow these steps to run the RemoteSensingApplication:

1. **Run the Application:**
   Execute the `app.py` script to start the sensor, gateway, and web server processes:

   ```bash
   python3 app.py
   ```

2. **Access Web Interface:**
   Open your web browser and navigate to the following URLs:

   - Temperature: [http://localhost:8080/temperature](http://localhost:8080/temperature)
   - Humidity: [http://localhost:8080/humidity](http://localhost:8080/humidity)
   - Get Humidity: [http://localhost:8080/gethumidity](http://localhost:8080/gethumidity)

3. **Shutdown the Application:**
   To gracefully shutdown the application, use the provided `kill_app.py` script:
   ```bash
   python3 kill_app.py
   ```

Please note that the application relies on random sensor data for demonstration purposes. In a real-world scenario, you would replace this simulated data with actual sensor readings. Additionally, ensure that the specified ports in the `CONFIG.py` file are available and not in use by other processes on your system.
