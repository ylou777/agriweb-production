#!/usr/bin/env python3
"""
Debug de l'erreur 500 lors de la recherche toiture
"""

import requests
import json
import time

def test_debug_toiture():
    """Test avec capture d'erreur détaillée"""
    print("🐛 [DEBUG] Test recherche toiture avec capture d'erreur")
    
    # Attendre que le serveur démarre
    print("⏳ Attente démarrage serveur...")
    time.sleep(3)
    
    # Test simple d'abord
    try:
        print("🔍 [TEST] Vérification état serveur...")
        response = requests.get("http://localhost:5000/", timeout=10)
        print(f"📡 [SERVEUR] Status: {response.status_code}")
    except Exception as e:
        print(f"❌ [SERVEUR] Erreur connexion: {e}")
        return False
    
    # Test recherche toiture avec paramètres minimaux
    test_data = {
        "commune": "Boulbon",
        "filter_toitures": "true",
        "toitures_min_surface": "1000",  # Très restrictif
        "toitures_max_distance_bt": "100"
    }
    
    try:
        print(f"🧪 [TEST] Recherche toiture: {test_data}")
        
        response = requests.post(
            "http://localhost:5000/search_by_commune", 
            data=test_data, 
            timeout=60
        )
        
        print(f"📡 [RÉPONSE] Status Code: {response.status_code}")
        print(f"📡 [RÉPONSE] Headers: {dict(response.headers)}")
        
        if response.status_code == 500:
            print("❌ [ERREUR 500] Détails:")
            print(f"    Content-Type: {response.headers.get('Content-Type')}")
            print(f"    Contenu: {response.text[:1000]}")
            
            # Essayer de parser comme JSON pour voir s'il y a des détails
            try:
                if 'application/json' in response.headers.get('Content-Type', ''):
                    error_data = response.json()
                    print(f"    JSON Error: {error_data}")
            except:
                pass
                
        elif response.status_code == 200:
            print("✅ [SUCCÈS] Recherche réussie")
            data = response.json()
            toitures = data.get("toitures", {}).get("features", [])
            print(f"🏠 [RÉSULTAT] {len(toitures)} toitures trouvées")
            
        else:
            print(f"⚠️ [AUTRE ERREUR] Status: {response.status_code}")
            print(f"    Contenu: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("⏱️ [TIMEOUT] Requête trop longue")
    except Exception as e:
        print(f"❌ [EXCEPTION] {e}")

def test_endpoints_basiques():
    """Test des endpoints de base pour identifier le problème"""
    print("\n🧪 [DEBUG] Test endpoints basiques")
    
    endpoints = [
        "/",
        "/generated_map"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:5000{endpoint}", timeout=10)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"    {status} {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"    ❌ {endpoint}: Exception - {e}")

if __name__ == "__main__":
    test_endpoints_basiques()
    test_debug_toiture()
