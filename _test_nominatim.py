import requests

# 1. Bbox via Nominatim (recherche par nom, featuretype=city)
r = requests.get(
    'https://nominatim.openstreetmap.org/search',
    params={'q': 'Guéret', 'format': 'json', 'polygon_geojson': '1',
            'limit': '5', 'countrycodes': 'fr', 'featuretype': 'city'},
    headers={'User-Agent': 'AgriWeb/1.0'},
    timeout=12
)
results = r.json()
print(f"Nominatim: {len(results)} résultats")
for res in results:
    geom = res.get('geojson', {})
    print(f"  display={res.get('display_name','')[:60]} | geom_type={geom.get('type')}")

# Prend le premier polygon
geom = next((r.get('geojson', {}) for r in results if r.get('geojson', {}).get('type') in ('Polygon', 'MultiPolygon')), {})
print(f"\nGeometry retenu: {geom.get('type')}")

coords = geom.get('coordinates', [[]])[0]
if geom.get('type') == 'MultiPolygon':
    coords = geom['coordinates'][0][0]
lons = [c[0] for c in coords]
lats = [c[1] for c in coords]
print(f"Nb points: {len(lons)}")

if not lons:
    print("Fallback centroïde")
    minlon, maxlon = 1.8399, 1.8939
    minlat, maxlat = 46.1439, 46.1979
else:
    minlon = min(lons) - 0.0001
    maxlon = max(lons) + 0.0001
    minlat = min(lats) - 0.0001
    maxlat = max(lats) + 0.0001

print(f"bbox: {minlon:.4f} {minlat:.4f} -> {maxlon:.4f} {maxlat:.4f}")
print(f"taille: {(maxlon-minlon)*111:.1f} km x {(maxlat-minlat)*111:.1f} km")

# 2. Overpass parkings
query = (
    "[out:json][timeout:30];("
    "way[\"amenity\"=\"parking\"](" + str(minlat) + "," + str(minlon) + "," + str(maxlat) + "," + str(maxlon) + ");"
    "relation[\"amenity\"=\"parking\"](" + str(minlat) + "," + str(minlon) + "," + str(maxlat) + "," + str(maxlon) + ");"
    "way[\"landuse\"=\"parking\"](" + str(minlat) + "," + str(minlon) + "," + str(maxlat) + "," + str(maxlon) + ");"
    ");out body geom;"
)
print("\nRequête Overpass envoyée...")
r2 = requests.post('https://overpass-api.de/api/interpreter', data={'data': query}, timeout=35)
print(f"Overpass status: {r2.status_code}")
elements = r2.json().get('elements', [])
print(f"Parkings trouvés: {len(elements)}")
for el in elements[:5]:
    tags = el.get('tags', {})
    print(f"  - {tags.get('name', 'sans nom')} | amenity={tags.get('amenity')} | landuse={tags.get('landuse')}")


if not lons:
    print("Fallback centroïde")
    minlon, maxlon = 1.8399, 1.8939
    minlat, maxlat = 46.1439, 46.1979
else:
    minlon = min(lons) - 0.0001
    maxlon = max(lons) + 0.0001
    minlat = min(lats) - 0.0001
    maxlat = max(lats) + 0.0001

print(f"bbox: {minlon:.4f} {minlat:.4f} -> {maxlon:.4f} {maxlat:.4f}")
km_x = (maxlon - minlon) * 111
km_y = (maxlat - minlat) * 111
print(f"taille: {km_x:.1f} km x {km_y:.1f} km")

# 2. Overpass parkings
query = (
    "[out:json][timeout:30];("
    "way[\"amenity\"=\"parking\"](" + str(minlat) + "," + str(minlon) + "," + str(maxlat) + "," + str(maxlon) + ");"
    "relation[\"amenity\"=\"parking\"](" + str(minlat) + "," + str(minlon) + "," + str(maxlat) + "," + str(maxlon) + ");"
    "way[\"landuse\"=\"parking\"](" + str(minlat) + "," + str(minlon) + "," + str(maxlat) + "," + str(maxlon) + ");"
    ");out body geom;"
)
print("\nRequête Overpass envoyée...")
r2 = requests.post('https://overpass-api.de/api/interpreter', data={'data': query}, timeout=35)
print(f"Overpass status: {r2.status_code}")
elements = r2.json().get('elements', [])
print(f"Parkings trouvés: {len(elements)}")
for el in elements[:5]:
    tags = el.get('tags', {})
    print(f"  - {tags.get('name', 'sans nom')} | amenity={tags.get('amenity')} | landuse={tags.get('landuse')}")
