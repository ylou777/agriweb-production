#!/usr/bin/env python3
"""
🔐 Test des identifiants GeoServer par défaut
Vérifie si admin/admin bloque le démarrage
"""

import requests
import json
from datetime import datetime

def test_geoserver_auth():
    """Test d'authentification GeoServer avec différents scénarios"""
    
    base_url = "https://geoserver-agriweb-production.up.railway.app/geoserver"
    
    print("🔐 TEST AUTHENTIFICATION GEOSERVER")
    print("=" * 50)
    print(f"📍 URL de base: {base_url}")
    print(f"⏰ Test effectué: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Accès sans authentification
    print("1️⃣ Test accès public (sans auth)")
    try:
        response = requests.get(f"{base_url}/web/", timeout=10)
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📄 Taille réponse: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print("   🎉 Interface accessible !")
        elif response.status_code == 401:
            print("   🔒 Authentification requise")
        elif response.status_code == 404:
            print("   ⚠️ Service non trouvé (démarrage en cours?)")
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erreur connexion: {e}")
    
    print()
    
    # Test 2: Authentification admin/admin
    print("2️⃣ Test avec admin/admin")
    try:
        auth = ('admin', 'admin')
        response = requests.get(f"{base_url}/web/", auth=auth, timeout=10)
        print(f"   ✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   🎉 Connexion admin réussie !")
        elif response.status_code == 401:
            print("   🔒 Identifiants refusés")
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erreur connexion: {e}")
    
    print()
    
    # Test 3: API REST sans auth
    print("3️⃣ Test API REST (sans auth)")
    try:
        response = requests.get(f"{base_url}/rest/about/version", timeout=10)
        print(f"   ✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            version_info = response.json()
            print(f"   📊 Version GeoServer: {version_info}")
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erreur API: {e}")
    
    print()
    
    # Test 4: API REST avec auth
    print("4️⃣ Test API REST (avec admin/admin)")
    try:
        auth = ('admin', 'admin')
        response = requests.get(f"{base_url}/rest/workspaces", auth=auth, timeout=10)
        print(f"   ✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            workspaces = response.json()
            print(f"   📁 Workspaces disponibles: {workspaces}")
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erreur API auth: {e}")
    
    print()
    
    # Test 5: Vérification du service racine
    print("5️⃣ Test service racine")
    try:
        response = requests.get(base_url, timeout=10)
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📄 Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if 'tomcat' in response.text.lower():
            print("   🐱 Tomcat détecté dans la réponse")
        if 'geoserver' in response.text.lower():
            print("   🗺️ GeoServer détecté dans la réponse")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erreur service: {e}")
    
    print()
    print("🔍 ANALYSE DES RÉSULTATS:")
    print("- Si 404 partout: GeoServer en cours de démarrage")
    print("- Si 401 sur /web/: Auth requise (normal)")
    print("- Si 200 avec admin/admin: Identifiants par défaut OK")
    print("- Si refus admin/admin: Identifiants changés")
    print()
    print("💡 RECOMMANDATIONS:")
    print("1. Les identifiants admin/admin ne bloquent PAS le démarrage")
    print("2. Ils sont nécessaires pour l'interface d'administration")
    print("3. En production, il faut les changer pour la sécurité")
    print("4. Le 404 initial est normal pendant le démarrage (5-10min)")

def check_deployment_status():
    """Vérifie l'état du déploiement Railway"""
    print("\n🚀 VÉRIFICATION DÉPLOIEMENT RAILWAY")
    print("=" * 50)
    
    try:
        # Test simple de connectivité
        response = requests.head("https://geoserver-agriweb-production.up.railway.app", timeout=5)
        print(f"📡 Connectivité Railway: ✅ (Status: {response.status_code})")
        
        # Vérification headers
        server = response.headers.get('Server', 'N/A')
        print(f"🖥️ Serveur détecté: {server}")
        
        if 'tomcat' in server.lower():
            print("🎯 Tomcat confirmé - GeoServer peut démarrer")
        
    except Exception as e:
        print(f"❌ Problème connectivité: {e}")

if __name__ == "__main__":
    test_geoserver_auth()
    check_deployment_status()
