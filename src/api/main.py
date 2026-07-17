from fastapi import FastAPI, Form, UploadFile, File, HTTPException
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="Facial Access Control API")

base_options = mp_python.BaseOptions(model_asset_path=os.getenv("MODEL_PATH"))
detector_options = vision.FaceDetectorOptions(base_options=base_options)
detector = vision.FaceDetector.create_from_options(detector_options)


@app.get("/health")
def health_check():
    return {"status": "ok"}