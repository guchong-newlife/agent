import os
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
TRACKING_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tracking", "static")


@router.get("/admin")
async def admin_page():
    return FileResponse(os.path.join(STATIC_DIR, "admin.html"))


@router.get("/admin/tracking")
async def tracking_admin_page():
    return FileResponse(os.path.join(TRACKING_DIR, "tracking_admin.html"))
