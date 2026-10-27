import importlib.util
import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
PROJECT_ROOT = current_dir.parent if (current_dir.parent / "webhook-receiver").exists() else current_dir.parent.parent
webhook_dir = str(PROJECT_ROOT / "webhook-receiver")
if webhook_dir not in sys.path:
    sys.path.insert(0, webhook_dir)

import pytest
from fastapi.testclient import TestClient

_webhook_main_path = PROJECT_ROOT / "webhook-receiver" / "main.py"
_spec = importlib.util.spec_from_file_location("webhook_receiver_service", str(_webhook_main_path))
if _spec is not None and _spec.loader is not None:
    _webhook_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_webhook_module)
    app = _webhook_module.app
    received_alerts_history = _webhook_module.received_alerts_history
else:
    from main import app, received_alerts_history

@pytest.fixture(autouse=True)
def clean_history():
    received_alerts_history.clear()
    yield
    received_alerts_history.clear()


@pytest.fixture
def client():
    return TestClient(app)


SAMPLE_FIRING_PAYLOAD = {
    "version": "4",
    "groupKey": "{}:{alertname=\"DemoHighErrorRate\"}",
    "truncatedAlerts": 0,
    "status": "firing",
    "receiver": "webhook-notifications",
    "groupLabels": {"alertname": "DemoHighErrorRate"},
    "commonLabels": {
        "alertname": "DemoHighErrorRate",
        "severity": "critical",
        "tier": "api",
        "service": "demo-application",
    },
    "commonAnnotations": {
        "summary": "Ti le loi HTTP 5xx vuot qua 5%",
        "description": "Ti le loi HTTP 5xx cua demo-app hien tai dat 70.00% trong 1 phut qua.",
        "action": "Kiem tra log container demo-app hoac dung kich ban traffic-error.",
    },
    "externalURL": "http://alertmanager:9093",
    "alerts": [
        {
            "status": "firing",
            "labels": {
                "alertname": "DemoHighErrorRate",
                "severity": "critical",
                "tier": "api",
                "service": "demo-application",
            },
            "annotations": {
                "summary": "Ti le loi HTTP 5xx vuot qua 5%",
                "description": "Ti le loi HTTP 5xx cua demo-app hien tai dat 70.00% trong 1 phut qua.",
                "action": "Kiem tra log container demo-app hoac dung kich ban traffic-error.",
            },
            "startsAt": "2026-10-18T11:30:00.000Z",
            "endsAt": "0001-01-01T00:00:00Z",
            "generatorURL": "http://prometheus:9090/graph?g0.expr=...",
        }
    ],
}

SAMPLE_RESOLVED_PAYLOAD = {
    "version": "4",
    "groupKey": "{}:{alertname=\"DemoHighErrorRate\"}",
    "truncatedAlerts": 0,
    "status": "resolved",
    "receiver": "webhook-notifications",
    "groupLabels": {"alertname": "DemoHighErrorRate"},
    "commonLabels": {
        "alertname": "DemoHighErrorRate",
        "severity": "critical",
        "tier": "api",
        "service": "demo-application",
    },
    "commonAnnotations": {
        "summary": "Ti le loi HTTP 5xx vuot qua 5%",
        "description": "Ti le loi HTTP 5xx cua demo-app hien tai dat 0.00% trong 1 phut qua.",
    },
    "externalURL": "http://alertmanager:9093",
    "alerts": [
        {
            "status": "resolved",
            "labels": {
                "alertname": "DemoHighErrorRate",
                "severity": "critical",
                "tier": "api",
                "service": "demo-application",
            },
            "annotations": {
                "summary": "Ti le loi HTTP 5xx vuot qua 5%",
            },
            "startsAt": "2026-10-18T11:30:00.000Z",
            "endsAt": "2026-10-18T11:32:00.000Z",
            "generatorURL": "http://prometheus:9090/graph?g0.expr=...",
        }
    ],
}


def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "UP"
    assert data["service"] == "webhook-receiver"


def test_receive_firing_webhook(client):
    res = client.post("/webhook", json=SAMPLE_FIRING_PAYLOAD)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["alerts_count"] == 1

    latest_res = client.get("/alerts/latest")
    assert latest_res.status_code == 200
    latest = latest_res.json()
    assert latest["status"] == "firing"
    assert latest["receiver"] == "webhook-notifications"
    assert latest["commonLabels"]["alertname"] == "DemoHighErrorRate"
    assert latest["commonLabels"]["severity"] == "critical"
    assert "alerts" in latest["payload"]


def test_receive_resolved_webhook(client):
    client.post("/webhook", json=SAMPLE_FIRING_PAYLOAD)
    res = client.post("/webhook", json=SAMPLE_RESOLVED_PAYLOAD)
    assert res.status_code == 200

    latest_res = client.get("/alerts/latest")
    assert latest_res.status_code == 200
    latest = latest_res.json()
    assert latest["status"] == "resolved"
    assert latest["payload"]["alerts"][0]["status"] == "resolved"
    assert latest["payload"]["alerts"][0]["endsAt"] == "2026-10-18T11:32:00.000Z"


def test_history_and_clear(client):
    client.post("/webhook", json=SAMPLE_FIRING_PAYLOAD)
    client.post("/webhook", json=SAMPLE_RESOLVED_PAYLOAD)

    hist_res = client.get("/alerts?limit=10")
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert hist["total_stored"] == 2
    assert len(hist["alerts"]) == 2

    del_res = client.delete("/alerts")
    assert del_res.status_code == 200

    assert len(received_alerts_history) == 0
    empty_latest = client.get("/alerts/latest")
    assert empty_latest.status_code == 404
