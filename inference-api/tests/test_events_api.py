"""운영 이벤트 API 테스트."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


def _mock_db(return_data: dict, list_data: list[dict] | None = None):
    """DB 세션 의존성 오버라이드 — 실제 DB 없이 테스트."""
    async def _override():
        session = AsyncMock()
        result = MagicMock()
        result.mappings.return_value.one.return_value = return_data
        result.mappings.return_value.all.return_value = list_data or []
        session.execute.return_value = result
        yield session

    return _override


class TestDeploymentAPI:
    def test_create_deployment_returns_201(self):
        app.dependency_overrides[get_db] = _mock_db({
            "id": 1, "service_name": "inference-api",
            "version": "0.1.0", "deployed_at": "2024-01-01T00:00:00", "status": "deployed",
        })
        client = TestClient(app)
        resp = client.post("/events/deployments", json={
            "service_name": "inference-api", "version": "0.1.0", "deployed_by": "tester",
        })
        assert resp.status_code == 201
        assert resp.json()["service_name"] == "inference-api"
        app.dependency_overrides.clear()

    def test_create_deployment_missing_field_returns_422(self):
        client = TestClient(app)
        resp = client.post("/events/deployments", json={"version": "0.1.0"})
        assert resp.status_code == 422


class TestIncidentAPI:
    def test_create_incident_returns_201(self):
        app.dependency_overrides[get_db] = _mock_db({
            "id": 1, "sensor_id": "s-01", "reason": "variance_spike",
            "anomaly_score": 2.1, "detected_at": "2024-01-01T00:00:00", "severity": "warning",
        })
        client = TestClient(app)
        resp = client.post("/events/incidents", json={
            "sensor_id": "s-01", "reason": "variance_spike", "anomaly_score": 2.1,
        })
        assert resp.status_code == 201
        assert resp.json()["reason"] == "variance_spike"
        app.dependency_overrides.clear()


class TestScenarioRunAPI:
    def test_create_scenario_run_returns_201(self):
        app.dependency_overrides[get_db] = _mock_db({
            "id": 1, "scenario": "S2", "profile": "error", "started_at": "2024-01-01T00:00:00",
        })
        client = TestClient(app)
        resp = client.post("/events/scenario_runs", json={"scenario": "S2", "profile": "error"})
        assert resp.status_code == 201
        assert resp.json()["scenario"] == "S2"
        app.dependency_overrides.clear()

    def test_list_scenario_runs_returns_200(self):
        app.dependency_overrides[get_db] = _mock_db(
            {},
            list_data=[{"id": 1, "scenario": "S1", "profile": "load",
                        "started_at": "2024-01-01T00:00:00", "ended_at": None, "notes": None}],
        )
        client = TestClient(app)
        resp = client.get("/events/scenario_runs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        app.dependency_overrides.clear()
