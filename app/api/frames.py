"""Endpoint API terkait katalog frame."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from app.db import get_db
from app.services import frame_service

router = APIRouter(prefix="/api/frames", tags=["frames"])


class PhotoSelectionRequest(BaseModel):
    selected_photo_count: int


def _serialize(frame) -> dict:
    return {
        "id": frame.id,
        "name": frame.name,
        "type": frame.type,
        "min_photos": frame.min_photos,
        "max_photos": frame.max_photos,
        "print_width_px": frame.print_width_px,
        "print_height_px": frame.print_height_px,
        "dpi": frame.dpi,
        "is_active": frame.is_active,
    }


@router.get("")
def list_frames(db: DBSession = Depends(get_db)):
    """Daftar semua frame aktif beserta batasan min/max foto."""
    frames = frame_service.get_active_frames(db)
    return {"count": len(frames), "frames": [_serialize(f) for f in frames]}


@router.get("/{frame_id}")
def frame_detail(frame_id: int, db: DBSession = Depends(get_db)):
    """Detail satu frame berdasarkan ID."""
    frame = frame_service.get_frame_by_id(db, frame_id)
    if frame is None or not frame.is_active:
        raise HTTPException(status_code=404, detail=f"Frame dengan id {frame_id} tidak ditemukan.")
    return _serialize(frame)


@router.post("/{frame_id}/validate-selection")
def validate_selection(
    frame_id: int, payload: PhotoSelectionRequest, db: DBSession = Depends(get_db)
):
    """Validasi jumlah foto yang dipilih terhadap slot frame.

    Dipakai frontend sebelum lanjut ke tahap preview.
    """
    valid, message = frame_service.validate_photo_selection(
        db, frame_id, payload.selected_photo_count
    )
    return {"valid": valid, "message": message}
