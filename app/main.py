"""Entry point aplikasi FastAPI Self-Photo Studio."""

from fastapi import FastAPI

from app.db import init_db
from app.api import frames, health, sessions
from app.services.frame_service import seed_frames

app = FastAPI(
    title="Self-Photo Studio API",
    version="0.1.0",
    description="Backend kiosk self-photo studio (MVP).",
)

# Daftarkan router
app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(frames.router)


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
