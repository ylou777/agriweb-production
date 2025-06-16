import os
import logging
from flask import Flask, jsonify, request
from urllib.parse import quote, quote_plus
from geopy.geocoders import Nominatim
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import unicodedata
from functools import lru_cache
from shapely.geometry import shape, mapping, Point
from shapely.ops import transform
from pyproj import Transformer
import folium
import geopandas as gpd
import json
import time

# --- Configuration ---
app = Flask(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

CONFIG = {
    "GEOSERVER_URL": os.getenv("GEOSERVER_URL", "http://localhost:8080/geoserver"),
    "GEOSERVER_WFS_URL": os.getenv("GEOSERVER_WFS_URL", "http://localhost:8080/geoserver/wfs"),
    "ELEVATION_API_URL": os.getenv("ELEVATION_API_URL", "https://api.elevationapi.com/api/Elevation"),
    "PVGIS_API_URL": os.getenv("PVGIS_API_URL", "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc"),
    "GEO_API_GOUVERNEMENT": os.getenv("GEO_API_GOUVERNEMENT", "https://geo.api.gouv.fr"),
    "API_ADRESSE": os.getenv("API_ADRESSE", "https://api-adresse.data.gouv.fr"),
    "LAYERS": {
        "PARCELLE": "gpu:PARCELLE",
        "POSTE_BT": "gpu:poste_elec_shapefile",
        "POSTE_HTA": "gpu:hta_milieu",
        "RPG": "gpu:RPG",
        "PLU": "gpu:PLU",
        "PARKINGS": "gpu:parkings",
        "FRICHES": "gpu:friches",
        "ZAER": "gpu:ZAER",
        "SIRENE": "gpu:sirene",
    }
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    filename="agriweb.log",
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configure requests session with retries
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

# --- Utility Functions ---
def normalize_address(address):
    """Normalize address input by removing extra spaces and normalizing accents."""
    if not address:
        return None
    address = " ".join(address.strip().split())
    address = unicodedata.normalize("NFKD", address).encode("ASCII", "ignore").decode("ASCII")
    return address

@lru_cache(maxsize=1000)
def geocode_address_geoapi(address, timeout=10):
    """Geocode an address using Géo API Gouv."""
    try:
        url = f"{CONFIG['API_ADRESSE']}/search/?q={quote_plus(address)}&limit=1"
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features", [])
        if not features:
            return None
        geom = features[0].get("geometry", {}).get("coordinates", [])
        if len(geom) != 2:
            return None
        lon, lat = geom
        return lat, lon
    except Exception as e:
        logger.error(f"Géo API Gouv geocoding failed for '{address}': {e}")
        return None

@lru_cache(maxsize=1000)
def geocode_address_nominatim(address, timeout=10):
    """Fallback geocoding using Nominatim."""
    try:
        geolocator = Nominatim(user_agent="agriweb", timeout=timeout)
        location = geolocator.geocode(address, country_codes="fr")
        if location:
            return location.latitude, location.longitude
        return None
    except Exception as e:
        logger.error(f"Nominatim geocoding failed for '{address}': {e}")
        return None

def geocode_address(address):
    """Geocode an address using Géo API Gouv with Nominatim fallback."""
    normalized = normalize_address(address)
    if not normalized:
        logger.error("Empty or invalid address provided")
        return None
    coords = geocode_address_geoapi(normalized)
    if coords:
        logger.info(f"Geocoded '{normalized}' to {coords} using Géo API Gouv")
        return coords
    time.sleep(1)  # Respect Nominatim's rate limit
    coords = geocode_address_nominatim(normalized)
    if coords:
        logger.info(f"Geocoded '{normalized}' to {coords} using Nominatim")
        return coords
    logger.warning(f"Geocoding failed for '{normalized}'")
    return None

def validate_coordinates(lat, lon):
    """Validate latitude and longitude, ensuring they are within France's bounds."""
    try:
        lat, lon = float(lat), float(lon)
        if not (41 <= lat <= 51) or not (-5 <= lon <= 9):
            logger.warning(f"Coordinates ({lat}, {lon}) outside France's bounds")
            return None
        return lat, lon
    except (ValueError, TypeError):
        logger.error(f"Invalid coordinates: lat={lat}, lon={lon}")
        return None

def to_feature_collection(data):
    """Convert data to GeoJSON FeatureCollection."""
    if not data:
        return {"type": "FeatureCollection", "features": []}
    if isinstance(data, dict) and data.get("type") == "FeatureCollection":
        return data
    if isinstance(data, list):
        feats = [f for f in data if isinstance(f, dict) and f.get("type") == "Feature"]
        return {"type": "FeatureCollection", "features": feats}
    return {"type": "FeatureCollection", "features": []}

def fetch_wfs_data(layer_name, bbox, srsname="EPSG:4326"):
    """Fetch data from GeoServer WFS."""
    try:
        layer_q = quote(layer_name, safe=':')
        url = f"{CONFIG['GEOSERVER_WFS_URL']}?service=WFS&version=2.0.0&request=GetFeature&typeName={layer_q}&outputFormat=application/json&bbox={bbox}&srsname={srsname}"
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        if 'xml' in resp.headers.get('Content-Type', ''):
            logger.error(f"Received XML response for {layer_name}: {resp.text[:200]}")
            return []
        return resp.json().get('features', [])
    except Exception as e:
        logger.error(f"Error fetching WFS data for {layer_name}: {e}")
        return []

def get_all_parcelles(lat, lon, radius=0.03):
    """Fetch all parcels within a radius."""
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius}"
    return to_feature_collection(fetch_wfs_data(CONFIG["LAYERS"]["PARCELLE"], bbox))

def get_parcelle_info(lat, lon):
    """Fetch information for the parcel containing the point."""
    point = Point(lon, lat)
    parcelles = get_all_parcelles(lat, lon)
    for feature in parcelles["features"]:
        poly = shape(feature["geometry"])
        if poly.contains(point):
            return feature["properties"]
    return {}

def get_nearest_postes(lat, lon, radius_deg=0.009):
    """Fetch nearest BT postes."""
    bbox = f"{lon - radius_deg},{lat - radius_deg},{lon + radius_deg},{lat + radius_deg}"
    return to_feature_collection(fetch_wfs_data(CONFIG["LAYERS"]["POSTE_BT"], bbox))

def get_nearest_ht_postes(lat, lon, radius_deg=0.009):
    """Fetch nearest HTA postes."""
    bbox = f"{lon - radius_deg},{lat - radius_deg},{lon + radius_deg},{lat + radius_deg}"
    return to_feature_collection(fetch_wfs_data(CONFIG["LAYERS"]["POSTE_HTA"], bbox))

def get_rpg_info(lat, lon, radius=0.0027):
    """Fetch RPG (agricultural) data."""
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius}"
    return to_feature_collection(fetch_wfs_data(CONFIG["LAYERS"]["RPG"], bbox))

