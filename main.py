"""Jalankan server: `.venv/bin/python main.py` atau `fastapi dev` (tanpa argumen).

Objek `app` di-import agar FastAPI CLI menemukan aplikasi di file ini.
"""

from app.main import app  # noqa: F401 — dipakai oleh `fastapi dev` / `fastapi run`

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
