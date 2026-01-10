from pynput.mouse import Controller, Button

class MouseController:
    def __init__(self):
        self.mouse = Controller()
        self.screen_w, self.screen_h = self._get_screen_size()

    def _get_screen_size(self):
        # Move mouse to bottom-right corner to infer size
        self.mouse.position = (99999, 99999)
        return self.mouse.position

    def click_left(self):
        self.mouse.click(Button.left, 1)

    def move_to(self, x, y):
        self.mouse.position = (x, y)
