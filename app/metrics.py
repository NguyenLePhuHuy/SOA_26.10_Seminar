from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY,
)

REQUESTS_TOTAL = Counter(
    name="demo_http_requests_total",
    documentation="Total count of HTTP requests handled by the demo application",
    labelnames=["method", "route", "status"],
)

REQUEST_DURATION_SECONDS = Histogram(
    name="demo_http_request_duration_seconds",
    documentation="HTTP request handling duration in seconds",
    labelnames=["method", "route"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

REQUESTS_IN_PROGRESS = Gauge(
    name="demo_http_requests_in_progress",
    documentation="Current number of HTTP requests being processed in-flight",
    labelnames=["method", "route"],
)

APP_INFO = Info(
    name="demo_app",
    documentation="Demo Application metadata and build information",
)
APP_INFO.info({
    "version": "1.0.0",
    "framework": "fastapi",
    "workshop": "prometheus_grafana_tdtu",
})

SIMULATED_ACTIVE_USERS = Gauge(
    name="demo_active_users_current",
    documentation="Simulated current active user sessions connected to the service",
)
SIMULATED_ACTIVE_USERS.set(12)
