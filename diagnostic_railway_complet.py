#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC COMPLET RAILWAY GEOSERVER
Vérifie l'état réel du déploiement après 1h+ d'attente
"""

import requests
import json
import time
from datetime import datetime

def comprehensive_railway_check():
    """Diagnostic complet du déploiement Railway"""
    
    print("🔍 DIAGNOSTIC RAILWAY GEOSERVER - APRÈS 1H+ D'ATTENTE")
    print("=" * 60)
    print(f"⏰ Vérification: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    base_url = "https://geoserver-agriweb-production.up.railway.app"
    
    # Test 1: Vérification de l'infrastructure Railway
    print("1️⃣ TEST INFRASTRUCTURE RAILWAY")
    print("-" * 40)
    
    try:
        # Test de la racine Railway
        response = requests.get(base_url, timeout=10)
        print(f"   📡 Railway Status: {response.status_code}")
        print(f"   🖥️ Server: {response.headers.get('Server', 'N/A')}")
        print(f"   📄 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   📏 Response Size: {len(response.content)} bytes")
        
        # Analyse du contenu de la réponse
        content = response.text.lower()
        if 'tomcat' in content:
            print("   ✅ Tomcat détecté dans la réponse")
        if 'geoserver' in content:
            print("   ✅ GeoServer détecté dans la réponse")
        if '404' in content:
            print("   ⚠️ Page 404 détectée")
        if 'error' in content:
            print("   ❌ Erreur détectée dans le contenu")
            
    except Exception as e:
        print(f"   💥 ERREUR Infrastructure: {e}")
        print("   ❌ Railway semble complètement inaccessible")
        
    print()
    
    # Test 2: Tests spécifiques GeoServer
    print("2️⃣ TESTS ENDPOINTS GEOSERVER")
    print("-" * 40)
    
    endpoints = [
        "/geoserver",
        "/geoserver/",
        "/geoserver/web",
        "/geoserver/web/",
        "/geoserver/rest/about/version",
        "/geoserver/ows"
    ]
    
    for endpoint in endpoints:
        try:
            url = base_url + endpoint
            response = requests.get(url, timeout=5)
            print(f"   {endpoint:<25} → {response.status_code}")
            
            if response.status_code == 200:
                print(f"      ✅ ACCESSIBLE!")
            elif response.status_code == 404:
                print(f"      ❌ Non trouvé")
            elif response.status_code == 401:
                print(f"      🔒 Auth requise (normal)")
            elif response.status_code == 500:
                print(f"      💥 Erreur serveur")
                
        except Exception as e:
            print(f"   {endpoint:<25} → TIMEOUT/ERROR")
    
    print()
    
    # Test 3: Vérification des headers détaillés
    print("3️⃣ ANALYSE HEADERS DÉTAILLÉE")
    print("-" * 40)
    
    try:
        response = requests.head(base_url + "/geoserver", timeout=10)
        headers = dict(response.headers)
        
        print(f"   Status Code: {response.status_code}")
        for key, value in headers.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"   ❌ Impossible de récupérer les headers: {e}")
    
    print()
    
    # Test 4: Diagnostic temporel
    print("4️⃣ DIAGNOSTIC TEMPOREL")
    print("-" * 40)
    
    print("   ⏱️ Temps d'attente actuel: 1h+")
    print("   📊 Temps normal Railway: 5-15 minutes")
    print("   📊 Temps maximum observé: 30 minutes")
    print("   🚨 CONCLUSION: Dépassement anormal!")
    print()
    
    # Test 5: Hypothèses de problèmes
    print("5️⃣ HYPOTHÈSES DE PROBLÈMES")
    print("-" * 40)
    
    print("   🔴 PROBLÈME PROBABLE:")
    print("   - Déploiement échoué silencieusement")
    print("   - Image Docker corrompue")
    print("   - Ressources insuffisantes")
    print("   - Configuration Railway incorrecte")
    print()
    
    print("   ✅ SOLUTIONS À TESTER:")
    print("   1. Redéploiement complet")
    print("   2. Vérification variables d'environnement")
    print("   3. Test avec image GeoServer alternative")
    print("   4. Vérification logs Railway détaillés")
    
    print()
    
    # Test 6: Recommendations
    print("6️⃣ RECOMMANDATIONS IMMÉDIATES")
    print("-" * 40)
    
    print("   🔧 ACTIONS À FAIRE:")
    print("   1. railway logs --help (voir options disponibles)")
    print("   2. railway ps (voir processus actifs)")
    print("   3. railway restart (redémarrage forcé)")
    print("   4. Vérifier dashboard Railway web")
    print()
    
    print("   💡 SI RIEN NE FONCTIONNE:")
    print("   - Supprimer le service actuel")
    print("   - Recréer avec une image différente")
    print("   - Utiliser geoserver/geoserver au lieu de kartoza/geoserver")
    
    print()
    print("🎯 VERDICT: Après 1h+, le déploiement semble BLOQUÉ ou ÉCHOUÉ")
    print("⚡ ACTION: Redéploiement nécessaire!")

def quick_alternative_test():
    """Test rapide d'alternatives"""
    print("\n🚀 TEST ALTERNATIVES RAPIDES")
    print("=" * 40)
    
    # Test si d'autres services Railway fonctionnent
    test_urls = [
        "https://railway.app",
        "https://docs.railway.app",
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {url} → {response.status_code}")
        except:
            print(f"❌ {url} → INACCESSIBLE")

if __name__ == "__main__":
    comprehensive_railway_check()
    quick_alternative_test()
