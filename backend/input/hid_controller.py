
import socket
import struct
import time
import threading

class HIDController:
    def __init__(self, width=1920, height=1080):
        self.sock_control = None
        self.sock_interrupt = None
        self.client_control = None
        self.client_interrupt = None
        self.connected = False
        
        # Screen dim for scaling (not really used in relative mode but kept for API compat)
        self.last_x = width // 2
        self.last_y = height // 2

        # Start listener in background
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def _listen(self):
        print("HIDController: Waiting for Bluetooth connection on (L2CAP 17/19)...")
        try:
            # L2CAP Control (Port 17)
            self.sock_control = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_L2CAP)
            self.sock_control.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock_control.bind((socket.BDADDR_ANY, 17))
            self.sock_control.listen(1)

            # L2CAP Interrupt (Port 19)
            self.sock_interrupt = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_L2CAP)
            self.sock_interrupt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock_interrupt.bind((socket.BDADDR_ANY, 19))
            self.sock_interrupt.listen(1)

            # Accept control first
            self.client_control, addr = self.sock_control.accept()
            print(f"HIDController: Control connection from {addr}")

            # Accept interrupt
            self.client_interrupt, addr = self.sock_interrupt.accept()
            print(f"HIDController: Interrupt connection from {addr}")

            self.connected = True
            
        except Exception as e:
            print(f"HIDController Listen Error: {e}")

    def send_report(self, data):
        if not self.connected:
            return
        try:
            # data is a bytes object of the report
            # Standard report header for data: 0xA1 (DATA)
            self.client_interrupt.send(b'\xA1' + data)
        except Exception as e:
            print(f"HID Send Error: {e}")
            self.connected = False

    def move_to(self, x, y):
        dx = int(x) - self.last_x
        dy = int(y) - self.last_y
        
        # Clip to byte capability (-127 to 127)
        dx = max(-127, min(127, dx))
        dy = max(-127, min(127, dy))
        
        self.last_x = int(x)
        self.last_y = int(y)
        
        if dx == 0 and dy == 0:
            return

        # Report ID 0x01 (Mouse) from standard descriptor
        # Format: [ReportID, Buttons, X, Y]
        report = struct.pack('BBbb', 0x01, 0, dx, dy)
        self.send_report(report)

    def click_left(self):
        # Click Down
        report = struct.pack('BBbb', 0x01, 1, 0, 0) # Button 1 (Left) pressed
        self.send_report(report)
        time.sleep(0.05)
        # Release
        report = struct.pack('BBbb', 0x01, 0, 0, 0) # Release
        self.send_report(report)

    def screenshot(self):
        # Keyboard Report ID 0x02 (if we had one, but we used Mouse descriptor above)
        # Implementing keyboard is tricky without a complex descriptor.
        # For now, let's just print that we can't do screenshots easily via raw HID yet
        print("Screenshot not fully implemented in bare-socket HID yet.")
