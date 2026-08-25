"""Service: pembuatan & validasi session foto (PRD section 4.1).

Session dibuat oleh sistem mesin foto studio. Karena integrasi mesin foto
belum ada, tersedia generator dummy untuk testing manual.
"""

import secrets
import sqlite3  # noqa: F401 (hanya untuk type hint kecil bila diperlukan)
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image
from sqlalchemy.orm import Session as DBSession

from app.config import SESSION_EXPIRY_MINUTES, SESSIONS_DIR
from app.models.session import Session


class SessionValidationError(Exception):
    """Base error validasi session."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def generate_session_code() -> str:
    """Generate session_code unik, contoh: SES-A1B2C3D4."""
    return f"SES-{secrets.token_hex(4).upper()}"


def create_dummy_session(db: DBSession, num_photos: int = 4) -> Session:
    """Simulasi pembuatan session oleh mesin foto studio (dummy).

    - Generate session_code baru
    - Buat folder data/sessions/{session_code}/
    - Isi dengan `num_photos` gambar placeholder warna solid
    - Simpan record session ke database dengan expiry default
    """
    code = generate_session_code()
    folder = SESSIONS_DIR / code
    folder.mkdir(parents=True, exist_ok=True)

    # Warna solid berbeda per foto agar mudah dibedakan saat testing
    palette = [
        (220, 60, 60),    # merah
        (60, 160, 80),    # hijau
        (50, 90, 200),    # biru
        (230, 180, 40),   # kuning
        (150, 60, 200),   # ungu
        (240, 130, 30),   # oranye
        (30, 190, 190),   # teal
        (90, 90, 100),    # abu gelap
    ]
    for i in range(1, num_photos + 1):
        color = palette[(i - 1) % len(palette)]
        img = Image.new("RGB", (600, 800), color)
        img.save(folder / f"photo_{i:02d}.jpg", "JPEG", quality=90)

    now_utc = datetime.now(timezone.utc)
    session = Session(
        session_code=code,
        folder_path=str(folder),
        created_at=now_utc,
        expires_at=now_utc + timedelta(minutes=SESSION_EXPIRY_MINUTES),
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def validate_session(db: DBSession, session_code: str) -> Session:
    """Validasi session_code.

    Raises:
        SessionValidationError: 404 jika tidak ditemukan (DB/folder),
                                410 jika sudah expired.
    Returns:
        Instance Session jika valid.
    """
    session = (
        db.query(Session).filter(Session.session_code == session_code).first()
    )
    if session is None:
        raise SessionValidationError(
            status_code=404,
            detail=f"Session '{session_code}' tidak ditemukan.",
        )

    # Cek folder di filesystem
    if not Path(session.folder_path).is_dir():
        raise SessionValidationError(
            status_code=404,
            detail=f"Folder foto untuk session '{session_code}' tidak ditemukan di server.",
        )

    # Cek expiry (bandingkan expires_at dengan waktu sekarang)
    expires_at = session.expires_at
    if expires_at is not None:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            session.status = "expired"
            db.commit()
            raise SessionValidationError(
                status_code=410,
                detail=f"Session '{session_code}' sudah kedaluwarsa pada {expires_at.isoformat()}.",
            )

    return session
