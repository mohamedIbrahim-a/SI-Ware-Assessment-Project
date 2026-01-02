import socket
import json
import time
import logging
import threading
from PyQt6.QtCore import QThread, pyqtSignal
from core.sensor_config import HOST, PORT

class CommThread(QThread):
    data_received = pyqtSignal(dict)
    connection_status = pyqtSignal(bool)

    def __init__(self, host=HOST, port=PORT):
        super().__init__()
        self._stop_event = threading.Event()
        self.host = host
        self.port = port
        self.socket = None
        self.socket_lock = threading.Lock()

    def send_command(self, command, **kwargs):
        """Sends a JSON command to the simulator."""
        if self.socket:
            payload = {"command": command}
            payload.update(kwargs)
            try:
                with self.socket_lock:
                    self.socket.sendall(json.dumps(payload).encode('utf-8'))
            except Exception as e:
                logging.error(f"Failed to send command: {e}")

    def run(self):
        while not self._stop_event.is_set():
            try:
                # Create socket
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                self.connection_status.emit(True)
                
                # Receive Loop
                while not self._stop_event.is_set():
                    try:
                        data = self.socket.recv(4096)
                        if not data:
                            break
                        
                        # Handle multiple JSON objects in one buffer (newline delimited from server)
                        messages = data.decode('utf-8').strip().split('\n')
                        for msg in messages:
                            if not msg: continue
                            try:
                                reading = json.loads(msg)
                                # Check if it's a data packet or a command response
                                if "status" in reading:
                                    # It's a command response (Ack)
                                    # For now, maybe just log it or emit a different signal?
                                    pass 
                                else:
                                    # It's sensor data
                                    self.data_received.emit(reading)
                            except json.JSONDecodeError:
                                pass
                                
                            except socket.timeout:
                                continue 
                            except OSError: 
                                continue

                    except (ConnectionRefusedError, socket.timeout, OSError) as e:
                        logging.debug(f"Connection failed: {e}")
                        self.sleep(2)

            except Exception as e:
                logging.error(f"Thread error: {e}")
                self.sleep(2)
    
    def stop(self):
        self._stop_event.set()
        self.wait()
