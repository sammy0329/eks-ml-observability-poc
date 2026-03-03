from prometheus_client import Counter, Histogram, Info

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
