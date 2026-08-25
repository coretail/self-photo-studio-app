"""Service: generate file JPEG siap cetak (PRD section 4.4).

Mereplikasi geometri canvas Preview & Adjust (koordinat center + scale)
ke composite Pillow pada resolusi cetak frame.
"""

import json
import secrets
from datetime import datetime
from pathlib import Path

from PIL import Image
from sqlalchemy.orm import Session as DBSession

from app.config import DATA_DIR
from app.models.frame import Frame
from app.models.selection import Selection
from app.models.session import Session as PhotoSession
from app.services.frame_service import get_frame_by_id

OUTPUTS_DIR = DATA_DIR / "outputs"


def compute_slots(frame_w: int, frame_h: int, num_slots: int) -> list[dict]:
    """Layout slot vertikal - HARUS sama dengan adjust.js."""
    slot_h = frame_h / num_slots
    return [
        {"left": 0, "top": i * slot_h, "width": frame_w, "height": slot_h}
        for i in range(num_slots)
    ]


def generate_order_ref() -> str:
    """Format human-readable: ORD-YYYYMMDD-XXXX."""
    today = datetime.now().strftime("%Y%m%d")
    return f"ORD-{today}-{secrets.token_hex(2).upper()}"


def render_composite(
    frame: Frame,
    session_folder: Path,
    adjustments: list[dict],
    out_path: Path,
) -> None:
    """Render foto-foto terposisi ke kanvas berukuran cetak frame.

    Geometri di halaman adjust (Fabric.js):
      - img.left/img.top = titik PUSAT foto dalam ruang pixel cetak
      - scaleX/scaleY   = faktor zoom
    Maka area foto di ruang cetak:
      width  = img.width * scale, height = img.height * scale
      topleft = (x - width/2, y - height/2)
    Foto di-crop otomatis ke batas slotnya (seperti clipPath).
    """
    num_slots = frame.min_photos
    slots = compute_slots(frame.print_width_px, frame.print_height_px, num_slots)

    canvas = Image.new("RGB", (frame.print_width_px, frame.print_height_px), "#2a2a38")

    for idx, adj in enumerate(adjustments[:num_slots]):
        slot = slots[idx]
        src = session_folder / adj["filename"]
        if not src.is_file():
            continue  # skip foto hilang, biarkan background slot

        with Image.open(src) as im:
            im = im.convert("RGB")
            rw = max(1, round(im.width * adj["scale"]))
            rh = max(1, round(im.height * adj["scale"]))
            resized = im.resize((rw, rh), Image.LANCZOS)

        # Titik pusat foto (dari state canvas) -> sudut kiri-atas
        left = adj["x"] - rw / 2
        top = adj["y"] - rh / 2

        # Posisi relatif terhadap slot; offset negatif = auto-crop oleh Pillow
        paste_x = round(left - slot["left"])
        paste_y = round(top - slot["top"])

        slot_img = Image.new("RGB", (round(slot["width"]), round(slot["height"])), "#2a2a38")
        slot_img.paste(resized, (paste_x, paste_y))
        canvas.paste(slot_img, (round(slot["left"]), round(slot["top"])))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, "JPEG", quality=95, dpi=(frame.dpi, frame.dpi))


def generate_print_file(db: DBSession, session_code: str) -> dict:
    """Ambil selection + adjustment, render JPEG final, buat record Order.

    Returns:
        dict ringkasan order.
    Raises:
        ValueError: bila belum ada selection/adjustment atau data tidak valid.
    """
    session = (
        db.query(PhotoSession).filter(PhotoSession.session_code == session_code).first()
    )
    if session is None:
        raise ValueError(f"Session '{session_code}' tidak ditemukan.")

    selection = (
        db.query(Selection).filter(Selection.session_id == session.id).first()
    )
    if selection is None or not selection.adjustments_json:
        raise ValueError(
            "Belum ada penyesuaian posisi/zoom. Selesaikan tahap Preview & Adjust dulu."
        )

    frame = get_frame_by_id(db, selection.frame_id)
    adjustments = json.loads(selection.adjustments_json)
    photos = json.loads(selection.photos_json)

    order_ref = generate_order_ref()
    out_path = OUTPUTS_DIR / f"{order_ref}.jpg"

    try:
        render_composite(frame, Path(session.folder_path), adjustments, out_path)
        status = "completed"
        error_msg = None
    except Exception as exc:  # noqa: BLE001 - catat gagal render sebagai Order failed
        status = "failed"
        error_msg = str(exc)

    from app.models.order import Order

    order = Order(
        session_id=session.id,
        frame_id=frame.id,
        order_ref=order_ref,
        output_file_path=str(out_path),
        status=status,
    )
    db.add(order)
    db.commit()

    if status == "failed":
        raise RuntimeError(f"Gagal generate file cetak: {error_msg}")

    return {
        "order_ref": order_ref,
        "status": status,
        "output_file_path": str(out_path),
        "output_url": f"/media/outputs/{order_ref}.jpg",
        "frame": {"id": frame.id, "name": frame.name},
        "num_photos": len(photos),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
