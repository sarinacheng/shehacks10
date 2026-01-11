import time
import math
from utils.constants import INDEX_TIP, MIDDLE_TIP

# MediaPipe landmark indices for finger joints
INDEX_PIP = 6
MIDDLE_PIP = 10
RING_TIP, PINKY_TIP = 16, 20
RING_PIP, PINKY_PIP = 14, 18

class ScrollDetector:
    """
    Detects two-finger scroll gesture: index and middle fingers moving together up/down.
    Emits scroll events based on vertical movement of the two fingers.
    """
    def __init__(self, 
                 finger_raise_threshold=0.005,  # More lenient - fingers don't need to be fully extended
                 min_scroll_delta=0.0003,      # Lower threshold for more responsive scrolling
                 scroll_sensitivity=150.0,     # Increased sensitivity
                 finger_distance_threshold=0.08):  # More lenient - fingers can be slightly apart
        self.finger_raise_threshold = finger_raise_threshold
        self.min_scroll_delta = min_scroll_delta
        self.scroll_sensitivity = scroll_sensitivity
        self.finger_distance_threshold = finger_distance_threshold
        
        self._is_scrolling = False
        self._last_y_position = None

    def _is_finger_raised(self, landmarks, tip_idx, pip_idx):
        """Check if finger is raised (tip is above PIP joint)"""
        tip = landmarks[tip_idx]
        pip = landmarks[pip_idx]
        # In image coordinates, y increases downward
        # Finger is raised if tip is above PIP (extended finger)
        return (pip.y - tip.y) > self.finger_raise_threshold

    def _fingers_together(self, landmarks):
        """Check if index and middle fingers are close together"""
        index_tip = landmarks[INDEX_TIP]
        middle_tip = landmarks[MIDDLE_TIP]
        distance = math.sqrt(
            (index_tip.x - middle_tip.x) ** 2 +
            (index_tip.y - middle_tip.y) ** 2 +
            (index_tip.z - middle_tip.z) ** 2
        )
        return distance < self.finger_distance_threshold

    def _get_average_y(self, landmarks):
        """Get average y position of index and middle finger tips"""
        index_tip = landmarks[INDEX_TIP]
        middle_tip = landmarks[MIDDLE_TIP]
        return (index_tip.y + middle_tip.y) / 2.0

    def update(self, hand_landmarks):
        """
        hand_landmarks: a single MediaPipe HandLandmarks object
        returns: list of events, each is ("SCROLL", delta_y) where delta_y is scroll amount
        """
        events = []
        lms = hand_landmarks.landmark

        # Check if fingers are together (primary requirement)
        fingers_together = self._fingers_together(lms)
        
        # Check if index and middle fingers are extended
        index_raised = self._is_finger_raised(lms, INDEX_TIP, INDEX_PIP)
        middle_raised = self._is_finger_raised(lms, MIDDLE_TIP, MIDDLE_PIP)
        
        # Check that ring and pinky are NOT extended (critical to distinguish from swipe)
        # Ring and pinky should be below their PIP joints (not extended)
        # Use stricter check: tips should be at or below PIP joints
        ring_not_extended = lms[RING_TIP].y >= lms[RING_PIP].y
        pinky_not_extended = lms[PINKY_TIP].y >= lms[PINKY_PIP].y
        
        # Scroll requires: 
        # - Index AND middle together and raised (both must be raised)
        # - Ring AND pinky NOT extended (both must be down)
        # This ensures exactly 2 fingers, not 4
        exactly_two_fingers = (index_raised and middle_raised and 
                             ring_not_extended and pinky_not_extended)
        
        if fingers_together and exactly_two_fingers:
            current_y = self._get_average_y(lms)
            
            if self._last_y_position is not None:
                # Calculate vertical movement (positive = moved down, negative = moved up)
                delta_y = current_y - self._last_y_position
                
                # Emit scroll for any movement to ensure smooth, continuous scrolling
                if abs(delta_y) > self.min_scroll_delta:
                    # delta_y: positive = moved down, negative = moved up
                    # In pynput: positive dy scrolls UP, negative dy scrolls DOWN
                    # So we invert: when fingers move up (negative delta_y), we want positive scroll (scroll up)
                    scroll_amount = -delta_y * self.scroll_sensitivity
                    # Filter out very small movements to avoid noise (lowered threshold)
                    if abs(scroll_amount) > 0.3:
                        events.append(("SCROLL", scroll_amount))
            
            # Update position for next frame
            self._last_y_position = current_y
            self._is_scrolling = True
        else:
            # Reset when fingers are no longer together
            self._last_y_position = None
            self._is_scrolling = False

        return events

    def is_scrolling(self):
        """Returns True if currently in scrolling mode (two fingers raised)"""
        return self._is_scrolling
