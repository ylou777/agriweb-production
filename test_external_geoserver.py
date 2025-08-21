#!/usr/bin/env python3
"""
Test de connectivité externe après ouverture du port 8080
"""

import requests
from requests.auth import HTTPBasicAuth
import time

def test_external_geoserver():
    """Test de GeoServer depuis l'extérieur"""
    
    external_url = "http://81.220.178.156:8080/geoserver"
    
    print("🌐 Test de connectivité externe GeoServer")
    print(f"URL externe: {external_url}")
    print("-" * 50)
    
    try:
        print("🔍 Test de connexion...")
        response = requests.get(f"{external_url}/web/",
                              auth=HTTPBasicAuth("admin", "geoserver"),
                              timeout=15)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS! GeoServer accessible depuis l'extérieur")
            print("🎉 Railway pourra maintenant se connecter!")
            return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            print("🔧 Vérifiez la configuration du routeur")
            return False
            
    except requests.exceptions.ConnectTimeout:
        print("❌ Timeout de connexion")
        print("🔧 Le port 8080 n'est probablement pas ouvert sur le routeur")
        return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Erreur de connexion: {e}")
        print("🔧 Vérifiez:")
        print("   1. Configuration du routeur (port forwarding)")
        print("   2. Firewall Windows")
        print("   3. GeoServer en cours d'exécution")
        return False
        
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

if __name__ == "__main__":
    # Test local d'abord
    print("1️⃣ Test local d'abord...")
    try:
        local_response = requests.get("http://localhost:8080/geoserver/web/", 
                                    auth=HTTPBasicAuth("admin", "geoserver"), 
                                    timeout=5)
        if local_response.status_code == 200:
            print("✅ GeoServer fonctionne localement")
        else:
            print("❌ GeoServer ne répond pas localement")
            exit(1)
    except:
        print("❌ GeoServer non accessible localement - démarrez-le d'abord")
        exit(1)
    
    print("\n2️⃣ Test externe...")
    time.sleep(1)
    
    success = test_external_geoserver()
    
    if success:
        print("\n🎯 PROCHAINES ÉTAPES:")
        print("1. Configurez les variables d'environnement Railway:")
        print("   GEOSERVER_URL=http://81.220.178.156:8080/geoserver")
        print("   GEOSERVER_USERNAME=admin")
        print("   GEOSERVER_PASSWORD=geoserver")
        print("   ENVIRONMENT=production")
        print("\n2. Déployez votre application Railway")
        print("\n3. Testez l'accès depuis Railway")
    else:
        print("\n🚨 Le port 8080 n'est pas encore accessible depuis l'extérieur")
        print("Suivez le guide GUIDE_OUVERTURE_PORT_8080.md")
