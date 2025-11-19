@echo off
echo 🏠 LANCEMENT MODE DÉVELOPPEMENT LOCAL
echo =====================================
echo.
echo Configuration:
echo - GeoServer: localhost:8080
echo - Mode: Développement
echo - Tunnel: Désactivé
echo.

REM Forcer le mode local
set FORCE_LOCAL_GEOSERVER=true
set ENVIRONMENT=development
set FLASK_DEBUG=true

echo ✅ Variables d'environnement définies
echo.

REM Vérifier que GeoServer local est disponible
echo 🔍 Vérification GeoServer local...
curl -s -o nul -w "%%{http_code}" http://localhost:8080/geoserver > temp_status.txt
set /p STATUS=<temp_status.txt
del temp_status.txt

if "%STATUS%"=="200" (
    echo ✅ GeoServer local accessible
) else if "%STATUS%"=="302" (
    echo ✅ GeoServer local accessible (redirection)
) else (
    echo ❌ GeoServer local non accessible (Status: %STATUS%)
    echo.
    echo SOLUTIONS:
    echo 1. Vérifiez que GeoServer est démarré
    echo 2. Vérifiez l'URL: http://localhost:8080/geoserver
    echo 3. Ou utilisez run_production.bat pour le mode tunnel
    echo.
    pause
    exit /b 1
)

echo.
echo 🚀 Démarrage de l'application en mode LOCAL...
python agriweb_hebergement_gratuit.py
pause
