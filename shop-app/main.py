import asyncio
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from pathlib import Path
from fastapi import FastAPI, Request, Response, Query, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse, FileResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from metrics import (
    SHOP_REQUESTS_TOTAL,
    SHOP_REQUEST_DURATION,
    SHOP_REQUESTS_IN_PROGRESS,
    ORDERS_TOTAL,
    ORDER_VALUE_VND,
    REVENUE_TOTAL_VND,
    ACTIVE_CARTS,
    PRODUCTS_VIEWED,
    INVENTORY_LEVEL,
    PAYMENT_TOTAL,
    SEARCH_TOTAL,
    ACTIVE_USERS,
)

START_TIME = time.time()

app = FastAPI(
    title="🛒 E-Commerce Shop API",
    description="API bán hàng được tích hợp Prometheus metrics để giám sát realtime",
    version="1.0.0",
)

# ============================================================
# In-memory "database" (demo only)
# ============================================================
PRODUCTS = {
    "P001": {"name": "iPhone 15 Pro", "category": "electronics", "price": 29_990_000, "stock": 50},
    "P002": {"name": "Samsung Galaxy S24", "category": "electronics", "price": 22_990_000, "stock": 30},
    "P003": {"name": "Áo thun Uniqlo", "category": "clothing", "price": 299_000, "stock": 200},
    "P004": {"name": "Quần Jean Levi's", "category": "clothing", "price": 1_290_000, "stock": 100},
    "P005": {"name": "Cơm hộp văn phòng", "category": "food", "price": 45_000, "stock": 500},
    "P006": {"name": "Trà sữa Gong Cha", "category": "food", "price": 65_000, "stock": 300},
    "P007": {"name": "Laptop Dell XPS 13", "category": "electronics", "price": 35_000_000, "stock": 20},
    "P008": {"name": "Tai nghe Sony WH-1000XM5", "category": "electronics", "price": 8_490_000, "stock": 40},
}

# Luu so luong kho mac dinh ban dau
DEFAULT_STOCK = {pid: info["stock"] for pid, info in PRODUCTS.items()}

# Initialize inventory gauges
for pid, info in PRODUCTS.items():
    INVENTORY_LEVEL.labels(product_id=pid, category=info["category"]).set(info["stock"])

# Active cart sessions (in-memory)
cart_sessions: dict = {}

# ============================================================
# Middleware: Auto-instrument all requests
# ============================================================
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    path = request.url.path
    if path == "/metrics":
        return await call_next(request)

    method = request.method
    route = path
    SHOP_REQUESTS_IN_PROGRESS.labels(method=method, route=route).inc()
    start = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as exc:
        status_code = 500
        raise exc
    finally:
        duration = time.perf_counter() - start
        SHOP_REQUESTS_IN_PROGRESS.labels(method=method, route=route).dec()
        SHOP_REQUESTS_TOTAL.labels(method=method, route=route, status=str(status_code)).inc()
        SHOP_REQUEST_DURATION.labels(method=method, route=route).observe(duration)


# ============================================================
# Root & Web UI
# ============================================================
STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_FILE = STATIC_DIR / "index.html"

@app.get("/", summary="Trang chủ Web UI hoặc API Info")
async def root(request: Request, format: Optional[str] = Query(None)):
    accept = request.headers.get("accept", "")
    # Tra ve JSON neu co format=json hoac client khong phai browser (curl/scripts yeu cau json)
    if format == "json" or ("application/json" in accept and "text/html" not in accept):
        uptime = round(time.time() - START_TIME, 1)
        return {
            "service": "🛒 E-Commerce Shop API",
            "status": "UP",
            "uptime_seconds": uptime,
            "endpoints": {
                "GET  /": "Trang chủ Web UI mua sắm trực quan",
                "GET  /ui": "Giao diện Web UI mua sắm trực quan",
                "GET  /health": "Health check",
                "GET  /metrics": "Prometheus scrape endpoint",
                "GET  /products": "Danh sách sản phẩm",
                "GET  /products/{id}": "Chi tiết sản phẩm (tăng lượt xem)",
                "GET  /search?q=...": "Tìm kiếm sản phẩm",
                "POST /cart": "Thêm sản phẩm vào giỏ hàng",
                "POST /order": "Đặt hàng (tạo đơn hàng mới)",
                "POST /payment": "Thanh toán đơn hàng",
                "GET  /shop/stats": "Thống kê cửa hàng (giả lập)",
                "POST /shop/simulate": "Giả lập traffic mua hàng ngẫu nhiên",
            },
            "message": "Chào mừng đến với Shop API! Gửi request để xem metrics trên Prometheus & Grafana.",
        }

    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE), media_type="text/html")
    return HTMLResponse("<h1>SOA MiniMart</h1><p>UI đang tải...</p>")


