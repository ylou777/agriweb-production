"""Test diagnostic du rapport commune"""
import json, time, sys

# Import de l'app
from agriweb_hebergement_gratuit import generate_integrated_commune_report

print("=== TEST RAPPORT INTEGRE ===")
t = time.time()
rapport = generate_integrated_commune_report("Ahun", {
    "filter_rpg": True,
    "filter_parkings": True,
    "filter_friches": True,
    "filter_toitures": True,
    "toitures_min_surface": 100.0,
    "parking_min_area": 500.0,
    "friches_min_area": 500.0
})
dt = time.time() - t
print(f"\nTemps: {dt:.1f}s")

if rapport.get("error"):
    print(f"ERREUR: {rapport['error']}")
    sys.exit(1)

# Resume
ci = rapport.get("commune_info", {})
print(f"Commune: {ci.get('caracteristiques_generales', {}).get('nom', '?')}")
print(f"Superficie: {ci.get('superficie_total_ha', 0)} ha")
print(f"Population: {ci.get('population', 0)}")

rpg = rapport.get("rpg_analysis", {}).get("resume_executif", {})
print(f"RPG: {rpg.get('total_parcelles', 0)} parcelles, {rpg.get('surface_totale_ha', 0)} ha")

pk = rapport.get("parkings_analysis", {}).get("resume_executif", {})
print(f"Parkings: {pk.get('total_parkings', 0)}")

fr = rapport.get("friches_analysis", {}).get("resume_executif", {})
print(f"Friches: {fr.get('total_friches', 0)}")

toi = rapport.get("toitures_analysis", {}).get("resume_executif", {})
print(f"Toitures: {toi.get('total_toitures', 0)}")

# Details
pd = rapport.get("parkings_details", [])
fd = rapport.get("friches_details", [])
td = rapport.get("toitures_details", [])
print(f"\nparkings_details: {len(pd)}")
print(f"friches_details: {len(fd)}")
print(f"toitures_details: {len(td)}")

if pd:
    p0 = pd[0]
    print(f"  Premier parking:")
    print(f"    adresse: {p0.get('adresse', 'MANQUANT')}")
    print(f"    surface_m2: {p0.get('surface_m2', 'MANQUANT')}")
    print(f"    poste_bt_proche: {p0.get('poste_bt_proche', 'MANQUANT')}")
if td:
    t0 = td[0]
    print(f"  Premiere toiture:")
    print(f"    adresse: {t0.get('adresse', 'MANQUANT')}")
    print(f"    surface_m2: {t0.get('surface_m2', 'MANQUANT')}")
if fd:
    f0 = fd[0]
    print(f"  Premiere friche:")
    print(f"    adresse: {f0.get('adresse', 'MANQUANT')}")

# Eleveurs
elev = rapport.get("eleveurs", {}).get("features", [])
print(f"\nEleveurs: {len(elev)}")
if elev:
    e0 = elev[0].get("properties", {})
    print(f"  Premier eleveur: {e0.get('nom', '')} {e0.get('prenom', '')}")
    print(f"  Adresse: {e0.get('adresse', 'MANQUANT')}")

# Zones
zones = rapport.get("zones", {}).get("features", [])
print(f"Zones urbanisme: {len(zones)}")

# Carte
print(f"\nCarte URL: {rapport.get('carte_url', 'MANQUANT')}")

# Cles principales du rapport
print(f"\nCles du rapport: {list(rapport.keys())}")
