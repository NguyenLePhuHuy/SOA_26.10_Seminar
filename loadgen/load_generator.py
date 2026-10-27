import os
import random
import sys
import time
import requests

TARGET_URL = os.getenv("TARGET_URL", "http://demo-app:8000")
MODE = os.getenv("MODE", "NORMAL").upper()
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0.5"))

print("[LOADGEN] Starting Load Generator Container...")
print(f"Target URL : {TARGET_URL}")
print(f"Active Mode: {MODE}")
print(f"Base Delay : {REQUEST_DELAY}s")


def wait_for_target():
    health_url = f"{TARGET_URL}/health"
    print(f"Dang kiem tra ket noi toi {health_url}...")
    for attempt in range(1, 31):
        try:
            res = requests.get(health_url, timeout=2)
            if res.status_code == 200:
                print(f"Demo App da san sang (Attempt {attempt})!")
                return True
        except Exception:
            pass
        time.sleep(1)
    print("Khong the ket noi toi Demo App sau 30 giay. Van tiep tuc thu...")
    return False


def send_request(endpoint: str, timeout: float = 5.0):
    url = f"{TARGET_URL}{endpoint}"
    try:
        res = requests.get(url, timeout=timeout)
        print(f"[{time.strftime('%X')}] GET {endpoint:<25} -> HTTP {res.status_code}")
    except requests.exceptions.Timeout:
        print(f"[{time.strftime('%X')}] GET {endpoint:<25} -> Timeout ({timeout}s)")
    except Exception as exc:
        print(f"[{time.strftime('%X')}] GET {endpoint:<25} -> Error: {exc}")


def run_normal():
    r = random.random()
    if r < 0.85:
        send_request("/work")
    elif r < 0.95:
        send_request("/")
    else:
        send_request("/slow?delay=0.2")


def run_heavy():
    for _ in range(5):
        send_request("/work")
        time.sleep(0.05)


def run_error():
    if random.random() < 0.70:
        send_request("/error?status=500")
    else:
        send_request("/work")


def run_latency():
    if random.random() < 0.80:
        send_request("/slow?delay=1.5", timeout=3.0)
    else:
        send_request("/work")


def run_chaos():
    r = random.random()
    if r < 0.45:
        send_request("/work")
    elif r < 0.70:
        send_request("/slow?delay=1.2", timeout=3.0)
    elif r < 0.90:
        send_request("/error?status=500")
    else:
        send_request("/health")


def main():
    wait_for_target()
    print("Bat dau sinh tai lien tuc theo che do...")

    while True:
        try:
            if MODE in ("ERROR", "ERROR_BURST"):
                run_error()
            elif MODE in ("LATENCY", "SLOW", "SLOW_SPIKE"):
                run_latency()
            elif MODE == "HEAVY":
                run_heavy()
            elif MODE == "CHAOS":
                run_chaos()
            else:
                run_normal()

            time.sleep(REQUEST_DELAY)
        except KeyboardInterrupt:
            print("\nLoad Generator da dung an toan.")
            sys.exit(0)
        except Exception as e:
            print(f"Exception in main loop: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
