"""
Diagnostic solaire municipal par commune — données MAJIC + IGN + OSM
=====================================================================
Pour chaque commune :
  1. MAJIC (PostgreSQL Railway) → parcelles appartenant à la commune
  2. IGN Apicarto             → géométries GeoJSON des parcelles
  3. Overpass / IGN BDTOPO    → parkings + bâtiments publics
  4. PVGIS                    → irradiance par centroïde de parcelle
  5. Folium                   → carte HTML interactive par commune
  6. Synthèse PDF (optionnel) → rapport mini-plan à envoyer

Colonnes MAJIC utilisées :
  code_insee, section, numero, contenance (m²), denomination, forme_juridique
"""

import os
import math
import json
import time
import hashlib
import logging
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional

logger = logging.getLogger(__name__)

# ── Connexion PostgreSQL (même config que proprietaires_utils.py) ──────────────
import re as _re

DATABASE_URL = (
    os.environ.get('DATABASE_URL') or
    os.environ.get('DATABASE_PUBLIC_URL') or
    "postgresql://postgres:WbjgkcXDKvbbYJhWprDDQQobbpnggYJc@yamanote.proxy.rlwy.net:42931/railway"
)

def _parse_db_url(url: str) -> Optional[dict]:
    m = _re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', url)
    if m:
        return {'user': m.group(1), 'password': m.group(2),
                'host': m.group(3), 'port': int(m.group(4)), 'database': m.group(5)}
    return None

DB_CONFIG = _parse_db_url(DATABASE_URL)

def _pg():
    if not DB_CONFIG:
        raise RuntimeError("DATABASE_URL invalide")
    return psycopg2.connect(**DB_CONFIG, connect_timeout=15)

# ── Codes forme_juridique réels dans la base ──────────────────────────────────
# (codes NAF/INSEE tels que chargés — différents des codes MAJIC standard)
# 7210 = Communes, 7220 = Départements/Régions, 7113 = État, 9900 = ONF/État,
# 7313 = Sections de commune, 7312 = Syndicats intercommunaux
CODES_COMMUNE = {'7210'}
CODES_PUBLIC  = {'7113', '7210', '7220', '7312', '7313', '9900', '9220'}

# Seuil surface minimum pour être intéressant
SEUIL_SURFACE_M2 = 200   # parcelles < 200 m² ignorées

# Seuils légaux Art. L.171-5 CCH — solarisation obligatoire d'ici 2028
SEUIL_BATIMENT_M2 = 500   # bâtiments publics < 500 m² exclus
SEUIL_PARKING_M2  = 1500  # parkings < 1 500 m² exclus

# ══════════════════════════════════════════════════════════════════════════════
# 1. MAJIC — Parcelles municipales
# ══════════════════════════════════════════════════════════════════════════════

def get_parcelles_municipales(code_insee: str) -> list:
    """
    Retourne toutes les parcelles appartenant à la commune (MAJIC).
    Pas de filtre sur la surface : on veut TOUTES les parcelles pour avoir
    les polygones réels via Apicarto et faire un filtrage PIP fiable.
    Tri par contenance ASC : les petites parcelles (bâties) en premier,
    puis les grandes (parcs, forêts) — utile si on veut sous-échantillonner.
    """
    if not DB_CONFIG:
        return []
    try:
        conn = _pg()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT
                section,
                numero,
                contenance,
                denomination,
                forme_juridique,
                siren
            FROM proprietaires_parcelles
            WHERE code_insee = %s
              AND (
                  forme_juridique IN ('7210')
                  OR UPPER(denomination) LIKE 'COMMUNE DE %%'
                  OR UPPER(denomination) LIKE 'MAIRIE DE %%'
                  OR UPPER(denomination) = 'LA COMMUNE'
              )
            ORDER BY contenance ASC NULLS LAST
        """, (code_insee,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        logger.warning(f"MAJIC query failed for {code_insee}: {e}")
        return []


def get_parcelles_publiques(code_insee: str) -> list:
    """
    Toutes les parcelles d'entités publiques dans la commune
    (élargi : commune + état + dpt + région + EP).
    """
    if not DB_CONFIG:
        return []
    try:
        conn = _pg()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        codes = list(CODES_PUBLIC)
        placeholder = ','.join(['%s'] * len(codes))
        cur.execute(f"""
            SELECT section, numero, contenance, denomination, forme_juridique, siren
            FROM proprietaires_parcelles
            WHERE code_insee = %s
              AND forme_juridique IN ({placeholder})
              AND (contenance IS NULL OR contenance >= %s)
            ORDER BY contenance DESC NULLS LAST
        """, [code_insee] + codes + [SEUIL_SURFACE_M2])
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        logger.warning(f"MAJIC public query failed for {code_insee}: {e}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
# 2. IGN Apicarto — Géométries des parcelles
# ══════════════════════════════════════════════════════════════════════════════

_APICARTO = "https://apicarto.ign.fr/api/cadastre/parcelle"

def _apicarto_parcelle(code_insee: str, section: str, numero: str) -> Optional[dict]:
    """Retourne le feature GeoJSON d'une parcelle (ou None)."""
    try:
        # normaliser : section 2 chars, numéro 4 chars
        section = section.strip().upper().zfill(2)
        numero  = numero.strip().zfill(4)
        r = requests.get(_APICARTO, params={
            'code_insee': code_insee,
            'section': section,
            'numero': numero,
            '_limit': 1
        }, timeout=10)
        r.raise_for_status()
        data = r.json()
        features = data.get('features', [])
        return features[0] if features else None
    except Exception as e:
        logger.debug(f"Apicarto {code_insee}/{section}/{numero}: {e}")
        return None


def _centroid_geojson(geometry: dict) -> tuple:
    """Calcule le centroïde d'un GeoJSON geometry (Polygon ou MultiPolygon)."""
    try:
        coords = []
        gtype = geometry.get('type', '')
        if gtype == 'Polygon':
            coords = geometry['coordinates'][0]
        elif gtype == 'MultiPolygon':
            # prendre le plus grand anneau
            coords = max(geometry['coordinates'], key=lambda r: len(r[0]))[0]
        if coords:
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            return round(sum(lats)/len(lats), 6), round(sum(lons)/len(lons), 6)
    except Exception:
        pass
    return None, None


def enrich_parcelles_with_geometry(code_insee: str, parcelles: list,
                                   max_requests: int = 9999) -> list:
    """
    Enrichit les parcelles MAJIC avec leurs polygones IGN via Apicarto.

    Stratégie par section (N requêtes = N sections distinctes) :
      - Regroupe les parcelles MAJIC par section cadastrale
      - Fait 1 requête Apicarto par section (retourne jusqu'à 200 parcelles/section)
      - Filtre côté client par les numéros MAJIC voulus
      → Beaucoup plus rapide que 1 requête par parcelle
      → Pour une commune à 43 sections : ~43 req × 0.25s = ~12s au lieu de 695 × 0.25s = 174s

    Les parcelles sans géométrie IGN sont retournées avec geometry=None
    (centroïde None) et devront être exclues du calcul PIP.
    """
    if not parcelles:
        return []

    # Grouper par section
    from collections import defaultdict
    by_section: dict = defaultdict(list)
    for p in parcelles:
        sect = p['section'].strip().upper()
        sect = sect.zfill(2)   # Apicarto exige 2 caractères (ex: "A" → "0A")
        by_section[sect].append(p)

    # Construire index section→{numero: parcelle} pour filtre rapide
    index: dict = {}
    for sect, items in by_section.items():
        index[sect] = {p['numero'].strip().zfill(4): p for p in items}

    enriched = []
    sections = list(by_section.keys())

    for i, sect in enumerate(sections[:max_requests]):
        try:
            r = requests.get(_APICARTO, params={
                'code_insee': code_insee,
                'section':    sect,
                '_limit':     500,   # Apicarto max ~500 par requête
            }, timeout=12)
            r.raise_for_status()
            features = r.json().get('features', [])
        except Exception as e:
            logger.debug(f"Apicarto section {sect}: {e}")
            features = []

        for feat in features:
            props = feat.get('properties', {})
            geom  = feat.get('geometry', {})
            num_raw = str(props.get('numero', '')).strip().zfill(4)
            if num_raw not in index.get(sect, {}):
                continue   # parcelle de la section mais pas dans MAJIC → ignorer
            p_orig = index[sect][num_raw]
            lat, lon = _centroid_geojson(geom)
            p2 = dict(p_orig)
            p2['geometry']    = geom if geom else None
            p2['lat']         = lat
            p2['lon']         = lon
            p2['surface_ign'] = props.get('contenance') or p_orig.get('contenance')
            p2['id_parcelle'] = f"{code_insee}-{sect}-{num_raw}"
            enriched.append(p2)

        if i < len(sections) - 1:
            time.sleep(0.25)

    return enriched


