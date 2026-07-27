import os

import cv2
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

base_options = mp_python.BaseOptions(model_asset_path=os.getenv("MODEL_PATH"))
detector_options = vision.FaceDetectorOptions(base_options=base_options)
detector = vision.FaceDetector.create_from_options(detector_options)

def crop_with_margin(img, bbox, margin: float = 0.4):
    img_h, img_w = img.shape[:2]
    x, y, w, h = bbox.origin_x, bbox.origin_y, bbox.width, bbox.height

    pad_w = int(w * margin)
    pad_h = int(h * margin)

    x1 = max(0, x - pad_w)
    y1 = max(0, y - pad_h)
    x2 = min(img_w, x + w + pad_w)
    y2 = min(img_h, y + h + pad_h)

    face_crop = img[y1:y2, x1:x2]
    _, buffer = cv2.imencode(".jpg", face_crop)
    return buffer.tobytes()