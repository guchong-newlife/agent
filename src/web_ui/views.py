from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter()

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@router.get("/")
async def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
