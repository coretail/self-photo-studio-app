"""Konfigurasi aplikasi — nilai bisa dioverride lewat environment variable."""

import os
from pathlib import Path

# Masa berlaku session dalam menit (default 60 menit, sesuai PRD 4.1)
SESSION_EXPIRY_MINUTES = int(os.getenv("SESSION_EXPIRY_MINUTES", "60"))

# Root folder penyimpanan hasil sesi foto
DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
SESSIONS_DIR = DATA_DIR / "sessions"
