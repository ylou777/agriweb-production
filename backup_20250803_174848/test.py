import requests
import json

lat, lon = 43.0283395, 6.4684372

# Exemple de polygone autour du point (100m)
def bbox_to_polygon(lon, lat, delta=0.001):
    return {
        "type": "Polygon",
        "coordinates": [[
            [lon - delta, lat - delta],
            [lon + delta, lat - delta],
            [lon + delta, lat + delta],
            [lon - delta, lat + delta],
            [lon - delta, lat - delta]
        ]]
    }

geom = bbox_to_polygon(lon, lat)

# Liste des endpoints IGN Nature
endpoints = [
    "/nature/natura-habitat",
    "/nature/natura-oiseaux",
    "/nature/rnc",
    "/nature/rnn",
    "/nature/znieff1",
    "/nature/znieff2",
    "/nature/pn",
    "/nature/pnr",
    "/nature/rncf"
]

for ep in endpoints:
    url = f"https://apicarto.ign.fr/api{ep}"
    params = {"geom": json.dumps(geom), "_limit": 1000}
    r = requests.get(url, params=params)
    print(f"{ep}: {r.status_code}, {len(r.json().get('features', [])) if r.ok else 'Erreur'} features")

# Exemple PPRI (GeoRisques)
ppri_url = "https://www.georisques.gouv.fr/api/v1/ppri"
params = {"lat": lat, "lon": lon}
r = requests.get(ppri_url, params=params)
print(f"PPRI: {r.status_code}, {len(r.json().get('features', [])) if r.ok else 'Erreur'} features")