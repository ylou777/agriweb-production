@echo off
echo Demarrage de ngrok...
.\ngrok.exe http 5000 --hostname=agriweb-prod.ngrok-free.app
pause
