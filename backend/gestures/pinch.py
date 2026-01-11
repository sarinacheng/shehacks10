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
        pinch_threshold=0.025,
        release_threshold=0.025,
        hold_delay_s=0.25   # 👈 controls click vs select
    ):
        self.pinch_threshold = pinch_threshold
        self.release_threshold = release_threshold
        self.hold_delay_s = hold_delay_s

        self._pinch_start_t = None
        self._dragging = False

    def update(self, hand_landmarks):
        events = []
        lms = hand_landmarks.landmark
        d = _dist3(lms[THUMB_TIP], lms[INDEX_TIP])
        now = time.time()

        # ---------- PINCH DETECTED ----------
        if d < self.pinch_threshold:
            if self._pinch_start_t is None:
                self._pinch_start_t = now

            # Held long enough → start drag
            if (
                not self._dragging
                and (now - self._pinch_start_t) >= self.hold_delay_s
            ):
                self._dragging = True
                events.append("PINCH_START")

        # ---------- RELEASE ----------
        else:
            if self._pinch_start_t is not None:
                if self._dragging:
                    events.append("PINCH_END")
                else:
                    events.append("CLICK")

            # reset state
            self._pinch_start_t = None
            self._dragging = False

        return events
