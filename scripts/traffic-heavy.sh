#!/usr/bin/env bash
set -e

DURATION=${1:-30}
RPS=${2:-15.0}
WORKERS=${3:-4}

APP_PORT=8000
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

echo -e "\033[1;33mSINH TAI LON (HEAVY TRAFFIC) - QUAN SAT RPS VOT CAO\033[0m"
echo -e "\033[1;32m[*] Muc tieu: http://localhost:${APP_PORT} trong ${DURATION}s (${WORKERS} workers)...\033[0m"

python3 scripts/traffic_generator.py --mode heavy --duration ${DURATION} --rps ${RPS} --workers ${WORKERS} --url "http://localhost:${APP_PORT}"
