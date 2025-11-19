@echo off
echo 🚀 Demarrage du serveur AgriWeb avec recherche toiture corrigee
echo.
echo ✅ Corrections appliquees:
echo    - Protection contre erreurs OSError (WinError 233)
echo    - Optimisation recherche toiture (limite 500 batiments)
echo    - Enrichissement cadastral optimise (limite 50 toitures)
echo    - Correction logique de distance
echo.
echo 🔧 Parametres recommandes pour toitures:
echo    - Surface minimale: 500m² ou plus
echo    - Distance BT: 200m maximum  
echo    - Distance HTA: 300m maximum
echo.
echo 🌐 Le serveur sera accessible sur: http://localhost:5000
echo.
cd "c:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\AgW3b"
python run_app.py
pause
