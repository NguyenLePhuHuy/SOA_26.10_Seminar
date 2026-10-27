import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
PROJECT_ROOT = current_dir.parent if (current_dir.parent / "app").exists() else current_dir.parent.parent
app_dir = str(PROJECT_ROOT / "app")
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from main import app
from metrics import (
    REQUESTS_TOTAL,
    REQUEST_DURATION_SECONDS,
    REQUESTS_IN_PROGRESS,
)


@pytest.fixture
def client():
    return TestClient(app)


def get_counter_value(metric, method: str, route: str, status: str) -> float:
    try:
        return metric.labels(method=method, route=route, status=status)._value.get()
    except KeyError:
        return 0.0


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert "uptime_seconds" in data


def test_work_endpoint_increments_counter(client):
    initial_count = get_counter_value(REQUESTS_TOTAL, "GET", "/work", "200")

    response = client.get("/work")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    new_count = get_counter_value(REQUESTS_TOTAL, "GET", "/work", "200")
    assert new_count == initial_count + 1


def test_error_endpoint_increments_error_counter(client):
    initial_500 = get_counter_value(REQUESTS_TOTAL, "GET", "/error", "500")
    initial_200 = get_counter_value(REQUESTS_TOTAL, "GET", "/error", "200")

    response = client.get("/error?status=500")
    assert response.status_code == 500
    assert response.json()["status"] == "error"

    new_500 = get_counter_value(REQUESTS_TOTAL, "GET", "/error", "500")
    new_200 = get_counter_value(REQUESTS_TOTAL, "GET", "/error", "200")

    assert new_500 == initial_500 + 1
    assert new_200 == initial_200


def get_histogram_count(metric, method: str, route: str) -> float:
    for sample in metric.collect()[0].samples:
        if sample.name.endswith("_count") and sample.labels.get("method") == method and sample.labels.get("route") == route:
            return sample.value
    return 0.0


def test_slow_endpoint_records_duration_in_histogram(client):
    initial_count = get_histogram_count(REQUEST_DURATION_SECONDS, "GET", "/slow")

    response = client.get("/slow?delay=0.1")
    assert response.status_code == 200

    new_count = get_histogram_count(REQUEST_DURATION_SECONDS, "GET", "/slow")
    assert new_count == initial_count + 1


def test_requests_in_progress_gauge_resets(client):
    client.get("/work")
    gauge_val = REQUESTS_IN_PROGRESS.labels(method="GET", route="/work")._value.get()
    assert gauge_val == 0.0


def test_metrics_endpoint_exposition_format(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    body = response.text

    assert "demo_http_requests_total" in body
    assert "demo_http_request_duration_seconds" in body
    assert "demo_http_requests_in_progress" in body
    assert "demo_active_users_current" in body
    assert "demo_app_info" in body


def test_chaos_mode_toggle(client):
    post_res = client.post("/chaos?enabled=true&error_rate=1.0")
    assert post_res.status_code == 200

    work_res = client.get("/work")
    assert work_res.status_code == 500

    post_res = client.post("/chaos?enabled=false&error_rate=0.0")
    assert post_res.status_code == 200

    work_res_normal = client.get("/work")
    assert work_res_normal.status_code == 200
