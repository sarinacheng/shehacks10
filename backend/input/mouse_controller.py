from pynput.mouse import Controller, Button

class MouseController:
    def __init__(self):
        self.mouse = Controller()

    def click_left(self):
        self.mouse.click(Button.left, 1)
