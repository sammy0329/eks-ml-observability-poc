from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

NORMAL_PAYLOAD = {
    "sensor_id": "sensor-01",
    "timestamp": datetime.now().isoformat(),
    "values": [1.0, 1.1, 0.9, 1.05, 0.95, 1.02, 0.98, 1.0, 1.01, 0.99],
}

SPIKE_PAYLOAD = {
    "sensor_id": "sensor-02",
    "timestamp": datetime.now().isoformat(),
    "values": [1.0] * 20 + [500.0],
}

MISSING_PAYLOAD = {
    "sensor_id": "sensor-03",
    "timestamp": datetime.now().isoformat(),
    "values": [1.0] * 10,
    "missing_flags": [True] * 4 + [False] * 6,
}


class TestPredictNormal:
    def test_returns_200(self):
        response = client.post("/predict", json=NORMAL_PAYLOAD)
        assert response.status_code == 200

    def test_response_has_required_fields(self):
        response = client.post("/predict", json=NORMAL_PAYLOAD)
        body = response.json()
        assert "anomaly_score" in body
        assert "is_anomaly" in body
        assert "reason" in body

    def test_normal_data_not_anomaly(self):
        response = client.post("/predict", json=NORMAL_PAYLOAD)
        assert response.json()["is_anomaly"] is False


class TestPredictAnomaly:
    def test_spike_detected_as_anomaly(self):
        response = client.post("/predict", json=SPIKE_PAYLOAD)
        body = response.json()
        assert body["is_anomaly"] is True
        assert body["reason"] == "variance_spike"

    def test_missing_data_detected(self):
        response = client.post("/predict", json=MISSING_PAYLOAD)
        body = response.json()
        assert body["is_anomaly"] is True
        assert body["reason"] == "missing_rate_high"


class TestPredictValidation:
    def test_empty_values_returns_422(self):
        payload = {**NORMAL_PAYLOAD, "values": []}
        response = client.post("/predict", json=payload)
        assert response.status_code == 422

    def test_missing_sensor_id_returns_422(self):
        payload = {k: v for k, v in NORMAL_PAYLOAD.items() if k != "sensor_id"}
        response = client.post("/predict", json=payload)
        assert response.status_code == 422

    def test_invalid_values_type_returns_422(self):
        payload = {**NORMAL_PAYLOAD, "values": "not-a-list"}
        response = client.post("/predict", json=payload)
        assert response.status_code == 422
