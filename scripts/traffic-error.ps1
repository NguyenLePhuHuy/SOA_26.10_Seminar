param(
    [int]$Duration = 45,
    [double]$Rps = 4.0
)

$appPort = "8000"
$promPort = "9091"
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^APP_PORT=(.+)$") { $appPort = $matches[1].Trim() }
        if ($_ -match "^PROMETHEUS_PORT=(.+)$") { $promPort = $matches[1].Trim() }
    }
}

Write-Host "SINH TAI LOI HTTP 500 DE KICH HOAT DemoHighErrorRate" -ForegroundColor Yellow
Write-Host "   Mo tab Alert tren Prometheus: http://localhost:$promPort/alerts" -ForegroundColor White
Write-Host "   Theo doi trang thai: INACTIVE -> PENDING (vang) -> FIRING (do)" -ForegroundColor Cyan
Write-Host "   Thoi gian chay: $Duration giay (can vuot nguong > 5% lien tuc 30s)...`n" -ForegroundColor Gray

python scripts/traffic_generator.py --mode error --duration $Duration --rps $Rps --url "http://localhost:$appPort"
