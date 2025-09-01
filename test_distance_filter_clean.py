#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_distance_filter():
    """Test du filtrage par distance"""
    
    print("=== TEST DU FILTRAGE PAR DISTANCE AUX POSTES ===")
    
    # URL de l'API
    url = 'http://localhost:5000/search_by_commune'
    
    # Test avec filtrage par distance activé
    print("\n1. TEST AVEC FILTRAGE PAR DISTANCE ACTIVÉ")
    params = {
        'commune': 'Saint Sulpice les Champs',
        'filter_rpg': 'true',
        'rpg_min_area': '2',
        'rpg_max_area': '50',
        'filter_by_distance': 'true',  # IMPORTANT: activer le filtrage
        'max_distance_bt': '150',      # 150 mètres
        'max_distance_hta': '1000',    # 1000 mètres  
        'poste_type_filter': 'ALL'     # Tous les postes
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Clés dans la réponse: {list(result.keys())}")
            
            if 'rpg_parcelles' in result:
                rpg = result['rpg_parcelles']
                if isinstance(rpg, dict) and 'features' in rpg:
                    print(f"✅ Nombre de parcelles RPG trouvées: {len(rpg['features'])}")
                    
                    # Analyser les distances
                    if len(rpg['features']) > 0:
                        distances_bt = []
                        distances_hta = []
                        parcelles_avec_distance = 0
                        parcelles_sans_distance = 0
                        
                        for feature in rpg['features']:
                            props = feature.get('properties', {})
                            d_bt = props.get('min_distance_bt_m')
                            d_hta = props.get('min_distance_hta_m')
                            
                            if d_bt is not None or d_hta is not None:
                                parcelles_avec_distance += 1
                                if d_bt is not None:
                                    distances_bt.append(d_bt)
                                if d_hta is not None:
                                    distances_hta.append(d_hta)
                            else:
                                parcelles_sans_distance += 1
                        
                        print(f"📈 Parcelles avec distance: {parcelles_avec_distance}")
                        print(f"📉 Parcelles sans distance: {parcelles_sans_distance}")
                        
                        if distances_bt:
                            print(f"📏 Distances BT : min={min(distances_bt):.1f}m, max={max(distances_bt):.1f}m, moyenne={sum(distances_bt)/len(distances_bt):.1f}m")
                            # Vérifier les parcelles qui dépassent les limites
                            depassements_bt = [d for d in distances_bt if d > 150]
                            if depassements_bt:
                                print(f"⚠️ {len(depassements_bt)} parcelles dépassent la limite BT de 150m: {depassements_bt[:5]}...")
                            else:
                                print(f"✅ Toutes les parcelles respectent la limite BT de 150m")
                        else:
                            print("❌ Aucune distance BT trouvée")
                            
                        if distances_hta:
                            print(f"📏 Distances HTA: min={min(distances_hta):.1f}m, max={max(distances_hta):.1f}m, moyenne={sum(distances_hta)/len(distances_hta):.1f}m")
                            depassements_hta = [d for d in distances_hta if d > 1000]
                            if depassements_hta:
                                print(f"⚠️ {len(depassements_hta)} parcelles dépassent la limite HTA de 1000m: {depassements_hta[:5]}...")
                            else:
                                print(f"✅ Toutes les parcelles respectent la limite HTA de 1000m")
                        else:
                            print("ℹ️ Aucune distance HTA trouvée (normal si pas de postes HTA)")
                            
                else:
                    print(f"❌ Structure rpg_parcelles incorrecte: {type(rpg)}")
            else:
                print("❌ Pas de clé 'rpg_parcelles' dans la réponse")
                
            # Vérifier les informations de filtrage dans la réponse
            if 'distance_filter_info' in result:
                info = result['distance_filter_info']
                print(f"📊 Info filtrage: {info}")
                
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            print(f"Réponse: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")

if __name__ == "__main__":
    test_distance_filter()
