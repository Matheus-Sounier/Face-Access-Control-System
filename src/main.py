import time
import cv2

from camera.stream import CameraStream
from recognition.detector import detect_faces
from recognition.face_crop import crop_face
from recognition.api_client import recognize_face
from ui.overlay import draw_face_box, draw_result


camera = CameraStream(index=0, use_dshow=True)

last_sent_time = 0
COOLDOWN_LOCAL = 2

while True:
    success, img = camera.read()

    if not success:
        continue

    result = detect_faces(img)

    if result.detections:
        for detection in result.detections:
            bbox = detection.bounding_box

            x, y, w, h = (
                bbox.origin_x,
                bbox.origin_y,
                bbox.width,
                bbox.height,
            )

            img = draw_face_box(img, x, y, w, h)

            now = time.time()

            if now - last_sent_time > COOLDOWN_LOCAL:
                last_sent_time = now

                image_bytes = crop_face(img, x, y, w, h)

                data = recognize_face(image_bytes)

                draw_result(img, x, y, data)

    cv2.imshow("Facial Access Control", img)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()