# backend/main.py

import time
import cv2
import numpy as np
import threading

from camera.webcam import Webcam
from tracking.hand_tracker import HandTracker

from gestures.pinch import PinchDetector
from gestures.scroll import ScrollDetector
from gestures.cursor import CursorMapper
from gestures.copy_paste import CopyPasteGestureHandler
from gestures.frame import FrameDetector

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


def main():
    # ---------- Camera & Tracking ----------
    cam = Webcam(index=0, window_name="Hand Tracker")
    tracker = HandTracker(max_num_hands=2)

    # ---------- Gesture Detectors ----------
    pinch = PinchDetector(
        pinch_threshold=0.030,
        release_threshold=0.040,
        hold_delay_s=0.25
    )

    frame_detector = FrameDetector()
    copy_paste = CopyPasteGestureHandler()

    scroll = ScrollDetector(
        finger_raise_threshold=0.015,
        min_scroll_delta=0.0005,
        scroll_sensitivity=100.0,
        finger_distance_threshold=0.04  # ← tighter = fingers must be closer
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

    try:
        while True:
            frame = cam.read()
            if frame is None:
                break

            results = tracker.process(frame)
            tracker.draw(frame, results)

            if results.multi_hand_landmarks:
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










