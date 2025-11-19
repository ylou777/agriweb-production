#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test pour rechercher le parking ID 94321 dans la base de données
"""

import sys
sys.path.append('.')

from agriweb_source import get_parkings_info

def find_parking_94321():
    """Rechercher le parking ID 94321 dans les données"""
    
    print("🔍 Recherche du parking ID 94321...")
    
    try:
        # Test avec différentes communes pour voir si le parking existe
        test_communes = ['saumur', 'angers', 'tours', 'nantes']
        
        for commune in test_communes:
            print(f"\n📍 Test commune: {commune}")
            
            # Récupérer les données de parkings
            parkings = get_parkings_data(
                commune=commune,
                surface_min=0,
                distance_poste_max=5000  # Distance très large pour tout capturer
            )
            
            print(f"   Nombre de parkings trouvés: {len(parkings)}")
            
            # Chercher le parking 94321
            parking_94321 = None
            for parking in parkings:
                if parking.get('id') == 94321:
                    parking_94321 = parking
                    break
            
            if parking_94321:
                print(f"✅ TROUVÉ ! Parking ID 94321 dans {commune}")
                print(f"   Surface: {parking_94321.get('surface_m2', 'N/A')} m²")
                print(f"   Distance poste: {parking_94321.get('min_poste_distance_m', 'N/A')} m")
                print(f"   Géométrie: {type(parking_94321.get('geometry', 'N/A'))}")
                return parking_94321
            
            # Afficher quelques IDs pour debug
            sample_ids = [p.get('id') for p in parkings[:10]]
            print(f"   Exemples d'IDs: {sample_ids}")
    
    except Exception as e:
        print(f"❌ Erreur lors de la recherche: {e}")
        return None
    
    print("\n❌ Parking ID 94321 non trouvé dans les communes testées")
    return None

if __name__ == "__main__":
    result = find_parking_94321()
    if result:
        print("\n📊 Détails complets du parking :")
        for key, value in result.items():
            if key != 'geometry':  # Éviter d'afficher la géométrie complète
                print(f"   {key}: {value}")
    else:
        print("\n💡 Le parking ID 94321 pourrait être:")
        print("   - Dans une commune non testée")
        print("   - Filtré par les critères de surface/distance")
        print("   - Absent de la base de données actuelle")
