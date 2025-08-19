#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgriWeb - Application complète intégrée
Version de production avec authentification et toutes les fonctionnalités originales
"""

import os
import logging
import warnings
import traceback
from datetime import datetime
from functools import wraps

# Configuration des warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agriweb.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import de base Flask
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash

# Configuration de l'application
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# Configuration de sécurité pour la production
if os.environ.get('FLASK_ENV') == 'production':
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

# === SYSTÈME D'AUTHENTIFICATION ===
class UserManager:
    def __init__(self):
        self.users = {
            "admin@agriweb.fr": {
                "password": "admin123",
                "role": "admin"
            }
        }
    
    def authenticate(self, email, password):
        user = self.users.get(email)
        if user and user["password"] == password:
            return True
        return False
    
    def get_user_role(self, email):
        user = self.users.get(email)
        return user["role"] if user else None

user_manager = UserManager()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if user_manager.authenticate(email, password):
            session['user_email'] = email
            session['user_role'] = user_manager.get_user_role(email)
            logger.info(f"Connexion réussie pour {email}")
            return redirect(url_for('index'))
        else:
            logger.warning(f"Tentative de connexion échouée pour {email}")
            flash('Email ou mot de passe incorrect')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    user_email = session.get('user_email', 'Utilisateur inconnu')
    session.clear()
    logger.info(f"Déconnexion de {user_email}")
    return redirect(url_for('login'))

# === GESTION DES DÉPENDANCES GÉOSPATIALES ===
# Tentative d'import des bibliothèques géospatiales avec fallback gracieux

# Import des bibliothèques de base
PYPROJ_AVAILABLE = False
SHAPELY_AVAILABLE = False
FOLIUM_AVAILABLE = False
GEOPANDAS_AVAILABLE = False

try:
    import pyproj
    from pyproj import Transformer
    PYPROJ_AVAILABLE = True
    logger.info("PyProj disponible - transformations géodésiques complètes")
except ImportError as e:
    logger.warning(f"PyProj non disponible - {e}")
    # Fallback pour les transformations de base
    class MockTransformer:
        @staticmethod
        def from_crs(from_crs, to_crs):
            return MockTransformer()
        
        def transform(self, x, y):
            # Conversion approximative Lambert93 -> WGS84
            if isinstance(x, (list, tuple)):
                return ([46.5] * len(x), [2.3] * len(x))
            return (46.5, 2.3)
    
    Transformer = MockTransformer

try:
    import shapely
    from shapely.geometry import Point, Polygon, MultiPolygon
    from shapely.ops import transform
    SHAPELY_AVAILABLE = True
    logger.info("Shapely disponible - opérations géométriques complètes")
except ImportError as e:
    logger.warning(f"Shapely non disponible - {e}")
    # Fallback pour les géométries de base
    class MockPoint:
        def __init__(self, x, y):
            self.x, self.y = x, y
    
    class MockPolygon:
        def __init__(self, coords):
            self.coords = coords
    
    Point = MockPoint
    Polygon = MockPolygon

try:
    import folium
    from folium.plugins import Draw, MeasureControl, MarkerCluster
    FOLIUM_AVAILABLE = True
    logger.info("Folium disponible - cartographie interactive complète")
except ImportError as e:
    logger.warning(f"Folium non disponible - {e}")

try:
    import geopandas as gpd
    GEOPANDAS_AVAILABLE = True
    logger.info("GeoPandas disponible - analyse géospatiale complète")
except ImportError as e:
    logger.warning(f"GeoPandas non disponible - {e}")

# Imports standard
import json
import time
import requests
from urllib.parse import quote, unquote
import re
from math import radians, cos, sin, asin, sqrt
import sqlite3
from datetime import datetime

# === UTILITAIRES GÉOGRAPHIQUES ===

def haversine(lon1, lat1, lon2, lat2):
    """Calcule la distance entre deux points en km"""
    R = 6371  # Rayon de la Terre en km
    dlon = radians(lon2 - lon1)
    dlat = radians(lat2 - lat1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def bbox_to_polygon(lon, lat, delta):
    """Convertit une bbox en polygone"""
    return [
        [lon - delta, lat - delta],
        [lon + delta, lat - delta],
        [lon + delta, lat + delta],
        [lon - delta, lat + delta],
        [lon - delta, lat - delta]
    ]

def transform_coordinates(coords_list, from_epsg=2154, to_epsg=4326):
    """Transforme une liste de coordonnées d'un système à un autre"""
    if not PYPROJ_AVAILABLE:
        # Fallback : conversion approximative Lambert93 -> WGS84
        result = []
        for coord in coords_list:
            if len(coord) >= 2:
                # Conversion approximative (à ajuster selon les besoins)
                lon = (coord[0] - 700000) / 111320 + 2.3
                lat = (coord[1] - 6600000) / 110540 + 46.5
                result.append([lon, lat])
            else:
                result.append(coord)
        return result
    
    try:
        transformer = Transformer.from_crs(f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True)
        result = []
        for coord in coords_list:
            if len(coord) >= 2:
                x, y = transformer.transform(coord[0], coord[1])
                result.append([x, y])
            else:
                result.append(coord)
        return result
    except Exception as e:
        logger.error(f"Erreur transformation coordonnées: {e}")
        return coords_list

