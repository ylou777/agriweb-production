#!/usr/bin/env python3
"""
Test direct de la fonction synthese_departement
"""

# Import minimal pour tester la fonction
import sys
sys.path.append('.')

def test_synthese_function():
    """Test de la fonction synthese_departement directement"""
    
    # Simuler les données de test
    mock_reports = [
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
    
    print("🧪 [TEST] === TEST DIRECT FONCTION SYNTHESE ===")
    
    try:
        # Import de la fonction
        from agriweb_source import synthese_departement
        print("✅ [TEST] Import synthese_departement: OK")
        
        # Test de la fonction
        result = synthese_departement(mock_reports)
        print(f"✅ [TEST] Exécution synthese_departement: OK")
        print(f"📊 [TEST] Résultat: {result}")
        
        # Vérifications
        expected_parcelles = 2
        expected_eleveurs = 2
        
        assert result["nb_parcelles"] == expected_parcelles, f"Erreur parcelles: {result['nb_parcelles']} != {expected_parcelles}"
        assert result["nb_agriculteurs"] == expected_eleveurs, f"Erreur éleveurs: {result['nb_agriculteurs']} != {expected_eleveurs}"
        assert len(result["top50"]) == 2, f"Erreur top50: {len(result['top50'])} != 2"
        
        print("✅ [TEST] Toutes les vérifications passent")
        print("✅ [TEST] La fonction synthese_departement fonctionne correctement")
        
        return True
        
    except Exception as e:
        print(f"❌ [TEST] Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_synthese_function()
    if success:
        print("🎉 [TEST] Test réussi ! La fonction synthese_departement est opérationnelle.")
    else:
        print("💥 [TEST] Test échoué ! Il y a un problème avec la fonction.")
