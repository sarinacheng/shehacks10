# backend/main.py

import time
import cv2
import numpy as np

from camera.webcam import Webcam
from tracking.hand_tracker import HandTracker

from gestures.pinch import PinchDetector
from gestures.scroll import ScrollDetector
from gestures.cursor import CursorMapper
from gestures.copy_paste import CopyPasteDetector
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
import threading

def get_screen_size():
    b = CGDisplayBounds(CGMainDisplayID())
    return int(b.size.width), int(b.size.height)

def show_screenshot_preview(image, filename):
    """Show a simple popup notification that screenshot was taken"""
    print(f"📸 Screenshot taken! File: {filename}")
    print(f"show_screenshot_preview called - image={image is not None}, filename={filename}")
    
    # First, try macOS system notification (most reliable)
    try:
        import subprocess
        result = subprocess.run([
            'osascript', '-e',
            f'display notification "Screenshot saved!" with title "📸 Screenshot Taken"'
        ], capture_output=True, timeout=2)
        print(f"System notification result: {result.returncode}")
    except Exception as e:
        print(f"System notification failed: {e}")
    
    # Always show a simple text notification first
    def _show_simple_notification():
        try:
            if HAS_APPKIT:
                app = NSApplication.sharedApplication()
                if not app.isRunning():
                    app.finishLaunching()
                app.activateIgnoringOtherApps_(True)
                
                screen_w, screen_h = get_screen_size()
                
                # Create a simple text notification window
                from AppKit import NSTextField, NSFont, NSColor, NSMutableParagraphStyle, NSTextAlignmentCenter
                
                # Window size for notification
                notif_width = 300
                notif_height = 80
                margin = 20
                x = screen_w - notif_width - margin
                y = margin
                
                # Create window
                notif_window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
                    ((x, y), (notif_width, notif_height)),
                    NSWindowStyleMaskBorderless,
                    NSBackingStoreBuffered,
                    False
                )
                
                # Set window properties
                try:
                    from AppKit import NSWindowLevelScreenSaver
                    notif_window.setLevel_(NSWindowLevelScreenSaver + 1)
                except:
                    notif_window.setLevel_(NSWindowLevelFloating + 1000)
                
                notif_window.setOpaque_(False)
                notif_window.setBackgroundColor_(NSColor.clearColor())
                notif_window.setHasShadow_(True)
                notif_window.setIgnoresMouseEvents_(True)
                
                # Create text field with message
                text_field = NSTextField.alloc().initWithFrame_(
                    ((10, 10), (notif_width - 20, notif_height - 20))
                )
                text_field.setStringValue_("📸 Screenshot Saved!")
                text_field.setBezeled_(False)
                text_field.setDrawsBackground_(False)
                text_field.setEditable_(False)
                text_field.setSelectable_(False)
                
                # Style the text
                font = NSFont.boldSystemFontOfSize_(16.0)
                text_field.setFont_(font)
                text_field.setTextColor_(NSColor.whiteColor())
                
                # Center align
                paragraph_style = NSMutableParagraphStyle.alloc().init()
                paragraph_style.setAlignment_(NSTextAlignmentCenter)
                
                # Create background view
                bg_view = NSView.alloc().initWithFrame_(
                    ((0, 0), (notif_width, notif_height))
                )
                bg_view.setWantsLayer_(True)
                try:
                    bg_view.layer().setBackgroundColor_(NSColor.blackColor().colorWithAlphaComponent_(0.8).CGColor())
                    bg_view.layer().setCornerRadius_(10.0)
                except:
                    bg_view.setBackgroundColor_(NSColor.blackColor())
                
                bg_view.addSubview_(text_field)
                notif_window.contentView().addSubview_(bg_view)
                
                # Show window
                notif_window.setAlphaValue_(0.0)
                notif_window.makeKeyAndOrderFront_(None)
                notif_window.orderFrontRegardless()
                
                import time
                # Fade in
                for i in range(10):
                    notif_window.setAlphaValue_(i / 10.0)
                    app.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.02))
                    time.sleep(0.02)
                
                # Stay visible
                time.sleep(2.0)
                
                # Fade out
                for i in range(10):
                    notif_window.setAlphaValue_(1.0 - (i / 10.0))
                    app.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.02))
                    time.sleep(0.02)
                
                notif_window.close()
                print("Notification window closed")
            else:
                print("AppKit not available - showing text notification only")
        except Exception as e:
            print(f"Notification error: {e}")
            import traceback
            traceback.print_exc()
    
    # Show notification
    thread = threading.Thread(target=_show_simple_notification, daemon=True)
    thread.start()
    
    # Also try to show thumbnail if AppKit is available
    if not HAS_APPKIT:
        print("AppKit not available - cannot show screenshot preview thumbnail")
        return
    
    def _show_preview():
        print("_show_preview function started")
        try:
            try:
                from AppKit import (
                    NSImageView, NSImage, NSRect, NSPoint, NSSize, NSView,
                    NSWindowCollectionBehaviorCanJoinAllSpaces,
                    NSWindowCollectionBehaviorStationary,
                    NSWindowLevelFloating
                )
            except ImportError:
                try:
                    from Cocoa import (
                        NSImageView, NSImage, NSRect, NSPoint, NSSize, NSView,
                        NSWindowCollectionBehaviorCanJoinAllSpaces,
                        NSWindowCollectionBehaviorStationary,
                        NSWindowLevelFloating
                    )
                except ImportError:
                    # Fallback without background view
                    from AppKit import NSImageView, NSImage, NSRect, NSPoint, NSSize
                    NSView = None
                    NSWindowCollectionBehaviorCanJoinAllSpaces = 1 << 0
                    NSWindowCollectionBehaviorStationary = 1 << 4
                    NSWindowLevelFloating = 3
            
            print("Creating screenshot preview window...")
            # Initialize NSApplication properly
            app = NSApplication.sharedApplication()
            if not app.isRunning():
                app.finishLaunching()
            app.activateIgnoringOtherApps_(True)  # Activate app to show window
            
            # Ensure we're on the main thread for UI operations
            import threading
            if threading.current_thread() != threading.main_thread():
                print("Warning: Not on main thread, window might not appear")
            
            print(f"NSApplication initialized, isRunning={app.isRunning()}, mainThread={threading.current_thread() == threading.main_thread()}")
            
            screen_w, screen_h = get_screen_size()
            print(f"Screen size: {screen_w}x{screen_h}")
            
            # Thumbnail size (similar to macOS - slightly smaller)
            thumb_width = 280
            thumb_height = 180
            margin = 20
            
            # Calculate position (bottom right corner)
            # macOS NSWindow coordinates: origin at bottom-left, y increases upward
            x = screen_w - thumb_width - margin
            y = margin  # Distance from bottom
            
            print(f"Creating window at position: ({x}, {y}), size: {thumb_width}x{thumb_height}")
            
            # Create borderless window with proper settings
            window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
                ((x, y), (thumb_width, thumb_height)),
                NSWindowStyleMaskBorderless,
                NSBackingStoreBuffered,
                False
            )
            
            # Set window to be on top of everything
            # Use a very high level - try both floating and screen saver levels
            try:
                from AppKit import NSWindowLevelScreenSaver
                window.setLevel_(NSWindowLevelScreenSaver + 1)  # Above screen saver
            except:
                window.setLevel_(NSWindowLevelFloating + 1000)  # Very high floating level
            print(f"Window level set to: {window.level()}")
            window.setCollectionBehavior_(
                NSWindowCollectionBehaviorCanJoinAllSpaces | 
                NSWindowCollectionBehaviorStationary
            )
            window.setOpaque_(False)
            window.setBackgroundColor_(NSColor.clearColor())
            window.setHasShadow_(True)
            window.setIgnoresMouseEvents_(True)  # Ignore mouse events - just visual indicator
            window.setMovable_(False)  # Don't allow moving
            window.setMovableByWindowBackground_(False)
            
            # Convert PIL image to NSImage
            import io
            img_buffer = io.BytesIO()
            # Resize image for thumbnail
            thumb_image = image.copy()
            thumb_image.thumbnail((thumb_width, thumb_height), resample=3)  # Use high quality
            thumb_image.save(img_buffer, format='PNG')
            img_data = img_buffer.getvalue()
            ns_image = NSImage.alloc().initWithData_(img_data)
            
            if ns_image is None:
                print("Failed to create NSImage from screenshot")
                return
            
            print("Creating image view...")
            # Create image view
            image_view = NSImageView.alloc().initWithFrame_(
                NSRect(NSPoint(0, 0), NSSize(thumb_width, thumb_height))
            )
            image_view.setImage_(ns_image)
            image_view.setImageScaling_(1)  # Scale to fit (1 = scale proportionally)
            image_view.setImageAlignment_(2)  # Center alignment
            
            # Create container view with white background and rounded corners
            container_view = NSView.alloc().initWithFrame_(
                NSRect(NSPoint(0, 0), NSSize(thumb_width, thumb_height))
            )
            container_view.setWantsLayer_(True)
            
            try:
                # Set up layer with white background and rounded corners (macOS style)
                layer = container_view.layer()
                layer.setBackgroundColor_(NSColor.whiteColor().CGColor())
                layer.setCornerRadius_(10.0)  # Rounded corners like macOS
                layer.setMasksToBounds_(True)
            except Exception as e:
                print(f"Could not set layer properties: {e}")
                # Fallback: just use white background
                container_view.setBackgroundColor_(NSColor.whiteColor())
            
            # Add image view to container (with padding for rounded corners)
            padding = 5
            image_frame = NSRect(
                NSPoint(padding, padding), 
                NSSize(thumb_width - 2*padding, thumb_height - 2*padding)
            )
            image_view.setFrame_(image_frame)
            
            container_view.addSubview_(image_view)
            window.contentView().addSubview_(container_view)
            
            # Just a visual indicator - no click handling needed
            
            print("Showing window...")
            # Start invisible and fade in
            window.setAlphaValue_(0.0)
            
            # Show window - use multiple methods to ensure it appears
            window.makeKeyAndOrderFront_(None)
            window.orderFrontRegardless()  # Force to front
            window.orderFront_(None)  # Another way to bring to front
            window.display()  # Force display update
            
            # Process events multiple times to ensure window appears
            for _ in range(5):
                app.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.02))
            
            print(f"Window created, isVisible={window.isVisible()}, alpha={window.alphaValue()}, frame={window.frame()}")
            print(f"Window on screen: {window.isOnActiveSpace()}, isKey={window.isKeyWindow()}")
            
            # If window is not visible, try making it visible immediately
            if not window.isVisible():
                print("WARNING: Window is not visible! Trying to force visibility...")
                window.setAlphaValue_(1.0)  # Make fully visible for testing
                window.orderFrontRegardless()
                app.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))
                print(f"After force: isVisible={window.isVisible()}")
            
            # Fade in animation (smooth like macOS)
            import time
            print("Fading in...")
            fade_steps = 15
            for i in range(fade_steps):
                alpha = i / float(fade_steps)
                window.setAlphaValue_(alpha)
                # Process events during animation to ensure smooth fade
                app.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.016))  # ~60fps
                time.sleep(0.016)
            
            window.setAlphaValue_(1.0)  # Ensure fully visible
            app.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.05))
            print(f"Fade in complete, alpha={window.alphaValue()}, isVisible={window.isVisible()}")
            
            print("Preview visible, waiting 3 seconds...")
            # Stay visible for 3 seconds (process events periodically)
            print("Preview visible, waiting 3 seconds...")
            for _ in range(30):  # 30 * 0.1 = 3 seconds
                app.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))
                time.sleep(0.1)
            
            # Fade out
            print("Fading out...")
            for i in range(20):
                alpha = 1.0 - (i / 20.0)
                window.setAlphaValue_(alpha)
                app.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.02))
                time.sleep(0.02)
            print("Fade out complete")
            
            print("Closing preview window...")
            window.close()
        except Exception as e:
            print(f"Screenshot preview error: {e}")
            import traceback
            traceback.print_exc()
    
    # Run preview in a separate thread
    # Note: macOS UI operations should ideally be on main thread, but this should still work
    thread = threading.Thread(target=_show_preview, daemon=True)
    thread.start()
    print(f"Started preview thread: {thread.name}")


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


    scroll = ScrollDetector(
        finger_raise_threshold=0.015,
        min_scroll_delta=0.0005,  # Very small threshold for smooth, continuous scrolling
        scroll_sensitivity=100.0  # High sensitivity: small hand movement = large page scroll
    )

    # ---------- Mouse + Event Loop ----------
    mouse = MouseController()
    # No need for screenshot preview callback since macOS handles it
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

                # Check for scroll events first to update scrolling state
                scroll_events = scroll.update(hand)
                is_scrolling = scroll.is_scrolling()

                # Only move cursor if not scrolling
                if not is_scrolling:
                    x, y = cursor.update(hand)
                    events.emit(("MOVE", x, y))

                # pinch click events (supports PINCH_START and PINCH_END for hold/release)
                for ev in pinch.update(hand):
                    events.emit(ev)

                # scroll events (two-finger scroll)
                for ev in scroll_events:
                    print(f"Scroll event: {ev}")  # Debug output
                    events.emit(ev)

                # ---------- FRAME GESTURES ----------
                for ev in frame_detector.update(results):
                    if ev == "SCREENSHOT":
                        print(f"Main: Emitting SCREENSHOT event")
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
