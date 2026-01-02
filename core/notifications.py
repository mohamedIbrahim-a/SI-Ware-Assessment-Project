import time
import logging
import smtplib
from PyQt6.QtWidgets import QSystemTrayIcon, QStyle, QApplication
from PyQt6.QtGui import QIcon
from email.mime.text import MIMEText
from twilio.rest import Client

class NotificationManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.tray_icon = None
        self.last_alert_time = {} # {sensor_id: timestamp}
        self.cooldown = 10.0 # Seconds between alerts for same sensor (Anti-Spam)
        self.email_config = {
            "enabled": False,
            "sender": "your-email@gmail.com",
            "password": "your-app-password-here",
            "recipients": ["recipient@example.com"],
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587
        }
        self.sms_config = {
            "enabled": False,
            "sid": "your-twilio-sid",
            "token": "your-twilio-token",
            "from": "+1234567890",
            "to": "+0987654321"
        }
        
        self._setup_tray()

    def _setup_tray(self):
        # Setup System Tray Icon for Desktop Notifications
        if self.parent:
            self.tray_icon = QSystemTrayIcon(self.parent)
            # Use the window icon if available, or a fallback
            icon = self.parent.windowIcon()
            if icon.isNull():
                icon = self.parent.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            self.tray_icon.setIcon(icon)
            self.tray_icon.setVisible(True)

    def send_alert(self, sensor_id, sensor_name, message, level="WARNING"):
        """
        Triggers notifications across all channels if cooldown passed.
        level: "FAULT" or "LIMIT"
        """
        now = time.time()
        last = self.last_alert_time.get(sensor_id, 0)
        
        # Rate Limiting
        if (now - last) < self.cooldown:
            return 
            
        self.last_alert_time[sensor_id] = now
        timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
        
        # Professional Message Format
        subject = f"Smart Factory Alert: {level}"
        
        full_msg = (
            f"SMART FACTORY ALERT SYSTEM\n"
            f"--------------------------------------------------\n"
            f"Event Type: {level}\n"
            f"Sensor:     {sensor_name}\n"
            f"ID:         {sensor_id}\n"
            f"Time:       {timestamp_str}\n\n"
            f"Message:\n"
            f"{message}\n"
            f"--------------------------------------------------\n"
            f"Please take immediate action."
        )
        
        # Short format for SMS/Desktop Title
        short_msg = f"[{level}] {sensor_name}: {message}"
        
        # 1. Desktop Notification (Title + Short Msg)
        self._send_desktop(subject, short_msg)
        
        # 2. Email (Full Professional Body)
        self._send_email(subject, full_msg)
        
        # 3. SMS (Short Msg)
        self._send_sms(short_msg)
        
    def _send_desktop(self, title, message):
        if self.tray_icon:
            # Map level to standard icon type
            icon_type = QSystemTrayIcon.MessageIcon.Warning
            if "FAULT" in title:
                icon_type = QSystemTrayIcon.MessageIcon.Critical
            
            self.tray_icon.showMessage(title, message, icon_type, 5000)

    def _send_email(self, subject, body):
        if not self.email_config["enabled"]:
            print(f"[MOCK EMAIL] To: {self.email_config['recipients']} | Sub: {subject} | Body: {body}")
            return

        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.email_config["sender"]
            msg['To'] = ", ".join(self.email_config["recipients"])

            with smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"]) as server:
                server.starttls()
                server.login(self.email_config["sender"], self.email_config["password"])
                server.send_message(msg)
                print("Email Sent Successfully")
        except Exception as e:
            print(f"Email Failed: {e}")

    def _send_sms(self, body):
        if not self.sms_config["enabled"]:
             print(f"[MOCK SMS] To: {self.sms_config['to']} | Msg: {body}")
             return
             
        try:
            client = Client(self.sms_config['sid'], self.sms_config['token'])
            message = client.messages.create(
                body=body,
                from_=self.sms_config['from'],
                to=self.sms_config['to']
            )
            print(f"SMS Sent Successfully. SID: {message.sid}")
        except Exception as e:
            print(f"SMS Failed: {e}")
