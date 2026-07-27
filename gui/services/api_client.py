import requests
from config import API_URL

def enroll_person(name, employee_id, access_level, photos):
    """photos: dictionary in the format {"photo_1": (filename, bytes, mimetype), ...}"""
    data = {
        "name": name,
        "employee_id": employee_id,
        "access_level": access_level,
    }
    return requests.post(
        f"{API_URL}/enroll",
        data=data,
        files=photos,
        timeout=40,
    )

def ask_analytics(message, history):
    return requests.post(
        f"{API_URL}/analytics/chat",
        json={"message": message, "history": history},
        timeout=120,
    )

def get_unknown_faces(limit):
    return requests.get(
        f"{API_URL}/analytics/unknown-faces",
        params={"limit": limit},
        timeout=15,
    )

def regenerate_description(face_id, image_bytes):
    return requests.post(
        f"{API_URL}/analytics/unknown-faces/{face_id}/regenerate-description",
        files={"photo": ("face.jpg", image_bytes, "image/jpeg")},
        timeout=40,
    )