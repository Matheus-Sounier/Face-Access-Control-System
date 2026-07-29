from analytics.face_description import describe_face
from db.database import update_log_description

def generate_and_save_description(log_id: int, image_bytes: bytes):
    try:
        description = describe_face(image_bytes)
        update_log_description(log_id, description)
    except Exception as exc:
        print(f"[face_description] failed for log {log_id}: {exc}")