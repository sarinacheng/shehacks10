# backend/main.py

from camera.webcam import Webcam
from tracking.hand_tracker import HandTracker

from gestures.pinch import PinchDetector
from gestures.cursor import CursorMapper

from gestures.frame import FrameDetector
from input.mouse_controller import MouseController
from input.event_loop import EventLoop

from Quartz import CGDisplayBounds, CGMainDisplayID


def get_screen_size():
    b = CGDisplayBounds(CGMainDisplayID())
    return int(b.size.width), int(b.size.height)


def main():
    cam = Webcam(index=0, window_name="Hand Tracker")
    tracker = HandTracker(max_num_hands=2)

    frame_detector = FrameDetector()

    pinch = PinchDetector(
        pinch_threshold=0.045,
        release_threshold=0.060,
        hold_delay_s=0.25
    )   


    # Mouse controller + event loop (runs OS input on separate thread)
    mouse = MouseController()
    events = EventLoop(mouse)
    events.start()

    # Use macOS Quartz for real screen size (prevents "invisible wall")
    screen_w, screen_h = get_screen_size()
    print("screen:", screen_w, screen_h)

    # Cursor mapping (tune these)
    cursor = CursorMapper(
        screen_w, screen_h,
        roi_x_min=0.05, roi_x_max=0.95,
        roi_y_min=0.10, roi_y_max=0.90,
        gain=2.2,
        smoothing=0.15,
        offset_px=(5, 0)   # cursor appears slightly beside fingertip
    )

    try:
        while True:
            frame = cam.read()
            if frame is None:
                break

            results = tracker.process(frame)
            tracker.draw(frame, results)

            if results.multi_hand_landmarks:
                # 1. Pinch Detection (using first detected hand)
                hand = results.multi_hand_landmarks[0]

                # cursor move every frame
                x, y = cursor.update(hand)
                events.emit(("MOVE", x, y))

                # pinch click events
                pinch_events = pinch.update(hand)
                for ev in pinch_events:
                    events.emit(ev)
                # pinch.handle_pinch_events(pinch_events)
                for ev in pinch_events:
                    events.emit(ev)

                # 2. Frame Gesture Detection (passing all results)
                for ev in frame_detector.update(results):
                    events.emit(ev)

            if cam.show(frame):
                break

    finally:
        events.stop()
        cam.release()


if __name__ == "__main__":
    main()
