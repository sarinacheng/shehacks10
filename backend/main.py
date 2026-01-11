# backend/main.py

import time
import cv2
import numpy as np
import threading
import sys

from camera.webcam import Webcam
from tracking.hand_tracker import HandTracker

from gestures.pinch import PinchDetector
from gestures.scroll import ScrollDetector
from gestures.cursor import CursorMapper
from gestures.copy_paste import CopyPasteGestureHandler
from gestures.frame import FrameDetector
from gestures.stop_resume import StopResumeDetector
from gestures.palm_arrow import PalmArrowDetector
from gestures.swipe import SwipeDetector

# New Bluetooth Input Modules
from input.bluetooth_service import BluetoothService
from input.bt_mouse_controller import BtMouseController
from input.event_loop import EventLoop

def get_virtual_screen_size():
    # Use a standard resolution for normalizing movement
    return 1920, 1080

def main():
    print("[INFO] Starting Hover Mouse for Raspberry Pi (Bluetooth HID)")
    
    # ---------- Bluetooth Setup ----------
    # This must run as root (sudo) usually
    try:
        bt_service = BluetoothService()
        bt_service.setup()
    except Exception as e:
        print(f"[ERROR] Failed to setup Bluetooth Service: {e}")
        print("Did you run with sudo?")
        return

    mouse = BtMouseController(bt_service)
    
    # ---------- Camera & Tracking ----------
    # On Pi, we might need lower resolution if performance is bad, 
    # but Webcam class defaults should be tried first.
    cam = Webcam(index=0, window_name="Hand Tracker (Pi)")
    tracker = HandTracker(max_num_hands=2)

    # ---------- Gesture Detectors ----------
    pinch = PinchDetector(
        pinch_threshold=0.045, 
        release_threshold=0.065, 
        hold_delay_s=0.25
    )

    frame_detector = FrameDetector()
    
    # Modified CopyPaste to use simple callback since we don't have NetBridge
    copy_paste = CopyPasteGestureHandler(
        on_copy=lambda: mouse.copy(),
        on_paste=lambda: mouse.paste()
    )
    
    stop_resume = StopResumeDetector()
    palm_arrow = PalmArrowDetector()
    swipe = SwipeDetector()

    scroll = ScrollDetector(
        finger_raise_threshold=0.005,
        min_scroll_delta=0.0003,
        scroll_sensitivity=150.0,
        finger_distance_threshold=0.08
    )

    # ---------- Event Loop ----------
    events = EventLoop(mouse, screenshot_preview_callback=None)
    events.start()

    # ---------- Screen Size ----------
    screen_w, screen_h = get_virtual_screen_size()
    print(f"Virtual Screen Size: {screen_w}x{screen_h}")

    # ---------- Cursor Mapping ----------
    cursor = CursorMapper(
        screen_w, screen_h,
        roi_x_min=0.05, roi_x_max=0.95,
        roi_y_min=0.10, roi_y_max=0.90,
        gain=2.0,       # Slightly reduced gain for relative movement control
        smoothing=0.15,
        offset_px=(0, 0)
    )

    # ---------- Feature Control ----------
    features_enabled = True 
    print("[INFO] Waiting for Bluetooth connection to Host...")
    print("[INFO] Once connected, raise hand to control cursor.")

    try:
        while True:
            frame = cam.read()
            if frame is None:
                break

            results = tracker.process(frame)
            # Drawing on Pi might handle X11 forwarding or local display (HDMI)
            tracker.draw(frame, results)

            # Check for STOP/RESUME gestures
            stop_resume_event = stop_resume.update(results)
            if stop_resume_event == "STOP":
                features_enabled = False
                print("[INFO] Paused.")
            elif stop_resume_event == "RESUME":
                features_enabled = True
                print("[INFO] Resumed.")

            if features_enabled and results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]
                
                # Hand Label
                hand_label = None
                if results.multi_handedness:
                    for idx, classification in enumerate(results.multi_handedness):
                        if idx < len(results.multi_hand_landmarks) and results.multi_hand_landmarks[idx] == hand:
                            hand_label = classification.classification[0].label
                            break

                copy_paste.process_landmarks(hand)

                swipe_event = swipe.update(hand, hand_label)
                
                if not swipe_event:
                    scroll_events = scroll.update(hand)
                    is_scrolling = scroll.is_scrolling()

                    if not is_scrolling:
                        x, y = cursor.update(hand)
                        # Emit absolute target, controller handles relative logic
                        events.emit(("MOVE", x, y))

                    for ev in scroll_events:
                        events.emit(ev)
                else:
                    events.emit(swipe_event)
                    print(f"[SWIPE] {swipe_event}")

                for ev in pinch.update(hand):
                    events.emit(ev)

                for ev in frame_detector.update(results):
                    events.emit(ev)
                
                palm_event = palm_arrow.update(results)
                if palm_event:
                    events.emit(palm_event)

            # Show frame (this will fail if no display is attached, so we catch it)
            try:
                if cam.show(frame):
                    break
            except Exception:
                pass

    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")

    finally:
        events.stop()
        cam.release()
        # Clean up Bluetooth profile if possible?
        # bt_service.profile.Release() # Not strictly required as process death frees it

if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()










