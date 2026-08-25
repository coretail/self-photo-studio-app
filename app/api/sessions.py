"""Endpoint API terkait session foto."""

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from app.db import get_db
from app.services.session_service import (
    SessionValidationError,
    create_dummy_session,
    validate_session,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SessionValidateRequest(BaseModel):
    session_code: str


@router.post("/validate")
def validate_session_endpoint(
    payload: SessionValidateRequest, db: DBSession = Depends(get_db)
):
    """Validasi session_code klien.

    - 200 : session valid, mengembalikan info session + expires_at
    - 404 : session tidak ditemukan (DB atau folder)
    - 410 : session sudah expired
    """
    try:
        session = validate_session(db, payload.session_code)
    except SessionValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    expires_at = session.expires_at
    photos = []
    folder = Path(session.folder_path)
    if folder.is_dir():
        photos = sorted(p.name for p in folder.glob("photo_*.jpg"))

    return {
        "valid": True,
        "session": {
            "id": session.id,
            "session_code": session.session_code,
            "folder_path": session.folder_path,
            "status": session.status,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "expires_at": expires_at.isoformat() if expires_at else None,
        },
        "photos": photos,
    }


@router.post("/dummy")
def create_dummy_session_endpoint(
    num_photos: int = 4, db: DBSession = Depends(get_db)
):
    """[Testing] Buat session dummy seolah-olah dibuat mesin foto studio.

    Untuk pengujian manual endpoint /validate.
    """
    session = create_dummy_session(db, num_photos=max(1, min(num_photos, 8)))
    return {
        "message": "Dummy session berhasil dibuat.",
        "session_code": session.session_code,
        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
        "num_photos": max(1, min(num_photos, 8)),
    }
