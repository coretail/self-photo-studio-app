"""Entry point aplikasi FastAPI Self-Photo Studio."""

from fastapi import FastAPI

from app.db import init_db
from app.api import health, sessions

app = FastAPI(
    title="Self-Photo Studio API",
    version="0.1.0",
    description="Backend kiosk self-photo studio (MVP).",
)

# Daftarkan router
app.include_router(health.router)
app.include_router(sessions.router)


@app.on_event("startup")
def on_startup() -> None:
    """Buat tabel database saat aplikasi pertama kali dijalankan."""
    init_db()
