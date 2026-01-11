from pynput.mouse import Controller, Button
from pynput.keyboard import Controller as KeyboardController, Key
import pyautogui
import subprocess
import platform

class MouseController:
    def __init__(self):
        self.mouse = Controller()
        self.keyboard = KeyboardController()

    def _get_screen_size(self):
        return pyautogui.size()

    def move_to(self, x, y):
        self.mouse.position = (x, y)

    def left_down(self):
        self.mouse.press(Button.left)

    def left_up(self):
        self.mouse.release(Button.left)

    def click_left(self):
        self.mouse.click(Button.left, 1)

    def screenshot(self):
        # Trigger Command + Shift + 3 screenshot on macOS
        # Use pynput for more reliable key presses
        from pynput.keyboard import Key
        import time
        
        # Press all keys together
        self.keyboard.press(Key.cmd_l)  # Command key
        self.keyboard.press(Key.shift)   # Shift key
        self.keyboard.press('3')         # 3 key
        # Small delay to ensure all keys are pressed
        time.sleep(0.05)
        # Release in reverse order
        self.keyboard.release('3')
        self.keyboard.release(Key.shift)
        self.keyboard.release(Key.cmd_l)

    def scroll(self, dx, dy):
        # dx ignored; dy >0 scrolls up in pynput
        self.mouse.scroll(dx, dy)

    def copy(self):
        pyautogui.hotkey("command", "c")

    def paste(self):
        pyautogui.hotkey("command", "v")
    
    def control_right(self):
        pyautogui.hotkey("ctrl", "right")
    
    def control_left(self):
        pyautogui.hotkey("ctrl", "left")
    
    def swipe_left(self):
        from pynput.keyboard import Key
        self.keyboard.press(Key.left)
        self.keyboard.release(Key.left)
    
    def swipe_right(self):
        from pynput.keyboard import Key
        self.keyboard.press(Key.right)
        self.keyboard.release(Key.right)
    
    def swipe_up(self):
        from pynput.keyboard import Key
        self.keyboard.press(Key.up)
        self.keyboard.release(Key.up)
    
    def swipe_down(self):
        from pynput.keyboard import Key
        self.keyboard.press(Key.down)
        self.keyboard.release(Key.down)

