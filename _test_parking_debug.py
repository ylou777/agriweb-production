import requests, json, math

# 1. Bbox commune via geo API (param geometry=contour)
r = requests.get('https://geo.api.gouv.fr/communes',
                 params={'codeInsee': '23096', 'format': 'geojson',
                         'geometry': 'contour', 'fields': 'contour'}, timeout=8)
features = r.json().get('features', [])
feat = features[0] if features else {}
geom = feat.get('geometry', {})
print(f"Geometry type: {geom.get('type')}")

lons = []; lats = []
if geom.get('type') == 'Polygon':
    for c in geom['coordinates'][0]: lons.append(c[0]); lats.append(c[1])
elif geom.get('type') == 'MultiPolygon':
    for poly in geom['coordinates']:
        for ring in poly:
            for c in ring: lons.append(c[0]); lats.append(c[1])

if not lons:
    print('Fallback centroide')
    lons = [1.8669]; lats = [46.1709]
    minlon = 1.8669-0.027; minlat = 46.1709-0.027
    maxlon = 1.8669+0.027; maxlat = 46.1709+0.027
else:
    minlon = min(lons)-0.0001; minlat = min(lats)-0.0001
    maxlon = max(lons)+0.0001; maxlat = max(lats)+0.0001

print(f"bbox: {minlon:.4f} {minlat:.4f} -> {maxlon:.4f} {maxlat:.4f}")
print(f"taille: {(maxlon-minlon)*111:.1f} km x {(maxlat-minlat)*111:.1f} km")

minlon = min(lons)-0.0001; minlat = min(lats)-0.0001
maxlon = max(lons)+0.0001; maxlat = max(lats)+0.0001
print(f"bbox commune: {minlon:.4f} {minlat:.4f} {maxlon:.4f} {maxlat:.4f}")

# 2. Overpass avec bbox commune
q_parts = [
    "[out:json][timeout:30];",
    "(",
    f'way["amenity"="parking"]({minlat},{minlon},{maxlat},{maxlon});',
    f'relation["amenity"="parking"]({minlat},{minlon},{maxlat},{maxlon});',
    f'way["landuse"="parking"]({minlat},{minlon},{maxlat},{maxlon});',
    ");",
    "out body geom;"
]
query = "\n".join(q_parts)

r2 = requests.post('https://overpass-api.de/api/interpreter',
                   data={'data': query}, timeout=35)
print(f"Overpass status: {r2.status_code}")
elements = r2.json().get('elements', [])
print(f"Nb elements: {len(elements)}")

for el in elements[:8]:
    g = el.get('geometry', [])
    t = el.get('tags', {})
    if not g:
        continue
    n = len(g); lat0 = g[0]['lat']
    M = 111320.0; ML = M * math.cos(math.radians(lat0))
    xs = [(c['lon'] - g[0]['lon']) * ML for c in g]
    ys = [(c['lat'] - lat0) * M for c in g]
    surf = abs(sum(xs[i]*ys[(i+1)%n] - xs[(i+1)%n]*ys[i] for i in range(n))) / 2
    print(f"  {t.get('name','?'):<30} {surf:>7.0f} m2  access={t.get('access','?')}")