# ══════════════════════════════════════════════════════════════════════════════
# 3. OSM Overpass — Parkings + bâtiments publics
# ══════════════════════════════════════════════════════════════════════════════

_OVERPASS = "https://overpass-api.de/api/interpreter"

def get_parkings_osm(lat: float, lon: float, rayon_m: int = 3000) -> list:
    """
    Requête Overpass pour les parkings publics autour du centre-commune.
    Retourne liste de features {lat, lon, surface_m2, name, ref}.
    """
    if not lat or not lon:
        return []
    query = f"""
[out:json][timeout:15];
(
  way["amenity"="parking"](around:{rayon_m},{lat},{lon});
  relation["amenity"="parking"](around:{rayon_m},{lat},{lon});
  way["landuse"="parking"](around:{rayon_m},{lat},{lon});
);
out body geom;
"""
    try:
        r = requests.post(_OVERPASS, data={'data': query}, timeout=20)
        r.raise_for_status()
        elements = r.json().get('elements', [])
        parkings = []
        for el in elements:
            geom = el.get('geometry', [])
            tags = el.get('tags', {})
            if not geom:
                continue
            lats = [g['lat'] for g in geom]
            lons = [g['lon'] for g in geom]
            clat = sum(lats)/len(lats)
            clon = sum(lons)/len(lons)
            # surface approx par shoelace
            surf = _polygon_area_m2(geom)
            if surf < 200:
                continue
            parkings.append({
                'type': 'parking_osm',
                'lat': round(clat, 6),
                'lon': round(clon, 6),
                'surface_m2': round(surf),
                'name': tags.get('name', 'Parking'),
                'access': tags.get('access', ''),
                'denomination': tags.get('name', 'Parking OSM'),
                'geometry_osm': geom,
            })
        return parkings
    except Exception as e:
        logger.debug(f"Overpass error: {e}")
        return []


def get_parkings_geoserver_bbox(bbox: tuple) -> list:
    """
    Parkings depuis la couche GeoServer `parkings_sup500m2` (tous les parkings
    > 500 m² de France, données propres).
    bbox = (minlon, minlat, maxlon, maxlat).
    Résultats mis en cache.
    """
    cache_key = tuple(round(x, 4) for x in bbox)
    if cache_key in _parkings_cache:
        logger.debug(f"GeoServer parkings cache hit: {cache_key}")
        return _parkings_cache[cache_key]

    minlon, minlat, maxlon, maxlat = bbox
    parkings = []
    geoserver_ok = False
    try:
        from geoserver_config_flexible import geoserver
        bbox_str = f"{minlon},{minlat},{maxlon},{maxlat},EPSG:4326"
        features = geoserver.fetch_layer_data(
            "parkings_sup500m2",
            bbox_str,
            max_features=500,
            srsname="EPSG:4326",
        )
        geoserver_ok = True  # réponse reçue (même vide = zone sans parking)
        for feat in features:
            geom  = feat.get('geometry', {})
            props = feat.get('properties', {})
            if not geom:
                continue
            lat_c, lon_c = _centroid_geojson(geom)
            if not lat_c or not lon_c:
                continue
            # Surface : propriété de la couche ou calcul Shoelace
            surf = (
                props.get('surface_m2') or
                props.get('area') or
                props.get('shape_area') or
                _geojson_area_m2(geom)
            )
            try:
                surf = float(surf)
            except (TypeError, ValueError):
                surf = _geojson_area_m2(geom)
            if surf < 50:
                continue
            name = (
                props.get('nom') or
                props.get('name') or
                props.get('denomination') or
                'Parking'
            )
            parkings.append({
                'type':        'parking_geoserver',
                'lat':         lat_c,
                'lon':         lon_c,
                'surface_m2':  round(surf),
                'name':        name,
                'denomination': name,
                'geometry':    geom,
            })
        logger.info(f"GeoServer parkings_sup500m2: {len(parkings)} parkings dans bbox")
    except Exception as e:
        logger.warning(f"GeoServer parkings error: {e}")
        geoserver_ok = False

    # Ne mettre en cache que si GeoServer a répondu (évite de cacher un échec réseau)
    if geoserver_ok:
        _parkings_cache[cache_key] = parkings
    return parkings


def get_parkings_osm_bbox(bbox: tuple) -> list:
    """
    Fallback Overpass : parkings OSM dans une bbox (minlon, minlat, maxlon, maxlat).
    Utilisé uniquement si GeoServer est inaccessible.
    """
    cache_key = tuple(round(x, 4) for x in bbox)
    if cache_key in _parkings_cache:
        logger.debug(f"Overpass parkings cache hit: {cache_key}")
        return _parkings_cache[cache_key]

    minlon, minlat, maxlon, maxlat = bbox
    ov_timeout = 60
    req_timeout = 70
    query = (
        "[out:json][timeout:" + str(ov_timeout) + "];\n"
        "(\n"
        "  way[\"amenity\"=\"parking\"](" + str(minlat) + "," + str(minlon) + "," + str(maxlat) + "," + str(maxlon) + ");\n"
        "  relation[\"amenity\"=\"parking\"](" + str(minlat) + "," + str(minlon) + "," + str(maxlat) + "," + str(maxlon) + ");\n"
        "  way[\"landuse\"=\"parking\"](" + str(minlat) + "," + str(minlon) + "," + str(maxlat) + "," + str(maxlon) + ");\n"
        ");\n"
        "out body geom;"
    )
    parkings = []
    last_exc = None
    for attempt in range(3):
        if attempt > 0:
            wait = 15 * attempt
            logger.warning(f"Overpass retry {attempt}/2 dans {wait}s...")
            time.sleep(wait)
        try:
            r = requests.post(_OVERPASS, data={'data': query}, timeout=req_timeout)
            r.raise_for_status()
            elements = r.json().get('elements', [])
            for el in elements:
                geom = el.get('geometry', [])
                tags = el.get('tags', {})
                if not geom:
                    continue
                lats_el = [g['lat'] for g in geom]
                lons_el = [g['lon'] for g in geom]
                clat = sum(lats_el) / len(lats_el)
                clon = sum(lons_el) / len(lons_el)
                surf = _polygon_area_m2(geom)
                if surf < 50:
                    continue
                parkings.append({
                    'type':        'parking_osm',
                    'lat':         round(clat, 6),
                    'lon':         round(clon, 6),
                    'surface_m2':  round(surf),
                    'name':        tags.get('name', 'Parking'),
                    'access':      tags.get('access', ''),
                    'denomination': tags.get('name') or 'Parking communal',
                    'geometry_osm': geom,
                })
            break
        except Exception as e:
            last_exc = e
            logger.warning(f"Overpass bbox error (tentative {attempt+1}/3): {e}")

    if last_exc and not parkings:
        logger.warning(f"Overpass : 0 parkings après 3 tentatives — {last_exc}")

    _parkings_cache[cache_key] = parkings
    return parkings


