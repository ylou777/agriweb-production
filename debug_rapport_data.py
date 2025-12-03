"""
Script de débogage pour vérifier les données du rapport commune
"""
import json
import sys

# Charger un rapport exemple depuis l'URL
import requests

# Remplacez par votre commune de test
COMMUNE = "Limoges"
URL = f"http://localhost:5000/rapport_commune_complet?commune={COMMUNE}"

print(f"🔍 Récupération du rapport pour {COMMUNE}...")
response = requests.get(URL)

if response.status_code == 200:
    try:
        data = response.json()
        
        print("\n📊 Structure du rapport:")
        print(f"  - Clés racine: {list(data.keys())}")
        
        if "toitures_analysis" in data:
            toitures = data["toitures_analysis"]
            print(f"\n🏠 Toitures Analysis:")
            print(f"  - Clés: {list(toitures.keys())}")
            
            if "details" in toitures:
                details = toitures["details"]
                print(f"  - Nombre de toitures: {len(details)}")
                
                if details and len(details) > 0:
                    print(f"\n📝 Première toiture:")
                    premier = details[0]
                    print(json.dumps(premier, indent=2, ensure_ascii=False))
                    
                    # Vérifier présence de lat/lon
                    has_lat = "lat" in premier
                    has_lon = "lon" in premier
                    has_coords = "coords" in premier
                    has_centroid_lat = "centroid_lat" in premier
                    has_centroid_lon = "centroid_lon" in premier
                    
                    print(f"\n✅ Champs de coordonnées:")
                    print(f"  - lat: {has_lat}")
                    print(f"  - lon: {has_lon}")
                    print(f"  - coords: {has_coords}")
                    print(f"  - centroid_lat: {has_centroid_lat}")
                    print(f"  - centroid_lon: {has_centroid_lon}")
                else:
                    print("  ⚠️ Aucune toiture dans details")
            else:
                print("  ⚠️ Pas de clé 'details' dans toitures_analysis")
        else:
            print("❌ Pas de clé 'toitures_analysis' dans le rapport")
            
    except Exception as e:
        print(f"❌ Erreur lors du parsing JSON: {e}")
        print(f"Réponse brute: {response.text[:500]}")
else:
    print(f"❌ Erreur HTTP {response.status_code}")
