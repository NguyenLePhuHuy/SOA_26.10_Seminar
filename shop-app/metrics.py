from prometheus_client import Counter, Histogram, Gauge, Info

# ============================================================
# HTTP Traffic Metrics
# ============================================================
SHOP_REQUESTS_TOTAL = Counter(
    name="shop_http_requests_total",
    documentation="Tổng số HTTP requests nhận được bởi Shop App",
    labelnames=["method", "route", "status"],
)

SHOP_REQUEST_DURATION = Histogram(
    name="shop_http_request_duration_seconds",
    documentation="Thời gian xử lý HTTP request (giây)",
    labelnames=["method", "route"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

SHOP_REQUESTS_IN_PROGRESS = Gauge(
    name="shop_http_requests_in_progress",
    documentation="Số lượng HTTP requests đang được xử lý",
    labelnames=["method", "route"],
)

# ============================================================
# Business Metrics - E-commerce
# ============================================================
ORDERS_TOTAL = Counter(
    name="shop_orders_total",
    documentation="Tổng số đơn hàng theo trạng thái",
    labelnames=["status", "category"],  # status: success/failed/cancelled, category: electronics/clothing/food
)

ORDER_VALUE_VND = Histogram(
    name="shop_order_value_vnd",
    documentation="Giá trị đơn hàng tính bằng VND",
    labelnames=["category"],
    buckets=[50000, 100000, 200000, 500000, 1000000, 2000000, 5000000, 10000000],
)

REVENUE_TOTAL_VND = Counter(
    name="shop_revenue_total_vnd",
    documentation="Tổng doanh thu theo danh mục (VND)",
    labelnames=["category"],
)

ACTIVE_CARTS = Gauge(
    name="shop_active_carts_current",
    documentation="Số giỏ hàng đang được dùng hiện tại",
)

PRODUCTS_VIEWED = Counter(
    name="shop_products_viewed_total",
    documentation="Tổng số lượt xem sản phẩm",
    labelnames=["product_id", "category"],
)

INVENTORY_LEVEL = Gauge(
    name="shop_inventory_level",
    documentation="Mức tồn kho theo sản phẩm",
    labelnames=["product_id", "category"],
)

PAYMENT_TOTAL = Counter(
    name="shop_payment_total",
    documentation="Tổng số giao dịch thanh toán",
    labelnames=["method", "status"],  # method: credit_card/momo/vnpay/cod
)

SEARCH_TOTAL = Counter(
    name="shop_search_total",
    documentation="Tổng số lượt tìm kiếm sản phẩm",
    labelnames=["has_results"],  # has_results: true/false
)

ACTIVE_USERS = Gauge(
    name="shop_active_users_current",
    documentation="Số người dùng đang online hiện tại",
)

# App info
SHOP_INFO = Info(
    name="shop_app",
    documentation="Shop Application metadata",
)
SHOP_INFO.info({
    "version": "1.0.0",
    "framework": "fastapi",
    "app": "ecommerce_shop",
})

# Initialize some gauge defaults
ACTIVE_CARTS.set(0)
ACTIVE_USERS.set(0)