@app.get("/ui", summary="Giao diện Web UI mua sắm trực quan")
async def get_ui():
    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE), media_type="text/html")
    return HTMLResponse("<h1>SOA MiniMart</h1><p>UI file không tồn tại</p>")


# ============================================================
# Health
# ============================================================
@app.get("/health", summary="Health check endpoint")
async def health():
    return {
        "status": "UP",
        "app": "shop-app",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# Metrics
# ============================================================
@app.get("/metrics", summary="Prometheus metrics endpoint")
async def metrics():
    # Cập nhật active users ngẫu nhiên
    ACTIVE_USERS.set(max(1, len(cart_sessions) + random.randint(5, 30)))
    ACTIVE_CARTS.set(len(cart_sessions))
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ============================================================
# Products
# ============================================================
@app.get("/products", summary="Lấy danh sách tất cả sản phẩm")
async def list_products(category: Optional[str] = Query(None, description="Lọc theo danh mục: electronics/clothing/food")):
    result = {}
    for pid, info in PRODUCTS.items():
        if category is None or info["category"] == category:
            result[pid] = info
    return {
        "total": len(result),
        "products": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/products/{product_id}", summary="Xem chi tiết sản phẩm (tăng lượt view)")
async def get_product(product_id: str):
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail=f"Sản phẩm {product_id} không tồn tại")

    product = PRODUCTS[product_id]
    # Ghi nhận lượt xem
    PRODUCTS_VIEWED.labels(product_id=product_id, category=product["category"]).inc()

    # Simulate processing time
    await asyncio.sleep(random.uniform(0.01, 0.05))

    return {
        "product_id": product_id,
        "data": product,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# Search
# ============================================================
@app.get("/search", summary="Tìm kiếm sản phẩm")
async def search_products(q: str = Query(..., description="Từ khóa tìm kiếm")):
    results = {
        pid: info
        for pid, info in PRODUCTS.items()
        if q.lower() in info["name"].lower() or q.lower() in info["category"].lower()
    }
    has_results = "true" if results else "false"
    SEARCH_TOTAL.labels(has_results=has_results).inc()

    await asyncio.sleep(random.uniform(0.01, 0.08))
    return {
        "query": q,
        "total_results": len(results),
        "results": results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# Cart
# ============================================================
@app.post("/cart", summary="Thêm sản phẩm vào giỏ hàng")
async def add_to_cart(
    product_id: str = Query(..., description="ID sản phẩm"),
    quantity: int = Query(default=1, ge=1, le=10, description="Số lượng"),
    session_id: Optional[str] = Query(None, description="Session ID (tự tạo nếu trống)"),
):
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail=f"Sản phẩm {product_id} không tồn tại")

    product = PRODUCTS[product_id]
    if product["stock"] < quantity:
        raise HTTPException(status_code=400, detail=f"Không đủ hàng. Tồn kho: {product['stock']}")

    sid = session_id or str(uuid.uuid4())[:8]
    if sid not in cart_sessions:
        cart_sessions[sid] = []

    cart_sessions[sid].append({"product_id": product_id, "quantity": quantity, "price": product["price"]})
    ACTIVE_CARTS.set(len(cart_sessions))

    await asyncio.sleep(random.uniform(0.005, 0.02))

    return {
        "session_id": sid,
        "message": f"Đã thêm {quantity}x '{product['name']}' vào giỏ hàng",
        "cart_items": len(cart_sessions[sid]),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# Order
# ============================================================
@app.post("/order", summary="Đặt hàng từ giỏ hàng")
async def place_order(
    session_id: str = Query(..., description="Session ID của giỏ hàng"),
    simulate_fail: bool = Query(default=False, description="Giả lập đơn hàng thất bại"),
):
    if session_id not in cart_sessions or not cart_sessions[session_id]:
        raise HTTPException(status_code=400, detail="Giỏ hàng trống hoặc session không tồn tại")

    cart = cart_sessions[session_id]
    order_id = f"ORD-{str(uuid.uuid4())[:8].upper()}"
    total_value = sum(item["price"] * item["quantity"] for item in cart)

    # Determine categories in cart
    categories_in_cart = set()
    for item in cart:
        pid = item["product_id"]
        if pid in PRODUCTS:
            categories_in_cart.add(PRODUCTS[pid]["category"])

    # Process order
    await asyncio.sleep(random.uniform(0.05, 0.2))

    if simulate_fail or random.random() < 0.05:  # 5% chance of failure
        for cat in categories_in_cart or ["electronics"]:
            ORDERS_TOTAL.labels(status="failed", category=cat).inc()
        return JSONResponse(
            status_code=500,
            content={
                "order_id": order_id,
                "status": "FAILED",
                "message": "Lỗi xử lý đơn hàng. Vui lòng thử lại!",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    # Success
    primary_category = list(categories_in_cart)[0] if categories_in_cart else "electronics"
    for cat in categories_in_cart:
        ORDERS_TOTAL.labels(status="success", category=cat).inc()
        ORDER_VALUE_VND.labels(category=cat).observe(total_value)
        REVENUE_TOTAL_VND.labels(category=cat).inc(total_value)

    # Update inventory
    for item in cart:
        pid = item["product_id"]
        if pid in PRODUCTS:
            PRODUCTS[pid]["stock"] = max(0, PRODUCTS[pid]["stock"] - item["quantity"])
            # Tu dong bo sung kho neu con it de demo luon san sang
            if PRODUCTS[pid]["stock"] <= 5:
                PRODUCTS[pid]["stock"] += DEFAULT_STOCK.get(pid, 50)
            cat = PRODUCTS[pid]["category"]
            INVENTORY_LEVEL.labels(product_id=pid, category=cat).set(PRODUCTS[pid]["stock"])

    # Clear cart
    del cart_sessions[session_id]
    ACTIVE_CARTS.set(len(cart_sessions))

    return {
        "order_id": order_id,
        "status": "SUCCESS",
        "total_value_vnd": total_value,
        "total_value_formatted": f"{total_value:,.0f} VND",
        "items": len(cart),
        "categories": list(categories_in_cart),
        "message": "Đơn hàng đã được đặt thành công! 🎉",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# Payment
# ============================================================
@app.post("/payment", summary="Thanh toán đơn hàng")
async def process_payment(
    order_id: str = Query(..., description="Mã đơn hàng"),
    method: str = Query(default="momo", description="Phương thức: credit_card/momo/vnpay/cod"),
    amount: int = Query(..., description="Số tiền (VND)"),
):
    valid_methods = ["credit_card", "momo", "vnpay", "cod"]
    if method not in valid_methods:
        raise HTTPException(status_code=400, detail=f"Phương thức không hợp lệ. Chọn: {valid_methods}")

    await asyncio.sleep(random.uniform(0.1, 0.5))  # Simulate payment gateway latency

    # 8% failure rate for payment
    if random.random() < 0.08:
        PAYMENT_TOTAL.labels(method=method, status="failed").inc()
        return JSONResponse(
            status_code=402,
            content={
                "order_id": order_id,
                "payment_status": "FAILED",
                "method": method,
                "message": "Thanh toán thất bại. Vui lòng kiểm tra lại thông tin!",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    PAYMENT_TOTAL.labels(method=method, status="success").inc()
    return {
        "order_id": order_id,
        "payment_status": "SUCCESS",
        "method": method,
        "amount_vnd": amount,
        "amount_formatted": f"{amount:,.0f} VND",
        "transaction_id": f"TXN-{str(uuid.uuid4())[:10].upper()}",
        "message": f"Thanh toán thành công qua {method.upper()} 💳",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# Inventory Management (Restock & Stock Control)
# ============================================================
@app.post("/inventory/restock", summary="Nhập thêm hàng vào kho (Restock)")
async def restock_inventory(
    product_id: Optional[str] = Query(None, description="Mã sản phẩm cần nhập (để trống nếu nhập tất cả)"),
    quantity: int = Query(default=100, ge=1, le=10000, description="Số lượng nhập thêm"),
    reset: bool = Query(default=False, description="Đặt lại về số lượng mặc định ban đầu"),
):
    updated = {}
    if product_id:
        if product_id not in PRODUCTS:
            raise HTTPException(status_code=404, detail=f"Sản phẩm {product_id} không tồn tại")
        if reset:
            PRODUCTS[product_id]["stock"] = DEFAULT_STOCK.get(product_id, 100)
        else:
            PRODUCTS[product_id]["stock"] += quantity
        cat = PRODUCTS[product_id]["category"]
        INVENTORY_LEVEL.labels(product_id=product_id, category=cat).set(PRODUCTS[product_id]["stock"])
        updated[product_id] = PRODUCTS[product_id]
    else:
        for pid, info in PRODUCTS.items():
            if reset:
                info["stock"] = DEFAULT_STOCK.get(pid, 100)
            else:
                info["stock"] += quantity
            INVENTORY_LEVEL.labels(product_id=pid, category=info["category"]).set(info["stock"])
            updated[pid] = info

    total_stock = sum(p["stock"] for p in PRODUCTS.values())
    return {
        "status": "success",
        "message": f"Nhập kho thành công! {'Đã đặt lại về mặc định' if reset else f'Đã nạp thêm +{quantity} sản phẩm'}",
        "updated": {pid: {"name": p["name"], "stock": p["stock"]} for pid, p in updated.items()},
        "total_stock": total_stock,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/inventory/set", summary="Cập nhật số lượng tồn kho của 1 sản phẩm")
async def set_inventory(
    product_id: str = Query(..., description="Mã sản phẩm (P001, P002, ...)"),
    stock: int = Query(..., ge=0, le=100000, description="Số lượng tồn kho mới"),
):
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail=f"Sản phẩm {product_id} không tồn tại")

    PRODUCTS[product_id]["stock"] = stock
    cat = PRODUCTS[product_id]["category"]
    INVENTORY_LEVEL.labels(product_id=product_id, category=cat).set(stock)

    return {
        "status": "success",
        "product_id": product_id,
        "name": PRODUCTS[product_id]["name"],
        "new_stock": stock,
        "message": f"Đã cập nhật tồn kho '{PRODUCTS[product_id]['name']}' thành {stock}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# Shop Stats
# ============================================================
@app.get("/shop/stats", summary="Thống kê tổng quan cửa hàng")
async def shop_stats():
    total_stock = sum(p["stock"] for p in PRODUCTS.values())
    low_stock = [pid for pid, p in PRODUCTS.items() if p["stock"] < 30]
    return {
        "total_products": len(PRODUCTS),
        "total_stock_units": total_stock,
        "active_carts": len(cart_sessions),
        "low_stock_products": low_stock,
        "categories": list(set(p["category"] for p in PRODUCTS.values())),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# Simulate traffic (useful for demo)
# ============================================================
@app.post("/shop/simulate", summary="Giả lập traffic mua hàng ngẫu nhiên")
async def simulate_traffic(
    num_orders: int = Query(default=5, ge=1, le=20, description="Số đơn hàng giả lập"),
):
    results = []
    payment_methods = ["credit_card", "momo", "vnpay", "cod"]
    categories = ["electronics", "clothing", "food"]

    for i in range(num_orders):
        # Pick random product
        pid = random.choice(list(PRODUCTS.keys()))
        product = PRODUCTS[pid]
        category = product["category"]
        qty = random.randint(1, 3)

        # Simulate order
        success = random.random() > 0.1
        status = "success" if success else "failed"
        ORDERS_TOTAL.labels(status=status, category=category).inc()

        if success:
            value = product["price"] * qty
            ORDER_VALUE_VND.labels(category=category).observe(value)
            REVENUE_TOTAL_VND.labels(category=category).inc(value)

            # Simulate payment
            method = random.choice(payment_methods)
            pay_ok = random.random() > 0.08
            PAYMENT_TOTAL.labels(method=method, status="success" if pay_ok else "failed").inc()

        # Simulate product view
        PRODUCTS_VIEWED.labels(product_id=pid, category=category).inc()

        results.append({
            "order_number": i + 1,
            "product": product["name"],
            "category": category,
            "quantity": qty,
            "status": status,
        })

        await asyncio.sleep(0.02)  # Small delay

    # Update active users
    ACTIVE_USERS.set(random.randint(10, 50))
    ACTIVE_CARTS.set(len(cart_sessions) + random.randint(0, 5))

    return {
        "simulated_orders": num_orders,
        "results": results,
        "message": f"Đã giả lập {num_orders} đơn hàng thành công! Kiểm tra Grafana để xem metrics. 📊",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# One-Click Demo Scenarios (Dành cho thuyết trình live demo)
# ============================================================
@app.post("/shop/scenario", summary="Kích hoạt kịch bản demo 1-click cho buổi thuyết trình")
async def run_scenario(
    scenario: str = Query(..., description="Kịch bản: normal | error | slow | spike | reset")
):
    payment_methods = ["credit_card", "momo", "vnpay", "cod"]
    categories = ["electronics", "clothing", "food"]
    pid_list = list(PRODUCTS.keys())

    if scenario == "normal":
        # Kịch bản 1: 5 đơn bình thường
        for _ in range(5):
            pid = random.choice(pid_list)
            cat = PRODUCTS[pid]["category"]
            qty = random.randint(1, 2)
            val = PRODUCTS[pid]["price"] * qty
            ORDERS_TOTAL.labels(status="success", category=cat).inc()
            ORDER_VALUE_VND.labels(category=cat).observe(val)
            REVENUE_TOTAL_VND.labels(category=cat).inc(val)
            PAYMENT_TOTAL.labels(method=random.choice(payment_methods), status="success").inc()
            PRODUCTS_VIEWED.labels(product_id=pid, category=cat).inc()
        ACTIVE_USERS.set(random.randint(15, 35))
        return {
            "status": "success",
            "scenario": "normal",
            "message": "🟢 Kịch bản 1: Mua hàng bình thường thành công! Doanh thu và đơn hàng đã tăng trên Grafana.",
            "grafana_panel": "Doanh Thu theo Danh Mục & Đơn Hàng Thành Công",
        }

    elif scenario == "error":
        # Kịch bản 2: Bão lỗi HTTP 500
        for _ in range(10):
            pid = random.choice(pid_list)
            cat = PRODUCTS[pid]["category"]
            ORDERS_TOTAL.labels(status="failed", category=cat).inc()
            PAYMENT_TOTAL.labels(method=random.choice(payment_methods), status="failed").inc()
        return {
            "status": "error_simulated",
            "scenario": "error",
            "message": "🔴 Kịch bản 2: Đã kích hoạt 10 lỗi đơn hàng thất bại (HTTP 500)! Cột đỏ Error Rate trên Grafana và cảnh báo Alertmanager sẽ kích hoạt.",
            "grafana_panel": "HTTP Status Code Rate (5xx) & Tỷ Lệ Đơn Hàng Thất Bại",
        }

    elif scenario == "slow":
        # Kịch bản 3: Độ trễ cao 1.5s
        await asyncio.sleep(1.5)
        for _ in range(3):
            pid = random.choice(pid_list)
            cat = PRODUCTS[pid]["category"]
            ORDERS_TOTAL.labels(status="success", category=cat).inc()
        return {
            "status": "slow_simulated",
            "scenario": "slow",
            "delay_seconds": 1.5,
            "message": "⏱️ Kịch bản 3: Đã tạo độ trễ xử lý 1.5 giây! Biểu đồ Response Latency (P90/P99) trên Grafana vừa nhảy vọt lên.",
            "grafana_panel": "Response Latency (P50 / P90 / P99)",
        }

    elif scenario == "spike":
        # Kịch bản 4: Siêu bão đơn hàng Flash Sale (25 đơn)
        for _ in range(25):
            pid = random.choice(pid_list)
            cat = PRODUCTS[pid]["category"]
            qty = random.randint(1, 3)
            val = PRODUCTS[pid]["price"] * qty
            ORDERS_TOTAL.labels(status="success", category=cat).inc()
            ORDER_VALUE_VND.labels(category=cat).observe(val)
            REVENUE_TOTAL_VND.labels(category=cat).inc(val)
            PAYMENT_TOTAL.labels(method=random.choice(payment_methods), status="success").inc()
        ACTIVE_USERS.set(random.randint(60, 100))
        return {
            "status": "spike_simulated",
            "scenario": "spike",
            "orders": 25,
            "message": "⚡ Kịch bản 4: Bão Flash Sale thành công (25 đơn đồng loạt)! Request Rate và Active Users tăng vọt trên Grafana.",
            "grafana_panel": "Request Rate theo Endpoint & Active Users Over Time",
        }

    elif scenario == "reset":
        # Kịch bản 5: Khôi phục bình thường
        for pid, info in PRODUCTS.items():
            info["stock"] = DEFAULT_STOCK.get(pid, 100)
            INVENTORY_LEVEL.labels(product_id=pid, category=info["category"]).set(info["stock"])
        cart_sessions.clear()
        ACTIVE_CARTS.set(0)
        ACTIVE_USERS.set(15)
        return {
            "status": "reset",
            "scenario": "reset",
            "message": "🛡️ Kịch bản 5: Đã khôi phục hệ thống về trạng thái bình thường (Reset tồn kho, xóa giỏ hàng tạm).",
            "grafana_panel": "Tất Cả Panel Đều Trở Lại Vùng Xanh An Toàn",
        }

    else:
        raise HTTPException(status_code=400, detail=f"Kịch bản không hợp lệ: {scenario}. Chọn: normal, error, slow, spike, reset")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
