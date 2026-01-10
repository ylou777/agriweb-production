import requests

# Comparaison entre l'ancienne méthode et la nouvelle pour Boulbon
print("=== COMPARAISON MÉTHODES POUR BOULBON ===\n")

# 1) Ancienne méthode avec rayon
print("1) Ancienne méthode (rayon):")
response = requests.post('http://localhost:5000/search_toitures_commune', 
                        data={'commune': 'boulbon', 'min_surface_toiture': '100'})
if response.status_code == 200:
    data = response.json()
    toitures = data.get('toitures', [])
    print(f'   Résultats: {len(toitures)} toitures trouvées')
    if toitures:
        for i, toiture in enumerate(toitures[:3]):
            props = toiture.get('properties', {})
            surface = props.get('surface_toiture_m2', 'N/A')
            print(f'   - Toiture {i+1}: {surface}m²')
else:
    print('   Erreur:', response.status_code)

print()

# 2) Nouvelle méthode avec polygone commune
print("2) Nouvelle méthode (polygone commune):")
response = requests.post('http://localhost:5000/search_toitures_commune_polygon', 
                        data={'commune': 'boulbon', 'min_surface_toiture': '100'})
if response.status_code == 200:
    data = response.json()
    toitures = data.get('toitures', [])
    print(f'   Résultats: {len(toitures)} toitures trouvées')
    if toitures:
        for i, toiture in enumerate(toitures[:5]):
            props = toiture.get('properties', {})
            surface = props.get('surface_toiture_m2', 'N/A')
            print(f'   - Toiture {i+1}: {surface}m²')
else:
    print('   Erreur:', response.status_code)

print("\n=== RÉSUMÉ ===")
print("La nouvelle méthode utilise le polygone exact de la commune")
print("au lieu d'un rayon fixe, permettant une couverture complète du territoire.")
