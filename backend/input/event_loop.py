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
        # event: "CLICK", "PINCH_START", "PINCH_END", "SCREENSHOT", ("MOVE", x, y), or ("SCROLL", dy)
        self.q.put(event)

    def _run(self):
        while not self._stop.is_set():
            ev = self.q.get()
            if ev is None:
                continue

            self._process(ev)

    def _process(self, event):
        """Process events - supports click, hold/release, scroll, and screenshot"""
        if isinstance(event, tuple) and event[0] == "MOVE":
            _, x, y = event
            self.mouse.move_to(x, y)
        elif event == "CLICK":
            # Short pinch = click
            self.mouse.click_left()
        elif event == "PINCH_START":
            # Long pinch = hold (press) for drag functionality
            self.mouse.left_down()
        elif event == "PINCH_END":
            # Release on pinch end
            self.mouse.left_up()
        elif event == "SCREENSHOT":
            print("EventLoop: Received SCREENSHOT event - triggering Command+Shift+3")
            # Trigger macOS screenshot shortcut
            success = self.mouse.screenshot()
            if success:
                print("✓ Screenshot shortcut triggered - macOS will handle the screenshot")
            else:
                print("✗ Failed to trigger screenshot shortcut")
        elif isinstance(event, tuple) and event[0] == "SCROLL":
            _, dy = event
            # pynput scroll: positive dy scrolls down, negative scrolls up
            print(f"Executing scroll: {dy}")  # Debug output
            self.mouse.scroll(0, dy)
