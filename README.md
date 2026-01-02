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
│   ├── comm_thread.py       # Client communication thread
│   └── notifications.py     # Multi-channel notification manager
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
.\.venv\Scripts\activate

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

### Maintenance Console Access
- Navigate to the "Maintenance" tab
- Click "Unlock Console"
- Enter password: `admin123`

## Configuration

### Email Notifications
Edit `core/notifications.py`:
```python
self.email_config = {
    "enabled": True,
    "sender": "your-email@gmail.com",
    "password": "your-app-password",  # Use Google App Password
    "recipients": ["recipient@example.com"],
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587
}
```

### SMS Notifications
Configure Twilio credentials in `core/notifications.py`:
```python
self.sms_config = {
    "enabled": True,
    "sid": "your-twilio-sid",
    "token": "your-twilio-token",
    "from": "+1234567890",
    "to": "+0987654321"
}
```

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

## License

This project was developed as part of the Si-Ware assessment.

## Author

Mohamed Ibrahim
