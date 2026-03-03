from datetime import datetime

from pydantic import BaseModel, field_validator


class PredictRequest(BaseModel):
    sensor_id: str
    timestamp: datetime
    values: list[float]
    missing_flags: list[bool] | None = None

    @field_validator("values")
    @classmethod
    def values_must_not_be_empty(cls, v: list[float]) -> list[float]:
        if len(v) == 0:
            raise ValueError("values must not be empty")
        return v


class PredictResponse(BaseModel):
    anomaly_score: float
    is_anomaly: bool
    reason: str
