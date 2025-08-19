#!/usr/bin/env python3
"""
Test direct de l'API du serveur principal
"""
import requests
import json

def test_api_principale():
    """Test de l'API principale sur port 5000"""
    
    url = "http://localhost:5000/api/trial/register"
    data = {
        "email": "ylaurent.perso@gmail.com",
        "name": "Laurent",
        "company": "lumicasol"
    }
    
    print("🧪 Test API Serveur Principal (port 5000)")
    print(f"📍 URL: {url}")
    print(f"📧 Email: {data['email']}")
    print("=" * 50)
    
    try:
        response = requests.post(
            url,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            print(f"📄 Réponse JSON:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Vérifier la nouvelle logique
            if 'action' in result:
                print(f"✅ NOUVELLE LOGIQUE DÉTECTÉE!")
                print(f"🎯 Action: {result['action']}")
                if result['action'] == 'login':
                    print("✅ Bouton de connexion devrait apparaître")
            else:
                print("❌ ANCIENNE LOGIQUE - Pas d'action spécifique")
        else:
            print(f"❌ Réponse non-JSON: {response.text[:200]}...")
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur principal")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_api_principale()
