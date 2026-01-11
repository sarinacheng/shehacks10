import time
import math
import subprocess
from typing import Optional
import pyautogui

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
    Gestures:
      COPY  -> 🤌 all five fingertips bundled together (hold 1s)
      PASTE -> ✋ all five fingers extended and widely spread (hold 1s)
    """

    HOLD_DURATION = 1.0          # seconds
    OPEN_THRESHOLD = 0.30        # openness for spread hand
    SPREAD_MIN_DIST = 0.08       # min distance between adjacent fingertips
    BUNDLE_RADIUS = 0.05         # max radius for fingertip bundle

    def __init__(self) -> None:
        self._active_gesture: Optional[str] = None
        self._gesture_start_time: Optional[float] = None

    # ---------- Public API ----------

    def process_landmarks(self, hand_landmarks) -> None:
        gesture = self._classify_gesture(hand_landmarks)

        # New gesture or reset
        if gesture != self._active_gesture:
            self._active_gesture = gesture
            self._gesture_start_time = time.time() if gesture else None
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
        All five fingertips are close together in space.
        """
        lms = hand_landmarks.landmark
        tips = [lms[i] for i in
                (THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP)]

        # Center of fingertips
        cx = sum(t.x for t in tips) / len(tips)
        cy = sum(t.y for t in tips) / len(tips)
        cz = sum(t.z for t in tips) / len(tips)

        # All tips must be close to the center
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

        # All fingers extended (tips above PIP joints)
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

    def _show_notification(self, title: str, message: str) -> None:
        """Show both a notification banner and pop-up dialog"""
        # Escape quotes and special characters
        escaped_message = message.replace('"', '\\"').replace('\\', '\\\\')
        escaped_title = title.replace('"', '\\"').replace('\\', '\\\\')
        
        # Notification banner (top right corner)
        notification_script = f'''
        display notification "{escaped_message}" with title "{escaped_title}" sound name "Glass"
        '''
        
        # Pop-up dialog (center of screen)
        dialog_script = f'''
        display dialog "{escaped_message}" with title "{escaped_title}" buttons {{"OK"}} default button "OK" giving up after 2
        '''
        
        # Show both
        subprocess.Popen(["osascript", "-e", notification_script], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen(["osascript", "-e", dialog_script], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _trigger_action(self, gesture: str) -> None:
        if gesture == "copy":
            pyautogui.hotkey("command", "c")
            self._show_notification("Copied!", "Copied!")
        elif gesture == "paste":
            pyautogui.hotkey("command", "v")
            # No notification for paste
       


