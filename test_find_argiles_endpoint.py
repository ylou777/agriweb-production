"""Test pour trouver l'endpoint correct des argiles"""
import requests

lat, lon = 47.210212, -1.587217
latlon = f"{lon},{lat}"
code_insee = "44109"

print("=== Test différents endpoints argiles ===\n")

# Test 1: gaspar/argiles avec code_insee
print("1. gaspar/argiles (code_insee)")
r = requests.get("https://www.georisques.gouv.fr/api/v1/gaspar/argiles", 
                 params={"code_insee": code_insee}, timeout=10)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    print(f"   Data: {r.json()}")

# Test 2: alea_retrait_gonflement_argiles avec latlon
print("\n2. alea_retrait_gonflement_argiles (latlon)")
r = requests.get("https://www.georisques.gouv.fr/api/v1/alea_retrait_gonflement_argiles", 
                 params={"latlon": latlon}, timeout=10)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    print(f"   Data: {r.json()}")

# Test 3: zonage_argiles avec latlon
print("\n3. zonage_argiles (latlon)")
r = requests.get("https://www.georisques.gouv.fr/api/v1/zonage_argiles", 
                 params={"latlon": latlon}, timeout=10)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    print(f"   Data: {r.json()}")

# Test 4: argiles avec code_insee
print("\n4. argiles (code_insee)")
r = requests.get("https://www.georisques.gouv.fr/api/v1/argiles", 
                 params={"code_insee": code_insee}, timeout=10)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    print(f"   Data: {r.json()}")

# Test 5: Chercher dans la doc de l'API
print("\n5. gaspar/communes pour voir les données disponibles")
r = requests.get("https://www.georisques.gouv.fr/api/v1/gaspar/communes", 
                 params={"code_insee": code_insee}, timeout=10)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"   Keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
    if data.get('data'):
        print(f"   Data keys: {data['data'][0].keys() if data['data'] else 'No data'}")
