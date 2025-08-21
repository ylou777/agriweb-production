#!/usr/bin/env python3
"""Test des identifiants GeoServer"""

import os

# Configuration test
os.environ['GEOSERVER_URL'] = 'https://complete-simple-ghost.ngrok-free.app/geoserver'
os.environ['GEOSERVER_USERNAME'] = 'admin'
os.environ['GEOSERVER_PASSWORD'] = 'geoserver'

print("🔧 Test de configuration GeoServer:")
print(f"   URL: {os.environ['GEOSERVER_URL']}")
print(f"   Username: {os.environ['GEOSERVER_USERNAME']}")
print(f"   Password: {'*' * len(os.environ['GEOSERVER_PASSWORD'])}")

# Test d'importation de la fonction d'auth
try:
    from requests.auth import HTTPBasicAuth
    auth = HTTPBasicAuth(os.environ['GEOSERVER_USERNAME'], os.environ['GEOSERVER_PASSWORD'])
    print("✅ Authentification GeoServer configurée!")
    print(f"   Type: {type(auth)}")
except Exception as e:
    print(f"❌ Erreur: {e}")
