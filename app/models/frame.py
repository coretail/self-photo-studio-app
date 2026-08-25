"""Model SQLAlchemy: tabel frames."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Frame(Base):
    __tablename__ = "frames"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    type: Mapped[str] = mapped_column(String(32))  # contoh: strip / 4r / polaroid
    min_photos: Mapped[int] = mapped_column(Integer, default=1)
    max_photos: Mapped[int] = mapped_column(Integer, default=1)
    print_width_px: Mapped[int] = mapped_column(Integer)   # dimensi cetak dalam pixel
    print_height_px: Mapped[int] = mapped_column(Integer)
    dpi: Mapped[int] = mapped_column(Integer, default=300)
    is_active: Mapped[bool] = mapped_column(default=True)

    orders: Mapped[list["Order"]] = relationship(back_populates="frame")
