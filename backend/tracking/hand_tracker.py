import cv2
import mediapipe as mp

class HandTracker:
    def __init__(self, max_num_hands=2, det_conf=0.6, track_conf=0.6):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=det_conf,
            min_tracking_confidence=track_conf,
        )
        self.drawer = mp.solutions.drawing_utils

    def process(self, frame_bgr):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return self.hands.process(rgb)

    def draw(self, frame_bgr, results):
        if results.multi_hand_landmarks:
            for hand in results.multi_hand_landmarks:
                self.drawer.draw_landmarks(
                    frame_bgr, hand, self.mp_hands.HAND_CONNECTIONS
                )
