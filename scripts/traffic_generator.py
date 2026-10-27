#!/usr/bin/env python3

import argparse
import concurrent.futures
import os
import random
import sys
import time
import requests

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def load_env_file():
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        os.path.join(os.getcwd(), ".env"),
    ]
    for env_path in candidates:
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip()
                            if k not in os.environ:
                                os.environ[k] = v
                break
            except Exception:
                pass


load_env_file()


def get_base_url():
    port = os.getenv("APP_PORT", "8000")
    host = os.getenv("APP_HOST", "localhost")
    return f"http://{host}:{port}"


def send_single_request(url: str, timeout: float = 5.0):
    start = time.perf_counter()
    try:
        res = requests.get(url, timeout=timeout)
        duration_ms = (time.perf_counter() - start) * 1000
        return res.status_code, duration_ms, None
    except requests.exceptions.Timeout:
        duration_ms = (time.perf_counter() - start) * 1000
        return 0, duration_ms, f"Timeout after {timeout}s"
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        return 0, duration_ms, str(exc)


def run_load(mode: str, duration: int, rps: float, base_url: str, workers: int = 1):
    mode_normalized = mode.lower()
    if mode_normalized == "slow":
        mode_normalized = "latency"

    print(f"\nBAT DAU KICH BAN TAI: [{mode_normalized.upper()}]")
    print(f"Muc tieu: {base_url}")
    print(f"Thoi luong: {duration} giay | Toc do dinh huong: ~{rps} req/giay | Luong: {workers}\n")

    end_time = time.time() + duration
    delay = 1.0 / max(rps, 0.1) if rps > 0 else 0.05
    stats = {"total": 0, "200": 0, "500": 0, "other": 0, "timeouts": 0}

    def choose_endpoint():
        if mode_normalized == "normal":
            return "/work" if random.random() < 0.90 else "/"
        elif mode_normalized == "heavy":
            r = random.random()
            if r < 0.85:
                return "/work"
            elif r < 0.95:
                return "/"
            else:
                return "/slow?delay=0.1"
        elif mode_normalized == "error":
            return "/error?status=500" if random.random() < 0.70 else "/work"
        elif mode_normalized == "latency":
            return "/slow?delay=1.5" if random.random() < 0.70 else "/work"
        elif mode_normalized == "chaos":
            r = random.random()
            if r < 0.40:
                return "/work"
            elif r < 0.70:
                return "/slow?delay=1.2"
            elif r < 0.95:
                return "/error?status=500"
            else:
                return "/health"
        else:
            return "/work"

    try:
        if workers > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                while time.time() < end_time:
                    futures = []
                    batch_size = max(1, int(rps / 2)) if rps > 0 else workers
                    for _ in range(batch_size):
                        endpoint = choose_endpoint()
                        futures.append(executor.submit(send_single_request, f"{base_url}{endpoint}"))
                    
                    for fut in concurrent.futures.as_completed(futures):
                        status, dur_ms, err = fut.result()
                        stats["total"] += 1
                        if status == 200:
                            stats["200"] += 1
                            symbol = "[OK]"
                        elif status >= 500:
                            stats["500"] += 1
                            symbol = "[ERR]"
                        else:
                            stats["other"] += 1
                            symbol = "[WARN]"
                        print(f"{symbol} [{time.strftime('%X')}] HTTP {status:<4} ({dur_ms:.1f}ms)")
                    time.sleep(delay)
        else:
            while time.time() < end_time:
                endpoint = choose_endpoint()
                status, dur_ms, err = send_single_request(f"{base_url}{endpoint}")
                stats["total"] += 1

                if status == 200:
                    stats["200"] += 1
                    symbol = "[OK]"
                elif status >= 500:
                    stats["500"] += 1
                    symbol = "[ERR]"
                else:
                    stats["other"] += 1
                    symbol = "[WARN]"

                print(f"{symbol} [{time.strftime('%X')}] GET {endpoint:<25} -> {status} ({dur_ms:.1f}ms)")
                time.sleep(delay)

    except KeyboardInterrupt:
        print("\nNguoi dung ngat tai an toan (Ctrl+C).")

    print(f"\nKET QUA KICH BAN TAI [{mode_normalized.upper()}]:")
    print(f"   - Tong so request : {stats['total']}")
    print(f"   - HTTP 200 (OK)   : {stats['200']}")
    print(f"   - HTTP 500 (Loi)  : {stats['500']}")
    print(f"   - Khac / Timeout  : {stats['other']}")
    if stats["total"] > 0:
        error_rate = (stats["500"] / stats["total"]) * 100
        print(f"   - Ti le loi thuc te : {error_rate:.1f}%\n")


