#!/usr/bin/env bash
set -e

DURATION=${1:-45}
RPS=${2:-4.0}

APP_PORT=8000
PROMETHEUS_PORT=9091
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

echo -e "\033[1;31mSINH TAI LOI HTTP 500 DE KICH HOAT DemoHighErrorRate\033[0m"
echo -e "   Xem alerts: \033[1;37mhttp://localhost:${PROMETHEUS_PORT}/alerts\033[0m"
echo -e "   Thoi gian chay: ${DURATION}s..."

python3 scripts/traffic_generator.py --mode error --duration ${DURATION} --rps ${RPS} --url "http://localhost:${APP_PORT}"
