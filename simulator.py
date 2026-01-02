import socket
import json
import time
import random
import threading
import argparse
import select
from core.sensor_config import HOST, PORT, SENSOR_CONFIG, SIM_CONFIG

class SensorSimulator:
    def __init__(self, host=HOST, port=PORT, sensor_config=None, sim_config=None):
        self.host = host
        self.port = port
        self.sensor_config = sensor_config if sensor_config else SENSOR_CONFIG
        self.sim_config = sim_config if sim_config else SIM_CONFIG
        self._stop_event = threading.Event()
        self.paused = False
        
        # Initialize fault states: {sid: start_time_of_fault or None}
        self.fault_states = {sid: None for sid in self.sensor_config}
        
        # Initialize current values to the middle of the range
        self.current_values = {}
        self.reset_simulation()

    def reset_simulation(self):
        """Resets all sensor values to default."""
        for sid, info in self.sensor_config.items():
            low, high = info['limits']
            self.current_values[sid] = (low + high) / 2
        self.fault_states = {sid: None for sid in self.sensor_config}
        print("Simulation Reset")

    def process_command(self, cmd_data):
        """Handles incoming JSON commands."""
        try:
            cmd = cmd_data.get("command")
            print(f"Received Command: {cmd}")
            
            if cmd == "RESET":
                self.reset_simulation()
                return {"status": "OK", "message": "Simulation Reset"}
            elif cmd == "CLEAR_FAULTS":
                self.fault_states = {sid: None for sid in self.sensor_config}
                print("Faults Cleared")
                return {"status": "OK", "message": "Faults Cleared"}
            elif cmd == "TOGGLE_SIM":
                self.paused = not self.paused
                state = "Paused" if self.paused else "Resumed"
                print(f"Simulation {state}")
                return {"status": "OK", "message": f"Simulation {state}", "paused": self.paused}
            else:
                return {"status": "ERROR", "message": "Unknown Command"}
        except Exception as e:
            print(f"Command Error: {e}")
            return {"status": "ERROR", "message": str(e)}

    def generate_data(self):
        """Generates a dictionary of sensor data with trend-based drift."""
        data = {}
        
        # Unpack Simulation Params
        prob_fault = self.sim_config["fault_prob"]
        prob_spike = self.sim_config["spike_prob"]
        drift_factor = self.sim_config["drift_amount"]
        fault_duration = self.sim_config.get("fault_duration", 20.0)
        current_time = time.time()

        for sid, info in self.sensor_config.items():
            low, high = info['limits']
            span = high - low
            
            # 1. Update Trend (Drift)
            drift = (random.random() - 0.5) * 2 * (span * drift_factor)
            new_val = self.current_values[sid] + drift
            new_val = max(low * 0.9, min(high * 1.1, new_val))
            self.current_values[sid] = new_val
            
            final_val = new_val
            status = "OK"

            # 2. Check for Sticky Faults
            if self.fault_states.get(sid) is not None:
                # Sensor is already faulty
                if current_time - self.fault_states[sid] < fault_duration:
                    status = "Faulty Sensor"
                    final_val = 0.0
                else:
                    # Fault duration passed, recover
                    self.fault_states[sid] = None
                    status = "OK"
            else:
                # Sensor is "OK", check if we should trigger a new fault/spike
                rand_check = random.random()
                
                if rand_check < prob_fault:
                    status = "Faulty Sensor"
                    final_val = 0.0
                    self.fault_states[sid] = current_time # Start fault timer
                
                elif rand_check < (prob_fault + prob_spike):
                    # Sudden Spike (Out of limits) - Spikes are transient (one-off)
                    if random.choice([True, False]):
                        final_val = high + (span * 0.2)
                    else:
                        final_val = low - (span * 0.2)
            
            data[sid] = {
                "id": sid,
                "name": info['name'],
                "type": info['type'],
                "unit": info['unit'],
                "value": round(final_val, 2),
                "timestamp": time.time(),
                "status": status
            }
        return data

    def start(self):
        print("Socket created")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            print("Options applied")
            s.bind((self.host, self.port))
            print(f"Bind address: {self.host}:{self.port}")
            s.listen()
            s.settimeout(1.0)
            print("Listening started")

            while not self._stop_event.is_set():
                try:
                    try:
                        conn, addr = s.accept()
                        print("Client accepted")
                    except socket.timeout:
                        continue 

                    with conn:
                        last_update = time.time()
                        update_rate = self.sim_config.get("update_rate", 0.5)
                        
                        while not self._stop_event.is_set():
                            # I/O Multiplexing: Check if socket has data (Command) or if we need to send data (Timer)
                            # Calculate time remaining until next data push
                            now = time.time()
                            time_since_update = now - last_update
                            timeout = max(0, update_rate - time_since_update)
                            
                            # Wait for data or timeout
                            # rlist=[conn] means we wait for incoming data
                            rlist, _, _ = select.select([conn], [], [], timeout)
                            
                            if rlist:
                                # Data received! (Command?)
                                try:
                                    raw_data = conn.recv(1024)
                                    if not raw_data:
                                        print("Client disconnected (EOF)")
                                        break
                                    
                                    # Handle multiple commands if they come in a burst, split by newline
                                    # But simplistic approach first: assume one JSON per packet or clean buffer
                                    # For robustness, let's decode and parse
                                    try:
                                        msg = raw_data.decode('utf-8').strip()
                                        if msg:
                                            cmd_json = json.loads(msg)
                                            response = self.process_command(cmd_json)
                                            # Send Ack
                                            conn.sendall((json.dumps(response) + "\n").encode('utf-8'))
                                    except json.JSONDecodeError:
                                        print(f"Invalid JSON received: {raw_data}")
                                except (ConnectionResetError, BrokenPipeError):
                                    print("Client disconnected (Reset)")
                                    break
                            
                            # Check if it's time to send data
                            if time.time() - last_update >= update_rate:
                                if not self.paused:
                                    sensor_data = self.generate_data()
                                    json_data = json.dumps(sensor_data)
                                    try:
                                        conn.sendall((json_data + "\n").encode('utf-8'))
                                    except (ConnectionResetError, BrokenPipeError):
                                        print("Client disconnected (Pipe)")
                                        break
                                last_update = time.time()
                                
                except Exception as e:
                    if not self._stop_event.is_set():
                         print(f"Server error: {e}")
        print("Socket closed")

    def stop(self):
        """Signals the simulator to stop running."""
        self._stop_event.set()

