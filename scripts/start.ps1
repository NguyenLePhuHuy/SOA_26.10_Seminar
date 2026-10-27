$ErrorActionPreference = "Stop"

Write-Host "PROMETHEUS & GRAFANA WORKSHOP - KHOI DONG HE THONG" -ForegroundColor Yellow

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[X] LOI: Khong tim thay lenh 'docker'. Vui long cai dat Docker Desktop!" -ForegroundColor Red
    exit 1
}
docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] LOI: Docker daemon chua duoc bat hoac Docker Desktop chua khoi dong!" -ForegroundColor Red
    Write-Host "    Vui long mo Docker Desktop va thu lai." -ForegroundColor Yellow
    exit 1
}

$appPort = "8000"
$promPort = "9091"
$grafPort = "3005"
$alertPort = "9093"
$webhookPort = "5001"

if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#")) {
            $parts = $line.Split("=", 2)
            if ($parts.Count -eq 2) {
                if ($parts[0] -eq "APP_PORT") { $appPort = $parts[1] }
                if ($parts[0] -eq "PROMETHEUS_PORT") { $promPort = $parts[1] }
                if ($parts[0] -eq "GRAFANA_PORT") { $grafPort = $parts[1] }
                if ($parts[0] -eq "ALERTMANAGER_PORT") { $alertPort = $parts[1] }
                if ($parts[0] -eq "WEBHOOK_PORT") { $webhookPort = $parts[1] }
            }
        }
    }
}

Write-Host "[*] Dang khoi chay Docker Compose..." -ForegroundColor Green
docker compose up -d --build

Write-Host "`n[*] Dang cho Demo App va Webhook Receiver san sang..." -ForegroundColor Yellow
$healthy = $false
for ($i = 1; $i -le 15; $i++) {
    try {
        $res = Invoke-RestMethod -Uri "http://localhost:$appPort/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($res.status -eq "UP") {
            $healthy = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 1
}

if ($healthy) {
    Write-Host "[v] Tat ca dich vu da san sang!" -ForegroundColor Green
} else {
    Write-Host "[!] Dang khoi dong nen, hay cho them vai giay..." -ForegroundColor Yellow
}

Write-Host "`nTRUY CAP CAC DICH VU TREN TRINH DUYET CUA BAN:" -ForegroundColor Yellow
Write-Host "  1. Demo App API   : http://localhost:$appPort" -ForegroundColor White
Write-Host "  2. Metrics Raw    : http://localhost:$appPort/metrics" -ForegroundColor White
Write-Host "  3. Prometheus Web : http://localhost:$promPort" -ForegroundColor White
Write-Host "     -> Xem Targets : http://localhost:$promPort/targets" -ForegroundColor Gray
Write-Host "     -> Xem Alerts  : http://localhost:$promPort/alerts" -ForegroundColor Gray
Write-Host "  4. Alertmanager UI: http://localhost:$alertPort" -ForegroundColor White
Write-Host "     -> Xem Routing : http://localhost:$alertPort/#/alerts" -ForegroundColor Gray
Write-Host "  5. Grafana Dash   : http://localhost:$grafPort" -ForegroundColor White
Write-Host "     -> Tai khoan   : admin / admin" -ForegroundColor Gray
Write-Host "  6. Webhook Notif  : http://localhost:$webhookPort/alerts/latest" -ForegroundColor White
Write-Host "     -> Xem Logs    : docker compose logs -f webhook-receiver" -ForegroundColor Gray
Write-Host "`n[*] Chay lenh sau de thu nghiem tao loi: " -ForegroundColor Yellow
Write-Host "    .\scripts\traffic-error.ps1`n" -ForegroundColor White
