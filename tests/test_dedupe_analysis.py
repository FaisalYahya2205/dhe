import pandas as pd
import pytest

from app.services.dedupe_analysis import analyze_dataframe


def test_analyze_exact_duplicates() -> None:
    df = pd.DataFrame(
        [
            {"a": 1, "b": 2},
            {"a": 1, "b": 2},
            {"a": 3, "b": 4},
        ]
    )
    r = analyze_dataframe(df, fuzzy_threshold=90, max_rows_fuzzy=10_000)
    assert r["row_count_input"] == 3
    assert r["exact_duplicate_rows"] == 1
    assert r["rows_after_exact_dedupe"] == 2
    assert r["exact_dedupe_health_pct"] == pytest.approx(2 / 3 * 100, abs=0.02)


def test_analyze_fuzzy_merges_near_duplicate_rows() -> None:
    df = pd.DataFrame(
        [
            {"a": "hello world", "b": 1},
            {"a": "hello worl", "b": 1},
        ]
    )
    r = analyze_dataframe(df, fuzzy_threshold=92, max_rows_fuzzy=10_000)
    assert r["rows_after_exact_dedupe"] == 2
    assert r["fuzzy_skipped"] is False
    assert r["rows_after_fuzzy_grouping"] == 1
    assert r["fuzzy_redundant_rows_among_exact_unique"] == 1


def test_analyze_fuzzy_skipped_when_too_many_unique_rows() -> None:
    df = pd.DataFrame([{"x": i} for i in range(5)])
    r = analyze_dataframe(df, fuzzy_threshold=90, max_rows_fuzzy=3)
    assert r["fuzzy_skipped"] is True
    assert r["fuzzy_skip_reason"] is not None


def test_analyze_text_typos_suggests_mapping() -> None:
    df = pd.DataFrame(
        [
            {"city": "Jakarta"},
            {"city": "Jakarta"},
            {"city": "Jakrta"},
            {"city": "Bandung"},
            {"city": "Bandung"},
            {"city": "Bandung"},
        ]
    )
    r = analyze_dataframe(df, fuzzy_threshold=90, max_rows_fuzzy=10_000, typo_threshold=90)
    typo = r["typo"]
    assert isinstance(typo, dict)
    suggestions = typo["suggestions"]
    assert any(s["from"] == "jakrta" and s["to"] == "jakarta" for s in suggestions)
