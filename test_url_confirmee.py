#!/usr/bin/env python3
"""
🧪 Test spécifique pour votre GeoServer Railway
URL: https://geoserver-agriweb-production.up.railway.app
"""

import requests
import time
from datetime import datetime

def test_geoserver_startup():
    """Tester le démarrage de GeoServer avec votre URL"""
    
    base_url = "https://geoserver-agriweb-production.up.railway.app"
    admin_user = "admin"
    admin_password = "admin123"
    
    print("🚀 TEST GEOSERVER RAILWAY - URL CONFIRMÉE")
    print("=" * 60)
    print(f"🌐 URL: {base_url}")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Serveur répond
    print("🏥 Test 1: Serveur de base...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Serveur Railway répond")
        else:
            print(f"⚠️ Code: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    # Test 2: GeoServer en cours de démarrage
    print("\n🔄 Test 2: Démarrage GeoServer...")
    endpoints_to_test = [
        "/geoserver",
        "/geoserver/web",
        "/geoserver/web/",
        "/geoserver/ows"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=15)
            print(f"  {endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ GeoServer accessible via: {endpoint}")
                break
        except Exception as e:
            print(f"  {endpoint}: ❌ {e}")
    
    # Test 3: Attendre le démarrage complet
    print("\n⏳ Test 3: Attente démarrage complet...")
    max_attempts = 10
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"  Tentative {attempt}/{max_attempts}...")
            response = requests.get(f"{base_url}/geoserver/web/", timeout=30)
            
            if response.status_code == 200:
                print("✅ GeoServer complètement démarré!")
                
                # Test connexion admin
                print("\n🔐 Test 4: Connexion admin...")
                auth_response = requests.get(
                    f"{base_url}/geoserver/rest/workspaces",
                    auth=(admin_user, admin_password),
                    timeout=15
                )
                
                if auth_response.status_code == 200:
                    print("✅ Connexion admin réussie!")
                    workspaces = auth_response.json()
                    workspace_count = len(workspaces.get('workspaces', {}).get('workspace', []))
                    print(f"📁 Workspaces disponibles: {workspace_count}")
                    
                    print("\n🎉 GEOSERVER PRÊT POUR PRODUCTION!")
                    print("=" * 60)
                    print(f"🌐 Interface Admin: {base_url}/geoserver/web/")
                    print(f"👤 Login: {admin_user} / {admin_password}")
                    print(f"🔧 API REST: {base_url}/geoserver/rest/")
                    print(f"🗺️ Services WMS/WFS: {base_url}/geoserver/ows")
                    print("\n📋 Prochaines étapes:")
                    print("1. Importer vos 100 Go de données géospatiales")
                    print("2. Configurer vos couches")
                    print("3. Connecter votre application Flask")
                    print("4. Tester en production!")
                    
                    return True
                else:
                    print(f"⚠️ Problème auth admin: {auth_response.status_code}")
            
            else:
                print(f"  Status: {response.status_code} - GeoServer encore en démarrage...")
                
        except Exception as e:
            print(f"  Erreur: {e}")
        
        if attempt < max_attempts:
            print("  ⏳ Attente 30 secondes...")
            time.sleep(30)
    
    print("\n⚠️ GeoServer prend plus de temps que prévu à démarrer")
    print("💡 Ceci est normal pour le premier démarrage")
    print(f"🌐 Continuez à vérifier: {base_url}/geoserver/web/")
    
    return False

if __name__ == "__main__":
    test_geoserver_startup()
