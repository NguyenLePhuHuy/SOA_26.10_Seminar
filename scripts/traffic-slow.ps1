param(
    [int]$Duration = 45,
    [double]$Rps = 3.0
)

$appPort = "8000"
$promPort = "9091"
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^APP_PORT=(.+)$") { $appPort = $matches[1].Trim() }
        if ($_ -match "^PROMETHEUS_PORT=(.+)$") { $promPort = $matches[1].Trim() }
    }
}

Write-Host "SINH TAI DO TRE CAO DE KICH HOAT DemoHighLatency (>0.5s)" -ForegroundColor Yellow
Write-Host "   Mo bieu do p95 tren Grafana va Alert: http://localhost:$promPort/alerts" -ForegroundColor Cyan
Write-Host "   Theo doi: INACTIVE -> PENDING (vang) -> FIRING (do)" -ForegroundColor White
Write-Host "   Thoi gian chay: $Duration giay (can vuot nguong > 500ms lien tuc 30s)...`n" -ForegroundColor Gray

python scripts/traffic_generator.py --mode latency --duration $Duration --rps $Rps --url "http://localhost:$appPort"
