@echo off
echo 🚀 Démarrage du serveur de test AgriWeb
echo.
echo 📍 URL de test de l'éditeur : http://127.0.0.1:5001/test_layer_editor
echo 📍 URL demo avancée        : http://127.0.0.1:5001/demo_advanced_layers  
echo 📍 URL application normale : http://127.0.0.1:5001/
echo.
echo 🎨 L'éditeur de couches devrait apparaître automatiquement avec :
echo    - Contrôles d'opacité (0-100%%)
echo    - Drag & Drop pour réorganiser
echo    - Groupes de couches
echo    - Recherche de couches
echo    - Sauvegarde des préférences
echo.
python test_layer_editor.py
