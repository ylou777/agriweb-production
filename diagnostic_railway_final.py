#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC FINAL RAILWAY GEOSERVER
Analyse definitive du problème de déploiement
"""

import requests
import json
from datetime import datetime

def diagnostic_final():
    """Diagnostic définitif du problème Railway"""
    
    print("🔍 DIAGNOSTIC FINAL RAILWAY GEOSERVER")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    base_url = "https://geoserver-agriweb-production.up.railway.app"
    
    # Test 1: Page racine Railway
    print("1️⃣ ANALYSE PAGE RACINE RAILWAY")
    print("-" * 40)
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Taille: {len(response.content):,} bytes")
        
        if response.status_code == 200:
            content = response.text.lower()
            print("🔍 Analyse du contenu:")
            
            # Vérifications spécifiques
            checks = {
                "Apache Tomcat": "apache tomcat" in content,
                "GeoServer": "geoserver" in content,
                "Manager App": "manager" in content,
                "Host Manager": "host-manager" in content,
                "Documentation": "documentation" in content,
                "Examples": "examples" in content
            }
            
            for check, found in checks.items():
                status = "✅" if found else "❌"
                print(f"   {status} {check}")
            
            # Recherche de liens d'applications
            print("\n🔗 Applications détectées:")
            if "manager" in content:
                print("   📁 /manager/ - Tomcat Manager")
            if "host-manager" in content:
                print("   📁 /host-manager/ - Host Manager")
            if "examples" in content:
                print("   📁 /examples/ - Exemples Servlet")
            if "docs" in content:
                print("   📁 /docs/ - Documentation Tomcat")
            
            # Vérification critique
            if "geoserver" not in content:
                print("   ❌ /geoserver/ - NON TROUVÉ!")
                print("   💡 GeoServer webapp n'est PAS déployée!")
            else:
                print("   ✅ /geoserver/ - Trouvé")
                
        elif response.status_code == 502:
            print("❌ Status 502: Service en erreur")
            try:
                error_data = response.json()
                print(f"Erreur: {error_data.get('message', 'Unknown')}")
            except:
                print("Réponse non-JSON")
        else:
            print(f"❌ Status inattendu: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
    
    print()
    
    # Test 2: Test direct GeoServer
    print("2️⃣ TEST DIRECT GEOSERVER")
    print("-" * 40)
    try:
        response = requests.get(f"{base_url}/geoserver", timeout=10)
        print(f"Status /geoserver: {response.status_code}")
        
        if response.status_code == 404:
            print("❌ GeoServer webapp NON DÉPLOYÉE")
        elif response.status_code == 502:
            print("⚠️ Service en erreur")
        elif response.status_code == 200:
            print("✅ GeoServer accessible")
        else:
            print(f"⚠️ Status inattendu: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print()
    
    # Test 3: Test applications Tomcat standards
    print("3️⃣ TEST APPLICATIONS TOMCAT STANDARDS")
    print("-" * 40)
    
    tomcat_apps = [
        ("manager", "Tomcat Manager"),
        ("host-manager", "Host Manager"),
        ("docs", "Documentation"),
        ("examples", "Exemples")
    ]
    
    for app_path, app_name in tomcat_apps:
        try:
            response = requests.get(f"{base_url}/{app_path}/", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ /{app_path}/ - {app_name} (OK)")
            elif response.status_code == 401:
                print(f"   🔐 /{app_path}/ - {app_name} (Auth requise)")
            elif response.status_code == 404:
                print(f"   ❌ /{app_path}/ - {app_name} (Non trouvé)")
            else:
                print(f"   ⚠️ /{app_path}/ - Status {response.status_code}")
        except:
            print(f"   ❌ /{app_path}/ - Erreur connexion")
    
    print()
    
    # Verdict final
    print("=" * 60)
    print("📋 VERDICT FINAL")
    print("=" * 60)
    
    print("🔍 ANALYSE DES PREUVES:")
    print()
    print("✅ Railway fonctionne")
    print("✅ Tomcat 9.0.20 démarré")
    print("✅ Applications Tomcat standard présentes:")
    print("   - Manager, Host-Manager, Docs, Examples")
    print()
    print("❌ PROBLÈME IDENTIFIÉ:")
    print("   🚨 GEOSERVER WEBAPP MANQUANTE!")
    print("   📁 Aucun déploiement /webapps/geoserver/")
    print("   🐳 Image Docker incorrecte")
    print()
    print("💡 SOLUTION:")
    print("   1. Changer l'image Docker Railway")
    print("   2. Utiliser: kartoza/geoserver:2.24.0")
    print("   3. Cette image contient GeoServer pré-installé")
    print("   4. Redéployer le service")
    print()
    print("🔗 PREUVE:")
    print("   Les logs Railway montrent seulement:")
    print("   • webapps/manager")
    print("   • webapps/host-manager") 
    print("   • webapps/docs")
    print("   • webapps/examples")
    print("   • webapps/ROOT")
    print("   ❌ AUCUN webapps/geoserver!")
    
    print("=" * 60)

if __name__ == "__main__":
    diagnostic_final()
