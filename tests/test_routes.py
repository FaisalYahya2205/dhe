from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root() -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"message": "ok"}


def test_item() -> None:
    r = client.get("/items/42?q=hi")
    assert r.status_code == 200
    assert r.json() == {"item_id": 42, "q": "hi"}
