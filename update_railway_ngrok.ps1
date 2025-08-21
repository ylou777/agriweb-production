# Script de mise à jour Railway après configuration ngrok
# À exécuter une fois votre domaine ngrok permanent configuré

param(
    [Parameter(Mandatory=$true)]
    [string]$NgrokDomain
)

Write-Host "🚀 Mise à jour Railway avec domaine ngrok permanent" -ForegroundColor Green
Write-Host "Domaine fourni: $NgrokDomain" -ForegroundColor Yellow

# Validation du domaine
if (-not ($NgrokDomain.EndsWith(".ngrok.io") -or $NgrokDomain.EndsWith(".ngrok-free.app"))) {
    Write-Host "❌ Erreur: Le domaine doit se terminer par .ngrok.io ou .ngrok-free.app" -ForegroundColor Red
    exit 1
}

# Construction de l'URL complète
$GEOSERVER_URL = "https://$NgrokDomain/geoserver"
Write-Host "URL GeoServer finale: $GEOSERVER_URL" -ForegroundColor Cyan

Write-Host "`n📋 Étapes à suivre:" -ForegroundColor Yellow
Write-Host "1. Connectez-vous à Railway:" -ForegroundColor White
Write-Host "   railway login" -ForegroundColor Gray
Write-Host "2. Sélectionnez votre projet:" -ForegroundColor White  
Write-Host "   railway link" -ForegroundColor Gray
Write-Host "3. Mettez à jour la variable d'environnement:" -ForegroundColor White
Write-Host "   railway variables set GEOSERVER_URL=$GEOSERVER_URL" -ForegroundColor Gray
Write-Host "4. Redéployez votre application:" -ForegroundColor White
Write-Host "   railway up" -ForegroundColor Gray

Write-Host "`n✅ Votre application Railway utilisera maintenant une URL fixe !" -ForegroundColor Green
Write-Host "🔗 URL GeoServer stable: $GEOSERVER_URL" -ForegroundColor Green

# Optionnel: Mettre à jour automatiquement si Railway CLI est configuré
$confirmation = Read-Host "`nVoulez-vous mettre à jour Railway automatiquement maintenant? (y/n)"
if ($confirmation -eq "y" -or $confirmation -eq "Y") {
    Write-Host "🔄 Mise à jour Railway..." -ForegroundColor Yellow
    railway variables set "GEOSERVER_URL=$GEOSERVER_URL"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Variable GEOSERVER_URL mise à jour sur Railway" -ForegroundColor Green
        Write-Host "🚀 Redéploiement en cours..." -ForegroundColor Yellow
        railway up
    } else {
        Write-Host "❌ Erreur lors de la mise à jour. Vérifiez votre connexion Railway." -ForegroundColor Red
    }
}
