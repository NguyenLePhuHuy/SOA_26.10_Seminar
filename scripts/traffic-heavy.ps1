param(
    [int]$Duration = 30,
    [double]$Rps = 15.0,
    [int]$Workers = 4
)

$appPort = "8000"
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^APP_PORT=(.+)$") { $appPort = $matches[1].Trim() }
    }
}

Write-Host "SINH TAI LON (HEAVY TRAFFIC) - QUAN SAT RPS VOT CAO" -ForegroundColor Yellow
Write-Host "[*] Muc tieu: http://localhost:$appPort trong $Duration giay voi $Workers workers..." -ForegroundColor Green

python scripts/traffic_generator.py --mode heavy --duration $Duration --rps $Rps --workers $Workers --url "http://localhost:$appPort"
