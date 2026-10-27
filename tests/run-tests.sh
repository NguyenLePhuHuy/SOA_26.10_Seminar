#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "THUC THI KIEM THU TU DONG (APP METRICS & WEBHOOK)"

echo -e "\n[*] 1. Kiem tra Unit & Integration Tests cho Demo App Metrics..."
python3 -m pytest "$SCRIPT_DIR/test_metrics.py" -v

echo -e "\n[*] 2. Kiem tra Unit & Integration Tests cho Webhook Receiver..."
python3 -m pytest "$SCRIPT_DIR/test_webhook.py" -v

echo -e "\n[v] TAT CA TEST CASES DA PASS 100%! BAO DAM DO TIN CAY!"
