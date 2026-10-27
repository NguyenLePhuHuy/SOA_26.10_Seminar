param(
    [switch]$Logs,
    [switch]$Clear
)

$webhookPort = "5001"
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^WEBHOOK_PORT=(.+)$") { $webhookPort = $matches[1].Trim() }
    }
}

if ($Logs) {
    Write-Host "[*] Dang hien thi log container webhook-receiver (Ctrl+C de thoat)..." -ForegroundColor Cyan
    docker compose logs -f --tail=30 webhook-receiver
    exit 0
}

if ($Clear) {
    Write-Host "[*] Dang xoa lich su alerts tren Webhook Receiver..." -ForegroundColor Yellow
    try {
        $res = Invoke-RestMethod -Uri "http://localhost:$webhookPort/alerts" -Method Delete
        Write-Host "[v] $($res.message)" -ForegroundColor Green
    } catch {
        Write-Host "[X] Khong the ket noi toi Webhook Receiver tai http://localhost:$webhookPort" -ForegroundColor Red
    }
    exit 0
}

Write-Host "THONG TIN CANH BAO MOI NHAT TREN WEBHOOK RECEIVER" -ForegroundColor Yellow

try {
    $health = Invoke-RestMethod -Uri "http://localhost:$webhookPort/health" -TimeoutSec 2
    Write-Host "[v] Trang thai Receiver: $($health.status) | Tong alerts da nhan: $($health.received_count)" -ForegroundColor Green
} catch {
    Write-Host "[X] Khong the ket noi toi Webhook Receiver tai http://localhost:$webhookPort/health" -ForegroundColor Red
    Write-Host "    Hay dam bao docker compose da khoi chay ('docker compose up -d')." -ForegroundColor Yellow
    exit 1
}

try {
    $latest = Invoke-RestMethod -Uri "http://localhost:$webhookPort/alerts/latest" -TimeoutSec 3
    $statusColor = if ($latest.status -eq 'firing') { 'Red' } else { 'Green' }
    Write-Host "`n[!] [CANH BAO NHAN DUOC TU ALERTMANAGER]:" -ForegroundColor Yellow
    Write-Host "  * Thoi diem nhan : $($latest.received_at)" -ForegroundColor White
    Write-Host "  * Trang thai     : $($latest.status.ToUpper())" -ForegroundColor $statusColor
    Write-Host "  * Receiver       : $($latest.receiver)" -ForegroundColor White
    Write-Host "  * Alert Name     : $($latest.commonLabels.alertname)" -ForegroundColor Cyan
    Write-Host "  * Muc do         : $($latest.commonLabels.severity)" -ForegroundColor Yellow
    Write-Host "  * Dich vu        : $($latest.commonLabels.service)" -ForegroundColor White
    Write-Host "  * Tom tat        : $($latest.commonAnnotations.summary)" -ForegroundColor White
    Write-Host "  * Mo ta          : $($latest.commonAnnotations.description)" -ForegroundColor Gray
    if ($latest.commonAnnotations.action) {
        Write-Host "  * Khac phuc      : $($latest.commonAnnotations.action)" -ForegroundColor Cyan
    }
    Write-Host "  * So alerts gom  : $($latest.alerts_count)" -ForegroundColor White
    Write-Host "[*] Meo: Chay '.\scripts\view-webhook.ps1 -Logs' de xem live log!" -ForegroundColor Cyan
} catch {
    Write-Host "`n[i] Chua nhan duoc payload alert nao tu Alertmanager." -ForegroundColor Yellow
    Write-Host "    (Hay chay '.\scripts\traffic-error.ps1' de kich hoat alert DemoHighErrorRate)`n" -ForegroundColor Gray
}
