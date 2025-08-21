#!/bin/bash
# restart-ngrok.sh - Script pour redémarrer ngrok automatiquement

# Arrêter ngrok existant
taskkill /F /IM ngrok.exe 2>nul

# Attendre 2 secondes
Start-Sleep -Seconds 2

# Redémarrer ngrok
ngrok start geoserver

# Ou alternative avec URL directe :
# ngrok http 8080 --host-header=localhost:8080
