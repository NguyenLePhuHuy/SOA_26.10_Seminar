#!/usr/bin/env bash
set -e

echo -e "\033[1;33mPROMETHEUS & GRAFANA WORKSHOP - KHOI DONG HE THONG\033[0m"

if ! docker info > /dev/null 2>&1; then
    echo -e "\033[1;31m[X] LOI: Docker chua duoc bat! Vui long khoi dong Docker daemon.\033[0m"
    exit 1
fi

APP_PORT=8000
PROMETHEUS_PORT=9091
GRAFANA_PORT=3005
ALERTMANAGER_PORT=9093
WEBHOOK_PORT=5001

if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

echo -e "\033[1;32m[*] Dang khoi chay Docker Compose...\033[0m"
docker compose up -d --build

echo -e "\033[1;33m[*] Dang cho Demo App san sang...\033[0m"
for i in {1..15}; do
    if curl -s http://localhost:${APP_PORT}/health | grep -q '"UP"'; then
        echo -e "\033[1;32m[v] Demo App da san sang!\033[0m"
        break
    fi
    sleep 1
done

echo -e "\n\033[1;33mTRUY CAP CAC DICH VU TREN TRINH DUYET CUA BAN:\033[0m"
echo -e "  1. Demo App API   : \033[1;37mhttp://localhost:${APP_PORT}\033[0m"
echo -e "  2. Metrics Raw    : \033[1;37mhttp://localhost:${APP_PORT}/metrics\033[0m"
echo -e "  3. Prometheus Web : \033[1;37mhttp://localhost:${PROMETHEUS_PORT}\033[0m"
echo -e "     -> Xem Targets : http://localhost:${PROMETHEUS_PORT}/targets"
echo -e "     -> Xem Alerts  : http://localhost:${PROMETHEUS_PORT}/alerts"
echo -e "  4. Alertmanager UI: \033[1;37mhttp://localhost:${ALERTMANAGER_PORT:-9093}\033[0m"
echo -e "     -> Xem Routing : http://localhost:${ALERTMANAGER_PORT:-9093}/#/alerts"
echo -e "  5. Grafana Dash   : \033[1;37mhttp://localhost:${GRAFANA_PORT}\033[0m"
echo -e "     -> Tai khoan   : admin / admin"
echo -e "  6. Webhook Notif  : \033[1;37mhttp://localhost:${WEBHOOK_PORT:-5001}/alerts/latest\033[0m"
echo -e "     -> Xem Logs    : docker compose logs -f webhook-receiver\n"
