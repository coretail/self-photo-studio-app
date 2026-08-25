"""Model SQLAlchemy: tabel selections (pilihan foto sementara per session)."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Selection(Base):
    __tablename__ = "selections"

    id: Mapped[int] = mapped_column(primary_key=True)
    # unique: satu session hanya menyimpan pilihan terakhir (upsert)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), unique=True)
    frame_id: Mapped[int] = mapped_column(ForeignKey("frames.id"))
    # daftar filename dipilih, disimpan sebagai JSON string
    photos_json: Mapped[str] = mapped_column(String(4096))
    # hasil penyesuaian posisi/zoom tiap foto (JSON string), nullable sampai
    # klien menekan Konfirmasi di halaman Preview & Adjust
    adjustments_json: Mapped[str | None] = mapped_column(String(8192), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session: Mapped["Session"] = relationship(back_populates="selection")
