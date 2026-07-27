import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks

from recognition.embedding import extract_embedding
from db.database import log_access, find_closest_match, has_recent_unknown_log
from services.description_tasks import generate_and_save_description

router = APIRouter()

@router.post("/recognize")
async def recognize_person(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    image_bytes = await file.read()
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")

    try:
        embedding = extract_embedding(image)
    except ValueError:
        log_id = log_access(person_id=None, employee_id=None, recognized=False, access_granted=False, face_image_bytes=image_bytes)
        if not has_recent_unknown_log():
            background_tasks.add_task(generate_and_save_description, log_id, image_bytes)
        return {"match": False}

    person = find_closest_match(embedding)

    if person is None:
        log_id = log_access(person_id=None, employee_id=None, recognized=False, access_granted=False, face_image_bytes=image_bytes)
        if not has_recent_unknown_log():
            background_tasks.add_task(generate_and_save_description, log_id, image_bytes)
        return {"match": False}

    access_granted = person["access_level"] != "Visitor"

    log_access(
        person_id=person["id"],
        employee_id=person["employee_id"],
        recognized=True,
        access_granted=access_granted,
        face_image_bytes=image_bytes,
    )

    return {
        "match": True,
        "name": person["name"],
        "employee_id": person["employee_id"],
        "access_level": person["access_level"],
        "access_granted": access_granted,
    }