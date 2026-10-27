#!/usr/bin/env bash
set -e

APP_PORT=8000
PROMETHEUS_PORT=9091
GRAFANA_PORT=3005
ALERTMANAGER_PORT=9093
WEBHOOK_PORT=5001

if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

echo -e "\033[1;33mKIEM THU VONG DOI CANH BAO: FIRING & RESOLVED\033[0m"
echo -e "\033[1;33m(2 Co che: Webhook Receiver JSON + Telegram Push Notif)\033[0m"
echo -e "\n[BUOC 1] Hay mo cac tab sau tren trinh duyet va dien thoai:"
echo -e "  -> Prometheus Alerts : \033[1;37mhttp://localhost:${PROMETHEUS_PORT}/alerts\033[0m"
echo -e "  -> Alertmanager UI   : \033[1;37mhttp://localhost:${ALERTMANAGER_PORT:-9093}/#/alerts\033[0m"
echo -e "  -> Grafana Dashboard : \033[1;37mhttp://localhost:${GRAFANA_PORT}\033[0m"
echo -e "  -> Webhook Payload   : \033[1;37mhttp://localhost:${WEBHOOK_PORT:-5001}/alerts/latest\033[0m"
echo -e "  -> Webhook Logs Live : docker compose logs -f webhook-receiver"
echo -e "  -> Telegram Chat     : Mo doan chat bot Telegram cua ban"
echo -e "  (Trang thai ban dau: INACTIVE)\n"

curl -s -X DELETE "http://localhost:${WEBHOOK_PORT:-5001}/alerts" > /dev/null 2>&1 || true

read -p "Nhan ENTER de bat dau tiem loi (Phase 1: Trigger Alert)..."

echo -e "\n\033[1;31m[BUOC 2] Bat dau tiem loi 500 lien tuc trong 45 giay...\033[0m"
echo -e "  * Giay 5-30: Alert DemoHighErrorRate chuyen mau vang [PENDING] (for: 30s)"
echo -e "  * Giay 30+ : Alert chuyen mau do [FIRING] tren Prometheus"
echo -e "  * Giay 35+ : Alertmanager gui thong bao FIRING toi Webhook Receiver & Telegram!"

python3 scripts/traffic_generator.py --mode error --duration 45 --rps 6 --url "http://localhost:${APP_PORT}"

echo -e "\n\033[1;33m[BUOC 3] Kiem tra payload nhan duoc tren Webhook Receiver:\033[0m"
sleep 5
curl -s "http://localhost:${WEBHOOK_PORT:-5001}/alerts/latest" | python3 -m json.tool || true

echo -e "\n\033[1;32m[BUOC 4] Loi da dung! He thong tu phuc hoi (Recovery)...\033[0m"
echo -e "  * Alert se quay lai trang thai [INACTIVE] tren Prometheus sau ~60s"
echo -e "  * Alertmanager gui thong bao [RESOLVED] toi Webhook Receiver & Telegram!\n"
