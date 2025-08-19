#!/usr/bin/env python3
"""
Test simple de connectivité GeoServer Railway
"""

import requests
import time
from datetime import datetime

def test_geoserver():
    url = "https://geoserver-agriweb-production.up.railway.app/geoserver"
    
    print(f"🔍 Test GeoServer Railway - {datetime.now().strftime('%H:%M:%S')}")
    print(f"URL: {url}")
    print("-" * 50)
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print("✅ GEOSERVER ACCESSIBLE !")
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            
            # Vérifier si c'est bien GeoServer
            if 'geoserver' in response.text.lower():
                print("✅ Réponse GeoServer confirmée")
            else:
                print("⚠️  Réponse reçue mais contenu inattendu")
                
            return True
            
        else:
            print(f"❌ Status non-OK: {response.status_code}")
            print(f"Réponse: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Erreur de connexion - Service pas encore prêt")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout - Service trop lent ou pas prêt")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    test_geoserver()