def get_batiments_publics_osm(lat: float, lon: float, rayon_m: int = 2000) -> list:
    """
    Bâtiments publics OSM : mairie, école, salle polyvalente, etc.
    """
    if not lat or not lon:
        return []
    query = f"""
[out:json][timeout:15];
(
  way["amenity"~"townhall|school|community_centre|fire_station|library|hospital|sports_centre"](around:{rayon_m},{lat},{lon});
  way["building"~"public|civic|school|hospital"](around:{rayon_m},{lat},{lon});
);
out body geom;
"""
    try:
        r = requests.post(_OVERPASS, data={'data': query}, timeout=20)
        r.raise_for_status()
        elements = r.json().get('elements', [])
        result = []
        for el in elements:
            geom = el.get('geometry', [])
            tags = el.get('tags', {})
            if not geom:
                continue
            lats = [g['lat'] for g in geom]
            lons = [g['lon'] for g in geom]
            surf = _polygon_area_m2(geom)
            if surf < 100:
                continue
            amenity = tags.get('amenity', tags.get('building', 'batiment_public'))
            AMENITY_LABELS = {
                'townhall': 'Mairie', 'school': 'École', 'community_centre': 'Salle communale',
                'fire_station': 'Caserne', 'library': 'Bibliothèque',
                'hospital': 'Hôpital', 'sports_centre': 'Complexe sportif',
                'public': 'Bâtiment public', 'civic': 'Équipement civique',
            }
            result.append({
                'type': 'batiment_public',
                'lat': round(sum(lats)/len(lats), 6),
                'lon': round(sum(lons)/len(lons), 6),
                'surface_m2': round(surf),
                'name': tags.get('name', AMENITY_LABELS.get(amenity, 'Bâtiment public')),
                'amenity': amenity,
                'denomination': tags.get('name', AMENITY_LABELS.get(amenity, '')),
                'geometry_osm': geom,
            })
        return result
    except Exception as e:
        logger.debug(f"Overpass bâtiments error: {e}")
        return []


def _polygon_area_m2(geom_list: list) -> float:
    """Surface approx en m² via Shoelace — format OSM [{lat, lon}, ...]."""
    try:
        n = len(geom_list)
        if n < 3:
            return 0.0
        lat0 = geom_list[0]['lat']
        M_PER_DEG_LAT = 111320.0
        M_PER_DEG_LON = 111320.0 * math.cos(math.radians(lat0))
        xs = [(g['lon'] - geom_list[0]['lon']) * M_PER_DEG_LON for g in geom_list]
        ys = [(g['lat'] - lat0) * M_PER_DEG_LAT for g in geom_list]
        area = abs(sum(xs[i]*ys[(i+1)%n] - xs[(i+1)%n]*ys[i] for i in range(n))) / 2
        return area
    except Exception:
        return 0.0


def _ring_area_m2(ring: list) -> float:
    """Surface approx en m² via Shoelace — format GeoJSON [[lon, lat], ...]."""
    try:
        n = len(ring)
        if n < 3:
            return 0.0
        lat0 = ring[0][1]
        M_LAT = 111320.0
        M_LON = 111320.0 * math.cos(math.radians(lat0))
        xs = [(c[0] - ring[0][0]) * M_LON for c in ring]
        ys = [(c[1] - lat0) * M_LAT for c in ring]
        area = abs(sum(xs[i]*ys[(i+1)%n] - xs[(i+1)%n]*ys[i] for i in range(n))) / 2
        return area
    except Exception:
        return 0.0


def _geojson_area_m2(geometry: dict) -> float:
    """Surface en m² d'une géométrie GeoJSON Polygon ou MultiPolygon."""
    try:
        gtype = geometry.get('type', '')
        if gtype == 'Polygon':
            return _ring_area_m2(geometry['coordinates'][0])
        elif gtype == 'MultiPolygon':
            return sum(_ring_area_m2(poly[0]) for poly in geometry['coordinates'])
    except Exception:
        pass
    return 0.0


# ── Helpers géométriques : point-in-polygon (ray casting) + bbox union ────────

def _point_in_ring(lon: float, lat: float, ring: list) -> bool:
    """Ray casting. ring = [[lon, lat], ...] (format GeoJSON)."""
    n = len(ring)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        denom = yj - yi
        if denom and (yi > lat) != (yj > lat):
            if lon < (xj - xi) * (lat - yi) / denom + xi:
                inside = not inside
        j = i
    return inside


def _point_in_geojson(lon: float, lat: float, geometry: dict) -> bool:
    """Teste si (lon, lat) est dans un GeoJSON Polygon ou MultiPolygon."""
    try:
        gtype = geometry.get('type', '')
        coords = geometry.get('coordinates', [])
        if gtype == 'Polygon':
            return bool(coords) and _point_in_ring(lon, lat, coords[0])
        elif gtype == 'MultiPolygon':
            return any(_point_in_ring(lon, lat, poly[0]) for poly in coords)
    except Exception:
        pass
    return False


def _point_in_any_parcel(lon: float, lat: float, parcelles: list) -> bool:
    """
    Retourne True si (lon, lat) est dans au moins une parcelle communale MAJIC.
    Utilisé pour filtrer les bâtiments BD TOPO et les parkings.
    """
    for p in parcelles:
        geom = p.get('geometry')
        if geom and _point_in_geojson(lon, lat, geom):
            return True
    return False


def _find_parcel_id(lon: float, lat: float, parcelles: list) -> str:
    """
    Retourne l'id_parcelle MAJIC (section-numero) de la première parcelle
    communale contenant le point (lon, lat), ou '' si aucune.
    """
    for p in parcelles:
        geom = p.get('geometry')
        if geom and _point_in_geojson(lon, lat, geom):
            pid = p.get('id_parcelle', '')
            # Format : {code_insee}-{section}-{numero} → on retourne section-numero
            parts = pid.split('-', 1)
            return parts[1] if len(parts) == 2 else pid
    return ''


def _bbox_parcelles(parcelles: list) -> Optional[tuple]:
    """
    Bounding box union (minlon, minlat, maxlon, maxlat) des polygones MAJIC.
    Retourne None si aucune géométrie disponible.
    """
    lons: list = []
    lats: list = []
    for p in parcelles:
        geom = p.get('geometry')
        if not geom:
            if p.get('lon') and p.get('lat'):
                lons.append(float(p['lon']))
                lats.append(float(p['lat']))
            continue
        try:
            gtype = geom.get('type', '')
            if gtype == 'Polygon':
                for ring in geom['coordinates']:
                    for c in ring:
                        lons.append(c[0]); lats.append(c[1])
            elif gtype == 'MultiPolygon':
                for poly in geom['coordinates']:
                    for ring in poly:
                        for c in ring:
                            lons.append(c[0]); lats.append(c[1])
        except Exception:
            pass
    if not lons:
        return None
    buf = 0.0001  # ~10 m de buffer
    return (min(lons) - buf, min(lats) - buf, max(lons) + buf, max(lats) + buf)


# ══════════════════════════════════════════════════════════════════════════════
# 3b. IGN BD TOPO WFS — Empreintes des bâtiments sur parcelles communales
# ══════════════════════════════════════════════════════════════════════════════
#
# Logique APER : l'obligation ne concerne que les bâtiments appartenant à
# la commune. On requête BD TOPO par emprise géographique (bbox des parcelles
# MAJIC), sans filtre usage ni code_commune (souvent non exposé en WFS).
# Le tri par parcelle se fait en aval via point-in-polygon.

_BDTOPO_WFS = "https://data.geopf.fr/wfs/ows"
_USAGE_FR = {
    'Administratif': 'Bâtiment administratif',
    'Enseignement':  'École / Lycée',
    'Sportif':       'Équipement sportif',
    'Culturel':      'Équipement culturel',
    'Religieux':     'Édifice religieux',
    'Santé':         'Établissement de santé',
    'Résidentiel':   'Logement communal',
    'Industriel':    'Bâtiment technique',
}


