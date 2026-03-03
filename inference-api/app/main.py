import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Inference API",
    description="EKS ML Observability PoC — FastAPI 추론 서비스",
    version="0.1.0",
)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
