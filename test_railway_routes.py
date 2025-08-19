#!/usr/bin/env python3
"""
Test des routes principales de l'application AgriWeb Railway
"""
import requests
import time

# URL de base - local et Railway
BASE_URLS = [
    "http://127.0.0.1:5000",
    "https://agriweb-production-production.up.railway.app"
]

ROUTES_TO_TEST = [
    "/",
    "/toitures", 
    "/rapport_departement",
    "/carte_risques"
]

def test_route(base_url, route):
    """Test une route spécifique"""
    try:
        url = f"{base_url}{route}"
        print(f"🔍 Test de {url}")
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"✅ {route} : OK (Status 200)")
            return True
        else:
            print(f"❌ {route} : Erreur {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"⚠️ {route} : Connexion impossible - {e}")
        return False

def test_all_routes():
    """Test toutes les routes sur tous les serveurs"""
    print("🌾 Test des routes AgriWeb\n")
    
    for base_url in BASE_URLS:
        print(f"🚀 Test du serveur : {base_url}")
        print("=" * 50)
        
        success_count = 0
        total_routes = len(ROUTES_TO_TEST)
        
        for route in ROUTES_TO_TEST:
            if test_route(base_url, route):
                success_count += 1
            time.sleep(0.5)  # Petite pause entre les tests
        
        print(f"\n📊 Résultat : {success_count}/{total_routes} routes fonctionnelles")
        print("-" * 50)
        print()

if __name__ == "__main__":
    test_all_routes()
