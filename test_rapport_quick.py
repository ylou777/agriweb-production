"""Test rapide diagnostic du rapport - limite a 5 toitures"""
import json, time, sys, os

# Monkey-patch pour limiter le nombre de toitures traitees
os.environ['TEST_MAX_TOITURES'] = '5'

from agriweb_hebergement_gratuit import generate_integrated_commune_report

print("=== TEST RAPPORT RAPIDE (max 5 toitures) ===")
t = time.time()
rapport = generate_integrated_commune_report("Ahun", {
    "filter_rpg": True,
    "filter_parkings": True,
    "filter_friches": True,
    "filter_toitures": True,
    "toitures_min_surface": 500.0,  # gros seuil pour limiter
    "parking_min_area": 500.0,
    "friches_min_area": 500.0
})
dt = time.time() - t
print(f"\n{'='*60}")
print(f"Temps total: {dt:.1f}s")
print(f"{'='*60}")

if rapport.get("error"):
    print(f"ERREUR: {rapport['error']}")
    sys.exit(1)

# Resume complet
ci = rapport.get("commune_info", {})
print(f"Commune: {ci.get('caracteristiques_generales', {}).get('nom', '?')}")
print(f"Superficie: {ci.get('superficie_total_ha', 0)} ha")
print(f"Population: {ci.get('population', 0)}")

rpg = rapport.get("rpg_analysis", {}).get("resume_executif", {})
print(f"RPG: {rpg.get('total_parcelles', 0)} parcelles, {rpg.get('surface_totale_ha', 0)} ha")

pk = rapport.get("parkings_analysis", {}).get("resume_executif", {})
print(f"Parkings resume: {pk.get('total_parkings', 0)}")

fr = rapport.get("friches_analysis", {}).get("resume_executif", {})
print(f"Friches resume: {fr.get('total_friches', 0)}")

toi = rapport.get("toitures_analysis", {}).get("resume_executif", {})
print(f"Toitures resume: {toi.get('total_toitures', 0)}")

# Details
pd = rapport.get("parkings_details", [])
fd = rapport.get("friches_details", [])
td = rapport.get("toitures_details", [])
print(f"\n--- DETAILS ---")
print(f"parkings_details: {len(pd)} elements")
print(f"friches_details: {len(fd)} elements")
print(f"toitures_details: {len(td)} elements")

# Premier de chaque
for label, details in [("Parking", pd), ("Toiture", td), ("Friche", fd)]:
    if details:
        d = details[0]
        print(f"\n  {label} #1:")
        for k in ['adresse', 'surface_m2', 'min_distance_bt_m', 'min_distance_hta_m', 
                   'poste_bt_proche', 'poste_hta_proche', 'lat', 'lon', 'lien_streetview']:
            v = d.get(k, 'CLE_ABSENTE')
            if isinstance(v, dict):
                v = f"dict({len(v)} cles)"
            print(f"    {k}: {v}")

# Eleveurs
elev = rapport.get("eleveurs", {}).get("features", [])
print(f"\nEleveurs: {len(elev)}")
if elev:
    e0 = elev[0].get("properties", {})
    print(f"  #{1}: {e0.get('nom', '')} {e0.get('prenom', '')} - adresse: {e0.get('adresse', 'MANQUANT')}")

# Zones
zones = rapport.get("zones", {}).get("features", [])
print(f"Zones urbanisme: {len(zones)}")

# Carte  
print(f"Carte URL: {rapport.get('carte_url', 'MANQUANT')}")
print(f"\nCles du rapport: {sorted(rapport.keys())}")
