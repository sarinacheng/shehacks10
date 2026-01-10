from camera.webcam import Webcam
from tracking.hand_tracker import HandTracker

from gestures.pinch import PinchDetector
from input.mouse_controller import MouseController
from input.event_loop import EventLoop

def main():
    cam = Webcam(index=0, window_name="Hand Tracker")
    tracker = HandTracker(max_num_hands=1)

    pinch = PinchDetector(
        pinch_threshold=0.045,
        release_threshold=0.060,
        cooldown_s=0.20,
    )

    mouse = MouseController()
    events = EventLoop(mouse)
    events.start()

    try:
        while True:
            frame = cam.read()
            if frame is None:
                break

            results = tracker.process(frame)
            tracker.draw(frame, results)

            # Emit events (option B)
            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]
                for ev in pinch.update(hand):
                    events.emit(ev)

            if cam.show(frame):
                break
    finally:
        events.stop()
        cam.release()

if __name__ == "__main__":
    main()
