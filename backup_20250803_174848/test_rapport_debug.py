#!/usr/bin/env python3
# Test de la génération du rapport avec debug des API Nature

import sys
import os
sys.path.append(os.path.dirname(__file__))

import requests
from agriweb_source import *

def test_rapport_api_nature():
    """Test de la logique exacte utilisée dans rapport_point"""
    
    lat_float = 43.006497
    lon_float = 6.396759
    
    print(f"=== TEST RAPPORT API NATURE ===")
    print(f"lat_float: {lat_float}")
    print(f"lon_float: {lon_float}")
    
    # === Test 1: Variables utilisées dans le rapport ===
    lat = lat_float  # Variable utilisée dans le rapport
    lon = lon_float  # Variable utilisée dans le rapport
    
    print(f"lat (dans rapport): {lat}")
    print(f"lon (dans rapport): {lon}")
    
    # === Test 2: Géométrie ===
    geom = {"type": "Point", "coordinates": [lon, lat]}
    print(f"Géométrie: {geom}")
    
    # === Test 3: Appel direct de la fonction ===
    try:
        print("\n--- Appel get_all_api_nature_data ---")
        nature_data = get_all_api_nature_data(geom)
        print(f"Type résultat: {type(nature_data)}")
        
        if nature_data:
            print(f"Clés: {list(nature_data.keys())}")
            if "features" in nature_data:
                features = nature_data["features"]
                print(f"Nombre de features: {len(features)}")
                
                for i, feature in enumerate(features):
                    props = feature.get("properties", {})
                    nom = props.get("NOM") or props.get("nom") or "Sans nom"
                    type_prot = props.get("TYPE_PROTECTION", "Non défini")
                    print(f"  Feature {i+1}: {nom} ({type_prot})")
        else:
            print("nature_data est None")
            
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    # === Test 4: Logique de la condition exacte du rapport ===
    print(f"\n--- Test conditions rapport ---")
    print(f"nature_data is not None: {nature_data is not None}")
    print(f"'features' in nature_data: {'features' in nature_data if nature_data else False}")
    print(f"nature_data['features'] truthy: {bool(nature_data['features']) if nature_data and 'features' in nature_data else False}")
    
    condition = nature_data and "features" in nature_data and nature_data["features"]
    print(f"Condition complète: {condition}")
    
    if condition:
        print("✅ API Nature devrait être SUCCESS")
        count = len(nature_data["features"])
        print(f"✅ Nombre de zones: {count}")
    else:
        print("❌ API Nature sera marquée comme AUCUNE")

if __name__ == "__main__":
    test_rapport_api_nature()
