import cv2

def crop_face(img, x, y, w, h):
    face_crop = img[y:y + h, x:x + w]

    _, buffer = cv2.imencode(".jpg", face_crop)

    return buffer.tobytes()