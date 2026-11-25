# start_pilot.ps1 - bring the pilot annotation server back online with one command (README_pilot section 2b).
#
# Run in a normal PowerShell window (NOT inside the Claude app, whose AppData is virtualised):
#   powershell -ExecutionPolicy Bypass -File data_collection\annotation\start_pilot.ps1
#
# What it does: (1) if nothing answers on port 8080, opens a new window running Label Studio with the
# CSRF / signup settings the public address needs; (2) if ngrok is not running, opens a second window
# with the fixed ngrok domain; (3) checks the public address and prints the result.
# Both windows stay open; close them only to stop the service. Safe to run again: it skips what is
# already running.

$Port = 8080
$Domain = "decent-reopen-curable.ngrok-free.dev"
$Public = "https://$Domain"

function Test-Local { try { (Invoke-WebRequest -Uri "http://localhost:$Port/health" -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200 } catch { $false } }

# 1) Label Studio
if (Test-Local) {
    Write-Host "[1/3] Label Studio already running on port $Port" -ForegroundColor Green
} else {
    Write-Host "[1/3] starting Label Studio in a new window ..." -ForegroundColor Yellow
    $cmd = "`$env:CSRF_TRUSTED_ORIGINS='https://*.trycloudflare.com,$Public'; `$env:DISABLE_SIGNUP_WITHOUT_LINK='1'; label-studio start --port $Port"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd
    $ok = $false
    for ($i = 0; $i -lt 60; $i++) { Start-Sleep -Seconds 2; if (Test-Local) { $ok = $true; break } }
    if ($ok) { Write-Host "      Label Studio is up" -ForegroundColor Green } else { Write-Host "      Label Studio did not answer within 2 min; look at its window" -ForegroundColor Red }
}

# 2) ngrok
if (Get-Process ngrok -ErrorAction SilentlyContinue) {
    Write-Host "[2/3] ngrok already running" -ForegroundColor Green
} else {
    Write-Host "[2/3] starting ngrok in a new window ..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http --url=$Domain $Port"
    Start-Sleep -Seconds 6
}

# 3) public check
Write-Host "[3/3] checking $Public ..." -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "$Public/user/login/" -Headers @{ "ngrok-skip-browser-warning" = "1" } -UseBasicParsing -TimeoutSec 15
    if ($r.StatusCode -eq 200) { Write-Host "      OK - annotators can reach $Public" -ForegroundColor Green }
    else { Write-Host "      unexpected status $($r.StatusCode)" -ForegroundColor Red }
} catch {
    Write-Host "      not reachable yet: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "      wait a few seconds and run this script again, or check the ngrok window (Session Status should be 'online')"
}
