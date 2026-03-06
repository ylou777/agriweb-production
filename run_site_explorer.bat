@echo off
chcp 65001 >nul
title AgriWeb – Site Explorer Agent

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║       AGRIWEB / HELIAPV – SITE EXPLORER AGENT       ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

REM Activer le venv
call .venv\Scripts\activate.bat

REM Vérifier playwright
python -c "from playwright.async_api import async_playwright" 2>nul
if errorlevel 1 (
    echo  [!] Playwright non trouvé, installation...
    python site_explorer_agent.py --install
)

REM Lancer l'agent en mode interactif (il demandera URL, user, password)
python site_explorer_agent.py %*

echo.
echo  Appuyez sur une touche pour ouvrir la présentation...
pause >nul

REM Ouvrir la présentation HTML dans le navigateur par défaut
if exist "site_explorer_output\presentation.html" (
    start "" "site_explorer_output\presentation.html"
) else (
    echo  [!] Présentation non trouvée.
)
