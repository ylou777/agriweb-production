#!/usr/bin/env python3
"""
Test rapide de connectivité GeoServer Railway
"""
import requests
import time

def test_geoserver():
    url = "https://geoserver-agriweb-production.up.railway.app/geoserver"
    
    print("🔍 Test de connectivité GeoServer Railway...")
    print(f"URL: {url}")
    
    try:
        print("⏳ Connexion en cours (timeout 60s)...")
        response = requests.get(url, timeout=60)
        
        print(f"✅ Connexion réussie!")
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"Taille réponse: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print(f"🎉 GeoServer est accessible!")
            if 'geoserver' in response.text.lower():
                print(f"✅ Page GeoServer détectée")
                return True
            else:
                print(f"⚠️  Page non-GeoServer")
                
    except requests.exceptions.Timeout:
        print(f"⏰ Timeout après 60 secondes")
    except requests.exceptions.ConnectionError as e:
        print(f"🔌 Erreur de connexion: {e}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    return False

if __name__ == "__main__":
    success = test_geoserver()
    exit(0 if success else 1)