def generate_dynamic_config(target_count):
    """Generates a larger sensor config if needed."""
    base_config = SENSOR_CONFIG.copy()
    current_count = len(base_config)
    
    if target_count <= current_count:
        # If we want fewer, just slice
        # (Dictionaries are ordered in modern Python, but safer to take first N keys)
        keys = list(base_config.keys())[:target_count]
        return {k: base_config[k] for k in keys}
    else:
        # Add extra sensors
        new_config = base_config.copy()
        for i in range(current_count + 1, target_count + 1):
            sid = f"S{i:02d}"
            new_config[sid] = {
                "name": f"Extra Sensor {i}",
                "type": "Generic",
                "unit": "Units",
                "limits": (0.0, 100.0)
            }
        return new_config

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-Time Sensor Simulator")
    parser.add_argument("-p", "--port", type=int, default=PORT, help="Port to listen on")
    parser.add_argument("-r", "--rate", type=float, help="Update rate in seconds")
    parser.add_argument("-n", "--count", type=int, help="Total number of sensors")
    
    args = parser.parse_args()
    
    # Prepare Configs
    final_sensor_config = SENSOR_CONFIG
    final_sim_config = SIM_CONFIG.copy()
    
    if args.count:
        print(f"Configuring {args.count} sensors...")
        final_sensor_config = generate_dynamic_config(args.count)
    
    if args.rate:
        print(f"Setting update rate to {args.rate}s")
        final_sim_config["update_rate"] = args.rate

    sim = SensorSimulator(port=args.port, sensor_config=final_sensor_config, sim_config=final_sim_config)
    try:
        sim.start()
    except KeyboardInterrupt:
        print("\nStopping Simulator...")
        sim.stop()
