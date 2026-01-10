from camera.webcam import Webcam
from tracking.hand_tracker import HandTracker

from gestures.pinch import PinchDetector
from gestures.cursor import CursorMapper

from input.mouse_controller import MouseController
from input.event_loop import EventLoop


def main():
    cam = Webcam(index=0, window_name="Hand Tracker")
    tracker = HandTracker(max_num_hands=1)

    pinch = PinchDetector(
        pinch_threshold=0.045,
        release_threshold=0.060,
        cooldown_s=0.20
    )

    # Create mouse controller first so we can get screen size
    mouse = MouseController()
    screen_w, screen_h = mouse.screen_w, mouse.screen_h

    # Now cursor mapper can use screen size
    # cursor = CursorMapper(screen_w, screen_h, offset_px=(40, 0))   # 40px to the right
    # or
    cursor = CursorMapper(screen_w, screen_h, offset_px=(5, 0)) # right + a bit up

    events = EventLoop(mouse)
    events.start()

    try:
        while True:
            frame = cam.read()
            if frame is None:
                break

            results = tracker.process(frame)
            tracker.draw(frame, results)

            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]

                # cursor move every frame
                x, y = cursor.update(hand)
                events.emit(("MOVE", x, y))

                # pinch click events
                for ev in pinch.update(hand):
                    events.emit(ev)

            if cam.show(frame):
                break
    finally:
        events.stop()
        cam.release()


if __name__ == "__main__":
    main()
