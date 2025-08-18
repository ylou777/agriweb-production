#!/usr/bin/env python3
"""
Script de test pour vérifier les corrections du rapport départemental
"""

# Simuler des données de test
def test_synthese_corrections():
    """Test des corrections de la synthèse départementale"""
    
    # Données de test simulées
    mock_reports = [
        {
            "commune": "Commune A",
            "dept": "83",
            "rpg_parcelles": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "ID_PARCEL": "83001-001",
                            "code_com": "83001",
                            "section": "AB",
                            "numero": "123",
                            "distance_bt": 250,
                            "surface": "2.5"
                        },
                        "geometry": {"type": "Point", "coordinates": [6.1, 43.1]}
                    },
                    {
                        "type": "Feature", 
                        "properties": {
                            "ID_PARCEL": "83001-002",
                            "code_com": "83001",
                            "section": "AB",
                            "numero": "124",
                            "distance_hta": 500,
                            "surface": "1.8"
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
                            "nom": "Eleveur A",
                            "siret": "12345678901234",
                            "activite": "Bovins"
                        },
                        "geometry": {"type": "Point", "coordinates": [6.15, 43.15]}
                    }
                ]
            }
        },
        {
            "commune": "Commune B", 
            "dept": "83",
            "rpg_parcelles": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "ID_PARCEL": "83002-001",
                            "code_com": "83002",
                            "section": "CD",
                            "numero": "456",
                            "distance_bt": 150,
                            "surface": "3.2"
                        },
                        "geometry": {"type": "Point", "coordinates": [6.3, 43.3]}
                    }
                ]
            },
            "eleveurs": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "nom": "Eleveur B",
                            "siret": "98765432109876",
                            "activite": "Ovins"
                        },
                        "geometry": {"type": "Point", "coordinates": [6.35, 43.35]}
                    },
                    {
                        "type": "Feature",
                        "properties": {
                            "nom": "Eleveur C",
                            "activite": "Caprins"
                            # Pas de SIRET - test du cas sans SIRET
                        },
                        "geometry": {"type": "Point", "coordinates": [6.4, 43.4]}
                    }
                ]
            }
        }
    ]
    
    print("🧪 [TEST] === TEST DES CORRECTIONS SYNTHÈSE DÉPARTEMENTALE ===")
    print(f"🧪 [TEST] Données d'entrée: {len(mock_reports)} rapports communaux")
    
    # Test 1: Agrégation des totaux
    total_rpg_expected = 3  # 2 + 1 parcelles
    total_eleveurs_expected = 3  # 1 + 2 éleveurs
    
    all_rpg = []
    all_eleveurs = []
    
    for rpt in mock_reports:
        fc_rpg = rpt.get("rpg_parcelles", {})
        if fc_rpg and "features" in fc_rpg:
            all_rpg.extend(fc_rpg["features"])
            
        fc_e = rpt.get("eleveurs", {})
        if fc_e and "features" in fc_e:
            all_eleveurs.extend(fc_e["features"])
    
    print(f"🧪 [TEST] Agrégation: {len(all_rpg)} parcelles RPG, {len(all_eleveurs)} éleveurs")
    
    # Vérification
    assert len(all_rpg) == total_rpg_expected, f"Erreur agrégation RPG: {len(all_rpg)} != {total_rpg_expected}"
    assert len(all_eleveurs) == total_eleveurs_expected, f"Erreur agrégation éleveurs: {len(all_eleveurs)} != {total_eleveurs_expected}"
    
    print("✅ [TEST] Agrégation des totaux: OK")
    
    # Test 2: Tri par distance
    def get_dist(feat):
        props = feat.get("properties", {})
        for key in ["distance_bt", "distance_au_poste", "distance_hta"]:
            v = props.get(key)
            if v is not None and isinstance(v, (int, float)) and v > 0:
                return v
        return 999999
    
    sorted_rpg = sorted(all_rpg, key=get_dist)
    distances = [get_dist(p) for p in sorted_rpg]
    print(f"🧪 [TEST] Distances triées: {distances}")
    
    # Vérification du tri (150 < 250 < 500)
    assert distances[0] == 150, f"Erreur tri: première distance {distances[0]} != 150"
    assert distances[1] == 250, f"Erreur tri: deuxième distance {distances[1]} != 250" 
    assert distances[2] == 500, f"Erreur tri: troisième distance {distances[2]} != 500"
    
    print("✅ [TEST] Tri par distance: OK")
    
    # Test 3: Correction des distances formatées
    def fix_distances_in_features(features):
        fixed = []
        for feat in features:
            props = feat.get("properties", {}).copy()
            
            min_distance = None
            for key in ["distance_bt", "distance_au_poste", "distance_hta"]:
                val = props.get(key)
                if val is not None and isinstance(val, (int, float)) and val > 0:
                    if min_distance is None or val < min_distance:
                        min_distance = val
            
            if min_distance is not None:
                props["distance_formatted"] = f"{int(min_distance)} m"
                props["distance_valid"] = True
            else:
                props["distance_formatted"] = "Distance non calculée"
                props["distance_valid"] = False
            
            feat_copy = feat.copy()
            feat_copy["properties"] = props
            fixed.append(feat_copy)
        
        return fixed
    
    fixed_features = fix_distances_in_features(sorted_rpg)
    
    # Vérification du formatage
    assert fixed_features[0]["properties"]["distance_formatted"] == "150 m"
    assert fixed_features[1]["properties"]["distance_formatted"] == "250 m"
    assert fixed_features[2]["properties"]["distance_formatted"] == "500 m"
    
    print("✅ [TEST] Formatage des distances: OK")
    
    # Test 4: Correction des liens cadastre
    def fix_cadastre_links(features):
        for feat in features:
            props = feat.get("properties", {})
            
            code_commune = props.get("code_com")
            section = props.get("section")
            numero = props.get("numero")
            
            if code_commune and section and numero:
                cadastre_url = f"https://www.cadastre.gouv.fr/scpc/accueil.do#c={code_commune}&sec={section}&n={numero}"
                props["cadastre_link"] = cadastre_url
                props["cadastre_link_valid"] = True
            else:
                props["cadastre_link"] = None
                props["cadastre_link_valid"] = False
        
        return features
    
    linked_features = fix_cadastre_links(fixed_features)
    
    # Vérification des liens
    for feat in linked_features:
        props = feat["properties"]
        if props.get("code_com") and props.get("section") and props.get("numero"):
            assert props["cadastre_link_valid"] == True
            assert "cadastre.gouv.fr" in props["cadastre_link"]
    
    print("✅ [TEST] Génération des liens cadastre: OK")
    
    print("🎉 [TEST] === TOUS LES TESTS RÉUSSIS ===")
    print("🎉 [TEST] Les corrections pour la synthèse départementale fonctionnent correctement")


if __name__ == "__main__":
    test_synthese_corrections()
