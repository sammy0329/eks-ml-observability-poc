from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas import PredictRequest, PredictResponse


class TestPredictRequest:
    def test_valid_request(self):
        req = PredictRequest(
            sensor_id="sensor-01",
            timestamp=datetime.now(),
            values=[1.0, 2.0, 3.0],
        )
        assert req.sensor_id == "sensor-01"
        assert len(req.values) == 3
        assert req.missing_flags is None

    def test_valid_request_with_missing_flags(self):
        req = PredictRequest(
            sensor_id="sensor-01",
            timestamp=datetime.now(),
            values=[1.0, 2.0, 3.0],
            missing_flags=[False, True, False],
        )
        assert req.missing_flags == [False, True, False]

    def test_empty_values_raises_error(self):
        with pytest.raises(ValidationError):
            PredictRequest(
                sensor_id="sensor-01",
                timestamp=datetime.now(),
                values=[],
            )

    def test_wrong_type_raises_error(self):
        with pytest.raises(ValidationError):
            PredictRequest(
                sensor_id="sensor-01",
                timestamp=datetime.now(),
                values="not-a-list",
            )


class TestPredictResponse:
    def test_valid_response(self):
        res = PredictResponse(
            anomaly_score=0.85,
            is_anomaly=True,
            reason="variance_spike",
        )
        assert res.anomaly_score == 0.85
        assert res.is_anomaly is True
        assert res.reason == "variance_spike"
