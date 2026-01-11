import time
import math
from typing import Optional

# MediaPipe landmark indices
WRIST = 0
THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP = 4, 8, 12, 16, 20
THUMB_IP, INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP = 3, 6, 10, 14, 18


def _dist3(a, b) -> float:
    return math.sqrt(
        (a.x - b.x) ** 2 +
        (a.y - b.y) ** 2 +
        (a.z - b.z) ** 2
    )


class StopResumeDetector:
    """
    Detects two gestures:
    1. STOP: Both palms up with all five fingers extended (disables all features)
    2. RESUME: Both hands making semi-circles (enables all features)
    """
    
    def __init__(
        self,
        stop_hold_time=1.0,  # Hold both palms up for 1 second to stop
        semi_circle_radius_threshold=0.03,  # Minimum radius for semi-circle detection
        semi_circle_angle_threshold=2.5,  # Minimum angle coverage for semi-circle (radians, ~143 degrees)
        circle_time_window=2.0  # Time window to complete both semi-circles
    ):
        self.stop_hold_time = stop_hold_time
        self.semi_circle_radius_threshold = semi_circle_radius_threshold
        self.semi_circle_angle_threshold = semi_circle_angle_threshold
        self.circle_time_window = circle_time_window
        
        # State tracking
        self._stop_gesture_start = None
        self._left_hand_positions = []  # List of (x, y, time) tuples for left hand
        self._right_hand_positions = []  # List of (x, y, time) tuples for right hand
        
    def _all_fingers_extended(self, hand_landmarks) -> bool:
        """Check if all 5 fingers are extended"""
        lms = hand_landmarks.landmark
        
        # All fingertips should be above their PIP joints (y decreases upward)
        thumb_extended = lms[THUMB_TIP].y < lms[THUMB_IP].y
        index_extended = lms[INDEX_TIP].y < lms[INDEX_PIP].y
        middle_extended = lms[MIDDLE_TIP].y < lms[MIDDLE_PIP].y
        ring_extended = lms[RING_TIP].y < lms[RING_PIP].y
        pinky_extended = lms[PINKY_TIP].y < lms[PINKY_PIP].y
        
        return thumb_extended and index_extended and middle_extended and ring_extended and pinky_extended
    
    def _palm_facing_up(self, hand_landmarks) -> bool:
        """Check if palm is facing up (wrist below fingertips)"""
        lms = hand_landmarks.landmark
        wrist_y = lms[WRIST].y
        
        # Average y-coordinate of fingertips (lower y = higher up)
        avg_fingertip_y = (
            lms[THUMB_TIP].y +
            lms[INDEX_TIP].y +
            lms[MIDDLE_TIP].y +
            lms[RING_TIP].y +
            lms[PINKY_TIP].y
        ) / 5
        
        # Wrist should be below fingertips (higher y value)
        return wrist_y > avg_fingertip_y + 0.02
    
    def _detect_stop_gesture(self, results) -> bool:
        """Detect if both palms are up with all fingers extended"""
        if not results.multi_hand_landmarks or len(results.multi_hand_landmarks) != 2:
            return False
        
        # Check both hands
        for hand in results.multi_hand_landmarks:
            if not self._all_fingers_extended(hand):
                return False
            if not self._palm_facing_up(hand):
                return False
        
        return True
    
    def _detect_semi_circle(self, positions) -> bool:
        """Detect if positions form a semi-circle"""
        if len(positions) < 5:
            return False
        
        now = time.time()
        # Remove old positions
        recent_positions = [(x, y, t) for x, y, t in positions if (now - t) <= self.circle_time_window]
        
        if len(recent_positions) < 5:
            return False
        
        # Calculate center
        center_x = sum(x for x, y, t in recent_positions) / len(recent_positions)
        center_y = sum(y for x, y, t in recent_positions) / len(recent_positions)
        
        # Calculate average radius
        radii = [
            math.sqrt((x - center_x)**2 + (y - center_y)**2)
            for x, y, t in recent_positions
        ]
        avg_radius = sum(radii) / len(radii)
        
        # Check if radius is large enough
        if avg_radius < self.semi_circle_radius_threshold:
            return False
        
        # Calculate angles relative to center
        angles = []
        for x, y, t in recent_positions:
            angle = math.atan2(y - center_y, x - center_x)
            angles.append(angle)
        
        # Sort angles and calculate total angle coverage
        angles_sorted = sorted(angles)
        # Calculate total angular span
        total_span = angles_sorted[-1] - angles_sorted[0]
        
        # Handle wrap-around case
        if total_span < 0:
            total_span += 2 * math.pi
        
        # Check if the span covers at least a semi-circle
        return total_span >= self.semi_circle_angle_threshold
    
    def _detect_two_hand_circle_gesture(self, results) -> bool:
        """Detect if both hands are making semi-circles"""
        if not results.multi_hand_landmarks or len(results.multi_hand_landmarks) != 2:
            return False
        
        now = time.time()
        lms_left = None
        lms_right = None
        
        # Identify left and right hands
        if not results.multi_handedness:
            return False
        
        for idx, classification in enumerate(results.multi_handedness):
            label = classification.classification[0].label
            landmarks = results.multi_hand_landmarks[idx]
            
            if label == "Left":
                lms_left = landmarks
            elif label == "Right":
                lms_right = landmarks
        
        if not lms_left or not lms_right:
            return False
        
        # Track positions for both hands
        left_x = lms_left.landmark[INDEX_TIP].x
        left_y = lms_left.landmark[INDEX_TIP].y
        right_x = lms_right.landmark[INDEX_TIP].x
        right_y = lms_right.landmark[INDEX_TIP].y
        
        # Add current positions
        self._left_hand_positions.append((left_x, left_y, now))
        self._right_hand_positions.append((right_x, right_y, now))
        
        # Remove old positions
        self._left_hand_positions = [
            (x, y, t) for x, y, t in self._left_hand_positions
            if (now - t) <= self.circle_time_window
        ]
        self._right_hand_positions = [
            (x, y, t) for x, y, t in self._right_hand_positions
            if (now - t) <= self.circle_time_window
        ]
        
        # Check if both hands are making semi-circles
        left_semi_circle = self._detect_semi_circle(self._left_hand_positions)
        right_semi_circle = self._detect_semi_circle(self._right_hand_positions)
        
        return left_semi_circle and right_semi_circle
    
    def update(self, results) -> Optional[str]:
        """
        Returns:
            "STOP" if stop gesture detected
            "RESUME" if resume gesture detected
            None otherwise
        """
        events = None
        now = time.time()
        
        # Check for STOP gesture (both palms up)
        if self._detect_stop_gesture(results):
            if self._stop_gesture_start is None:
                self._stop_gesture_start = now
            elif (now - self._stop_gesture_start) >= self.stop_hold_time:
                events = "STOP"
                self._stop_gesture_start = None
                # Reset circle detection when stop is triggered
                self._left_hand_positions = []
                self._right_hand_positions = []
        else:
            self._stop_gesture_start = None
        
        # Check for RESUME gesture (both hands making semi-circles)
        if self._detect_two_hand_circle_gesture(results):
            events = "RESUME"
            # Reset positions after detecting
            self._left_hand_positions = []
            self._right_hand_positions = []
        
        return events
