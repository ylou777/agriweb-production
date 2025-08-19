#!/usr/bin/env python3
"""
🧪 TEST COMPLET GEOSERVER RAILWAY
Vérification après déploiement réussi avec kartoza/geoserver:2.24.0
"""

import requests
import json
import time
from datetime import datetime

def test_geoserver_deployment():
    """Test complet du déploiement GeoServer Railway"""
    
    base_url = "https://geoserver-agriweb-production.up.railway.app"
    
    print("🚀 TEST COMPLET GEOSERVER RAILWAY")
    print("=" * 50)
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 URL de base: {base_url}")
    print()
    
    # Test 1: Page racine Tomcat/GeoServer
    print("1️⃣ Test de la page racine")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📄 Taille: {len(response.content)} bytes")
        if "geoserver" in response.text.lower():
            print("   🎯 Contenu GeoServer détecté!")
        elif "tomcat" in response.text.lower():
            print("   ⚠️ Page Tomcat détectée (normal)")
        print()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        print()
    
    # Test 2: Interface Web GeoServer
    print("2️⃣ Test de l'interface web GeoServer")
    try:
        response = requests.get(f"{base_url}/geoserver/web/", timeout=10)
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📄 Taille: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print("   🎉 INTERFACE WEB GEOSERVER ACCESSIBLE!")
            if "login" in response.text.lower() or "username" in response.text.lower():
                print("   🔐 Page de connexion détectée")
        elif response.status_code == 404:
            print("   ❌ GeoServer webapp non déployée")
        else:
            print(f"   ⚠️ Status inattendu: {response.status_code}")
        print()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        print()
    
    # Test 3: Page de services REST
    print("3️⃣ Test des services REST")
    try:
        response = requests.get(f"{base_url}/geoserver/rest/", timeout=10)
        print(f"   ✅ Status: {response.status_code}")
        if response.status_code == 401:
            print("   🔐 Authentification requise (normal)")
        elif response.status_code == 200:
            print("   ✅ Services REST accessibles")
        print()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        print()
    
    # Test 4: Page WMS Capabilities
    print("4️⃣ Test WMS GetCapabilities")
    try:
        wms_url = f"{base_url}/geoserver/wms?service=WMS&version=1.3.0&request=GetCapabilities"
        response = requests.get(wms_url, timeout=10)
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📄 Taille: {len(response.content)} bytes")
        
        if response.status_code == 200:
            if "WMS_Capabilities" in response.text:
                print("   🎯 Document WMS Capabilities valide!")
                # Compter les couches
                layer_count = response.text.count("<Layer")
                print(f"   📊 Couches détectées: {layer_count}")
            else:
                print("   ⚠️ Réponse WMS invalide")
        print()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        print()
    
    # Test 5: Page WFS Capabilities  
    print("5️⃣ Test WFS GetCapabilities")
    try:
        wfs_url = f"{base_url}/geoserver/wfs?service=WFS&version=2.0.0&request=GetCapabilities"
        response = requests.get(wfs_url, timeout=10)
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📄 Taille: {len(response.content)} bytes")
        
        if response.status_code == 200:
            if "WFS_Capabilities" in response.text:
                print("   🎯 Document WFS Capabilities valide!")
            else:
                print("   ⚠️ Réponse WFS invalide")
        print()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        print()
    
    # Test 6: Authentification avec admin/admin
    print("6️⃣ Test d'authentification admin/admin")
    try:
        auth = ('admin', 'admin')
        response = requests.get(f"{base_url}/geoserver/rest/workspaces", 
                              auth=auth, timeout=10)
        print(f"   ✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   🎉 AUTHENTIFICATION RÉUSSIE!")
            try:
                workspaces = response.json()
                if 'workspaces' in workspaces:
                    workspace_count = len(workspaces['workspaces']['workspace'])
                    print(f"   🗂️ Workspaces trouvés: {workspace_count}")
                    for ws in workspaces['workspaces']['workspace']:
                        print(f"      - {ws['name']}")
            except:
                print("   📝 Données JSON non parsables")
        elif response.status_code == 401:
            print("   ❌ Authentification échouée")
        else:
            print(f"   ⚠️ Status inattendu: {response.status_code}")
        print()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        print()
    
    # Test 7: Recherche du workspace "gpu"
    print("7️⃣ Test du workspace GPU")
    try:
        auth = ('admin', 'admin')
        response = requests.get(f"{base_url}/geoserver/rest/workspaces/gpu", 
                              auth=auth, timeout=10)
        print(f"   ✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   🎯 Workspace GPU trouvé!")
        elif response.status_code == 404:
            print("   ⚠️ Workspace GPU non trouvé (normal pour nouvelle install)")
        print()
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        print()
    
    # Résumé final
    print("=" * 50)
    print("📋 RÉSUMÉ DU TEST")
    print("=" * 50)
    
    try:
        # Test synthèse
        web_ok = False
        try:
            resp = requests.get(f"{base_url}/geoserver/web/", timeout=5)
            web_ok = resp.status_code == 200
        except:
            pass
        
        auth_ok = False
        try:
            auth = ('admin', 'admin')
            resp = requests.get(f"{base_url}/geoserver/rest/workspaces", 
                              auth=auth, timeout=5)
            auth_ok = resp.status_code == 200
        except:
            pass
        
        if web_ok and auth_ok:
            print("🎉 DÉPLOIEMENT RÉUSSI - GEOSERVER FONCTIONNEL!")
            print("✅ Interface web accessible")
            print("✅ Services REST opérationnels")
            print("✅ Authentification admin/admin fonctionnelle")
            print()
            print("🔗 Liens utiles:")
            print(f"   🌐 Interface web: {base_url}/geoserver/web/")
            print(f"   🔧 API REST: {base_url}/geoserver/rest/")
            print(f"   🗺️ WMS: {base_url}/geoserver/wms")
            print(f"   📊 WFS: {base_url}/geoserver/wfs")
            print()
            print("📝 Prochaines étapes:")
            print("   1. Créer le workspace 'gpu'")
            print("   2. Importer les 14 couches configurées")
            print("   3. Tester l'intégration avec AgriWeb")
            
        elif web_ok:
            print("⚠️ GEOSERVER PARTIELLEMENT FONCTIONNEL")
            print("✅ Interface web accessible")
            print("❌ Problème d'authentification")
            
        else:
            print("❌ PROBLÈME DE DÉPLOIEMENT")
            print("❌ Interface web inaccessible")
            print("💡 Le déploiement peut prendre quelques minutes supplémentaires")
            
    except Exception as e:
        print(f"❌ Erreur lors du résumé: {e}")
    
    print()
    print("🕒 Test terminé à:", datetime.now().strftime('%H:%M:%S'))

if __name__ == "__main__":
    test_geoserver_deployment()
