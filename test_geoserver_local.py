#!/usr/bin/env python3
"""
Test local de GeoServer
"""

import requests
import os
from requests.auth import HTTPBasicAuth

def test_local_geoserver():
    """Test de GeoServer en local"""
    
    print("🔍 Test GeoServer local")
    print("-" * 30)
    
    # Test sur localhost
    for url in ["http://localhost:8080/geoserver", "http://127.0.0.1:8080/geoserver"]:
        try:
            print(f"\n🌐 Test: {url}")
            response = requests.get(f"{url}/web/", 
                                  auth=HTTPBasicAuth("admin", "geoserver"),
                                  timeout=5)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ GeoServer accessible localement")
                return True
            else:
                print(f"   ❌ Erreur: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    print("\n❌ GeoServer non accessible localement")
    return False

if __name__ == "__main__":
    test_local_geoserver()
