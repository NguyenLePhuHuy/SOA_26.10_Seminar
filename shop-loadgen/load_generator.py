import os
import random
import sys
import time
import requests

TARGET_URL = os.getenv("TARGET_URL", "http://shop-app:8001")
MODE = os.getenv("MODE", "NORMAL").upper()
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0.3"))

print("[SHOP-LOADGEN] Khởi động Shop Load Generator...")
print(f"Target: {TARGET_URL} | Mode: {MODE} | Delay: {REQUEST_DELAY}s")

PRODUCTS = ["P001", "P002", "P003", "P004", "P005", "P006", "P007", "P008"]
PAYMENT_METHODS = ["credit_card", "momo", "vnpay", "cod"]
SEARCH_TERMS = ["iphone", "samsung", "áo", "quần", "cơm", "trà sữa", "laptop", "tai nghe", "điện tử", "xyz_not_found"]


def wait_for_target():
    url = f"{TARGET_URL}/health"
    for attempt in range(1, 31):
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                print(f"[SHOP-LOADGEN] Shop App sẵn sàng (attempt {attempt})")
                return True
        except Exception:
            pass
        time.sleep(1)
    print("[SHOP-LOADGEN] Không kết nối được, tiếp tục...")
    return False


def browse():
    """Xem sản phẩm ngẫu nhiên"""
    pid = random.choice(PRODUCTS)
    try:
        r = requests.get(f"{TARGET_URL}/products/{pid}", timeout=3)
        print(f"[{time.strftime('%X')}] VIEW   /products/{pid}  -> {r.status_code}")
    except Exception as e:
        print(f"[{time.strftime('%X')}] VIEW   ERROR: {e}")


def search():
    """Tìm kiếm sản phẩm"""
    q = random.choice(SEARCH_TERMS)
    try:
        r = requests.get(f"{TARGET_URL}/search", params={"q": q}, timeout=3)
        print(f"[{time.strftime('%X')}] SEARCH q={q!r:20} -> {r.status_code}")
    except Exception as e:
        print(f"[{time.strftime('%X')}] SEARCH ERROR: {e}")


def full_purchase():
    """Mô phỏng luồng mua hàng hoàn chỉnh: view -> cart -> order -> payment"""
    try:
        pid = random.choice(PRODUCTS)
        qty = random.randint(1, 2)

        # Add to cart
        r = requests.post(f"{TARGET_URL}/cart", params={"product_id": pid, "quantity": qty}, timeout=3)
        if r.status_code != 200:
            print(f"[{time.strftime('%X')}] CART   FAILED {r.status_code} (Het hang). Tu dong nap kho...")
            requests.post(f"{TARGET_URL}/inventory/restock", params={"quantity": 100}, timeout=3)
            return
        sid = r.json().get("session_id")
        print(f"[{time.strftime('%X')}] CART   session={sid} product={pid} qty={qty}")

        time.sleep(random.uniform(0.05, 0.15))

        # Place order
        r2 = requests.post(f"{TARGET_URL}/order", params={"session_id": sid}, timeout=5)
        order_data = r2.json()
        print(f"[{time.strftime('%X')}] ORDER  {order_data.get('order_id','')} -> {r2.status_code}")

        if r2.status_code == 200:
            order_id = order_data.get("order_id", "ORD-UNKNOWN")
            amount = order_data.get("total_value_vnd", 100000)
            method = random.choice(PAYMENT_METHODS)

            time.sleep(random.uniform(0.05, 0.2))

            # Payment
            r3 = requests.post(f"{TARGET_URL}/payment",
                               params={"order_id": order_id, "method": method, "amount": amount},
                               timeout=5)
            print(f"[{time.strftime('%X')}] PAY    {order_id} via {method} -> {r3.status_code}")

    except Exception as e:
        print(f"[{time.strftime('%X')}] PURCHASE ERROR: {e}")


def simulate_bulk():
    """Gửi simulate request"""
    try:
        num = random.randint(3, 10)
        r = requests.post(f"{TARGET_URL}/shop/simulate", params={"num_orders": num}, timeout=10)
        print(f"[{time.strftime('%X')}] SIMULATE {num} orders -> {r.status_code}")
    except Exception as e:
        print(f"[{time.strftime('%X')}] SIMULATE ERROR: {e}")


def run_normal():
    r = random.random()
    if r < 0.35:
        browse()
    elif r < 0.55:
        search()
    elif r < 0.80:
        full_purchase()
    else:
        simulate_bulk()


def run_heavy():
    for _ in range(4):
        full_purchase()
        time.sleep(0.1)


def run_browse_only():
    for _ in range(3):
        browse()
        search()
        time.sleep(0.1)


def main():
    wait_for_target()
    print("[SHOP-LOADGEN] Bắt đầu sinh traffic...")

    while True:
        try:
            if MODE == "HEAVY":
                run_heavy()
            elif MODE == "BROWSE":
                run_browse_only()
            else:
                run_normal()

            time.sleep(REQUEST_DELAY)
        except KeyboardInterrupt:
            print("\n[SHOP-LOADGEN] Đã dừng.")
            sys.exit(0)
        except Exception as e:
            print(f"[SHOP-LOADGEN] Exception: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
