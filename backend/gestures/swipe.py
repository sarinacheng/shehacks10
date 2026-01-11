import time
import math
from typing import Optional

# MediaPipe landmark indices
INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP = 8, 12, 16, 20
INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP = 6, 10, 14, 18

def _dist3(a, b) -> float:
    """Calculate 3D distance between two landmarks"""
    return math.sqrt(
        (a.x - b.x) ** 2 +
        (a.y - b.y) ** 2 +
        (a.z - b.z) ** 2
    )


class SwipeDetector:
    """
    Detects swipe gestures with fingers together (not spread out).
    This distinguishes swipe from paste gesture which requires fingers spread out.
    
    Requirements:
    - Fingers must be together (adjacent fingertips close)
    - All fingers extended
    - Horizontal or vertical movement
    """
    
    def __init__(
        self,
        finger_together_threshold=0.06,  # Max distance between adjacent fingertips (lenient - just needs to be closer than paste)
        min_swipe_distance=0.02,  # Minimum movement distance to trigger swipe (more sensitive)
        hold_time=0.15  # Time to hold gesture before recognizing swipe (faster)
    ):
        self.finger_together_threshold = finger_together_threshold
        self.min_swipe_distance = min_swipe_distance
        self.hold_time = hold_time
        
        # State tracking
        self._gesture_start_time = None
        self._start_position = None
        self._last_position = None
    
    def _fingers_together(self, hand_landmarks) -> bool:
        """Check if fingers are together (adjacent fingertips are reasonably close, not spread out like paste)"""
        lms = hand_landmarks.landmark
        
        # Adjacent finger pairs that should be close together
        finger_pairs = [
            (INDEX_TIP, MIDDLE_TIP),
            (MIDDLE_TIP, RING_TIP),
            (RING_TIP, PINKY_TIP),
        ]
        
        # Check that at least 2 out of 3 adjacent finger pairs are close together
        # This makes it more lenient - doesn't require all fingers to be perfectly together
        close_pairs = 0
        for tip1_idx, tip2_idx in finger_pairs:
            distance = _dist3(lms[tip1_idx], lms[tip2_idx])
            if distance <= self.finger_together_threshold:
                close_pairs += 1
        
        # At least 2 pairs should be close (more lenient than requiring all 3)
        return close_pairs >= 2
    
    def _all_fingers_extended(self, hand_landmarks) -> bool:
        """Check if all 4 fingers (index, middle, ring, pinky) are extended"""
        lms = hand_landmarks.landmark
        
        index_extended = lms[INDEX_TIP].y < lms[INDEX_PIP].y
        middle_extended = lms[MIDDLE_TIP].y < lms[MIDDLE_PIP].y
        ring_extended = lms[RING_TIP].y < lms[RING_PIP].y
        pinky_extended = lms[PINKY_TIP].y < lms[PINKY_PIP].y
        
        # ALL 4 fingers must be extended for swipe (strict requirement)
        # This ensures exactly 4 fingers, not 2
        all_four_extended = (index_extended and middle_extended and 
                            ring_extended and pinky_extended)
        
        return all_four_extended
    
    def update(self, hand_landmarks, hand_label=None) -> Optional[str]:
        """
        Returns:
            "CONTROL_LEFT" if left hand swipes horizontally
            "CONTROL_RIGHT" if right hand swipes horizontally
            None otherwise
        """
        if hand_landmarks is None:
            self._gesture_start_time = None
            self._start_position = None
            self._last_position = None
            return None
        
        now = time.time()
        lms = hand_landmarks.landmark
        
        # Get current hand position (using middle finger tip as reference)
        current_pos = (lms[MIDDLE_TIP].x, lms[MIDDLE_TIP].y)
        
        # Check if fingers are together and extended
        fingers_together = self._fingers_together(hand_landmarks)
        fingers_extended = self._all_fingers_extended(hand_landmarks)
        
        # Debug output (occasionally)
        if int(now * 2) % 2 == 0:  # Print roughly every 0.5 seconds
            pass  # Commented out to reduce noise, uncomment if needed for debugging
            # print(f"[SWIPE DEBUG] Fingers together: {fingers_together}, Extended: {fingers_extended}")
        
        if fingers_together and fingers_extended:
            if self._start_position is None:
                self._start_position = current_pos
                self._gesture_start_time = now
                self._last_position = current_pos
            else:
                # Calculate movement distance
                dx = current_pos[0] - self._start_position[0]
                dy = current_pos[1] - self._start_position[1]
                distance = math.sqrt(dx**2 + dy**2)
                
                # Check if movement is significant and gesture held long enough
                if distance >= self.min_swipe_distance and (now - self._gesture_start_time) >= self.hold_time:
                    # Only trigger on horizontal swipes (left/right)
                    if abs(dx) > abs(dy):
                        # Horizontal swipe - determine based on hand
                        if hand_label == "Left":
                            # Left hand swipes → Control Left
                            result = "CONTROL_LEFT"
                        elif hand_label == "Right":
                            # Right hand swipes → Control Right
                            result = "CONTROL_RIGHT"
                        else:
                            # Fallback: use swipe direction if hand label not available
                            if dx > 0:
                                result = "CONTROL_RIGHT"
                            else:
                                result = "CONTROL_LEFT"
                        
                        print(f"[SWIPE] {result} detected! Hand: {hand_label}, Distance: {distance:.3f}, Time: {now - self._gesture_start_time:.2f}s")
                        
                        # Reset after detecting swipe
                        self._gesture_start_time = None
                        self._start_position = None
                        self._last_position = None
                        return result
                    # Vertical swipes are ignored
                
                
                self._last_position = current_pos
        else:
            # Reset if fingers are not together or not extended
            self._gesture_start_time = None
            self._start_position = None
            self._last_position = None
        
        return None
