#!/usr/bin/env bash

WEBHOOK_PORT=5001
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi
PORT=${WEBHOOK_PORT:-5001}

if [ "$1" == "--logs" ] || [ "$1" == "-l" ]; then
    echo -e "\033[1;36mDang hien thi log container webhook-receiver (Ctrl+C de thoat)...\033[0m"
    docker compose logs -f --tail=30 webhook-receiver
    exit 0
fi

if [ "$1" == "--clear" ] || [ "$1" == "-c" ]; then
    curl -s -X DELETE "http://localhost:${PORT}/alerts"
    echo -e "\033[1;32mDa xoa lich su alerts.\033[0m"
    exit 0
fi

echo -e "\033[1;33mTHONG TIN CANH BAO MOI NHAT TREN WEBHOOK RECEIVER\033[0m"

HEALTH=$(curl -s "http://localhost:${PORT}/health" 2>/dev/null)
if [ -z "$HEALTH" ]; then
    echo -e "\033[1;31mKhong the ket noi toi Webhook Receiver tai http://localhost:${PORT}\033[0m"
    exit 1
fi

LATEST=$(curl -s "http://localhost:${PORT}/alerts/latest" 2>/dev/null)
if echo "$LATEST" | grep -q '"status"'; then
    echo -e "\033[1;33m[PAYLOAD NHAN DUOC TU ALERTMANAGER]:\033[0m"
    echo "$LATEST" | python3 -m json.tool 2>/dev/null || echo "$LATEST"
else
    echo -e "\033[1;33mChua co payload alert nao. Chay './scripts/traffic-error.sh' de kich hoat!\033[0m"
fi
