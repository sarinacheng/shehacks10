from camera.webcam import Webcam
from tracking.hand_tracker import HandTracker

def main():
    cam = Webcam(index=0, window_name="Hover Screen")
    tracker = HandTracker(max_num_hands=2)

    while True:
        frame = cam.read()
        if frame is None:
            break

        results = tracker.process(frame)
        tracker.draw(frame, results)

        if cam.show(frame):  # returns True if user pressed ESC/Q
            break

    cam.release()

if __name__ == "__main__":
    main()