def get_plu_info(lat, lon, radius=0.03):
    """Fetch PLU (urban planning) data."""
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius}"
    return to_feature_collection(fetch_wfs_data(CONFIG["LAYERS"]["PLU"], bbox))

def get_api_cadastre_data(geom_point):
    """Fetch cadastre data from IGN API."""
    try:
        url = "https://apicarto.ign.fr/api/cadastre/parcelle"
        resp = session.post(url, json=geom_point, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Error fetching cadastre data: {e}")
        return {}

def get_pvgis_production(lat, lon, tilt=30, azimuth=180, peakpower=1.0):
    """Fetch solar production data from PVGIS."""
    try:
        params = {
            "lat": lat,
            "lon": lon,
            "peakpower": peakpower,
            "mountingplace": "free",
            "angle": tilt,
            "aspect": azimuth,
            "loss": 14,
            "outputformat": "json"
        }
        resp = session.get(CONFIG["PVGIS_API_URL"], params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("outputs", {}).get("totals", {}).get("fixed", {}).get("E_y", None)
    except Exception as e:
        logger.error(f"Error fetching PVGIS data for lat={lat}, lon={lon}: {e}")
        return None

def build_map(lat, lon, address, parcelle, parcelles_data, postes_bt, postes_hta, plu_info, *args, **kwargs):
    """Generate an interactive Folium map."""
    m = folium.Map(location=[lat, lon], zoom_start=15, tiles="OpenStreetMap")
    
    # Add marker for the searched location
    folium.Marker(
        [lat, lon],
        popup=f"Address: {address or 'Coordinates'}",
        icon=folium.Icon(color="blue")
    ).add_to(m)
    
    # Add parcels
    folium.GeoJson(
        parcelles_data,
        name="Parcelles",
        style_function=lambda x: {"fillColor": "green", "color": "black", "weight": 1, "fillOpacity": 0.3}
    ).add_to(m)
    
    # Add BT postes
    for feature in postes_bt["features"]:
        coords = feature["geometry"]["coordinates"]
        folium.CircleMarker(
            [coords[1], coords[0]],
            radius=5,
            color="red",
            fill=True,
            fill_color="red",
            popup=feature["properties"].get("nom", "BT Poste")
        ).add_to(m)
    
    # Add HTA postes
    for feature in postes_hta["features"]:
        coords = feature["geometry"]["coordinates"]
        folium.CircleMarker(
            [coords[1], coords[0]],
            radius=5,
            color="purple",
            fill=True,
            fill_color="purple",
            popup=feature["properties"].get("Nom", "HTA Poste")
        ).add_to(m)
    
    # Add PLU data
    folium.GeoJson(
        plu_info,
        name="PLU",
        style_function=lambda x: {"fillColor": "blue", "color": "black", "weight": 1, "fillOpacity": 0.2}
    ).add_to(m)
    
    folium.LayerControl().add_to(m)
    return m

def save_map_to_cache(map_obj):
    """Save Folium map to cache (placeholder)."""
    # Implement caching logic (e.g., save to file or Redis)
    map_obj.save("cache/map.html")  # Example implementation

# --- Flask Endpoints ---
@app.route("/search_by_address", methods=["GET", "POST"])
def search_by_address():
    """Search geospatial data by address or coordinates."""
    values = request.values
    address = values.get("address")
    lat_str = values.get("lat")
    lon_str = values.get("lon")
    
    # Validate radii
    try:
        ht_radius_km = float(values.get("ht_radius", 1.0))
        bt_radius_km = float(values.get("bt_radius", 1.0))
    except ValueError:
        return jsonify({"error": "Invalid radius parameters (must be numbers)"}), 400
    
    # Get coordinates
    if lat_str and lon_str:
        coords = validate_coordinates(lat_str, lon_str)
        if not coords:
            return jsonify({"error": "Coordinates are invalid or outside France"}), 400
        lat, lon = coords
    elif address:
        coords = geocode_address(address)
        if not coords:
            return jsonify({
                "error": "Address not found",
                "details": "Could not geocode the provided address. Please check the format or try a more specific address (e.g., include postal code)."
            }), 404
        lat, lon = coords
    else:
        return jsonify({"error": "Please provide an address or coordinates"}), 400
    
    # Convert radii to degrees (approximate: 1 degree ≈ 111 km)
    search_radius = 0.03
    bt_radius_deg = bt_radius_km / 111
    ht_radius_deg = ht_radius_km / 111
    
    # Fetch geospatial data
    try:
        parcelles_data = get_all_parcelles(lat, lon, radius=search_radius)
        parcelle = get_parcelle_info(lat, lon)
        postes_bt = get_nearest_postes(lat, lon, radius_deg=bt_radius_deg)
        postes_hta = get_nearest_ht_postes(lat, lon, radius_deg=ht_radius_deg)
        plu_info = get_plu_info(lat, lon, radius=search_radius)
        rpg_data = get_rpg_info(lat, lon, radius=0.0027)
        geom_point = {"type": "Point", "coordinates": [lon, lat]}
        api_cadastre = get_api_cadastre_data(geom_point)
        solaire = {"kwh_per_kwc": get_pvgis_production(lat, lon, tilt=30, azimuth=180)}
    except Exception as e:
        logger.error(f"Error fetching geospatial data for lat={lat}, lon={lon}: {e}")
        return jsonify({"error": "Failed to fetch geospatial data", "details": str(e)}), 500
    
    # Build response
    response = {
        "lat": lat,
        "lon": lon,
        "address": address,
        "parcelles": to_feature_collection(parcelles_data),
        "parcelle": parcelle or {},
        "postes_bt": to_feature_collection(postes_bt),
        "postes_hta": to_feature_collection(postes_hta),
        "plu": to_feature_collection(plu_info),
        "rpg": to_feature_collection(rpg_data),
        "solaire": solaire,
        "api_cadastre": api_cadastre or {},
    }
    
    # Generate and cache map
    try:
        map_obj = build_map(lat, lon, address, parcelle, parcelles_data, postes_bt, postes_hta, plu_info)
        save_map_to_cache(map_obj)
    except Exception as e:
        logger.error(f"Error generating map for lat={lat}, lon={lon}: {e}")
        response["map_error"] = "Failed to generate map"
    
    return jsonify(response)

@app.route("/feasibility_simplified", methods=["GET"])
def feasibility_simplified():
    """Estimate solar production for given coordinates."""
    required_params = ["lat", "lon", "tilt", "azimuth"]
    missing = [p for p in required_params if not request.args.get(p)]
    if missing:
        return jsonify({"error": f"Missing parameters: {', '.join(missing)}"}), 400
    
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
        tilt = float(request.args.get("tilt"))
        azimuth = float(request.args.get("azimuth"))
    except ValueError:
        return jsonify({"error": "All parameters must be valid numbers"}), 400
    
    coords = validate_coordinates(lat, lon)
    if not coords:
        return jsonify({"error": "Coordinates are invalid or outside France"}), 400
    
    kwh_an = get_pvgis_production(lat, lon, tilt, azimuth, peakpower=1.0)
    if kwh_an is None:
        return jsonify({"error": "Failed to fetch PVGIS data", "details": "Service unavailable or invalid parameters"}), 500
    
    return jsonify({"kwh_per_kwc": round(kwh_an, 2)})

# Placeholder for other endpoints
@app.route("/rapport", methods=["POST"])
def rapport():
    """Generate a detailed report (placeholder)."""
    return jsonify({"status": "Not implemented", "message": "Rapport generation to be implemented"})

@app.route("/generate_reports_by_dept_sse", methods=["GET"])
def generate_reports_by_dept_sse():
    """Generate reports for a department using SSE (placeholder)."""
    return jsonify({"status": "Not implemented", "message": "Department report generation to be implemented"})

# --- Run Application ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)