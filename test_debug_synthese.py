#!/usr/bin/env python3
"""
Test direct de la fonction synthese_departement 
"""

def test_synthese_function():
    """Test de la fonction synthese_departement corrigée"""
    
    # Importer la fonction depuis le module principal
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    
    try:
        from agriweb_source import synthese_departement
        print("✅ [TEST] Fonction synthese_departement importée avec succès")
        
        # Données de test identiques à celles utilisées dans l'endpoint
        test_reports = [
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
                        },
                        {
                            "type": "Feature",
                            "properties": {
                                "ID_PARCEL": "TEST-002",
                                "code_com": "83001",
                                "section": "CD",
                                "numero": "456",
                                "distance_hta": 150,
                                "surface": "3.0",
                                "nom_com": "Test Commune A"
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
        
        print(f"🧪 [TEST] Appel synthese_departement avec {len(test_reports)} rapport(s)")
        
        # Appel de la fonction
        synthese_result = synthese_departement(test_reports)
        
        print(f"🧪 [TEST] Résultat obtenu:")
        print(f"    Type: {type(synthese_result)}")
        print(f"    Clés: {list(synthese_result.keys()) if isinstance(synthese_result, dict) else 'N/A'}")
        
        if isinstance(synthese_result, dict):
            for key, value in synthese_result.items():
                if key == "top50" or key == "top50_parcelles":
                    print(f"    {key}: {len(value) if hasattr(value, '__len__') else value} éléments")
                else:
                    print(f"    {key}: {value}")
        
        # Vérifications
        if isinstance(synthese_result, dict):
            # Test des champs requis
            required_fields = ["nb_agriculteurs", "nb_parcelles", "top50"]
            missing_fields = [field for field in required_fields if field not in synthese_result]
            
            if missing_fields:
                print(f"❌ [TEST] Champs manquants: {missing_fields}")
            else:
                print("✅ [TEST] Tous les champs requis sont présents")
                
            # Test des valeurs
            nb_agri = synthese_result.get("nb_agriculteurs")
            nb_parc = synthese_result.get("nb_parcelles")
            
            if nb_agri == 2 and nb_parc == 2:
                print("✅ [TEST] Valeurs correctes: 2 agriculteurs, 2 parcelles")
            else:
                print(f"❌ [TEST] Valeurs incorrectes: {nb_agri} agriculteurs, {nb_parc} parcelles")
                
        else:
            print(f"❌ [TEST] Type de retour incorrect: {type(synthese_result)}")
            
    except ImportError as e:
        print(f"❌ [TEST] Erreur d'import: {e}")
    except Exception as e:
        print(f"❌ [TEST] Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_synthese_function()
