$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

$testScript = if (Test-Path (Join-Path $projectRoot "tests\run-tests.ps1")) {
    Join-Path $projectRoot "tests\run-tests.ps1"
} elseif (Test-Path (Join-Path $projectRoot "prepare\tests\run-tests.ps1")) {
    Join-Path $projectRoot "prepare\tests\run-tests.ps1"
} else {
    $null
}

if ($testScript) {
    & $testScript
} else {
    Write-Host "[X] Khong tim thay test suite" -ForegroundColor Red
    exit 1
}
