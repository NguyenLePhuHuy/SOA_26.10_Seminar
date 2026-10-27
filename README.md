# 🚀 Prometheus & Grafana Monitoring — Hướng Dẫn Chạy Dự Án

Dự án gồm **2 ứng dụng FastAPI** được giám sát đầy đủ bởi **Prometheus + Grafana**:
- `demo-app` — App demo gốc (port 8000)
- `shop-app` — App bán hàng mới (port 8001) với metrics doanh thu, đơn hàng, thanh toán

---

## 📋 Yêu Cầu Trước Khi Chạy

| Công cụ | Phiên bản tối thiểu | Kiểm tra |
|---|---|---|
| **Docker Desktop** | 24+ | `docker --version` |
| **Docker Compose** | v2+ | `docker compose version` |

> ⚠️ Đảm bảo **Docker Desktop đang chạy** trước khi thực hiện các bước dưới đây.

---

## ⚡ Chạy Nhanh (3 bước)

### Bước 1 — Mở terminal trong thư mục dự án

```powershell
cd "đường-dẫn-tới\SOA_26.10_Seminar-main"
```

Ví dụ:
```powershell
cd "D:\SOA_26.10_Seminar-main"
```

---

### Bước 2 — Tạo file cấu hình `.env`

```powershell
.env.example .env
```

> File `.env` chứa các cổng kết nối. Mặc định không cần chỉnh sửa gì thêm.

---

### Bước 3 — Khởi động toàn bộ hệ thống

```powershell
docker compose up -d --build
```

Lần đầu sẽ mất **3–5 phút** để tải images và build. Các lần sau chạy nhanh hơn.

Kiểm tra tất cả container đang chạy:
```powershell
docker compose ps
```

Kết quả mong đợi — tất cả STATUS phải là `running`:
```
NAME                        STATUS
workshop-demo-app           running
workshop-shop-app           running
workshop-prometheus         running
workshop-grafana            running
workshop-alertmanager       running
workshop-webhook-receiver   running
workshop-load-generator     running
workshop-shop-loadgen       running
```

---

## 🌐 Truy Cập Các Dịch Vụ

Sau khi khởi động xong, mở trình duyệt vào các địa chỉ sau:

| Dịch vụ | URL | Ghi chú |
|---|---|---|
| 🛍️ **Demo App** | http://localhost:8000 | App demo gốc |
| 🛍️ **Demo App Docs** | http://localhost:8000/docs | Swagger UI |
| 🛒 **Shop App** | http://localhost:8001 | App bán hàng mới |
| 🛒 **Shop App Docs** | http://localhost:8001/docs | Swagger UI bán hàng |
| 📊 **Prometheus UI** | http://localhost:9091 | Xem metrics, targets, alerts |
| 📈 **Grafana** | http://localhost:3005 | Dashboard trực quan |
| 🔔 **Alertmanager** | http://localhost:9093 | Quản lý cảnh báo |
| 📨 **Webhook Receiver** | http://localhost:5001/alerts/latest | Log cảnh báo nhận được |

**Đăng nhập Grafana:** username `admin` / password `admin`

---

## 📈 Xem Dashboard Grafana

1. Truy cập http://localhost:3005
2. Đăng nhập `admin` / `admin`
3. Vào **Dashboards** → **Workshop** → chọn dashboard:
   - **Demo Dashboard** — giám sát demo-app
   - **🛒 E-Commerce Shop Dashboard** — giám sát shop-app

---

## 🛒 Sử Dụng Shop App (App Bán Hàng)

### Tạo traffic nhanh để xem Grafana ngay:

```powershell
# Giả lập 20 đơn hàng cùng lúc
curl -X POST "http://localhost:8001/shop/simulate?num_orders=20"
```

### Luồng mua hàng thủ công:

```powershell
# 1. Xem danh sách sản phẩm
curl http://localhost:8001/products

# 2. Xem chi tiết sản phẩm (tăng lượt view)
curl http://localhost:8001/products/P001

# 3. Tìm kiếm
curl "http://localhost:8001/search?q=iphone"

# 4. Thêm vào giỏ hàng → nhận về session_id
curl -X POST "http://localhost:8001/cart?product_id=P001&quantity=1"

# 5. Đặt hàng (thay <session_id> bằng giá trị nhận được ở bước 4)
curl -X POST "http://localhost:8001/order?session_id=<session_id>"

# 6. Thanh toán (thay <order_id> bằng giá trị nhận được ở bước 5)
curl -X POST "http://localhost:8001/payment?order_id=<order_id>&method=momo&amount=29990000"
```

### Phương thức thanh toán hỗ trợ:
`momo` | `vnpay` | `credit_card` | `cod`

---

## 🎭 Kịch Bản Demo (Demo App)

Chạy các kịch bản để xem cảnh báo trên Prometheus & Grafana:

