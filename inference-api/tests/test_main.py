from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz_returns_200():
    response = client.get("/healthz")
    assert response.status_code == 200


def test_healthz_returns_ok():
    response = client.get("/healthz")
    assert response.json() == {"status": "ok"}


def test_docs_accessible():
    response = client.get("/docs")
    assert response.status_code == 200
