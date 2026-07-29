from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from db.database import init_db
from routers import health, enrollment, recognition, analytics

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Facial Access Control API", lifespan=lifespan)

app.include_router(health.router)
app.include_router(enrollment.router)
app.include_router(recognition.router)
app.include_router(analytics.router)