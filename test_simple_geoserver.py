#!/usr/bin/env python3
"""
Script de test simple pour GeoServer
"""
import os

# Définir les variables d'environnement AVANT l'import
os.environ['FORCE_LOCAL_GEOSERVER'] = 'true'
os.environ['GEOSERVER_URL'] = 'http://localhost:8080/geoserver'

print("🧪 [TEST] Variables d'environnement définies:")
print(f"   FORCE_LOCAL_GEOSERVER: {os.environ.get('FORCE_LOCAL_GEOSERVER')}")
print(f"   GEOSERVER_URL: {os.environ.get('GEOSERVER_URL')}")

# Test simple de la fonction
def test_function():
    # Copie de la logique corrigée
    if os.getenv('FORCE_LOCAL_GEOSERVER') == 'true':
        local_url = "http://localhost:8080/geoserver"
        print(f"🏠 [FORCED] GeoServer local forcé: {local_url}")
        return local_url
    
    geoserver_url = os.getenv('GEOSERVER_URL')
    if geoserver_url and 'localhost:8080' in geoserver_url:
        print(f"🏠 [LOCALHOST_VAR] Variable GEOSERVER_URL contient localhost: {geoserver_url}")
        return geoserver_url
    
    return "PROBLÈME - AUCUNE CONDITION REMPLIE"

print("\n🔍 [TEST] Test de la logique:")
result = test_function()
print(f"🎯 [RÉSULTAT] {result}")

if 'localhost:8080' in result:
    print("✅ [SUCCESS] Logique correcte!")
else:
    print("❌ [FAIL] Problème dans la logique")
