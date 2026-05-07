# DHE

## Setup

Buat venv (jika belum):

```bash
cd /path/ke/dhe
python3 -m venv .venv
```

Pasang dependensi proyek (FastAPI + Uvicorn sudah tercantum di `pyproject.toml`):

```bash
.venv/bin/python -m pip install -e ".[dev]"
```

Kalau venv-mu **bukan** `.venv` (misalnya `.dhe_venv@3.13.5`), ganti `.venv` di perintah di atas, dan sesuaikan `python.defaultInterpreterPath` di `.vscode/settings.json`.

## Run

```bash
.venv/bin/python main.py
```

Atau memakai CLI FastAPI (reload, default `127.0.0.1:8000`):

```bash
.venv/bin/fastapi dev
```

`main.py` di root meng-ekspor objek `app` supaya perintah di atas bisa tanpa argumen.

- Docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health
- Analisis duplikasi (pandas + rapidfuzz): `POST /upload/analyze` (lihat `/docs`)

## Test

```bash
.venv/bin/python -m pytest -q
```

## Frontend (Next.js, JavaScript, folder `src/`)

```bash
cd frontend
cp .env.example .env.local   # sesuaikan NEXT_PUBLIC_API_URL jika API tidak di :8000
npm install
npm run dev
```

Buka http://localhost:3000 — form upload memanggil `POST /upload` di backend. Pastikan API sudah jalan dan CORS mengizinkan origin di atas (sudah diset di `app/main.py`).
