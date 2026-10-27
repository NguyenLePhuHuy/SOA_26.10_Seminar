import asyncio
import random
import time
from datetime import datetime, timezone
from typing import Optional

from pathlib import Path
from fastapi import FastAPI, Request, Response, Query, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse, FileResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from metrics import (
    REQUESTS_TOTAL,
    REQUEST_DURATION_SECONDS,
    REQUESTS_IN_PROGRESS,
    SIMULATED_ACTIVE_USERS,
)

START_TIME = time.time()

app = FastAPI(
    title="Prometheus & Grafana Workshop Demo Service",
    description="Microservice providing instrumented metrics for hands-on observability seminar",
    version="1.0.0",
)

chaos_config = {
    "enabled": False,
    "error_rate": 0.0,
    "extra_latency": 0.0,
}


@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    path = request.url.path

    if path == "/metrics":
        return await call_next(request)

    method = request.method
    route = path

    REQUESTS_IN_PROGRESS.labels(method=method, route=route).inc()
    start_time = time.perf_counter()
    status_code = 500

    try:
        if chaos_config["enabled"] and path != "/health" and path != "/chaos":
            if chaos_config["extra_latency"] > 0:
                await asyncio.sleep(chaos_config["extra_latency"])
            if random.random() < chaos_config["error_rate"]:
                response = JSONResponse(
                    status_code=500,
                    content={"error": "Chaos error injected dynamically", "status": 500},
                )
                status_code = 500
                return response

        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as exc:
        status_code = 500
        raise exc
    finally:
        duration = time.perf_counter() - start_time
        REQUESTS_IN_PROGRESS.labels(method=method, route=route).dec()
        REQUESTS_TOTAL.labels(
            method=method,
            route=route,
            status=str(status_code),
        ).inc()
        REQUEST_DURATION_SECONDS.labels(
            method=method,
            route=route,
        ).observe(duration)


STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_FILE = STATIC_DIR / "index.html"


@app.get("/", summary="Trang chu Web UI hoac danh sach endpoints")
async def root(request: Request, format: Optional[str] = Query(None)):
    accept = request.headers.get("accept", "")
    if format == "json" or ("application/json" in accept and "text/html" not in accept):
        uptime = round(time.time() - START_TIME, 1)
        return {
            "service": "Prometheus & Grafana Demo Application",
            "status": "UP",
            "uptime_seconds": uptime,
            "chaos_mode": chaos_config,
            "endpoints": {
                "GET /": "Trang chu Web UI dieu khien",
                "GET /health": "Health check probe cho Docker/Kubernetes",
                "GET /metrics": "Prometheus metrics scrape target",
                "GET /work": "Mo phong request xu ly nghiep vu binh thuong (latency 20-80ms)",
                "GET /slow": "Endpoint chu dong tao do tre cao (?delay=1.5)",
                "GET /error": "Endpoint chu dong tra loi HTTP 500 (?status=500)",
                "GET /chaos": "Xem cau hinh Chaos testing hien tai",
                "POST /chaos": "Bat/tat Chaos mode (?enabled=true&error_rate=0.5&latency=0.5)",
            },
            "message": "Chao mung ban den voi buoi Workshop Prometheus & Grafana! Hay dung cac endpoint tren de sinh du lieu giam sat.",
        }

    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE), media_type="text/html")
    return HTMLResponse("<h1>Workshop Demo Service</h1><p>UI dang tai...</p>")


@app.get("/health", summary="Health check endpoint")
async def health():
    return {
        "status": "UP",
        "app": "demo-app",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/metrics", summary="Prometheus metrics scrape endpoint")
async def metrics():
    current_users = 10 + random.randint(-3, 8)
    SIMULATED_ACTIVE_USERS.set(max(1, current_users))

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/work", summary="Endpoint mo phong request binh thuong")
async def work():
    simulated_delay = random.uniform(0.02, 0.08)
    await asyncio.sleep(simulated_delay)
    return {
        "status": "success",
        "message": "Work completed successfully",
        "duration_ms": round(simulated_delay * 1000, 2),
        "data": {
            "processed_items": random.randint(1, 20),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@app.get("/slow", summary="Endpoint mo phong xu ly cham (High Latency)")
async def slow(
    delay: float = Query(
        default=1.5,
        ge=0.1,
        le=10.0,
        description="Thoi gian delay tinh bang giay (0.1 - 10.0s)",
    )
):
    await asyncio.sleep(delay)
    return {
        "status": "success",
        "message": f"Slow task completed after {delay} seconds",
        "delay_seconds": delay,
    }


@app.get("/error", summary="Endpoint chu dong tra loi HTTP 5xx")
async def trigger_error(
    status: int = Query(
        default=500,
        ge=400,
        le=599,
        description="HTTP status code muon tra ve (mac dinh 500)",
    )
):
    return JSONResponse(
        status_code=status,
        content={
            "status": "error",
            "code": status,
            "message": f"Deliberate error simulated with status code {status}",
            "hint": "Quan sat bieu do Error Rate tren Grafana hoac tab Alerts tren Prometheus!",
        },
    )


@app.get("/chaos", summary="Lay thong tin cau hinh Chaos")
async def get_chaos():
    return chaos_config


@app.post("/chaos", summary="Cau hinh Chaos mode tuc thoi")
async def set_chaos(
    enabled: bool = Query(..., description="Bat (true) hoac tat (false)"),
    error_rate: float = Query(default=0.3, ge=0.0, le=1.0, description="Ti le loi (0.0 - 1.0)"),
    latency: float = Query(default=0.0, ge=0.0, le=5.0, description="Do tre bo sung (giay)"),
):
    chaos_config["enabled"] = enabled
    chaos_config["error_rate"] = error_rate
    chaos_config["extra_latency"] = latency
    return {
        "message": "Chaos configuration updated successfully",
        "current_config": chaos_config,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
