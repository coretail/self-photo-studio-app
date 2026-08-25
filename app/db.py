"""Database setup: koneksi SQLite + session factory (SQLAlchemy)."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# File SQLite disimpan di root project (sejajar dengan folder app/)
DB_PATH = Path(__file__).resolve().parent.parent / "studio.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # dibutuhkan untuk SQLite + FastAPI
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class untuk semua model ORM."""


def init_db() -> None:
    """Buat semua tabel berdasarkan model yang sudah terdaftar.

    Model harus di-import dulu sebelum fungsi ini dipanggil agar
    metadata-nya terisi.
    """
    from app.models import frame, order, session  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency FastAPI: buka session DB per-request dan tutup setelahnya."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
