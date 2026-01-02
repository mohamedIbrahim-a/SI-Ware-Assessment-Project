from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QTextEdit,
                             QPushButton, QGridLayout, QGroupBox, QInputDialog, QMessageBox, QLineEdit)
from PyQt6.QtCore import pyqtSlot, Qt, QTimer, QSize
from PyQt6.QtGui import QColor, QFont, QIcon
import pyqtgraph as pg
import time
from collections import deque
from core.sensor_config import SENSOR_CONFIG
from core.notifications import NotificationManager

class Dashboard(QMainWindow):
    def __init__(self, comm_thread):
        super().__init__()
        self.comm_thread = comm_thread
        self.setWindowTitle("ProLine Sensor Dashboard")
        self.resize(1200, 800)

        # Data storage for plots (last 20 seconds @ 2Hz ~ 40-50 points)
        self.history_len = 100 
        # History keyed by Sensor ID
        self.data_history = {sid: deque(maxlen=self.history_len) for sid in SENSOR_CONFIG}
        self.time_history = {sid: deque(maxlen=self.history_len) for sid in SENSOR_CONFIG}
        self.start_time = time.time()
        
        # Track last alarm message to prevent flooding (Deduplication)
        self.alarm_states = {}
        
        # Notification System
        self.notifications = NotificationManager(self)

        self.setup_ui()
        self.comm_thread.data_received.connect(self.update_data)
        self.comm_thread.connection_status.connect(self.update_status)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Header / Status
        self.status_label = QLabel("DISCONNECTED")
        self.status_label.setStyleSheet("color: red; font-weight: bold; font-size: 16px;")
        main_layout.addWidget(self.status_label)

        # Tabs
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # Dark Theme Palette
        # Professional 'Smart Factory' Dark Theme (Catppuccin Mocha-inspired)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            QWidget {
                color: #cdd6f4;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            QLabel {
                color: #cdd6f4;
            }
            QGroupBox {
                border: 2px solid #313244;
                border-radius: 8px;
                margin-top: 1.5em;
                background-color: #181825;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background-color: #1e1e2e; /* Matches Window BG to look floating */
                color: #89b4fa;
            }
            QTableWidget {
                background-color: #181825;
                alternate-background-color: #1e1e2e;
                color: #cdd6f4;
                gridline-color: #313244;
                border: none;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #89b4fa;
                padding: 8px;
                border: 1px solid #1e1e2e;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            QTextEdit {
                background-color: #11111b;
                color: #a6e3a1; /* Greenish for logs */
                border: 1px solid #45475a;
                border-radius: 6px;
                font-family: 'Consolas', monospace;
            }
            /* Tabs */
            QTabWidget::pane {
                border: 1px solid #45475a;
                border-radius: 8px;
                top: -1px; 
                background-color: #1e1e2e;
            }
            QTabBar::tab {
                background: #313244;
                color: #a6adc8;
                padding: 10px 25px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background: #89b4fa;
                color: #11111b; /* Dark text on bright tab */
            }
            /* Buttons */
            QPushButton {
                background-color: #45475a;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
            QPushButton:pressed {
                background-color: #313244;
            }
        """)

        # -- Dashboard Tab --
        dash_tab = QWidget()
        dash_layout = QHBoxLayout(dash_tab)
        dash_layout.setSpacing(20)
        
        # Left Panel: Table & Logs
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # CARD 1: Sensor Table
        table_group = QGroupBox("SENSOR READINGS")
        table_layout = QVBoxLayout(table_group)
        
        self.sensor_table = QTableWidget()
        # [ID, Name, Value, Unit, Status, Time]
        self.sensor_table.setColumnCount(6)
        self.sensor_table.setHorizontalHeaderLabels(["ID", "Name", "Value", "Unit", "Status", "Time"])
        self.sensor_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sensor_table.setRowCount(len(SENSOR_CONFIG))
        self.sensor_table.verticalHeader().setVisible(False)
        self.sensor_table.setAlternatingRowColors(True)
        # self.sensor_table.setStyleSheet("alternate-background-color: #444444;") # Handled by global css
        
        # Initialize Table
        # Store row indices for each sensor ID
        self.sensor_rows = {}
        for i, (sid, info) in enumerate(SENSOR_CONFIG.items()):
            self.sensor_rows[sid] = i
            self.sensor_table.setItem(i, 0, QTableWidgetItem(sid))
            self.sensor_table.setItem(i, 1, QTableWidgetItem(info['name']))
            self.sensor_table.setItem(i, 2, QTableWidgetItem("-"))
            self.sensor_table.setItem(i, 3, QTableWidgetItem(info['unit']))
            self.sensor_table.setItem(i, 4, QTableWidgetItem("-"))
            self.sensor_table.setItem(i, 5, QTableWidgetItem("-"))
        
        table_layout.addWidget(self.sensor_table)
        left_layout.addWidget(table_group)
        
        # Split Logs Area
        logs_container = QWidget()
        logs_layout = QHBoxLayout(logs_container)
        logs_layout.setContentsMargins(0, 10, 0, 0)
        logs_layout.setSpacing(10)
        
        # Fault Log (Left)
        fault_panel = QWidget()
        fault_layout = QVBoxLayout(fault_panel)
        fault_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_fault = QLabel("⚠️ SENSOR FAULTS")
        lbl_fault.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_fault.setStyleSheet("color: #bd93f9;") # Purple
        self.fault_log = QTextEdit()
        self.fault_log.setReadOnly(True)
        self.fault_log.setStyleSheet("border: 1px solid #bd93f9;")
        
        fault_layout.addWidget(lbl_fault)
        fault_layout.addWidget(self.fault_log)
        
        # Limit Log (Right)
        limit_panel = QWidget()
        limit_layout = QVBoxLayout(limit_panel)
        limit_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_limit = QLabel("⚡ LIMIT ALERTS")
        lbl_limit.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_limit.setStyleSheet("color: #ff5555;") # Red
        self.limit_log = QTextEdit()
        self.limit_log.setReadOnly(True)
        self.limit_log.setStyleSheet("border: 1px solid #ff5555;")
        
        limit_layout.addWidget(lbl_limit)
        limit_layout.addWidget(self.limit_log)
        
        logs_layout.addWidget(fault_panel)
        logs_layout.addWidget(limit_panel)
        
        left_layout.addWidget(logs_container)

        dash_layout.addWidget(left_panel, stretch=2)

        # Right Panel: Plots
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        
        # CARD 2: Live Trends
        trends_group = QGroupBox("LIVE TRENDS (Last 20s)")
        trends_layout = QVBoxLayout(trends_group)
        self.plots = {}
        
        # msg_label = QLabel("LIVE TRENDS (Last 20s)")
        # msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # msg_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        # plot_layout.addWidget(msg_label)

        # Set Global pyqtgraph config
        pg.setConfigOption('background', '#181825')
        pg.setConfigOption('foreground', '#cdd6f4')
        pg.setConfigOptions(antialias=True)

        for sid, info in SENSOR_CONFIG.items():
            title = f"{info['name']} ({sid})"
            p = pg.PlotWidget(title=title)
            p.showGrid(x=True, y=True, alpha=0.3)
            p.setLabel('left', info['unit'])
            p.getAxis('left').setPen('#888')
            p.getAxis('bottom').setPen('#888')
            
            # Distinct color per plot could be nice, currently using yellow
            self.plots[sid] = p.plot(pen=pg.mkPen('#89b4fa', width=2)) 
            trends_layout.addWidget(p) # Add to GroupBox layout
        
        plot_layout.addWidget(trends_group) # Add GroupBox to container
        
        dash_layout.addWidget(plot_container, stretch=3)
        tabs.addTab(dash_tab, "Dashboard")
        
        # -- Maintenance Tab --
        maint_tab = QWidget()
        self.setup_maint_ui(maint_tab)
        tabs.addTab(maint_tab, "Maintenance")

    def setup_maint_ui(self, tab_widget):
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 1. Access Control Section
        access_group = QGroupBox("Access Control")
        access_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #555; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        access_layout = QHBoxLayout(access_group)
        
        self.lbl_auth_status = QLabel("🔒 LOCKED")
        self.lbl_auth_status.setStyleSheet("color: #ff5555; font-weight: bold; font-size: 14px;")
        
        self.btn_unlock = QPushButton("Unlock Console")
        self.btn_unlock.setFixedSize(150, 40)
        self.btn_unlock.setStyleSheet("""
            QPushButton { background-color: #6272a4; color: white; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #7484b0; }
            QPushButton:pressed { background-color: #4d5b85; }
        """)
        self.btn_unlock.clicked.connect(self.unlock_console)
        
        access_layout.addWidget(self.lbl_auth_status)
        access_layout.addStretch()
        access_layout.addWidget(self.btn_unlock)
        
        layout.addWidget(access_group)

        # 2. Remote Commands Section
        cmd_group = QGroupBox("Remote Simulator Commands")
        cmd_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #555; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        cmd_layout = QGridLayout(cmd_group)
        cmd_layout.setSpacing(15)
        
        # Define Buttons
        self.btn_reset = QPushButton("RESET SIMULATION")
        self.btn_reset.setStyleSheet("""
            QPushButton { background-color: #ffb86c; color: black; font-weight: bold; padding: 10px; border-radius: 4px; }
            QPushButton:hover { background-color: #ffdca3; }
            QPushButton:pressed { background-color: #dba56b; }
        """)
        self.btn_reset.clicked.connect(lambda: self.send_remote_command("RESET"))
        
        self.btn_clear_faults = QPushButton("CLEAR FAULTS")
        self.btn_clear_faults.setStyleSheet("""
            QPushButton { background-color: #bd93f9; color: black; font-weight: bold; padding: 10px; border-radius: 4px; }
            QPushButton:hover { background-color: #d1b3ff; }
            QPushButton:pressed { background-color: #9a76d6; }
        """)
        self.btn_clear_faults.clicked.connect(lambda: self.send_remote_command("CLEAR_FAULTS"))
        
        self.btn_toggle = QPushButton("PAUSE / RESUME")
        self.btn_toggle.setStyleSheet("""
            QPushButton { background-color: #8be9fd; color: black; font-weight: bold; padding: 10px; border-radius: 4px; }
            QPushButton:hover { background-color: #b3f2ff; }
            QPushButton:pressed { background-color: #69bfd1; }
        """)
        self.btn_toggle.clicked.connect(lambda: self.send_remote_command("TOGGLE_SIM"))

        self.btn_clear_logs = QPushButton("Clear Local Logs")
        self.btn_clear_logs.setStyleSheet("""
            QPushButton { background-color: #45475a; color: white; padding: 10px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #585b70; }
            QPushButton:pressed { background-color: #313244; }
        """)
        self.btn_clear_logs.clicked.connect(self.clear_local_logs)

        # Grid Placement
        cmd_layout.addWidget(self.btn_reset, 0, 0)
        cmd_layout.addWidget(self.btn_clear_faults, 0, 1)
        cmd_layout.addWidget(self.btn_toggle, 1, 0)
        cmd_layout.addWidget(self.btn_clear_logs, 1, 1)

        layout.addWidget(cmd_group)

        # 3. Live System Log
        log_group = QGroupBox("Live System Log (Debug)")
        log_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #555; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        log_layout = QVBoxLayout(log_group)
        
        self.system_log = QTextEdit()
        self.system_log.setReadOnly(True)
        self.system_log.setStyleSheet("background-color: #1e1e1e; color: #50fa7b; font-family: Consolas; border: none;")
        
        log_layout.addWidget(self.system_log)
        layout.addWidget(log_group, stretch=1)

        # Initially Disable Controls
        self.set_controls_enabled(False)
        self.is_unlocked = False

    def set_controls_enabled(self, enabled):
        self.btn_reset.setEnabled(enabled)
        self.btn_clear_faults.setEnabled(enabled)
        self.btn_toggle.setEnabled(enabled)
        self.btn_clear_logs.setEnabled(enabled)
        if not enabled:
            self.btn_reset.setToolTip("Unlock console to use")
        else:
            self.btn_reset.setToolTip("")

    def unlock_console(self):
        if self.is_unlocked:
            # Lock it
            self.is_unlocked = False
            self.lbl_auth_status.setText("🔒 LOCKED")
            self.lbl_auth_status.setStyleSheet("color: #ff5555; font-weight: bold; font-size: 14px;")
            self.btn_unlock.setText("Unlock Console")
            self.set_controls_enabled(False)
            self.system_log.append("Console Locked.")
        else:
            # Unlock it - Custom Styled Dialog
            dialog = QInputDialog(self)
            dialog.setWindowTitle("Maintenance Access")
            dialog.setLabelText("Enter Admin Password:")
            dialog.setTextEchoMode(QLineEdit.EchoMode.Password)
            dialog.setInputMode(QInputDialog.InputMode.TextInput)
            
            # Apply Dark Theme Query (Matches Global Theme)
            dialog.setStyleSheet("""
                QInputDialog { background-color: #1e1e2e; color: #cdd6f4; }
                QLabel { color: #cdd6f4; font-family: 'Segoe UI'; font-size: 14px; font-weight: bold; }
                QLineEdit { background-color: #313244; color: #cdd6f4; border: 1px solid #89b4fa; padding: 6px; border-radius: 4px; }
                QPushButton { background-color: #45475a; color: white; padding: 6px 15px; border: none; border-radius: 4px; font-weight: bold; }
                QPushButton:hover { background-color: #585b70; }
            """)
            
            ok = dialog.exec()
            password = dialog.textValue()
            
            if ok and password == "admin123":
                self.is_unlocked = True
                self.lbl_auth_status.setText("🔓 UNLOCKED (Admin)")
                self.lbl_auth_status.setStyleSheet("color: #50fa7b; font-weight: bold; font-size: 14px;")
                self.btn_unlock.setText("Lock Console")
                self.set_controls_enabled(True)
                self.system_log.append("Access Granted: Console Unlocked.")
            elif ok:
                QMessageBox.warning(self, "Access Denied", "Incorrect Password!")
                self.system_log.append("Access Denied: Incorrect Password.")

    def send_remote_command(self, cmd):
        self.comm_thread.send_command(cmd)
        self.system_log.append(f"Command Sent: {cmd}")
    
    def clear_local_logs(self):
        # Clear the split logs
        if hasattr(self, 'fault_log'):
            self.fault_log.clear()
        if hasattr(self, 'limit_log'):
            self.limit_log.clear()
        self.alarm_states.clear()
        self.system_log.append("Local Logs Cleared.")

    @pyqtSlot(bool)
    def update_status(self, connected):
        if connected:
            self.status_label.setText("CONNECTED (System OK)")
            self.status_label.setStyleSheet("color: green; font-weight: bold; font-size: 16px;")
        else:
            self.status_label.setText("DISCONNECTED - Waiting for Simulator...")
            self.status_label.setStyleSheet("color: red; font-weight: bold; font-size: 16px;")

    @pyqtSlot(dict)
    def update_data(self, data):
        current_time = time.time()
        time_rel = current_time - self.start_time

        # Data is now a dict keyed by Sensor ID
        for sid, reading in data.items():
            if sid in SENSOR_CONFIG:
                val = reading['value']
                status = reading['status']
                timestamp = reading['timestamp']
                
                # Get Config for limits/name
                info = SENSOR_CONFIG[sid]
                name = info['name']

                # Update Table
                row = self.sensor_rows[sid]
                self.sensor_table.item(row, 2).setText(str(val))
                self.sensor_table.item(row, 4).setText(status)
                self.sensor_table.item(row, 5).setText(time.strftime("%H:%M:%S", time.localtime(timestamp)))

                # Check Limits & Color
                low, high = info['limits']
                bg_color = None
                text_color = QColor("#ffffff") # Default white text
                
                alarm_msg = None
                alarm_type = "NONE" # NONE, FAULT, LIMIT

                if status != "OK":
                    bg_color = QColor("#bd93f9") # Dracula Purple for Fault
                    text_color = QColor("#000000") 
                    alarm_msg = f"FAULT: {status}"
                    alarm_type = "FAULT"
                elif val < low:
                    bg_color = QColor("#ff5555") # Red for ALL Limits
                    text_color = QColor("#000000") # Black text
                    alarm_msg = f"LOW LIMIT: {val} < {low}"
                    alarm_type = "LIMIT"
                elif val > high:
                    bg_color = QColor("#ff5555") # Red for ALL Limits
                    text_color = QColor("#000000") # Black text
                    alarm_msg = f"HIGH LIMIT: {val} > {high}"
                    alarm_type = "LIMIT"
                else:
                    # Default: Transparent to let alternating row colors show
                    bg_color = QColor(0, 0, 0, 0)

                # Colorize row
                for col in range(6):
                    item = self.sensor_table.item(row, col)
                    # Only override background if it's an alarm
                    if alarm_msg:
                        item.setBackground(bg_color)
                        item.setForeground(text_color)
                        item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                    else:
                        # Restore default look
                        item.setBackground(bg_color) # Transparent
                        item.setForeground(QColor("#cdd6f4")) # Theme Text Color
                        item.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))

                # Log Alarm if needed
                if alarm_msg:
                    if alarm_type == "FAULT":
                        alarm_msg += " (under fixation)"

                    # Check for duplicates (Deduplication)
                    last_msg = self.alarm_states.get(sid)
                    
                    if last_msg != alarm_msg:
                        t_str = time.strftime("%H:%M:%S")
                        log_entry = f"[{t_str}] {name} ({sid}) - {alarm_msg}"
                        
                        if alarm_type == "FAULT":
                            self.fault_log.append(log_entry)
                            # Trigger Notification
                            self.notifications.send_alert(sid, name, f"Sensor Fault detected: {status}", "FAULT")
                        elif alarm_type == "LIMIT":
                            self.limit_log.append(log_entry)
                            # Trigger Notification
                            self.notifications.send_alert(sid, name, f"Limit Exceeded: {val}", "LIMIT")
                            
                        self.alarm_states[sid] = alarm_msg
                else:
                    # Reset alarm state when back to normal
                    if sid in self.alarm_states:
                        del self.alarm_states[sid]

                # Update Plots
                self.data_history[sid].append(val)
                self.time_history[sid].append(time_rel)
                self.plots[sid].setData(list(self.time_history[sid]), list(self.data_history[sid]))

    def closeEvent(self, event):
        self.comm_thread.stop()
        event.accept()
