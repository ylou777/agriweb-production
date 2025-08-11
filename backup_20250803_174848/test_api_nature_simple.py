#!/usr/bin/env python3
# Test simple et direct de la fonction get_all_api_nature_data

import sys
import os
sys.path.append(os.path.dirname(__file__))

from agriweb_source import get_all_api_nature_data

def test_api_nature():
    print("=== TEST API NATURE DIRECT ===")
    
    # Coordonnées d'Hyères
    lat, lon = 43.006497, 6.396759
    geom = {"type": "Point", "coordinates": [lon, lat]}
    
    print(f"Coordonnées: {lat}, {lon}")
    print(f"Géométrie: {geom}")
    
    try:
        print("\nAppel de get_all_api_nature_data...")
        nature_data = get_all_api_nature_data(geom)
        
        print(f"Résultat type: {type(nature_data)}")
        
        if nature_data:
            print(f"Clés disponibles: {list(nature_data.keys())}")
            
            if "features" in nature_data:
                feature_count = len(nature_data["features"])
                print(f"Nombre de features: {feature_count}")
                
                if feature_count > 0:
                    print("\nDétail des zones trouvées:")
                    for i, feature in enumerate(nature_data["features"]):
                        props = feature.get("properties", {})
                        nom = props.get("NOM") or props.get("nom") or "Sans nom"
                        type_protection = props.get("TYPE_PROTECTION", "Non défini")
                        print(f"  {i+1}. {nom} ({type_protection})")
                else:
                    print("Aucune feature trouvée")
            else:
                print("Pas de clé 'features' dans le résultat")
        else:
            print("nature_data est None ou vide")
            
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_nature()
