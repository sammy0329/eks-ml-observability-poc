"""sensor_generator CLI — python -m sensor_generator --profile <name>"""
import asyncio
import logging
import random
from pathlib import Path

import typer
import yaml

from sensor_generator.client import send_predict, stream
from sensor_generator.generator import (
    generate_drift,
    generate_missing,
    generate_normal,
    generate_spike,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

PROFILES_DIR = Path(__file__).parent.parent / "profiles"

app = typer.Typer(help="합성 센서 데이터 생성기")


def _load_profile(profile_name: str) -> dict:
    path = PROFILES_DIR / f"{profile_name}.yaml"
    if not path.exists():
        typer.echo(f"Profile not found: {path}", err=True)
        raise typer.Exit(1)
    with path.open() as f:
        return yaml.safe_load(f)


def _make_values_fn(profile: dict):
    """프로파일 설정에 따라 데이터 생성 함수를 반환한다."""
    anomaly_type = profile.get("anomaly_type", "normal")
    window_size = profile.get("window_size", 30)
    missing_rate = profile.get("missing_rate", 0.0)
    spike_magnitude = profile.get("spike_magnitude", 10.0)
    drift_rate = profile.get("drift_rate", 0.5)
    error_ratio = profile.get("error_ratio", 0.0)

    def values_fn():
        # error_ratio 비율로 빈 values 전송 (422 에러 유발)
        if error_ratio > 0 and random.random() < error_ratio:
            return [], None

        if anomaly_type == "spike":
            values = generate_spike(window_size, spike_magnitude=spike_magnitude)
        elif anomaly_type == "drift":
            values = generate_drift(window_size, drift_rate=drift_rate)
        else:
            values = generate_normal(window_size)

        flags = None
        if missing_rate > 0:
            values, flags = generate_missing(window_size, missing_rate=missing_rate)

        return values, flags

    return values_fn


@app.command()
def main(
    profile: str = typer.Option("normal", "--profile", "-p", help="시나리오 프로파일 이름"),
    target_url: str = typer.Option("http://localhost:8000", "--url", help="추론 API URL"),
    sensor_id: str = typer.Option("sensor-01", "--sensor-id", help="센서 ID"),
    duration: float = typer.Option(None, "--duration", "-d", help="실행 시간 (초). 없으면 무한"),
):
    """합성 센서 데이터를 추론 서비스에 스트리밍한다."""
    cfg = _load_profile(profile)
    rps = cfg.get("rps", 1.0)
    delay_ms = cfg.get("delay_ms", 0)

    typer.echo(f"[{cfg['name']}] {cfg.get('description', '')}")
    typer.echo(f"target={target_url}  sensor_id={sensor_id}  rps={rps}")

    values_fn = _make_values_fn(cfg)

    async def _run():
        import httpx
        interval = 1.0 / rps
        predict_url = f"{target_url}/predict"
        async with httpx.AsyncClient() as client:
            start = asyncio.get_event_loop().time()
            while True:
                if duration and (asyncio.get_event_loop().time() - start) >= duration:
                    break
                if delay_ms:
                    await asyncio.sleep(delay_ms / 1000)
                values, flags = values_fn()
                await send_predict(client, predict_url, sensor_id, values, flags)
                await asyncio.sleep(interval)

    asyncio.run(_run())


if __name__ == "__main__":
    app()
