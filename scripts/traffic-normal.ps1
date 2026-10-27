param(
    [int]$Duration = 30,
    [double]$Rps = 4.0
)

$appPort = "8000"
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^APP_PORT=(.+)$") { $appPort = $matches[1].Trim() }
    }
}

Write-Host "[*] Dang gui request thanh cong vao http://localhost:$appPort trong $Duration giay..." -ForegroundColor Green
python scripts/traffic_generator.py --mode normal --duration $Duration --rps $Rps --url "http://localhost:$appPort"
