import logging
import sys
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("webhook-receiver")

app = FastAPI(
    title="Alertmanager Webhook Receiver",
    description="Dedicated Webhook Notification Endpoint for Prometheus Alertmanager Seminar Demo",
    version="1.0.0",
)

MAX_HISTORY = 50
received_alerts_history: deque = deque(maxlen=MAX_HISTORY)


class AlertItem(BaseModel):
    status: str
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    startsAt: Optional[str] = None
    endsAt: Optional[str] = None
    generatorURL: Optional[str] = None
    fingerprint: Optional[str] = None


class AlertmanagerPayload(BaseModel):
    version: Optional[str] = None
    groupKey: Optional[str] = None
    truncatedAlerts: Optional[int] = 0
    status: str
    receiver: str
    groupLabels: Dict[str, str] = Field(default_factory=dict)
    commonLabels: Dict[str, str] = Field(default_factory=dict)
    commonAnnotations: Dict[str, str] = Field(default_factory=dict)
    externalURL: Optional[str] = None
    alerts: List[AlertItem] = Field(default_factory=list)


def format_alert_log(payload: AlertmanagerPayload) -> str:
    is_firing = payload.status.lower() == "firing"
    status_icon = "[ALARM FIRING]" if is_firing else "[ALERT RESOLVED]"

    lines = [
        "",
        f"WEBHOOK NOTIFICATION RECEIVED: {status_icon}",
        f"Trang thai   : {payload.status.upper()}",
        f"Receiver     : {payload.receiver}",
        f"Alert Name   : {payload.commonLabels.get('alertname', 'N/A')}",
        f"Muc do       : {payload.commonLabels.get('severity', 'N/A')}",
        f"Dich vu      : {payload.commonLabels.get('service', 'N/A')}",
        f"Tom tat      : {payload.commonAnnotations.get('summary', 'N/A')}",
        f"Mo ta        : {payload.commonAnnotations.get('description', 'N/A')}",
    ]

    if payload.commonAnnotations.get("action"):
        lines.append(f"Khac phuc    : {payload.commonAnnotations.get('action')}")

    lines.append(f"So luong     : {len(payload.alerts)} alert(s) in this notification")

    for idx, alert in enumerate(payload.alerts, 1):
        lines.append(f"   --- Alert #{idx} ---")
        lines.append(f"   * Trang thai : {alert.status}")
        if alert.startsAt:
            lines.append(f"   * Bat dau    : {alert.startsAt}")
        if alert.endsAt and not alert.endsAt.startswith("0001"):
            lines.append(f"   * Ket thuc   : {alert.endsAt}")
        if alert.generatorURL:
            lines.append(f"   * PromQL URL : {alert.generatorURL}")

    lines.append("")
    return "\n".join(lines)


@app.get("/health", summary="Health check endpoint for Docker Compose probe")
async def health():
    return {
        "status": "UP",
        "service": "webhook-receiver",
        "received_count": len(received_alerts_history),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/webhook", summary="Alertmanager HTTP POST Webhook Receiver")
@app.post("/api/v1/alerts", summary="Alias endpoint for alerts")
async def receive_webhook(payload: AlertmanagerPayload, request: Request):
    received_time = datetime.now(timezone.utc).isoformat()
    record = {
        "received_at": received_time,
        "status": payload.status,
        "receiver": payload.receiver,
        "commonLabels": payload.commonLabels,
        "commonAnnotations": payload.commonAnnotations,
        "alerts_count": len(payload.alerts),
        "payload": payload.model_dump(),
    }
    received_alerts_history.appendleft(record)

    log_text = format_alert_log(payload)
    print(log_text, flush=True)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "message": f"Webhook payload received and processed ({payload.status})",
            "alerts_count": len(payload.alerts),
            "received_at": received_time,
        },
    )


@app.get("/alerts/latest", summary="Get the latest received alert payload")
async def get_latest_alert():
    if not received_alerts_history:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "No webhook alerts received yet", "total_received": 0},
        )
    return received_alerts_history[0]


@app.get("/alerts", summary="Get list of recent webhook alerts")
async def get_alerts_history(limit: int = 10):
    history = list(received_alerts_history)[:limit]
    return {
        "total_stored": len(received_alerts_history),
        "returned": len(history),
        "alerts": history,
    }


@app.delete("/alerts", summary="Clear alerts history")
async def clear_alerts():
    received_alerts_history.clear()
    return {"message": "Alerts history cleared", "total_stored": 0}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=False)
