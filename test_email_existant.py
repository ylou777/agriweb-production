#!/usr/bin/env python3
"""
Test pour vérifier la gestion des emails existants
"""

import requests
import json

# URL de base
BASE_URL = "http://localhost:5000"

def test_email_existant():
    """Test d'inscription avec un email existant"""
    
    # Données de test
    test_data = {
        "email": "ylaurent.perso@gmail.com",
        "name": "Laurent",
        "company": "lumicasol"
    }
    
    print("🧪 Test d'inscription avec email existant...")
    print(f"📧 Email: {test_data['email']}")
    
    try:
        # Tenter l'inscription
        response = requests.post(
            f"{BASE_URL}/api/trial/register",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            print(f"📋 Réponse JSON:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Vérifier les nouvelles fonctionnalités
            if 'action' in result:
                print(f"✅ Action détectée: {result['action']}")
                if result['action'] == 'login':
                    print("✅ Le système propose correctement la connexion")
                elif result['action'] == 'expired':
                    print("✅ Le système détecte un essai expiré")
            else:
                print("❌ Pas d'action spécifique proposée")
        else:
            print(f"📄 Réponse HTML (longueur: {len(response.text)})")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_connexion_existant():
    """Test de connexion avec un utilisateur existant"""
    
    test_data = {
        "email": "ylaurent.perso@gmail.com"
    }
    
    print("\n🔑 Test de connexion utilisateur existant...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/user/login",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            print(f"📋 Réponse JSON:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"📄 Réponse non-JSON")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    print("🚀 Test de gestion des emails existants - AgriWeb 2.0")
    print("=" * 60)
    
    test_email_existant()
    test_connexion_existant()
    
    print("\n✅ Tests terminés")
