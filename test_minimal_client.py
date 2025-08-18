#!/usr/bin/env python3
"""
Test du serveur minimal
"""
import requests
import json

def test_minimal_server():
    # Données de test
    test_data = {
        "data": [
            {
                "commune": "Test Commune A",
                "dept": "83",
                "rpg_parcelles": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {
                                "ID_PARCEL": "TEST-001",
                                "code_com": "83001",
                                "section": "AB",
                                "numero": "123",
                                "distance_bt": 200,
                                "surface": "2.5"
                            },
                            "geometry": {"type": "Point", "coordinates": [6.1, 43.1]}
                        },
                        {
                            "type": "Feature",
                            "properties": {
                                "ID_PARCEL": "TEST-002",
                                "code_com": "83001",
                                "section": "CD", 
                                "numero": "456",
                                "distance_hta": 150,
                                "surface": "3.0"
                            },
                            "geometry": {"type": "Point", "coordinates": [6.2, 43.2]}
                        }
                    ]
                },
                "eleveurs": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {
                                "nom": "Test Eleveur A",
                                "siret": "12345678901234",
                                "activite": "Bovins"
                            },
                            "geometry": {"type": "Point", "coordinates": [6.1, 43.1]}
                        },
                        {
                            "type": "Feature",
                            "properties": {
                                "nom": "Test Eleveur B",
                                "activite": "Ovins"
                            },
                            "geometry": {"type": "Point", "coordinates": [6.15, 43.15]}
                        }
                    ]
                }
            }
        ]
    }
    
    try:
        print("🧪 [TEST] Test du serveur minimal...")
        
        # Test de la route de base
        response = requests.get("http://localhost:5001/test", timeout=5)
        print(f"📋 [TEST] Route /test: {response.status_code} - {response.text}")
        
        # Test de l'endpoint rapport_departement
        response = requests.post(
            "http://localhost:5001/rapport_departement",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📋 [TEST] POST /rapport_departement: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ [TEST] Réponse JSON: {json.dumps(result, indent=2)}")
            
            # Vérifications
            if result.get("status") == "success":
                synthese = result.get("synthese", {})
                print(f"✅ [TEST] nb_agriculteurs: {synthese.get('nb_agriculteurs')}")
                print(f"✅ [TEST] nb_parcelles: {synthese.get('nb_parcelles')}")
                print(f"✅ [TEST] Toutes les corrections fonctionnent !")
            else:
                print("❌ [TEST] Status n'est pas 'success'")
        else:
            print(f"❌ [TEST] Erreur: {response.status_code}")
            print(f"❌ [TEST] Réponse: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ [TEST] Impossible de se connecter au serveur sur port 5001")
    except Exception as e:
        print(f"❌ [TEST] Erreur: {e}")

if __name__ == "__main__":
    test_minimal_server()
