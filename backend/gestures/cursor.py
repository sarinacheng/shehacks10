# backend/gestures/cursor.py

INDEX_TIP = 8

def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

class CursorMapper:
    """
    Maps index fingertip -> screen coords using a "virtual trackpad" ROI.
    Adds optional offset so cursor appears beside fingertip.
    """
    def __init__(
        self,
        screen_w,
        screen_h,
        roi_x_min=0.05, roi_x_max=0.95,
        roi_y_min=0.10, roi_y_max=0.90,
        gain=2.2,
        smoothing=0.15,
        offset_px=(0, 0),   # (right, down)
    ):
        self.screen_w = screen_w
        self.screen_h = screen_h

        self.roi_x_min = roi_x_min
        self.roi_x_max = roi_x_max
        self.roi_y_min = roi_y_min
        self.roi_y_max = roi_y_max

        self.gain = gain
        self.smoothing = smoothing

        self.offx, self.offy = offset_px

        self._sx = None
        self._sy = None

    def update(self, hand_landmarks):
        lm = hand_landmarks.landmark[INDEX_TIP]

        # 1) Normalize finger position into ROI -> [0..1]
        nx = (lm.x - self.roi_x_min) / (self.roi_x_max - self.roi_x_min)
        ny = (lm.y - self.roi_y_min) / (self.roi_y_max - self.roi_y_min)
        nx = _clamp(nx, 0.0, 1.0)
        ny = _clamp(ny, 0.0, 1.0)

        # 2) Map to screen pixels
        tx = nx * self.screen_w
        ty = ny * self.screen_h

        # Initialize or apply gain (speed)
        if self._sx is None:
            self._sx, self._sy = tx, ty
        else:
            dx = (tx - self._sx) * self.gain
            dy = (ty - self._sy) * self.gain
            tx = self._sx + dx
            ty = self._sy + dy

        # 3) Apply offset so cursor is beside fingertip
        tx += self.offx
        ty += self.offy

        # 4) Clamp to screen bounds
        tx = _clamp(tx, 0, self.screen_w - 1)
        ty = _clamp(ty, 0, self.screen_h - 1)

        # 5) Smoothing (EMA)
        a = self.smoothing
        self._sx = (1 - a) * self._sx + a * tx
        self._sy = (1 - a) * self._sy + a * ty

        return int(self._sx), int(self._sy)