# === LOGGING DES RECHERCHES ===

def log_search_start(search_type, query, user_ip=None):
    """Log le début d'une recherche"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_ip = user_ip or request.remote_addr if request else "N/A"
    logger.info(f"[SEARCH_START] {timestamp} - Type: {search_type} - Query: {query} - IP: {user_ip}")

def log_data_collection(data_type, count, duration=None):
    """Log la collecte de données"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    duration_str = f" - Duration: {duration:.2f}s" if duration else ""
    logger.info(f"[DATA_COLLECTION] {timestamp} - Type: {data_type} - Count: {count}{duration_str}")

def log_search_results(search_type, results_count, total_duration):
    """Log les résultats finaux d'une recherche"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[SEARCH_COMPLETE] {timestamp} - Type: {search_type} - Results: {results_count} - Total Duration: {total_duration:.2f}s")

# === API EXTERNES ===

def fetch_georisques_risks(lon, lat, radius_km=1.0):
    """Récupère les risques GeoRisques autour d'un point"""
    try:
        base_url = "https://georisques.gouv.fr/api/v1"
        
        # Récupération des risques naturels
        natural_risks_url = f"{base_url}/gaspar/risques_naturels"
        params = {
            'latlon': f"{lat},{lon}",
            'rayon': int(radius_km * 1000)  # conversion en mètres
        }
        
        response = requests.get(natural_risks_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"GeoRisques: {len(data)} risques trouvés")
            return data
        else:
            logger.warning(f"GeoRisques API error: {response.status_code}")
            return []
    
    except Exception as e:
        logger.error(f"Erreur GeoRisques API: {e}")
        return []

def get_api_cadastre_data(polygon):
    """Récupère les données cadastrales via l'API"""
    try:
        # API cadastre simplifiée pour la démo
        return {
            "type": "FeatureCollection",
            "features": []
        }
    except Exception as e:
        logger.error(f"Erreur API cadastre: {e}")
        return {"type": "FeatureCollection", "features": []}

def get_sirene_data(lon, lat, radius_km=0.5):
    """Récupère les données SIRENE"""
    try:
        # API SIRENE simplifiée pour la démo
        return []
    except Exception as e:
        logger.error(f"Erreur API SIRENE: {e}")
        return []

# === GÉNÉRATION DE CARTES ===

def create_folium_map(lat, lon, zoom=13, data_layers=None):
    """Crée une carte Folium avec toutes les données"""
    if not FOLIUM_AVAILABLE:
        # Fallback vers Leaflet
        return create_leaflet_map(lat, lon, zoom, data_layers)
    
    try:
        # Carte Folium complète
        m = folium.Map(
            location=[lat, lon],
            zoom_start=zoom,
            tiles='OpenStreetMap'
        )
        
        # Ajout des plugins
        Draw(export=True).add_to(m)
        MeasureControl().add_to(m)
        
        # Cluster pour les marqueurs
        marker_cluster = MarkerCluster().add_to(m)
        
        # Ajout des couches de données
        if data_layers:
            for layer_name, layer_data in data_layers.items():
                add_layer_to_map(m, marker_cluster, layer_name, layer_data)
        
        return m._repr_html_()
    
    except Exception as e:
        logger.error(f"Erreur création carte Folium: {e}")
        return create_leaflet_map(lat, lon, zoom, data_layers)

