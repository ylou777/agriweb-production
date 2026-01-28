"""
Test de la fonctionnalité get_nearest_consommation
Vérifie que les points de consommation Enedis sont bien récupérés et triés par distance
"""
from agriweb_hebergement_gratuit import get_nearest_consommation, get_all_consommation

# Test avec une commune - Aast (64160)
# Coordonnées du centre d'Aast
lat_aast = 43.1667
lon_aast = -0.2833

print("=" * 80)
print("🧪 TEST: Récupération des points de consommation Enedis les plus proches")
print("=" * 80)

print(f"\n📍 Recherche autour d'Aast (lat={lat_aast}, lon={lon_aast})")

# Test 1: Récupérer TOUS les points de consommation dans un rayon
print("\n🔍 Test 1: get_all_consommation (rayon = 0.05°)")
all_consos = get_all_consommation(lat_aast, lon_aast, radius_deg=0.05)
print(f"✅ {len(all_consos)} points de consommation trouvés")

if all_consos:
    print("\n📊 Détails des 3 premiers points:")
    for i, conso in enumerate(all_consos[:3], 1):
        props = conso.get('properties', {})
        print(f"\n   Point {i}:")
        print(f"      - Distance: {props.get('distance', 'N/A')} m")
        print(f"      - Adresse: {props.get('adresse', 'N/A')}")
        print(f"      - Consommation: {props.get('consommation_mwh', 'N/A')} MWh")
        print(f"      - Secteur: {props.get('secteur', 'N/A')}")
        print(f"      - Lat/Lon: {props.get('latitude')}, {props.get('longitude')}")

# Test 2: Récupérer les N points les plus proches
print("\n\n🔍 Test 2: get_nearest_consommation (count=5)")
nearest_consos = get_nearest_consommation(lat_aast, lon_aast, count=5, radius_deg=0.05)
print(f"✅ {len(nearest_consos)} points de consommation les plus proches")

if nearest_consos:
    print("\n📊 Top 5 des points de consommation les plus proches:")
    for i, conso in enumerate(nearest_consos, 1):
        props = conso.get('properties', {})
        print(f"\n   #{i}: Distance: {props.get('distance', 'N/A')} m")
        print(f"         Adresse: {props.get('adresse', 'N/A')}")
        print(f"         Consommation: {props.get('consommation_mwh', 'N/A')} MWh/an")
        print(f"         Secteur: {props.get('secteur', 'N/A')}")
        
# Test 3: Vérifier le tri par distance
print("\n\n🔍 Test 3: Vérification du tri par distance")
if len(nearest_consos) >= 2:
    distances = [c.get('properties', {}).get('distance', float('inf')) for c in nearest_consos]
    is_sorted = all(distances[i] <= distances[i+1] for i in range(len(distances)-1))
    if is_sorted:
        print("✅ Les points sont bien triés par distance croissante")
        print(f"   Distances: {distances}")
    else:
        print("❌ ERREUR: Les points ne sont PAS triés correctement")
        print(f"   Distances: {distances}")
else:
    print("⚠️ Pas assez de points pour vérifier le tri")

print("\n" + "=" * 80)
print("✅ Test terminé")
print("=" * 80)
