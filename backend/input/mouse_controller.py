from pynput.mouse import Controller, Button
from pynput.keyboard import Controller as KeyboardController, Key
import pyautogui

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
        pyautogui.hotkey("command", "shift", "3")

    def scroll(self, dx, dy):
        # dx ignored; dy >0 scrolls up in pynput
        self.mouse.scroll(dx, dy)

    def copy(self):
        pyautogui.hotkey("command", "c")

    def paste(self):
        pyautogui.hotkey("command", "v")

