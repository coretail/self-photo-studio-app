"""Entry point aplikasi FastAPI Self-Photo Studio."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import DATA_DIR
from app.db import init_db
from app.api import frames, health, sessions
from app.services.frame_service import seed_frames

app = FastAPI(
    title="Self-Photo Studio API",
    version="0.1.0",
    description="Backend kiosk self-photo studio (MVP).",
)

# Serve foto session: /media/sessions/{session_code}/{filename}
DATA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(DATA_DIR)), name="media")

# Serve asset frontend
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static",
)

# Daftarkan router
app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(frames.router)


@app.get("/", include_in_schema=False)
def landing_page():
    """Halaman Landing/Start: input session ID + pilih frame."""
    from fastapi.responses import FileResponse

    return FileResponse(Path(__file__).parent / "templates" / "landing.html")


@app.get("/adjust", include_in_schema=False)
def adjust_page():
    """Halaman Preview & Adjust (canvas Fabric.js)."""
    from fastapi.responses import FileResponse

    return FileResponse(Path(__file__).parent / "templates" / "adjust.html")


@app.get("/picker", include_in_schema=False)
def picker_page():
    """Halaman photo picker (frontend sederhana)."""
    from pathlib import Path

    from fastapi.responses import FileResponse

    return FileResponse(Path(__file__).parent / "templates" / "picker.html")


@app.on_event("startup")
def on_startup() -> None:
    """Buat tabel database & seed data frame awal saat aplikasi dijalankan."""
    from app.db import SessionLocal

    init_db()
    db = SessionLocal()
    try:
        seed_frames(db)
    finally:
        db.close()
