import cv2

from src.camera.stream import CameraStream
from src.recognition.detector import detect_faces
from src.recognition.face_crop import crop_face
from src.recognition.face_tracker import FaceTracker
from src.ui.overlay import draw_face_box
from src.ui.colors import GREEN, RED

camera = CameraStream(index=0, use_dshow=True)
tracker = FaceTracker(cooldown_seconds=4, stability_hold_time=0.3)

frame_count = 0
PROCESS_EVERY_N_FRAMES = 3

while True:
    success, img = camera.read()
    if not success:
        continue

    frame_count += 1
    run_detection = frame_count % PROCESS_EVERY_N_FRAMES == 0

    if run_detection:
        result = detect_faces(img)

        if result.detections:
            bbox = result.detections[0].bounding_box
            bbox_tuple = (bbox.origin_x, bbox.origin_y, bbox.width, bbox.height)

            should_recognize = tracker.update(bbox_tuple)

            if should_recognize:
                x, y, w, h = bbox_tuple
                image_bytes = crop_face(img, x, y, w, h)
                tracker.start_recognition(image_bytes, match_color=GREEN, no_match_color=RED)
        else:
            tracker.clear()

    if tracker.current_bbox is not None:
        x, y, w, h = tracker.current_bbox
        img = draw_face_box(img, x, y, w, h, color=tracker.get_color())

    cv2.imshow("Facial Access Control", img)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()