import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database.session import init_db
from .api.router import router as api_router
from .web_ui.views import router as ui_router
from .admin.views import router as admin_view_router
from .admin.router import router as admin_api_router
from .tracking.router import tracking_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.FileHandler(settings.log_file, encoding="utf-8"), logging.StreamHandler()],
    )
    init_db()
    logging.getLogger("uvicorn").info("Database initialized")
    yield


app = FastAPI(title="企业智能搜索系统", version="1.0.0", lifespan=lifespan)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "web_ui", "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(ui_router)
app.include_router(admin_view_router)
app.include_router(admin_api_router)
app.include_router(tracking_router)
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
