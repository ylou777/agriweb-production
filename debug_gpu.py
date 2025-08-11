#!/usr/bin/env python3
"""
Script de debug pour analyser les données GPU Zone Urba
"""

import json
from agriweb_source import get_all_gpu_data

def debug_gpu_data():
    """Test de récupération des données GPU pour un point spécifique"""
    # Coordonnées du test (Nantes)
    lat = 47.218637
    lon = -1.554136
    
    print(f"🔍 Test GPU pour le point : {lat}, {lon}")
    print("=" * 60)
    
    try:
        # Récupération des données
        geom = {"type": "Point", "coordinates": [lon, lat]}
        gpu_data = get_all_gpu_data(geom)
        
        if gpu_data:
            print(f"✅ Données GPU récupérées : {len(gpu_data)} couches")
            
            # Analyse de Zone Urba spécifiquement
            if 'Zone Urba' in gpu_data:
                zone_data = gpu_data['Zone Urba']
                print(f"\n📋 Zone Urba trouvée :")
                print(f"   - Nombre de features : {len(zone_data.get('features', []))}")
                
                for i, feature in enumerate(zone_data.get('features', [])[:3]):
                    props = feature.get('properties', {})
                    print(f"\n   Feature {i+1}:")
                    for key, value in props.items():
                        if value and str(value).strip():
                            print(f"     {key}: {value}")
            else:
                print("❌ Aucune Zone Urba trouvée")
                print("Couches disponibles :", list(gpu_data.keys()))
            
            # Analyse générale des couches
            print(f"\n📊 Résumé des couches :")
            total_features = 0
            for layer_name, layer_data in gpu_data.items():
                if isinstance(layer_data, dict) and 'features' in layer_data:
                    count = len(layer_data['features'])
                    total_features += count
                    print(f"   - {layer_name}: {count} features")
            
            print(f"\nTotal features : {total_features}")
            
        else:
            print("❌ Aucune donnée GPU récupérée")
            
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_gpu_data()
