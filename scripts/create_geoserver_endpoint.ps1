# Creates/Lists/Deletes an ngrok Cloud Endpoint for GeoServer using the ngrok REST API v2
# Requirements:
# - Set an environment variable NGROK_API_KEY with your ngrok API Key (not the authtoken)
# - The reserved domain should exist in your ngrok account (e.g. agriweb-prod.ngrok-free.app)

[CmdletBinding()]
param(
    [string]$Domain = "agriweb-prod.ngrok-free.app",
    [string]$Description = "AgriWeb GeoServer endpoint",
    [ValidateSet('public')]
    [string]$Bindings = "public",
    [string]$TrafficPolicy,
    [switch]$PoolingEnabled,
    [string]$ApiKey,
    [switch]$List,
    [switch]$Delete
)

function Assert-NgrokApiKey {
    if (-not $script:ResolvedApiKey) {
        Write-Error "NGROK_API_KEY is not set and -ApiKey not provided. Get your API Key from dashboard.ngrok.com -> API -> Keys. Then run with -ApiKey '<key>' or set `$env:NGROK_API_KEY."
        exit 1
    }
}

function Get-CommonHeaders {
    return @{
        'Authorization' = "Bearer $($script:ResolvedApiKey)"
        'Content-Type'  = 'application/json'
        'Ngrok-Version' = '2'
    }
}

function Get-AllEndpoints {
    Assert-NgrokApiKey
    $resp = Invoke-RestMethod -Method Get -Headers (Get-CommonHeaders) -Uri 'https://api.ngrok.com/endpoints'
    return $resp.endpoints
}

function Find-EndpointByDomainHost([string]$HostName) {
    $eps = Get-AllEndpoints
    foreach ($ep in $eps) {
        # Try to match by public_url host or domain.ref if present
        $publicUrl = $ep.public_url
        if ($publicUrl) {
            try { $u = [System.Uri]$publicUrl } catch { $u = $null }
            if ($u -and $u.Host -ieq $HostName) { return $ep }
        }
        if ($ep.domain -and $ep.domain.uri) {
            # domain ref exists but not always includes host; skip
        }
        if ($ep.host) {
            if ($ep.host -ieq $HostName) { return $ep }
        }
    }
    return $null
}

function Create-CloudEndpoint([string]$EndpointHost, [string]$desc, [string[]]$bindings, [string]$policy, [bool]$pooling) {
    Assert-NgrokApiKey
    $existing = Find-EndpointByDomainHost -HostName $EndpointHost
    if ($existing) {
        Write-Host "Endpoint already exists for $EndpointHost -> $($existing.public_url) (id: $($existing.id))" -ForegroundColor Yellow
        return $existing
    }
    $body = @{ 
        url = "https://$EndpointHost" 
        type = 'cloud'
        description = $desc
        metadata = '{"service":"geoserver"}'
        bindings = $bindings
    }
    if ($policy) { $body.traffic_policy = $policy }
    if ($pooling) { $body.pooling_enabled = $true }
    $json = $body | ConvertTo-Json -Depth 5
    $resp = Invoke-RestMethod -Method Post -Headers (Get-CommonHeaders) -Uri 'https://api.ngrok.com/endpoints' -Body $json
    Write-Host "Created endpoint: $($resp.public_url) (id: $($resp.id))" -ForegroundColor Green
    return $resp
}

function Delete-EndpointById([string]$id) {
    Assert-NgrokApiKey
    Invoke-RestMethod -Method Delete -Headers (Get-CommonHeaders) -Uri "https://api.ngrok.com/endpoints/$id" | Out-Null
    Write-Host "Deleted endpoint id: $id" -ForegroundColor Green
}

if ($PSBoundParameters.ContainsKey('ApiKey') -and $ApiKey) {
    $script:ResolvedApiKey = $ApiKey
} else {
    $script:ResolvedApiKey = $env:NGROK_API_KEY
}

if ($List) {
    $eps = Get-AllEndpoints
    if (-not $eps) { Write-Host 'No endpoints found.'; exit 0 }
    $eps | ForEach-Object {
        [PSCustomObject]@{
            id         = $_.id
            type       = $_.type
            proto      = $_.proto
            public_url = $_.public_url
            created_at = $_.created_at
            updated_at = $_.updated_at
            upstream   = $_.upstream_url
            name       = $_.name
        }
    } | Format-Table -AutoSize
    exit 0
}

if ($Delete) {
    $ep = Find-EndpointByDomainHost -HostName $Domain
    if ($ep) {
        Delete-EndpointById -id $ep.id
    } else {
        Write-Host "No endpoint found for host $Domain" -ForegroundColor Yellow
    }
    exit 0
}

$created = Create-CloudEndpoint -EndpointHost $Domain -desc $Description -bindings @($Bindings) -policy $TrafficPolicy -pooling $PoolingEnabled.IsPresent
if ($created) {
    $public = $created.public_url
    Write-Host "Next: start a tunnel from your machine to GeoServer on port 8080:" -ForegroundColor Cyan
    Write-Host "  ngrok http 8080 --domain $Domain --host-header=rewrite" -ForegroundColor Cyan
    Write-Host "Then set GEOSERVER_TUNNEL_URL for the app (current session):" -ForegroundColor Cyan
    Write-Host "  `$env:GEOSERVER_TUNNEL_URL = '$public/geoserver'" -ForegroundColor Cyan
}
