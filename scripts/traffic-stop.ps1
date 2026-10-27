$appPort = "8000"
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^APP_PORT=(.+)$") { $appPort = $matches[1].Trim() }
    }
}

Write-Host "DUNG SINH TAI VA KHOI PHUC HE THONG (RECOVERY)" -ForegroundColor Yellow

python scripts/traffic_generator.py --mode stop --url "http://localhost:$appPort"