def get_batiments_bdtopo_bbox(bbox: tuple, max_features: int = 2000) -> list:
    """
    Empreintes de bâtiments BD TOPO V3 dans une bbox (minlon, minlat, maxlon, maxlat).
    Pas de filtre usage ni code_commune : requête spatiale pure, le filtrage
    par parcelle MAJIC se fait en aval (point-in-polygon).
    Surface retournée = empreinte au sol réelle du bâtiment (m²).
    """
    minlon, minlat, maxlon, maxlat = bbox
    cql_bbox = f"BBOX(geometrie,{minlon},{minlat},{maxlon},{maxlat},'CRS:84')"
    try:
        r = requests.get(_BDTOPO_WFS, params={
            'SERVICE':      'WFS',
            'REQUEST':      'GetFeature',
            'VERSION':      '2.0.0',
            'TYPENAMES':    'BDTOPO_V3:batiment',
            'outputFormat': 'application/json',
            'SRSNAME':      'CRS:84',
            'CQL_FILTER':   cql_bbox,
            'COUNT':        max_features,
        }, timeout=25)
        r.raise_for_status()
        features = r.json().get('features', [])
        result = []
        for feat in features:
            geom  = feat.get('geometry', {})
            props = feat.get('properties', {})
            if not geom:
                continue
            surf = _geojson_area_m2(geom)
            if surf < 50:
                continue
            lat_c, lon_c = _centroid_geojson(geom)
            if not lat_c or not lon_c:
                continue
            usage = props.get('usage_1', '') or props.get('nature', '') or ''
            denomination = _USAGE_FR.get(usage, '') or 'Bâtiment communal'
            result.append({
                'type':        'batiment_public',
                'source':      'BDTOPO',
                'lat':         lat_c,
                'lon':         lon_c,
                'surface_m2':  round(surf),
                'name':        denomination,
                'denomination': denomination,
                'usage':       usage,
                'geometry':    geom,
            })
        logger.info(f"BDTOPO bbox: {len(result)} bâtiments dans emprise parcelles")
        return result
    except Exception as e:
        logger.warning(f"BDTOPO WFS bbox error: {e}")
        return []


def get_commune_bbox(code_insee: str, lat: float, lon: float,
                     nom_commune: str = '') -> tuple:
    """
    Retourne la bbox (minlon, minlat, maxlon, maxlat) du territoire communal
    via Nominatim (OSM) avec polygon_geojson=1.
    Fallback : carré ~5 km autour du centroïde.
    """
    def _extract(geom):
        lons_all: list = []; lats_all: list = []
        gtype = geom.get('type', '')
        coords = geom.get('coordinates', [])
        if gtype == 'Polygon':
            rings = coords
        elif gtype == 'MultiPolygon':
            rings = [ring for poly in coords for ring in poly]
        else:
            return None
        for ring in rings:
            for c in ring:
                lons_all.append(c[0]); lats_all.append(c[1])
        if lons_all:
            buf = 0.0001
            return (min(lons_all)-buf, min(lats_all)-buf,
                    max(lons_all)+buf, max(lats_all)+buf)
        return None

    # Cache : évite de ré-appeler Nominatim pour la même commune (rate-limit)
    if code_insee in _commune_bbox_cache:
        return _commune_bbox_cache[code_insee]

    # Nominatim : recherche par nom de commune (boundary/city)
    search_q = nom_commune if nom_commune else code_insee
    try:
        import time as _time
        _time.sleep(1.1)   # Respecter le rate-limit Nominatim (1 req/s)
        r = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={
                'q': search_q,
                'format': 'json',
                'polygon_geojson': '1',
                'limit': '5',
                'countrycodes': 'fr',
                'featuretype': 'city',
            },
            headers={'User-Agent': 'AgriWeb-Heliapv/1.0 (contact@heliapv.fr)'},
            timeout=12
        )
        r.raise_for_status()
        results = r.json()
        # Prend le premier résultat avec un polygon (type Polygon/MultiPolygon)
        for candidate in results:
            geom = candidate.get('geojson', {})
            if geom.get('type') in ('Polygon', 'MultiPolygon'):
                result = _extract(geom)
                if result:
                    logger.debug(f"get_commune_bbox {code_insee}: Nominatim OK ({candidate.get('display_name','')[:50]})")
                    _commune_bbox_cache[code_insee] = result
                    return result
    except Exception as e:
        logger.debug(f"get_commune_bbox Nominatim {code_insee}: {e}")

    # Fallback : carré ~5 km autour du centroïde
    if lat and lon:
        d = 0.045   # ~5 km
        logger.debug(f"get_commune_bbox {code_insee}: fallback 5km")
        result = (lon - d, lat - d, lon + d, lat + d)
        _commune_bbox_cache[code_insee] = result
        return result
    return None


# ══════════════════════════════════════════════════════════════════════════════
# 4. PVGIS — Irradiance par coordonnée
# ══════════════════════════════════════════════════════════════════════════════

_pvgis_cache: dict = {}
_commune_bbox_cache: dict = {}   # cache bbox communale (Nominatim → rate-limit safe)
_parkings_cache: dict = {}       # cache résultats Overpass parkings (évite double appel)

def pvgis_irradiance(lat: float, lon: float) -> dict:
    """Retourne {irradiance, prod_kwh_kwc, label} avec cache local."""
    if not lat or not lon:
        return {'irradiance': 1350, 'prod_kwh_kwc': 1050, 'label': 'moyen'}
    key = f"{round(lat,2)},{round(lon,2)}"
    if key in _pvgis_cache:
        return _pvgis_cache[key]
    try:
        url = (
            "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc"
            f"?lat={lat}&lon={lon}&peakpower=1&loss=14&outputformat=json&browser=0"
        )
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        data = r.json()
        irr  = data['outputs']['totals']['fixed']['H(i)_y']
        prod = data['outputs']['totals']['fixed']['E_y']   # kWh/kWc/an
        label = 'excellent' if irr > 1600 else 'bon' if irr > 1400 else 'moyen'
        result = {'irradiance': round(irr), 'prod_kwh_kwc': round(prod), 'label': label}
        _pvgis_cache[key] = result
        return result
    except Exception:
        return {'irradiance': 1350, 'prod_kwh_kwc': 1050, 'label': 'moyen'}


def compute_solar_per_asset(asset: dict) -> dict:
    """
    Calcule le potentiel solaire d'un asset (parcelle ou bâtiment).
    Utilise la surface de l'asset pour dimensionner l'installation.
    Retourne l'asset enrichi.
    """
    lat = asset.get('lat')
    lon = asset.get('lon')
    surface = asset.get('surface_m2') or asset.get('contenance') or 0

    pvgis = pvgis_irradiance(lat, lon)

    # Règles de dimensionnement :
    # Parking : 1 kWc par 7 m² d'ombrière (couverture ~60% surface) 
    # Toiture : 1 kWc par 6 m² (couverture ~70% surface, inclinaison toit)
    type_asset = asset.get('type', 'batiment_public')
    if 'parking' in type_asset.lower():
        coeff_couverture = 0.55
        m2_par_kwc = 7
    else:
        coeff_couverture = 0.65
        m2_par_kwc = 6

    surface_utile = surface * coeff_couverture
    puissance_kwc = round(surface_utile / m2_par_kwc, 1)
    prod_annuelle_kwh = round(puissance_kwc * pvgis['prod_kwh_kwc'])
    economie_annuelle = round(prod_annuelle_kwh * 0.18)   # 18 c€/kWh
    co2_evite_kg = round(prod_annuelle_kwh * 0.055)       # 55 g/kWh mix FR

    asset['pvgis']           = pvgis
    asset['puissance_kwc']   = puissance_kwc
    asset['prod_annuelle_kwh'] = prod_annuelle_kwh
    asset['economie_annuelle'] = economie_annuelle
    asset['co2_evite_kg']    = co2_evite_kg
    asset['surface_utile_m2'] = round(surface_utile)
    return asset


