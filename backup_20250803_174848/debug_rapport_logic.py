#!/usr/bin/env python3
# Debug de la logique exacte du rapport pour les API Nature

import sys
import os
sys.path.append(os.path.dirname(__file__))

from agriweb_source import get_all_api_nature_data

def debug_rapport_logic():
    """Debug de la logique exacte utilisée dans rapport_point"""
    
    print("=== DEBUG LOGIQUE RAPPORT API NATURE ===")
    
    # Coordonnées d'Hyères
    lat = 43.006497
    lon = 6.396759
    
    print(f"Coordonnées: {lat}, {lon}")
    
    # === Initialisation api_details comme dans le rapport ===
    api_details = {
        "nature": {"success": False, "data": None, "details": {}, "count": 0, "error": None}
    }
    
    print(f"État initial api_details['nature']: {api_details['nature']}")
    
    # === Logique exacte du rapport ===
    try:
        print("\n--- Appel get_all_api_nature_data ---")
        geom = {"type": "Point", "coordinates": [lon, lat]}
        nature_data = get_all_api_nature_data(geom)
        
        print(f"nature_data type: {type(nature_data)}")
        print(f"nature_data keys: {list(nature_data.keys()) if nature_data else 'None'}")
        
        # Condition exacte du rapport
        condition = nature_data and "features" in nature_data and nature_data["features"]
        print(f"Condition rapport (nature_data and 'features' in nature_data and nature_data['features']): {condition}")
        
        if condition:
            print("✅ Condition vraie - API Nature devrait être SUCCESS")
            api_details["nature"]["success"] = True
            api_details["nature"]["data"] = nature_data
            api_details["nature"]["count"] = len(nature_data["features"])
            print(f"✅ api_details['nature']['count']: {api_details['nature']['count']}")
            print(f"✅ api_details['nature']['success']: {api_details['nature']['success']}")
        else:
            print("❌ Condition fausse - API Nature sera AUCUNE")
            api_details["nature"]["success"] = False
            api_details["nature"]["data"] = {"type": "FeatureCollection", "features": []}
            api_details["nature"]["count"] = 0
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        api_details["nature"]["success"] = False
        api_details["nature"]["error"] = str(e)
    
    print(f"\nÉtat final api_details['nature']: {api_details['nature']}")
    
    # === Test condition template ===
    print("\n--- Test condition template ---")
    report_api_details_nature = api_details["nature"]
    
    template_condition = (
        report_api_details_nature and 
        report_api_details_nature.get("data") and 
        report_api_details_nature.get("count", 0) > 0
    )
    
    print(f"Condition template: {template_condition}")
    
    if template_condition:
        print("✅ Template devrait afficher les zones naturelles")
        print(f"✅ Nombre à afficher: {report_api_details_nature.get('count')}")
        
        # Afficher quelques zones pour vérification
        data = report_api_details_nature.get("data", {})
        features = data.get("features", [])
        print(f"✅ Features disponibles: {len(features)}")
        
        for i, feature in enumerate(features[:3]):
            props = feature.get("properties", {})
            nom = props.get("NOM", "Espace naturel")
            type_protection = props.get("TYPE_PROTECTION", "Non défini")
            print(f"  Zone {i+1}: {nom} ({type_protection})")
    else:
        print("❌ Template affichera 'Aucun espace naturel protégé'")
        
        # Debug pourquoi la condition échoue
        print("Debug condition template:")
        print(f"  report_api_details_nature: {bool(report_api_details_nature)}")
        print(f"  .get('data'): {bool(report_api_details_nature.get('data') if report_api_details_nature else False)}")
        print(f"  .get('count', 0) > 0: {(report_api_details_nature.get('count', 0) > 0) if report_api_details_nature else False}")

if __name__ == "__main__":
    debug_rapport_logic()
