"""Test des corrections GeoRisques avec la nouvelle API"""
import sys
sys.path.insert(0, '.')

from agriweb_hebergement_gratuit import fetch_georisques_risks

# Test avec Nice
print("=" * 60)
print("TEST 1: Nice (06088)")
print("=" * 60)
lat, lon = 43.71273, 7.25092
risques = fetch_georisques_risks(lat, lon)

print("\nRésultats:")
for category, data in risques.items():
    count = len(data) if isinstance(data, list) else 0
    print(f"  {category}: {count} résultat(s)")
    if count > 0 and count <= 3:
        print(f"    Données: {data}")

print("\n" + "=" * 60)
print("TEST 2: Nantes (44109)")
print("=" * 60)
lat, lon = 47.210212, -1.587217
risques = fetch_georisques_risks(lat, lon)

print("\nRésultats:")
for category, data in risques.items():
    count = len(data) if isinstance(data, list) else 0
    print(f"  {category}: {count} résultat(s)")
    if count > 0 and count <= 3:
        print(f"    Données: {data}")

print("\n✅ Tests terminés!")
