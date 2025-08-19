#!/usr/bin/env python3
"""
🔍 TEST D'ACCÈS GEOSERVER
Vérification de l'accès aux différentes URL GeoServer
"""

import requests
from datetime import datetime

def test_geoserver_urls():
    """Test des différentes URL GeoServer"""
    
    print("🔍 TEST D'ACCÈS GEOSERVER")
    print("=" * 50)
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    base_url = "https://geoserver-agriweb-production.up.railway.app"
    
    urls_to_test = {
        "🏠 Page d'accueil Tomcat": f"{base_url}/",
        "🌐 Interface GeoServer": f"{base_url}/geoserver/",
        "🔧 Interface Admin": f"{base_url}/geoserver/web/",
        "📊 Services WMS": f"{base_url}/geoserver/wms",
        "📋 Services WFS": f"{base_url}/geoserver/ows",
        "🗂️ REST API": f"{base_url}/geoserver/rest/",
        "📈 Workspace GPU": f"{base_url}/geoserver/rest/workspaces/gpu"
    }
    
    results = {}
    
    for name, url in urls_to_test.items():
        try:
            print(f"Testing {name}...")
            response = requests.get(url, timeout=10, verify=True)
            status = response.status_code
            
            if status == 200:
                print(f"✅ {name}: OK (200)")
                results[name] = "✅ OK"
            elif status == 404:
                print(f"🔍 {name}: Non trouvé (404)")
                results[name] = "❌ Non trouvé"
            elif status == 401:
                print(f"🔐 {name}: Authentification requise (401)")
                results[name] = "🔐 Auth requise"
            elif status == 403:
                print(f"🚫 {name}: Accès interdit (403)")
                results[name] = "🚫 Interdit"
            else:
                print(f"⚠️ {name}: Code {status}")
                results[name] = f"⚠️ {status}"
                
        except requests.exceptions.ConnectTimeout:
            print(f"⏰ {name}: Timeout de connexion")
            results[name] = "⏰ Timeout"
        except requests.exceptions.RequestException as e:
            print(f"❌ {name}: Erreur - {e}")
            results[name] = f"❌ Erreur"
    
    print()
    print("📋 RÉSUMÉ DES TESTS")
    print("=" * 30)
    for name, result in results.items():
        print(f"{result} {name}")
    
    print()
    
    # Test spécial avec authentification
    print("🔐 TEST AVEC AUTHENTIFICATION")
    print("-" * 30)
    
    try:
        auth_url = f"{base_url}/geoserver/web/"
        print(f"Testing avec admin:admin...")
        
        response = requests.get(
            auth_url, 
            auth=('admin', 'admin'),
            timeout=10,
            verify=True
        )
        
        if response.status_code == 200:
            print("✅ Authentification admin:admin OK")
            if "GeoServer" in response.text:
                print("✅ Interface GeoServer détectée")
            else:
                print("⚠️ Contenu inattendu")
        else:
            print(f"❌ Authentification échouée: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur d'authentification: {e}")
    
    print()
    print("💡 INSTRUCTIONS SUIVANTES")
    print("-" * 25)
    print("1. 🌐 Ouvrez: https://geoserver-agriweb-production.up.railway.app/geoserver/web/")
    print("2. 🔐 Connectez-vous avec: admin / admin")
    print("3. 🗂️ Créez le workspace 'gpu'")
    print("4. 📥 Importez vos couches de données")

if __name__ == "__main__":
    test_geoserver_urls()
