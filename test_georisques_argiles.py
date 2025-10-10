"""Test des endpoints GeoRisques pour argiles avec code INSEE"""
import requests

# Nice = 06088
code_insee = "06088"

print("=== Test Argiles avec code_insee ===")
endpoints = [
    ("radon", {"code_insee": code_insee}),
    ("alea_retrait_gonflement_argiles", {"code_insee": code_insee}),
    ("argiles", {"code_insee": code_insee}),
]

for ep, params in endpoints:
    try:
        url = f"https://www.georisques.gouv.fr/api/v1/{ep}"
        r = requests.get(url, params=params, timeout=10)
        print(f"{ep}: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"  Data: {data}")
    except Exception as e:
        print(f"{ep}: Erreur - {e}")

print("\n=== Test avec gaspar ===")
try:
    url = "https://www.georisques.gouv.fr/api/v1/gaspar/risques"
    r = requests.get(url, params={"code_insee": code_insee}, timeout=10)
    print(f"gaspar/risques: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Data keys: {data.keys()}")
        print(f"  Results: {data.get('results', 0)}")
        if data.get('data'):
            print(f"  First result: {data['data'][0]}")
except Exception as e:
    print(f"Erreur: {e}")
