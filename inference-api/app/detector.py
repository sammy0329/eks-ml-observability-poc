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


def detect_anomaly(
    values: list[float],
    missing_flags: list[bool] | None = None,
    zscore_threshold: float = ZSCORE_THRESHOLD,
    missing_rate_threshold: float = MISSING_RATE_THRESHOLD,
) -> DetectionResult:
    if missing_flags is None:
        missing_flags = [False] * len(values)

    # 1. 결측률 검사
    missing_rate = sum(missing_flags) / len(missing_flags)
    if missing_rate > missing_rate_threshold:
        return DetectionResult(
            anomaly_score=float(missing_rate),
            is_anomaly=True,
            reason="missing_rate_high",
        )

    # 유효 값만 추출
    valid_values = [v for v, m in zip(values, missing_flags) if not m]
    if len(valid_values) < 2:
        return DetectionResult(anomaly_score=0.0, is_anomaly=False, reason="ok")

    arr = np.array(valid_values, dtype=float)
    mean = float(np.mean(arr))
    std = float(np.std(arr))

    if std == 0:
        return DetectionResult(anomaly_score=0.0, is_anomaly=False, reason="ok")

    # 2. Z-score 기반 스파이크 검사
    zscores = np.abs((arr - mean) / std)
    max_zscore = float(np.max(zscores))

    if max_zscore > zscore_threshold:
        return DetectionResult(
            anomaly_score=max_zscore / zscore_threshold,
            is_anomaly=True,
            reason="variance_spike",
        )

    # 3. 드리프트 검사 (전반부 vs 후반부 평균 차이 — 각 반쪽 std 기준)
    mid = len(arr) // 2
    if mid > 0:
        half_std = (float(np.std(arr[:mid])) + float(np.std(arr[mid:]))) / 2 + 1e-9
        drift_score = abs(float(np.mean(arr[mid:])) - float(np.mean(arr[:mid]))) / half_std
    else:
        drift_score = 0.0

    if drift_score > DRIFT_THRESHOLD:
        return DetectionResult(
            anomaly_score=drift_score / DRIFT_THRESHOLD,
            is_anomaly=True,
            reason="drift_detected",
        )

    return DetectionResult(
        anomaly_score=max_zscore / zscore_threshold,
        is_anomaly=False,
        reason="ok",
    )
