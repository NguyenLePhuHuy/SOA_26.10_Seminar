param(
    [switch]$Auto,
    [int]$Duration = 45,
    [int]$Rps = 6
)

$appPort = "8000"
$promPort = "9091"
$grafPort = "3005"
$alertPort = "9093"
$webhookPort = "5001"

if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^APP_PORT=(.+)$") { $appPort = $matches[1].Trim() }
        if ($_ -match "^PROMETHEUS_PORT=(.+)$") { $promPort = $matches[1].Trim() }
        if ($_ -match "^GRAFANA_PORT=(.+)$") { $grafPort = $matches[1].Trim() }
        if ($_ -match "^ALERTMANAGER_PORT=(.+)$") { $alertPort = $matches[1].Trim() }
        if ($_ -match "^WEBHOOK_PORT=(.+)$") { $webhookPort = $matches[1].Trim() }
    }
}

Write-Host "KIEM THU VONG DOI CANH BAO: FIRING & RESOLVED" -ForegroundColor Yellow
Write-Host "(2 Co che: Webhook Receiver JSON + Telegram Push Notif)" -ForegroundColor Yellow

Write-Host "`n[BUOC 1] Danh sach cac tab quan sat:" -ForegroundColor Yellow
Write-Host "  -> Prometheus Alerts : http://localhost:$promPort/alerts" -ForegroundColor White
Write-Host "  -> Alertmanager UI   : http://localhost:$alertPort/#/alerts" -ForegroundColor White
Write-Host "  -> Grafana Dashboard : http://localhost:$grafPort" -ForegroundColor White
Write-Host "  -> Webhook Payload   : http://localhost:$webhookPort/alerts/latest" -ForegroundColor White
Write-Host "  -> Webhook Logs Live : docker compose logs -f webhook-receiver" -ForegroundColor Gray
Write-Host "  -> Telegram Chatbot  : Mo cuoc tro chuyen bot tren dien thoai/desktop" -ForegroundColor Cyan
Write-Host "  (Trang thai ban dau cua 'DemoHighErrorRate' la: INACTIVE)`n" -ForegroundColor Green

if (-not $Auto) {
    Read-Host "Nhan ENTER de bat dau tiem loi (Phase 1: Trigger Alert)..."
}

try {
    Invoke-RestMethod -Uri "http://localhost:$webhookPort/alerts" -Method Delete -ErrorAction SilentlyContinue | Out-Null
    Write-Host "[*] Da dat lai bo nho tam cua Webhook Receiver." -ForegroundColor Gray
} catch {}

Write-Host "`n[BUOC 2] Bat dau tiem loi 500 lien tuc trong $Duration giay (RPS=$Rps)..." -ForegroundColor Red
Write-Host "  * Giay 0 - 5  : Ti le loi vuot nguong 5%, Prometheus phat hien." -ForegroundColor Gray
Write-Host "  * Giay 5 - 30 : Alert chuyen sang mau vang [PENDING] (cho dieu kien 'for: 30s')." -ForegroundColor Yellow
Write-Host "  * Giay 30+    : Alert chuyen sang mau do [FIRING] tren Prometheus." -ForegroundColor Red
Write-Host "  * Giay 35+    : Alertmanager dieu phoi va gui:" -ForegroundColor Cyan
Write-Host "                  1) HTTP POST JSON toi Webhook Receiver" -ForegroundColor White
Write-Host "                  2) Push Notification toi Telegram Bot" -ForegroundColor White

python scripts/traffic_generator.py --mode error --duration $Duration --rps $Rps --url "http://localhost:$appPort"

