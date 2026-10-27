#!/usr/bin/env bash
set -e

DURATION=${1:-30}
RPS=${2:-4.0}

APP_PORT=8000
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

echo -e "\033[1;32m[*] Gui request thanh cong vao http://localhost:${APP_PORT} trong ${DURATION}s...\033[0m"

python3 scripts/traffic_generator.py --mode normal --duration ${DURATION} --rps ${RPS} --url "http://localhost:${APP_PORT}"
