"""Model SQLAlchemy: tabel orders."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    frame_id: Mapped[int] = mapped_column(ForeignKey("frames.id"))
    order_ref: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    output_file_path: Mapped[str] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session: Mapped["Session"] = relationship(back_populates="orders")
    frame: Mapped["Frame"] = relationship(back_populates="orders")
