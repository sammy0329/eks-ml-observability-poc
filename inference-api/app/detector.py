from dataclasses import dataclass

import numpy as np

MISSING_RATE_THRESHOLD = 0.3
ZSCORE_THRESHOLD = 3.0
DRIFT_THRESHOLD = 2.0


@dataclass
class DetectionResult:
    anomaly_score: float
    is_anomaly: bool
    reason: str
    missing_rate: float = 0.0
    drift_score: float = 0.0


def detect_anomaly(
    values: list[float],
    missing_flags: list[bool] | None = None,
    zscore_threshold: float = ZSCORE_THRESHOLD,
    missing_rate_threshold: float = MISSING_RATE_THRESHOLD,
) -> DetectionResult:
    if missing_flags is None:
        missing_flags = [False] * len(values)

    # 1. 결측률 계산
    missing_rate = sum(missing_flags) / len(missing_flags)
    if missing_rate > missing_rate_threshold:
        return DetectionResult(
            anomaly_score=float(missing_rate),
            is_anomaly=True,
            reason="missing_rate_high",
            missing_rate=missing_rate,
        )

    # 유효 값만 추출
    valid_values = [v for v, m in zip(values, missing_flags) if not m]
    if len(valid_values) < 2:
        return DetectionResult(
            anomaly_score=0.0, is_anomaly=False, reason="ok",
            missing_rate=missing_rate,
        )

    arr = np.array(valid_values, dtype=float)
    mean = float(np.mean(arr))
    std = float(np.std(arr))

    # 드리프트 점수 항상 계산
    mid = len(arr) // 2
    half_std = (float(np.std(arr[:mid])) + float(np.std(arr[mid:]))) / 2 + 1e-9
    drift_score = abs(float(np.mean(arr[mid:])) - float(np.mean(arr[:mid]))) / half_std

    if std == 0:
        return DetectionResult(
            anomaly_score=0.0, is_anomaly=False, reason="ok",
            missing_rate=missing_rate, drift_score=drift_score,
        )

    # 2. Z-score 기반 스파이크 검사
    zscores = np.abs((arr - mean) / std)
    max_zscore = float(np.max(zscores))

    if max_zscore > zscore_threshold:
        return DetectionResult(
            anomaly_score=max_zscore / zscore_threshold,
            is_anomaly=True,
            reason="variance_spike",
            missing_rate=missing_rate,
            drift_score=drift_score,
        )

    # 3. 드리프트 검사
    if drift_score > DRIFT_THRESHOLD:
        return DetectionResult(
            anomaly_score=drift_score / DRIFT_THRESHOLD,
            is_anomaly=True,
            reason="drift_detected",
            missing_rate=missing_rate,
            drift_score=drift_score,
        )

    return DetectionResult(
        anomaly_score=max_zscore / zscore_threshold,
        is_anomaly=False,
        reason="ok",
        missing_rate=missing_rate,
        drift_score=drift_score,
    )
