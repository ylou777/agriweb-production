#!/usr/bin/env python3
"""
🧪 Test AgriWeb + GeoServer Railway
Vérifier l'intégration complète Flask + GeoServer
"""

import requests
import time
from datetime import datetime

def test_flask_geoserver_integration():
    """Tester l'intégration Flask + GeoServer"""
    
    print("🧪 TEST INTÉGRATION AGRIWEB + GEOSERVER RAILWAY")
    print("=" * 60)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # URLs de test
    flask_url = "http://localhost:5000"  # Votre app locale
    geoserver_url = "https://geoserver-agriweb-production.up.railway.app"
    
    results = {}
    
    # Test 1: Application Flask locale
    print("🐍 Test 1: Application Flask locale...")
    try:
        response = requests.get(flask_url, timeout=10)
        if response.status_code == 200:
            print("✅ Flask app accessible")
            results['flask'] = True
        else:
            print(f"⚠️ Flask app code: {response.status_code}")
            results['flask'] = False
    except Exception as e:
        print(f"❌ Flask app: {e}")
        print("💡 Lancez d'abord: python agriweb_hebergement_gratuit.py")
        results['flask'] = False
    
    # Test 2: GeoServer Railway
    print("\n🗺️ Test 2: GeoServer Railway...")
    try:
        response = requests.get(f"{geoserver_url}/geoserver/web/", timeout=15)
        if response.status_code == 200:
            print("✅ GeoServer accessible")
            results['geoserver'] = True
            
            # Test API REST
            try:
                rest_response = requests.get(
                    f"{geoserver_url}/geoserver/rest/workspaces",
                    auth=("admin", "admin123"),
                    timeout=10
                )
                if rest_response.status_code == 200:
                    print("✅ API REST GeoServer fonctionnelle")
                    workspaces = rest_response.json()
                    count = len(workspaces.get('workspaces', {}).get('workspace', []))
                    print(f"📁 Workspaces disponibles: {count}")
                    results['geoserver_api'] = True
                else:
                    print(f"⚠️ API REST: {rest_response.status_code}")
                    results['geoserver_api'] = False
            except Exception as e:
                print(f"⚠️ API REST: {e}")
                results['geoserver_api'] = False
                
        else:
            print(f"⏳ GeoServer code: {response.status_code}")
            results['geoserver'] = False
            
    except Exception as e:
        print(f"⏳ GeoServer: {e}")
        results['geoserver'] = False
    
    # Test 3: Intégration dans Flask
    print("\n🔗 Test 3: Configuration dans Flask...")
    try:
        # Tester l'endpoint de health de votre app
        response = requests.get(f"{flask_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Health check Flask OK")
            print(f"📍 Plateforme: {health_data.get('platform', 'Inconnue')}")
            print(f"💳 Stripe: {'✅' if health_data.get('stripe_available') else '❌'}")
            results['flask_health'] = True
        else:
            print("⚠️ Health check non disponible")
            results['flask_health'] = False
    except Exception as e:
        print(f"⚠️ Health check: {e}")
        results['flask_health'] = False
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("-" * 30)
    
    for test_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    all_success = all(results.values())
    
    if all_success:
        print("\n🎉 INTÉGRATION COMPLÈTE RÉUSSIE!")
        print("🚀 Votre AgriWeb est prêt pour la production!")
        print()
        print("📋 Prochaines étapes:")
        print("1. ✅ Déployer votre Flask app sur Railway/Render/Heroku")
        print("2. ✅ Configurer les variables d'environnement")
        print("3. ✅ Importer vos données dans GeoServer")
        print("4. ✅ Tester en production")
        
    else:
        print("\n⚠️ Intégration partielle")
        print("💡 Solutions:")
        
        if not results.get('flask'):
            print("🐍 Lancez Flask: python agriweb_hebergement_gratuit.py")
        
        if not results.get('geoserver'):
            print("🗺️ Attendez le démarrage complet de GeoServer (5-10 min)")
            print(f"   URL: {geoserver_url}/geoserver/web/")
        
        if not results.get('geoserver_api'):
            print("🔧 Vérifiez les credentials GeoServer (admin/admin123)")
    
    return all_success

def quick_geoserver_check():
    """Check rapide du statut GeoServer"""
    print("⚡ Check rapide GeoServer...")
    
    try:
        response = requests.get(
            "https://geoserver-agriweb-production.up.railway.app/geoserver/web/",
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ GeoServer opérationnel!")
            print("🌐 Interface: https://geoserver-agriweb-production.up.railway.app/geoserver/web/")
            print("👤 Login: admin / admin123")
            return True
        else:
            print(f"⏳ GeoServer status: {response.status_code}")
            print("💡 Encore en cours de démarrage...")
            return False
            
    except Exception as e:
        print(f"⏳ GeoServer: {e}")
        print("💡 Démarrage en cours...")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_geoserver_check()
    else:
        print("🧪 Test complet d'intégration AgriWeb + GeoServer")
        print("💡 Pour un test rapide: python test_integration.py --quick")
        print()
        
        test_flask_geoserver_integration()
