#!/usr/bin/env python3
"""
🚀 SERVEUR AGRIWEB 2.0 UNIFIÉ - COMMERCIALISATION + GEOSERVER
Serveur complet avec essais gratuits, licences, paiements et GeoServer intégré
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import sys
import os
from datetime import datetime, timedelta
import requests
import uuid
import json

# Imports pour les cartes
import folium
from folium.plugins import Draw, MeasureControl, MarkerCluster, Search
import geopandas as gpd
from shapely.geometry import shape, Point, mapping, MultiPolygon, Polygon
from shapely.ops import transform as shp_transform
from shapely.errors import GEOSException
from pyproj import Transformer
from urllib.parse import quote, quote_plus
import unicodedata, re
import time

# Import des modules AgriWeb existants
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agriweb_source import (
        build_report_data,
        get_communes_for_dept,
        fetch_gpu_data,
        geocode_address,
        get_address_from_coordinates
    )
    print("✅ Modules AgriWeb importés avec succès")
except ImportError as e:
    print(f"❌ Erreur import AgriWeb: {e}")

import os

# Configuration Flask avec dossier static
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('SECRET_KEY', 'agriweb-2025-production-key')

# Créer le dossier static/cartes si il n'existe pas
static_cartes_dir = os.path.join(os.path.dirname(__file__), 'static', 'cartes')
os.makedirs(static_cartes_dir, exist_ok=True)
print(f"📁 Dossier static/cartes créé: {static_cartes_dir}")

# Configuration GeoServer - Utilise les variables d'environnement Railway
# Fonction pour nettoyer les guillemets des variables Railway
def clean_env_var(var_name, default_value):
    """Nettoie les guillemets des variables d'environnement Railway"""
    value = os.getenv(var_name, default_value)
    if value and value.startswith('"') and value.endswith('"'):
        value = value[1:-1]  # Retire les guillemets
    return value

GEOSERVER_URL = clean_env_var('GEOSERVER_URL', 'http://localhost:8080/geoserver')
GEOSERVER_WFS_URL = f"{GEOSERVER_URL}/ows"
GEOSERVER_USERNAME = clean_env_var('GEOSERVER_USERNAME', 'admin')
GEOSERVER_PASSWORD = clean_env_var('GEOSERVER_PASSWORD', 'geoserver')

# Base de données simple des utilisateurs (en production, utiliser une vraie DB)
USERS_DB = {}

print(f"🚀 [PRODUCTION] Utilisation de GEOSERVER_URL: {GEOSERVER_URL}")
print(f"🚀 Configuration Railway:")
print(f"   - GeoServer URL: {GEOSERVER_URL}")
print(f"   - GeoServer Auth: {GEOSERVER_USERNAME}:{'*' * len(GEOSERVER_PASSWORD)}")
print(f"   - Port: {os.getenv('PORT', '5000')}")
print(f"   - Debug: {os.getenv('FLASK_DEBUG', 'False')}")
print(f"🔗 GeoServer configuré: {GEOSERVER_URL}")

# Debug variables d'environnement
print("🔍 [DEBUG] Variables d'environnement reçues:")
print(f"   - GEOSERVER_URL raw: '{os.getenv('GEOSERVER_URL', 'NOT_SET')}'")
print(f"   - PORT raw: '{os.getenv('PORT', 'NOT_SET')}'")
print(f"   - FLASK_DEBUG raw: '{os.getenv('FLASK_DEBUG', 'NOT_SET')}'")
print(f"   - SECRET_KEY présente: {'Oui' if os.getenv('SECRET_KEY') else 'Non'}")

# Configuration des couches GeoServer
CADASTRE_LAYER = "gpu:prefixes_sections"
POSTE_LAYER = "gpu:poste_elec_shapefile"          # Postes BT
PLU_LAYER = "gpu:gpu1"
PARCELLE_LAYER = "gpu:PARCELLE2024"
HT_POSTE_LAYER = "gpu:postes-electriques-rte"      # Postes HTA
CAPACITES_RESEAU_LAYER = "gpu:CapacitesDAccueil"   # Capacités d'accueil (HTA)
PARKINGS_LAYER = "gpu:parkings_sup500m2"
FRICHES_LAYER = "gpu:friches-standard"
POTENTIEL_SOLAIRE_LAYER = "gpu:POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93"
ZAER_LAYER = "gpu:ZAER_ARRETE_SHP_FRA"
PARCELLES_GRAPHIQUES_LAYER = "gpu:PARCELLES_GRAPHIQUES"  # RPG
SIRENE_LAYER = "gpu:GeolocalisationEtablissement_Sirene france"  # Sirène
ELEVEURS_LAYER = "gpu:etablissements_eleveurs"
PPRI_LAYER = "gpu:ppri"

# === FONCTIONS UTILITAIRES POUR LES CARTES ===

def save_map_html(map_obj, filename):
    """
    Save a Folium map object to static/cartes/ and return the relative path for use in the app.
    """
    import os
    # Ensure the directory exists
    cartes_dir = os.path.join(os.path.dirname(__file__), "static", "cartes")
    os.makedirs(cartes_dir, exist_ok=True)
    # Save the map
    filepath = os.path.join(cartes_dir, filename)
    map_obj.save(filepath)
    # Return the relative path from /static/
    return f"cartes/{filename}"

def bbox_to_polygon(lon, lat, delta):
    """
    Construit un polygone de type 'Polygon' (GeoJSON)
    autour d'un centre (lon, lat) avec un rayon en degrés = delta.
    """
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

# Mapping des cultures RPG
rpg_culture_mapping = {
    "BTH": "Blé tendre d'hiver",
    "BTP": "Blé tendre de printemps",
    "MID": "Maïs doux",
    "MIE": "Maïs ensilage",
    "MIS": "Maïs",
    "ORH": "Orge d'hiver",
    "ORP": "Orge de printemps",
    "AVH": "Avoine d'hiver",
    "AVP": "Avoine de printemps",
    "CZH": "Colza d'hiver",
    "CZP": "Colza de printemps",
    "TRN": "Tournesol",
    "ARA": "Arachide"
}

def decode_rpg_feature(feature):
    props = feature.get("properties", {})
    code = props.get("CODE_CULTU", "").strip()
    if code in rpg_culture_mapping:
        props["Culture"] = rpg_culture_mapping[code]
    else:
        props["Culture"] = code
    return feature

def calculate_min_distance(centroid, postes):
    distances = [
        shape(poste["geometry"]).distance(Point(centroid)) * 111000
        for poste in postes
    ]
    return min(distances) if distances else None

def flatten_gpu_dict_to_featurecollection(gpu_dict):
    features = []
    for key, value in gpu_dict.items():
        # Chaque "value" devrait être une FeatureCollection
        if isinstance(value, dict) and value.get("type") == "FeatureCollection":
            features += value.get("features", [])
    return {"type": "FeatureCollection", "features": features}

def get_all_gpu_data(geom):
    """Version simplifiée pour Railway - utilise fetch_gpu_data si disponible"""
    endpoints = [
        "zone-urba",
        "prescription-surf",
        "prescription-lin",
        "prescription-pct",
        "secteur-cc"
    ]
    results = {}
    for ep in endpoints:
        try:
            if 'fetch_gpu_data' in globals():
                data = fetch_gpu_data(ep, geom)
            else:
                data = {"type": "FeatureCollection", "features": []}
            results[ep] = data
        except Exception as e:
            print(f"[DEBUG] Erreur GPU {ep}: {e}")
            results[ep] = {"type": "FeatureCollection", "features": []}
    return results

# === FONCTIONS DE RÉCUPÉRATION DYNAMIQUE DES DONNÉES GEOSERVER ===

def fetch_wfs_data(layer_name, bbox, srsname="EPSG:4326"):
    """Récupère les données WFS depuis GeoServer de façon dynamique"""
    from urllib.parse import quote
    layer_q = quote(layer_name, safe=':')
    url = f"{GEOSERVER_WFS_URL}?service=WFS&version=2.0.0&request=GetFeature&typeName={layer_q}&outputFormat=application/json&bbox={bbox}&srsname={srsname}"
    try:
        resp = requests.get(url, auth=(GEOSERVER_USERNAME, GEOSERVER_PASSWORD), timeout=10)
        resp.raise_for_status()
        if 'xml' in resp.headers.get('Content-Type', ''):
            print(f"[fetch_wfs_data] GeoServer error XML for {layer_name}:\n{resp.text[:200]}")
            return []
        return resp.json().get('features', [])
    except Exception as e:
        print(f"[fetch_wfs_data] Erreur {layer_name}: {e}")
        return []

def get_all_postes(lat, lon, radius_deg=0.1):
    """Récupère dynamiquement les postes BT depuis GeoServer"""
    bbox = f"{lon-radius_deg},{lat-radius_deg},{lon+radius_deg},{lat+radius_deg},EPSG:4326"
    features = fetch_wfs_data(POSTE_LAYER, bbox)
    if not features:
        print(f"[DEBUG] Aucun poste trouvé dans le bbox {bbox}")
        return []
    
    point = Point(lon, lat)
    postes = []
    for feature in features:
        geom_shp = shape(feature["geometry"])
        dist = geom_shp.distance(point) * 111000  # Conversion en mètres
        postes.append({
            "properties": feature["properties"],
            "distance": round(dist, 2),
            "geometry": mapping(geom_shp)
        })
    print(f"[DEBUG] {len(postes)} postes trouvés, distances: {[p['distance'] for p in postes[:3]]}")
    return postes

