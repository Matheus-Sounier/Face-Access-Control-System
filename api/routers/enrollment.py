from typing import Optional

import cv2
import numpy as np
import mediapipe as mp
import oracledb
from fastapi import APIRouter, Form, UploadFile, File, HTTPException

from core.face_detector import detector, crop_with_margin
from recognition.embedding import extract_embedding
from db.database import insert_person, insert_face

router = APIRouter()

@router.post("/enroll")
async def enroll_person(
    name: str = Form(...),
    employee_id: str = Form(...),
    access_level: str = Form(...),
    photo_1: UploadFile = File(...),
    photo_2: Optional[UploadFile] = File(None),
    photo_3: Optional[UploadFile] = File(None),
):
    photos = [p for p in (photo_1, photo_2, photo_3) if p is not None]

    processed_faces = []

    for i, photo in enumerate(photos, start=1):
        image_bytes = await photo.read()
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail=f"Photo {i}: invalid file")

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB),
        )
        result = detector.detect(mp_image)

        if not result.detections:
            raise HTTPException(status_code=422, detail=f"Photo {i}: no face detected")

        if len(result.detections) > 1:
            raise HTTPException(status_code=422, detail=f"Photo {i}: more than one face detected")

        try:
            embedding = extract_embedding(image)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=f"Photo {i}: {exc}")

        cropped_bytes = crop_with_margin(image, result.detections[0].bounding_box)
        processed_faces.append((embedding, cropped_bytes))

    try:
        person_id = insert_person(name, employee_id, access_level)
    except oracledb.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"employee_id '{employee_id}' is already registered.",
        )

    for embedding, cropped_bytes in processed_faces:
        insert_face(person_id, embedding, cropped_bytes)

    return {
        "id": person_id,
        "name": name,
        "employee_id": employee_id,
        "access_level": access_level,
        "photos_registered": len(processed_faces),
        "status": "enrolled",
    }