```powershell
# Tạo traffic bình thường
.\scripts\traffic-normal.ps1

# Tạo nhiều lỗi HTTP 500 (kích hoạt alert DemoHighErrorRate)
.\scripts\traffic-error.ps1

# Tạo tải nặng (High Traffic)
.\scripts\traffic-heavy.ps1

# Tạo độ trễ cao (kích hoạt alert DemoHighLatency)
.\scripts\traffic-slow.ps1

# Dừng tạo traffic và tắt chaos mode
.\scripts\traffic-stop.ps1

# Kiểm thử tự động toàn bộ vòng đời cảnh báo
.\scripts\test-alert.ps1

# Xem log webhook nhận cảnh báo
.\scripts\view-webhook.ps1
```

---

## 🔍 Kiểm Tra Prometheus

Vào http://localhost:9091 và thử các truy vấn PromQL:

```promql
# Tốc độ request shop-app (req/s)
sum(rate(shop_http_requests_total[1m]))

# Tổng doanh thu theo danh mục
sum by (category) (shop_revenue_total_vnd)

# Tỷ lệ lỗi shop-app
sum(rate(shop_http_requests_total{status=~"5.."}[1m])) / sum(rate(shop_http_requests_total[1m])) * 100

# Latency P99
histogram_quantile(0.99, sum by (le) (rate(shop_http_request_duration_seconds_bucket[1m])))

# Tồn kho theo sản phẩm
shop_inventory_level

# Số đơn hàng thành công (5 phút)
increase(shop_orders_total{status="success"}[5m])
```

---

## 🏪 Danh Sách Sản Phẩm Mẫu (Shop App)

| ID | Tên sản phẩm | Danh mục | Giá |
|---|---|---|---|
| P001 | iPhone 15 Pro | electronics | 29,990,000 VND |
| P002 | Samsung Galaxy S24 | electronics | 22,990,000 VND |
| P003 | Áo thun Uniqlo | clothing | 299,000 VND |
| P004 | Quần Jean Levi's | clothing | 1,290,000 VND |
| P005 | Cơm hộp văn phòng | food | 45,000 VND |
| P006 | Trà sữa Gong Cha | food | 65,000 VND |
| P007 | Laptop Dell XPS 13 | electronics | 35,000,000 VND |
| P008 | Tai nghe Sony WH-1000XM5 | electronics | 8,490,000 VND |

---

## 📁 Cấu Trúc Thư Mục

```
SOA_26.10_Seminar-main/
│
├── app/                        # Demo App gốc (port 8000)
│   ├── main.py
│   ├── metrics.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── shop-app/                   # 🆕 App bán hàng (port 8001)
│   ├── main.py                 # API endpoints bán hàng
│   ├── metrics.py              # Prometheus metrics
│   ├── requirements.txt
│   └── Dockerfile
│
├── shop-loadgen/               # 🆕 Load generator cho shop-app
│   ├── load_generator.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── loadgen/                    # Load generator cho demo-app
├── prometheus/
│   ├── prometheus.yml          # Cấu hình scrape (demo-app + shop-app)
│   └── alert.rules.yml         # Luật cảnh báo
│
├── grafana/
│   ├── dashboards/
│   │   ├── demo-dashboard.json # Dashboard demo-app
│   │   └── shop-dashboard.json # 🆕 Dashboard bán hàng
│   └── provisioning/           # Cấu hình auto-load datasource & dashboard
│
├── alertmanager/               # Cấu hình cảnh báo (Telegram, Webhook)
├── webhook-receiver/           # Nhận webhook từ Alertmanager
├── scripts/                    # Script demo PowerShell & Bash
├── tests/                      # Unit & Integration tests
│
├── docker-compose.yml          # Điều phối toàn bộ 8 services
├── .env.example                # Mẫu biến môi trường
└── README.md                   # File này
```

---

## 🛑 Dừng Hệ Thống

```powershell
# Dừng tất cả container (giữ lại data)
docker compose down

# Dừng và xóa toàn bộ data (volumes)
docker compose down -v
```

---

## ❓ Xử Lý Lỗi Thường Gặp

**Lỗi: Port đã được dùng**
```powershell
# Kiểm tra cổng nào đang bị chiếm
netstat -ano | findstr :8001
# Đổi cổng trong file .env rồi chạy lại
```

**Container bị `unhealthy` hoặc `exited`**
```powershell
# Xem log của container lỗi
docker compose logs shop-app
docker compose logs prometheus
```

**Grafana không hiện dashboard**
```powershell
# Restart grafana để reload provisioning
docker compose restart grafana
```

**Prometheus không scrape được shop-app**
> Vào http://localhost:9091/targets — kiểm tra target `shop-app` có status `UP` không.
> Nếu `DOWN`, chờ thêm 30 giây để container khởi động xong rồi F5 lại.
