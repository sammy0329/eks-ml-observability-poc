from prometheus_client import Counter, Gauge, Histogram, Info

REQUEST_COUNT = Counter(
    "request_count",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

APP_INFO = Info("app", "Application information")
APP_INFO.info({"version": "0.1.0"})

# 도메인 메트릭
INPUT_MISSING_RATE = Gauge(
    "input_missing_rate",
    "Ratio of missing flags in the input window",
    ["sensor_id"],
)

INPUT_DELAY_MS = Histogram(
    "input_delay_ms",
    "Inference processing time in milliseconds",
    ["sensor_id"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0],
)

DRIFT_SCORE = Gauge(
    "drift_score",
    "Drift score between first and second half of input window",
    ["sensor_id"],
)

ANOMALY_RATE = Gauge(
    "anomaly_rate",
    "1.0 if latest prediction is anomaly, 0.0 otherwise",
    ["sensor_id"],
)
