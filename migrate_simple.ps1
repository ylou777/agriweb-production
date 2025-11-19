# Migration GeoServer Simple - Sans Docker
# Alternative pour commencer la migration sans Docker

Write-Host "🚀 Migration GeoServer Simplifiée" -ForegroundColor Green

# Configuration
$GEOSERVER_LOCAL = "http://localhost:8080/geoserver"
$RAILWAY_APP_NAME = "geoserver-agriweb"

Write-Host "`n📋 Étapes de migration:" -ForegroundColor Yellow
Write-Host "1. ✅ Préparer la configuration locale" -ForegroundColor Green
Write-Host "2. 🔄 Export des données GeoServer" -ForegroundColor Yellow  
Write-Host "3. 🌐 Création du projet Railway" -ForegroundColor Yellow
Write-Host "4. 📤 Déploiement" -ForegroundColor Yellow
Write-Host "5. 🔧 Configuration de l'application" -ForegroundColor Yellow

# Étape 1: Test de connexion locale
Write-Host "`n🔍 Test de connexion GeoServer local..." -ForegroundColor Cyan

try {
    $response = Invoke-WebRequest -Uri "$GEOSERVER_LOCAL/rest/about/version" -Method GET -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ GeoServer local accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ GeoServer local non accessible sur $GEOSERVER_LOCAL" -ForegroundColor Red
    Write-Host "💡 Assurez-vous que GeoServer est démarré localement" -ForegroundColor Yellow
    $continue = Read-Host "Continuer quand même? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}

# Étape 2: Export des workspaces (préparation)
Write-Host "`n📦 Préparation de l'export des données..." -ForegroundColor Cyan

$exportScript = @"
import requests
import json
import os

def export_geoserver_config():
    base_url = '$GEOSERVER_LOCAL'
    
    try:
        # Test de connexion
        response = requests.get(f'{base_url}/rest/workspaces', 
                              auth=('admin', 'admin'), timeout=10)
        
        if response.status_code == 200:
            workspaces = response.json()
            print(f'✅ Trouvé {len(workspaces.get("workspaces", {}).get("workspace", []))} workspaces')
            
            # Sauvegarde de la configuration
            with open('geoserver_config_backup.json', 'w') as f:
                json.dump(workspaces, f, indent=2)
            
            print('✅ Configuration sauvegardée dans geoserver_config_backup.json')
            return True
        else:
            print(f'❌ Erreur: {response.status_code}')
            return False
            
    except Exception as e:
        print(f'❌ Erreur de connexion: {e}')
        return False

if __name__ == '__main__':
    export_geoserver_config()
"@

$exportScript | Out-File -FilePath "export_config.py" -Encoding UTF8

# Exécution de l'export
Write-Host "Exécution de l'export des configurations..." -ForegroundColor Cyan
python export_config.py

# Étape 3: Informations pour Railway
Write-Host "`n🚂 Configuration Railway:" -ForegroundColor Cyan
Write-Host "Nom du projet suggéré: $RAILWAY_APP_NAME" -ForegroundColor Yellow

$projectName = Read-Host "Nom du projet Railway (appuyez sur Entrée pour '$RAILWAY_APP_NAME')"
if ([string]::IsNullOrEmpty($projectName)) {
    $projectName = $RAILWAY_APP_NAME
}

# Étape 4: Création du fichier de configuration pour Railway
Write-Host "`n📁 Création des fichiers de configuration..." -ForegroundColor Cyan

# Railway configuration
$railwayToml = @"
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile.geoserver"

[deploy]
startCommand = "/opt/geoserver_startup.sh"
restartPolicyType = "never"

[[services]]
name = "geoserver"

[services.variables]
GEOSERVER_ADMIN_USER = "admin"
GEOSERVER_ADMIN_PASSWORD = "admin123"
JAVA_OPTS = "-Xms512m -Xmx1024m"
INITIAL_MEMORY = "512M"
MAXIMUM_MEMORY = "1024M"
"@

$railwayToml | Out-File -FilePath "railway.toml" -Encoding UTF8

# Étape 5: Mise à jour de l'application
Write-Host "`n🔧 Mise à jour de la configuration application..." -ForegroundColor Cyan

# Création du fichier d'environnement
$envContent = @"
# Configuration GeoServer - Généré automatiquement
GEOSERVER_LOCAL_URL=http://localhost:8080/geoserver
GEOSERVER_PRODUCTION_URL=https://$projectName.up.railway.app/geoserver
ENVIRONMENT=development

# Pour passer en production, changez ENVIRONMENT=production
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8

# Étape 6: Instructions pour la suite
Write-Host "`n📋 Prochaines étapes:" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 PRÉREQUIS (si pas déjà fait):" -ForegroundColor Yellow
Write-Host "   .\install_prerequisites.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "🚂 DÉPLOIEMENT RAILWAY:" -ForegroundColor Yellow
Write-Host "   1. Créez un compte sur https://railway.app" -ForegroundColor Cyan
Write-Host "   2. Connectez-vous: railway login" -ForegroundColor Cyan
Write-Host "   3. Déployez: railway project create $projectName" -ForegroundColor Cyan
Write-Host "   4. Upload: railway up --dockerfile Dockerfile.geoserver" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔄 ALTERNATIVE SANS CLI:" -ForegroundColor Yellow
Write-Host "   1. Allez sur https://railway.app/new" -ForegroundColor Cyan
Write-Host "   2. Choisissez 'Deploy from GitHub repo'" -ForegroundColor Cyan
Write-Host "   3. Connectez ce repository" -ForegroundColor Cyan
Write-Host "   4. Railway détectera automatiquement le Dockerfile" -ForegroundColor Cyan
Write-Host ""
Write-Host "📱 MIGRATION DES DONNÉES:" -ForegroundColor Yellow
Write-Host "   python migrate_geoserver.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚙️ FICHIERS CRÉÉS:" -ForegroundColor Green
Write-Host "   ✅ .env (configuration environnement)" -ForegroundColor Cyan
Write-Host "   ✅ railway.toml (configuration Railway)" -ForegroundColor Cyan
Write-Host "   ✅ export_config.py (script d'export)" -ForegroundColor Cyan
Write-Host "   ✅ geoserver_config_backup.json (backup configuration)" -ForegroundColor Cyan

Write-Host "`n🎯 URL finale estimée:" -ForegroundColor Green
Write-Host "   https://$projectName.up.railway.app/geoserver" -ForegroundColor Cyan

Write-Host "`n💡 Conseil:" -ForegroundColor Yellow
Write-Host "   Gardez ce terminal ouvert et suivez les instructions étape par étape" -ForegroundColor Cyan
