import time
import threading

from src.recognition.api_client import recognize_face
from src.ui.colors import WHITE

class FaceTracker:
    """Maintains stability state, cooldown, and asynchronous recognition between frames"""

    def __init__(self, cooldown_seconds=4, stability_hold_time=0.3):
        self.cooldown_seconds = cooldown_seconds
        self.stability_hold_time = stability_hold_time

        self.current_bbox = None
        self.box_color = WHITE
        self.face_stable_since = None
        self.last_sent_time = 0
        self.recognition_in_progress = False
        self._color_lock = threading.Lock()

    def clear(self):
        """Called when no face is detected in the current frame"""
        self.current_bbox = None
        self.face_stable_since = None
        with self._color_lock:
            self.box_color = WHITE

    def update(self, bbox):
        """Called when a face is detected; decides whether to trigger recognition"""
        self.current_bbox = bbox
        now = time.time()

        if self.face_stable_since is None:
            self.face_stable_since = now

        is_stable = now - self.face_stable_since >= self.stability_hold_time
        cooldown_ok = now - self.last_sent_time > self.cooldown_seconds

        if is_stable and cooldown_ok and not self.recognition_in_progress:
            self.last_sent_time = now
            self.recognition_in_progress = True
            return True

        return False

    def get_color(self):
        with self._color_lock:
            return self.box_color

    def start_recognition(self, image_bytes, match_color, no_match_color):
        threading.Thread(
            target=self._run_recognition,
            args=(image_bytes, match_color, no_match_color),
            daemon=True,
        ).start()

    def _run_recognition(self, image_bytes, match_color, no_match_color):
        data = recognize_face(image_bytes)
        new_color = match_color if (data and data.get("match")) else no_match_color

        with self._color_lock:
            self.box_color = new_color
            self.recognition_in_progress = False