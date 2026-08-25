"""Service: katalog frame & aturan pemilihan foto (PRD section 4.2)."""

from sqlalchemy.orm import Session as DBSession

from app.models.frame import Frame

# Seed data awal: estimasi ukuran cetak umum studio photobooth @300 DPI
FRAME_SEED_DATA = [
    {
        "name": "Strip",
        "type": "strip",
        "min_photos": 4,
        "max_photos": 4,
        "print_width_px": 600,    # 2 x 6 inch @ 300 DPI
        "print_height_px": 1800,
        "dpi": 300,
    },
    {
        "name": "4R",
        "type": "4r",
        "min_photos": 1,
        "max_photos": 1,
        "print_width_px": 1200,   # 4 x 6 inch @ 300 DPI
        "print_height_px": 1800,
        "dpi": 300,
    },
    {
        "name": "Polaroid",
        "type": "polaroid",
        "min_photos": 1,
        "max_photos": 1,
        "print_width_px": 1050,   # ~3.5 x 4.2 inch @ 300 DPI
        "print_height_px": 1260,
        "dpi": 300,
    },
]


def seed_frames(db: DBSession) -> None:
    """Isi tabel frames dengan data awal jika masih kosong (idempotent)."""
    if db.query(Frame).count() > 0:
        return
    for data in FRAME_SEED_DATA:
        db.add(Frame(**data))
    db.commit()


def get_active_frames(db: DBSession) -> list[Frame]:
    """Semua frame aktif untuk ditampilkan di frontend."""
    return db.query(Frame).filter(Frame.is_active.is_(True)).all()


def get_frame_by_id(db: DBSession, frame_id: int) -> Frame | None:
    return db.query(Frame).filter(Frame.id == frame_id).first()


def validate_photo_selection(
    db: DBSession, frame_id: int, selected_photo_count: int
) -> tuple[bool, str]:
    """Cek apakah jumlah foto yang dipilih sesuai slot frame.

    Returns:
        (valid, message) - message berisi penjelasan jika tidak valid.
    """
    frame = get_frame_by_id(db, frame_id)
    if frame is None:
        return False, f"Frame dengan id {frame_id} tidak ditemukan."
    if not frame.is_active:
        return False, f"Frame '{frame.name}' sedang tidak aktif."

    if selected_photo_count < frame.min_photos:
        return False, (
            f"Jumlah foto kurang. Frame '{frame.name}' membutuhkan minimal "
            f"{frame.min_photos} foto, anda memilih {selected_photo_count}."
        )
    if selected_photo_count > frame.max_photos:
        return False, (
            f"Jumlah foto melebihi batas. Frame '{frame.name}' hanya menerima "
            f"maksimal {frame.max_photos} foto, anda memilih {selected_photo_count}."
        )
    return True, (
        f"Jumlah foto valid untuk frame '{frame.name}' "
        f"({selected_photo_count}/{frame.max_photos} slot)."
    )
