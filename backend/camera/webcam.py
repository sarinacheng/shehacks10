import cv2

class Webcam:
    def __init__(self, index=0, window_name="Camera"):
        self.cap = cv2.VideoCapture(index)
        self.window_name = window_name

    def read(self):
        if not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        if not ret:
            return None
        return cv2.flip(frame, 1)

    def show(self, frame):
        cv2.imshow(self.window_name, frame)
        key = cv2.waitKey(1) & 0xFF
        return key in (27, ord("q"))  # ESC or q

    def release(self):
        if self.cap:
            self.cap.release()
        import cv2
        cv2.destroyAllWindows()
