import time
from typing import Optional

# MediaPipe landmark indices
WRIST = 0
THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP = 4, 8, 12, 16, 20
THUMB_IP, INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP = 3, 6, 10, 14, 18


class PalmArrowDetector:
    """
    Detects palm-up gestures to trigger arrow key navigation:
    - Right hand palm up → Control + Right arrow
    - Left hand palm up → Control + Left arrow
    """
    
    def __init__(
        self,
        hold_time=3.0,  # Hold palm up for this duration to trigger (3 seconds)
        cooldown=0.5  # Cooldown between triggers
    ):
        self.hold_time = hold_time
        self.cooldown = cooldown
        
        # State tracking
        self._right_palm_up_start = None
        self._left_palm_up_start = None
        self._last_right_trigger = 0.0
        self._last_left_trigger = 0.0
    
    def _all_fingers_extended(self, hand_landmarks) -> bool:
        """Check if all 5 fingers are extended (flat hand)"""
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
    
    def _is_flat_palm_up(self, hand_landmarks) -> bool:
        """Check if hand is flat (all fingers extended) AND palm is facing up"""
        return self._all_fingers_extended(hand_landmarks) and self._palm_facing_up(hand_landmarks)
    
    def _identify_hand(self, hand_landmarks, mediapipe_label):
        """
        Identify which hand it is (user's left or right).
        Uses MediaPipe label as primary, with position-based verification.
        Returns: "left" or "right" from user's perspective
        """
        # MediaPipe labels hands from the person's perspective:
        # "Left" = person's left hand, "Right" = person's right hand
        # This should be correct, but we can verify with position
        
        # Get wrist position for position-based verification
        wrist_x = hand_landmarks.landmark[WRIST].x
        
        # If MediaPipe says "Left", it's the user's left hand
        # If MediaPipe says "Right", it's the user's right hand
        # Position check: left hand is typically on left side (x < 0.5), right hand on right (x > 0.5)
        # But this can vary, so we trust MediaPipe's label primarily
        
        if mediapipe_label == "Left":
            return "left"
        elif mediapipe_label == "Right":
            return "right"
        else:
            # Fallback: use position if label is unclear
            return "left" if wrist_x < 0.5 else "right"
    
    def update(self, results) -> Optional[str]:
        """
        Returns:
            "CONTROL_RIGHT" if right hand palm is up
            "CONTROL_LEFT" if left hand palm is up
            None otherwise
        """
        if not results.multi_hand_landmarks:
            self._right_palm_up_start = None
            self._left_palm_up_start = None
            return None
        
        now = time.time()
        event = None
        
        # Check each detected hand
        for idx, hand in enumerate(results.multi_hand_landmarks):
            if not results.multi_handedness:
                continue
            
            # Get MediaPipe hand label
            classification = results.multi_handedness[idx]
            mediapipe_label = classification.classification[0].label
            
            # Identify which hand it is from user's perspective
            user_hand = self._identify_hand(hand, mediapipe_label)
            
            # Check if hand is flat (all fingers extended) AND palm is facing up
            flat_palm_up = self._is_flat_palm_up(hand)
            
            # Map user's hand to the correct arrow key
            # Left hand → Control + Left arrow
            # Right hand → Control + Right arrow
            # Only trigger when hand is FLAT and palm is UP for the full hold_time
            if user_hand == "left" and flat_palm_up:
                # User's left hand flat and palm up → Control Left
                if self._left_palm_up_start is None:
                    self._left_palm_up_start = now
                elif (now - self._left_palm_up_start) >= self.hold_time:
                    # Check cooldown
                    if (now - self._last_left_trigger) >= self.cooldown:
                        event = "CONTROL_LEFT"
                        self._last_left_trigger = now
                        self._left_palm_up_start = None
            else:
                # Reset if hand is not flat and palm up, or not left hand
                if user_hand == "left":
                    self._left_palm_up_start = None
            
            if user_hand == "right" and flat_palm_up:
                # User's right hand flat and palm up → Control Right
                if self._right_palm_up_start is None:
                    self._right_palm_up_start = now
                elif (now - self._right_palm_up_start) >= self.hold_time:
                    # Check cooldown
                    if (now - self._last_right_trigger) >= self.cooldown:
                        event = "CONTROL_RIGHT"
                        self._last_right_trigger = now
                        self._right_palm_up_start = None
            else:
                # Reset if hand is not flat and palm up, or not right hand
                if user_hand == "right":
                    self._right_palm_up_start = None
        
        return event