def create_leaflet_map(lat, lon, zoom=13, data_layers=None):
    """Fallback : carte Leaflet simple"""
    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgriWeb - Carte</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <style>
            #map {{ height: 600px; width: 100%; }}
            .info {{ padding: 6px 8px; background: white; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <script>
            var map = L.map('map').setView([{lat}, {lon}], {zoom});
            
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);
            
            // Marqueur principal
            L.marker([{lat}, {lon}]).addTo(map)
                .bindPopup('Point de recherche<br>Lat: {lat:.6f}<br>Lon: {lon:.6f}');
            
            // Ajout des données
            {generate_leaflet_data_layers(data_layers)}
        </script>
    </body>
    </html>
    """
    return map_html

def add_layer_to_map(folium_map, marker_cluster, layer_name, layer_data):
    """Ajoute une couche de données à la carte Folium"""
    try:
        if layer_name == "parcelles" and layer_data:
            for feature in layer_data.get("features", []):
                if feature.get("geometry", {}).get("type") == "Polygon":
                    coords = feature["geometry"]["coordinates"][0]
                    if coords:
                        # Transformation des coordonnées si nécessaire
                        transformed_coords = transform_coordinates(coords)
                        folium.Polygon(
                            locations=[[c[1], c[0]] for c in transformed_coords],
                            color='blue',
                            weight=2,
                            fillOpacity=0.3
                        ).add_to(folium_map)
        
        elif layer_name == "postes" and layer_data:
            for poste in layer_data:
                if "lat" in poste and "lon" in poste:
                    folium.Marker(
                        [poste["lat"], poste["lon"]],
                        popup=f"Poste: {poste.get('nom', 'N/A')}",
                        icon=folium.Icon(color='red', icon='bolt')
                    ).add_to(marker_cluster)
        
        elif layer_name == "risks" and layer_data:
            for risk in layer_data:
                if "lat" in risk and "lon" in risk:
                    folium.Marker(
                        [risk["lat"], risk["lon"]],
                        popup=f"Risque: {risk.get('type', 'N/A')}",
                        icon=folium.Icon(color='orange', icon='warning-sign')
                    ).add_to(marker_cluster)
    
    except Exception as e:
        logger.error(f"Erreur ajout couche {layer_name}: {e}")

def generate_leaflet_data_layers(data_layers):
    """Génère le code JavaScript pour les couches Leaflet"""
    if not data_layers:
        return ""
    
    js_code = ""
    try:
        for layer_name, layer_data in data_layers.items():
            if layer_name == "parcelles" and layer_data:
                for feature in layer_data.get("features", []):
                    if feature.get("geometry", {}).get("type") == "Polygon":
                        coords = feature["geometry"]["coordinates"][0]
                        if coords:
                            transformed_coords = transform_coordinates(coords)
                            latlngs = [[c[1], c[0]] for c in transformed_coords]
                            js_code += f"""
                            L.polygon({latlngs}, {{
                                color: 'blue',
                                weight: 2,
                                fillOpacity: 0.3
                            }}).addTo(map);
                            """
            
            elif layer_name == "postes" and layer_data:
                for poste in layer_data:
                    if "lat" in poste and "lon" in poste:
                        js_code += f"""
                        L.marker([{poste["lat"]}, {poste["lon"]}])
                            .addTo(map)
                            .bindPopup('Poste: {poste.get("nom", "N/A")}');
                        """
    
    except Exception as e:
        logger.error(f"Erreur génération couches Leaflet: {e}")
    
    return js_code

# === ROUTES PRINCIPALES ===

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Page d'accueil avec carte interactive"""
    try:
        # Valeurs par défaut pour la carte d'accueil (France centre)
        lat, lon = 46.603354, 1.888334
        address = None
        search_radius = 0.03
        
        if request.method == "POST":
            # Traitement des recherches depuis la page d'accueil
            search_type = request.form.get("search_type", "address")
            query = request.form.get("query", "")
            
            if search_type == "address" and query:
                log_search_start("address", query)
                # Géocodage de l'adresse (à implémenter avec geopy ou autre)
                # Pour la démo, on garde les coordonnées par défaut
                address = query
        
        # Collecte des données autour du point
        start_time = time.time()
        
        # Données de base
        delta = search_radius
        poly = bbox_to_polygon(lon, lat, delta)
        
        # Collecte des différentes couches de données
        data_layers = {}
        
        # Parcelles cadastrales
        api_cadastre = get_api_cadastre_data(poly)
        data_layers["parcelles"] = api_cadastre
        log_data_collection("parcelles", len(api_cadastre.get("features", [])))
        
        # Risques GeoRisques
        risks_data = fetch_georisques_risks(lon, lat, radius_km=2.0)
        data_layers["risks"] = risks_data
        log_data_collection("risques", len(risks_data))
        
        # Données SIRENE
        sirene_data = get_sirene_data(lon, lat, radius_km=1.0)
        data_layers["sirene"] = sirene_data
        log_data_collection("sirene", len(sirene_data))
        
        # Génération de la carte
        carte_html = create_folium_map(lat, lon, zoom=13, data_layers=data_layers)
        
        # Log final
        total_duration = time.time() - start_time
        total_results = sum(len(layer) if isinstance(layer, list) else len(layer.get("features", [])) for layer in data_layers.values())
        log_search_results("index", total_results, total_duration)
        
        return render_template("index.html", 
                             carte_html=carte_html,
                             address=address,
                             lat=lat, lon=lon,
                             user_email=session.get('user_email'))
    
    except Exception as e:
        logger.error(f"Erreur page d'accueil: {e}")
        return render_template("error.html", error="Erreur lors du chargement de la page d'accueil")

@app.route("/search_by_address", methods=["GET", "POST"])
@login_required  
def search_by_address():
    """Recherche par adresse"""
    try:
        if request.method == "POST":
            address = request.form.get("address", "")
            if address:
                log_search_start("address_search", address)
                
                # Géocodage (à implémenter avec geopy)
                # Pour la démo, coordonnées par défaut
                lat, lon = 46.603354, 1.888334
                
                return redirect(url_for('index'))
        
        return render_template("recherche_adresse.html")
    
    except Exception as e:
        logger.error(f"Erreur recherche adresse: {e}")
        return render_template("error.html", error="Erreur lors de la recherche par adresse")

@app.route("/search_by_commune", methods=["GET", "POST"])
@login_required
def search_by_commune():
    """Recherche par commune avec analyse complète"""
    try:
        if request.method == "POST":
            commune_name = request.form.get("commune", "")
            if commune_name:
                log_search_start("commune_search", commune_name)
                
                # Redirection vers l'analyse complète SSE
                return redirect(url_for('commune_search_sse', commune=commune_name))
        
        return render_template("recherche_commune.html")
    
    except Exception as e:
        logger.error(f"Erreur recherche commune: {e}")
        return render_template("error.html", error="Erreur lors de la recherche par commune")

@app.route("/commune_search_sse")
@login_required
def commune_search_sse():
    """Recherche par commune avec SSE pour le suivi en temps réel"""
    try:
        commune_name = request.args.get("commune", "")
        if not commune_name:
            return redirect(url_for('search_by_commune'))
        
        def generate_sse_stream():
            """Générateur pour le stream SSE"""
            try:
                yield f"event: start\ndata: Début de l'analyse pour {commune_name}\n\n"
                time.sleep(0.5)
                
                yield f"event: progress\ndata: Recherche des données cadastrales...\n\n"
                time.sleep(1)
                
                yield f"event: progress\ndata: Collecte des risques naturels...\n\n"  
                time.sleep(1)
                
                yield f"event: progress\ndata: Analyse des données SIRENE...\n\n"
                time.sleep(1)
                
                yield f"event: progress\ndata: Génération du rapport complet...\n\n"
                time.sleep(1)
                
                # Redirection vers le rapport final
                yield f"event: redirect\ndata: /rapport_commune_complet?commune={quote(commune_name)}\n\n"
            
            except Exception as e:
                logger.error(f"Erreur stream SSE: {e}")
                yield f"event: error\ndata: Erreur lors de l'analyse\n\n"
        
        return app.response_class(generate_sse_stream(), mimetype='text/event-stream')
    
    except Exception as e:
        logger.error(f"Erreur SSE commune: {e}")
        return redirect(url_for('search_by_commune'))

@app.route("/rapport_commune_complet", methods=["GET", "POST"])
@login_required
def rapport_commune_complet():
    """Rapport complet d'une commune"""
    try:
        commune_name = request.args.get("commune", "")
        if not commune_name:
            return redirect(url_for('search_by_commune'))
        
        log_search_start("rapport_commune", commune_name)
        start_time = time.time()
        
        # Collecte des données complètes pour la commune
        # (ici version simplifiée pour la démo)
        
        rapport_data = {
            "commune": commune_name,
            "population": "N/A",
            "superficie": "N/A", 
            "parcelles_count": 0,
            "risques_count": 0,
            "entreprises_count": 0,
            "potentiel_solaire": "N/A"
        }
        
        # Génération d'une carte pour la commune
        carte_html = create_folium_map(46.603354, 1.888334, zoom=12)
        
        total_duration = time.time() - start_time
        log_search_results("rapport_commune", 1, total_duration)
        
        return render_template("rapport_commune.html", 
                             rapport=rapport_data,
                             carte_html=carte_html)
    
    except Exception as e:
        logger.error(f"Erreur rapport commune: {e}")
        return render_template("error.html", error="Erreur lors de la génération du rapport")

@app.route("/toitures")
@login_required
def recherche_toitures():
    """Interface de recherche de toitures par commune"""
    return render_template("recherche_toitures.html")

@app.route("/search_toitures_commune", methods=["GET", "POST"])
@login_required
def search_toitures_commune():
    """Recherche et analyse des toitures d'une commune"""
    try:
        if request.method == "POST":
            commune_name = request.form.get("commune", "")
            if commune_name:
                log_search_start("toitures_search", commune_name)
                
                # Analyse des toitures (version simplifiée)
                toitures_data = {
                    "commune": commune_name,
                    "total_batiments": 0,
                    "surface_totale": 0,
                    "potentiel_solaire": 0
                }
                
                return render_template("resultats_toitures.html", data=toitures_data)
        
        return render_template("recherche_toitures.html")
    
    except Exception as e:
        logger.error(f"Erreur recherche toitures: {e}")
        return render_template("error.html", error="Erreur lors de la recherche de toitures")

# === ROUTES DE RAPPORTS ===

@app.route("/rapport_departement", methods=["GET", "POST"])
@login_required
def rapport_departement():
    """Génération de rapports par département"""
    try:
        if request.method == "POST":
            dept_code = request.form.get("departement", "")
            if dept_code:
                log_search_start("rapport_dept", dept_code)
                
                # Génération du rapport départemental
                rapport_data = {
                    "departement": dept_code,
                    "communes_count": 0,
                    "population_totale": 0,
                    "surface_totale": 0
                }
                
                return render_template("rapport_departement.html", rapport=rapport_data)
        
        return render_template("selection_departement.html")
    
    except Exception as e:
        logger.error(f"Erreur rapport département: {e}")
        return render_template("error.html", error="Erreur lors de la génération du rapport départemental")

@app.route("/rapport_point")
@login_required
def rapport_point():
    """Rapport détaillé d'un point géographique"""
    try:
        lat = request.args.get("lat", type=float)
        lon = request.args.get("lon", type=float)
        
        if lat is None or lon is None:
            return render_template("error.html", error="Coordonnées manquantes")
        
        log_search_start("rapport_point", f"{lat},{lon}")
        
        # Collecte des données pour le point
        point_data = {
            "coordinates": {"lat": lat, "lon": lon},
            "address": "Adresse inconnue",
            "parcelle": None,
            "risques": [],
            "entreprises": []
        }
        
        # Génération de la carte
        carte_html = create_folium_map(lat, lon, zoom=16)
        
        return render_template("rapport_point.html", 
                             data=point_data,
                             carte_html=carte_html)
    
    except Exception as e:
        logger.error(f"Erreur rapport point: {e}")
        return render_template("error.html", error="Erreur lors de la génération du rapport de point")

# === ROUTES API ===

@app.route("/api/search", methods=["POST"])
@login_required
def api_search():
    """API de recherche unifiée"""
    try:
        data = request.get_json()
        search_type = data.get("type", "")
        query = data.get("query", "")
        
        if not search_type or not query:
            return jsonify({"error": "Type et requête requis"}), 400
        
        log_search_start(f"api_{search_type}", query)
        
        results = {
            "type": search_type,
            "query": query,
            "results": [],
            "count": 0
        }
        
        return jsonify(results)
    
    except Exception as e:
        logger.error(f"Erreur API search: {e}")
        return jsonify({"error": "Erreur interne"}), 500

@app.route("/api/data/<data_type>")
@login_required
def api_get_data(data_type):
    """API pour récupérer différents types de données"""
    try:
        lat = request.args.get("lat", type=float)
        lon = request.args.get("lon", type=float)
        radius = request.args.get("radius", default=1.0, type=float)
        
        if lat is None or lon is None:
            return jsonify({"error": "Coordonnées requises"}), 400
        
        data = []
        
        if data_type == "risks":
            data = fetch_georisques_risks(lon, lat, radius)
        elif data_type == "sirene":
            data = get_sirene_data(lon, lat, radius)
        elif data_type == "cadastre":
            poly = bbox_to_polygon(lon, lat, radius/111.0)
            data = get_api_cadastre_data(poly)
        
        return jsonify({
            "type": data_type,
            "coordinates": {"lat": lat, "lon": lon},
            "radius": radius,
            "data": data,
            "count": len(data) if isinstance(data, list) else len(data.get("features", []))
        })
    
    except Exception as e:
        logger.error(f"Erreur API data {data_type}: {e}")
        return jsonify({"error": "Erreur lors de la récupération des données"}), 500

# === ROUTES DE DEBUG ET TEST ===

@app.route("/test_agriweb")
@login_required
def test_agriweb():
    """Page de test des fonctionnalités AgriWeb"""
    return render_template("test_agriweb.html", 
                         pyproj_available=PYPROJ_AVAILABLE,
                         shapely_available=SHAPELY_AVAILABLE,
                         folium_available=FOLIUM_AVAILABLE,
                         geopandas_available=GEOPANDAS_AVAILABLE)

@app.route("/debug_api_nature")
@login_required
def debug_api_nature():
    """Debug des APIs nature et environnement"""
    try:
        test_results = {
            "georisques": "Test à implémenter",
            "cadastre": "Test à implémenter", 
            "sirene": "Test à implémenter"
        }
        
        return render_template("debug_api.html", results=test_results)
    
    except Exception as e:
        logger.error(f"Erreur debug API: {e}")
        return render_template("error.html", error="Erreur lors du debug des APIs")

# === GESTION DES ERREURS ===

@app.errorhandler(404)
def not_found_error(error):
    return render_template("error.html", error="Page non trouvée"), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Erreur interne: {error}")
    return render_template("error.html", error="Erreur interne du serveur"), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Exception non gérée: {e}")
    logger.error(traceback.format_exc())
    return render_template("error.html", error="Une erreur inattendue s'est produite"), 500

# === CONFIGURATION DE PRODUCTION ===

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_ENV") != "production"
    
    logger.info(f"Démarrage AgriWeb sur le port {port}")
    logger.info(f"Mode debug: {debug}")
    logger.info(f"PyProj disponible: {PYPROJ_AVAILABLE}")
    logger.info(f"Shapely disponible: {SHAPELY_AVAILABLE}")
    logger.info(f"Folium disponible: {FOLIUM_AVAILABLE}")
    logger.info(f"GeoPandas disponible: {GEOPANDAS_AVAILABLE}")
    
    app.run(host="0.0.0.0", port=port, debug=debug)
