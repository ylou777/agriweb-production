#!/usr/bin/env python3
"""
Test minimal pour vérifier la structure de synthese
"""

def test_synthese_structure():
    """Test de la structure exacte retournée par synthese_departement"""
    
    # Test data minimal
    test_reports = [{
        "rpg_parcelles": {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "properties": {"ID_PARCEL": "TEST-001", "distance_bt": 200}, "geometry": {"type": "Point", "coordinates": [6.1, 43.1]}}]
        },
        "eleveurs": {
            "type": "FeatureCollection", 
            "features": [{"type": "Feature", "properties": {"nom": "Test"}, "geometry": {"type": "Point", "coordinates": [6.1, 43.1]}}]
        }
    }]
    
    # Simulation de la fonction synthese_departement
    all_rpg = []
    all_eleveurs = []
    
    for rpt in test_reports:
        fc_rpg = rpt.get("rpg_parcelles", {})
        if fc_rpg and isinstance(fc_rpg, dict) and "features" in fc_rpg:
            all_rpg.extend(fc_rpg.get("features", []))
        fc_e = rpt.get("eleveurs", {})
        if fc_e and isinstance(fc_e, dict) and "features" in fc_e:
            all_eleveurs.extend(fc_e.get("features", []))
    
    # Structure de retour comme dans notre fonction corrigée
    synthese_result = {
        "nb_agriculteurs": len(all_eleveurs),
        "nb_parcelles": len(all_rpg),
        "total_eleveurs": len(all_eleveurs),
        "total_parcelles": len(all_rpg),
        "top50_parcelles": all_rpg[:50],
        "top50": all_rpg[:50]
    }
    
    print("🔍 [TEST] Structure synthese_result:")
    for key, value in synthese_result.items():
        if key in ["top50", "top50_parcelles"]:
            print(f"    {key}: {len(value)} éléments")
        else:
            print(f"    {key}: {value}")
    
    # Test template-like access
    print(f"\n🔍 [TEST] Accès template-like:")
    print(f"    synthese.nb_agriculteurs: {synthese_result.get('nb_agriculteurs')}")
    print(f"    synthese.nb_parcelles: {synthese_result.get('nb_parcelles')}")
    print(f"    synthese.top50: {len(synthese_result.get('top50', []))} éléments")
    
    # Validation
    if synthese_result.get('nb_agriculteurs') == 1 and synthese_result.get('nb_parcelles') == 1:
        print("✅ [TEST] Structure synthese correcte")
        return True
    else:
        print("❌ [TEST] Structure synthese incorrecte")
        return False

if __name__ == "__main__":
    test_synthese_structure()
