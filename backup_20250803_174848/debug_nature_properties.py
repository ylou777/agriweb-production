#!/usr/bin/env python3
"""
Script pour analyser les propriétés disponibles dans les données API Nature
"""

import sys
sys.path.append('.')
from agriweb_source import get_all_api_nature_data
import json

def analyze_nature_properties():
    """Analyse les propriétés disponibles pour les zones naturelles"""
    print("=== ANALYSE PROPRIÉTÉS API NATURE ===")
    
    # Coordonnées d'Hyères où on sait qu'il y a 4 zones
    geom = {"type": "Point", "coordinates": [6.396759, 43.006497]}
    
    print(f"🔍 Test avec les coordonnées: {geom}")
    
    try:
        nature_data = get_all_api_nature_data(geom)
        
        if nature_data and "features" in nature_data:
            print(f"✅ {len(nature_data['features'])} zones trouvées")
            print()
            
            for i, feature in enumerate(nature_data["features"], 1):
                print(f"--- ZONE {i} ---")
                props = feature.get("properties", {})
                
                print(f"📝 Toutes les propriétés disponibles:")
                for key, value in sorted(props.items()):
                    if value and str(value).strip():  # Seulement les valeurs non-vides
                        print(f"  • {key}: {value}")
                
                print()
                
                # Propriétés spéciales
                type_protection = props.get('TYPE_PROTECTION', 'Non défini')
                nom = props.get('NOM') or props.get('nom', 'Sans nom')
                
                print(f"🏷️ Type de protection: {type_protection}")
                print(f"📍 Nom: {nom}")
                
                # Analyse des propriétés potentiellement intéressantes
                interesting_props = [
                    'SUPERFICIE', 'superficie', 'surface',
                    'ANNEE_CREATION', 'date_creation', 'creation',
                    'GESTIONNAIRE', 'gestionnaire', 'gestion',
                    'STATUT', 'statut', 'status',
                    'DESCRIPTION', 'description', 'desc',
                    'CODE', 'code', 'id_mnhn', 'identifiant',
                    'URL', 'url', 'lien',
                    'COMMUNE', 'commune', 'communes',
                    'DEPARTEMENT', 'departement', 'dept'
                ]
                
                found_interesting = {}
                for prop in interesting_props:
                    if prop in props and props[prop] and str(props[prop]).strip():
                        found_interesting[prop] = props[prop]
                
                if found_interesting:
                    print(f"🎯 Propriétés intéressantes trouvées:")
                    for key, value in found_interesting.items():
                        print(f"  → {key}: {value}")
                
                print("=" * 50)
                
        else:
            print("❌ Aucune donnée trouvée")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_nature_properties()
