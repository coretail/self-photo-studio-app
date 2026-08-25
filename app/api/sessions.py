"""Endpoint API terkait session foto."""

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from app.db import get_db
from app.models.selection import Selection
from app.services.session_service import (
    SessionValidationError,
    create_dummy_session,
    validate_session as validate_session_code,
)
from app.services.photo_service import list_session_photos, select_photos

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


@router.get("/{session_code}/photos")
def list_photos_endpoint(session_code: str, db: DBSession = Depends(get_db)):
    """List foto dalam session (validasi session + expiry dulu).

    - 200 : daftar foto (filename, url, size_bytes)
    - 404 : session/folder tidak ditemukan
    - 410 : session expired
    """
    try:
        session = validate_session_code(db, session_code)
    except SessionValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    return {
        "session_code": session.session_code,
        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
        "photos": list_session_photos(session),
    }


class SelectPhotosRequest(BaseModel):
    frame_id: int
    filenames: list[str]


@router.post("/{session_code}/select-photos")
def select_photos_endpoint(
    session_code: str, payload: SelectPhotosRequest, db: DBSession = Depends(get_db)
):
    """Simpan pilihan foto klien untuk frame tertentu.

    - 200 : pilihan tersimpan
    - 404/410 : session tidak valid/expired
    - 400 : jumlah foto tidak sesuai slot frame / filename tidak ada
    """
    try:
        result = select_photos(db, session_code, payload.frame_id, payload.filenames)
    except SessionValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@router.get("/{session_code}/selection")
def get_selection_endpoint(session_code: str, db: DBSession = Depends(get_db)):
    """Ambil pilihan foto tersimpan untuk session (dipakai halaman adjust)."""
    import json

    try:
        session = validate_session_code(db, session_code)
    except SessionValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    selection = (
        db.query(Selection).filter(Selection.session_id == session.id).first()
    )
    if selection is None:
        raise HTTPException(
            status_code=404,
            detail="Belum ada pilihan foto untuk session ini.",
        )
    return {
        "session_code": session.session_code,
        "frame_id": selection.frame_id,
        "selected_photos": json.loads(selection.photos_json),
        "adjustments": json.loads(selection.adjustments_json)
        if selection.adjustments_json
        else None,
    }


class AdjustPhotosRequest(BaseModel):
    """Payload konfirmasi Preview & Adjust: posisi/zoom final tiap foto."""

    frame_id: int
    # contoh item: {"filename": "photo_01.jpg", "x": 100, "y": 250, "scale": 1.2}
    adjustments: list[dict]


@router.post("/{session_code}/adjust-photos")
def adjust_photos_endpoint(
    session_code: str, payload: AdjustPhotosRequest, db: DBSession = Depends(get_db)
):
    """Simpan posisi/zoom final tiap foto (dari halaman Preview & Adjust).

    Disimpan di tabel selections yang sama (kolom adjustments_json) karena
    adjustment 1:1 dengan selection - tidak perlu tabel baru.
    Koordinat memakai ruang pixel cetak (print_width_px x print_height_px).
    """
    import json

    try:
        session = validate_session_code(db, session_code)
    except SessionValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    selection = (
        db.query(Selection).filter(Selection.session_id == session.id).first()
    )
    if selection is None:
        raise HTTPException(
            status_code=404,
            detail="Belum ada pilihan foto untuk session ini. Pilih foto dulu.",
        )
    if selection.frame_id != payload.frame_id:
        raise HTTPException(
            status_code=400,
            detail="Frame_id tidak cocok dengan pilihan foto yang tersimpan.",
        )

    filenames = json.loads(selection.photos_json)
    by_name = {a.get("filename"): a for a in payload.adjustments}
    missing = [f for f in filenames if f not in by_name]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Adjustment belum lengkap, kurang: {', '.join(missing)}",
        )

    # Simpan hanya field yang dibutuhkan, urut sesuai urutan pemilihan
    clean = [
        {
            "filename": f,
            "x": float(by_name[f].get("x", 0)),
            "y": float(by_name[f].get("y", 0)),
            "scale": float(by_name[f].get("scale", 1)),
        }
        for f in filenames
    ]
    selection.adjustments_json = json.dumps(clean)
    db.commit()

    return {
        "session_code": session.session_code,
        "frame_id": payload.frame_id,
        "saved": len(clean),
        "message": "Penyesuaian posisi/zoom berhasil disimpan.",
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

