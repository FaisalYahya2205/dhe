import hashlib
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.services.dedupe_analysis import analyze_dataframe, bytes_to_dataframe

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


async def _read_upload_bytes(file: UploadFile) -> tuple[bytes, str, str | None]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nama file kosong")
    _require_allowed_extension(file.filename)

    chunks: list[bytes] = []
    total = 0
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
        chunks.append(chunk)

    return b"".join(chunks), file.filename, file.content_type


@router.post("/upload")
async def upload_file(
    file: Annotated[
        UploadFile,
        File(description="File CSV atau Excel (.csv, .xlsx, .xlsm, .xls)"),
    ],
) -> dict[str, str | int | None]:
    """Unggah file; kembalikan metadata + hash (tanpa analisis isi)."""
    raw, filename, content_type = await _read_upload_bytes(file)
    return {
        "filename": filename,
        "content_type": content_type,
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


@router.post("/upload/analyze")
async def upload_analyze(
    file: Annotated[
        UploadFile,
        File(description="File CSV atau Excel untuk analisis duplikasi"),
    ],
    fuzzy_threshold: Annotated[
        int,
        Query(
            ge=50,
            le=100,
            description="Skor rapidfuzz.ratio minimum (0–100) untuk menganggap dua baris 'mirip'",
        ),
    ] = 88,
    max_rows_fuzzy: Annotated[
        int,
        Query(
            ge=100,
            le=200_000,
            description="Batas baris unik (setelah dedupe eksak) untuk menjalankan fuzzy; jika lebih, fuzzy dilewati",
        ),
    ] = 20_000,
    typo_threshold: Annotated[
        int,
        Query(
            ge=70,
            le=100,
            description="Ambang rapidfuzz untuk mendeteksi typo pada nilai teks per kolom",
        ),
    ] = 90,
) -> dict[str, object]:
    """
    Unggah file, baca dengan pandas, laporkan duplikasi eksak dan kelompok mirip (rapidfuzz).
    """
    raw, filename, content_type = await _read_upload_bytes(file)
    digest = hashlib.sha256(raw).hexdigest()

    try:
        df = bytes_to_dataframe(filename, raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    analysis = analyze_dataframe(
        df,
        fuzzy_threshold=fuzzy_threshold,
        max_rows_fuzzy=max_rows_fuzzy,
        typo_threshold=typo_threshold,
    )

    return {
        "filename": filename,
        "content_type": content_type,
        "size_bytes": len(raw),
        "sha256": digest,
        "analysis": analysis,
    }
