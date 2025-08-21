#!/usr/bin/env python3
"""
Test direct de connexion GeoServer après désactivation anti-bruteforce
"""

import requests
import os
from requests.auth import HTTPBasicAuth
import json

# Configuration GeoServer
GEOSERVER_URL = "http://81.220.178.156:8080/geoserver"
GEOSERVER_USER = "admin"
GEOSERVER_PASSWORD = "geoserver"

def test_geoserver_connection():
    """Test complet de la connexion GeoServer"""
    
    print("🔍 Test de connexion GeoServer direct")
    print(f"URL: {GEOSERVER_URL}")
    print(f"Utilisateur: {GEOSERVER_USER}")
    print("-" * 50)
    
    # Test 1: Accès de base
    try:
        print("1️⃣ Test d'accès de base...")
        response = requests.get(f"{GEOSERVER_URL}/web/", 
                              auth=HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD),
                              timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Accès de base OK")
        else:
            print(f"   ❌ Erreur d'accès: {response.status_code}")
            print(f"   Réponse: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
        return False
    
    # Test 2: API REST
    try:
        print("\n2️⃣ Test API REST...")
        response = requests.get(f"{GEOSERVER_URL}/rest/workspaces.json",
                              auth=HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD),
                              timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ API REST OK")
            workspaces = response.json()
            print(f"   Workspaces trouvés: {len(workspaces.get('workspaces', {}).get('workspace', []))}")
        else:
            print(f"   ❌ Erreur API REST: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur API REST: {e}")
    
    # Test 3: WMS Capabilities
    try:
        print("\n3️⃣ Test WMS Capabilities...")
        response = requests.get(f"{GEOSERVER_URL}/wms",
                              params={
                                  'service': 'WMS',
                                  'version': '1.1.0',
                                  'request': 'GetCapabilities'
                              },
                              auth=HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD),
                              timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ WMS Capabilities OK")
            if 'WMT_MS_Capabilities' in response.text or 'WMS_Capabilities' in response.text:
                print("   ✅ Format XML WMS valide")
            else:
                print("   ⚠️ Format XML WMS non reconnu")
        else:
            print(f"   ❌ Erreur WMS: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur WMS: {e}")
    
    # Test 4: WFS Capabilities
    try:
        print("\n4️⃣ Test WFS Capabilities...")
        response = requests.get(f"{GEOSERVER_URL}/wfs",
                              params={
                                  'service': 'WFS',
                                  'version': '1.0.0',
                                  'request': 'GetCapabilities'
                              },
                              auth=HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD),
                              timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ WFS Capabilities OK")
            if 'WFS_Capabilities' in response.text:
                print("   ✅ Format XML WFS valide")
            else:
                print("   ⚠️ Format XML WFS non reconnu")
        else:
            print(f"   ❌ Erreur WFS: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur WFS: {e}")
    
    # Test 5: Vérification des couches
    try:
        print("\n5️⃣ Test des couches disponibles...")
        response = requests.get(f"{GEOSERVER_URL}/rest/layers.json",
                              auth=HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASSWORD),
                              timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            layers_data = response.json()
            layers = layers_data.get('layers', {}).get('layer', [])
            print(f"   ✅ {len(layers)} couches trouvées")
            if layers:
                print("   Premières couches:")
                for layer in layers[:3]:
                    layer_name = layer.get('name', 'Nom inconnu')
                    print(f"     - {layer_name}")
        else:
            print(f"   ❌ Erreur couches: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur couches: {e}")
    
    print("\n" + "="*50)
    print("🏁 Test terminé")
    return True

if __name__ == "__main__":
    test_geoserver_connection()
