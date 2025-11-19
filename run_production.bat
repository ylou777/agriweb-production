@echo off
echo 🌐 LANCEMENT MODE PRODUCTION (TUNNEL)
echo ====================================
echo.
echo Configuration:
echo - GeoServer: Tunnel ngrok/distant
echo - Mode: Production
echo - Détection: Automatique
echo.

REM Mode production avec détection automatique
set ENVIRONMENT=production
set FLASK_DEBUG=false
REM Ne pas définir FORCE_LOCAL_GEOSERVER pour permettre la détection auto

echo ✅ Variables d'environnement définies
echo.
echo 🚀 Démarrage de l'application en mode PRODUCTION...
echo    (Détection automatique ngrok/tunnel)
echo.
python agriweb_hebergement_gratuit.py
pause
