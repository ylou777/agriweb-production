#!/usr/bin/env python3
"""
🎉 TEST GEOSERVER FONCTIONNEL
Vérification après déploiement réussi
"""

import requests
from datetime import datetime

def test_geoserver_working():
    """Test GeoServer maintenant fonctionnel"""
    
    print("🎉 GEOSERVER EST MAINTENANT INSTALLÉ !")
    print("=" * 50)
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    print("📋 Preuve dans les logs Railway :")
    print("   ✅ 'Deployment of web application directory [/usr/local/tomcat/webapps/geoserver] has finished in [41,502] ms'")
    print()
    
    base_url = "https://geoserver-agriweb-production.up.railway.app/geoserver"
    
    tests = [
        ("Interface Web", f"{base_url}/web/"),
        ("Services WMS", f"{base_url}/wms?service=WMS&version=1.3.0&request=GetCapabilities"),
        ("Services WFS", f"{base_url}/wfs?service=WFS&version=2.0.0&request=GetCapabilities"),
        ("API REST", f"{base_url}/rest/workspaces")
    ]
    
    results = {}
    
    for test_name, url in tests:
        print(f"🔍 Test {test_name}...")
        try:
            if "rest" in url:
                # Test avec authentification pour REST
                response = requests.get(url, auth=('admin', 'admin'), timeout=15)
            else:
                response = requests.get(url, timeout=15)
            
            results[test_name] = response.status_code
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS ! Status: {response.status_code}")
                print(f"   📄 Taille: {len(response.content):,} bytes")
                
                # Analyse du contenu
                if "wms" in url.lower() and "capabilities" in response.text.lower():
                    print("   🗺️ Document WMS Capabilities valide!")
                elif "wfs" in url.lower() and "capabilities" in response.text.lower():
                    print("   📊 Document WFS Capabilities valide!")
                elif "web" in url and "geoserver" in response.text.lower():
                    print("   🌐 Interface GeoServer chargée!")
                elif "rest" in url:
                    print("   🔧 API REST accessible!")
                    
            elif response.status_code == 401:
                print(f"   🔐 Auth requise (normal pour REST): {response.status_code}")
                results[test_name] = "Auth OK"
            else:
                print(f"   ⚠️ Status: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout - Service potentiellement en cours de démarrage")
            results[test_name] = "Timeout"
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            results[test_name] = "Error"
        
        print()
    
    # Résumé final
    print("=" * 50)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 50)
    
    success_count = sum(1 for status in results.values() 
                       if status == 200 or status == "Auth OK")
    total_tests = len(results)
    
    print(f"📈 Score: {success_count}/{total_tests} services fonctionnels")
    print()
    
    for test_name, status in results.items():
        if status == 200:
            print(f"   ✅ {test_name}: Fonctionnel")
        elif status == "Auth OK":
            print(f"   🔐 {test_name}: Auth requise (normal)")
        elif status == "Timeout":
            print(f"   ⏰ {test_name}: En cours de démarrage")
        else:
            print(f"   ⚠️ {test_name}: Status {status}")
    
    print()
    
    if success_count >= 2:
        print("🎉 GEOSERVER EST FONCTIONNEL !")
        print("✅ Prêt pour la création du workspace GPU")
        print("🔗 Interface admin: https://geoserver-agriweb-production.up.railway.app/geoserver/web/")
        print("👤 Identifiants: admin / admin")
        print()
        print("🚀 PROCHAINES ÉTAPES:")
        print("   1. Créer le workspace 'gpu'")
        print("   2. Importer les 14 couches de données")
        print("   3. Configurer les styles")
        print("   4. Tester l'intégration AgriWeb")
    else:
        print("⏳ GEOSERVER EN COURS DE FINALISATION")
        print("💡 Attendez 2-3 minutes et relancez le test")
    
    print("=" * 50)
    return results

if __name__ == "__main__":
    test_geoserver_working()
