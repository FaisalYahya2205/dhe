from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_upload_file_csv() -> None:
    r = client.post(
        "/upload",
        files={"file": ("data.csv", b"a,b\n1,2", "text/csv")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["filename"] == "data.csv"
    assert body["size_bytes"] == 7
    assert body["content_type"] == "text/csv"
    assert isinstance(body["sha256"], str) and len(body["sha256"]) == 64


def test_upload_accepts_xls() -> None:
    r = client.post(
        "/upload",
        files={"file": ("legacy.xls", b"\xd0\xcf\x11\xe0", "application/vnd.ms-excel")},
    )
    assert r.status_code == 200
    assert r.json()["filename"] == "legacy.xls"


def test_upload_accepts_xlsx_case_insensitive() -> None:
    r = client.post(
        "/upload",
        files={
            "file": (
                "Report.XLSX",
                b"dummy",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert r.status_code == 200
    assert r.json()["filename"] == "Report.XLSX"


def test_upload_rejects_non_csv_excel() -> None:
    r = client.post(
        "/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 400
    assert "csv" in r.json()["detail"].lower() or "excel" in r.json()["detail"].lower()


def test_upload_analyze_csv() -> None:
    csv_body = b"a,b\n1,2\n1,2\n3,4\n"
    r = client.post(
        "/upload/analyze",
        files={"file": ("data.csv", csv_body, "text/csv")},
    )
    assert r.status_code == 200
    payload = r.json()
    assert "sha256" in payload
    a = payload["analysis"]
    assert a["row_count_input"] == 3
    assert a["exact_duplicate_rows"] == 1
    assert a["rows_after_exact_dedupe"] == 2


def test_upload_analyze_rejects_garbage_xlsx() -> None:
    r = client.post(
        "/upload/analyze",
        files={"file": ("bad.xlsx", b"not-a-workbook", "application/octet-stream")},
    )
    assert r.status_code == 400


def test_upload_rejects_oversized(monkeypatch: object) -> None:
    from app.routers import upload as upload_mod

    monkeypatch.setattr(upload_mod, "MAX_FILE_BYTES", 8)
    r = client.post(
        "/upload",
        files={"file": ("big.csv", b"123456789", "text/csv")},
    )
    assert r.status_code == 413
