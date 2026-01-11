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
        circle_time_window=2.0,  # Time window to track hand movements
        min_arc_points=5,  # Minimum points needed to detect arc motion
        min_arc_angle=1.5,  # Minimum angle span for arc detection (radians, ~86 degrees)
        min_arc_radius=0.02,  # Minimum radius for arc to be considered valid
        finger_tip_connection_threshold=0.06  # Maximum distance between finger tips to consider them "connected"
    ):
        self.stop_hold_time = stop_hold_time
        self.circle_time_window = circle_time_window
        self.min_arc_points = min_arc_points
        self.min_arc_angle = min_arc_angle
        self.min_arc_radius = min_arc_radius
        self.finger_tip_connection_threshold = finger_tip_connection_threshold
        
        # State tracking
        self._stop_gesture_start = None
        self._left_hand_positions = []  # List of (x, y, time) tuples for left hand
        self._right_hand_positions = []  # List of (x, y, time) tuples for right hand
        self._last_resume_time = 0.0
        self._resume_cooldown = 0.8  # Cooldown between resume detections
        
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
    
    def _detect_arc_motion(self, positions) -> bool:
        """Simple check if positions form an arc (semi-circle motion)"""
        now = time.time()
        # Get recent positions
        recent = [(x, y, t) for x, y, t in positions if (now - t) <= self.circle_time_window]
        
        if len(recent) < self.min_arc_points:
            return False
        
        # Simple approach: check if there's significant angular change
        # Calculate center of recent positions
        center_x = sum(x for x, y, t in recent) / len(recent)
        center_y = sum(y for x, y, t in recent) / len(recent)
        
        # Calculate angles relative to center
        angles = [math.atan2(y - center_y, x - center_x) for x, y, t in recent]
        
        # Calculate average radius
        radii = [
            math.sqrt((x - center_x)**2 + (y - center_y)**2)
            for x, y, t in recent
        ]
        avg_radius = sum(radii) / len(radii)
        
        # Check if radius is large enough
        if avg_radius < self.min_arc_radius:
            return False
        
        # Calculate angular span
        angles_sorted = sorted(angles)
        span = angles_sorted[-1] - angles_sorted[0]
        
        # Handle wrap-around
        if span < 0:
            span += 2 * math.pi
        
        # Check if span is large enough for a semi-circle
        return span >= self.min_arc_angle
    
    def _detect_two_hand_circle_gesture(self, results) -> bool:
        """Detect when both hands make semi-circles and come together"""
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
        
        # Get current finger tip positions
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
        
        # Check if both hands are making arc motions (semi-circles)
        left_arc = self._detect_arc_motion(self._left_hand_positions)
        right_arc = self._detect_arc_motion(self._right_hand_positions)
        
        # Check if finger tips are currently close together (connected)
        finger_tip_distance = math.sqrt((left_x - right_x)**2 + (left_y - right_y)**2)
        fingers_connected = finger_tip_distance <= self.finger_tip_connection_threshold
        
        # Resume when both hands are making arcs AND they come together
        return left_arc and right_arc and fingers_connected
    
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
        # Only check if cooldown has passed
        if (now - self._last_resume_time) >= self._resume_cooldown:
            if self._detect_two_hand_circle_gesture(results):
                events = "RESUME"
                self._last_resume_time = now
                # Reset positions after detecting
                self._left_hand_positions = []
                self._right_hand_positions = []
        
        return events
