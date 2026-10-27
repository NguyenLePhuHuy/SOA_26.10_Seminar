#!/usr/bin/env bash
set -e

APP_PORT=8000
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

echo -e "\033[1;33mDUNG SINH TAI VA KHOI PHUC HE THONG (RECOVERY)\033[0m"

python3 scripts/traffic_generator.py --mode stop --url "http://localhost:${APP_PORT}"
