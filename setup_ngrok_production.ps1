# Script de configuration ngrok Pay-as-you-go
# À exécuter après souscription à l'abonnement

Write-Host "🚀 Configuration ngrok Pay-as-you-go pour AgriWeb" -ForegroundColor Green

# 1. Vérifier l'abonnement
Write-Host "1. Vérification de l'abonnement..." -ForegroundColor Yellow
ngrok account status

# 2. Créer un domaine permanent (remplacez par votre domaine choisi)
$DOMAIN_NAME = "agriweb-geoserver"
Write-Host "2. Création du domaine permanent: $DOMAIN_NAME.ngrok.io" -ForegroundColor Yellow

# Note: Cette commande sera disponible après l'abonnement
# ngrok config add-endpoint $DOMAIN_NAME.ngrok.io

# 3. Lancer ngrok avec le domaine fixe
Write-Host "3. Lancement de ngrok avec domaine fixe..." -ForegroundColor Yellow
Write-Host "Commande à utiliser: ngrok http 8088 --url=$DOMAIN_NAME.ngrok.io" -ForegroundColor Cyan

# 4. URL finale pour Railway
$FINAL_URL = "https://$DOMAIN_NAME.ngrok.io/geoserver"
Write-Host "4. URL finale à configurer dans Railway:" -ForegroundColor Yellow
Write-Host "   GEOSERVER_URL=$FINAL_URL" -ForegroundColor Green

Write-Host "`n✅ Configuration terminée !" -ForegroundColor Green
Write-Host "📋 Prochaines étapes:" -ForegroundColor Yellow
Write-Host "   1. Souscrivez à Pay-as-you-go sur ngrok.com" -ForegroundColor White
Write-Host "   2. Créez votre domaine permanent" -ForegroundColor White
Write-Host "   3. Lancez ngrok avec votre domaine" -ForegroundColor White
Write-Host "   4. Mettez à jour GEOSERVER_URL sur Railway" -ForegroundColor White
