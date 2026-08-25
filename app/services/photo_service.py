"""Service: akses foto dalam session (PRD section 4.3)."""

from pathlib import Path

from sqlalchemy.orm import Session as DBSession

from app.models.selection import Selection
from app.models.session import Session
from app.services.frame_service import get_frame_by_id, validate_photo_selection
from app.services.session_service import (
    SessionValidationError,
    validate_session as validate_session_code,
)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def list_session_photos(session: Session) -> list[dict]:
    """List semua file gambar di folder session beserta info aksesnya."""
    folder = Path(session.folder_path)
    photos = []
    if folder.is_dir():
        for f in sorted(folder.iterdir()):
            if f.suffix.lower() in ALLOWED_EXTENSIONS and f.is_file():
                photos.append(
                    {
                        "filename": f.name,
                        "url": f"/media/sessions/{session.session_code}/{f.name}",
                        "size_bytes": f.stat().st_size,
                    }
                )
    return photos


def select_photos(
    db: DBSession, session_code: str, frame_id: int, filenames: list[str]
) -> dict:
    """Simpan pilihan foto klien untuk session tertentu.

    Raises:
        SessionValidationError: 404/410 dari validasi session.
        ValueError: pesan error validasi jumlah foto / filename tidak ada.
    """
    # 1. Validasi session (ada & belum expired)
    session = validate_session_code(db, session_code)

    # 2. Validasi frame & jumlah foto sesuai min/max slot
    valid, message = validate_photo_selection(db, frame_id, len(filenames))
    if not valid:
        raise ValueError(message)

    # 3. Pastikan semua filename benar-benar ada di folder session
    existing = {p["filename"] for p in list_session_photos(session)}
    invalid = [f for f in filenames if f not in existing]
    if invalid:
        raise ValueError(f"File tidak ditemukan di session ini: {', '.join(invalid)}")

    frame = get_frame_by_id(db, frame_id)
    import json

    # 4. Upsert: satu session hanya menyimpan pilihan terakhir
    selection = db.query(Selection).filter(Selection.session_id == session.id).first()
    if selection is None:
        selection = Selection(session_id=session.id)
        db.add(selection)
    selection.frame_id = frame_id
    selection.photos_json = json.dumps(sorted(filenames))
    db.commit()
    db.refresh(selection)

    return {
        "session_code": session.session_code,
        "frame": {"id": frame.id, "name": frame.name},
        "selected_photos": json.loads(selection.photos_json),
        "message": message,
    }


__all__ = [
    "ALLOWED_EXTENSIONS",
    "SessionValidationError",
    "list_session_photos",
    "select_photos",
]
