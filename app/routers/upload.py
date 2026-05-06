import hashlib
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(tags=["upload"])

# CSV dan Excel: .xlsx/.xlsm (Open XML), .xls (Excel 97–2003 biner).
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".csv", ".xlsx", ".xlsm", ".xls"})

# Batas ukuran satu request upload (ubah sesuai kebutuhan).
MAX_FILE_BYTES = 10 * 1024 * 1024
READ_CHUNK = 1024 * 1024


def _require_allowed_extension(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"Hanya file CSV atau Excel yang didukung ({allowed}). Ekstensi ini: {suffix!r}",
        )


@router.post("/upload")
async def upload_file(
    file: Annotated[
        UploadFile,
        File(description="File CSV atau Excel (.csv, .xlsx, .xlsm, .xls)"),
    ],
) -> dict[str, str | int | None]:
    """
    Terima satu file multipart (`file`), baca dengan streaming, tolak jika melewati batas ukuran.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nama file kosong")

    _require_allowed_extension(file.filename)

    total = 0
    digest = hashlib.sha256()

    while True:
        chunk = await file.read(READ_CHUNK)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_FILE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File terlalu besar (maks {MAX_FILE_BYTES // (1024 * 1024)} MiB)",
            )
        digest.update(chunk)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": total,
        "sha256": digest.hexdigest(),
    }
