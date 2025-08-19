# Script de déploiement Railway mis à jour - CLI v4
Write-Host "🚀 Déploiement GeoServer Railway - CLI v4" -ForegroundColor Green

Write-Host "`n📊 État actuel:" -ForegroundColor Yellow
railway status

Write-Host "`n🔍 Analyse du problème..." -ForegroundColor Yellow
Write-Host "Le build a échoué car GeoServer nécessite des variables d'environnement." -ForegroundColor Cyan

Write-Host "`n✅ SOLUTION - Interface Web:" -ForegroundColor Green
Write-Host "1. Ouvrez: https://railway.com/project/d9f8d8f2-122a-42a9-bc98-a3d87067b475" -ForegroundColor Cyan
Write-Host "2. Cliquez sur le service déployé" -ForegroundColor Cyan
Write-Host "3. Allez dans 'Variables'" -ForegroundColor Cyan
Write-Host "4. Ajoutez ces variables:" -ForegroundColor Cyan
Write-Host "   GEOSERVER_ADMIN_USER = admin" -ForegroundColor White
Write-Host "   GEOSERVER_ADMIN_PASSWORD = admin123" -ForegroundColor White
Write-Host "   JAVA_OPTS = -Xms512m -Xmx1024m" -ForegroundColor White
Write-Host "   INITIAL_MEMORY = 512M" -ForegroundColor White
Write-Host "   MAXIMUM_MEMORY = 1024M" -ForegroundColor White
Write-Host "5. Cliquez 'Deploy' pour redéployer" -ForegroundColor Cyan

Write-Host "`n🔄 ALTERNATIVE - CLI mis à jour:" -ForegroundColor Green

# Tentative avec la nouvelle syntaxe
Write-Host "Tentative de liaison du service..." -ForegroundColor Yellow

try {
    # Redéploiement
    Write-Host "Redéploiement en cours..." -ForegroundColor Cyan
    railway up --detach
    
    Write-Host "✅ Redéploiement lancé" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur CLI - Utilisez l'interface web" -ForegroundColor Red
}

Write-Host "`n📱 INSTRUCTIONS IMMÉDIATES:" -ForegroundColor Green
Write-Host "1. Ouvrez le dashboard Railway dans votre navigateur" -ForegroundColor Cyan
Write-Host "2. Configurez les variables d'environnement" -ForegroundColor Cyan
Write-Host "3. Redéployez le service" -ForegroundColor Cyan
Write-Host "4. Récupérez l'URL finale" -ForegroundColor Cyan

Write-Host "`n🌐 Liens directs:" -ForegroundColor Yellow
Write-Host "   Dashboard: https://railway.com/project/d9f8d8f2-122a-42a9-bc98-a3d87067b475" -ForegroundColor Cyan
Write-Host "   Settings: https://railway.com/project/d9f8d8f2-122a-42a9-bc98-a3d87067b475/settings" -ForegroundColor Cyan
