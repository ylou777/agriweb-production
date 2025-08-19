# 🔧 INSTALLATION AUTOMATIQUE NGROK
# Script pour télécharger et configurer ngrok automatiquement

param(
    [switch]$Download,
    [switch]$Configure,
    [string]$AuthToken = "31UrhBFN9GpDYlr8yORTQkwedNI_29vvhqzAb5naKvH8hRV9d"
)

function Show-Banner {
    Write-Host "🔧 INSTALLATION NGROK AUTOMATIQUE" -ForegroundColor Cyan
    Write-Host "==================================" -ForegroundColor Cyan
    Write-Host ""
}

function Install-Ngrok {
    Write-Host "📦 Téléchargement de ngrok..." -ForegroundColor Yellow
    
    $ngrokDir = "C:\ngrok"
    $ngrokZip = "$env:TEMP\ngrok.zip"
    $ngrokUrl = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
    
    try {
        # Créer le dossier ngrok
        if (-not (Test-Path $ngrokDir)) {
            New-Item -ItemType Directory -Path $ngrokDir -Force | Out-Null
            Write-Host "✅ Dossier créé: $ngrokDir" -ForegroundColor Green
        }
        
        # Télécharger ngrok
        Write-Host "⬇️ Téléchargement depuis: $ngrokUrl" -ForegroundColor Cyan
        Invoke-WebRequest -Uri $ngrokUrl -OutFile $ngrokZip -ErrorAction Stop
        Write-Host "✅ Téléchargement terminé" -ForegroundColor Green
        
        # Extraire l'archive
        Write-Host "📂 Extraction vers: $ngrokDir" -ForegroundColor Cyan
        Expand-Archive -Path $ngrokZip -DestinationPath $ngrokDir -Force
        Write-Host "✅ Extraction terminée" -ForegroundColor Green
        
        # Nettoyer
        Remove-Item $ngrokZip -ErrorAction SilentlyContinue
        
        # Vérifier l'installation
        $ngrokExe = "$ngrokDir\ngrok.exe"
        if (Test-Path $ngrokExe) {
            Write-Host "✅ ngrok installé avec succès: $ngrokExe" -ForegroundColor Green
            
            # Tester la version
            $version = & $ngrokExe version 2>$null
            Write-Host "📋 Version: $version" -ForegroundColor Cyan
            
            return $ngrokExe
        }
        else {
            Write-Host "❌ Erreur: ngrok.exe non trouvé après extraction" -ForegroundColor Red
            return $null
        }
    }
    catch {
        Write-Host "❌ Erreur lors du téléchargement: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Configure-NgrokAuth {
    param([string]$NgrokPath, [string]$Token)
    
    Write-Host "🔐 Configuration de l'authtoken..." -ForegroundColor Yellow
    
    try {
        $result = & $NgrokPath config add-authtoken $Token 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Authtoken configuré avec succès" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ Erreur lors de la configuration: $result" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Erreur: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-NgrokInstallation {
    $ngrokPath = "C:\ngrok\ngrok.exe"
    
    if (Test-Path $ngrokPath) {
        Write-Host "✅ ngrok trouvé: $ngrokPath" -ForegroundColor Green
        
        try {
            $version = & $ngrokPath version 2>$null
            Write-Host "📋 Version: $version" -ForegroundColor Cyan
            
            # Tester la configuration
            $config = & $ngrokPath config check 2>&1
            if ($config -match "authtoken") {
                Write-Host "✅ Authtoken configuré" -ForegroundColor Green
            }
            else {
                Write-Host "⚠️ Authtoken non configuré" -ForegroundColor Yellow
            }
            
            return $ngrokPath
        }
        catch {
            Write-Host "⚠️ Erreur lors du test de ngrok" -ForegroundColor Yellow
            return $ngrokPath
        }
    }
    else {
        Write-Host "❌ ngrok non trouvé" -ForegroundColor Red
        return $null
    }
}

function Add-NgrokToPath {
    $ngrokDir = "C:\ngrok"
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    
    if ($currentPath -notlike "*$ngrokDir*") {
        Write-Host "➕ Ajout de ngrok au PATH utilisateur..." -ForegroundColor Yellow
        $newPath = "$currentPath;$ngrokDir"
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
        Write-Host "✅ PATH mis à jour (redémarrez PowerShell pour effet)" -ForegroundColor Green
    }
    else {
        Write-Host "✅ ngrok déjà dans le PATH" -ForegroundColor Green
    }
}

# SCRIPT PRINCIPAL
Show-Banner

if ($Download) {
    # Installation complète
    Write-Host "🚀 Installation complète de ngrok..." -ForegroundColor Cyan
    
    $ngrokPath = Install-Ngrok
    if ($ngrokPath) {
        Write-Host ""
        Write-Host "🔐 Configuration de l'authtoken..." -ForegroundColor Cyan
        if (Configure-NgrokAuth -NgrokPath $ngrokPath -Token $AuthToken) {
            Write-Host ""
            Write-Host "📁 Ajout au PATH..." -ForegroundColor Cyan
            Add-NgrokToPath
            
            Write-Host ""
            Write-Host "🎉 INSTALLATION TERMINÉE AVEC SUCCÈS!" -ForegroundColor Green
            Write-Host "📋 Prochaines étapes:" -ForegroundColor Cyan
            Write-Host "1. Redémarrez PowerShell (ou utilisez: C:\ngrok\ngrok.exe)" -ForegroundColor White
            Write-Host "2. Testez avec: .\start_tunnel_simple.ps1" -ForegroundColor White
        }
    }
}
elseif ($Configure) {
    # Configuration seulement
    $ngrokPath = Test-NgrokInstallation
    if ($ngrokPath) {
        Configure-NgrokAuth -NgrokPath $ngrokPath -Token $AuthToken
    }
    else {
        Write-Host "❌ ngrok non trouvé. Utilisez -Download pour l'installer" -ForegroundColor Red
    }
}
else {
    # Test et informations
    Write-Host "📋 ÉTAT ACTUEL DE NGROK:" -ForegroundColor Cyan
    Write-Host ""
    
    $ngrokPath = Test-NgrokInstallation
    
    if ($ngrokPath) {
        Write-Host ""
        Write-Host "✅ ngrok est installé et prêt!" -ForegroundColor Green
        Write-Host "🚀 Utilisez: .\start_tunnel_simple.ps1" -ForegroundColor Cyan
    }
    else {
        Write-Host ""
        Write-Host "📦 INSTALLATION REQUISE:" -ForegroundColor Yellow
        Write-Host "🔧 Utilisez: .\install_ngrok.ps1 -Download" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "🎯 ALTERNATIVE MANUELLE:" -ForegroundColor Yellow
        Write-Host "1. Téléchargez: https://ngrok.com/download" -ForegroundColor White
        Write-Host "2. Décompressez dans: C:\ngrok\" -ForegroundColor White
        Write-Host "3. Configurez: C:\ngrok\ngrok.exe config add-authtoken $AuthToken" -ForegroundColor White
    }
}

Write-Host ""
