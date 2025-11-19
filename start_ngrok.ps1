# Script de démarrage ngrok pour AgriWeb
# Double-cliquez sur ce fichier pour lancer ngrok automatiquement

Write-Host "🚀 Démarrage ngrok pour AgriWeb..." -ForegroundColor Green
Write-Host ""

$targetPath = "C:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\AgW3b"
Set-Location $targetPath
Write-Host "📁 Dossier : $PWD" -ForegroundColor Cyan
Write-Host ""

Write-Host "🌐 Lancement du tunnel vers agriweb-prod.ngrok-free.app..." -ForegroundColor Yellow
Write-Host "⚠️  IMPORTANT: Gardez cette fenêtre ouverte !" -ForegroundColor Red
Write-Host ""

# Lancer ngrok
.\ngrok.exe http --hostname=agriweb-prod.ngrok-free.app 8080

Write-Host ""
Write-Host "Appuyez sur une touche pour continuer..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")