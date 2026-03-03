import logging
import time

from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.detector import detect_anomaly
from app.metrics import REQUEST_COUNT, REQUEST_LATENCY
from app.schemas import PredictRequest, PredictResponse

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Inference API",
    description="EKS ML Observability PoC — FastAPI 추론 서비스",
    version="0.1.0",
)



@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    endpoint = request.url.path
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        status=str(response.status_code),
    ).inc()
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)

    return response


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    start = time.perf_counter()

    result = detect_anomaly(
        values=request.values,
        missing_flags=request.missing_flags,
    )

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "predict: sensor_id=%s anomaly_score=%.3f is_anomaly=%s reason=%s latency_ms=%.2f",
        request.sensor_id,
        result.anomaly_score,
        result.is_anomaly,
        result.reason,
        duration_ms,
    )

    return PredictResponse(
        anomaly_score=result.anomaly_score,
        is_anomaly=result.is_anomaly,
        reason=result.reason,
    )
