import time
import math

class FrameDetector:
    """
    Detects a "Picture Frame" gesture using two hands.
    
    Gesture Description:
      - Left Hand: Thumb pointing UP, Index pointing RIGHT.
      - Right Hand: Thumb pointing DOWN, Index pointing LEFT.
      - Relative Position: Right hand is roughly above and to the right of the Left hand.
      
    Emits:
      - "SCREENSHOT_TRIGGER" when the pose is held for `activation_time` seconds.
    """
    def __init__(self, activation_time=1.0, cooldown_s=2.0):
        self.activation_time = activation_time
        self.cooldown_s = cooldown_s
        
        self._pose_start_time = None
        self._last_trigger_time = 0.0
        self._last_debug_time = 0.0

    def update(self, results):
        """
        results: MediaPipe Hands results object.
        returns: list of event strings (e.g., ["SCREENSHOT"])
        """
        events = []
        now = time.time()

        # Cooldown check
        if (now - self._last_trigger_time) < self.cooldown_s:
            self._pose_start_time = None # Reset pending trigger
            return events

        # Need exactly 2 hands
        if not results.multi_hand_landmarks or len(results.multi_hand_landmarks) != 2:
            self._pose_start_time = None
            return events

        # Identify hands by label ("Left", "Right")
        # Note: multi_handedness[i] corresponds to multi_hand_landmarks[i]
        # MediaPipe usually returns "Left" for the person's left hand (which is on the right side of the image if mirrored, 
        # but let's assume standard webcam mirroring or handle both).
        # Actually, let's just find one "Left" and one "Right".
        
        left_hand_lms = None
        right_hand_lms = None

        if not results.multi_handedness:
             self._pose_start_time = None
             return events

        for idx, classification in enumerate(results.multi_handedness):
            # classification.classification[0].label is 'Left' or 'Right'
            label = classification.classification[0].label
            landmarks = results.multi_hand_landmarks[idx]
            
            if label == "Left":
                left_hand_lms = landmarks
            elif label == "Right":
                right_hand_lms = landmarks

        if not left_hand_lms or not right_hand_lms:
            self._pose_start_time = None
            return events

        # Check poses
        left_pose = self._is_left_hand_pose(left_hand_lms)
        right_pose = self._is_right_hand_pose(right_hand_lms)
        
        # Debug output to help diagnose detection issues (only print occasionally)
        if (not left_pose or not right_pose) and (now - self._last_debug_time > 2.0):
            if not left_pose:
                print("⚠ Left hand pose not detected - need: thumb UP, index RIGHT")
            if not right_pose:
                print("⚠ Right hand pose not detected - need: thumb DOWN, index LEFT")
            self._last_debug_time = now
        
        if left_pose and right_pose:
             # Check relative positions if needed (Right hand above/right of Left hand)
             # but individual poses might be unique enough.
             
             if self._pose_start_time is None:
                 self._pose_start_time = now
                 print("✓ Frame gesture detected! Hold for 1 second to take screenshot...")
             else:
                 elapsed = now - self._pose_start_time
                 if elapsed > self.activation_time:
                     events.append("SCREENSHOT")
                     print("📸 SCREENSHOT event triggered!")
                     self._last_trigger_time = now
                     self._pose_start_time = None
        else:
            if self._pose_start_time is not None:
                print("✗ Frame gesture lost - resetting")
            self._pose_start_time = None

        return events

    def _is_left_hand_pose(self, lms):
        """
        Left Hand: Thumb Up, Index Right.
        """
        # Landmarks
        # 4: Thumb Tip, 3: Thumb IP, 2: Thumb MCP
        # 8: Index Tip, 6: Index PIP, 5: Index MCP
        
        l = lms.landmark
        
        # Check Thumb UP: Tip y should be significantly above IP and MCP
        # Use threshold for more lenient detection
        thumb_up = (l[4].y < l[3].y - 0.01) and (l[3].y < l[2].y - 0.01)
        
        # Check Index RIGHT: Tip x should be to the right of PIP and MCP
        # (Note: x increases to the right, y increases downward)
        index_right = (l[8].x > l[6].x + 0.01) and (l[6].x > l[5].x + 0.01)
        
        return thumb_up and index_right

    def _is_right_hand_pose(self, lms):
        """
        Right Hand: Thumb Down, Index Left.
        """
        l = lms.landmark
        
        # Check Thumb DOWN: Tip y should be significantly below IP and MCP
        thumb_down = (l[4].y > l[3].y + 0.01) and (l[3].y > l[2].y + 0.01)
        
        # Check Index LEFT: Tip x should be to the left of PIP and MCP
        index_left = (l[8].x < l[6].x - 0.01) and (l[6].x < l[5].x - 0.01)
        
        return thumb_down and index_left
