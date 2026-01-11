import queue
import threading

class EventLoop:
    def __init__(self, mouse_controller):
        self.q = queue.Queue()
        self.mouse = mouse_controller
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self.q.put(None)

    def emit(self, event):
        # event can be a string ("PINCH_START") OR a tuple ("MOVE", x, y)
        self.q.put(event)

    def _run(self):
        while not self._stop.is_set():
            ev = self.q.get()
            if ev is None:
                continue

            if ev == "PINCH_START":
                self.mouse.click_left()
            elif isinstance(ev, tuple) and ev[0] == "MOVE":
                _, x, y = ev
                self.mouse.move_to(x, y)
            elif ev == "SCREENSHOT":
                self.mouse.screenshot()