def toggle_chaos(base_url: str, enabled: bool, error_rate: float, latency: float):
    url = f"{base_url}/chaos?enabled={'true' if enabled else 'false'}&error_rate={error_rate}&latency={latency}"
    try:
        res = requests.post(url, timeout=3)
        if res.status_code == 200:
            status_text = "BAT (ON)" if enabled else "TAT (OFF)"
            print(f"\nDa cap nhat Chaos Mode: {status_text}")
            print(f"   - Error Rate injected: {error_rate * 100:.0f}%")
            print(f"   - Extra Latency: {latency}s")
            print(f"   - Theo doi phan hoi tuc thi tren Prometheus va Grafana!\n")
        else:
            print(f"That bai: HTTP {res.status_code} - {res.text}")
    except Exception as exc:
        print(f"Khong the ket noi toi Demo App: {exc}")


def stop_load(base_url: str):
    print("\nDang gui yeu cau dung va tat moi che do tiem loi...")
    toggle_chaos(base_url, enabled=False, error_rate=0.0, latency=0.0)
    print("He thong da duoc khoi phuc ve trang thai binh thuong (Recovery Mode).\n")


def main():
    parser = argparse.ArgumentParser(description="Traffic Generator & Chaos Testing for Workshop")
    parser.add_argument("--mode", choices=["normal", "heavy", "error", "latency", "slow", "chaos", "stop"], default="normal",
                        help="Kich ban sinh tai: normal, heavy, error (500), latency/slow (cham), chaos, stop (khoi phuc)")
    parser.add_argument("--duration", type=int, default=30, help="Thoi gian chay tinh bang giay (mac dinh 30s)")
    parser.add_argument("--rps", type=float, default=3.0, help="So request moi giay (mac dinh 3 req/s)")
    parser.add_argument("--workers", type=int, default=1, help="So luong worker thread dong thoi (mac dinh 1, tang khi chay heavy)")
    parser.add_argument("--url", type=str, default="", help="URL cua demo app (mac dinh http://localhost:8000)")
    parser.add_argument("--chaos-enable", action="store_true", help="Kich hoat Chaos Mode tren server")
    parser.add_argument("--chaos-disable", action="store_true", help="Vo hieu hoa Chaos Mode tren server")
    parser.add_argument("--error-rate", type=float, default=0.5, help="Ti le loi khi bat Chaos Mode (0.0 - 1.0)")
    parser.add_argument("--extra-latency", type=float, default=1.0, help="Do tre bo sung khi bat Chaos Mode (giay)")

    args = parser.parse_args()
    base_url = args.url if args.url else get_base_url()

    if args.mode == "stop" or args.chaos_disable:
        stop_load(base_url)
        return

    if args.chaos_enable:
        toggle_chaos(base_url, enabled=True, error_rate=args.error_rate, latency=args.extra_latency)
        return

    workers = args.workers
    rps = args.rps
    if args.mode == "heavy" and workers == 1:
        workers = 4
        if rps <= 3.0:
            rps = 15.0

    run_load(mode=args.mode, duration=args.duration, rps=rps, base_url=base_url, workers=workers)


if __name__ == "__main__":
    main()