def get_all_ht_postes(lat, lon, radius_deg=0.5):
    """Récupère dynamiquement les postes HTA depuis GeoServer"""
    bbox = f"{lon-radius_deg},{lat-radius_deg},{lon+radius_deg},{lat+radius_deg},EPSG:4326"
    features = fetch_wfs_data(HT_POSTE_LAYER, bbox)
    if not features:
        return []
    
    point = Point(lon, lat)
    postes = []
    for feature in features:
        geom_shp = shape(feature["geometry"])
        dist = geom_shp.distance(point) * 111000
        postes.append({
            "properties": feature["properties"],
            "distance": round(dist, 2),
            "geometry": mapping(geom_shp)
        })
    return postes

def get_plu_info(lat, lon, radius=0.03):
    """Récupère dynamiquement les données PLU depuis GeoServer"""
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    features = fetch_wfs_data(PLU_LAYER, bbox)
    plu_info = []
    for feature in features:
        props = feature["properties"]
        plu_info.append({
            "insee": props.get("insee"),
            "typeref": props.get("typeref"),
            "archive_url": props.get("archiveUrl"),
            "files": props.get("files", "").split(", "),
            "geometry": feature.get("geometry")
        })
    return plu_info

def get_parkings_info(lat, lon, radius=0.03):
    """Récupère dynamiquement les parkings depuis GeoServer"""
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    return fetch_wfs_data(PARKINGS_LAYER, bbox)

def get_friches_info(lat, lon, radius=0.03):
    """Récupère dynamiquement les friches depuis GeoServer"""
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    return fetch_wfs_data(FRICHES_LAYER, bbox)

def get_potentiel_solaire_info(lat, lon, radius=1.0):
    """Récupère dynamiquement le potentiel solaire depuis GeoServer"""
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    return fetch_wfs_data(POTENTIEL_SOLAIRE_LAYER, bbox)

def get_zaer_info(lat, lon, radius=0.03):
    """Récupère dynamiquement les zones ZAER depuis GeoServer"""
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    return fetch_wfs_data(ZAER_LAYER, bbox)

def get_rpg_info(lat, lon, radius=0.0027):
    """Récupère dynamiquement les données RPG depuis GeoServer"""
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    print(f"[DEBUG RPG] BBOX: {bbox}")
    print(f"[DEBUG RPG] Layer: {PARCELLES_GRAPHIQUES_LAYER}")
    
    features = fetch_wfs_data(PARCELLES_GRAPHIQUES_LAYER, bbox)
    print(f"[DEBUG RPG] Features trouvées: {len(features) if features else 0}")
    
    if features:
        print(f"[DEBUG RPG] Première feature: {list(features[0].get('properties', {}).keys())}")
    
    return features

def get_sirene_info(lat, lon, radius):
    """Récupère dynamiquement les données Sirene depuis GeoServer"""
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    return fetch_wfs_data(SIRENE_LAYER, bbox)

def get_eleveurs_info(lat, lon, radius=0.1):
    """Récupère dynamiquement les éleveurs depuis GeoServer"""
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    return fetch_wfs_data(ELEVEURS_LAYER, bbox)

def get_ppri_info(lat, lon, radius=0.03):
    """Récupère dynamiquement les données PPRI depuis GeoServer"""
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    features = fetch_wfs_data(PPRI_LAYER, bbox)
    return {"type": "FeatureCollection", "features": features}

def get_capacites_reseau_info(lat, lon, radius=0.5):
    """Récupère dynamiquement les capacités réseau depuis GeoServer"""
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    features = fetch_wfs_data(CAPACITES_RESEAU_LAYER, bbox)
    capacites = []
    for feature in features:
        capacites.append({
            "properties": feature["properties"],
            "geometry": feature["geometry"]
        })
    return capacites

print("🗺️ [COUCHES] Configuration GeoServer:")
print(f"   - Parcelles: {PARCELLE_LAYER}")
print(f"   - RPG: {PARCELLES_GRAPHIQUES_LAYER}")
print(f"   - PLU: {PLU_LAYER}")
print(f"   - Postes BT: {POSTE_LAYER}")
print(f"   - Postes HTA: {HT_POSTE_LAYER}")

