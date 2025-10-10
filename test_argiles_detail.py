"""Test détaillé pour comprendre la structure des données argiles"""
import requests

# Nantes = 44109
code_insee = "44109"

print("=== Test gaspar/risques pour Nantes ===")
url = "https://www.georisques.gouv.fr/api/v1/gaspar/risques"
r = requests.get(url, params={"code_insee": code_insee}, timeout=10)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    print(f"Nombre de résultats: {data.get('results', 0)}")
    
    if data.get('data'):
        for item in data['data']:
            print(f"\nCommune: {item.get('libelle_commune')}")
            print(f"Nombre de risques: {len(item.get('risques_detail', []))}")
            
            # Afficher tous les risques pour voir
            for risk in item.get('risques_detail', []):
                libelle = risk.get('libelle_risque_long', '')
                print(f"  - {libelle}")

print("\n=== Test radon pour Nantes ===")
url = "https://www.georisques.gouv.fr/api/v1/radon"
r = requests.get(url, params={"code_insee": code_insee}, timeout=10)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Données radon: {data}")
