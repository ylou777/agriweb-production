#!/usr/bin/env pwsh
# Script de correction pour Railway CLI v4 - Syntaxe mise à jour
Write-Host "🔧 Configuration Railway CLI v4..." -ForegroundColor Green

# Vérifier la version de Railway CLI
Write-Host "`n📋 Version Railway CLI:" -ForegroundColor Cyan
railway --version

# Statut actuel
Write-Host "`n📊 Statut du projet:" -ForegroundColor Cyan
railway status

# Instructions pour la configuration manuelle via l'interface web
Write-Host "`n🌐 CONFIGURATION VIA L'INTERFACE WEB (RECOMMANDÉE)" -ForegroundColor Yellow
Write-Host "1. Ouvrez votre dashboard Railway:" -ForegroundColor White
Write-Host "   https://railway.com/project/d9f8d8f2-122a-42a9-bc98-a3d87067b475" -ForegroundColor Blue

Write-Host "`n2. Sélectionnez votre service GeoServer" -ForegroundColor White

Write-Host "`n3. Allez dans l'onglet 'Variables'" -ForegroundColor White

Write-Host "`n4. Ajoutez ces variables d'environnement:" -ForegroundColor White
Write-Host "   GEOSERVER_ADMIN_USER = admin" -ForegroundColor Green
Write-Host "   GEOSERVER_ADMIN_PASSWORD = admin123" -ForegroundColor Green
Write-Host "   JAVA_OPTS = -Xms512m -Xmx1024m" -ForegroundColor Green
Write-Host "   INITIAL_MEMORY = 512M" -ForegroundColor Green
Write-Host "   MAXIMUM_MEMORY = 1024M" -ForegroundColor Green

Write-Host "`n5. Cliquez sur 'Deploy' pour redéployer" -ForegroundColor White

# Alternative avec la nouvelle syntaxe CLI v4 (si le service est lié)
Write-Host "`n🔧 ALTERNATIVE CLI (après avoir lié le service):" -ForegroundColor Yellow
Write-Host "railway variables -h  # Voir la nouvelle syntaxe"
Write-Host "railway domain        # Obtenir l'URL après déploiement"

# Ouvrir automatiquement le dashboard
Write-Host "`n🚀 Ouverture du dashboard..." -ForegroundColor Green
try {
    railway open
    Write-Host "✅ Dashboard ouvert dans votre navigateur" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Ouvrez manuellement: https://railway.com/project/d9f8d8f2-122a-42a9-bc98-a3d87067b475" -ForegroundColor Yellow
}

Write-Host "`n📝 NEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Configurez les variables via l'interface web" -ForegroundColor White
Write-Host "2. Redéployez le service" -ForegroundColor White
Write-Host "3. Récupérez l'URL: railway domain" -ForegroundColor White
Write-Host "4. Testez: https://VOTRE-URL.up.railway.app/geoserver" -ForegroundColor White
