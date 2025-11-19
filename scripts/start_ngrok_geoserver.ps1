# Starts ngrok to expose local GeoServer (default 8080) on a reserved domain and exports GEOSERVER_TUNNEL_URL
# Prereqs:
# - Install ngrok and ensure ngrok.exe is in PATH or set $NgrokPath
# - Run: ngrok config add-authtoken <your-authtoken>

[CmdletBinding()]
param(
    [string]$Domain = "agriweb-prod.ngrok-free.app",
    [int]$LocalPort = 8080,
    [string]$NgrokPath = "ngrok", # can be 'ngrok', '.\\ngrok.exe', or full path
    [switch]$Background
)

$ErrorActionPreference = 'Stop'

# Resolve ngrok path robustly (supports .\ngrok.exe, PATH, and common install dirs)
$script:ResolvedNgrokPath = $null
function Resolve-NgrokPath {
    param([string]$Hint)
    if ($Hint -and (Test-Path $Hint)) { return $Hint }
    $pathFromCmd = $null
    try { $pathFromCmd = (Get-Command ngrok -ErrorAction Stop).Path } catch {}
    $candidates = @(
        ".\\ngrok.exe",
        $pathFromCmd,
        (Join-Path $env:LOCALAPPDATA 'ngrok\\ngrok.exe'),
        'C:\\ngrok\\ngrok.exe'
    ) | Where-Object { $_ }
    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) { return $c }
    }
    return $null
}

$script:ResolvedNgrokPath = Resolve-NgrokPath -Hint $NgrokPath
if (-not $script:ResolvedNgrokPath) {
    Write-Error "ngrok not found. Download from https://ngrok.com/download, place ngrok.exe in the project folder, or specify -NgrokPath 'C:\\ngrok\\ngrok.exe'."
    exit 1
}
Write-Host "Using ngrok at: $script:ResolvedNgrokPath" -ForegroundColor Cyan

$ngrokArgs = @('http', $LocalPort, '--domain', $Domain, '--host-header=rewrite')
if ($Background) {
    Start-Process -FilePath $script:ResolvedNgrokPath -ArgumentList $ngrokArgs -WindowStyle Minimized
    Start-Sleep -Seconds 2
} else {
    & $script:ResolvedNgrokPath @ngrokArgs
}

# Export for current PowerShell session
$env:GEOSERVER_TUNNEL_URL = "https://$Domain/geoserver"
Write-Host "GEOSERVER_TUNNEL_URL set to $($env:GEOSERVER_TUNNEL_URL)" -ForegroundColor Green
