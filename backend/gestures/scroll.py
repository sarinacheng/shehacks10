import time
from utils.constants import INDEX_TIP, MIDDLE_TIP

# MediaPipe landmark indices for finger joints
INDEX_PIP = 6
MIDDLE_PIP = 10

class ScrollDetector:
    """
    Detects two-finger scroll gesture: index and middle fingers moving together up/down.
    Emits scroll events based on vertical movement of the two fingers.
    """
    def __init__(self, 
                 finger_raise_threshold=0.015,  # How much tip must be above PIP for raised finger
                 min_scroll_delta=0.0005,      # Minimum movement to trigger scroll
                 scroll_sensitivity=100.0):   # Multiplier for scroll amount
        self.finger_raise_threshold = finger_raise_threshold
        self.min_scroll_delta = min_scroll_delta
        self.scroll_sensitivity = scroll_sensitivity
        
        self._is_scrolling = False
        self._last_y_position = None

    def _is_finger_raised(self, landmarks, tip_idx, pip_idx):
        """Check if finger is raised (tip is above PIP joint)"""
        tip = landmarks[tip_idx]
        pip = landmarks[pip_idx]
        # In image coordinates, y increases downward
        # Finger is raised if tip is above PIP (extended finger)
        return (pip.y - tip.y) > self.finger_raise_threshold

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

        # Check if both index and middle fingers are raised (extended)
        index_raised = self._is_finger_raised(lms, INDEX_TIP, INDEX_PIP)
        middle_raised = self._is_finger_raised(lms, MIDDLE_TIP, MIDDLE_PIP)
        
        # If both fingers are raised, track their movement for scrolling
        if index_raised and middle_raised:
            current_y = self._get_average_y(lms)
            
            if self._last_y_position is not None:
                # Calculate vertical movement (positive = moved down, negative = moved up)
                delta_y = current_y - self._last_y_position
                
                # Emit scroll for any movement to ensure smooth, continuous scrolling
                if abs(delta_y) > self.min_scroll_delta:
                    # delta_y: positive = moved down, negative = moved up
                    # scroll_amount: positive = scroll down, negative = scroll up
                    scroll_amount = delta_y * self.scroll_sensitivity
                    # Filter out very small movements to avoid noise
                    if abs(scroll_amount) > 0.5:
                        events.append(("SCROLL", scroll_amount))
            
            # Update position for next frame
            self._last_y_position = current_y
            self._is_scrolling = True
        else:
            # Reset when both fingers are no longer raised
            self._last_y_position = None
            self._is_scrolling = False

        return events

    def is_scrolling(self):
        """Returns True if currently in scrolling mode (two fingers raised)"""
        return self._is_scrolling
