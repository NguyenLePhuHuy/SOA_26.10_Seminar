Write-Host "THUC THI KIEM THU TU DONG (APP METRICS & WEBHOOK)" -ForegroundColor Yellow

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "`n[*] 1. Kiem tra Unit & Integration Tests cho Demo App Metrics..." -ForegroundColor Cyan
python -m pytest "$scriptDir\test_metrics.py" -v
$appTestResult = $LASTEXITCODE

Write-Host "`n[*] 2. Kiem tra Unit & Integration Tests cho Webhook Receiver..." -ForegroundColor Cyan
python -m pytest "$scriptDir\test_webhook.py" -v
$webhookTestResult = $LASTEXITCODE

if ($appTestResult -eq 0 -and $webhookTestResult -eq 0) {
    Write-Host "`n[v] TAT CA TEST CASES DA PASS 100%! BAO DAM DO TIN CAY!" -ForegroundColor Green
} else {
    Write-Host "`n[X] Co test case that bai. Hay kiem tra thu vien hoac ma nguon!" -ForegroundColor Red
}

exit ($appTestResult + $webhookTestResult)
