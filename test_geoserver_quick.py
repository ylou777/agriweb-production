#!/usr/bin/env python3
"""
🎉 TEST RAPIDE GEOSERVER - Post déploiement réussi
"""

import requests
from datetime import datetime

def test_geoserver_quick():
    """Test rapide GeoServer après déploiement réussi"""
    
    base_url = "https://geoserver-agriweb-production.up.railway.app"
    
    print("🎉 TEST RAPIDE GEOSERVER APRÈS DÉPLOIEMENT RÉUSSI")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Test interface web
    print("🌐 Test interface web...")
    try:
        response = requests.get(f"{base_url}/geoserver/web/", timeout=15)
        if response.status_code == 200:
            print(f"   ✅ Interface web accessible (Status: {response.status_code})")
            print(f"   📄 Taille réponse: {len(response.content):,} bytes")
            if "login" in response.text.lower():
                print("   🔐 Page de connexion détectée - PARFAIT!")
        else:
            print(f"   ⚠️ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print()
    
    # Test authentification admin/admin
    print("🔑 Test authentification admin/admin...")
    try:
        auth = ('admin', 'admin')
        response = requests.get(f"{base_url}/geoserver/rest/workspaces", 
                              auth=auth, timeout=15)
        if response.status_code == 200:
            print(f"   ✅ Authentification réussie!")
            data = response.json()
            if 'workspaces' in data:
                count = len(data['workspaces']['workspace'])
                print(f"   🗂️ Workspaces trouvés: {count}")
            else:
                print("   🗂️ Aucun workspace trouvé (normal pour nouvelle installation)")
        else:
            print(f"   ⚠️ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print()
    
    # Test WMS GetCapabilities
    print("🗺️ Test WMS GetCapabilities...")
    try:
        wms_url = f"{base_url}/geoserver/wms?service=WMS&version=1.3.0&request=GetCapabilities"
        response = requests.get(wms_url, timeout=15)
        if response.status_code == 200:
            print(f"   ✅ WMS GetCapabilities fonctionne!")
            print(f"   📄 Taille: {len(response.content):,} bytes")
            if "WMS_Capabilities" in response.text:
                print("   🎯 Document XML WMS valide!")
        else:
            print(f"   ⚠️ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print()
    print("=" * 60)
    print("🎉 RÉSUMÉ:")
    
    # Test final synthétique
    try:
        web_ok = requests.get(f"{base_url}/geoserver/web/", timeout=10).status_code == 200
        auth_ok = requests.get(f"{base_url}/geoserver/rest/workspaces", 
                             auth=('admin', 'admin'), timeout=10).status_code == 200
        wms_ok = requests.get(f"{base_url}/geoserver/wms?service=WMS&version=1.3.0&request=GetCapabilities", 
                            timeout=10).status_code == 200
        
        if web_ok and auth_ok and wms_ok:
            print("🚀 GEOSERVER ENTIÈREMENT FONCTIONNEL!")
            print("✅ Interface web accessible")
            print("✅ Authentification opérationnelle") 
            print("✅ Services WMS disponibles")
            print()
            print("🔗 LIENS UTILES:")
            print(f"   🌐 Interface: {base_url}/geoserver/web/")
            print(f"   🔧 API REST: {base_url}/geoserver/rest/")
            print(f"   🗺️ WMS: {base_url}/geoserver/wms")
            print(f"   📊 WFS: {base_url}/geoserver/wfs")
            print()
            print("👤 Identifiants: admin / admin")
            print()
            print("📝 PROCHAINES ÉTAPES:")
            print("   1. Créer le workspace 'gpu'")
            print("   2. Importer les 14 couches configurées")
            print("   3. Tester l'intégration avec AgriWeb")
        else:
            print("⚠️ PROBLÈMES DÉTECTÉS:")
            print(f"   Interface web: {'✅' if web_ok else '❌'}")
            print(f"   Authentification: {'✅' if auth_ok else '❌'}")
            print(f"   Services WMS: {'✅' if wms_ok else '❌'}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test synthétique: {e}")
    
    print("=" * 60)

if __name__ == "__main__":
    test_geoserver_quick()
