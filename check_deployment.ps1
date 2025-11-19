# Script de suivi du déploiement GeoServer sur Railway
Write-Host "🔍 Suivi du déploiement GeoServer..." -ForegroundColor Green

# Informations du projet
Write-Host "`n📊 Informations du projet:" -ForegroundColor Yellow
railway status

Write-Host "`n🔧 Variables d'environnement:" -ForegroundColor Yellow
railway variables

Write-Host "`n📋 Logs récents:" -ForegroundColor Yellow
railway logs --lines 20

Write-Host "`n🌐 URLs du projet:" -ForegroundColor Green
Write-Host "   Dashboard: https://railway.com/project/d9f8d8f2-122a-42a9-bc98-a3d87067b475" -ForegroundColor Cyan
Write-Host "   Service logs: https://railway.com/project/d9f8d8f2-122a-42a9-bc98-a3d87067b475/service/9f67c947-d0a1-4e9e-8e9b-3a7cf1cc0da5" -ForegroundColor Cyan

# Instructions
Write-Host "`n💡 Instructions:" -ForegroundColor Yellow
Write-Host "1. Le déploiement peut prendre 5-10 minutes" -ForegroundColor Cyan
Write-Host "2. Surveillez les logs avec: railway logs" -ForegroundColor Cyan
Write-Host "3. Une fois déployé, récupérez l'URL avec: railway domain" -ForegroundColor Cyan
Write-Host "4. Testez GeoServer: https://VOTRE-URL.up.railway.app/geoserver" -ForegroundColor Cyan

Write-Host "`n🔄 Commandes utiles:" -ForegroundColor Green
Write-Host "   railway logs         - Voir les logs" -ForegroundColor White
Write-Host "   railway status       - État du projet" -ForegroundColor White
Write-Host "   railway domain       - Obtenir l'URL publique" -ForegroundColor White
Write-Host "   railway open         - Ouvrir le dashboard" -ForegroundColor White
