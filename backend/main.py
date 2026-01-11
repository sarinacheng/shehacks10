# backend/main.py

import time
import cv2
import numpy as np
import threading
import subprocess

from camera.webcam import Webcam
from tracking.hand_tracker import HandTracker

from gestures.pinch import PinchDetector
from gestures.scroll import ScrollDetector
from gestures.cursor import CursorMapper
from gestures.copy_paste import CopyPasteGestureHandler
from gestures.frame import FrameDetector
from gestures.stop_resume import StopResumeDetector

from input.mouse_controller import MouseController
from input.event_loop import EventLoop

from Quartz import CGDisplayBounds, CGMainDisplayID

try:
    from AppKit import (
        NSWindow, NSBackingStoreBuffered, NSWindowStyleMaskBorderless,
        NSColor, NSApplication, NSDate, NSView
    )
    HAS_APPKIT = True
except ImportError:
    try:
        from Cocoa import (
            NSWindow, NSBackingStoreBuffered, NSWindowStyleMaskBorderless,
            NSColor, NSApplication, NSDate, NSView
        )
        HAS_APPKIT = True
    except ImportError:
        HAS_APPKIT = False
        print("Warning: AppKit/Cocoa not available - screenshot preview will not work")


def get_screen_size():
    b = CGDisplayBounds(CGMainDisplayID())
    return int(b.size.width), int(b.size.height)


def show_notification(title: str, message: str) -> None:
    """Show both a notification banner and pop-up dialog"""
    # Escape quotes and special characters
    escaped_message = message.replace('"', '\\"').replace('\\', '\\\\')
    escaped_title = title.replace('"', '\\"').replace('\\', '\\\\')
    
    # Notification banner (top right corner)
    notification_script = f'''
    display notification "{escaped_message}" with title "{escaped_title}" sound name "Glass"
    '''
    
    # Pop-up dialog (center of screen)
    dialog_script = f'''
    display dialog "{escaped_message}" with title "{escaped_title}" buttons {{"OK"}} default button "OK" giving up after 2
    '''
    
    # Show both
    subprocess.Popen(["osascript", "-e", notification_script], 
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.Popen(["osascript", "-e", dialog_script], 
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    # ---------- Camera & Tracking ----------
    cam = Webcam(index=0, window_name="Hand Tracker")
    tracker = HandTracker(max_num_hands=2)

    # ---------- Gesture Detectors ----------
    pinch = PinchDetector(
        pinch_threshold=0.065,  # Slightly less sensitive
        release_threshold=0.085,  # Slightly less forgiving release
        hold_delay_s=0.12  # Slightly slower click response
    )

    frame_detector = FrameDetector()
    copy_paste = CopyPasteGestureHandler()
    stop_resume = StopResumeDetector()

    scroll = ScrollDetector(
        finger_raise_threshold=0.005,  # More lenient - works with fingers side by side
        min_scroll_delta=0.0003,       # More responsive
        scroll_sensitivity=150.0,      # Increased sensitivity
        finger_distance_threshold=0.08  # More lenient - fingers can be slightly apart
    )

    # ---------- Mouse + Event Loop ----------
    mouse = MouseController()
    events = EventLoop(mouse, screenshot_preview_callback=None)
    events.start()

    # ---------- Screen Size ----------
    screen_w, screen_h = get_screen_size()
    print("screen:", screen_w, screen_h)

    # ---------- Cursor Mapping ----------
    cursor = CursorMapper(
        screen_w, screen_h,
        roi_x_min=0.05, roi_x_max=0.95,
        roi_y_min=0.10, roi_y_max=0.90,
        gain=2.2,
        smoothing=0.15,
        offset_px=(5, 0)
    )

    # ---------- Feature Control ----------
    features_enabled = True  # Start with features enabled
    print("[INFO] Hand gesture features ENABLED. Raise both palms to disable, make semi-circles with both hands to resume.")

    try:
        while True:
            frame = cam.read()
            if frame is None:
                break

            results = tracker.process(frame)
            tracker.draw(frame, results)

            # Check for STOP/RESUME gestures first (works regardless of features_enabled state)
            stop_resume_event = stop_resume.update(results)
            if stop_resume_event == "STOP":
                features_enabled = False
                print("[INFO] Features DISABLED. Make semi-circles with both hands to resume.")
                show_notification("Paused!", "Paused!")
            elif stop_resume_event == "RESUME":
                features_enabled = True
                print("[INFO] Features ENABLED. Raise both palms to disable.")
                show_notification("Resumed!", "Resumed!")

            # Only process other gestures if features are enabled
            if features_enabled and results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]

                # Copy/Paste handler works internally (no events needed)
                copy_paste.process_landmarks(hand)

                # Scroll updates
                scroll_events = scroll.update(hand)
                is_scrolling = scroll.is_scrolling()

                # Cursor move only when not scrolling
                if not is_scrolling:
                    x, y = cursor.update(hand)
                    events.emit(("MOVE", x, y))

                # Pinch click/drag
                for ev in pinch.update(hand):
                    events.emit(ev)

                # Scroll events
                for ev in scroll_events:
                    events.emit(ev)

                # Frame gestures
                for ev in frame_detector.update(results):
                    events.emit(ev)

            if cam.show(frame):
                break

    except KeyboardInterrupt:
        print("\n[INFO] Shutting down hover mouse...")

    finally:
        events.stop()
        cam.release()


if __name__ == "__main__":
    main()










