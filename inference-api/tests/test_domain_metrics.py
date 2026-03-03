"""도메인 메트릭 계측 통합 테스트."""
import re

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestDomainMetrics:
    def _predict(self, sensor_id, values, missing_flags=None):
        payload = {
            "sensor_id": sensor_id,
            "timestamp": "2024-01-01T00:00:00",
            "values": values,
        }
        if missing_flags is not None:
            payload["missing_flags"] = missing_flags
        return client.post("/predict", json=payload)

    def _metrics_text(self):
        return client.get("/metrics").text

    def test_domain_metric_names_exposed(self):
        self._predict("dm-sensor-1", [1.0] * 30)
        text = self._metrics_text()
        assert "input_missing_rate" in text
        assert "input_delay_ms" in text
        assert "drift_score" in text
        assert "anomaly_rate" in text

    def test_input_missing_rate_reflects_flags(self):
        # 40% 결측 (30개 중 12개)
        values = [1.0] * 30
        flags = [True] * 12 + [False] * 18
        self._predict("dm-sensor-2", values, flags)
        text = self._metrics_text()
        assert 'input_missing_rate{sensor_id="dm-sensor-2"} 0.4' in text

    def test_anomaly_rate_one_for_spike(self):
        values = [1.0] * 29 + [100.0]
        self._predict("dm-sensor-3", values)
        text = self._metrics_text()
        assert 'anomaly_rate{sensor_id="dm-sensor-3"} 1.0' in text

    def test_anomaly_rate_zero_for_normal(self):
        values = [1.0] * 30
        self._predict("dm-sensor-4", values)
        text = self._metrics_text()
        assert 'anomaly_rate{sensor_id="dm-sensor-4"} 0.0' in text

    def test_input_delay_ms_histogram_recorded(self):
        self._predict("dm-sensor-5", [1.0] * 30)
        text = self._metrics_text()
        assert 'input_delay_ms_bucket{' in text
        assert 'sensor_id="dm-sensor-5"' in text

    def test_drift_score_nonzero_for_drift_input(self):
        # 강한 드리프트: 전반부 ~0, 후반부 ~10
        values = [0.1 * i for i in range(15)] + [10.0 + 0.1 * i for i in range(15)]
        self._predict("dm-sensor-6", values)
        text = self._metrics_text()
        match = re.search(r'drift_score\{sensor_id="dm-sensor-6"\} ([\d.e+\-]+)', text)
        assert match is not None
        assert float(match.group(1)) > 0
