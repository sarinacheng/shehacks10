import time
import math

# MediaPipe landmark indices
THUMB_TIP = 4
INDEX_TIP = 8

def _dist3(a, b) -> float:
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)

class PinchDetector:
    """
    Emits:
      - "PINCH_START" once when pinch begins
      - "PINCH_END" once when pinch ends
    Uses hysteresis to avoid flicker, plus an optional cooldown.
    """
    def __init__(self, pinch_threshold=0.045, release_threshold=0.060, cooldown_s=0.20):
        self.pinch_threshold = pinch_threshold
        self.release_threshold = release_threshold
        self.cooldown_s = cooldown_s

        self._is_pinching = False
        self._last_start_t = 0.0

    def update(self, hand_landmarks):
        """
        hand_landmarks: a single MediaPipe HandLandmarks object
        returns: list of event strings (0..2 events)
        """
        events = []

        lms = hand_landmarks.landmark
        d = _dist3(lms[THUMB_TIP], lms[INDEX_TIP])
        now = time.time()

        if not self._is_pinching:
            if d < self.pinch_threshold and (now - self._last_start_t) >= self.cooldown_s:
                self._is_pinching = True
                self._last_start_t = now
                events.append("PINCH_START")
        else:
            if d > self.release_threshold:
                self._is_pinching = False
                events.append("PINCH_END")

        return events
