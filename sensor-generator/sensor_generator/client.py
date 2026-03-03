import asyncio
import logging
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


async def send_predict(
    client: httpx.AsyncClient,
    url: str,
    sensor_id: str,
    values: list[float],
    missing_flags: list[bool] | None = None,
    max_retries: int = 2,
) -> dict | None:
    """추론 서비스 /predict 엔드포인트에 데이터를 전송한다.

    실패 시 max_retries 횟수만큼 재시도하고, 최종 실패 시 None 반환.
    """
    payload = {
        "sensor_id": sensor_id,
        "timestamp": datetime.now().isoformat(),
        "values": values,
        "missing_flags": missing_flags,
    }

    for attempt in range(max_retries + 1):
        try:
            response = await client.post(url, json=payload, timeout=3.0)
            response.raise_for_status()
            result = response.json()
            logger.info(
                "sensor_id=%s anomaly_score=%.3f is_anomaly=%s reason=%s",
                sensor_id,
                result["anomaly_score"],
                result["is_anomaly"],
                result["reason"],
            )
            return result
        except httpx.HTTPError as e:
            if attempt < max_retries:
                logger.warning("retry %d/%d: %s", attempt + 1, max_retries, e)
                await asyncio.sleep(0.05)
            else:
                logger.error("failed after %d retries: %s", max_retries, e)
                return None


async def stream(
    base_url: str,
    sensor_id: str,
    values_fn,
    rps: float = 1.0,
    duration_seconds: float | None = None,
) -> None:
    """지정된 RPS로 추론 서비스에 센서 데이터를 스트리밍한다."""
    interval = 1.0 / rps
    predict_url = f"{base_url}/predict"

    async with httpx.AsyncClient() as client:
        start = asyncio.get_event_loop().time()
        while True:
            if duration_seconds and (asyncio.get_event_loop().time() - start) >= duration_seconds:
                break
            values, missing_flags = values_fn()
            await send_predict(client, predict_url, sensor_id, values, missing_flags)
            await asyncio.sleep(interval)
