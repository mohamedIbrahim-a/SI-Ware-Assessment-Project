# Si-Ware Smart Factory Dashboard

A real-time sensor monitoring and control system with remote maintenance capabilities.

## Features

### Core Functionality
- **Real-time Sensor Monitoring**: Live data visualization for multiple sensor types (Temperature, Pressure, Speed, Vibration, Optical)
- **Trend Analysis**: Historical plots showing sensor behavior over time
- **Alarm Management**: Automatic detection and logging of faults and limit violations
- **Multi-channel Notifications**: Desktop, Email, and SMS alerts for critical events

### Remote Maintenance Console
- **Secure Access Control**: Password-protected maintenance operations
- **Remote Commands**: Reset simulation, clear faults, pause/resume data generation
- **Live System Logs**: Real-time audit trail of all maintenance actions

### Professional UI
- Modern dark theme with card-based layout
- Color-coded alarm states (Purple for faults, Red for limit violations)
- Interactive controls with visual feedback
- Responsive design with split-panel views

## Architecture

```
Siware_task/
├── core/
│   ├── sensor_config.py    # Sensor definitions and configuration
│   ├── comm_thread.py      # Client communication thread
│   └── notifications.py    # Multi-channel notification manager
├── gui/
│   └── dashboard.py         # Main dashboard UI
├── simulator.py             # Sensor data simulator (server)
└── main.py                  # Application entry point
```

## Installation

### Requirements
- Python 3.8+
- PyQt6
- pyqtgraph
- numpy
- twilio (for SMS notifications)

### Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
# PowerShell:
.\.venv\Scripts\Activate.ps1
# CMD:
.\.venv\Scripts\activate.bat

# Activate (Linux/macOS)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Start the Simulator
```bash
python simulator.py -p 9999
```

### Launch the Dashboard
```bash
python main.py -p 9999
```

### Running Unit Tests
```bash
python -m unittest tests/test_system.py
```

## Command Line Interface (CLI)

Both the simulator and the dashboard support command-line arguments for flexible configuration.

### Sensor Simulator (`simulator.py`)

| Argument | Flag | Default | Description |
|----------|------|---------|-------------|
| Port | `-p`, `--port` | `9999` | The TCP port the simulator listens on. |
| Update Rate | `-r`, `--rate` | `0.5` | How often (in seconds) data is pushed to clients. |
| Sensor Count | `-n`, `--count` | `10` | Total sensors to simulate (dynamic generation). |

**Example**: Run with 20 sensors and a 1.0s update rate:
```bash
python simulator.py --count 20 --rate 1.0
```

### Dashboard GUI (`main.py`)

| Argument | Flag | Default | Description |
|----------|------|---------|-------------|
| Host | `--host` | `127.0.0.1` | The IP address of the sensor simulator. |
| Port | `-p`, `--port` | `9999` | The port the dashboard connects to. |

**Example**: Connect to a remote simulator on port 8080:
```bash
python main.py --host 192.168.1.5 --port 8080
```

### Maintenance Console Access
- Navigate to the "Maintenance" tab
- Click "Unlock Console"
- Enter password: `admin123`

## Configuration

The system uses environment variables for sensitive credentials. You can set these in a `.env` file in the root directory.

### Environment Variables (.env)

Create a `.env` file and add the following keys:

```ini
# Email Configuration
EMAIL_ENABLED=False
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password-here
EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587

# SMS Configuration (Twilio)
SMS_ENABLED=False
SMS_TWILIO_SID=your-twilio-sid
SMS_TWILIO_TOKEN=your-twilio-token
SMS_TWILIO_FROM=+1234567890
SMS_TWILIO_TO=+0987654321
```

> [!TIP]
> For Gmail, you must use an **App Password**. See the [Google Account Security](https://myaccount.google.com/apppasswords) page to generate one.


## Remote Commands

| Command | Description |
|---------|-------------|
| `RESET` | Reset all sensor values to defaults |
| `CLEAR_FAULTS` | Clear all active fault states |
| `TOGGLE_SIM` | Pause/Resume data generation |

## Development

### Sensor Configuration
Sensors are defined in `core/sensor_config.py`:
```python
SENSOR_CONFIG = {
    "S01": {
        "name": "Temperature",
        "type": "Analog",
        "unit": "°C",
        "limits": (15.0, 25.0)
    },
    # ... more sensors
}
```

### Simulation Parameters
Adjust fault probability and drift in `core/sensor_config.py`:
```python
SIM_CONFIG = {
    "update_rate": 0.5,      # Seconds between updates
    "fault_prob": 0.001,     # Probability of fault per update
    "spike_prob": 0.005,     # Probability of limit spike
    "drift_amount": 0.02,    # Trend drift factor
    "fault_duration": 20.0   # Fault duration in seconds
}
```

## Author

Mohamed Ibrahim
