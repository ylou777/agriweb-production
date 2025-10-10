"""Test des endpoints GeoRisques pour identifier les bons endpoints"""
import requests

lat, lon = 43.71273, 7.25092
latlon = f"{lat},{lon}"

print("=== Test Argiles ===")
endpoints_argiles = [
    "argiles",
    "alea_retrait_gonflement_argiles", 
    "gaspar/alea_retrait_gonflement_argiles",
    "gaspar/argiles"
]

for ep in endpoints_argiles:
    try:
        url = f"https://www.georisques.gouv.fr/api/v1/{ep}"
        r = requests.get(url, params={"latlon": latlon}, timeout=10)
        print(f"{ep}: {r.status_code}")
        if r.status_code == 200:
            print(f"  Response: {r.text[:200]}")
    except Exception as e:
        print(f"{ep}: Erreur - {e}")

print("\n=== Test Radon (nécessite code_insee) ===")
# Pour Nice, code INSEE = 06088
try:
    r = requests.get("https://www.georisques.gouv.fr/api/v1/radon", 
                     params={"code_insee": "06088"}, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
except Exception as e:
    print(f"Erreur: {e}")

print("\n=== Test Installations ===")
endpoints_installations = [
    "installations",
    "installations_classees",
    "gaspar/installations_classees"
]

for ep in endpoints_installations:
    try:
        url = f"https://www.georisques.gouv.fr/api/v1/{ep}"
        r = requests.get(url, params={"latlon": latlon, "rayon": 2000}, timeout=10)
        print(f"{ep}: {r.status_code}")
        if r.status_code == 200:
            print(f"  Response: {r.text[:200]}")
    except Exception as e:
        print(f"{ep}: Erreur - {e}")
