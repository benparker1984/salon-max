from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

os.environ.setdefault("SALONMAX_APP_ROLE", "cloud")
os.environ.setdefault("SALONMAX_BIND_HOST", "0.0.0.0")
os.environ.setdefault("SALONMAX_PORT", "5001")
os.environ.setdefault("SALONMAX_DB_PATH", str(BASE_DIR / "salonmax_cloud_backoffice.db"))
os.environ.setdefault("SALONMAX_PLATFORM_DB_PATH", str(BASE_DIR / "salonmax_platform.db"))

from app import run_app


if __name__ == "__main__":
    run_app()
