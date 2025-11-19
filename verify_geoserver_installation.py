#!/usr/bin/env python3
"""
🔍 VÉRIFICATION RIGOUREUSE GEOSERVER
Est-ce que GeoServer est VRAIMENT installé sur Railway ?
"""

import requests
import json
from datetime import datetime

def verify_geoserver_installation():
    """Vérification rigoureuse de l'installation GeoServer"""
    
    base_url = "https://geoserver-agriweb-production.up.railway.app"
    
    print("🔍 VÉRIFICATION RIGOUREUSE GEOSERVER")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    print(f"🌐 URL: {base_url}")
    print()
    
    results = {
        "tomcat_root": False,
        "geoserver_web": False,
        "geoserver_rest": False,
        "geoserver_wms": False,
        "geoserver_wfs": False,
        "authentication": False
    }
    
    # Test 1: Page racine Tomcat
    print("1️⃣ Test page racine Tomcat...")
    try:
        response = requests.get(f"{base_url}/", timeout=15)
        results["tomcat_root"] = response.status_code == 200
        
        if results["tomcat_root"]:
            print(f"   ✅ Tomcat accessible (Status: {response.status_code})")
            print(f"   📄 Taille: {len(response.content):,} bytes")
            
            # Analyser le contenu
            content = response.text.lower()
            if "geoserver" in content:
                print("   🎯 Mention 'GeoServer' trouvée dans la page!")
            elif "tomcat" in content:
                print("   📝 Page Tomcat standard détectée")
            else:
                print("   ❓ Contenu non identifié")
        else:
            print(f"   ❌ Tomcat inaccessible (Status: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Erreur Tomcat: {e}")
    
    print()
    
    # Test 2: Interface web GeoServer - LE TEST CRUCIAL
    print("2️⃣ Test interface web GeoServer (CRUCIAL)...")
    try:
        response = requests.get(f"{base_url}/geoserver/web/", timeout=15)
        results["geoserver_web"] = response.status_code == 200
        
        if results["geoserver_web"]:
            print(f"   ✅ Interface GeoServer accessible! (Status: {response.status_code})")
            print(f"   📄 Taille: {len(response.content):,} bytes")
            
            content = response.text.lower()
            indicators = {
                "login": "login" in content,
                "username": "username" in content,
                "password": "password" in content,
                "geoserver": "geoserver" in content,
                "administration": "administration" in content
            }
            
            print(f"   🔍 Analyse contenu:")
            for indicator, found in indicators.items():
                status = "✅" if found else "❌"
                print(f"      {status} {indicator}")
                
        elif response.status_code == 404:
            print(f"   ❌ GeoServer NON INSTALLÉ (404 - webapp manquante)")
        else:
            print(f"   ⚠️ Status inattendu: {response.status_code}")
            print(f"   📄 Contenu: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Erreur interface: {e}")
    
    print()
    
    # Test 3: API REST GeoServer
    print("3️⃣ Test API REST GeoServer...")
    try:
        response = requests.get(f"{base_url}/geoserver/rest/", timeout=15)
        results["geoserver_rest"] = response.status_code in [200, 401]
        
        if response.status_code == 401:
            print(f"   ✅ API REST détectée (401 - Auth requise)")
        elif response.status_code == 200:
            print(f"   ✅ API REST accessible (200)")
        elif response.status_code == 404:
            print(f"   ❌ API REST non trouvée (404)")
        else:
            print(f"   ⚠️ Status API: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur API: {e}")
    
    print()
    
    # Test 4: Services WMS
    print("4️⃣ Test services WMS...")
    try:
        wms_url = f"{base_url}/geoserver/wms?service=WMS&version=1.3.0&request=GetCapabilities"
        response = requests.get(wms_url, timeout=15)
        results["geoserver_wms"] = response.status_code == 200
        
        if results["geoserver_wms"]:
            print(f"   ✅ WMS fonctionne! (Status: {response.status_code})")
            print(f"   📄 Taille: {len(response.content):,} bytes")
            
            if "WMS_Capabilities" in response.text:
                print("   🎯 Document WMS Capabilities valide!")
                # Compter les layers
                layer_count = response.text.count("<Layer")
                print(f"   📊 Layers WMS: {layer_count}")
            else:
                print("   ❌ Document WMS invalide")
        else:
            print(f"   ❌ WMS non fonctionnel (Status: {response.status_code})")
            
    except Exception as e:
        print(f"   ❌ Erreur WMS: {e}")
    
    print()
    
    # Test 5: Services WFS
    print("5️⃣ Test services WFS...")
    try:
        wfs_url = f"{base_url}/geoserver/wfs?service=WFS&version=2.0.0&request=GetCapabilities"
        response = requests.get(wfs_url, timeout=15)
        results["geoserver_wfs"] = response.status_code == 200
        
        if results["geoserver_wfs"]:
            print(f"   ✅ WFS fonctionne! (Status: {response.status_code})")
            if "WFS_Capabilities" in response.text:
                print("   🎯 Document WFS Capabilities valide!")
            else:
                print("   ❌ Document WFS invalide")
        else:
            print(f"   ❌ WFS non fonctionnel (Status: {response.status_code})")
            
    except Exception as e:
        print(f"   ❌ Erreur WFS: {e}")
    
    print()
    
    # Test 6: Authentification admin/admin
    print("6️⃣ Test authentification admin/admin...")
    try:
        auth = ('admin', 'admin')
        response = requests.get(f"{base_url}/geoserver/rest/workspaces", 
                              auth=auth, timeout=15)
        results["authentication"] = response.status_code == 200
        
        if results["authentication"]:
            print(f"   ✅ Authentification réussie! (Status: {response.status_code})")
            try:
                data = response.json()
                if 'workspaces' in data:
                    workspaces = data['workspaces']['workspace']
                    print(f"   🗂️ Workspaces: {len(workspaces)}")
                    for ws in workspaces[:5]:  # Limiter l'affichage
                        print(f"      - {ws['name']}")
                else:
                    print("   📭 Aucun workspace")
            except:
                print("   📄 Réponse non-JSON")
        elif response.status_code == 401:
            print(f"   ❌ Authentification échouée (401)")
        else:
            print(f"   ⚠️ Status auth: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur auth: {e}")
    
    print()
    print("=" * 60)
    print("📊 DIAGNOSTIC FINAL")
    print("=" * 60)
    
    # Calcul du score
    total_tests = len(results)
    passed_tests = sum(results.values())
    score = (passed_tests / total_tests) * 100
    
    print(f"📈 Score: {passed_tests}/{total_tests} tests passés ({score:.1f}%)")
    print()
    
    for test_name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name.replace('_', ' ').title()}")
    
    print()
    
    # Verdict final
    if results["geoserver_web"] and results["authentication"]:
        print("🎉 VERDICT: GEOSERVER INSTALLÉ ET FONCTIONNEL!")
        print("✅ Interface web accessible")
        print("✅ Authentification opérationnelle")
        print("✅ Prêt pour l'utilisation")
        print()
        print("🔗 ACCÈS GEOSERVER:")
        print(f"   🌐 Interface: {base_url}/geoserver/web/")
        print(f"   👤 Identifiants: admin / admin")
        
    elif results["tomcat_root"] and not results["geoserver_web"]:
        print("❌ VERDICT: TOMCAT SEUL - GEOSERVER NON INSTALLÉ!")
        print("✅ Tomcat fonctionne")
        print("❌ GeoServer webapp manquante")
        print("💡 Solution: Vérifier l'image Docker Railway")
        
    elif not results["tomcat_root"]:
        print("❌ VERDICT: SERVICE NON ACCESSIBLE!")
        print("❌ Aucun serveur web détecté")
        print("💡 Solution: Vérifier le déploiement Railway")
        
    else:
        print("⚠️ VERDICT: INSTALLATION PARTIELLE")
        print("💡 Certains services manquent ou dysfonctionnent")
    
    print("=" * 60)
    return results

if __name__ == "__main__":
    verify_geoserver_installation()
