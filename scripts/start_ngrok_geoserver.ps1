# Starts ngrok to expose local GeoServer (default 8080) on a reserved domain and exports GEOSERVER_TUNNEL_URL
# Prereqs:
# - Install ngrok and ensure ngrok.exe is in PATH or set $NgrokPath
# - Run: ngrok config add-authtoken <your-authtoken>

[CmdletBinding()]
param(
    [string]$Domain = "agriweb-prod.ngrok-free.app",
    [int]$LocalPort = 8080,
    [string]$NgrokPath = "ngrok",
    [switch]$Background
)

$ErrorActionPreference = 'Stop'

function Test-NgrokInstalled {
    try {
        & $NgrokPath version | Out-Null
        return $true
    } catch {
        Write-Error "ngrok not found. Install from https://ngrok.com/download and ensure ngrok.exe is in PATH or set -NgrokPath."
        return $false
    }
}

if (-not (Test-NgrokInstalled)) { exit 1 }

$ngrokArgs = @('http', $LocalPort, '--domain', $Domain, '--host-header=rewrite')
if ($Background) {
    Start-Process -FilePath $NgrokPath -ArgumentList $ngrokArgs -WindowStyle Minimized
    Start-Sleep -Seconds 2
} else {
    & $NgrokPath @ngrokArgs
}

# Export for current PowerShell session
$env:GEOSERVER_TUNNEL_URL = "https://$Domain/geoserver"
Write-Host "GEOSERVER_TUNNEL_URL set to $($env:GEOSERVER_TUNNEL_URL)" -ForegroundColor Green
