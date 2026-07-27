import base64

from fastapi import APIRouter, UploadFile, File, HTTPException

from schemas import ChatRequest
from db.database import get_unknown_faces, update_log_description
from analytics.face_description import describe_face
from analytics.sql_agent import run_chat

router = APIRouter()

@router.get("/analytics/unknown-faces")
def list_unknown_faces(limit: int = 40):
    faces = get_unknown_faces(limit=limit)
    return {
        "faces": [
            {
                "id": f["id"],
                "description": f["description"],
                "attempted_at": f["attempted_at"],
                "image_base64": (
                    base64.b64encode(f["image_bytes"]).decode("utf-8")
                    if f["image_bytes"] else None
                ),
            }
            for f in faces
        ]
    }

@router.post("/analytics/unknown-faces/{log_id}/regenerate-description")
async def regenerate_description(log_id: int, photo: UploadFile = File(...)):
    image_bytes = await photo.read()
    try:
        description = describe_face(image_bytes)
        update_log_description(log_id, description)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to generate description: {exc}")
    return {"status": "ok", "description": description}

@router.post("/analytics/chat")
async def analytics_chat(payload: ChatRequest):
    history = [turn.dict() for turn in payload.history]
    reply, new_history = run_chat(payload.message, history)
    return {"reply": reply, "history": new_history}