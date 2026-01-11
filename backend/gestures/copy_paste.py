import time
import math

FINGERTIPS = [4, 8, 12, 16, 20]
WRIST = 0

# Adjacent fingertip pairs to confirm spread
ADJ_PAIRS = [(4, 8), (8, 12), (12, 16), (16, 20)]


def dist(a, b):
    return math.sqrt(
        (a.x - b.x) ** 2 +
        (a.y - b.y) ** 2 +
        (a.z - b.z) ** 2
    )


class CopyPasteDetector:
    """
    Emits:
      - "COPY"  → closed fist (hold 2s)
      - "PASTE" → all five fingers widely spread (hold 2s)
    """

    def __init__(
        self,
        open_threshold=0.32,        # overall openness needed for spread hand
        closed_threshold=0.12,      # tight fist
        spread_min_dist=0.08,       # min distance between adjacent fingertips
        hold_duration=2.0,
        cooldown_s=0.6,
        timeout=3.0
    ):
        self.open_threshold = open_threshold
        self.closed_threshold = closed_threshold
        self.spread_min_dist = spread_min_dist
        self.hold_duration = hold_duration
        self.cooldown_s = cooldown_s
        self.timeout = timeout

        self._hold_start_t = None
        self._current_pose = None
        self._last_event_t = 0.0

    def _hand_openness(self, hand_landmarks):
        wrist = hand_landmarks.landmark[WRIST]
        tips = [hand_landmarks.landmark[i] for i in FINGERTIPS]
        return sum(dist(t, wrist) for t in tips) / len(tips)

    def _fingers_spread(self, hand_landmarks):
        lms = hand_landmarks.landmark
        for a, b in ADJ_PAIRS:
            if dist(lms[a], lms[b]) < self.spread_min_dist:
                return False
        return True

    def update(self, hand_landmarks):
        events = []
        now = time.time()

        openness = self._hand_openness(hand_landmarks)

        # Determine pose
        pose = None
        if openness < self.closed_threshold:
            pose = "CLOSED"  # fist
        elif openness > self.open_threshold and self._fingers_spread(hand_landmarks):
            pose = "OPEN_SPREAD"

        # Track/trigger
        if pose and pose == self._current_pose:
            if self._hold_start_t is None:
                self._hold_start_t = now

            held_for = now - self._hold_start_t

            if held_for > self.timeout:
                self._hold_start_t = None
                self._current_pose = None
                return events

            action = "PASTE" if pose == "OPEN_SPREAD" else "COPY"
            if held_for >= self.hold_duration and (now - self._last_event_t) >= self.cooldown_s:
                events.append(action)
                self._last_event_t = now
                self._hold_start_t = None
                self._current_pose = None

        elif pose and pose != self._current_pose:
            self._current_pose = pose
            self._hold_start_t = None

        else:  # pose is None
            self._hold_start_t = None
            self._current_pose = None

        return events




