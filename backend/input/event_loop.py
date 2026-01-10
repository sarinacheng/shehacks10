import queue
import threading

class EventLoop:
    """
    Thread-safe event dispatcher.
    Tracking thread: event_q.put("PINCH_START")
    Controller thread: reads and acts.
    """
    def __init__(self, mouse_controller):
        self.q = queue.Queue()
        self.mouse = mouse_controller
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self.q.put(None)  # wake thread

    def emit(self, event_name: str):
        self.q.put(event_name)

    def _run(self):
        while not self._stop.is_set():
            ev = self.q.get()
            if ev is None:
                continue

            # Map events → actions
            if ev == "PINCH_START":
                self.mouse.click_left()
