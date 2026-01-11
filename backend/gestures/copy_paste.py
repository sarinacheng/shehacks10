# copy_paste_gestures.py
#
# Gesture-based COPY / PASTE detector using MediaPipe hand landmarks.
#
# Gestures:
#   COPY  -> 🤌 All five fingertips bundled tightly together (hold 1s)
#   PASTE -> ✋ All five fingers extended and spread apart (hold 1s)
#
# This module DOES NOT touch networking.
# It triggers callbacks:
#   on_copy()
#   on_paste()
#
# Usage:
#   handler = CopyPasteGestureHandler(on_copy=..., on_paste=...)
#   handler.process_landmarks(hand_landmarks)

import time
import math
from typing import Optional, Callable

# MediaPipe landmark indices
WRIST = 0
THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP = 4, 8, 12, 16, 20
THUMB_IP, INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP = 3, 6, 10, 14, 18

ADJ_PAIRS = [
    (THUMB_TIP, INDEX_TIP),
    (INDEX_TIP, MIDDLE_TIP),
    (MIDDLE_TIP, RING_TIP),
    (RING_TIP, PINKY_TIP),
]


def dist(a, b):
    return math.sqrt(
        (a.x - b.x) ** 2 +
        (a.y - b.y) ** 2 +
        (a.z - b.z) ** 2
    )


class CopyPasteGestureHandler:
    """
    Detects COPY / PASTE gestures and triggers callbacks.

    COPY:
      - All five fingertips tightly bundled together
      - Hold for HOLD_DURATION seconds

    PASTE:
      - All fingers extended AND spread apart
      - Hold for HOLD_DURATION seconds
    """

    HOLD_DURATION = 1.0      # seconds gesture must be held
    OPEN_THRESHOLD = 0.30    # hand openness for paste
    SPREAD_MIN_DIST = 0.08   # min distance between adjacent fingertips
    BUNDLE_RADIUS = 0.05     # max radius for fingertip bundle

    def __init__(
        self,
        on_copy: Optional[Callable[[], None]] = None,
        on_paste: Optional[Callable[[], None]] = None,
    ) -> None:
        self.on_copy = on_copy
        self.on_paste = on_paste

        self._active_gesture: Optional[str] = None
        self._gesture_start_time: Optional[float] = None

        print("COPY/PASTE GESTURE HANDLER INITIALIZED")

    # ---------- Public API ----------

    def process_landmarks(self, hand_landmarks) -> None:
        gesture = self._classify_gesture(hand_landmarks)

        # New gesture or reset
        if gesture != self._active_gesture:
            self._active_gesture = gesture
            self._gesture_start_time = time.time() if gesture else None
            if gesture:
                print(f"GESTURE STARTED: {gesture.upper()}")
            return

        # Same gesture held
        if gesture and self._gesture_start_time:
            elapsed = time.time() - self._gesture_start_time
            if elapsed >= self.HOLD_DURATION:
                self._trigger_action(gesture)
                self._active_gesture = None
                self._gesture_start_time = None

    # ---------- Gesture classification ----------

    def _classify_gesture(self, hand_landmarks) -> Optional[str]:
        if hand_landmarks is None:
            return None

        if self._are_fingertips_bundled(hand_landmarks):
            return "copy"

        if self._is_five_spread(hand_landmarks):
            return "paste"

        return None

    # ---------- Geometry helpers ----------

    def _hand_openness(self, hand_landmarks):
        wrist = hand_landmarks.landmark[WRIST]
        tips = [
            hand_landmarks.landmark[i]
            for i in (THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP)
        ]
        return sum(dist(t, wrist) for t in tips) / len(tips)

    def _are_fingertips_bundled(self, hand_landmarks) -> bool:
        """
        COPY gesture:
        All five fingertips are close together in 3D space.
        """
        lms = hand_landmarks.landmark
        tips = [lms[i] for i in
                (THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP)]

        # Center of fingertips
        cx = sum(t.x for t in tips) / len(tips)
        cy = sum(t.y for t in tips) / len(tips)
        cz = sum(t.z for t in tips) / len(tips)

        for t in tips:
            if math.sqrt(
                (t.x - cx) ** 2 +
                (t.y - cy) ** 2 +
                (t.z - cz) ** 2
            ) > self.BUNDLE_RADIUS:
                return False

        return True

    def _is_five_spread(self, hand_landmarks) -> bool:
        """
        PASTE gesture:
        All fingers extended AND spread apart.
        """
        lms = hand_landmarks.landmark
        openness = self._hand_openness(hand_landmarks)

        # All fingers extended (tip above PIP)
        extended = (
            lms[THUMB_TIP].y < lms[THUMB_IP].y and
            lms[INDEX_TIP].y < lms[INDEX_PIP].y and
            lms[MIDDLE_TIP].y < lms[MIDDLE_PIP].y and
            lms[RING_TIP].y < lms[RING_PIP].y and
            lms[PINKY_TIP].y < lms[PINKY_PIP].y
        )

        if not (extended and openness > self.OPEN_THRESHOLD):
            return False

        # Adjacent fingertip spacing
        for a, b in ADJ_PAIRS:
            if dist(lms[a], lms[b]) < self.SPREAD_MIN_DIST:
                return False

        return True

    # ---------- Actions ----------

    def _trigger_action(self, gesture: str) -> None:
        if gesture == "copy":
            print("COPY GESTURE CONFIRMED 🤌")
            if self.on_copy:
                self.on_copy()

        elif gesture == "paste":
            print("PASTE GESTURE CONFIRMED ✋")
            if self.on_paste:
                self.on_paste()
