# run_tunnel.ps1 — keep a Cloudflare quick tunnel to the local Label Studio alive (README_pilot §2b).
#
# Why: a quick tunnel (trycloudflare.com) is deleted on the Cloudflare side as soon as the laptop loses
# network for a while (sleep, Wi-Fi switch). cloudflared then loops on "Unauthorized: Tunnel not found"
# forever and the address is dead. This script watches for that, restarts cloudflared, and always keeps
# the CURRENT address in data\pilot\tunnel_url.txt (git-ignored) and on screen.
#
# Run in a normal PowerShell window (not inside the Claude app) and leave it open:
#   powershell -ExecutionPolicy Bypass -File data_collection\annotation\run_tunnel.ps1
# The address changes on every restart — tell the annotators the new one (tunnel_url.txt).
# Also keep the laptop awake: powercfg /change standby-timeout-ac 0

param([int]$Port = 8080)
$exe = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$urlFile = Join-Path $root "data\pilot\tunnel_url.txt"
$log = Join-Path $env:TEMP "cloudflared_ls.log"

function Start-Tunnel {
    Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 1
    if (Test-Path $log) { Remove-Item $log -Force }
    $p = Start-Process -FilePath $exe -ArgumentList "tunnel --url http://localhost:$Port --no-autoupdate" -RedirectStandardError $log -NoNewWindow -PassThru
    $url = $null
    for ($i = 0; $i -lt 30 -and -not $url; $i++) {
        Start-Sleep -Seconds 2
        if (Test-Path $log) { $m = Select-String -Path $log -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" | Select-Object -First 1; if ($m) { $url = $m.Matches[0].Value } }
    }
    if ($url) {
        Set-Content -Path $urlFile -Value $url -Encoding ascii
        Write-Host ""
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host ("  {0}  Label Studio 접속 주소:" -f (Get-Date -Format "yyyy-MM-dd HH:mm")) -ForegroundColor Green
        Write-Host "  $url" -ForegroundColor Yellow
        Write-Host "  (바뀌면 어노테이터에게 다시 알릴 것. 파일: $urlFile)" -ForegroundColor Green
        Write-Host "==========================================================" -ForegroundColor Green
    } else {
        Write-Host "tunnel did not come up within 60 s; retrying" -ForegroundColor Red
    }
    return $p
}

$proc = Start-Tunnel
while ($true) {
    Start-Sleep -Seconds 20
    $dead = $proc.HasExited
    $lost = $false
    if (Test-Path $log) {
        $tail = Get-Content $log -Tail 6 -ErrorAction SilentlyContinue
        if ($tail -match "Tunnel not found") { $lost = $true }
    }
    if ($dead -or $lost) {
        Write-Host ("{0}  tunnel {1}; restarting" -f (Get-Date -Format "HH:mm:ss"), $(if ($dead) { "process exited" } else { "lost on the Cloudflare side" })) -ForegroundColor Red
        $proc = Start-Tunnel
    }
}
