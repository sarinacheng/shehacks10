
import socket
import struct
import time
import threading

# Fallback for systems (like Conda) where socket.AF_BLUETOOTH is missing
USE_PYBLUEZ = not hasattr(socket, 'AF_BLUETOOTH')
if USE_PYBLUEZ:
    try:
        import bluetooth
    except ImportError:
        print("Error: socket.AF_BLUETOOTH missing and 'pybluez' not installed.")
        USE_PYBLUEZ = False # Will crash later, but at least we warned

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
            if USE_PYBLUEZ:
                print("HIDController: Using PyBluez (socket.AF_BLUETOOTH missing)")
                # L2CAP Control (Port 17)
                self.sock_control = bluetooth.BluetoothSocket(bluetooth.L2CAP)
                self.sock_control.setblocking(True)
                self.sock_control.bind(("", 17))
                self.sock_control.listen(1)

                # L2CAP Interrupt (Port 19)
                self.sock_interrupt = bluetooth.BluetoothSocket(bluetooth.L2CAP)
                self.sock_interrupt.setblocking(True)
                self.sock_interrupt.bind(("", 19))
                self.sock_interrupt.listen(1)
            else:
                # Native Python Socket
                self.sock_control = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_L2CAP)
                self.sock_control.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.sock_control.bind((socket.BDADDR_ANY, 17))
                self.sock_control.listen(1)

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
        # Keyboard Report (ID 0x01 is mouse, usually 0x02 is keyboard if defined, 
        # but in simplified boot protocol or composite, it might vary).
        # Standard Boot Keyboard Report: [Modifier, Reserved, Key1, Key2, Key3, Key4, Key5, Key6]
        # Modifiers: LeftGUI (0x08) + LeftShift (0x02) = 0x0A
        # Key: '3' -> Keycode 0x20
        
        # NOTE: Without a full SDP Report Descriptor handshake, the Mac relies on the Class of Device (0x5C0).
        # If it treats us as a Composite device, we usually need Report IDs.
        # Let's try sending a standard Report ID 2 for Keyboard.
        
        print("Triggering Screenshot (Cmd+Shift+3)...")
        
        # Press: Report ID 2, Modifier 0x0A (Cmd+Shift), Reserved 0, Key 0x20 (3)
        # Structure: ID (1 byte) + Modifier (1 byte) + Reserved (1 byte) + Key (1 byte) + padding...
        # Actually standard report is: [Modifier, Reserved, Key1, Key2...]
        # Wrapped in L2CAP DATA frame (0xA1) + ReportID (0x02)
        
        # Cmd(8) + Shift(2) = 10
        # Key '3' = 32 (0x20)
        
        # Press
        # Report ID 2
        payload = struct.pack('BBBB', 0x02, 0x0A, 0x00, 0x20) + b'\x00'*5
        self.send_report(payload)
        
        time.sleep(0.05)
        
        # Release (All zeros)
        payload = struct.pack('BBBB', 0x02, 0x00, 0x00, 0x00) + b'\x00'*5
        self.send_report(payload)