# ══════════════════════════════════════════════════════════════════════════════
# 5. Diagnostic complet par commune
# ══════════════════════════════════════════════════════════════════════════════

def build_commune_diagnostic(
    code_insee: str,
    nom_commune: str,
    lat: float,
    lon: float,
    max_parcelles: int = 30,   # ignoré — conservé pour compatibilité API
    max_sections: int = 9999,  # toutes les sections MAJIC — pas de limite
) -> dict:
    """
    Diagnostic solaire basé sur la propriété foncière municipale.

    Pipeline :
      1. MAJIC (PostgreSQL) + IGN Apicarto
             → polygones des parcelles appartenant à la commune
      2. BD TOPO WFS (IGN)
             → empreintes de TOUS les bâtiments dans la bbox des parcelles
             → filtrage point-in-polygon : seuls les bâtiments SUR parcelle MAJIC
      3. GeoServer (parkings_sup500m2) + fallback Overpass
             → parkings dans la bbox des parcelles
             → filtrage point-in-polygon : seuls les parkings SUR parcelle MAJIC
      4. PVGIS  → irradiance par centroïde
      5. Calcul → puissance/production/économies sur empreinte au sol réelle

    Logique APER : l'obligation (L.171-5 CCH bâtiments, L111-19-1 CU parkings)
    ne s'applique qu'aux biens appartenant à la commune — d'où le filtrage MAJIC.
    La `contenance` cadastrale (surface foncière) n'est JAMAIS utilisée pour
    le dimensionnement solaire.
    """
    # ── 1. Parcelles MAJIC + polygones IGN Apicarto ─────────────────────────
    # Les polygones servent à DEUX choses :
    #   a) Couche cartographique (affichage)
    #   b) Filtre spatial aval — seuls les bâtiments et parkings dont le
    #      centroïde tombe dans une parcelle MAJIC sont retenus pour le calcul.
    parcelles_raw = get_parcelles_municipales(code_insee)
    # Enrichissement par section : N_sections requêtes au lieu de N_parcelles
    # Les parcelles sont déjà triées par contenance ASC (bâties en premier)
    parcelles_enriched = enrich_parcelles_with_geometry(
        code_insee, parcelles_raw,
        max_requests=max_sections
    )
    parcelles_carte = [
        {
            'type':        'parcelle_communale',
            'source':      'MAJIC + IGN',
            'id_parcelle': p.get('id_parcelle', ''),
            'denomination': p.get('denomination', 'Parcelle communale'),
            'section':     p.get('section', ''),
            'numero':      p.get('numero', ''),
            'lat':         p.get('lat'),
            'lon':         p.get('lon'),
            'surface_m2':  p.get('surface_ign') or p.get('contenance') or 0,
            'geometry':    p.get('geometry'),
        }
        for p in parcelles_enriched
        if p.get('lat') and p.get('lon')
    ]

    # ── 2. Bboxes ────────────────────────────────────────────────────────────
    # bbox_majic   : emprise des polygones parcelles MAJIC → pour les bâtiments
    # bbox_commune : contour officiel de la commune       → pour les parkings
    bbox_majic   = _bbox_parcelles(parcelles_enriched)
    bbox_commune = get_commune_bbox(code_insee, lat, lon, nom_commune=nom_commune)
    has_geoms = any(p.get('geometry') for p in parcelles_enriched)
    assets = []

    # ── 3. BD TOPO → bâtiments filtrés aux parcelles MAJIC ──────────────────
    # Stratégie : requête BD TOPO PAR SECTION (petite bbox autour de chaque
    # groupe de parcelles de même section) pour éviter qu'une bbox globale sur
    # une grande ville retourne 2000 bâtiments aléatoires dont aucun n'est
    # municipal. Une bbox par section (≈ quelques rues) garantit l'exhaustivité.
    if has_geoms:
        from collections import defaultdict as _dd
        by_section_geom = _dd(list)
        for p in parcelles_enriched:
            if p.get('geometry'):
                by_section_geom[p.get('section', 'XX')].append(p)
        batiments = []
        seen_bat = set()
        for sect_parcelles in by_section_geom.values():
            bbox_sect = _bbox_parcelles(sect_parcelles)
            if not bbox_sect:
                continue
            for b in get_batiments_bdtopo_bbox(bbox_sect, max_features=500):
                key = (round(b['lat'], 6), round(b['lon'], 6))
                if key in seen_bat:
                    continue
                pid = _find_parcel_id(b['lon'], b['lat'], sect_parcelles)
                if pid:
                    b['id_parcelle'] = pid
                    batiments.append(b)
                    seen_bat.add(key)
        assets.extend(batiments)
    elif bbox_majic:
        # Pas de géométries : requête bbox globale sans filtre PIP
        assets.extend(get_batiments_bdtopo_bbox(bbox_majic))

    # ── 4. Parkings (GeoServer) filtrés aux parcelles MAJIC ─────────────────
    # Source principale : couche GeoServer `parkings_sup500m2` (France entière,
    # données propres, > 500 m²). Fallback Overpass si GeoServer inaccessible.
    # L'obligation APER L111-19-1 CU ne vise que les parkings appartenant à la
    # commune — filtrage PIP sur parcelles MAJIC appliqué ensuite.
    bbox_pk = bbox_commune or bbox_majic
    if bbox_pk:
        parkings_raw = get_parkings_geoserver_bbox(bbox_pk)
        if not parkings_raw:
            logger.info(f"GeoServer parkings vide pour {code_insee}, fallback Overpass")
            parkings_raw = get_parkings_osm_bbox(bbox_pk)
        if has_geoms:
            parkings = []
            for p in parkings_raw:
                pid = _find_parcel_id(p['lon'], p['lat'], parcelles_enriched)
                if pid:
                    p['id_parcelle'] = pid
                    parkings.append(p)
        else:
            parkings = parkings_raw   # pas de polygones MAJIC : garder la bbox
        assets.extend(parkings)

    # Fallback si MAJIC inaccessible et aucun résultat
    if not assets and lat and lon:
        logger.warning(f"Fallback centroïde commune pour {code_insee}")
        assets.extend(get_batiments_publics_osm(lat, lon, rayon_m=2000))
        assets.extend(get_parkings_osm(lat, lon, rayon_m=3000)[:20])

    # ── 5. Calcul solaire sur les empreintes réelles ─────────────────────────
    # Bâtiments BDTOPO : empreinte au sol → ratio 0.65 / 6 m²/kWc
    # Parkings OSM     : surface au sol   → ratio 0.55 / 7 m²/kWc (ombrières)
    assets_with_solar = []
    for asset in assets:
        t    = asset.get('type', '')
        surf = (asset.get('surface_m2', 0) or 0)
        # Filtres légaux Art. L.171-5 CCH
        if t == 'batiment_public' and surf < SEUIL_BATIMENT_M2:
            continue
        if 'parking' in t and surf < SEUIL_PARKING_M2:
            continue
        if asset.get('lat') and asset.get('lon') and surf > 50:
            asset = compute_solar_per_asset(asset)
        assets_with_solar.append(asset)

    # ── 6. Synthèse ─────────────────────────────────────────────────────────
    nb_parcelles  = len(parcelles_carte)
    nb_parkings   = sum(1 for a in assets_with_solar if 'parking' in a['type'])
    nb_batiments  = sum(1 for a in assets_with_solar if a['type'] == 'batiment_public')
    puissance_tot = round(sum(a.get('puissance_kwc', 0) for a in assets_with_solar), 1)
    prod_tot      = sum(a.get('prod_annuelle_kwh', 0) for a in assets_with_solar)
    economie_tot  = sum(a.get('economie_annuelle', 0) for a in assets_with_solar)
    co2_tot       = sum(a.get('co2_evite_kg', 0) for a in assets_with_solar)

    pvgis_global = pvgis_irradiance(lat, lon)

    return {
        'code_insee':           code_insee,
        'nom_commune':          nom_commune,
        'lat':                  lat,
        'lon':                  lon,
        'assets':               assets_with_solar,
        'parcelles_carte':      parcelles_carte,
        'nb_parcelles':         nb_parcelles,
        'nb_parkings':          nb_parkings,
        'nb_batiments':         nb_batiments,
        'puissance_totale_kwc': puissance_tot,
        'prod_totale_kwh':      prod_tot,
        'economie_totale':      economie_tot,
        'co2_evite_kg':         co2_tot,
        'irradiance':           pvgis_global['irradiance'],
        'ensoleillement':       pvgis_global['label'],
    }


