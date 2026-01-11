from pynput.mouse import Controller, Button
from pynput.keyboard import Controller as KeyboardController, Key
from PIL import ImageGrab
import os
import datetime
import time

class MouseController:
    def __init__(self):
        self.mouse = Controller()
        self.keyboard = KeyboardController()
        self.screen_w, self.screen_h = self._get_screen_size()
        self._left_down = False  # 👈 IMPORTANT STATE

    def _get_screen_size(self):
        # Move mouse to bottom-right corner to infer size
        self.mouse.position = (99999, 99999)
        return self.mouse.position

    def move_to(self, x, y):
        self.mouse.position = (int(x), int(y))

    # ---------- CLICK / HOLD ----------
    def left_down(self):
        if not self._left_down:
            self.mouse.press(Button.left)
            self._left_down = True

    def left_up(self):
        if self._left_down:
            self.mouse.release(Button.left)
            self._left_down = False

    def click_left(self):
        self.mouse.click(Button.left, 1)

    def screenshot(self):
        """Trigger macOS Command+Shift+3 screenshot shortcut"""
        print("MouseController: Triggering Command+Shift+3 screenshot...")
        try:
            # Press Command+Shift+3 (macOS full screen screenshot)
            # Hold all keys, then release
            self.keyboard.press(Key.cmd)
            self.keyboard.press(Key.shift)
            self.keyboard.press('3')
            time.sleep(0.05)  # Brief delay to ensure keys are pressed
            self.keyboard.release('3')
            self.keyboard.release(Key.shift)
            self.keyboard.release(Key.cmd)
            print("✓ Command+Shift+3 triggered successfully")
            return True
        except Exception as e:
            print(f"✗ Failed to trigger screenshot shortcut: {e}")
            import traceback
            traceback.print_exc()
            return False

    def scroll(self, dx, dy):
        """Scroll the mouse wheel. dy: positive = scroll down, negative = scroll up"""
        self.mouse.scroll(dx, dy)
