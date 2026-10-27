param (
    [switch]$Volumes
)

Write-Host "DUNG HE THONG PROMETHEUS & GRAFANA WORKSHOP" -ForegroundColor Yellow

if ($Volumes) {
    Write-Host "[*] Dang dung containers va XOA toan bo volumes du lieu..." -ForegroundColor Red
    docker compose down -v
} else {
    Write-Host "[*] Dang dung containers (giu lai du lieu volumes)..." -ForegroundColor Yellow
    docker compose down
}

Write-Host "[v] Da dung toan bo dich vu an toan." -ForegroundColor Green
