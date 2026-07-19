from db.database import init_db, insert_person, find_closest_match, log_access
from recognition.embedding import extract_embedding
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from contextlib import asynccontextmanager
from dotenv import load_dotenv

import numpy as np
import mediapipe as mp

import oracledb
import cv2
import os

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Facial Access Control API", lifespan=lifespan)

base_options = mp_python.BaseOptions(model_asset_path=os.getenv("MODEL_PATH"))
detector_options = vision.FaceDetectorOptions(base_options=base_options)
detector = vision.FaceDetector.create_from_options(detector_options)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/enroll")
async def enroll_person(
    name: str = Form(...),
    employee_id: str = Form(...),
    access_level: str = Form(...),
    photo: UploadFile = File(...),
):
    image_bytes = await photo.read()
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB),
    )
    result = detector.detect(mp_image)

    if not result.detections:
        raise HTTPException(status_code=422, detail="No face detected in the uploaded image.")

    if len(result.detections) > 1:
        raise HTTPException(
            status_code=422,
            detail="Multiple faces detected. Upload an image with a single face.",
        )

    try:
        embedding = extract_embedding(image)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    try:
        person_id = insert_person(name, employee_id, access_level, embedding)
    except oracledb.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"employee_id '{employee_id}' is already registered.",
        )

    return {
        "id": person_id,
        "name": name,
        "employee_id": employee_id,
        "access_level": access_level,
        "status": "enrolled",
    }

@app.post("/recognize")
async def recognize_person(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")

    try:
        embedding = extract_embedding(image)
    except ValueError:
        # no recognizable face in the submitted cutout
        log_access(person_id=None, employee_id=None, recognized=False, access_granted=False)
        return {"match": False}

    person = find_closest_match(embedding)

    if person is None:
        log_access(person_id=None, employee_id=None, recognized=False, access_granted=False)
        return {"match": False}

    access_granted = person["access_level"] != "Visitor"

    log_access(
        person_id=person["id"],
        employee_id=person["employee_id"],
        recognized=True,
        access_granted=access_granted,
    )

    return {
        "match": True,
        "name": person["name"],
        "employee_id": person["employee_id"],
        "access_level": person["access_level"],
        "access_granted": access_granted,
    }