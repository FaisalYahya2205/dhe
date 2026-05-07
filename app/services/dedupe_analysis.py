"""Analisis duplikasi baris: eksak (pandas) dan mirip teks (rapidfuzz)."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz, process


def bytes_to_dataframe(filename: str, raw: bytes) -> pd.DataFrame:
    """Baca CSV / Excel ke DataFrame (sheet pertama untuk Excel)."""
    buf = io.BytesIO(raw)
    ext = Path(filename).suffix.lower()
    try:
        if ext == ".csv":
            return pd.read_csv(buf, encoding="utf-8-sig", on_bad_lines="skip")
        if ext in (".xlsx", ".xlsm"):
            return pd.read_excel(buf, sheet_name=0, engine="openpyxl")
        if ext == ".xls":
            return pd.read_excel(buf, sheet_name=0, engine="xlrd")
    except Exception as e:
        raise ValueError(f"Tidak bisa membaca file sebagai data tabular: {e!s}") from e
    raise ValueError("Ekstensi tidak didukung")


def _row_fingerprints(df: pd.DataFrame) -> list[str]:
    """Satu string normalisasi per baris (untuk perbandingan fuzzy)."""

    def norm_cell(v: object) -> str:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return ""
        return str(v).strip().lower()

    out: list[str] = []
    for _, row in df.iterrows():
        out.append("|".join(norm_cell(v) for v in row))
    return out


def _fuzzy_greedy_clusters(fingerprints: list[str], threshold: int) -> tuple[int, int]:
    """
    Kelompokkan baris yang mirip (ratio >= threshold) secara greedy terhadap perwakilan.
    Mengembalikan (jumlah_baris_masuk, jumlah_klaster/perwakilan).
    """
    reps: list[str] = []
    for fp in fingerprints:
        if not reps:
            reps.append(fp)
            continue

        hit = process.extractOne(
            fp,
            reps,
            scorer=fuzz.ratio,
            score_cutoff=threshold,
        )
        if hit is None:
            reps.append(fp)
    return len(fingerprints), len(reps)


def _normalize_text_value(v: object) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = str(v).strip()
    return " ".join(s.split()).lower()


def analyze_text_typos(
    df: pd.DataFrame,
    *,
    threshold: int = 90,
    max_unique_per_column: int = 2_000,
    max_suggestions_total: int = 200,
    min_value_len: int = 3,
) -> dict[str, object]:
    """
    Deteksi typo sederhana pada nilai teks per kolom.

    Strategi:
    - Ambil kolom tipe object/string.
    - Normalisasi (lower + trim + collapse whitespace).
    - Hitung frekuensi nilai unik (yang panjangnya >= min_value_len).
    - Untuk setiap nilai jarang, cari kandidat yang mirip (rapidfuzz) dan lebih sering muncul,
      lalu usulkan mapping `from -> to`.

    Catatan: ini heuristik; cocok untuk data kategorikal (kota, nama, produk), bukan paragraf panjang.
    """
    suggestions: list[dict[str, object]] = []
    columns_scanned: list[str] = []
    columns_skipped: dict[str, str] = {}

    for col in df.columns:
        if len(suggestions) >= max_suggestions_total:
            break

        s = df[col]
        if not (pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s)):
            continue

        values = s.dropna().map(_normalize_text_value)
        values = values[values.map(len) >= min_value_len]
        if values.empty:
            continue

        vc = values.value_counts()
        if len(vc) > max_unique_per_column:
            columns_skipped[str(col)] = (
                f"unique values {len(vc)} > max_unique_per_column {max_unique_per_column}"
            )
            continue

        columns_scanned.append(str(col))
        freq: dict[str, int] = {k: int(v) for k, v in vc.to_dict().items()}

        # Optimasi: frequent-first canonical reps.
        # Kita bangun daftar "canonical" dari nilai yang sering muncul dulu.
        # Nilai jarang akan dicoba dipetakan ke canonical via extractOne (ke reps),
        # sehingga tidak perlu compare ke semua choices (yang bisa O(n^2)).
        reps: list[str] = []
        # Nilai paling sering jadi prioritas canonical.
        for v in sorted(freq.keys(), key=lambda x: (-freq.get(x, 0), len(x))):
            if len(suggestions) >= max_suggestions_total:
                break

            if not reps:
                reps.append(v)
                continue

            hit = process.extractOne(
                v,
                reps,
                scorer=fuzz.ratio,
                score_cutoff=threshold,
            )
            if hit is None:
                reps.append(v)
                continue

            cand, score, _ = hit
            # Usulkan mapping jika v lebih jarang dari canonical.
            if freq.get(v, 0) < freq.get(cand, 0) and freq.get(v, 0) < 5:
                suggestions.append(
                    {
                        "column": str(col),
                        "from": v,
                        "to": cand,
                        "score": int(score),
                        "from_count": int(freq.get(v, 0)),
                        "to_count": int(freq.get(cand, 0)),
                    }
                )

    return {
        "threshold": threshold,
        "max_unique_per_column": max_unique_per_column,
        "max_suggestions_total": max_suggestions_total,
        "min_value_len": min_value_len,
        "columns_scanned": columns_scanned,
        "columns_skipped": columns_skipped,
        "suggestions": suggestions,
    }


def analyze_column_duplicates(
    df: pd.DataFrame,
    *,
    threshold: int = 90,
    max_unique_per_column: int = 5_000,
    max_columns: int = 80,
) -> list[dict[str, object]]:
    """
    Ringkasan duplikasi per kolom:
    - exact_duplicate_values: total_non_null - unique_non_null
    - fuzzy_grouping (text columns only): perkiraan jumlah kelompok canonical pada nilai unik
      menggunakan strategi reps (frequent-first) + rapidfuzz.extractOne.
    """
    out: list[dict[str, object]] = []
    for col in list(df.columns)[:max_columns]:
        s = df[col]
        non_null = int(s.notna().sum())
        unique_non_null = int(s.nunique(dropna=True))
        exact_dup = max(non_null - unique_non_null, 0)

        item: dict[str, object] = {
            "column": str(col),
            "non_null": non_null,
            "unique_non_null": unique_non_null,
            "exact_duplicate_values": exact_dup,
            "is_text": bool(
                pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s)
            ),
        }

        if item["is_text"] and non_null > 0:
            values = s.dropna().map(_normalize_text_value)
            values = values[values.map(len) >= 1]
            if values.empty:
                item["fuzzy_skipped"] = True
                item["fuzzy_skip_reason"] = "no text values"
            else:
                vc = values.value_counts()
                if len(vc) > max_unique_per_column:
                    item["fuzzy_skipped"] = True
                    item["fuzzy_skip_reason"] = (
                        f"unique values {len(vc)} > max_unique_per_column {max_unique_per_column}"
                    )
                else:
                    freq = {k: int(v) for k, v in vc.to_dict().items()}
                    reps: list[str] = []
                    for v in sorted(freq.keys(), key=lambda x: (-freq.get(x, 0), len(x))):
                        if not reps:
                            reps.append(v)
                            continue
                        hit = process.extractOne(
                            v,
                            reps,
                            scorer=fuzz.ratio,
                            score_cutoff=threshold,
                        )
                        if hit is None:
                            reps.append(v)

                    item["fuzzy_threshold"] = threshold
                    item["fuzzy_skipped"] = False
                    item["fuzzy_groups_unique_values"] = len(reps)
                    item["fuzzy_redundant_unique_values"] = max(len(freq) - len(reps), 0)
        out.append(item)
    return out


def analyze_dataframe(
    df: pd.DataFrame,
    *,
    fuzzy_threshold: int,
    max_rows_fuzzy: int,
    typo_threshold: int = 90,
    typo_max_unique_per_column: int = 2_000,
    typo_max_suggestions_total: int = 200,
) -> dict[str, object]:
    row_in = int(len(df))
    col_count = int(len(df.columns))

    if row_in == 0:
        return {
            "row_count_input": 0,
            "column_count": col_count,
            "exact_duplicate_rows": 0,
            "rows_after_exact_dedupe": 0,
            "exact_dedupe_health_pct": 100.0,
            "fuzzy_threshold": fuzzy_threshold,
            "fuzzy_skipped": False,
            "fuzzy_skip_reason": None,
            "rows_after_fuzzy_grouping": 0,
            "fuzzy_redundant_rows_among_exact_unique": 0,
            "fuzzy_dedupe_health_pct": 100.0,
            "typo": {
                "threshold": typo_threshold,
                "columns_scanned": [],
                "columns_skipped": {},
                "suggestions": [],
            },
        }

    df_exact = df.drop_duplicates()
    n_after_exact = int(len(df_exact))
    exact_dup = row_in - n_after_exact
    exact_health = (n_after_exact / row_in * 100.0) if row_in else 100.0

    fuzzy_skipped = n_after_exact > max_rows_fuzzy
    skip_reason: str | None = None
    if fuzzy_skipped:
        skip_reason = (
            f"Baris unik setelah dedupe eksak ({n_after_exact}) melebihi batas "
            f"fuzzy ({max_rows_fuzzy}); analisis fuzzy dilewati."
        )
        canonical = n_after_exact
        fuzzy_redundant = 0
        fuzzy_health = exact_health
    else:
        fps = _row_fingerprints(df_exact)
        _, canonical = _fuzzy_greedy_clusters(fps, fuzzy_threshold)
        fuzzy_redundant = n_after_exact - canonical
        fuzzy_health = (canonical / row_in * 100.0) if row_in else 100.0

    return {
        "row_count_input": row_in,
        "column_count": col_count,
        "exact_duplicate_rows": exact_dup,
        "rows_after_exact_dedupe": n_after_exact,
        "exact_dedupe_health_pct": round(exact_health, 2),
        "fuzzy_threshold": fuzzy_threshold,
        "fuzzy_skipped": fuzzy_skipped,
        "fuzzy_skip_reason": skip_reason,
        "rows_after_fuzzy_grouping": canonical,
        "fuzzy_redundant_rows_among_exact_unique": fuzzy_redundant,
        "fuzzy_dedupe_health_pct": round(fuzzy_health, 2),
        "typo": analyze_text_typos(
            df,
            threshold=typo_threshold,
            max_unique_per_column=typo_max_unique_per_column,
            max_suggestions_total=typo_max_suggestions_total,
        ),
        "columns": analyze_column_duplicates(
            df,
            threshold=typo_threshold,
            max_unique_per_column=max(typo_max_unique_per_column, 5_000),
        ),
    }
