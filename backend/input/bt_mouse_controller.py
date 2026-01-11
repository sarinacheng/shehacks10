
import time
import struct
import threading
import logging

# Key Mappings for Modifier Keys
KEY_MOD_LCTRL  = 0x01
KEY_MOD_LSHIFT = 0x02
KEY_MOD_LALT   = 0x04
KEY_MOD_LMETA  = 0x08  # Windows/Command
KEY_MOD_RCTRL  = 0x10
KEY_MOD_RSHIFT = 0x20
KEY_MOD_RALT   = 0x40
KEY_MOD_RMETA  = 0x80

# Scan Codes (USB HID usage table)
# https://usb.org/sites/default/files/hut1_12v2.pdf (Page 53)
SCANCODE_A = 0x04
SCANCODE_C = 0x06
SCANCODE_V = 0x19
SCANCODE_3 = 0x20
SCANCODE_4 = 0x21
SCANCODE_RIGHT = 0x4F
SCANCODE_LEFT = 0x50
SCANCODE_DOWN = 0x51
SCANCODE_UP = 0x52

class BtMouseController:
    def __init__(self, bluetooth_service):
        self.bt_svc = bluetooth_service
        self.ccontrol = None
        self.cinterrupt = None
        self.connected = False
        
        # State for relative movement calculation
        self._last_x = 0
        self._last_y = 0
        self._initialized = False
        
        # Button state
        self._buttons = 0  # Bitmask: 1=Left, 2=Right, 4=Middle

        # Start connection thread
        self.thread = threading.Thread(target=self._connection_loop, daemon=True)
        self.thread.start()

    def _connection_loop(self):
        while True:
            if not self.connected:
                print("[BT] Waiting for connection...")
                # This blocks until a connection is accepted
                ctrl, intr = self.bt_svc.accept_connection()
                if ctrl and intr:
                    self.ccontrol = ctrl
                    self.cinterrupt = intr
                    self.connected = True
                    print("[BT] Connected to Host!")
                else:
                    time.sleep(1)
            else:
                time.sleep(1)

    def _send_mouse(self, buttons, dx, dy, wheel):
        if not self.connected:
            return

        # Clamp values to signed 8-bit (-127 to 127)
        dx = max(-127, min(127, int(dx)))
        dy = max(-127, min(127, int(dy)))
        wheel = max(-127, min(127, int(wheel)))

        # Report ID 1 = Mouse
        # header 0xA1 (DATA | INPUT)
        # Structure: [0xA1, ReportID, Buttons, X, Y, Wheel]
        data = struct.pack('BBbbbb', 0xA1, 0x01, buttons, dx, dy, wheel)
        
        try:
            self.cinterrupt.send(data)
        except Exception as e:
            print(f"[BT] Send Error: {e}")
            self.connected = False
            self.ccontrol.close()
            self.cinterrupt.close()

    def _send_keyboard(self, modifiers, key_code):
        if not self.connected:
            return

        # Report ID 2 = Keyboard
        # Structure: [0xA1, ReportID, Modifier, Reserved, Key1, ...]
        # We only send 1 key press for simplicity in this project
        data = struct.pack('BBBBBBBBBB', 0xA1, 0x02, modifiers, 0x00, key_code, 0, 0, 0, 0, 0)
        
        try:
            self.cinterrupt.send(data)
        except Exception as e:
            print(f"[BT] Send Error: {e}")
            self.connected = False

    def _release_keyboard(self):
        self._send_keyboard(0, 0)

    # --- Mouse interface matching original MouseController ---

    def move_to(self, x, y):
        # We need to convert absolute (x,y) to relative (dx,dy)
        if not self._initialized:
            self._last_x = x
            self._last_y = y
            self._initialized = True
            return

        dx = x - self._last_x
        dy = y - self._last_y
        
        # Scale down if deltas are too large for byte (or clamp)
        # But we also update _last_x to what we ACTUALLY sent to keep sync?
        # A simple approach: send the delta, update last pos.
        
        if dx != 0 or dy != 0:
            self._send_mouse(self._buttons, dx, dy, 0)
        
        self._last_x = x
        self._last_y = y

    def left_down(self):
        self._buttons |= 0x01
        self._send_mouse(self._buttons, 0, 0, 0)

    def left_up(self):
        self._buttons &= ~0x01
        self._send_mouse(self._buttons, 0, 0, 0)

    def click_left(self):
        self.left_down()
        time.sleep(0.05)
        self.left_up()

    def scroll(self, dx, dy):
        # dy is usually vertical scroll
        # In HID, positive is UP.
        # Original MouseController: dy>0 scrolls up.
        # HID Mouse Wheel: positive is Forward/Up. Matches.
        
        # Scale down large scroll values
        scroll_val = int(dy)
        if scroll_val != 0:
            self._send_mouse(self._buttons, 0, 0, scroll_val)

    def screenshot(self):
        # CMD + SHIFT + 3
        # Modifiers: CMD (GUI) + SHIFT
        mods = KEY_MOD_LMETA | KEY_MOD_LSHIFT
        self._send_keyboard(mods, SCANCODE_3)
        time.sleep(0.1)
        self._release_keyboard()

    def copy(self):
        # CMD + C
        mods = KEY_MOD_LMETA
        self._send_keyboard(mods, SCANCODE_C)
        time.sleep(0.1)
        self._release_keyboard()

    def paste(self):
        # CMD + V
        mods = KEY_MOD_LMETA
        self._send_keyboard(mods, SCANCODE_V)
        time.sleep(0.1)
        self._release_keyboard()
    
    def control_right(self):
        # CTRL + RIGHT ARROW
        mods = KEY_MOD_LCTRL
        self._send_keyboard(mods, SCANCODE_RIGHT)
        time.sleep(0.1)
        self._release_keyboard()
    
    def control_left(self):
        # CTRL + LEFT ARROW
        mods = KEY_MOD_LCTRL
        self._send_keyboard(mods, SCANCODE_LEFT)
        time.sleep(0.1)
        self._release_keyboard()
    
    def swipe_left(self):
        # LEFT ARROW
        self._send_keyboard(0, SCANCODE_LEFT)
        time.sleep(0.1)
        self._release_keyboard()
    
    def swipe_right(self):
        # RIGHT ARROW
        self._send_keyboard(0, SCANCODE_RIGHT)
        time.sleep(0.1)
        self._release_keyboard()
    
    def swipe_up(self):
        # UP ARROW
        self._send_keyboard(0, SCANCODE_UP)
        time.sleep(0.1)
        self._release_keyboard()
    
    def swipe_down(self):
        # DOWN ARROW
        self._send_keyboard(0, SCANCODE_DOWN)
        time.sleep(0.1)
        self._release_keyboard()
