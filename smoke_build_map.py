import time
from agriweb_hebergement_gratuit import build_map, save_map_html

# Minimal smoke test exercising the Éleveurs popup HTML
lat, lon = 48.8566, 2.3522
address = "Test Adresse"

parcelle_props = {}
parcelles_data = {"type": "FeatureCollection", "features": []}
postes_data = []
ht_postes_data = []
plu_info = []
parkings_data = []
friches_data = []
potentiel_solaire_data = []
zaer_data = []
rpg_data = []
sirene_data = []
search_radius = 0.01
ht_radius_deg = 0.01
api_cadastre = {"type": "FeatureCollection", "features": []}
api_nature = {"type": "FeatureCollection", "features": []}
api_urbanisme = {}
capacites_reseau = []

# One Éleveur feature with typical fields
eleveurs_data = [
    {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "nomUniteLe": "Ferme Demo",
            "libelleCom": "Paris",
            "siret": "12345678901234"
        }
    }
]

m = build_map(
    lat, lon, address,
    parcelle_props, parcelles_data,
    postes_data, ht_postes_data, plu_info,
    parkings_data, friches_data, potentiel_solaire_data,
    zaer_data, rpg_data, sirene_data,
    search_radius, ht_radius_deg,
    api_cadastre=api_cadastre, api_nature=api_nature, api_urbanisme=api_urbanisme,
    eleveurs_data=eleveurs_data,
    capacites_reseau=capacites_reseau
)

filename = f"smoke_map_{int(time.time())}.html"
rel = save_map_html(m, filename)
print("SMOKE_SAVED:", rel)
