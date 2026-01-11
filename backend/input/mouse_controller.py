from pynput.mouse import Controller, Button
from PIL import ImageGrab
import os
import datetime

class MouseController:
    def __init__(self):
        self.mouse = Controller()
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
        # Create screenshots directory if it doesn't exist
        save_dir = os.path.expanduser("~/Desktop/Screenshots") # Or current dir
        if not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir)
            except OSError:
                save_dir = "." # Fallback to current directory
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(save_dir, f"screenshot_{timestamp}.png")
        
        try:
            im = ImageGrab.grab()
            im.save(filename)
            print(f"Screenshot saved to {filename}")
        except Exception as e:
            print(f"Failed to take screenshot: {e}")

    # def move_to(self, x, y):
    #     self.mouse.position = (x, y)

    def press(self):
        self.mouse.press(Button.left)

    def release(self):
        self.mouse.release(Button.left)