# ══════════════════════════════════════════════════════════════════════════════
# 6. Carte statique (thumbnail email)
# ══════════════════════════════════════════════════════════════════════════════

def generate_map_thumbnail(diagnostic: dict, width: int = 560, height: int = 280) -> str:
    """
    Génère une miniature PNG de la carte (fond OSM + polygones couleur)
    et retourne une data-URI base64 prête à insérer dans un <img src="...">.
    La vue est centrée sur les actifs solaires (bâtiments + parkings) à zoom 15.
    Retourne '' si staticmap n'est pas disponible.
    """
    try:
        from staticmap import StaticMap, Polygon as SMP, CircleMarker as SMCM
        import base64, io, math
    except ImportError:
        logger.debug("staticmap non disponible — thumbnail désactivé")
        return ''

    try:
        # ── Sélectionner l'asset principal (max kWc) comme centre de la carte ──
        # On zoome sur LE site le plus puissant, pas sur la moyenne des assets
        assets = diagnostic.get('assets', [])
        asset_lats, asset_lons = [], []

        # Trier les assets par puissance décroissante
        assets_sorted = sorted(assets, key=lambda a: a.get('puissance_kwc', 0), reverse=True)

        # Collecter les coords de TOUS les assets pour les afficher
        for asset in assets:
            alat = asset.get('lat')
            alon = asset.get('lon')
            if alat and alon:
                asset_lats.append(alat)
                asset_lons.append(alon)

        # Centre = centroïde du TOP 3 assets (les plus puissants)
        clat = diagnostic.get('lat', 46.5)
        clon = diagnostic.get('lon', 2.3)
        top_assets = [a for a in assets_sorted if a.get('lat') and a.get('lon')][:3]
        if top_assets:
            clat = sum(a['lat'] for a in top_assets) / len(top_assets)
            clon = sum(a['lon'] for a in top_assets) / len(top_assets)
        elif asset_lats:
            clat = sum(asset_lats) / len(asset_lats)
            clon = sum(asset_lons) / len(asset_lons)

        # ── Zoom calibré sur les top assets, pas sur toute la commune ────────
        if top_assets:
            if len(top_assets) == 1:
                # 1 seul asset → zoom serré sur sa superficie
                surf = top_assets[0].get('surface_m2', 0) or 0
                # surface → rayon approx → zoom
                if surf > 10000:
                    zoom = 15
                elif surf > 2000:
                    zoom = 16
                else:
                    zoom = 17
            else:
                top_lats = [a['lat'] for a in top_assets]
                top_lons = [a['lon'] for a in top_assets]
                lat_span = max(top_lats) - min(top_lats)
                lon_span = max(top_lons) - min(top_lons)
                max_span = max(lat_span, lon_span)
                if max_span > 0:
                    import math
                    zoom = max(14, min(17, int(math.log2(0.18 / max_span)) + 14))
                else:
                    zoom = 16
        elif asset_lats:
            import math
            lat_span = max(asset_lats) - min(asset_lats)
            lon_span = max(asset_lons) - min(asset_lons)
            max_span = max(lat_span, lon_span)
            zoom = max(13, min(16, int(math.log2(0.18 / max_span)) + 14)) if max_span > 0 else 15
        else:
            zoom = 14

        m = StaticMap(width, height,
                      url_template='https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                      padding_x=10, padding_y=10)

        def _add_poly(coords_lonlat, fill_color, outline_color, simplify=True):
            if not coords_lonlat or len(coords_lonlat) < 3:
                return
            if simplify and len(coords_lonlat) > 80:
                step = max(1, len(coords_lonlat) // 80)
                coords_lonlat = coords_lonlat[::step]
            pts = [(float(c[0]), float(c[1])) if isinstance(c, (list, tuple))
                   else (float(c['lon']), float(c['lat']))
                   for c in coords_lonlat]
            try:
                m.add_polygon(SMP(pts, fill_color, outline_color, simplify=False))
            except Exception:
                pass

        # Calcul bbox assets (avec buffer ~500m ≈ 0.005°)
        buf_deg = 0.006
        if asset_lats:
            bbox_minlat = min(asset_lats) - buf_deg
            bbox_maxlat = max(asset_lats) + buf_deg
            bbox_minlon = min(asset_lons) - buf_deg
            bbox_maxlon = max(asset_lons) + buf_deg
        else:
            d = 0.01
            bbox_minlat, bbox_maxlat = clat - d, clat + d
            bbox_minlon, bbox_maxlon = clon - d, clon + d

        # ── Parcelles MAJIC dans la bbox actifs (vert) ───────────────────────
        for p in diagnostic.get('parcelles_carte', []):
            plat = p.get('lat') or 0
            plon = p.get('lon') or 0
            # N'afficher que les parcelles proches des actifs
            if not (bbox_minlat <= plat <= bbox_maxlat and bbox_minlon <= plon <= bbox_maxlon):
                continue
            geom = p.get('geometry')
            if not geom:
                continue
            gtype = geom.get('type', '')
            coords = geom.get('coordinates', [])
            if gtype == 'Polygon' and coords:
                _add_poly(coords[0], '#10b98140', '#10b981')
            elif gtype == 'MultiPolygon':
                for poly in coords:
                    if poly:
                        _add_poly(poly[0], '#10b98140', '#10b981')

        # ── Assets solaires ──────────────────────────────────────────────────
        for asset in diagnostic.get('assets', []):
            atype = asset.get('type', '')
            geom_osm = asset.get('geometry_osm')
            geom_bdtopo = asset.get('geometry')

            if 'parking' in atype:
                if geom_osm:
                    pts = [(g['lon'], g['lat']) for g in geom_osm]
                    _add_poly(pts, '#0ea5e955', '#0ea5e9')
                else:
                    alat, alon = asset.get('lat'), asset.get('lon')
                    if alat and alon:
                        m.add_marker(SMCM((alon, alat), '#0ea5e9', 10))

            elif atype == 'batiment_public':
                if geom_bdtopo:
                    gtype = geom_bdtopo.get('type', '')
                    coords = geom_bdtopo.get('coordinates', [])
                    if gtype == 'Polygon' and coords:
                        _add_poly(coords[0], '#f9731699', '#f97316')
                    elif gtype == 'MultiPolygon':
                        for poly in coords:
                            if poly:
                                _add_poly(poly[0], '#f9731699', '#f97316')
                elif geom_osm:
                    pts = [(g['lon'], g['lat']) for g in geom_osm]
                    _add_poly(pts, '#f9731699', '#f97316')
                else:
                    alat, alon = asset.get('lat'), asset.get('lon')
                    if alat and alon:
                        m.add_marker(SMCM((alon, alat), '#f97316', 12))

        img = m.render(zoom=zoom, center=(clon, clat))
        buf = io.BytesIO()
        img.save(buf, format='PNG', optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        return f'data:image/png;base64,{b64}'

    except Exception as e:
        logger.warning(f"generate_map_thumbnail error: {e}")
        return ''


# ══════════════════════════════════════════════════════════════════════════════
# 7. Carte Folium interactive
# ══════════════════════════════════════════════════════════════════════════════

def generate_map_html(diagnostic: dict) -> str:
    """
    Génère une carte Folium HTML complète montrant :
    - Les parcelles communales (vert = potentiel bon, orange = moyen)
    - Les parkings (bleu marine avec ombrière)
    - Les bâtiments publics (violet)
    - Popup détaillé pour chaque asset
    Retourne la chaîne HTML.
    """
    try:
        import folium
        from folium.plugins import MiniMap, Fullscreen
    except ImportError:
        return _map_html_fallback(diagnostic)

    lat = diagnostic.get('lat') or 46.5
    lon = diagnostic.get('lon') or 2.3
    nom = diagnostic.get('nom_commune', 'Commune')

    # Centrer sur les assets solaires (top 3 par puissance), pas sur la commune
    assets_with_coords = [(a['lat'], a['lon'], a.get('puissance_kwc', 0))
                          for a in diagnostic.get('assets', [])
                          if a.get('lat') and a.get('lon')]
    assets_with_coords.sort(key=lambda x: x[2], reverse=True)  # tri par kWc desc
    if assets_with_coords:
        top3 = assets_with_coords[:3]
        lat = sum(a[0] for a in top3) / len(top3)
        lon = sum(a[1] for a in top3) / len(top3)

    m = folium.Map(
        location=[lat, lon],
        zoom_start=16,
        tiles=None,
    )

    # fit_bounds sur tous les assets si plusieurs sites éloignés
    if len(assets_with_coords) > 1:
        all_lats = [a[0] for a in assets_with_coords]
        all_lons = [a[1] for a in assets_with_coords]
        # Ajouter un léger padding (0.001°)
        m.fit_bounds(
            [[min(all_lats) - 0.003, min(all_lons) - 0.003],
             [max(all_lats) + 0.003, max(all_lons) + 0.003]]
        )

    # Fonds de carte — le dernier ajouté est actif par défaut
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
        attr='© CartoDB © OpenStreetMap contributors',
        name='Plan (CartoDB)',
        subdomains='abcd',
        max_zoom=20,
        show=False,
    ).add_to(m)

    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        attr='© CartoDB © OpenStreetMap contributors',
        name='Plan sombre (CartoDB)',
        subdomains='abcd',
        max_zoom=20,
        show=False,
    ).add_to(m)

    # Satellite IGN — ajouté EN DERNIER = fond actif par défaut
    folium.TileLayer(
        tiles='https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0'
              '&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal&FORMAT=image/jpeg'
              '&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
        attr='© IGN Géoportail',
        name='Satellite IGN',
        max_zoom=20,
        show=True,
    ).add_to(m)

    # Groupes de couches
    grp_parcelles  = folium.FeatureGroup(name='🟢 Parcelles communales (MAJIC)', show=True)
    grp_batiments  = folium.FeatureGroup(name='⚖️ Bâtiments publics ≥500m² — Jan. 2028', show=True)
    grp_parkings   = folium.FeatureGroup(name='⚠️ Parkings 1 500–10 000m² — Juil. 2028', show=True)
    grp_urgents    = folium.FeatureGroup(name='🔴 Parkings >10 000m² — URGENT juil. 2026', show=True)

    COLOR_SOLAR = {
        'excellent': '#16a34a',
        'bon':       '#2563eb',
        'moyen':     '#d97706',
    }

    def _legal_badge_bat(surf):
        """Badge obligation légale bâtiment public."""
        if surf >= 500:
            return (
                '<div style="margin-top:8px;padding:6px 8px;background:#eff6ff;'
                'border-left:3px solid #2563eb;border-radius:4px;font-size:11px;">'
                '<b style="color:#1d4ed8">⚖️ Obligation légale — Art. L.171-5 CCH</b><br>'
                '<span style="color:#374151">Solarisation toiture requise d\'ici le '
                '<b>1er janvier 2028</b></span></div>'
            )
        return ''

    def _legal_badge_parking(surf):
        """Badge obligation légale parking, avec niveau d'urgence."""
        if surf > 10000:
            return (
                '<div style="margin-top:8px;padding:6px 8px;background:#fef2f2;'
                'border-left:3px solid #dc2626;border-radius:4px;font-size:11px;">'
                '<b style="color:#dc2626">🔴 CRITIQUE — Art. L.111-19-1 CU (Loi APER art.40)</b><br>'
                '<span style="color:#374151">Ombrières PV sur ≥50% de la surface requises au '
                '<b>1er juillet 2026 — échéance dans 3 mois</b></span></div>'
            )
        elif surf >= 1500:
            return (
                '<div style="margin-top:8px;padding:6px 8px;background:#fffbeb;'
                'border-left:3px solid #d97706;border-radius:4px;font-size:11px;">'
                '<b style="color:#b45309">⚠️ Obligation légale — Art. L.111-19-1 CU (Loi APER art.40)</b><br>'
                '<span style="color:#374151">Ombrières PV sur ≥50% de la surface requises au '
                '<b>1er juillet 2028</b></span></div>'
            )
        return ''

    # ── Couche A : Parcelles MAJIC (propriété communale, sans calcul solaire) ──
    for p in diagnostic.get('parcelles_carte', []):
        plat = p.get('lat')
        plon = p.get('lon')
        if not plat or not plon:
            continue
        denom = p.get('denomination', 'Parcelle')
        sect  = p.get('section', '')
        num   = p.get('numero', '')
        surf  = p.get('surface_m2', 0) or 0
        popup_parc = f"""
<div style="font-family:Arial;font-size:13px;min-width:180px">
  <b style="color:#10b981">{denom}</b><br>
  <hr style="margin:4px 0;border-color:#e2e8f0">
  <table style="width:100%;font-size:12px">
    <tr><td>Parcelle</td><td><b>{sect} {num}</b></td></tr>
    <tr><td>Surface</td><td><b>{surf:,} m²</b></td></tr>
  </table>
  <small style="color:#94a3b8">Source : MAJIC cadastral</small>
</div>"""
        geom = p.get('geometry')
        if geom:
            _add_geojson_polygon(grp_parcelles, geom, '#10b981', popup_parc, opacity=0.25)
        else:
            folium.CircleMarker(
                [plat, plon], radius=6, color='#10b981', fill=True,
                fill_opacity=0.4, popup=folium.Popup(popup_parc, max_width=240),
                tooltip=f"{denom} — {sect}{num}"
            ).add_to(grp_parcelles)

    # ── Couches B+C+D : Assets solaires (bâtiments BDTOPO + parkings GeoServer) ──
    for asset in diagnostic.get('assets', []):
        atype = asset.get('type', '')
        alat  = asset.get('lat')
        alon  = asset.get('lon')
        if not alat or not alon:
            continue

        surf    = asset.get('surface_m2', 0) or 0
        puiss   = asset.get('puissance_kwc', 0)
        prod    = asset.get('prod_annuelle_kwh', 0)
        eco     = asset.get('economie_annuelle', 0)
        label   = asset.get('pvgis', {}).get('label', 'moyen')
        color   = COLOR_SOLAR.get(label, '#64748b')
        name    = asset.get('denomination') or asset.get('name', '')
        parcelle_id = asset.get('id_parcelle', '')

        # Libellé source selon type d'asset
        if 'parking' in atype:
            src = 'GeoServer (parkings_sup500m2) · Parcelle MAJIC'
        else:
            src = 'BD TOPO IGN · Parcelle MAJIC'

        if atype == 'batiment_public':
            legal_html = _legal_badge_bat(surf)
            tooltip_prefix = '⚖️ '
            park_color = color
        elif 'parking' in atype and surf > 10000:
            legal_html = _legal_badge_parking(surf)
            tooltip_prefix = '🔴 '
            park_color = '#dc2626'
        elif 'parking' in atype:
            legal_html = _legal_badge_parking(surf)
            tooltip_prefix = '⚠️ '
            park_color = '#0ea5e9'
        else:
            legal_html = ''
            tooltip_prefix = ''
            park_color = color

        parcelle_row = (
            f'<tr><td>Parcelle MAJIC</td><td><b style="font-family:monospace">{parcelle_id}</b></td></tr>'
            if parcelle_id else ''
        )

        popup_html = f"""
<div style="font-family:Arial;font-size:13px;min-width:220px">
  <b style="color:{park_color}">{tooltip_prefix}{name}</b><br>
  <hr style="margin:4px 0;border-color:#e2e8f0">
  <table style="width:100%;font-size:12px">
    {parcelle_row}
    <tr><td>Empreinte</td><td><b>{surf:,} m²</b></td></tr>
    <tr><td>Puissance</td><td><b>{puiss} kWc</b></td></tr>
    <tr><td>Production</td><td><b>{prod:,} kWh/an</b></td></tr>
    <tr><td>Économies</td><td><b style="color:#16a34a">{eco:,} €/an</b></td></tr>
    <tr><td>Irradiance</td><td>{asset.get('pvgis', {}).get('irradiance', '')} kWh/m²/an</td></tr>
  </table>
  {legal_html}
  <small style="color:#94a3b8">Source : {src}</small>
</div>"""

        if atype == 'batiment_public':
            geom = asset.get('geometry')
            geom_osm = asset.get('geometry_osm')
            if geom:
                _add_geojson_polygon(grp_batiments, geom, color, popup_html)
            elif geom_osm:
                _add_osm_polygon(grp_batiments, geom_osm, color, popup_html)
            else:
                folium.CircleMarker(
                    [alat, alon], radius=9, color=color, fill=True,
                    fill_opacity=0.75, popup=folium.Popup(popup_html, max_width=280),
                    tooltip=f"⚖️ {name}"
                ).add_to(grp_batiments)

        elif 'parking' in atype:
            geom_osm = asset.get('geometry_osm')
            if surf > 10000:
                # Parking URGENT 2026 → couche rouge séparée
                if geom_osm:
                    _add_osm_polygon(grp_urgents, geom_osm, '#dc2626', popup_html)
                else:
                    folium.CircleMarker(
                        [alat, alon], radius=14, color='#dc2626', fill=True,
                        fill_opacity=0.85, popup=folium.Popup(popup_html, max_width=280),
                        tooltip=f"🔴 URGENT 2026 — {name} ({surf:,} m²)"
                    ).add_to(grp_urgents)
            else:
                # Parking 2028 → couche bleue standard
                if geom_osm:
                    _add_osm_polygon(grp_parkings, geom_osm, '#0ea5e9', popup_html)
                else:
                    folium.CircleMarker(
                        [alat, alon], radius=10, color='#0ea5e9', fill=True,
                        fill_opacity=0.75, popup=folium.Popup(popup_html, max_width=280),
                        tooltip=f"⚠️ {name} — {surf:,} m²"
                    ).add_to(grp_parkings)

    grp_urgents.add_to(m)    # en premier = visible au-dessus
    grp_parcelles.add_to(m)
    grp_batiments.add_to(m)
    grp_parkings.add_to(m)

    folium.LayerControl(position='topright').add_to(m)
    MiniMap(toggle_display=True).add_to(m)
    Fullscreen().add_to(m)

    return m._repr_html_()


def _add_geojson_polygon(group, geometry: dict, color: str, popup_html: str, opacity=0.8):
    """Ajoute un polygone GeoJSON (IGN) sur une FeatureGroup."""
    try:
        import folium
        geojson_feature = {'type': 'Feature', 'geometry': geometry, 'properties': {}}
        folium.GeoJson(
            geojson_feature,
            style_function=lambda x, c=color: {
                'fillColor': c, 'color': c, 'weight': 2,
                'fillOpacity': opacity, 'opacity': 1
            },
            popup=folium.Popup(popup_html, max_width=260),
        ).add_to(group)
    except Exception as e:
        logger.debug(f"GeoJSON polygon error: {e}")


def _add_osm_polygon(group, geom_osm: list, color: str, popup_html: str):
    """Ajoute un polygone OSM (liste de {lat,lon}) sur une FeatureGroup."""
    try:
        import folium
        coords = [[g['lon'], g['lat']] for g in geom_osm]
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        geojson_feature = {
            'type': 'Feature',
            'geometry': {'type': 'Polygon', 'coordinates': [coords]},
            'properties': {}
        }
        folium.GeoJson(
            geojson_feature,
            style_function=lambda x, c=color: {
                'fillColor': c, 'color': c, 'weight': 2,
                'fillOpacity': 0.6, 'opacity': 1
            },
            popup=folium.Popup(popup_html, max_width=260),
        ).add_to(group)
    except Exception as e:
        logger.debug(f"OSM polygon error: {e}")


def _map_html_fallback(diagnostic: dict) -> str:
    """Carte légère sans folium (Leaflet CDN)."""
    lat = diagnostic.get('lat', 46.5)
    lon = diagnostic.get('lon', 2.3)
    nom = diagnostic.get('nom_commune', 'Commune')
    assets_js = json.dumps([
        {
            'lat': a['lat'], 'lon': a['lon'],
            'type': a.get('type', ''), 'name': a.get('denomination') or a.get('name', ''),
            'surface': a.get('surface_m2', 0), 'eco': a.get('economie_annuelle', 0),
        }
        for a in diagnostic.get('assets', []) if a.get('lat') and a.get('lon')
    ])
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body{{height:100%;margin:0}}#map{{height:100%}}</style>
</head><body>
<div id="map"></div>
<script>
var map=L.map('map').setView([{lat},{lon}],15);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{attribution:'© OpenStreetMap'}}).addTo(map);
var assets={assets_js};
var colors={{'parcelle_communale':'#16a34a','parking_osm':'#1e40af','batiment_public':'#7c3aed'}};
assets.forEach(function(a){{
  var c=colors[a.type]||'#64748b';
  L.circleMarker([a.lat,a.lon],{{radius:10,color:c,fillColor:c,fillOpacity:.75}})
   .bindPopup('<b>'+a.name+'</b><br>'+a.surface+' m² — '+a.eco+' €/an').addTo(map);
}});
</script></body></html>"""


# ══════════════════════════════════════════════════════════════════════════════
# 7. Résumé JSON (pour email + stockage BDD)
# ══════════════════════════════════════════════════════════════════════════════

def diagnostic_summary(diag: dict) -> dict:
    """Version allégée du diagnostic pour stocker dans la colonne JSON."""
    top_assets = sorted(
        [a for a in diag.get('assets', []) if a.get('economie_annuelle', 0) > 0],
        key=lambda x: x.get('economie_annuelle', 0), reverse=True
    )[:5]

    return {
        'nb_parcelles':         diag['nb_parcelles'],
        'nb_parkings':          diag['nb_parkings'],
        'nb_batiments':         diag['nb_batiments'],
        'puissance_totale_kwc': diag['puissance_totale_kwc'],
        'prod_totale_kwh':      diag['prod_totale_kwh'],
        'economie_totale':      diag['economie_totale'],
        'co2_evite_kg':         diag['co2_evite_kg'],
        'irradiance':           diag['irradiance'],
        'ensoleillement':       diag['ensoleillement'],
        'top_assets': [
            {
                'type': a['type'], 'name': a.get('denomination') or a.get('name', ''),
                'surface_m2': a.get('surface_m2', 0),
                'puissance_kwc': a.get('puissance_kwc', 0),
                'economie_annuelle': a.get('economie_annuelle', 0),
                'id_parcelle': a.get('id_parcelle', ''),
            }
            for a in top_assets
        ]
    }
