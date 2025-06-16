import requests
from shapely.geometry import Point, shape
from pyproj import Transformer
import folium
from pyproj import Transformer

def get_coordinates(lat, lon, from_crs="EPSG:4326", to_crs="EPSG:2154"):
    """
    Transforme les coordonnées entre deux systèmes de référence spatiale.

    Args:
        lat (float): Latitude.
        lon (float): Longitude.
        from_crs (str): Code EPSG du système de référence source.
        to_crs (str): Code EPSG du système de référence cible.

    Returns:
        tuple: Coordonnées transformées (x, y).
    """
    transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
    x, y = transformer.transform(lon, lat)
    return x, y


# Configuration GeoServer
GEOSERVER_URL = "http://localhost:8080/geoserver"
CADASTRE_LAYER = "gpu:prefixes_sections"
PARCELLE_LAYER = "gpu:PARCELLE2024"
POSTE_LAYER = "gpu:poste_elec_shapefile"
def get_coordinates(lat, lon, from_crs="EPSG:4326", to_crs="EPSG:2154"):
    """
    Transforme les coordonnées entre deux systèmes de référence spatiale.
    """
    transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
    x, y = transformer.transform(lon, lat)
    return x, y
def fetch_wfs_data(layer, bbox, srsname="EPSG:4326"):
    """
    Récupère les données WFS d'une couche GeoServer.
    """
    wfs_url = f"{GEOSERVER_URL}/wfs"
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": layer,
        "outputFormat": "application/json",
        "srsname": srsname,
        "bbox": bbox,
    }
    response = requests.get(wfs_url, params=params)
    if response.status_code == 200:
        return response.json().get("features", [])
    print(f"Erreur WFS : {response.status_code} - {response.text}")
    return []

def get_parcelle_info(lat, lon):
    """
    Récupère toutes les parcelles contenant le point (lat, lon).
    """
    bbox = f"{lon-0.001},{lat-0.001},{lon+0.001},{lat+0.001},EPSG:4326"
    features = fetch_wfs_data(CADASTRE_LAYER, bbox)
    point = Point(lon, lat)
    parcelles = []
    for feature in features:
        geom = shape(feature["geometry"])
        if geom.contains(point):
            # On renvoie le GeoJSON complet (geometry et properties)
            parcelles.append({
                "type": "Feature",
                "geometry": feature["geometry"],
                "properties": feature["properties"]
            })
    return parcelles  # retourne une liste (tu peux faire {type:FeatureCollection} côté JS)


def get_plu_info(lat, lon, radius=0.05):
    bbox = f"{lon-radius},{lat-radius},{lon+radius},{lat+radius},EPSG:4326"
    features = fetch_wfs_data("gpu:gpu1", bbox)
    plu_features = []
    for feature in features:
        plu_features.append({
            "type": "Feature",
            "geometry": feature["geometry"],
            "properties": feature["properties"]
        })
    return plu_features


def get_all_parcelles(lat, lon, radius=0.01):
    """
    Récupère toutes les parcelles dans un rayon donné autour d'une position.
    """
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
    x, y = transformer.transform(lon, lat)
    bbox = f"{x-radius*111000},{y-radius*111000},{x+radius*111000},{y+radius*111000},EPSG:2154"
    features = fetch_wfs_data(PARCELLE_LAYER, bbox)
    return {"features": features}  # Retourne les parcelles au format GeoJSON

def get_nearest_postes(lat, lon, radius=0.1):
    bbox = f"{lon-radius},{lat-radius},{lon+radius},{lat+radius},EPSG:4326"
    features = fetch_wfs_data(POSTE_LAYER, bbox)
    postes = []
    point = Point(lon, lat)
    for feature in features:
        geom = shape(feature["geometry"])
        distance = geom.distance(point) * 111000
        f = {
            "type": "Feature",
            "geometry": feature["geometry"],
            "properties": {**feature["properties"], "distance": round(distance, 2)}
        }
        postes.append(f)
    # Retourne les 3 plus proches (Feature)
    return sorted(postes, key=lambda x: x["properties"]["distance"])[:3]


def add_wms_layer(map_obj, layer_name):
    """
    Ajoute une couche WMS à une carte Folium.
    """
    folium.raster_layers.WmsTileLayer(
        url=f"{GEOSERVER_URL}/wms",
        layers=layer_name,
        fmt="image/png",
        transparent=True,
        name=layer_name,
        overlay=True,
        control=True,
    ).add_to(map_obj)
