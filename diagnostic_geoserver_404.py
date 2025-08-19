#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC GEOSERVER 404 - RAILWAY
Analyse complète de l'erreur 404 sur GeoServer Railway
"""

import requests
import time
from datetime import datetime

def test_geoserver_endpoints():
    """Test complet des endpoints GeoServer"""
    base_url = "https://geoserver-agriweb-production.up.railway.app"
    
    endpoints_to_test = [
        "/",                    # Racine Railway
        "/geoserver",          # Service GeoServer
        "/geoserver/",         # Service GeoServer avec slash
        "/geoserver/web",      # Interface admin sans slash
        "/geoserver/web/",     # Interface admin avec slash
        "/geoserver/rest",     # API REST
        "/geoserver/ows",      # Service OWS (WFS/WMS)
    ]
    
    print("🔍 DIAGNOSTIC GEOSERVER 404 - RAILWAY")
    print("=" * 50)
    print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Base URL: {base_url}")
    print()
    
    working_endpoints = []
    failed_endpoints = []
    
    for endpoint in endpoints_to_test:
        url = f"{base_url}{endpoint}"
        print(f"🔍 Test: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            status = response.status_code
            
            if status == 200:
                print(f"   ✅ OK - {status}")
                working_endpoints.append(endpoint)
            elif status == 404:
                print(f"   ❌ 404 - Non trouvé")
                failed_endpoints.append(endpoint)
            elif status == 302 or status == 301:
                print(f"   🔄 {status} - Redirection")
                print(f"   📍 Location: {response.headers.get('Location', 'Non spécifié')}")
                working_endpoints.append(endpoint)
            else:
                print(f"   ⚠️ {status} - Autre erreur")
                failed_endpoints.append(endpoint)
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connexion impossible")
            failed_endpoints.append(endpoint)
        except requests.exceptions.Timeout:
            print(f"   ⏱️ Timeout (>10s)")
            failed_endpoints.append(endpoint)
        except Exception as e:
            print(f"   ❌ Erreur: {str(e)}")
            failed_endpoints.append(endpoint)
        
        time.sleep(1)  # Pause entre les tests
    
    print("\n📊 RÉSULTATS:")
    print("=" * 30)
    print(f"✅ Endpoints fonctionnels: {len(working_endpoints)}")
    for ep in working_endpoints:
        print(f"   • {ep}")
    
    print(f"\n❌ Endpoints en erreur: {len(failed_endpoints)}")
    for ep in failed_endpoints:
        print(f"   • {ep}")

def check_railway_deployment():
    """Vérification du déploiement Railway"""
    print("\n🚂 VÉRIFICATION RAILWAY:")
    print("=" * 30)
    
    base_url = "https://geoserver-agriweb-production.up.railway.app"
    
    try:
        # Test de la racine Railway
        response = requests.get(base_url, timeout=10)
        
        print(f"Status: {response.status_code}")
        print(f"Headers:")
        for key, value in response.headers.items():
            if key.lower() in ['server', 'x-powered-by', 'content-type']:
                print(f"   {key}: {value}")
        
        if response.status_code == 200:
            content = response.text[:500]
            print(f"\nContenu (premier 500 chars):")
            print(content)
            
            if "geoserver" in content.lower():
                print("✅ Mention de GeoServer trouvée")
            else:
                print("⚠️ Aucune mention de GeoServer")
                
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")

def suggest_solutions():
    """Suggestions de solutions"""
    print("\n💡 SOLUTIONS POSSIBLES:")
    print("=" * 30)
    print("1. 🕒 Attendre le démarrage complet (5-10 minutes)")
    print("2. 🔄 Redémarrer le service Railway")
    print("3. 📝 Vérifier les logs Railway")
    print("4. 🌐 Tester l'URL alternative sans /geoserver")
    print("5. 🔧 Vérifier la configuration Docker")
    print()
    print("🌐 URLs à tester manuellement:")
    print("   • https://geoserver-agriweb-production.up.railway.app/")
    print("   • https://geoserver-agriweb-production.up.railway.app/geoserver")
    print("   • https://geoserver-agriweb-production.up.railway.app/geoserver/web/")

if __name__ == "__main__":
    test_geoserver_endpoints()
    check_railway_deployment()
    suggest_solutions()