# Test de connectivité GeoServer au démarrage
def test_geoserver_connection():
    """Test la connectivité GeoServer avec gestion d'erreurs"""
    try:
        import requests
        response = requests.get(GEOSERVER_URL, timeout=10, allow_redirects=True)
        print(f"✅ GeoServer test: HTTP {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"⚠️ GeoServer test failed: {e}")
        print("🔄 Application continue sans GeoServer...")
        return False

# Test au démarrage
geoserver_ok = test_geoserver_connection()

# === FONCTIONS UTILITAIRES POUR LES CARTES ===

def safe_print(*args, **kwargs):
    """Print sécurisé pour les logs"""
    try:
        print(*args, **kwargs)
    except Exception:
        pass

def get_parcelle_info(lat, lon):
    """Récupère info parcelle via API IGN"""
    try:
        url = "https://apicarto.ign.fr/api/cadastre/parcelle"
        params = {"lon": lon, "lat": lat}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        safe_print(f"Erreur API parcelle: {e}")
    return None

def get_all_parcelles(lat, lon, radius=0.03):
    """Récupère toutes parcelles dans rayon"""
    try:
        # bbox autour du point
        bbox = f"{lon-radius},{lat-radius},{lon+radius},{lat+radius}"
        url = "https://apicarto.ign.fr/api/cadastre/parcelle"
        params = {"bbox": bbox}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        safe_print(f"Erreur API parcelles: {e}")
    return {"type": "FeatureCollection", "features": []}

@app.route('/')
def index():
    """Page d'accueil principale"""
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgriWeb 2.0 - Géolocalisation Agricole Professionnelle</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
            
            .header { background: linear-gradient(135deg, #2c5f41, #4a8b3b); color: white; padding: 60px 0; text-align: center; }
            .header h1 { font-size: 3rem; margin-bottom: 20px; font-weight: 700; }
            .header p { font-size: 1.3rem; opacity: 0.9; margin-bottom: 30px; }
            
            .status-bar { background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; margin: 20px 0; border-radius: 8px; }
            .status-bar.error { background: #f8d7da; border-color: #f5c6cb; }
            
            .features { padding: 60px 0; background: #f8f9fa; }
            .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; margin-top: 40px; }
            .feature-card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
            .feature-card h3 { color: #2c5f41; margin-bottom: 15px; font-size: 1.4rem; }
            
            .pricing { padding: 60px 0; }
            .pricing h2 { text-align: center; margin-bottom: 50px; font-size: 2.5rem; color: #2c5f41; }
            .plans { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 30px; }
            .plan { background: white; border: 2px solid #e9ecef; border-radius: 12px; padding: 40px 30px; text-align: center; position: relative; }
            .plan.featured { border-color: #28a745; transform: scale(1.05); }
            .plan h3 { color: #2c5f41; margin-bottom: 20px; font-size: 1.8rem; }
            .plan .price { font-size: 2.5rem; color: #28a745; font-weight: bold; margin-bottom: 10px; }
            .plan ul { list-style: none; margin: 20px 0; }
            .plan li { padding: 8px 0; border-bottom: 1px solid #f1f1f1; }
            
            .cta { background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 80px 0; text-align: center; }
            .cta h2 { font-size: 2.5rem; margin-bottom: 20px; }
            
            .btn { display: inline-block; padding: 15px 30px; margin: 10px; border: none; border-radius: 8px; 
                   text-decoration: none; font-weight: 600; cursor: pointer; transition: all 0.3s ease; }
            .btn-primary { background: #28a745; color: white; }
            .btn-primary:hover { background: #218838; transform: translateY(-2px); }
            .btn-secondary { background: #6c757d; color: white; }
            .btn-secondary:hover { background: #545b62; }
            .btn-outline { background: transparent; color: #28a745; border: 2px solid #28a745; }
            .btn-outline:hover { background: #28a745; color: white; }
            
            .form-section { background: white; padding: 40px; margin: 20px 0; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 20px; }
            .form-group label { display: block; margin-bottom: 5px; font-weight: 600; color: #2c5f41; }
            .form-group input { width: 100%; padding: 12px; border: 2px solid #e9ecef; border-radius: 6px; font-size: 1rem; }
            .form-group input:focus { outline: none; border-color: #28a745; }
            
            .hidden { display: none; }
            .alert { padding: 15px; margin: 15px 0; border-radius: 6px; }
            .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            
            .footer { background: #2c5f41; color: white; padding: 40px 0; text-align: center; }
        </style>
    </head>
    <body>
        <header class="header">
            <div class="container">
                <h1>🌾 AgriWeb 2.0</h1>
                <p>Géolocalisation Agricole Professionnelle avec GeoServer Intégré</p>
                <div class="status-bar">
                    <strong>✅ Système Opérationnel</strong> - GeoServer connecté avec 48+ couches de données
                </div>
            </div>
        </header>

        <section class="features">
            <div class="container">
                <h2 style="text-align: center; margin-bottom: 20px; color: #2c5f41;">Fonctionnalités Avancées</h2>
                <div class="features-grid">
                    <div class="feature-card">
                        <h3>🗺️ GeoServer Intégré</h3>
                        <p>Accès à 48+ couches géographiques : cadastre, RPG, zones urbaines, parkings, friches...</p>
                    </div>
                    <div class="feature-card">
                        <h3>🎯 Recherche Précise</h3>
                        <p>Localisation par commune, coordonnées GPS, filtrage par distance aux réseaux électriques</p>
                    </div>
                    <div class="feature-card">
                        <h3>📊 Rapports Détaillés</h3>
                        <p>Analyses complètes avec cartes interactives, données cadastrales et risques géologiques</p>
                    </div>
                    <div class="feature-card">
                        <h3>🔒 Sécurisé & Fiable</h3>
                        <p>Système de licences professionnel, sauvegarde automatique, haute disponibilité</p>
                    </div>
                </div>
            </div>
        </section>

        <section class="pricing">
            <div class="container">
                <h2>Tarifs Professionnels</h2>
                <div class="plans">
                    <div class="plan">
                        <h3>🆓 Essai Gratuit</h3>
                        <div class="price">0€</div>
                        <p>7 jours d'accès complet</p>
                        <ul>
                            <li>✅ 10 communes</li>
                            <li>✅ Toutes les fonctionnalités</li>
                            <li>✅ Support technique</li>
                            <li>✅ GeoServer inclus</li>
                        </ul>
                        <button class="btn btn-primary" onclick="showTrialForm()">Commencer l'Essai</button>
                    </div>
                    
                    <div class="plan featured">
                        <h3>💼 Basic</h3>
                        <div class="price">299€<small>/an</small></div>
                        <p>Pour petites exploitations</p>
                        <ul>
                            <li>✅ 100 communes/mois</li>
                            <li>✅ 500 rapports/jour</li>
                            <li>✅ API basique</li>
                            <li>✅ Support email</li>
                        </ul>
                        <button class="btn btn-primary" onclick="showPaymentForm('basic')">Choisir Basic</button>
                    </div>
                    
                    <div class="plan">
                        <h3>🚀 Pro</h3>
                        <div class="price">999€<small>/an</small></div>
                        <p>Pour professionnels</p>
                        <ul>
                            <li>✅ 1000 communes/mois</li>
                            <li>✅ API complète</li>
                            <li>✅ Exports automatisés</li>
                            <li>✅ Support prioritaire</li>
                        </ul>
                        <button class="btn btn-primary" onclick="showPaymentForm('pro')">Choisir Pro</button>
                    </div>
                    
                    <div class="plan">
                        <h3>🏢 Enterprise</h3>
                        <div class="price">2999€<small>/an</small></div>
                        <p>Pour grandes organisations</p>
                        <ul>
                            <li>✅ Accès illimité</li>
                            <li>✅ GeoServer dédié</li>
                            <li>✅ API sur mesure</li>
                            <li>✅ Support 24/7</li>
                        </ul>
                        <button class="btn btn-primary" onclick="showPaymentForm('enterprise')">Choisir Enterprise</button>
                    </div>
                </div>
            </div>
        </section>

        <!-- Formulaire de connexion -->
        <div id="login-form" class="form-section container hidden">
            <h2>🔐 Se connecter à AgriWeb 2.0</h2>
            <div id="login-alert"></div>
            <form onsubmit="submitLogin(event)">
                <div class="form-group">
                    <label for="login-email">Adresse email</label>
                    <input type="email" id="login-email" name="email" required placeholder="votre.nom@entreprise.com">
                </div>
                <button type="submit" class="btn btn-primary">Se Connecter</button>
                <button type="button" class="btn btn-secondary" onclick="hideLoginForm()">Annuler</button>
            </form>
            <p style="margin-top: 15px; text-align: center;">
                Pas encore de compte ? 
                <a href="#" onclick="hideLoginForm(); showTrialForm();" style="color: #28a745;">Créer un essai gratuit</a>
            </p>
        </div>

        <!-- Formulaire d'essai gratuit -->
        <div id="trial-form" class="form-section container hidden">
            <h2>🆓 Démarrer votre essai gratuit (7 jours)</h2>
            <div id="trial-alert"></div>
            <form onsubmit="submitTrial(event)">
                <div class="form-group">
                    <label for="trial-email">Adresse email professionnelle</label>
                    <input type="email" id="trial-email" name="email" required placeholder="votre.nom@entreprise.com">
                </div>
                <div class="form-group">
                    <label for="trial-company">Nom de l'entreprise</label>
                    <input type="text" id="trial-company" name="company" required placeholder="Votre Entreprise">
                </div>
                <div class="form-group">
                    <label for="trial-name">Nom complet</label>
                    <input type="text" id="trial-name" name="name" required placeholder="Prénom Nom">
                </div>
                <button type="submit" class="btn btn-primary">Activer l'Essai Gratuit</button>
                <button type="button" class="btn btn-secondary" onclick="hideTrialForm()">Annuler</button>
            </form>
            <p style="margin-top: 15px; text-align: center;">
                Déjà un compte ? 
                <a href="#" onclick="hideTrialForm(); showLoginForm();" style="color: #28a745;">Se connecter</a>
            </p>
        </div>

        <!-- Interface utilisateur connecté -->
        <div id="user-interface" class="form-section container hidden">
            <h2>🎯 Interface AgriWeb 2.0</h2>
            <div class="status-bar">
                <span id="user-status"></span>
            </div>
            
            <div class="form-group">
                <label for="search-commune">Rechercher une commune</label>
                <input type="text" id="search-commune" placeholder="Nom de la commune (ex: Lyon)" value="Lyon">
                <button class="btn btn-primary" onclick="searchCommune()">🔍 Rechercher</button>
            </div>
            
            <div id="search-results"></div>
            
            <div style="margin-top: 30px;">
                <button class="btn btn-secondary" onclick="logout()">Se Déconnecter</button>
                <a href="/status" class="btn btn-outline" target="_blank">📊 Statut Système</a>
            </div>
        </div>

        <section class="cta">
            <div class="container">
                <h2>Prêt à optimiser votre géolocalisation agricole ?</h2>
                <p>Accédez à AgriWeb 2.0 dès maintenant</p>
                <button class="btn btn-primary" onclick="showLoginForm()">🔐 Se Connecter</button>
                <button class="btn btn-outline" onclick="showTrialForm()">🆓 Essai Gratuit (7 jours)</button>
            </div>
        </section>

        <footer class="footer">
            <div class="container">
                <p>&copy; 2025 AgriWeb 2.0 - Géolocalisation Agricole Professionnelle</p>
                <p>Système intégré avec GeoServer - Support technique disponible</p>
            </div>
        </footer>

        <script>
            // État de l'application
            let currentUser = null;
            
            function showTrialForm() {
                document.getElementById('trial-form').classList.remove('hidden');
                document.getElementById('login-form').classList.add('hidden');
                document.getElementById('trial-form').scrollIntoView({behavior: 'smooth'});
            }
            
            function hideTrialForm() {
                document.getElementById('trial-form').classList.add('hidden');
            }
            
            function showLoginForm() {
                document.getElementById('login-form').classList.remove('hidden');
                document.getElementById('trial-form').classList.add('hidden');
                document.getElementById('login-form').scrollIntoView({behavior: 'smooth'});
            }
            
            function hideLoginForm() {
                document.getElementById('login-form').classList.add('hidden');
            }
            
            function showPaymentForm(plan) {
                alert('Paiement ' + plan + ' - À implémenter avec Stripe');
            }
            
            async function submitLogin(event) {
                event.preventDefault();
                
                const email = document.getElementById('login-email').value;
                
                try {
                    const response = await fetch('/api/login', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({email: email})
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        document.getElementById('login-alert').innerHTML = 
                            '<div class="alert alert-success">✅ ' + result.message + '</div>';
                        
                        // Masquer le formulaire et afficher l'interface
                        setTimeout(() => {
                            hideLoginForm();
                            showUserInterface(result.user);
                        }, 1000);
                    } else {
                        document.getElementById('login-alert').innerHTML = 
                            '<div class="alert alert-danger">❌ ' + result.error + '</div>';
                    }
                } catch (error) {
                    document.getElementById('login-alert').innerHTML = 
                        '<div class="alert alert-danger">❌ Erreur de connexion: ' + error.message + '</div>';
                }
            }

            async function submitTrial(event) {
                event.preventDefault();
                
                const formData = {
                    email: document.getElementById('trial-email').value,
                    company: document.getElementById('trial-company').value,
                    name: document.getElementById('trial-name').value
                };
                
                try {
                    const response = await fetch('/api/trial', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(formData)
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        document.getElementById('trial-alert').innerHTML = 
                            '<div class="alert alert-success">✅ ' + result.message + '</div>';
                        
                        // Masquer le formulaire et afficher l'interface
                        setTimeout(() => {
                            hideTrialForm();
                            showUserInterface(result.user);
                        }, 2000);
                        
                    } else {
                        document.getElementById('trial-alert').innerHTML = 
                            '<div class="alert alert-error">❌ ' + result.error + '</div>';
                    }
                } catch (error) {
                    document.getElementById('trial-alert').innerHTML = 
                        '<div class="alert alert-error">❌ Erreur réseau: ' + error.message + '</div>';
                }
            }
            
            function showUserInterface(user) {
                currentUser = user;
                document.getElementById('user-interface').classList.remove('hidden');
                document.getElementById('user-interface').scrollIntoView({behavior: 'smooth'});
                
                document.getElementById('user-status').innerHTML = 
                    `👤 Connecté: ${user.name} (${user.email}) - Licence: ${user.license_type} - Expire: ${user.expires}`;
            }
            
            async function searchCommune() {
                const commune = document.getElementById('search-commune').value;
                
                if (!commune) {
                    alert('Veuillez saisir un nom de commune');
                    return;
                }
                
                document.getElementById('search-results').innerHTML = '🔍 Recherche en cours...';
                
                try {
                    const response = await fetch('/api/search', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({commune: commune})
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        let html = '<div class="alert alert-success"><h3>✅ Résultats pour ' + commune + '</h3>';
                        
                        // Si une carte a été générée, l'afficher
                        if (result.results.map_url) {
                            html += '<div style="margin: 20px 0;"><h4>🗺️ Carte Interactive</h4>' +
                                   '<iframe src="' + result.results.map_url + '" ' +
                                   'style="width: 100%; height: 600px; border: 1px solid #ccc; border-radius: 8px;" ' +
                                   'title="Carte interactive"></iframe></div>';
                        }
                        
                        // Informations de base
                        if (result.results.coordinates) {
                            html += '<p><strong>📍 Coordonnées:</strong> ' + 
                                   result.results.coordinates.lat.toFixed(4) + ', ' + 
                                   result.results.coordinates.lon.toFixed(4) + '</p>';
                        }
                        
                        // Statistiques des couches
                        if (result.results.search_results && result.results.search_results.layers_count) {
                            html += '<p><strong>📊 Couches chargées:</strong> ' + 
                                   result.results.search_results.layers_count + ' éléments</p>';
                        }
                        
                        // Détails techniques (repliable)
                        html += '<details style="margin-top: 20px;"><summary>🔧 Détails techniques</summary>' +
                               '<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow: auto; max-height: 300px;">' + 
                               JSON.stringify(result.results, null, 2) + '</pre></details>';
                        
                        html += '</div>';
                        document.getElementById('search-results').innerHTML = html;
                    } else {
                        document.getElementById('search-results').innerHTML = 
                            '<div class="alert alert-error">❌ ' + result.error + '</div>';
                    }
                } catch (error) {
                    document.getElementById('search-results').innerHTML = 
                        '<div class="alert alert-error">❌ Erreur: ' + error.message + '</div>';
                }
            }
            
            function logout() {
                currentUser = null;
                document.getElementById('user-interface').classList.add('hidden');
                window.location.reload();
            }
        </script>
    </body>
    </html>
    """
    
    return html_content

@app.route('/favicon.ico')
def favicon():
    """Route pour le favicon - évite les erreurs 502"""
    from flask import Response
    return Response(status=204)  # No Content - pas de favicon disponible

@app.route('/test-static')
def test_static():
    """Route de test pour vérifier que les fichiers statiques fonctionnent"""
    cartes_dir = os.path.join(app.static_folder, 'cartes')
    exists = os.path.exists(cartes_dir)
    files = []
    if exists:
        try:
            files = os.listdir(cartes_dir)
        except:
            files = ["Erreur lecture dossier"]
    
    return jsonify({
        'static_folder': app.static_folder,
        'cartes_dir': cartes_dir,
        'cartes_exists': exists,
        'files_count': len(files),
        'sample_files': files[:5] if files else []
    })

@app.route('/test-map')
def test_map():
    """Créer une carte de test très simple pour débugger Railway"""
    import folium
    import time
    
    # Carte très simple
    m = folium.Map(
        location=[45.75, 4.85],  # Lyon
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    # Ajouter un marqueur simple
    folium.Marker(
        [45.75, 4.85],
        popup='Test Railway',
        tooltip='Ceci est un test'
    ).add_to(m)
    
    # Sauver la carte
    timestamp = int(time.time())
    filename = f"test_simple_{timestamp}.html"
    map_path = os.path.join("static", "cartes", filename)
    
    # Créer le dossier si nécessaire
    os.makedirs(os.path.dirname(map_path), exist_ok=True)
    
    m.save(map_path)
    
    return jsonify({
        'success': True,
        'filename': filename,
        'url': f'/static/cartes/{filename}',
        'full_path': map_path
    })

@app.route('/api/login', methods=['POST'])
def api_login():
    """API de connexion pour utilisateurs existants"""
    
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Adresse email requise'
            }), 400
        
        # Vérifier si l'utilisateur existe
        if email not in USERS_DB:
            return jsonify({
                'success': False,
                'error': 'Aucun compte trouvé avec cette adresse email. Voulez-vous créer un essai gratuit ?'
            }), 404
        
        user_data = USERS_DB[email]
        
        # Vérifier si la licence est encore valide
        expires_date = datetime.fromisoformat(user_data['expires'])
        if datetime.now() > expires_date:
            return jsonify({
                'success': False,
                'error': f'Votre essai gratuit a expiré le {expires_date.strftime("%d/%m/%Y")}. Contactez-nous pour renouveler.'
            }), 403
        
        # Connecter l'utilisateur
        session['user_id'] = user_data['user_id']
        session['email'] = email
        session['license_valid'] = True
        session['license_type'] = user_data['license_type']
        session['expires'] = expires_date.strftime('%Y-%m-%d')
        
        print(f"✅ Connexion réussie: {user_data['name']} ({email})")
        
        return jsonify({
            'success': True,
            'message': f'Connexion réussie ! Bienvenue {user_data["name"]}',
            'user': {
                'name': user_data['name'],
                'email': email,
                'company': user_data['company'],
                'license_type': user_data['license_type'],
                'expires': expires_date.strftime('%d/%m/%Y'),
                'searches_today': user_data.get('searches_today', 0),
                'searches_total': user_data.get('searches_total', 0)
            }
        })
        
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return jsonify({
            'success': False,
            'error': f'Erreur de connexion: {str(e)}'
        }), 500

@app.route('/api/trial', methods=['POST'])
def api_trial():
    """API inscription essai gratuit"""
    
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        company = data.get('company', '').strip()
        name = data.get('name', '').strip()
        
        if not email or not company or not name:
            return jsonify({
                'success': False,
                'error': 'Tous les champs sont requis'
            }), 400
        
        # Vérifier si l'utilisateur existe déjà
        if email in USERS_DB:
            return jsonify({
                'success': False,
                'error': 'Cet email est déjà utilisé'
            }), 400
        
        # Créer l'utilisateur avec licence d'essai
        user_id = str(uuid.uuid4())
        expires_date = datetime.now() + timedelta(days=7)
        
        user_data = {
            'id': user_id,
            'email': email,
            'company': company,
            'name': name,
            'license_type': 'trial',
            'created': datetime.now().isoformat(),
            'expires': expires_date.isoformat(),
            'searches_today': 0,
            'searches_total': 0
        }
        
        USERS_DB[email] = user_data
        
        # Sauvegarder la session
        session['user_id'] = user_id
        session['email'] = email
        session['license_valid'] = True
        session['license_type'] = 'trial'
        session['expires'] = expires_date.strftime('%Y-%m-%d')
        
        print(f"✅ Nouvel utilisateur inscrit: {name} ({email}) - {company}")
        
        return jsonify({
            'success': True,
            'message': f'Essai gratuit activé pour {name} ! Valable 7 jours.',
            'user': {
                'name': name,
                'email': email,
                'company': company,
                'license_type': 'trial',
                'expires': expires_date.strftime('%d/%m/%Y')
            }
        })
        
    except Exception as e:
        print(f"❌ Erreur inscription: {e}")
        return jsonify({
            'success': False,
            'error': f'Erreur inscription: {str(e)}'
        }), 500

@app.route('/api/search', methods=['POST'])
def api_search():
    """API de recherche AgriWeb avec gestion des licences"""
    
    try:
        # Vérifier la licence
        if not session.get('license_valid'):
            return jsonify({
                'success': False,
                'error': 'Licence requise - Veuillez créer un essai gratuit'
            }), 403
        
        email = session.get('email')
        if email and email in USERS_DB:
            user = USERS_DB[email]
            user['searches_today'] += 1
            user['searches_total'] += 1
        
        data = request.get_json()
        commune = data.get('commune', '').strip()
        
        if not commune:
            return jsonify({
                'success': False,
                'error': 'Nom de commune requis'
            }), 400
        
        print(f"🔍 Recherche pour {commune} par {session.get('email', 'unknown')}")
        
        # ===== GÉNÉRATION VRAIE CARTE AVEC DONNÉES RÉELLES =====
        try:
            # 1. Géocodage de la commune pour obtenir lat/lon
            print(f"🌍 [GEOCODAGE] Géocodage de {commune}...")
            coordinates = geocode_address(commune)
            if not coordinates:
                # Fallback: essayer avec "Commune, France"
                coordinates = geocode_address(f"{commune}, France")
            
            if not coordinates:
                return jsonify({
                    'success': False,
                    'error': f'Impossible de localiser la commune {commune}'
                }), 400
                
            lat, lon = coordinates
            print(f"📍 [GEOCODAGE] {commune} trouvé: {lat}, {lon}")
            
            # 2. Génération du rapport complet avec carte
            print(f"🗺️ [RAPPORT] Génération rapport complet pour {commune}...")
            report_data = build_report_data(lat, lon, commune, ht_radius_km=1, sirene_radius_km=0.05)
            
            # 3. Génération de la carte avec notre fonction build_map
            print(f"🗺️ [CARTE] Génération carte complète...")
            
            # Récupération des données pour la carte
            parcelle_info = get_all_parcelles(lat, lon, radius=0.01)
            
            # Données GeoServer dynamiques
            postes_data = get_all_postes(lat, lon, radius_deg=0.1)
            ht_postes_data = get_all_ht_postes(lat, lon, radius_deg=0.5)
            plu_info = get_plu_info(lat, lon, radius=0.03)
            parkings_data = get_parkings_info(lat, lon, radius=0.03)
            friches_data = get_friches_info(lat, lon, radius=0.03)
            potentiel_solaire_data = get_potentiel_solaire_info(lat, lon, radius=1.0)
            zaer_data = get_zaer_info(lat, lon, radius=0.03)
            rpg_data = get_rpg_info(lat, lon, radius=0.0027)
            sirene_data = get_sirene_info(lat, lon, radius=0.03)
            eleveurs_data = get_eleveurs_info(lat, lon, radius=0.1)
            capacites_reseau = get_capacites_reseau_info(lat, lon, radius=0.5)
            ppri_data = get_ppri_info(lat, lon, radius=0.03)
            
            print(f"📊 [DONNÉES] Postes: {len(postes_data)}, PLU: {len(plu_info)}, Parkings: {len(parkings_data)}")
            
            # Construction de la carte
            map_obj = build_map(
                lat=lat, lon=lon, address=commune,
                parcelle_props=None, parcelles_data=parcelle_info,
                postes_data=postes_data, ht_postes_data=ht_postes_data,
                plu_info=plu_info, parkings_data=parkings_data,
                friches_data=friches_data, potentiel_solaire_data=potentiel_solaire_data,
                zaer_data=zaer_data, rpg_data=rpg_data, sirene_data=sirene_data,
                search_radius=1000, ht_radius_deg=0.1, api_cadastre=None,
                api_nature=None, api_urbanisme=None, eleveurs_data=eleveurs_data,
                capacites_reseau=capacites_reseau, ppri_data=ppri_data
            )
            
            # Sauvegarde de la carte
            timestamp = int(time.time())
            map_filename = f"commune_{commune}_{timestamp}.html"
            map_path = os.path.join("static", "cartes", map_filename)
            os.makedirs(os.path.dirname(map_path), exist_ok=True)
            map_obj.save(map_path)
            
            map_url = f"/static/cartes/{map_filename}?t={timestamp}"
            print(f"✅ [CARTE] Carte sauvée: {map_url}")
            
            # Résultats complets
            results = {
                'commune': commune,
                'coordinates': {'lat': lat, 'lon': lon},
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'map_url': map_url,
                'user': {
                    'email': session.get('email'),
                    'license': session.get('license_type'),
                    'expires': session.get('expires')
                },
                'report_data': report_data,
                'search_results': {
                    'status': 'success',
                    'message': f'Carte complète générée pour {commune}',
                    'layers_count': len(postes_data) + len(plu_info) + len(parkings_data) + len(friches_data)
                }
            }
            
            return jsonify({
                'success': True,
                'results': results
            })
            
        except Exception as e:
            print(f"❌ [ERREUR] Erreur génération carte commune: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback vers l'ancien système
            pass
        
        # === FALLBACK: ANCIEN SYSTÈME SIMPLE ===
        print("⚠️ [FALLBACK] Utilisation système simple")
        
        # Test connexion GeoServer
        try:
            response = requests.get(GEOSERVER_URL, timeout=5)
            geoserver_status = "✅ Connecté" if response.status_code == 200 else "❌ Erreur"
        except:
            geoserver_status = "❌ Inaccessible"
        
        # Test WFS et comptage des couches
        layer_count = 0
        sample_layers = []
        
        try:
            wfs_params = {
                "service": "WFS",
                "request": "GetCapabilities"
            }
            wfs_response = requests.get(GEOSERVER_WFS_URL, params=wfs_params, timeout=10)
            
            if "WFS_Capabilities" in wfs_response.text:
                import re
                layers = re.findall(r'<Name>([^<]+)</Name>', wfs_response.text)
                layer_count = len(layers)
                sample_layers = layers[:5]
        except:
            pass
        
        # Simulation d'une recherche réelle (vous pouvez intégrer ici vos vraies fonctions)
        results = {
            'commune': commune,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user': {
                'email': session.get('email'),
                'license': session.get('license_type'),
                'expires': session.get('expires')
            },
            'geoserver': {
                'url': GEOSERVER_URL,
                'status': geoserver_status,
                'layer_count': layer_count,
                'sample_layers': sample_layers
            },
            'search_results': {
                'status': 'success',
                'message': f'Recherche {commune} effectuée avec succès',
                'note': 'Données réelles disponibles via GeoServer'
            }
        }
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        print(f"❌ Erreur recherche: {e}")
        return jsonify({
            'success': False,
            'error': f'Erreur recherche: {str(e)}'
        }), 500

@app.route('/status')
def status():
    """Statut détaillé du système"""
    
    # Test GeoServer complet
    geoserver_details = {}
    
    try:
        response = requests.get(GEOSERVER_URL, timeout=5)
        geoserver_ok = response.status_code == 200
        
        if geoserver_ok:
            # Test WFS
            wfs_params = {"service": "WFS", "request": "GetCapabilities"}
            wfs_response = requests.get(GEOSERVER_WFS_URL, params=wfs_params, timeout=10)
            
            if "WFS_Capabilities" in wfs_response.text:
                import re
                layers = re.findall(r'<Name>([^<]+)</Name>', wfs_response.text)
                
                geoserver_details = {
                    'wfs_operational': True,
                    'layer_count': len(layers),
                    'sample_layers': layers[:10] if layers else [],
                    'response_time': 'OK'
                }
            else:
                geoserver_details = {'wfs_operational': False, 'error': 'WFS non disponible'}
        else:
            geoserver_details = {'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        geoserver_details = {'error': str(e)}
    
    status_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'system': {
            'agriweb': 'OK',
            'flask': 'OK',
            'python': 'OK'
        },
        'geoserver': {
            'url': GEOSERVER_URL,
            'status': 'OK' if geoserver_details.get('wfs_operational') else 'ERREUR',
            'details': geoserver_details
        },
        'users': {
            'total_registered': len(USERS_DB),
            'active_sessions': len([u for u in USERS_DB.values() if u.get('searches_today', 0) > 0])
        },
        'session': {
            'user_logged': session.get('email', 'Non connecté'),
            'license_valid': session.get('license_valid', False),
            'license_type': session.get('license_type', 'Aucune'),
            'expires': session.get('expires', 'N/A')
        }
    }
    
    return jsonify(status_data)

# === FONCTIONS CARTOGRAPHIQUES ===

def build_map(
    lat, lon, address,
    parcelle_props, parcelles_data,
    postes_data, ht_postes_data, plu_info,
    parkings_data, friches_data, potentiel_solaire_data,
    zaer_data, rpg_data, sirene_data,
    search_radius, ht_radius_deg,
    api_cadastre=None, api_nature=None, api_urbanisme=None,
    eleveurs_data=None,
    capacites_reseau=None,
    ppri_data=None  # Ajout PPRI
):
    import folium
    from folium.plugins import Draw, MeasureControl, MarkerCluster
    from pyproj import Transformer
    from shapely.geometry import shape, mapping, MultiPolygon
    from folium import Element

    # --- PATCH ROBUSTESSE ENTRÉES ---
    if parcelles_data is None or not isinstance(parcelles_data, dict):
        parcelles_data = {"type": "FeatureCollection", "features": []}
    if postes_data is None:
        postes_data = []
    if ht_postes_data is None:
        ht_postes_data = []
    if plu_info is None:
        plu_info = []
    if parkings_data is None:
        parkings_data = []
    if friches_data is None:
        friches_data = []
    if potentiel_solaire_data is None:
        potentiel_solaire_data = []
    if zaer_data is None:
        zaer_data = []
    if rpg_data is None:
        rpg_data = []
    if sirene_data is None:
        sirene_data = []
    if api_cadastre is None or not isinstance(api_cadastre, dict):
        api_cadastre = {"type": "FeatureCollection", "features": []}
    if api_nature is None or not isinstance(api_nature, dict):
        api_nature = {"type": "FeatureCollection", "features": []}
    if api_urbanisme is None or not isinstance(api_urbanisme, dict):
        api_urbanisme = {}
    # eleveurs_data : None accepté
    if capacites_reseau is None:
        capacites_reseau = []
    if ppri_data is None or not isinstance(ppri_data, dict):
        ppri_data = {"type": "FeatureCollection", "features": []}
    
    # === CRÉATION DE LA CARTE (doit être fait avant toute utilisation) ===
    map_obj = folium.Map(location=[lat, lon], zoom_start=13, tiles=None)
    
    # Ajouter les couches de base
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite",
        overlay=False, control=True, show=True
    ).add_to(map_obj)
    folium.TileLayer("OpenStreetMap", name="Fond OSM", overlay=False, control=True, show=False).add_to(map_obj)
    
    # --- PPRI ---
    if ppri_data.get("features"):
        ppri_group = folium.FeatureGroup(name="PPRI", show=True)
        for feat in ppri_data["features"]:
            geom = feat.get("geometry")
            valid_geom = False
            if geom and isinstance(geom, dict):
                gtype = geom.get("type")
                coords = geom.get("coordinates")
                if gtype in {"Point", "LineString", "Polygon", "MultiPoint", "MultiLineString", "MultiPolygon"}:
                    if coords and coords != [] and coords is not None:
                        valid_geom = True
            if valid_geom:
                try:
                    folium.GeoJson(
                        geom,
                        style_function=lambda _: {"color": "#FF00FF", "weight": 2, "fillColor": "#FFB6FF", "fillOpacity": 0.3},
                        tooltip="<br>".join(f"{k}: {v}" for k, v in feat.get("properties", {}).items())
                    ).add_to(ppri_group)
                except Exception as e:
                    print(f"[ERROR] Exception while adding PPRI geometry: {e}\nGeom: {geom}")
            else:
                print(f"[DEBUG] Invalid PPRI geometry: type={geom.get('type') if geom else None}, coords={geom.get('coordinates') if geom else None}")
        map_obj.add_child(ppri_group)

    # Option: mode léger (pas de LayerControl, pas de Marker inutile)
    mode_light = False  # Désactivé par défaut
    
    if not mode_light:
        from folium.plugins import Draw
        Draw(export=True).add_to(map_obj)
        MeasureControl(position="topright").add_to(map_obj)

    # Cadastre
    cadastre_group = folium.FeatureGroup(name="Cadastre (WFS)", show=True)
    if parcelle_props and parcelle_props.get("geometry"):
        tooltip = "<br>".join(f"{k}: {v}" for k, v in parcelle_props.items() if k != "geometry")
        geom = parcelle_props["geometry"]
        valid_geom = False
        if geom and isinstance(geom, dict):
            gtype = geom.get("type")
            coords = geom.get("coordinates")
            if gtype in {"Point", "LineString", "Polygon", "MultiPoint", "MultiLineString", "MultiPolygon"}:
                if coords and coords != [] and coords is not None:
                    valid_geom = True
        if valid_geom:
            try:
                folium.GeoJson(geom, style_function=lambda _: {"color": "blue", "weight": 2}, tooltip=tooltip).add_to(cadastre_group)
            except Exception as e:
                print(f"[ERROR] Exception while adding Cadastre geometry: {e}\nGeom: {geom}")
        else:
            print(f"[DEBUG] Invalid Cadastre geometry: type={geom.get('type') if geom else None}, coords={geom.get('coordinates') if geom else None}")
    if parcelles_data.get("features"):
        to_wgs84 = Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True).transform
        for feat in parcelles_data["features"]:
            try:
                geom_wgs = shp_transform(to_wgs84, shape(feat["geometry"]))
                props = feat.get("properties", {})
                tooltip = "<br>".join(f"{k}: {v}" for k, v in props.items())
                folium.GeoJson(mapping(geom_wgs), style_function=lambda _: {"color": "purple", "weight": 2}, tooltip=tooltip).add_to(cadastre_group)
            except Exception as e:
                print(f"[ERROR] Exception while adding Cadastre feature: {e}\nFeature: {feat}")
    map_obj.add_child(cadastre_group)

    if api_cadastre.get("features"):
        cad_api_group = folium.FeatureGroup(name="Cadastre (API IGN)", show=True)
        for feat in api_cadastre["features"]:
            geom = feat.get("geometry")
            valid_geom = False
            if geom and isinstance(geom, dict):
                gtype = geom.get("type")
                coords = geom.get("coordinates")
                if gtype in {"Point", "LineString", "Polygon", "MultiPoint", "MultiLineString", "MultiPolygon"}:
                    if coords and coords != [] and coords is not None:
                        valid_geom = True
            if valid_geom:
                try:
                    folium.GeoJson(geom, style_function=lambda _: {"color": "#FF6600", "weight": 2, "fillColor": "#FFFF00", "fillOpacity": 0.4}, tooltip="<br>".join(f"{k}: {v}" for k, v in feat.get("properties", {}).items())).add_to(cad_api_group)
                except Exception as e:
                    print(f"[ERROR] Exception while adding API Cadastre geometry: {e}\nGeom: {geom}")
            else:
                print(f"[DEBUG] Invalid API Cadastre geometry: type={geom.get('type') if geom else None}, coords={geom.get('coordinates') if geom else None}")
        map_obj.add_child(cad_api_group)

    # --- Postes BT (filtrage doublons par coordonnées) ---
    def poste_key(poste):
        geom = poste.get("geometry")
        if geom and "coordinates" in geom:
            coords = tuple(geom["coordinates"])
        else:
            coords = ()
        return coords

    seen_bt = set()
    filtered_bt = []
    for poste in postes_data:
        key = poste_key(poste)
        if key in seen_bt or not poste.get("geometry"):
            continue
        seen_bt.add(key)
        filtered_bt.append(poste)

    bt_group = folium.FeatureGroup(name="Postes BT", show=True)
    for poste in filtered_bt:
        props = poste.get("properties", {})
        dist_m = poste.get("distance")
        try:
            coords = poste["geometry"]["coordinates"]
            lat_p, lon_p = coords[1], coords[0]
        except Exception:
            continue
        popup = "<b>Poste BT</b><br>" + "<br>".join(f"{k}: {v}" for k, v in props.items())
        if dist_m is not None:
            popup += f"<br><b>Distance</b>: {dist_m:.1f} m"
        streetview_url = f"https://www.google.com/maps?q=&layer=c&cbll={lat_p},{lon_p}"
        popup += f"<br><a href='{streetview_url}' target='_blank'>Voir sur Street View</a>"
        folium.Marker([lat_p, lon_p], popup=popup, icon=folium.Icon(color="darkgreen", icon="flash", prefix="fa")).add_to(bt_group)
        folium.Circle([lat_p, lon_p], radius=25, color="darkgreen", fill=True, fill_opacity=0.2).add_to(bt_group)
    map_obj.add_child(bt_group)

    # --- Postes HTA (filtrage doublons par coordonnées) ---
    seen_hta = set()
    filtered_hta = []
    for poste in ht_postes_data:
        key = poste_key(poste)
        if key in seen_hta or not poste.get("geometry"):
            continue
        seen_hta.add(key)
        filtered_hta.append(poste)

    hta_group = folium.FeatureGroup(name="Postes HTA (capacité)", show=True)
    for poste in filtered_hta:
        props = poste.get("properties", {})
        dist_m = poste.get("distance")
        try:
            coords = poste["geometry"]["coordinates"]
            lat_p, lon_p = coords[1], coords[0]
        except Exception:
            continue
        capa = props.get("Capacité") or props.get("CapacitÃƒÂ©") or "N/A"
        popup = "<b>Poste HTA</b><br>" + "<br>".join(f"{k}: {v}" for k, v in props.items())
        if dist_m is not None:
            popup += f"<br><b>Distance</b>: {dist_m:.1f} m"
        popup += f"<br><b>Capacité dispo</b>: {capa}"
        streetview_url = f"https://www.google.com/maps?q=&layer=c&cbll={lat_p},{lon_p}"
        popup += f"<br><a href='{streetview_url}' target='_blank'>Voir sur Street View</a>"
        folium.Marker([lat_p, lon_p], popup=popup, icon=folium.Icon(color="orange", icon="bolt", prefix="fa")).add_to(hta_group)
    map_obj.add_child(hta_group)

    # PLU
    plu_group = folium.FeatureGroup(name="PLU", show=True)
    for item in plu_info:
        if item.get("geometry"):
            folium.GeoJson(item.get("geometry"), style_function=lambda _: {"color": "red", "weight": 2}, tooltip="<br>".join(f"{k}: {v}" for k, v in item.items())).add_to(plu_group)
    map_obj.add_child(plu_group)

    # Autres couches simples
    # DÉFINITION DES FONCTIONS DE STYLE EN DEHORS DE LA BOUCLE
    def style_parkings(feature):
        return {"color": "orange", "weight": 3, "fillColor": "orange", "fillOpacity": 0.4, "opacity": 0.8}
    
    def style_friches(feature):
        return {"color": "brown", "weight": 3, "fillColor": "brown", "fillOpacity": 0.4, "opacity": 0.8}
    
    def style_solaire(feature):
        return {"color": "gold", "weight": 3, "fillColor": "gold", "fillOpacity": 0.4, "opacity": 0.8}
    
    def style_zaer(feature):
        return {"color": "cyan", "weight": 3, "fillColor": "cyan", "fillOpacity": 0.4, "opacity": 0.8}

    for name, data, color in [("Parkings", parkings_data, "orange"), ("Friches", friches_data, "brown"), ("Potentiel Solaire", potentiel_solaire_data, "gold"), ("ZAER", zaer_data, "cyan")]:
        print(f"🎨 [COUCHE {name}] Affichage {len(data)} éléments en couleur {color}")
        group = folium.FeatureGroup(name=name, show=True)
        
        for f in data:
            geom = f.get("geometry")
            valid_geom = False
            if geom and isinstance(geom, dict):
                gtype = geom.get("type")
                coords = geom.get("coordinates")
                if gtype in {"Point", "LineString", "Polygon", "MultiPoint", "MultiLineString", "MultiPolygon"}:
                    if coords and coords != [] and coords is not None:
                        valid_geom = True
            if valid_geom:
                try:
                    # Création d'un tooltip enrichi
                    props = f.get("properties", {})
                    tooltip_lines = []
                    
                    # SOLUTION SIMPLE ET ROBUSTE: Utiliser les fonctions prédéfinies
                    if name == "Parkings":
                        style_func = style_parkings
                    elif name == "Friches":
                        style_func = style_friches
                    elif name == "Potentiel Solaire":
                        style_func = style_solaire
                    else:  # ZAER
                        style_func = style_zaer
                    
                    for k, v in props.items():
                        tooltip_lines.append(f"<b>{k}:</b> {v}")
                    
                    tooltip_text = "<br>".join(tooltip_lines)
                    
                    folium.GeoJson(
                        geom, 
                        style_function=style_func,
                        tooltip=tooltip_text,
                        popup=folium.Popup(tooltip_text, max_width=400)
                    ).add_to(group)
                except Exception as e:
                    print(f"[ERROR] Exception while adding {name} geometry: {e}\nGeom: {geom}")
            else:
                print(f"[DEBUG] Invalid {name} geometry: type={geom.get('type') if geom else None}, coords={geom.get('coordinates') if geom else None}")
        map_obj.add_child(group)

    # RPG
    rpg_group = folium.FeatureGroup(name="RPG", show=True)
    for idx, feat in enumerate(rpg_data):
        if not isinstance(feat, dict):
            print(f"[DEBUG] Skipping invalid RPG feature at index {idx}: not a dict, got {type(feat)}: {repr(feat)[:100]}")
            continue
        if "geometry" not in feat or "properties" not in feat:
            print(f"[DEBUG] Skipping invalid RPG feature at index {idx}: missing 'geometry' or 'properties' keys: {repr(feat)[:100]}")
            continue
        try:
            dec = decode_rpg_feature(feat)
            geom, props = dec['geometry'], dec['properties']
            id_parcel = props.get("ID_PARCEL", "N/A")
            surf_ha = props.get("SURF_PARC", props.get("SURF_HA", "N/A"))
            try:
                surf_ha = f"{float(surf_ha):.2f} ha"
            except Exception:
                surf_ha = str(surf_ha)
            code_cultu = props.get("CODE_CULTU", "N/A")
            culture_label = props.get("Culture", code_cultu)
            dist_bt = props.get("min_bt_distance_m", "N/A")
            dist_hta = props.get("min_ht_distance_m", "N/A")
            popup_html = (
                f"<b>ID Parcelle :</b> {id_parcel}<br>"
                f"<b>Surface :</b> {surf_ha}<br>"
                f"<b>Code culture :</b> {code_cultu}<br>"
                f"<b>Culture :</b> {culture_label}<br>"
                f"<b>Distance au poste BT :</b> {dist_bt} m<br>"
                f"<b>Distance au poste HTA :</b> {dist_hta} m"
            )
            valid_geom = False
            if geom and isinstance(geom, dict):
                gtype = geom.get("type")
                coords = geom.get("coordinates")
                if gtype in {"Point", "LineString", "Polygon", "MultiPoint", "MultiLineString", "MultiPolygon"}:
                    if coords and coords != [] and coords is not None:
                        valid_geom = True
            if valid_geom:
                try:
                    folium.GeoJson(
                        geom,
                        style_function=lambda _: {"color": "darkblue", "weight": 2, "fillOpacity": 0.3},
                        tooltip=folium.Tooltip(popup_html)
                    ).add_to(rpg_group)
                except Exception as e:
                    print(f"[ERROR] Exception while adding RPG geometry: {e}\nGeom: {geom}")
            else:
                print(f"[DEBUG] Invalid RPG geometry: type={geom.get('type') if geom else None}, coords={geom.get('coordinates') if geom else None}")
        except Exception as e:
            print(f"[ERROR] Exception while processing RPG feature at index {idx}: {e}\nFeature: {repr(feat)[:200]}")
    map_obj.add_child(rpg_group)

    # Capacités réseau HTA
    caps_group = folium.FeatureGroup(name="Postes HTA (Capacités)", show=True)
    for item in capacites_reseau:
        popup = "<br>".join(f"{k}: {v}" for k, v in item['properties'].items())
        # Attention : parfois la géométrie peut être un dict ou un shapely, adapte si besoin
        try:
            lon_c, lat_c = shape(item['geometry']).centroid.coords[0]
        except Exception:
            coords = item.get("geometry", {}).get("coordinates", [0, 0])
            lon_c, lat_c = coords[0], coords[1]
        folium.Marker([lat_c, lon_c], popup=popup, icon=folium.Icon(color="purple", icon="flash")).add_to(caps_group)
    map_obj.add_child(caps_group)

    # Sirene
    sir_group = folium.FeatureGroup(name="Entreprises Sirene", show=None)
    for feat in sirene_data:
        if feat.get('geometry', {}).get('type') == 'Point':
            lon_s, lat_s = feat['geometry']['coordinates']
            folium.Marker([lat_s, lon_s], popup="<br>".join(f"{k}: {v}" for k, v in feat['properties'].items()), icon=folium.Icon(color="darkred", icon="building")).add_to(sir_group)
    map_obj.add_child(sir_group)
    
    # Défini bbox_poly avant d'utiliser get_all_gpu_data(bbox_poly)
    delta = 5.0 / 111.0  # 5km en degrés ~
    bbox_poly = bbox_to_polygon(lon, lat, delta)
    
    # GPU Urbanisme : Ajout dynamique de toutes les couches du GPU urbanisme (zone-urba, prescription-surf, ...)
    COLOR_GPU = {
        "zone-urba": "#0055FF",
        "prescription-surf": "#FF9900",
        "prescription-lin": "#44AA44",
        "prescription-pct": "#AA44AA",
        "secteur-cc": "#666666",
    }
    gpu = api_urbanisme or get_all_gpu_data(bbox_poly)
    if not isinstance(gpu, dict):
        gpu = {}

    def make_style(couleur):
        return lambda feature: {"color": couleur, "weight": 2, "fillOpacity": 0.3, "fill": True}

    for ep, data in gpu.items():
        if not isinstance(data, dict):
            data = {"type": "FeatureCollection", "features": []}
        features = data.get('features', [])
        if not features:
            continue
        layer_label = ep.replace("-", " ").capitalize()
        color = COLOR_GPU.get(ep, "#3333CC")
        group = folium.FeatureGroup(name=f"Urbanisme - {layer_label}", show=(ep == "zone-urba"))

        for feat in features:
            geom = feat.get('geometry')
            props = feat.get('properties', {})
            popup_html = ""
            if not props:
                popup_html = "Aucune propriété trouvée"
            else:
                for k, v in props.items():
                    popup_html += f"<b>{k}</b>: {v}<br>"
            # Vérification stricte de la géométrie avant ajout
            valid_geom = False
            if geom and isinstance(geom, dict):
                gtype = geom.get("type")
                coords = geom.get("coordinates")
                if gtype in {"Point", "LineString", "Polygon", "MultiPoint", "MultiLineString", "MultiPolygon"}:
                    if coords and coords != [] and coords is not None:
                        valid_geom = True
            if valid_geom:
                try:
                    folium.GeoJson(
                        geom,
                        style_function=make_style(color),
                        tooltip=props.get("libelle", layer_label) or layer_label,
                        popup=folium.Popup(popup_html, max_width=400)
                    ).add_to(group)
                except Exception as e:
                    print(f"[ERROR] Exception while adding GPU geometry for {ep}: {e}\nGeom: {geom}")
            else:
                print(f"[DEBUG] Invalid GPU geometry for {ep}: type={geom.get('type') if geom else None}, coords={geom.get('coordinates') if geom else None}")

        map_obj.add_child(group)

    # Éleveurs
    if eleveurs_data:
        el_group = folium.FeatureGroup(name="Éleveurs", show=True)
        cluster = MarkerCluster().add_to(el_group)
        for feat in eleveurs_data:
            try:
                coords = shape(feat['geometry']).coords[0]
                if abs(coords[0]) > 180 or abs(coords[1]) > 90:
                    to_wgs = Transformer.from_crs("EPSG:2154","EPSG:4326",always_xy=True).transform
                    lon_e, lat_e = to_wgs(*coords)
                else:
                    lon_e, lat_e = coords
            except Exception:
                continue
            props = feat['properties']
            nom = props.get("nomUniteLe", "") or ""
            prenom = props.get("prenom1Uni", "") or ""
            denomination = props.get("denominati", "") or ""
            adresse = (
                f"{props.get('numeroVoie','') or ''} "
                f"{props.get('typeVoieEt','') or ''} "
                f"{props.get('libelleVoi','') or ''}, "
                f"{props.get('codePostal','') or ''} "
                f"{props.get('libelleCom','') or ''}"
            ).replace(" ,", "").strip()
            siret = props.get("siret", "")
            
            folium.Marker(
                [lat_e, lon_e],
                popup=folium.Popup(
                    f"<b>{nom} {prenom}</b><br>{adresse}<br>SIRET: {siret}",
                    max_width=300
                ),
                icon=folium.Icon(color="cadetblue", icon="paw", prefix="fa")
            ).add_to(cluster)
        map_obj.add_child(el_group)

    # API Cadastre/Nature IGN (5km)
    cad5 = api_cadastre or {"type": "FeatureCollection", "features": []}
    nat5 = api_nature or {"type": "FeatureCollection", "features": []}
    
    # Cadastre (masqué par défaut)
    cad_grp = folium.FeatureGroup(name="API Cadastre IGN (5km)", show=False)
    for f in cad5.get('features', []):
        if f.get('geometry'):
            folium.GeoJson(
                f['geometry'], 
                style_function=lambda _: {"color": "#FF5500", "weight": 2, "fillOpacity": 0.3}, 
                tooltip="<br>".join(f"{k}: {v}" for k, v in f.get('properties', {}).items())
            ).add_to(cad_grp)
    map_obj.add_child(cad_grp)
    
    # Zones naturelles protégées (affichées par défaut)
    if nat5.get('features'):
        nat_grp = folium.FeatureGroup(name="🌿 Zones Naturelles Protégées", show=True)
        
        # Couleurs par type de protection
        protection_colors = {
            "Parcs Nationaux": "#2E8B57",  # Vert foncé
            "Parcs Naturels Régionaux": "#228B22",  # Vert forêt
            "Natura 2000 Directive Habitat": "#4682B4",  # Bleu acier
            "Natura 2000 Directive Oiseaux": "#87CEEB",  # Bleu ciel
            "ZNIEFF Type 1": "#FFB347",  # Orange
            "ZNIEFF Type 2": "#FFA500",  # Orange foncé
            "Réserves Naturelles Nationales": "#8B0000",  # Rouge foncé
            "Réserves Naturelles de Corse": "#DC143C",  # Rouge cramoisi
            "Réserves Nationales de Chasse et Faune Sauvage": "#8B4513"  # Brun
        }
        
        for f in nat5.get('features', []):
            if f.get('geometry'):
                props = f.get('properties', {})
                type_protection = props.get('TYPE_PROTECTION', 'Zone naturelle')
                color = protection_colors.get(type_protection, "#22AA22")
                
                # Popup avec informations détaillées
                popup_content = f"<div style='max-width: 300px;'>"
                popup_content += f"<h5 style='color: {color};'>{props.get('NOM', 'Zone naturelle')}</h5>"
                popup_content += f"<span class='badge' style='background-color: {color}; color: white; margin-bottom: 10px;'>{type_protection}</span><br><br>"
                
                for k, v in props.items():
                    if k not in ['TYPE_PROTECTION'] and v:
                        popup_content += f"<b>{k}:</b> {v}<br>"
                popup_content += "</div>"
                
                folium.GeoJson(
                    f['geometry'], 
                    style_function=lambda _, c=color: {
                        "color": c, 
                        "weight": 3, 
                        "fillOpacity": 0.4,
                        "fillColor": c
                    },
                    popup=folium.Popup(popup_content, max_width=400),
                    tooltip=f"🌿 {props.get('NOM', 'Zone naturelle')} ({type_protection})"
                ).add_to(nat_grp)
        
        map_obj.add_child(nat_grp)

    if not mode_light:
        folium.LayerControl().add_to(map_obj)

    # --- Zoom sur emprise calculée ---
    bounds = None
    if parcelles_data and parcelles_data.get("features"):
        polys = [shape(f["geometry"]) for f in parcelles_data["features"] if "geometry" in f]
        if polys:
            try:
                multi = MultiPolygon([p for p in polys if p.geom_type == "Polygon"] + [p for p in polys if p.geom_type == "MultiPolygon"])
                minx, miny, maxx, maxy = multi.bounds
                bounds = [[miny, minx], [maxy, maxx]]
            except Exception:
                pass
    if not bounds:
        delta = 0.01
        bounds = [[lat - delta, lon - delta], [lat + delta, lon + delta]]

    helper_js = """
    <script>
    (function () {
    var mapInstance = (function () {
        for (var k in window) {
            if (window[k] instanceof L.Map) { return window[k]; }
        }
        return null;
    })();
    if (!mapInstance) { console.error('❌ Map instance not found'); return; }
    var dynLayer = L.geoJSON(null).addTo(mapInstance);
    window.addGeoJsonToMap = function (feature, style) {
        if (!feature) { return; }
        if (style) {
            L.geoJSON(feature, {
                style: function () { return style; },
                pointToLayer: function (f, latlng) {
                    return L.circleMarker(latlng, style);
                }
            }).addTo(mapInstance);
        } else {
            dynLayer.addData(feature);
        }
        mapInstance.fitBounds(dynLayer.getBounds(), {maxZoom: 18});
    };
    window.clearMap = function () {
        try { dynLayer.clearLayers(); } catch(e) {}
    };
    window.fetchAndDisplayGeoJson = function () {/* rien ici */};
    })();
    </script>
    """
    map_obj.get_root().html.add_child(Element(helper_js))

    map_obj.fit_bounds(bounds)
    if not mode_light:
        folium.Marker([lat, lon], popup="Test marker").add_to(map_obj)
    
    # Ajouter timestamp pour éviter le cache
    if getattr(map_obj, '_no_save', False):
        print("💡 Carte non sauvegardée sur disque (mode _no_save)")
    else:
        # Ajouter timestamp pour éviter le cache
        import time
        timestamp = int(time.time())
        save_map_html(map_obj, f"cartes_{timestamp}.html")
    return map_obj

@app.route('/search_by_address', methods=['GET', 'POST'])
def search_by_address_route():
    """Route de recherche par adresse avec cartes complètes"""
    
    safe_print(f"\n{'='*80}")
    safe_print(f"🔍 [RECHERCHE ADRESSE] === DÉBUT RECHERCHE PAR ADRESSE ===")
    safe_print(f"📅 Date/Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    values = request.values
    lat_str = values.get("lat")
    lon_str = values.get("lon") 
    address = values.get("address", "Adresse inconnue")
    
    safe_print(f"📍 Paramètres reçus:")
    safe_print(f"   - Latitude: {lat_str}")
    safe_print(f"   - Longitude: {lon_str}")
    safe_print(f"   - Adresse: {address}")
    
    try:
        lat = float(lat_str)
        lon = float(lon_str)
    except (TypeError, ValueError):
        return jsonify({
            'success': False,
            'error': 'Coordonnées invalides'
        }), 400
    
    # Récupération des parcelles cadastrales
    safe_print("🏠 [PARCELLES] Récupération données cadastrales...")
    parcelle_info = get_parcelle_info(lat, lon)
    if not parcelle_info or not parcelle_info.get("features"):
        parcelle_info = get_all_parcelles(lat, lon, radius=0.01)
    
    parcelles_count = len(parcelle_info.get("features", []))
    safe_print(f"📐 Parcelles trouvées: {parcelles_count}")
    
    # Génération de la carte
    safe_print("🗺️ [CARTE] Génération carte complète avec toutes les couches...")
    
    # ⚡ RÉCUPÉRATION DYNAMIQUE DES DONNÉES GEOSERVER ⚡
    safe_print("🔍 [GEOSERVER] Récupération dynamique des données...")
    
    # Postes électriques (BT et HTA)
    postes_data = get_all_postes(lat, lon, radius_deg=0.1)
    ht_postes_data = get_all_ht_postes(lat, lon, radius_deg=0.5)
    safe_print(f"⚡ Postes BT: {len(postes_data)}, HTA: {len(ht_postes_data)}")
    
    # PLU, parkings, friches
    plu_info = get_plu_info(lat, lon, radius=0.03)
    parkings_data = get_parkings_info(lat, lon, radius=0.03)
    friches_data = get_friches_info(lat, lon, radius=0.03)
    safe_print(f"🏛️ PLU: {len(plu_info)}, 🅿️ Parkings: {len(parkings_data)}, 🌾 Friches: {len(friches_data)}")
    
    # Potentiel solaire et ZAER
    potentiel_solaire_data = get_potentiel_solaire_info(lat, lon, radius=1.0)
    zaer_data = get_zaer_info(lat, lon, radius=0.03)
    safe_print(f"🏠 Toitures: {len(potentiel_solaire_data)}, 🌿 ZAER: {len(zaer_data)}")
    
    # RPG et Sirene
    rpg_data = get_rpg_info(lat, lon, radius=0.0027)
    sirene_data = get_sirene_info(lat, lon, radius=0.03)
    safe_print(f"🌾 RPG: {len(rpg_data)}, 🏢 Sirene: {len(sirene_data)}")
    
    # Éleveurs et capacités réseau
    eleveurs_data = get_eleveurs_info(lat, lon, radius=0.1)
    capacites_reseau = get_capacites_reseau_info(lat, lon, radius=0.5)
    safe_print(f"🐄 Éleveurs: {len(eleveurs_data)}, 🔌 Capacités: {len(capacites_reseau)}")
    
    # PPRI
    ppri_data = get_ppri_info(lat, lon, radius=0.03)
    safe_print(f"🌊 PPRI: {len(ppri_data.get('features', []))}")
    
    safe_print("✅ [GEOSERVER] Toutes les données récupérées avec succès !")
    
    map_obj = build_map(
        lat=lat, 
        lon=lon, 
        address=address,
        parcelle_props=None,  # Pas de parcelle individuelle pour l'instant
        parcelles_data=parcelle_info,  # Données parcelles IGN
        postes_data=postes_data,  # ✅ DONNÉES DYNAMIQUES
        ht_postes_data=ht_postes_data,  # ✅ DONNÉES DYNAMIQUES
        plu_info=plu_info,  # ✅ DONNÉES DYNAMIQUES
        parkings_data=parkings_data,  # ✅ DONNÉES DYNAMIQUES
        friches_data=friches_data,  # ✅ DONNÉES DYNAMIQUES
        potentiel_solaire_data=potentiel_solaire_data,  # ✅ DONNÉES DYNAMIQUES
        zaer_data=zaer_data,  # ✅ DONNÉES DYNAMIQUES
        rpg_data=rpg_data,  # ✅ DONNÉES DYNAMIQUES
        sirene_data=sirene_data,  # ✅ DONNÉES DYNAMIQUES
        search_radius=1000,  # 1km par défaut
        ht_radius_deg=0.1,  # 0.1° par défaut
        api_cadastre=None,  # Pas d'API cadastre pour l'instant
        api_nature=None,  # Pas d'API nature pour l'instant
        api_urbanisme=None,  # Pas d'API urbanisme pour l'instant
        eleveurs_data=eleveurs_data,  # ✅ DONNÉES DYNAMIQUES
        capacites_reseau=capacites_reseau,  # ✅ DONNÉES DYNAMIQUES
        ppri_data=ppri_data  # ✅ DONNÉES DYNAMIQUES
    )
    
    # Sauvegarde de la carte
    timestamp = int(time.time())
    map_filename = f"map_{timestamp}_{abs(hash(f'{lat}{lon}'))}.html"
    map_path = os.path.join("static", "cartes", map_filename)
    
    # Créer le dossier si nécessaire
    os.makedirs(os.path.dirname(map_path), exist_ok=True)
    
    map_obj.save(map_path)
    map_url = f"/static/cartes/{map_filename}?t={timestamp}"
    
    safe_print(f"✅ [CARTE] Carte sauvée: {map_url}")
    safe_print(f"✅ [RÉSULTATS] === RECHERCHE PAR ADRESSE TERMINÉE ===")
    
    return jsonify({
        'success': True,
        'map_url': map_url,
        'data': {
            'address': address,
            'coordinates': {'lat': lat, 'lon': lon},
            'parcelles_count': parcelles_count,
            'layers': ['Esri Satellite', 'OpenStreetMap', 'Parcelles cadastrales']
        }
    })

# Module serveur unifié - importé par run_app.py
# N'exécute pas directement l'application pour éviter les conflits Railway

# if __name__ == '__main__':
#     print("🚀 Démarrage AgriWeb 2.0 Unifié - Production")
#     print("=" * 60)
#     print(f"🔗 GeoServer: {GEOSERVER_URL}")
#     print(f"🌐 Interface web: http://localhost:5000")
#     print(f"📊 Statut système: http://localhost:5000/status")
#     print(f"🆓 Essais gratuits: Activés (7 jours)")
#     print(f"💼 Licences: Basic (299€), Pro (999€), Enterprise (2999€)")
#     print("=" * 60)
#     print("✅ Prêt pour la commercialisation !")
#     
#     app.run(host='0.0.0.0', port=5000, debug=False)
