from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from sensor_generator.client import send_predict


class TestSendPredict:
    async def test_returns_response_on_success(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "anomaly_score": 0.2,
            "is_anomaly": False,
            "reason": "ok",
        }

        with patch("sensor_generator.client.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await send_predict(
                mock_client,
                url="http://localhost:8000/predict",
                sensor_id="sensor-01",
                values=[1.0, 1.1, 0.9],
            )

        assert result is not None
        assert result["is_anomaly"] is False

    async def test_sends_correct_payload(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "anomaly_score": 0.1,
            "is_anomaly": False,
            "reason": "ok",
        }
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        await send_predict(
            mock_client,
            url="http://localhost:8000/predict",
            sensor_id="sensor-42",
            values=[1.0, 2.0],
            missing_flags=[False, False],
        )

        call_kwargs = mock_client.post.call_args
        payload = call_kwargs.kwargs["json"] if call_kwargs.kwargs else call_kwargs[1]["json"]
        assert payload["sensor_id"] == "sensor-42"
        assert payload["values"] == [1.0, 2.0]
        assert payload["missing_flags"] == [False, False]

    async def test_returns_none_after_max_retries(self):
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

        result = await send_predict(
            mock_client,
            url="http://localhost:8000/predict",
            sensor_id="sensor-01",
            values=[1.0],
            max_retries=2,
        )

        assert result is None
        assert mock_client.post.call_count == 3  # 최초 1회 + 재시도 2회

    async def test_retries_on_transient_error(self):
        success_response = MagicMock()
        success_response.raise_for_status = MagicMock()
        success_response.json.return_value = {
            "anomaly_score": 0.0,
            "is_anomaly": False,
            "reason": "ok",
        }
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[httpx.ConnectError("temporary"), success_response]
        )

        result = await send_predict(
            mock_client,
            url="http://localhost:8000/predict",
            sensor_id="sensor-01",
            values=[1.0],
            max_retries=2,
        )

        assert result is not None
        assert mock_client.post.call_count == 2

    async def test_uses_3s_timeout(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "anomaly_score": 0.0,
            "is_anomaly": False,
            "reason": "ok",
        }
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        await send_predict(
            mock_client,
            url="http://localhost:8000/predict",
            sensor_id="sensor-01",
            values=[1.0],
        )

        call_kwargs = mock_client.post.call_args
        timeout = call_kwargs.kwargs.get("timeout") or call_kwargs[1].get("timeout")
        assert timeout == 3.0
