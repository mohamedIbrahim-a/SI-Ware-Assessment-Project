import sys
import argparse
import logging
from PyQt6.QtWidgets import QApplication
from gui.dashboard import Dashboard
from core.comm_thread import CommThread
from core.sensor_config import HOST, PORT

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    parser = argparse.ArgumentParser(description="ProLine Sensor Dashboard")
    parser.add_argument("-p", "--port", type=int, default=PORT, help="Port to connect to")
    parser.add_argument("--host", type=str, default=HOST, help="Host to connect to")
    
    args = parser.parse_args()

    app = QApplication(sys.argv)
    
    comm_thread = CommThread(host=args.host, port=args.port)
    window = Dashboard(comm_thread)
    
    window.show()
    comm_thread.start()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
