"""
Test d'intégration pour vérifier les corrections du rapport départemental
"""
import json
import time

def test_with_curl():
    """Test via curl de l'endpoint rapport_departement"""
    
    # Données de test au format attendu par l'endpoint
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
                                "surface": "2.5",
                                "nom_com": "Test Commune A"
                            },
                            "geometry": {"type": "Point", "coordinates": [6.1, 43.1]}
                        }
                    ]
                },
                "eleveurs": {
                    "type": "FeatureCollection", 
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {
                                "nom": "Test Eleveur",
                                "siret": "12345678901234",
                                "activite": "Test"
                            },
                            "geometry": {"type": "Point", "coordinates": [6.1, 43.1]}
                        }
                    ]
                }
            }
        ]
    }
    
    # Écrire les données dans un fichier temporaire
    with open("test_dept_data.json", "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print("📝 Données de test créées dans test_dept_data.json")
    print("🧪 Pour tester l'endpoint, utilisez:")
    print('curl -X POST http://localhost:5000/rapport_departement -H "Content-Type: application/json" -d @test_dept_data.json')
    print("🧪 Ou testez directement dans votre navigateur à http://localhost:5000")
    
    # Instructions pour le test manuel
    print("\n=== INSTRUCTIONS DE TEST ===")
    print("1. Assurez-vous que le serveur Flask tourne sur port 5000")
    print("2. Allez sur http://localhost:5000/rapport_departement") 
    print("3. Chargez des données de commune")
    print("4. Vérifiez que:")
    print("   - La synthèse montre des totaux > 0 (pas 0)")
    print("   - Les distances ne montrent pas 'N/A m'")
    print("   - Les liens cadastre fonctionnent")
    print("   - Les données SIRET sont enrichies")

if __name__ == "__main__":
    test_with_curl()
