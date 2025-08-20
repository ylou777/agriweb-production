#!/usr/bin/env python3
"""
Script de test des endpoints d'authentification Railway
"""
import requests
import json

# Configuration
BASE_URL_RAILWAY = "https://aware-surprise-production.up.railway.app"
BASE_URL_LOCAL = "http://localhost:5000"

def test_auth_endpoints(base_url):
    """Teste les endpoints d'authentification"""
    print(f"\n🧪 Test des endpoints d'authentification sur {base_url}")
    
    # 1. Test endpoint de santé
    try:
        print("\n1. Test /health")
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text[:200]}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # 2. Test endpoint debug auth
    try:
        print("\n2. Test /debug/auth")
        response = requests.get(f"{base_url}/debug/auth", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text[:200]}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # 3. Test endpoint register (sans données valides)
    try:
        print("\n3. Test /register")
        response = requests.post(
            f"{base_url}/register",
            headers={'Content-Type': 'application/json'},
            json={},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # 4. Test endpoint login (sans données valides)
    try:
        print("\n4. Test /login")
        response = requests.post(
            f"{base_url}/login",
            headers={'Content-Type': 'application/json'},
            json={},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # 5. Test endpoint trial (sans données valides)
    try:
        print("\n5. Test /api/trial")
        response = requests.post(
            f"{base_url}/api/trial",
            headers={'Content-Type': 'application/json'},
            json={},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Exception: {e}")

if __name__ == "__main__":
    print("🚀 Test des endpoints d'authentification AgriWeb")
    
    # Test sur Railway
    test_auth_endpoints(BASE_URL_RAILWAY)
    
    # Test en local si disponible
    try:
        response = requests.get(f"{BASE_URL_LOCAL}/health", timeout=2)
        test_auth_endpoints(BASE_URL_LOCAL)
    except:
        print(f"\n⚠️ Serveur local non disponible sur {BASE_URL_LOCAL}")
    
    print("\n✅ Tests terminés")
