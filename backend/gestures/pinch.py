import time
import math

THUMB_TIP = 4
INDEX_TIP = 8

def _dist3(a, b) -> float:
    return math.sqrt(
        (a.x - b.x) ** 2 +
        (a.y - b.y) ** 2 +
        (a.z - b.z) ** 2
    )

class PinchDetector:
    """
    Emits:
      - "CLICK"        → short pinch
      - "PINCH_START"  → long pinch (drag start)
      - "PINCH_END"    → drag end
    """

    def __init__(
        self,
        pinch_threshold=0.030,
        release_threshold=0.040,
        hold_delay_s=0.25
    ):
        self.pinch_threshold = pinch_threshold
        self.release_threshold = release_threshold
        self.hold_delay_s = hold_delay_s

        self._pinch_start_t = None
        self._dragging = False

    def is_active(self):
        """True while drag-select is active"""
        return self._dragging

    def update(self, hand_landmarks):
        events = []
        lms = hand_landmarks.landmark
        d = _dist3(lms[THUMB_TIP], lms[INDEX_TIP])
        now = time.time()

        # ----- PINCH -----
        if d < self.pinch_threshold:
            if self._pinch_start_t is None:
                self._pinch_start_t = now

            if (
                not self._dragging
                and (now - self._pinch_start_t) >= self.hold_delay_s
            ):
                self._dragging = True
                events.append("PINCH_START")

        # ----- RELEASE -----
        elif d > self.release_threshold:
            if self._pinch_start_t is not None:
                if self._dragging:
                    events.append("PINCH_END")
                elif (now - self._pinch_start_t) > 0.05:
                    events.append("CLICK")

            self._pinch_start_t = None
            self._dragging = False

        return events
