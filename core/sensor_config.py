# Sensor Configuration

# Detailed Sensor Definitions
# ID is the key
SENSOR_CONFIG = {
    "S01": {
        "name": "Temperature",
        "type": "Thermal",
        "unit": "°C",
        "limits": (20.0, 80.0) # Low, High
    },
    "S02": {
        "name": "Pressure",
        "type": "Barometric",
        "unit": "hPa",
        "limits": (800.0, 1200.0)
    },
    "S03": {
        "name": "Speed",
        "type": "Mechanical",
        "unit": "RPM",
        "limits": (0.0, 1500.0)
    },
    "S04": {
        "name": "Vibration",
        "type": "Mechanical",
        "unit": "mm/s",
        "limits": (0.0, 5.0)
    },
    "S05": {
        "name": "Optical",
        "type": "Optical",
        "unit": "%",
        "limits": (0.0, 100.0)
    }
}

# Simulation Parameters
SIM_CONFIG = {
    "update_rate": 0.5,         # Seconds
    "fault_prob": 0.005,         # 5% chance of "Faulty Sensor"
    "spike_prob": 0.001,          # 10% chance of sudden limit exceed
    "drift_amount": 0.05,       # Max change per step relative to range (5%)
    "fault_duration": 20.0,     # Duration in seconds for a sensor to remain faulty
}

# Network Configuration
HOST = "127.0.0.1"
PORT = 65432
