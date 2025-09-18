@echo off
echo 🚀 Démarrage ngrok pour AgriWeb...
echo.
cd /d "C:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\AgW3b"
echo 📁 Dossier : %CD%
echo.
echo 🌐 Lancement du tunnel vers agriweb-prod.ngrok-free.app...
echo ⚠️  IMPORTANT: Gardez cette fenêtre ouverte !
echo.
.\ngrok.exe http --hostname=agriweb-prod.ngrok-free.app 8080
pause