Write-Host "`n[BUOC 3] Dang cho va xac minh thong bao FIRING..." -ForegroundColor Yellow
$firingReceived = $false
for ($i = 1; $i -le 25; $i++) {
    try {
        $latest = Invoke-RestMethod -Uri "http://localhost:$webhookPort/alerts/latest" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($latest -and $latest.status -eq "firing") {
            $firingReceived = $true
            Write-Host "`n[v] [XAC MINH THANH CONG] Webhook Receiver da nhan duoc HTTP POST FIRING tu Alertmanager!" -ForegroundColor Green
            Write-Host "   - Alert Name : $($latest.commonLabels.alertname)" -ForegroundColor White
            Write-Host "   - Severity   : $($latest.commonLabels.severity)" -ForegroundColor White
            Write-Host "   - Summary    : $($latest.commonAnnotations.summary)" -ForegroundColor White
            Write-Host "   - StartsAt   : $($latest.payload.alerts[0].startsAt)" -ForegroundColor Gray
            break
        }
    } catch {}
    Write-Host "  ... Dang cho Alertmanager hoan tat group_wait va gui POST ($i/25s)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if (-not $firingReceived) {
    Write-Host "[!] Chua phat hien FIRING tren Webhook trong thoi gian cho. Kiem tra tab Prometheus Alerts!" -ForegroundColor Yellow
}

Write-Host "`n[BUOC 4] Loi da dung! He thong buoc vao giai doan tu phuc hoi (RECOVERY)..." -ForegroundColor Green
Write-Host "  * PromQL rate(5xx)[1m] se giam dan ve 0 khi khong con request loi." -ForegroundColor Gray
Write-Host "  * Alert tren Prometheus chuyen tu [FIRING] -> [INACTIVE]." -ForegroundColor Gray
Write-Host "  * Alertmanager danh gia va gui thong bao [RESOLVED]:" -ForegroundColor Cyan
Write-Host "    1) HTTP POST JSON status: resolved toi Webhook Receiver" -ForegroundColor White
Write-Host "    2) Push Notification RESOLVED toi Telegram Bot" -ForegroundColor White
Write-Host "  (Giai doan nay can khoang 60-90 giay do cua so truot 1 phut va chu ky scrape 5s)`n" -ForegroundColor Gray

if (-not $Auto) {
    Write-Host "Dang theo doi tu dong chuyen trang thai RESOLVED..." -ForegroundColor Yellow
}

$resolvedReceived = $false
for ($i = 1; $i -le 50; $i++) {
    try {
        $latest = Invoke-RestMethod -Uri "http://localhost:$webhookPort/alerts/latest" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($latest -and $latest.status -eq "resolved") {
            $resolvedReceived = $true
            Write-Host "`n[v] [XAC MINH THANH CONG] Webhook Receiver da nhan duoc thong bao RESOLVED!" -ForegroundColor Green
            Write-Host "   - Alert Name : $($latest.commonLabels.alertname)" -ForegroundColor White
            Write-Host "   - Status     : RESOLVED" -ForegroundColor Green
            Write-Host "   - EndsAt     : $($latest.payload.alerts[0].endsAt)" -ForegroundColor Gray
            break
        }
    } catch {}
    Write-Host "  ... Dang cho he thong phuc hoi va Alertmanager gui resolved ($($i*3)s / 150s)" -ForegroundColor Gray
    Start-Sleep -Seconds 3
}

if (-not $resolvedReceived) {
    Write-Host "[i] Chua nhan duoc payload RESOLVED trong 150s. Ban co the kiem tra lai tai: http://localhost:$webhookPort/alerts/latest" -ForegroundColor Yellow
}

Write-Host "`nTONG KET KICH BAN KIEM CHUNG ALERT LIFECYCLE" -ForegroundColor Yellow
Write-Host "  1. Kich hoat loi thanh cong (DemoHighErrorRate)" -ForegroundColor White
$firingStatusText = if ($firingReceived) { 'PASS [v]' } else { 'CHECK' }
$firingColor = if ($firingReceived) { 'Green' } else { 'Yellow' }
Write-Host "  2. FIRING Webhook Notification : $firingStatusText" -ForegroundColor $firingColor
$resolvedStatusText = if ($resolvedReceived) { 'PASS [v]' } else { 'CHECK' }
$resolvedColor = if ($resolvedReceived) { 'Green' } else { 'Yellow' }
Write-Host "  3. RESOLVED Webhook Notif      : $resolvedStatusText" -ForegroundColor $resolvedColor
Write-Host "  4. Telegram Push Notification  : Xem tin nhan truc tiep tren dien thoai/bot" -ForegroundColor Cyan
Write-Host ""
