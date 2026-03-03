"""__main__.py 헬퍼 함수 및 stream 통합 테스트."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sensor_generator.__main__ import _load_profile, _make_values_fn
from sensor_generator.client import stream


class TestLoadProfile:
    def test_loads_normal_profile(self):
        cfg = _load_profile("normal")
        assert cfg["name"] == "normal"
        assert cfg["rps"] == 10

    def test_loads_load_profile(self):
        cfg = _load_profile("load")
        assert cfg["rps"] == 50

    def test_loads_error_profile(self):
        cfg = _load_profile("error")
        assert cfg["error_ratio"] == 0.3

    def test_loads_quality_degradation_profile(self):
        cfg = _load_profile("quality_degradation")
        assert cfg["missing_rate"] == 0.4

    def test_missing_profile_exits(self):
        import typer
        with pytest.raises(typer.Exit):
            _load_profile("nonexistent_profile_xyz")


class TestMakeValuesFn:
    def test_normal_returns_values_and_none(self):
        cfg = {"anomaly_type": "normal", "window_size": 10,
               "missing_rate": 0.0, "spike_magnitude": 0.0,
               "drift_rate": 0.0, "error_ratio": 0.0}
        fn = _make_values_fn(cfg)
        values, flags = fn()
        assert len(values) == 10
        assert flags is None

    def test_spike_profile_returns_values(self):
        cfg = {"anomaly_type": "spike", "window_size": 10,
               "missing_rate": 0.0, "spike_magnitude": 50.0,
               "drift_rate": 0.0, "error_ratio": 0.0}
        fn = _make_values_fn(cfg)
        values, flags = fn()
        assert len(values) == 10

    def test_missing_rate_returns_flags(self):
        cfg = {"anomaly_type": "normal", "window_size": 20,
               "missing_rate": 0.5, "spike_magnitude": 0.0,
               "drift_rate": 0.0, "error_ratio": 0.0}
        fn = _make_values_fn(cfg)
        values, flags = fn()
        assert flags is not None
        assert len(flags) == 20

    def test_error_ratio_can_return_empty_values(self):
        cfg = {"anomaly_type": "normal", "window_size": 10,
               "missing_rate": 0.0, "spike_magnitude": 0.0,
               "drift_rate": 0.0, "error_ratio": 1.0}  # 100% 에러
        fn = _make_values_fn(cfg)
        values, flags = fn()
        assert values == []


class TestStream:
    async def test_stream_stops_after_duration(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "anomaly_score": 0.0, "is_anomaly": False, "reason": "ok"
        }

        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_response

        with patch("sensor_generator.client.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = mock_post
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await stream(
                base_url="http://localhost:8000",
                sensor_id="sensor-01",
                values_fn=lambda: ([1.0, 1.1, 0.9], None),
                rps=100.0,
                duration_seconds=0.1,
            )

        assert call_count >= 1
