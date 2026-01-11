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
        # event: "PINCH_START", "PINCH_END", or ("MOVE", x, y)
        self.q.put(event)

    def _run(self):
        while not self._stop.is_set():
            ev = self.q.get()
            if ev is None:
                continue

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
        elif event == "SCREENSHOT":
                self.mouse.screenshot()
