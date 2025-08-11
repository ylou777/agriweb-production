
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from agriweb_source import build_map
import requests
import time

adresse = "nantes"  # Remplace par l'adresse de ton choix
url = "http://127.0.0.1:5000/search_by_address"
max_tries = 10

for i in range(max_tries):
    try:
        resp = requests.get(url, params={"address": adresse, "sirene_radius": 0.1})
        print(f"Essai {i+1}: Status {resp.status_code}")
        if resp.status_code == 200:
            print("Succès !")
            print(resp.json())
            break
        else:
            print("Erreur, nouvelle tentative dans 2s...")
            time.sleep(2)
    except Exception as e:
        print(f"Exception: {e}")
        time.sleep(2)
else:
    print("Échec après plusieurs tentatives.")

# Exemple d'appel à build_map (à adapter selon vos besoins)
# result = build_map(
#     lat=47.2184, lon=-1.5536, address="nantes",
#     parcelle_props=None, parcelles_data=None, postes_data=None, ht_postes_data=None,
#     plu_info=None, parkings_data=None, friches_data=None, potentiel_solaire_data=None,
#     zaer_data=None, rpg_data=None, sirene_data=None, search_radius=0.1, ht_radius_deg=None,
#     api_cadastre=None, api_nature=None, api_urbanisme=None, eleveurs_data=None,
#     capacites_reseau=None, ppri_data=None
# )
# print(result)