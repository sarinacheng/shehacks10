import queue
import threading

class EventLoop:
    def __init__(self, mouse_controller, screenshot_preview_callback=None):
        self.q = queue.Queue()
        self.mouse = mouse_controller
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self.screenshot_preview_callback = screenshot_preview_callback

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self.q.put(None)

    def emit(self, event):
        self.q.put(event)

    def _run(self):
        while not self._stop.is_set():
            ev = self.q.get()
            if ev is None:
                break
            self._process(ev)

    def _process(self, event):
        if event[0] == "MOVE":
            _, x, y = event
            self.mouse.move_to(x, y)
        elif event == "CLICK":
            self.mouse.click_left()
        elif event == "PINCH_START":
            self.mouse.left_down()
        elif event == "PINCH_END":
            self.mouse.left_up()
        elif event[0] == "SCROLL":
            _, dy = event
            self.mouse.scroll(0, dy)
        elif event == "SCREENSHOT":
            self.mouse.screenshot()
        elif event == "CONTROL_RIGHT":
            self.mouse.control_right()
        elif event == "CONTROL_LEFT":
            self.mouse.control_left()
        # COPY/PASTE now handled inside CopyPasteGestureHandler via pyautogui




