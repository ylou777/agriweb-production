# --- GeoRisques API: fetch risks for a point ---
import requests
import os
from datetime import datetime

# Fonction utilitaire pour logging sécurisé (évite les erreurs WinError 233)
def safe_print(*args, **kwargs):
    """Print sécurisé qui ignore les erreurs de canal fermé"""
    try:
        print(*args, **kwargs)
    except OSError:
        # Ignorer les erreurs de canal fermé (WinError 233)
        pass

def log_search_start(commune, params):
    """Log détaillé du début d'une recherche"""
    # print(f"\n{'='*80}")  # Optimisé pour production multi-user
    # print(f"🔍 [RECHERCHE COMMUNE] === DÉBUT RECHERCHE POUR '{commune.upper()}' ===")  # Optimisé pour production multi-user
    # print(f"📅 Date/Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")  # Optimisé pour production multi-user
    # print(f"📍 Commune: {commune}")  # Optimisé pour production multi-user
    # print(f"🎯 Filtres actifs:")  # Optimisé pour production multi-user
    
    if params['filter_rpg']:
        # print(f"   🌾 RPG: OUI (surface {params['rpg_min_area']}-{params['rpg_max_area']} ha)")  # Optimisé pour production multi-user
        pass
    else:
        # print(f"   🌾 RPG: NON")  # Optimisé pour production multi-user
        pass
        
    if params['filter_parkings']:
        # print(f"   🅿️ Parkings: OUI (surface min {params['parking_min_area']} m²)")  # Optimisé pour production multi-user
        pass
    else:
        # print(f"   🅿️ Parkings: NON")  # Optimisé pour production multi-user
        pass
        
    if params['filter_friches']:
        # print(f"   🏚️ Friches: OUI (surface min {params['friches_min_area']} m²)")  # Optimisé pour production multi-user
        pass
    else:
        # print(f"   🏚️ Friches: NON")  # Optimisé pour production multi-user
        pass
        
    if params['filter_zones']:
        type_zone = params['zones_type_filter'] or 'toutes'
        # print(f"   🏗️ Zones urbanisme: OUI (type: {type_zone}, surface min {params['zones_min_area']} m²)")  # Optimisé pour production multi-user
        pass
    else:
        # print(f"   🏗️ Zones urbanisme: NON")  # Optimisé pour production multi-user
        pass
        
    if params['filter_toitures']:
        # print(f"   🏠 Toitures: OUI (surface min {params['toitures_min_surface']} m²)")  # Optimisé pour production multi-user
        pass
    else:
        # print(f"   🏠 Toitures: NON")  # Optimisé pour production multi-user
        pass
        
    if params['filter_by_distance']:
        logic = "ET" if params['distance_logic'] == 'AND' else "OU"
        # print(f"   📏 Filtrage distance: OUI (BT<{params['max_distance_bt']}m {logic} HTA<{params['max_distance_hta']}m)")  # Optimisé pour performance
        pass
    else:
        # print(f"   📏 Filtrage distance: NON")  # Optimisé pour performance
        pass
        
    # print(f"⚡ Paramètres techniques:")  # Optimisé pour performance
    # print(f"   - Distance max HTA: {params['ht_max_km']} km")  # Optimisé pour performance
    # print(f"   - Distance max BT: {params['bt_max_km']} km")  # Optimisé pour performance
    # print(f"   - Rayon SIRENE: {params['sir_km']} km")  # Optimisé pour performance
    # print(f"{'='*80}")  # Optimisé pour performance

def log_data_collection(step, details):
    """Log détaillé de la collecte de données - optimisé pour performance"""
    # Réduire la verbosité des logs pour éviter les loops infinies
    if "✅" in details and ("récupérées" in details or "trouvées" in details):
        # Log seulement les résultats finaux, pas les étapes intermédiaires
        # print(f"📊 [COLLECTE] {step}: {details}")  # Optimisé pour performance
        pass
    # Ignorer les logs "Récupération" pour réduire la verbosité

def ensure_json_safe(value, _depth=0):
    """Convertit récursivement une structure Python en types JSON-sérialisables.
    - dict/list/tuple/set: parcours récursif
    - datetime/date: isoformat
    - bytes/bytearray: utf-8 (remplacement erreurs)
    - objets avec attribut __geo_interface__: utilise ce dict
    - tout le reste non-sérialisable: str(value)
    Limite la profondeur pour éviter références circulaires.
    """
    from datetime import date, datetime
    from decimal import Decimal

    if _depth > 10:
        # éviter récursion profonde/circulaire
        return str(value)

    # Primitifs JSON-safe
    if value is None or isinstance(value, (bool, int, float, str)):
        return value

    # Décimal -> float
    if isinstance(value, Decimal):
        try:
            return float(value)
        except Exception:
            return str(value)

    # Dates -> ISO
    if isinstance(value, (date, datetime)):
        try:
            return value.isoformat()
        except Exception:
            return str(value)

    # bytes -> utf-8
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode('utf-8', errors='replace')
        except Exception:
            return str(value)

    # Geo interface
    if hasattr(value, "__geo_interface__"):
        try:
            return ensure_json_safe(getattr(value, "__geo_interface__"), _depth+1)
        except Exception:
            return str(value)

    # dict
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            try:
                key = str(k)
            except Exception:
                key = repr(k)
            out[key] = ensure_json_safe(v, _depth+1)
        return out

    # list/tuple/set
    if isinstance(value, (list, tuple, set)):
        try:
            return [ensure_json_safe(v, _depth+1) for v in list(value)]
        except Exception:
            return [str(v) for v in list(value)]

    # numpy scalaires (sans importer numpy)
    mod = type(value).__module__
    if mod and mod.startswith('numpy'):
        try:
            return value.item()
        except Exception:
            return float(value) if hasattr(value, '__float__') else str(value)

    # Autres objets: fallback -> str
    return str(value)

def log_search_results(commune, results):
    """Log détaillé des résultats de recherche (robuste aux formats)."""
    def count_features(obj):
        try:
            if obj is None:
                return 0
            # GeoJSON FeatureCollection
            if isinstance(obj, dict):
                feats = obj.get('features')
                if isinstance(feats, list):
                    return len(feats)
                # Fallback: count items in dict if it's another structure (e.g., list-like fields)
                return len(obj)
            if isinstance(obj, list):
                return len(obj)
            return 0
        except Exception:
            return 0

    # print(f"\n{'='*80}")  # Optimisé pour production multi-user
    # print(f"✅ [RÉSULTATS] === RECHERCHE TERMINÉE POUR '{commune.upper()}' ===")  # Optimisé pour production multi-user
    # print(f"📊 Données collectées:")  # Optimisé pour production multi-user

    # Compter les éléments trouvés, qu'ils soient en liste ou en FeatureCollection
    rpg_count = count_features(results.get('rpg')) or count_features(results.get('rpg_parcelles'))
    parkings_count = count_features(results.get('parkings'))
    friches_count = count_features(results.get('friches'))
    toitures_count = count_features(results.get('toitures'))
    zones_count = count_features(results.get('plu'))
    parcelles_zones_count = count_features(results.get('parcelles_in_zones'))
    eleveurs_count = count_features(results.get('eleveurs'))
    postes_bt_count = count_features(results.get('postes_bt'))
    postes_hta_count = count_features(results.get('postes_hta'))
    sirene_count = count_features(results.get('sirene'))

    # print(f"   🌾 Parcelles RPG: {rpg_count}")  # Optimisé pour production multi-user
    # print(f"   🅿️ Parkings: {parkings_count}")  # Optimisé pour production multi-user
    # print(f"   🏚️ Friches: {friches_count}")  # Optimisé pour production multi-user
    # print(f"   🏠 Toitures: {toitures_count}")  # Optimisé pour production multi-user
    # print(f"   🏗️ Zones d'urbanisme: {zones_count}")  # Optimisé pour production multi-user
    # print(f"   📐 Parcelles dans zones: {parcelles_zones_count}")  # Optimisé pour production multi-user
    # print(f"   🐄 Éleveurs: {eleveurs_count}")  # Optimisé pour production multi-user
    # print(f"   ⚡ Postes BT: {postes_bt_count}")  # Optimisé pour production multi-user
    # print(f"   🔌 Postes HTA: {postes_hta_count}")  # Optimisé pour production multi-user
    # print(f"   🏢 Entreprises SIRENE: {sirene_count}")  # Optimisé pour production multi-user

    total_elements = (rpg_count + parkings_count + friches_count +
                      toitures_count + zones_count + eleveurs_count)
    # print(f"📈 Total éléments géographiques: {total_elements}")  # Optimisé pour production multi-user
    try:
        active_filters = [f for f in (results.get('filters_applied') or {}).values() if isinstance(f, dict) and f.get('active', False)]
        # print(f"🎯 Filtres appliqués: {len(active_filters)}")  # Optimisé pour production multi-user
        pass
    except Exception:
        # print(f"🎯 Filtres appliqués: N/A")  # Optimisé pour production multi-user
        pass
    # print(f"⏱️ Recherche terminée: {datetime.now().strftime('%H:%M:%S')}")  # Optimisé pour production multi-user
    # print(f"{'='*80}\n")  # Optimisé pour production multi-user
def fetch_georisques_risks(lat, lon):
    """
    Appelle l'API GeoRisques pour obtenir les risques naturels et technologiques pour un point.
    Utilise tous les endpoints disponibles dans l'API v1.
    Voir doc: https://www.georisques.gouv.fr/doc-api
    
    Modifications 2025:
    - Radon nécessite maintenant code_insee au lieu de latlon
    - Installations: endpoint est "installations_classees" (pas "installations")
    - Argiles: utilise gaspar/risques avec code_insee
    """
    risques = {}
    latlon = f"{lon},{lat}"  # Format longitude,latitude pour l'API
    
    # Obtenir le code INSEE de la commune via géocodage inversé
    code_insee = None
    try:
        geo_info = get_address_from_coordinates(lat, lon)
        if geo_info and geo_info.get('citycode'):
            code_insee = geo_info['citycode']
            # print(f"[GeoRisques] Code INSEE récupéré: {code_insee}")  # Optimisé pour performance
    except Exception as e:
        # print(f"[GeoRisques] Impossible de récupérer le code INSEE: {e}")  # Optimisé pour performance
        pass
    
    # 1. Zonage sismique
    try:
        url = "https://www.georisques.gouv.fr/api/v1/zonage_sismique"
        params = {"latlon": latlon}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            risques["sismique"] = data.get("data", [])
        else:
            # print(f"[GeoRisques Sismique] Erreur: {resp.status_code}")  # Optimisé pour performance
            risques["sismique"] = []
    except Exception as e:
        # print(f"[GeoRisques Sismique] Exception: {e}")  # Optimisé pour performance
        risques["sismique"] = []

    # 8. CATNAT - Catastrophes naturelles
    try:
        url = "https://www.georisques.gouv.fr/api/v1/gaspar/catnat"
        params = {"latlon": latlon, "rayon": 1000}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            risques["catnat"] = data.get("data", [])
        else:
            # print(f"[GeoRisques CATNAT] Erreur: {resp.status_code}")  # Optimisé pour performance
            risques["catnat"] = []
    except Exception as e:
        # print(f"[GeoRisques CATNAT] Exception: {e}")  # Optimisé pour performance
        risques["catnat"] = []

    # 9. Cavités souterraines
    try:
        url = "https://www.georisques.gouv.fr/api/v1/cavites"
        params = {"latlon": latlon, "rayon": 1000}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            risques["cavites"] = data.get("data", [])
        else:
            # print(f"[GeoRisques Cavités] Erreur: {resp.status_code}")  # Optimisé pour performance
            risques["cavites"] = []
    except Exception as e:
        # print(f"[GeoRisques Cavités] Exception: {e}")  # Optimisé pour performance
        risques["cavites"] = []

    # 10. MVT - Mouvements de terrains
    try:
        url = "https://www.georisques.gouv.fr/api/v1/mvt"
        params = {"latlon": latlon, "rayon": 1000}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            risques["mvt"] = data.get("data", [])
        else:
            # print(f"[GeoRisques MVT] Erreur: {resp.status_code}")  # Optimisé pour performance
            risques["mvt"] = []
    except Exception as e:
        # print(f"[GeoRisques MVT] Exception: {e}")  # Optimisé pour performance
        risques["mvt"] = []

    # 11. Retrait gonflement des argiles - Via gaspar/risques avec code_insee
    if code_insee:
        try:
            url = "https://www.georisques.gouv.fr/api/v1/gaspar/risques"
            params = {"code_insee": code_insee}
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("data", [])
                # Extraire les risques liés aux argiles/RGA
                argiles_risks = []
                for item in results:
                    for risk in item.get('risques_detail', []):
                        if 'argile' in risk.get('libelle_risque_long', '').lower() or \
                           'tassement' in risk.get('libelle_risque_long', '').lower():
                            argiles_risks.append(risk)
                risques["argiles"] = argiles_risks
            else:
                # print(f"[GeoRisques Argiles] Erreur: {resp.status_code}")  # Optimisé pour performance
                risques["argiles"] = []
        except Exception as e:
            # print(f"[GeoRisques Argiles] Exception: {e}")  # Optimisé pour performance
            risques["argiles"] = []
    else:
        risques["argiles"] = []

    # 12. Radon - Nécessite code_insee
    if code_insee:
        try:
            url = "https://www.georisques.gouv.fr/api/v1/radon"
            params = {"code_insee": code_insee}
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                risques["radon"] = data.get("data", [])
            else:
                # print(f"[GeoRisques Radon] Erreur: {resp.status_code}")  # Optimisé pour performance
                risques["radon"] = []
        except Exception as e:
            # print(f"[GeoRisques Radon] Exception: {e}")  # Optimisé pour performance
            risques["radon"] = []
    else:
        # print("[GeoRisques Radon] Code INSEE manquant, impossible de récupérer les données radon")  # Optimisé pour performance
        risques["radon"] = []

    # 13. Installations classées - Endpoint corrigé
    try:
        url = "https://www.georisques.gouv.fr/api/v1/installations_classees"
        params = {"latlon": latlon, "rayon": 2000}  # Rayon plus large pour les installations
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            risques["installations"] = data.get("data", [])
        else:
            # print(f"[GeoRisques Installations] Erreur: {resp.status_code}")  # Optimisé pour performance
            risques["installations"] = []
    except Exception as e:
        # print(f"[GeoRisques Installations] Exception: {e}")  # Optimisé pour performance
        risques["installations"] = []

    # 14. Installations nucléaires
    try:
        url = "https://www.georisques.gouv.fr/api/v1/installations_nucleaires"
        params = {"latlon": latlon, "rayon": 5000}  # Rayon plus large pour le nucléaire
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            risques["nucleaire"] = data.get("data", [])
        else:
            # print(f"[GeoRisques Nucléaire] Erreur: {resp.status_code}")  # Optimisé pour performance
            risques["nucleaire"] = []
    except Exception as e:
        # print(f"[GeoRisques Nucléaire] Exception: {e}")  # Optimisé pour performance
        risques["nucleaire"] = []
    
    # Comptons le nombre total de risques
    total_risks = 0
    for category, risks in risques.items():
        if risks and isinstance(risks, list):
            count = len(risks)
            total_risks += count
    
    # print(f"🔍 [GEORISQUES] === TOTAL: {total_risks} risques trouvés ===")  # Optimisé pour performance
    return risques
import logging
logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s')
# --- Utility: always return a list of features from any WFS or API result ---
def ensure_feature_list(data):
    """
    Prend un résultat d'API ou WFS (FeatureCollection, liste ou None) et retourne toujours une liste de features.
    """
    if data is None:
        return []
    if isinstance(data, dict) and data.get("type") == "FeatureCollection":
        return data.get("features", [])
    if isinstance(data, list):
        return data
    return []
# ...existing code...
# ...existing code...
# Imports principaux
# ──────────────────────────────────────────────────────────────
from flask import (
    Flask, request, render_template, render_template_string, jsonify, send_file, send_from_directory,
    make_response, Response, stream_with_context, redirect, session, flash
)
import folium
from folium.plugins import Draw, MeasureControl, MarkerCluster, Search

# Ajout import pour la route HTA lignes
try:
    from enedis_integration import get_lignes_hta
    ENEDIS_MODULE_OK = True
except Exception:
    ENEDIS_MODULE_OK = False
from shapely.geometry import shape, mapping, Point
from shapely.ops import transform as shp_transform
from shapely.errors import GEOSException
from pyproj import Transformer
from urllib.parse import quote, quote_plus
import unicodedata, re
from threading import Timer
from datetime import datetime, timedelta
import webbrowser
import os
import json
import io
import csv
import time
import sqlite3
import hashlib
import secrets
from functools import wraps
import zipfile
from io import BytesIO
import pprint
from functools import lru_cache
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from geopy.geocoders import Nominatim
from branca.element import Element
from docx import Document

# Import du module de rapport complet
try:
    from rapport_commune_complet import generate_comprehensive_commune_report
    RAPPORT_COMPLET_AVAILABLE = True
    print("📊 [RAPPORT] Module de rapport complet importé avec succès")
except ImportError as e:
    print(f"⚠️ [RAPPORT] Module de rapport complet non disponible: {e}")
    RAPPORT_COMPLET_AVAILABLE = False

# --- Utility: Clean filename for safe file naming ---
def clean_filename(text, max_length=50):
    """
    Nettoie un texte pour en faire un nom de fichier valide.
    Supprime les caractères spéciaux, remplace les espaces par des underscores.
    """
    import re
    # Supprimer les accents
    import unicodedata
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    # Remplacer les espaces et caractères spéciaux par des underscores
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s]+', '_', text)
    text = text.strip('_')
    # Limiter la longueur
    if len(text) > max_length:
        text = text[:max_length]
    return text

def sanitize_popup_html(html_content):
    """
    Nettoie et échappe le contenu HTML des popups pour éviter les erreurs JavaScript.
    Supprime les séquences d'échappement octales qui causent des erreurs dans les template strings.
    """
    if not html_content:
        return ""
    
    import html
    # Pas besoin d'échapper car folium.IFrame le fait déjà
    # Mais on doit remplacer les backslashes qui causent des problèmes
    cleaned = str(html_content)  # S'assurer que c'est une string
    cleaned = cleaned.replace('\\', '\\\\')  # Double les backslashes
    cleaned = cleaned.replace('\n', ' ')  # Supprime les retours à la ligne
    cleaned = cleaned.replace('\r', '')   # Supprime les retours chariot
    cleaned = cleaned.replace('\t', ' ')  # Remplace les tabulations
    # Supprime les séquences d'échappement octales (\0-\7)
    cleaned = re.sub(r'\\[0-7]{1,3}', '', cleaned)
    return cleaned

def safe_folium_popup(content, max_width=300):
    """
    Crée un popup Folium avec nettoyage automatique du contenu.
    Utilise IFrame pour éviter les problèmes d'échappement avec hauteur adaptative.
    """
    if not content:
        return None
    
    # Nettoyer le contenu
    clean_content = sanitize_popup_html(content)
    
    # Calculer une hauteur adaptative basée sur le contenu
    # Estimation: ~20px par <br>, minimum 150px, maximum 400px
    br_count = clean_content.count('<br>') + clean_content.count('<BR>')
    estimated_height = max(150, min(400, 80 + (br_count * 25)))
    
    # Utiliser IFrame pour isolation complète avec hauteur adaptative
    try:
        iframe = folium.IFrame(html=clean_content, width=max_width, height=estimated_height)
        return folium.Popup(iframe, max_width=max_width)
    except Exception as e:
        # Fallback sans IFrame
        print(f"⚠️ [POPUP] Erreur IFrame: {e}, utilisation Popup direct")
        return folium.Popup(clean_content, max_width=max_width)

def generate_secure_filename(prefix, description="", extension=".html"):
    """
    🔒 Génère un nom de fichier sécurisé avec token UUID pour éviter les collisions
    et empêcher la découverte par énumération.
    
    Format: {prefix}_{description}_{uuid8}_{timestamp}.{extension}
    Exemple: recherche_15-rue-paris_a3f8d2c1_20251010_150623.html
    
    Args:
        prefix: Type de fichier (recherche, rapport, commune, etc.)
        description: Description courte (adresse, commune, etc.) - optionnel
        extension: Extension du fichier (défaut: .html)
    
    Returns:
        str: Nom de fichier sécurisé et unique
    """
    import uuid
    from datetime import datetime
    
    # Générer un token UUID court (8 premiers caractères)
    token = str(uuid.uuid4())[:8]
    
    # Timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Nettoyer la description
    if description:
        clean_desc = clean_filename(description, max_length=30)
        filename = f"{prefix}_{clean_desc}_{token}_{timestamp}{extension}"
    else:
        filename = f"{prefix}_{token}_{timestamp}{extension}"
    
    return filename

# --- Utility: Save Folium map to static/cartes/ and return relative path ---
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

# ─── GUI licence (optionnel, protégé) ─────────────────────────
try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    tk = None  # Environnement headless (pas d’interface X11)

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = os.getenv('SECRET_KEY', 'agriweb-secret-key-2025-commercial')

# Marqueur de version diagnostic pour vérifier que ce fichier (avec la route /api/hta-lignes) est bien chargé
AGRIWEB_HTA_VERSION = "hta-lignes-v1.0-2025-09-18"
print(f"🔧 [HTA] Chargement serveur avec version: {AGRIWEB_HTA_VERSION}")

# Cookies de session sécurisés (Railway/Prod)
COOKIE_SECURE = os.getenv('COOKIE_SECURE', 'true').lower() in ('1','true','yes','on')
COOKIE_SAMESITE = os.getenv('COOKIE_SAMESITE', 'Lax')  # 'Lax' or 'None' for cross-site
app.config['SESSION_COOKIE_SECURE'] = COOKIE_SECURE
app.config['SESSION_COOKIE_SAMESITE'] = COOKIE_SAMESITE
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Intégration du système d'authentification (Blueprint)
try:
    from auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    print("🔐 [AUTH] Blueprint d'authentification enregistré (/auth/login, /auth/register, /auth/verify-email)")
except Exception as e:
    print(f"⚠️ [AUTH] Impossible d'enregistrer le blueprint d'auth: {e}")

# Redirections pour compatibilité avec les anciennes URLs
@app.route("/register", methods=["GET", "POST"])
def redirect_register():
    """Redirection vers la nouvelle URL d'inscription"""
    return redirect("/auth/register", code=301)

@app.route("/login", methods=["GET", "POST"])  
def redirect_login():
    """Redirection vers la nouvelle URL de connexion"""
    return redirect("/auth/login", code=301)
# Styles statiques pour éviter les problèmes avec les fonctions lambda en production
STATIC_STYLES = {
    'parcelles': {'color': '#FF6600', 'fillColor': '#FFD700', 'fillOpacity': 0.3, 'weight': 2},
    'postes_bt': {'color': '#FFD700', 'fillColor': '#FFD700', 'fillOpacity': 0.6, 'weight': 2},
    'postes_hta': {'color': '#D12322', 'fillColor': '#D12322', 'fillOpacity': 0.6, 'weight': 2},
    'eleveurs': {'color': '#34ad41', 'fillColor': '#34ad41', 'fillOpacity': 0.5, 'weight': 2},
    'parkings': {'color': '#2ecc71', 'fillColor': '#2ecc71', 'fillOpacity': 0.5, 'weight': 2},
    'solaire': {'color': '#ffd700', 'fillColor': '#ffd700', 'fillOpacity': 0.5, 'weight': 2},
    'rpg': {'color': '#228B22', 'fillColor': '#90EE90', 'fillOpacity': 0.3, 'weight': 1},
    'api_cadastre': {'color': '#FF6600', 'fillColor': '#FFE4B5', 'fillOpacity': 0.3, 'weight': 1},
    'api_nature': {'color': '#22AA22', 'fillColor': '#98FB98', 'fillOpacity': 0.3, 'weight': 1},
    'api_urbanisme': {'color': '#0000FF', 'fillColor': '#ADD8E6', 'fillOpacity': 0.3, 'weight': 1},
    'default': {'color': '#3388ff', 'fillColor': '#8cc0ff', 'fillOpacity': 0.3, 'weight': 2}
}

def get_static_style(layer_type='default'):
    """Retourne un style statique pour le type de couche donné"""
    return STATIC_STYLES.get(layer_type, STATIC_STYLES['default'])


# Configuration CORS pour Railway
@app.after_request
def after_request(response):
    """Configure les headers CORS pour Railway"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# ──────────────────────────────────────────────────────────────
# API: Lignes HTA (aériennes / souterraines) Enedis Open Data
# ──────────────────────────────────────────────────────────────
@app.route('/api/hta-lignes', methods=['GET'])
def api_lignes_hta():
    if not ENEDIS_MODULE_OK:
        return jsonify({"error": "Module Enedis indisponible"}), 503

    department = request.args.get('department')
    bbox_raw = request.args.get('bbox')  # format: minx,miny,maxx,maxy (EPSG:4326)
    include_aerienne = request.args.get('include_aerienne', 'true').lower() in ('1','true','yes','on')
    include_souterraine = request.args.get('include_souterraine', 'true').lower() in ('1','true','yes','on')
    limit = request.args.get('limit', type=int, default=1000)

    if not department and not bbox_raw:
        return jsonify({"error": "Paramètre requis: department ou bbox"}), 400

    bbox = None
    if bbox_raw:
        parts = bbox_raw.split(',')
        if len(parts) != 4:
            return jsonify({"error": "bbox mal formée. Format attendu: minx,miny,maxx,maxy"}), 400
        try:
            bbox = [float(p.strip()) for p in parts]
        except ValueError:
            return jsonify({"error": "bbox contient des valeurs non numériques"}), 400

    try:
        result = get_lignes_hta(
            department=department,
            bbox=bbox,
            include_aerienne=include_aerienne,
            include_souterraine=include_souterraine,
            limit=limit
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint debug: liste toutes les routes chargées
@app.route('/_debug/routes')
def debug_list_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        methods = sorted(m for m in rule.methods if m not in ('HEAD','OPTIONS'))
        routes.append({"rule": str(rule), "endpoint": rule.endpoint, "methods": methods})
    return jsonify({"count": len(routes), "routes": routes})

# Endpoint de diagnostic HTA
@app.route('/api/hta-diagnostic', methods=['GET'])
def api_hta_diagnostic():
    """Endpoint de diagnostic pour tester l'API HTA"""
    department = request.args.get('department', '83')  # Var par défaut
    
    diagnostic = {
        "timestamp": datetime.now().isoformat(),
        "department_requested": department,
        "enedis_module_status": ENEDIS_MODULE_OK,
        "api_version": AGRIWEB_HTA_VERSION
    }
    
    if not ENEDIS_MODULE_OK:
        diagnostic["error"] = "Module Enedis non disponible"
        diagnostic["suggestion"] = "Vérifier l'installation du module enedis_integration"
        return jsonify(diagnostic), 503
    
    try:
        # Test avec un département spécifique et une limite faible
        test_result = get_lignes_hta(
            department=department,
            bbox=None,
            include_aerienne=True,
            include_souterraine=True,
            limit=10  # Limite faible pour test
        )
        
        diagnostic["test_result"] = {
            "success": True,
            "aerienne_count": len(test_result.get("aerienne", {}).get("features", [])) if test_result.get("aerienne") else 0,
            "souterraine_count": len(test_result.get("souterraine", {}).get("features", [])) if test_result.get("souterraine") else 0,
            "total_features": len(test_result.get("aerienne", {}).get("features", [])) + len(test_result.get("souterraine", {}).get("features", [])),
            "summary": test_result.get("summary", "Pas de résumé"),
            "raw_keys": list(test_result.keys()) if test_result else []
        }
        
        # Ajouter un échantillon de données si disponible
        if test_result.get("aerienne", {}).get("features"):
            sample_aerienne = test_result["aerienne"]["features"][0]
            diagnostic["sample_aerienne"] = {
                "properties": sample_aerienne.get("properties", {}),
                "geometry_type": sample_aerienne.get("geometry", {}).get("type", "Unknown")
            }
            
        if test_result.get("souterraine", {}).get("features"):
            sample_souterraine = test_result["souterraine"]["features"][0]
            diagnostic["sample_souterraine"] = {
                "properties": sample_souterraine.get("properties", {}),
                "geometry_type": sample_souterraine.get("geometry", {}).get("type", "Unknown")
            }
        
    except Exception as e:
        diagnostic["test_result"] = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
        
    return jsonify(diagnostic)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                    SYSTÈME D'AUTHENTIFICATION COMMERCIAL                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# Configuration de la base de données
DATABASE_PATH = 'agriweb_users.db'

def init_database():
    """Initialise la base de données des utilisateurs"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Table des utilisateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            company TEXT,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            trial_start_date TIMESTAMP,
            trial_end_date TIMESTAMP,
            subscription_status TEXT DEFAULT 'trial',
            subscription_type TEXT,
            subscription_plan TEXT,
            subscription_end_date TIMESTAMP,
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            last_login TIMESTAMP,
            login_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Ajouter les colonnes Stripe si elles n'existent pas
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN subscription_plan TEXT')
        print("✅ Colonne subscription_plan ajoutée")
    except sqlite3.OperationalError:
        pass  # Colonne existe déjà
        
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN stripe_customer_id TEXT')
        print("✅ Colonne stripe_customer_id ajoutée")
    except sqlite3.OperationalError:
        pass  # Colonne existe déjà
        
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN stripe_subscription_id TEXT')
        print("✅ Colonne stripe_subscription_id ajoutée")
    except sqlite3.OperationalError:
        pass  # Colonne existe déjà
    
    # Table des sessions actives
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Table des logs d'utilisation
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            endpoint TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Ajouter la colonne is_admin si elle n'existe pas
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0')
        print("✅ Colonne is_admin ajoutée")
    except sqlite3.OperationalError:
        # La colonne existe déjà
        pass
    
    conn.commit()
    conn.close()

def hash_password(password, salt=None):
    """Hash un mot de passe avec du sel"""
    if salt is None:
        salt = secrets.token_hex(32)
    
    # Gérer le salt selon son type (string ou bytes)
    if isinstance(salt, str):
        salt_bytes = salt.encode('utf-8')
    else:
        salt_bytes = salt  # Déjà en bytes
    
    # Utilise PBKDF2 pour le hashing sécurisé
    password_hash = hashlib.pbkdf2_hmac('sha256', 
                                       password.encode('utf-8'), 
                                       salt_bytes, 
                                       100000)  # 100,000 itérations
    return password_hash.hex(), salt

def verify_password(password, stored_hash, salt):
    """Vérifie un mot de passe"""
    password_hash, _ = hash_password(password, salt)
    return password_hash == stored_hash

def create_user(email, name, company, password):
    """Crée un nouvel utilisateur avec période d'essai"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Vérifier si l'email existe déjà
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            return False, "Cet email est déjà enregistré"
        
        # Hash du mot de passe
        password_hash, salt = hash_password(password)
        
        # Calcul des dates d'essai
        trial_start = datetime.now()
        trial_end = trial_start + timedelta(days=7)
        
        # Insertion du nouvel utilisateur
        cursor.execute('''
            INSERT INTO users (email, name, company, password_hash, salt, 
                             trial_start_date, trial_end_date, subscription_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (email, name, company, password_hash, salt, trial_start, trial_end, 'trial'))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return True, f"Compte créé avec succès ! Essai gratuit jusqu'au {trial_end.strftime('%d/%m/%Y')}"
        
    except Exception as e:
        print(f"Erreur création utilisateur: {e}")
        return False, "Erreur lors de la création du compte"

def create_demo_accounts():
    """Crée les comptes de démonstration par défaut"""
    demo_accounts = [
        {
            'email': 'admin@test.com',
            'name': 'Administrateur',
            'company': 'AgriWeb Demo',
            'password': 'admin123',
            'subscription_status': 'active'
        },
        {
            'email': 'demo@test.com', 
            'name': 'Utilisateur Demo',
            'company': 'Demo Company',
            'password': 'demo123',
            'subscription_status': 'trial'
        }
    ]
    
    for account in demo_accounts:
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Vérifier si l'utilisateur existe déjà
            cursor.execute('SELECT id FROM users WHERE email = ?', (account['email'],))
            if cursor.fetchone():
                continue  # L'utilisateur existe déjà
            
            # Créer l'utilisateur de démo
            password_hash, salt = hash_password(account['password'])
            trial_end = datetime.now() + timedelta(days=365) if account['subscription_status'] == 'active' else datetime.now() + timedelta(days=7)
            
            cursor.execute('''
                INSERT INTO users (email, name, company, password_hash, salt, 
                                 subscription_status, trial_end_date, is_active, is_admin, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
            ''', (
                account['email'], account['name'], account['company'], 
                password_hash, salt, account['subscription_status'], trial_end.isoformat(),
                1 if account['email'] == 'admin@test.com' else 0  # Admin pour admin@test.com
            ))
            
            conn.commit()
            conn.close()
            print(f"✅ Compte démo créé: {account['email']}")
            
        except Exception as e:
            print(f"Erreur création compte démo {account['email']}: {e}")

def ensure_admin_rights():
    """S'assurer que admin@test.com a les droits administrateur"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Forcer les droits admin pour admin@test.com
        cursor.execute('UPDATE users SET is_admin = 1 WHERE email = ?', ('admin@test.com',))
        conn.commit()
        
        # Vérifier
        cursor.execute('SELECT is_admin FROM users WHERE email = ?', ('admin@test.com',))
        result = cursor.fetchone()
        if result and result[0] == 1:
            print("✅ Droits administrateur confirmés pour admin@test.com")
        else:
            print("⚠️ Problème avec les droits administrateur")
            
        conn.close()
    except Exception as e:
        print(f"Erreur mise à jour droits admin: {e}")

def authenticate_user(email, password):
    """Authentifie un utilisateur"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, password_hash, salt, subscription_status, trial_end_date, name, is_admin
            FROM users WHERE email = ? AND is_active = 1
        ''', (email,))
        
        user = cursor.fetchone()
        if not user:
            return False, None, "Email ou mot de passe incorrect"
        
        user_id, stored_hash, salt, subscription_status, trial_end, name, is_admin = user
        
        # Vérifier le mot de passe
        if not verify_password(password, stored_hash, salt):
            return False, None, "Email ou mot de passe incorrect"
        
        # Vérifier l'état de l'abonnement (sauf pour les comptes admin)
        now = datetime.now()
        if subscription_status == 'trial' and email != 'admin@test.com':
            trial_end_date = datetime.fromisoformat(trial_end)
            if now > trial_end_date:
                return False, None, "Période d'essai expirée. Veuillez souscrire à un abonnement."
        
        # Mettre à jour les stats de connexion
        cursor.execute('''
            UPDATE users 
            SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1
            WHERE id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        return True, {
            'id': user_id,
            'email': email,
            'name': name,
            'subscription_status': subscription_status,
            'trial_end': trial_end,
            'is_admin': bool(is_admin)
        }, "Connexion réussie"
        
    except Exception as e:
        print(f"Erreur authentification: {e}")
        return False, None, "Erreur lors de la connexion"

def create_session(user_id, ip_address=None, user_agent=None):
    """Crée une session utilisateur avec limite de 3 sessions max"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Nettoyer les sessions expirées
        cursor.execute('''
            DELETE FROM user_sessions 
            WHERE expires_at < datetime('now')
        ''')
        
        # Compter les sessions actives pour cet utilisateur
        cursor.execute('''
            SELECT COUNT(*) FROM user_sessions 
            WHERE user_id = ? AND expires_at > datetime('now')
        ''', (user_id,))
        
        active_sessions = cursor.fetchone()[0]
        
        # Si 3 sessions ou plus, supprimer la plus ancienne
        if active_sessions >= 3:
            cursor.execute('''
                DELETE FROM user_sessions 
                WHERE user_id = ? 
                ORDER BY created_at ASC 
                LIMIT 1
            ''', (user_id,))
            print(f"⚠️ Session la plus ancienne supprimée pour user_id {user_id} (limite 3 sessions)")
        
        # Créer la nouvelle session
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=24)  # Session de 24h
        
        cursor.execute('''
            INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, session_token, expires_at, ip_address, user_agent))
        
        conn.commit()
        
        # Compter les sessions actives après création
        cursor.execute('''
            SELECT COUNT(*) FROM user_sessions 
            WHERE user_id = ? AND expires_at > datetime('now')
        ''', (user_id,))
        final_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ Session créée pour user_id {user_id} ({final_count}/3 sessions actives)")
        return session_token
        
    except Exception as e:
        print(f"Erreur création session: {e}")
        return None

def get_user_by_session(session_token):
    """Récupère un utilisateur par token de session"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.email, u.name, u.subscription_status, u.trial_end_date,
                   s.expires_at
            FROM users u
            JOIN user_sessions s ON u.id = s.user_id
            WHERE s.session_token = ? AND s.expires_at > CURRENT_TIMESTAMP
        ''', (session_token,))
        
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return {
                'id': user_data[0],
                'email': user_data[1],
                'name': user_data[2],
                'subscription_status': user_data[3],
                'trial_end_date': user_data[4],
                'session_expires': user_data[5]
            }
        return None
        
    except Exception as e:
        print(f"Erreur récupération session: {e}")
        return None

def log_user_action(user_id, action, endpoint):
    """Enregistre une action utilisateur"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO usage_logs (user_id, action, endpoint)
            VALUES (?, ?, ?)
        ''', (user_id, action, endpoint))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erreur log action: {e}")

def require_auth(f):
    """Décorateur pour protéger les routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = session.get('session_token') or request.cookies.get('session_token')
        
        if not session_token:
            return redirect('/?login_required=1')
        
        user = get_user_by_session(session_token)
        if not user:
            session.pop('session_token', None)
            resp = make_response(redirect('/?session_expired=1'))
            resp.set_cookie('session_token', '', expires=0)
            return resp
        
        # Ajouter l'utilisateur au contexte de la requête
        request.current_user = user
        log_user_action(user['id'], f.__name__, request.endpoint)
        
        return f(*args, **kwargs)
    return decorated_function

# Initialiser la base de données au démarrage
init_database()
create_demo_accounts()
ensure_admin_rights()
print("✅ Système d'authentification commercial initialisé")

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                    DÉTECTION AUTOMATIQUE GEOSERVER                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def detect_working_geoserver():
    """Détecte automatiquement une URL GeoServer fonctionnelle"""
    
    # Forcer localhost si variable d'environnement présente - ARRÊT IMMÉDIAT
    if os.getenv('FORCE_LOCAL_GEOSERVER') == 'true':
        local_url = "http://localhost:8080/geoserver"
        print(f"🏠 [FORCED] GeoServer local forcé: {local_url}")
        print(f"🚫 [FORCED] Arrêt immédiat - pas de test de fallback")
        return local_url
    
    # DEUXIÈME CHECK: Variable GEOSERVER_URL avec localhost
    geoserver_url = os.getenv('GEOSERVER_URL')
    if geoserver_url and 'localhost:8080' in geoserver_url:
        print(f"🏠 [LOCALHOST_VAR] Variable GEOSERVER_URL contient localhost: {geoserver_url}")
        return geoserver_url
    
    # Priorité 1: GeoServer local (développement)
    local_url = "http://localhost:8080/geoserver"
    try:
        import requests
        response = requests.head(local_url, timeout=3, allow_redirects=True)
        if response.status_code in [200, 302]:
            print(f"✅ [DEV] GeoServer local accessible: {local_url}")
            return local_url
    except Exception as e:
        print(f"⚠️ [DEV] GeoServer local non accessible: {e}")
    
    # Priorité 2: Variable d'environnement (faire confiance directement sur Railway)
    env_url = os.getenv("GEOSERVER_URL")
    if env_url:
        # En production (Railway/Heroku), faire confiance à la variable d'environnement
        # sans test localhost car le serveur distant ne peut pas se connecter à localhost
        environment = os.getenv("ENVIRONMENT", "").lower()
        if environment in ["production", "railway"] or "railway" in os.environ.get("RAILWAY_ENVIRONMENT", ""):
            print(f"🚀 [PRODUCTION] Utilisation de GEOSERVER_URL: {env_url}")
            return env_url
        
        # En développement local, tester la connectivité
        try:
            import requests
            response = requests.head(env_url, timeout=5, allow_redirects=True)
            if response.status_code in [200, 302]:
                print(f"✅ [LOCAL] GeoServer accessible via variable d'environnement: {env_url}")
                return env_url
        except Exception as e:
            print(f"⚠️ [LOCAL] Test de la variable d'environnement échoué: {e}")
    
    # Priorité 3: Détection automatique ngrok (fallback pour développement)
    try:
        import requests
        response = requests.get("http://localhost:4040/api/tunnels", timeout=3)
        if response.status_code == 200:
            data = response.json()
            for tunnel in data.get('tunnels', []):
                if tunnel.get('proto') == 'https':
                    current_url = f"{tunnel.get('public_url')}/geoserver"
                    print(f"🔍 URL ngrok détectée automatiquement: {current_url}")
                    # Tester la connectivité
                    try:
                        test_response = requests.head(current_url, timeout=5, allow_redirects=True)
                        if test_response.status_code in [200, 302]:
                            print(f"✅ GeoServer accessible: {current_url}")
                            return current_url
                    except Exception as e:
                        print(f"❌ Test échoué pour {current_url}: {e}")
                    break
    except Exception as e:
        print(f"⚠️ Détection ngrok échouée: {e}")
    
    # Priorité 3: URL ngrok permanente UNIQUE
    fallback_urls = [
        "https://agriweb-prod.ngrok-free.app/geoserver",  # 🚀 Domaine ngrok réservé (fourni)
        "https://complete-simple-ghost.ngrok-free.app/geoserver",
    ]
    
    # Tester les URLs de fallback
    for url in fallback_urls:
        try:
            import requests
            response = requests.head(url, timeout=5, allow_redirects=True)
            if response.status_code in [200, 302]:
                print(f"✅ GeoServer accessible (fallback): {url}")
                return url
        except Exception as e:
            print(f"❌ Test échoué pour {url}: {e}")
            continue
    
    # URL par défaut si rien ne fonctionne
    final_fallback = "https://agriweb-prod.ngrok-free.app/geoserver"
    print(f"⚠️ Aucun GeoServer accessible, utilisation domaine permanent: {final_fallback}")
    return final_fallback

# Configuration pour Railway avec détection automatique
# FORÇAGE BRUTAL LOCALHOST - Ignorer detect_working_geoserver()
print("🔥 [BRUTAL FORCE] Forçage domaine ngrok réservé pour GeoServer")
GEOSERVER_URL = os.getenv("GEOSERVER_TUNNEL_URL", "https://agriweb-prod.ngrok-free.app/geoserver")
print(f"🏠 [FORCED URL] GEOSERVER_URL forcée à: {GEOSERVER_URL}")
GEOSERVER_USERNAME = os.getenv("GEOSERVER_USERNAME", "admin")
GEOSERVER_PASSWORD = os.getenv("GEOSERVER_PASSWORD", "geoserver")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

# print(f"🚀 Configuration Railway:")  # Optimisé pour production multi-user
# print(f"   - GeoServer URL: {GEOSERVER_URL}")  # Optimisé pour production multi-user
# print(f"   - GeoServer Auth: {GEOSERVER_USERNAME}:{'*' * len(GEOSERVER_PASSWORD)}")  # Optimisé pour production multi-user
# print(f"   - Port: {PORT}")  # Optimisé pour production multi-user
# print(f"   - Debug: {DEBUG}")  # Optimisé pour production multi-user

# Fonction d'authentification GeoServer
def get_geoserver_auth():
    """Retourne les credentials d'authentification GeoServer"""
    from requests.auth import HTTPBasicAuth
    return HTTPBasicAuth(GEOSERVER_USERNAME, GEOSERVER_PASSWORD)

# Add a global error handler for 500 errors to return JSON with error and traceback
from flask import jsonify
import traceback
@app.errorhandler(500)
def handle_500_error(e):
    tb = traceback.format_exc()
    return jsonify({"error": str(e), "traceback": tb}), 500

# Endpoint de santé pour Railway
@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint de santé pour Railway"""
    return jsonify({
        "status": "healthy",
        "service": "AgriWeb",
        "timestamp": datetime.now().isoformat(),
        "geoserver_url": GEOSERVER_URL
    }), 200

# Endpoint de debug pour tester les API d'authentification
@app.route("/debug/auth", methods=["GET"])
def debug_auth():
    """Debug des routes d'authentification"""
    return jsonify({
        "status": "ok",
        "message": "API d'authentification opérationnelle",
        "endpoints": {
            "register": "/register (POST)",
            "login": "/login (POST)", 
            "trial": "/api/trial (POST)",
            "logout": "/logout (POST/GET)"
        },
        "database": "SQLite operational",
        "environment": "Railway" if os.getenv("RAILWAY_ENVIRONMENT") else "Local"
    }), 200

# Route pour vérifier l'authentification (utilisée par le système de cartes)
@app.route("/check_auth", methods=["GET"])
def check_auth():
    """Vérifie si l'utilisateur est authentifié"""
    try:
        # Vérifier si l'utilisateur est connecté
        if 'user_id' in session and session.get('user_id'):
            return jsonify({
                "authenticated": True,
                "user_id": session.get('user_id'),
                "username": session.get('username', 'Utilisateur'),
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "authenticated": False,
                "message": "Utilisateur non connecté",
                "timestamp": datetime.now().isoformat()
            }), 200
    except Exception as e:
        return jsonify({
            "authenticated": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# Endpoint pour re-détecter GeoServer
@app.route("/debug/geoserver", methods=["GET"])
def debug_geoserver():
    """Re-détecte et teste GeoServer"""
    global GEOSERVER_URL
    
    old_url = GEOSERVER_URL
    new_url = detect_working_geoserver()
    
    # Test de connectivité
    try:
        import requests
        response = requests.head(new_url, timeout=5, allow_redirects=True)
        accessible = response.status_code in [200, 302]
    except:
        accessible = False
    
    # Mettre à jour l'URL globale si elle a changé
    if new_url != old_url:
        GEOSERVER_URL = new_url
        print(f"🔄 URL GeoServer mise à jour: {old_url} → {new_url}")
    
    return jsonify({
        "status": "ok",
        "previous_url": old_url,
        "current_url": new_url,
        "url_changed": new_url != old_url,
        "accessible": accessible,
        "test_timestamp": datetime.now().isoformat()
    }), 200

# Endpoint de debug pour la base de données
@app.route("/debug/database", methods=["GET"])
def debug_database():
    """Debug de la base de données pour voir les utilisateurs et tokens"""
    try:
        import sqlite3
        from datetime import datetime
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Compter les utilisateurs
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        # Lister tous les utilisateurs avec leurs tokens
        cursor.execute('''
            SELECT id, email, name, is_email_verified, 
                   email_verification_token, email_verification_expires,
                   created_at, subscription_status
            FROM users 
            ORDER BY created_at DESC
        ''')
        
        users = cursor.fetchall()
        users_info = []
        
        for user in users:
            user_info = {
                "id": user[0],
                "email": user[1], 
                "name": user[2],
                "verified": bool(user[3]),
                "has_token": user[4] is not None,
                "token_preview": user[4][:20] + "..." if user[4] else None,
                "token_expires": user[5],
                "created": user[6],
                "status": user[7]
            }
            
            # Vérifier si le token a expiré
            if user[5]:
                try:
                    expires_at = datetime.fromisoformat(user[5])
                    user_info["token_expired"] = datetime.now() > expires_at
                except:
                    user_info["token_expired"] = True
            
            users_info.append(user_info)
        
        conn.close()
        
        return jsonify({
            "status": "ok",
            "database_path": DATABASE_PATH,
            "user_count": user_count,
            "users": users_info,
            "environment": "Railway" if os.getenv("RAILWAY_ENVIRONMENT") else "Local",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "database_path": DATABASE_PATH
        }), 500

# Endpoint de debug pour tester la réinitialisation de mot de passe
@app.route("/debug/password-reset", methods=["GET", "POST"])
def debug_password_reset():
    """Debug de la réinitialisation de mot de passe"""
    try:
        if request.method == "GET":
            return jsonify({
                "status": "ok",
                "message": "Endpoint de debug pour la réinitialisation de mot de passe",
                "usage": "POST avec email pour tester la réinitialisation",
                "example": {"email": "ylaurent.perso@gmail.com"}
            }), 200
        
        # POST - Tester la réinitialisation
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({
                "status": "error",
                "error": "Email requis"
            }), 400
        
        # Importer le système d'auth
        from auth_system_improved import auth_system
        
        # Vérifier si la méthode existe
        if not hasattr(auth_system, 'request_password_reset'):
            return jsonify({
                "status": "error",
                "error": "Méthode request_password_reset non trouvée",
                "available_methods": [method for method in dir(auth_system) if not method.startswith('_')]
            }), 500
        
        # Tester la réinitialisation
        success, message = auth_system.request_password_reset(email)
        
        return jsonify({
            "status": "ok" if success else "error",
            "email": email,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }), 200 if success else 400
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": str(e)
        }), 500

# Endpoint de debug pour nettoyer les tokens de vérification
@app.route("/debug/clean-token", methods=["GET", "POST"])
def debug_clean_verification_token():
    """Nettoie les tokens de vérification résiduels"""
    try:
        if request.method == "GET":
            return jsonify({
                "status": "ok",
                "message": "Endpoint pour nettoyer les tokens de vérification résiduels",
                "usage": "POST avec email pour nettoyer le token",
                "example": {"email": "ylaurent.perso@gmail.com"}
            }), 200
        
        # POST - Nettoyer le token
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({
                "status": "error",
                "error": "Email requis"
            }), 400
        
        import sqlite3
        from datetime import datetime
        
        # Connexion à la base de données
        conn = sqlite3.connect("agriweb_users.db")
        cursor = conn.cursor()
        
        # Vérifier l'état avant
        cursor.execute('''
            SELECT id, email, is_email_verified, email_verification_token, 
                   email_verification_expires, subscription_status, trial_end_date
            FROM users WHERE email = ?
        ''', (email,))
        
        user_before = cursor.fetchone()
        if not user_before:
            return jsonify({
                "status": "error",
                "error": f"Utilisateur {email} non trouvé"
            }), 404
        
        user_id, user_email, is_verified, token, token_expires, sub_status, trial_end = user_before
        
        # Nettoyer le token de vérification et s'assurer que l'email est vérifié
        cursor.execute('''
            UPDATE users 
            SET email_verification_token = NULL, 
                email_verification_expires = NULL,
                is_email_verified = 1
            WHERE email = ?
        ''', (email,))
        
        rows_affected = cursor.rowcount
        conn.commit()
        
        # Vérifier l'état après
        cursor.execute('''
            SELECT id, email, is_email_verified, email_verification_token, 
                   email_verification_expires, subscription_status, trial_end_date
            FROM users WHERE email = ?
        ''', (email,))
        
        user_after = cursor.fetchone()
        conn.close()
        
        return jsonify({
            "status": "success",
            "message": f"Token de vérification nettoyé pour {email}",
            "email": email,
            "rows_affected": rows_affected,
            "before": {
                "id": user_before[0],
                "email": user_before[1],
                "verified": bool(user_before[2]),
                "has_token": bool(user_before[3]),
                "token_expires": user_before[4],
                "subscription": user_before[5],
                "trial_end": user_before[6]
            },
            "after": {
                "id": user_after[0],
                "email": user_after[1],
                "verified": bool(user_after[2]),
                "has_token": bool(user_after[3]),
                "token_expires": user_after[4],
                "subscription": user_after[5],
                "trial_end": user_after[6]
            },
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "details": f"Erreur lors du nettoyage du token: {str(e)}"
        }), 500

def get_geoserver_layers_info():
    """Récupère les informations sur les couches GeoServer via API REST"""
    try:
        # Utiliser l'API REST pour lister les couches (car WFS est bloqué)
        rest_url = f"{GEOSERVER_URL}/rest/layers"
        rest_response = http_session.get(rest_url, auth=get_geoserver_auth(), 
                                       headers={'Accept': 'application/json'}, timeout=10)
        
        if rest_response.status_code == 200:
            layers_data = rest_response.json()
            if 'layers' in layers_data and 'layer' in layers_data['layers']:
                layers_list = layers_data['layers']['layer']
                if isinstance(layers_list, list):
                    layer_names = [layer['name'] for layer in layers_list]
                else:
                    layer_names = [layers_list['name']]
                
                return {
                    'layer_count': len(layer_names),
                    'sample_layers': layer_names[:5],
                    'status': '✅ Connecté via REST API'
                }
        
        return {
            'layer_count': 0,
            'sample_layers': [],
            'status': f'❌ Erreur REST API: {rest_response.status_code}'
        }
    except Exception as e:
        return {
            'layer_count': 0,
            'sample_layers': [],
            'status': f'❌ Erreur: {str(e)}'
        }

# Route de test pour carte directe
@app.route("/test", methods=["GET"])
def test_carte():
    """Sert la page de test pour debug rapide"""
    return send_from_directory('.', 'test_carte_directe.html')

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                           TEMPLATES D'AUTHENTIFICATION                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# Templates HTML pour l'authentification qui fonctionnaient
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌾 AgriWeb 2.0 - Connexion</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
        }
        .container { 
            background: white; 
            padding: 3rem; 
            border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 400px; 
            width: 100%; 
        }
        .logo { text-align: center; margin-bottom: 2rem; }
        .form-group { margin: 1rem 0; }
        label { display: block; margin-bottom: 0.5rem; font-weight: 600; }
        input { 
            width: 100%; 
            padding: 0.8rem; 
            border: 2px solid #e0e0e0; 
            border-radius: 8px; 
            font-size: 1rem; 
            box-sizing: border-box;
        }
        button { 
            width: 100%; 
            background: linear-gradient(45deg, #667eea, #764ba2); 
            color: white; 
            border: none; 
            padding: 1rem; 
            border-radius: 8px; 
            font-size: 1.1rem; 
            cursor: pointer; 
            margin-top: 1rem;
        }
        button:hover { transform: translateY(-2px); }
        .links { text-align: center; margin-top: 1rem; }
        .links a { color: #667eea; text-decoration: none; }
        .demo-banner { 
            background: #e3f2fd; 
            padding: 1rem; 
            border-radius: 8px; 
            margin-bottom: 1rem; 
            text-align: center; 
            color: #1976d2; 
        }
        .error { 
            background: #ffebee; 
            color: #c62828; 
            padding: 1rem; 
            border-radius: 8px; 
            margin-bottom: 1rem; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>🌾 AgriWeb 2.0</h1>
            <p>Solution d'analyse agricole professionnelle</p>
        </div>
        
        <div class="demo-banner">
            <strong>🧪 Mode Démo</strong><br>
            Hébergement gratuit - Fonctionnalités limitées
        </div>
        
        {% if error %}
        <div class="error">
            {{ error }}
        </div>
        {% endif %}
        
        <form method="POST">
            <div class="form-group">
                <label for="email">📧 Email</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="password">🔒 Mot de passe</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit">🚀 Se connecter</button>
        </form>
        
        <div class="links">
            <a href="/register">📝 Créer un compte</a> | 
            <a href="/admin">👑 Admin</a>
        </div>
    </div>
</body>
</html>
"""

REGISTER_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📝 Inscription - AgriWeb 2.0</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; 
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            min-height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
        }
        .container { 
            background: white; 
            padding: 3rem; 
            border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 500px; 
            width: 100%; 
        }
        .form-group { margin: 1rem 0; }
        label { display: block; margin-bottom: 0.5rem; font-weight: 600; }
        input { 
            width: 100%; 
            padding: 0.8rem; 
            border: 2px solid #e0e0e0; 
            border-radius: 8px; 
            font-size: 1rem; 
            box-sizing: border-box;
        }
        button { 
            width: 100%; 
            background: linear-gradient(45deg, #28a745, #20c997); 
            color: white; 
            border: none; 
            padding: 1rem; 
            border-radius: 8px; 
            font-size: 1.1rem; 
            cursor: pointer; 
            margin-top: 1rem;
        }
        .trial-info { 
            background: #e8f5e8; 
            padding: 1rem; 
            border-radius: 8px; 
            margin: 1rem 0; 
        }
        .error { 
            background: #ffebee; 
            color: #c62828; 
            padding: 1rem; 
            border-radius: 8px; 
            margin-bottom: 1rem; 
        }
        .links { text-align: center; margin-top: 1rem; }
        .links a { color: #28a745; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📝 Inscription AgriWeb 2.0</h1>
        
        <div class="trial-info">
            <h3>🆓 Essai Gratuit Inclus</h3>
            <ul>
                <li>✅ 15 jours d'accès complet</li>
                <li>✅ 50 recherches gratuites</li>
                <li>✅ Toutes les fonctionnalités</li>
            </ul>
        </div>
        
        {% if error %}
        <div class="error">
            {{ error }}
        </div>
        {% endif %}
        
        <form method="POST">
            <div class="form-group">
                <label for="name">👤 Nom complet</label>
                <input type="text" id="name" name="name" required>
            </div>
            
            <div class="form-group">
                <label for="email">📧 Email</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="password">🔒 Mot de passe</label>
                <input type="password" id="password" name="password" required minlength="6">
            </div>
            
            <button type="submit">🚀 Créer mon compte gratuit</button>
        </form>
        
        <div class="links">
            <a href="/login">← Retour à la connexion</a>
        </div>
    </div>
</body>
</html>
"""

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                     GESTIONNAIRE D'UTILISATEURS SIMPLE                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

import uuid
import hashlib

class SimpleUserManager:
    """Gestionnaire d'utilisateurs simple sans envoi d'email"""
    def __init__(self):
        self.users = {}
        # Créer un admin par défaut
        admin_password = hashlib.sha256("admin123".encode()).hexdigest()
        self.users["admin@test.com"] = {
            'id': str(uuid.uuid4()),
            'email': "admin@test.com",
            'password': admin_password,
            'name': "Administrateur",
            'created_at': datetime.now().isoformat(),
            'active': True,
            'license_type': 'admin',
            'searches_used': 0,
            'searches_limit': 999999,
            'is_admin': True
        }
        print("🔧 SimpleUserManager initialisé avec admin par défaut")
    
    def create_user(self, email, password, name=""):
        """Créer un nouvel utilisateur"""
        if email in self.users:
            raise ValueError(f"L'utilisateur {email} existe déjà")
        
        user_id = str(uuid.uuid4())
        self.users[email] = {
            'id': user_id,
            'email': email,
            'password': hashlib.sha256(password.encode()).hexdigest(),
            'name': name,
            'created_at': datetime.now().isoformat(),
            'active': True,
            'license_type': 'trial',
            'searches_used': 0,
            'searches_limit': 50,
            'is_admin': False
        }
        print(f"👤 Utilisateur créé: {email} (ID: {user_id})")
        return user_id
    
    def authenticate_user(self, email, password):
        """Authentifier un utilisateur"""
        user = self.users.get(email)
        if user and user['password'] == hashlib.sha256(password.encode()).hexdigest():
            print(f"✅ Authentification réussie: {email}")
            return user
        print(f"❌ Authentification échouée: {email}")
        return None
    
    def get_user(self, email):
        """Récupérer un utilisateur par email"""
        return self.users.get(email)
    
    def add_user(self, email, password, name=""):
        """Alias pour create_user (compatibilité)"""
        return self.create_user(email, password, name)

# Instance du gestionnaire d'utilisateurs simple
simple_user_manager = SimpleUserManager()

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                           ROUTES D'AUTHENTIFICATION                      ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@app.route("/register_legacy", methods=["GET", "POST"])
def register_legacy():
    """Inscription d'un nouvel utilisateur - Support GET pour formulaire et POST pour données"""
    
    # Si c'est une requête GET, afficher le formulaire d'inscription
    if request.method == "GET":
        return render_template_string("""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Inscription - AgriWeb 2.0</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; 
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            min-height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
        }
        .register-container { 
            background: white; 
            padding: 2rem; 
            border-radius: 12px; 
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            width: 100%; 
            max-width: 450px; 
        }
        .logo { 
            text-align: center; 
            margin-bottom: 2rem; 
            font-size: 2rem; 
            color: #28a745; 
        }
        .form-group { 
            margin-bottom: 1rem; 
        }
        label { 
            display: block; 
            margin-bottom: 0.5rem; 
            font-weight: 600; 
            color: #333; 
        }
        input { 
            width: 100%; 
            padding: 0.75rem; 
            border: 2px solid #e9ecef; 
            border-radius: 8px; 
            font-size: 1rem;
            box-sizing: border-box;
        }
        input:focus { 
            outline: none; 
            border-color: #28a745; 
            box-shadow: 0 0 0 3px rgba(40, 167, 69, 0.1); 
        }
        .btn { 
            width: 100%; 
            padding: 0.75rem; 
            background: #28a745; 
            color: white; 
            border: none; 
            border-radius: 8px; 
            font-size: 1rem; 
            cursor: pointer; 
            transition: background 0.2s; 
        }
        .btn:hover { 
            background: #218838; 
        }
        .error { 
            color: #dc3545; 
            margin-top: 0.5rem; 
            font-size: 0.9rem; 
        }
        .success { 
            color: #28a745; 
            margin-top: 0.5rem; 
            font-size: 0.9rem; 
        }
        .login-link { 
            text-align: center; 
            margin-top: 1.5rem; 
        }
        .login-link a { 
            color: #28a745; 
            text-decoration: none; 
        }
        .login-link a:hover { 
            text-decoration: underline; 
        }
    </style>
</head>
<body>
    <div class="register-container">
        <div class="logo">🚀 AgriWeb 2.0</div>
        <h2 style="text-align: center; color: #333; margin-bottom: 2rem;">Créer un compte</h2>
        
        <form method="POST" action="/register">
            <div class="form-group">
                <label for="name">Nom complet *</label>
                <input type="text" id="name" name="name" required>
            </div>
            
            <div class="form-group">
                <label for="email">Email *</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="company">Entreprise/Organisation</label>
                <input type="text" id="company" name="company">
            </div>
            
            <div class="form-group">
                <label for="password">Mot de passe * (min. 6 caractères)</label>
                <input type="password" id="password" name="password" required minlength="6">
            </div>
            
            <button type="submit" class="btn">Créer le compte</button>
        </form>
        
        <div class="login-link">
            Déjà un compte ? <a href="/login">Se connecter</a>
        </div>
        
        <div class="login-link">
            <a href="/">← Retour à l'accueil</a>
        </div>
    </div>
</body>
</html>
        """)
    
    # Si c'est une requête POST, traiter l'inscription
    try:
        data = request.get_json() if request.is_json else request.form
        
        email = data.get('email', '').strip().lower()
        name = data.get('name', '').strip()
        company = data.get('company', '').strip()
        password = data.get('password', '').strip()
        
        # Validation des données
        if not email or not name or not password:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Tous les champs obligatoires sont requis'}), 400
            else:
                return render_template_string("""
                <script>
                    alert('Tous les champs obligatoires sont requis');
                    window.history.back();
                </script>
                """)
        
        if len(password) < 6:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Le mot de passe doit contenir au moins 6 caractères'}), 400
            else:
                return render_template_string("""
                <script>
                    alert('Le mot de passe doit contenir au moins 6 caractères');
                    window.history.back();
                </script>
                """)
        
        # Créer l'utilisateur
        success, message = create_user(email, name, company, password)
        
        if success:
            if request.is_json:
                return jsonify({'success': True, 'message': message}), 201
            else:
                return render_template_string("""
                <script>
                    alert('Compte créé avec succès ! Vous pouvez maintenant vous connecter.');
                    window.location.href = '/login';
                </script>
                """)
        else:
            if request.is_json:
                return jsonify({'success': False, 'error': message}), 400
            else:
                return render_template_string(f"""
                <script>
                    alert('Erreur : {message}');
                    window.history.back();
                </script>
                """)
            
    except Exception as e:
        print(f"Erreur register: {e}")
        if request.is_json:
            return jsonify({'success': False, 'error': 'Erreur lors de l\'inscription'}), 500
        else:
            return render_template_string("""
            <script>
                alert('Erreur lors de l\'inscription');
                window.history.back();
            </script>
            """)

@app.route("/login_legacy", methods=["GET", "POST"])
def login_legacy():
    """Connexion d'un utilisateur - Support GET pour formulaire et POST pour données"""
    
    # Si c'est une requête GET, afficher le formulaire de connexion
    if request.method == "GET":
        return render_template_string("""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔐 Connexion - AgriWeb 2.0</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; 
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            min-height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
        }
        .login-container { 
            background: white; 
            padding: 2rem; 
            border-radius: 12px; 
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            width: 100%; 
            max-width: 400px; 
        }
        .logo { 
            text-align: center; 
            margin-bottom: 2rem; 
            font-size: 2rem; 
            color: #28a745; 
        }
        .form-group { 
            margin-bottom: 1rem; 
        }
        label { 
            display: block; 
            margin-bottom: 0.5rem; 
            font-weight: 600; 
            color: #333; 
        }
        input { 
            width: 100%; 
            padding: 0.75rem; 
            border: 2px solid #e9ecef; 
            border-radius: 8px; 
            font-size: 1rem;
            box-sizing: border-box;
        }
        input:focus { 
            outline: none; 
            border-color: #28a745; 
            box-shadow: 0 0 0 3px rgba(40, 167, 69, 0.1); 
        }
        .btn { 
            width: 100%; 
            padding: 0.75rem; 
            background: #28a745; 
            color: white; 
            border: none; 
            border-radius: 8px; 
            font-size: 1rem; 
            cursor: pointer; 
            transition: background 0.2s; 
        }
        .btn:hover { 
            background: #218838; 
        }
        .register-link { 
            text-align: center; 
            margin-top: 1.5rem; 
        }
        .register-link a { 
            color: #28a745; 
            text-decoration: none; 
        }
        .register-link a:hover { 
            text-decoration: underline; 
        }
        .admin-link {
            text-align: center;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid #e9ecef;
        }
        .admin-link a {
            color: #6c757d;
            text-decoration: none;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">🔐 AgriWeb 2.0</div>
        <h2 style="text-align: center; color: #333; margin-bottom: 2rem;">Connexion</h2>
        
        <form method="POST" action="/login">
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="password">Mot de passe</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn">Se connecter</button>
        </form>
        
        <div class="register-link">
            Pas encore de compte ? <a href="/register">Créer un compte</a>
        </div>
        
        <div class="admin-link">
            <a href="/admin">Administration</a>
        </div>
        
        <div class="register-link">
            <a href="/">← Retour à l'accueil</a>
        </div>
    </div>
</body>
</html>
        """)
    
    # Si c'est une requête POST, traiter la connexion
    try:
        data = request.get_json() if request.is_json else request.form
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        
        if not email or not password:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Email et mot de passe requis'}), 400
            else:
                return render_template_string("""
                <script>
                    alert('Email et mot de passe requis');
                    window.history.back();
                </script>
                """)
        
        # Authentifier l'utilisateur
        success, user_data, message = authenticate_user(email, password)
        
        if success:
            # Créer une session
            session_token = create_session(
                user_data['id'], 
                request.remote_addr, 
                request.headers.get('User-Agent')
            )
            
            if session_token:
                # Créer la réponse de redirection
                if request.is_json:
                    resp = jsonify({
                        'success': True, 
                        'message': message,
                        'user': {
                            'name': user_data['name'],
                            'email': user_data['email'],
                            'subscription_status': user_data['subscription_status']
                        },
                        'redirect': '/app'
                    })
                else:
                    resp = make_response(redirect('/app'))
                
                # Stocker le token de session
                session['session_token'] = session_token
                resp.set_cookie('session_token', session_token, max_age=86400, httponly=True, secure=False)
                
                return resp
            else:
                if request.is_json:
                    return jsonify({'success': False, 'error': 'Erreur lors de la création de session'}), 500
                else:
                    return render_template_string("""
                    <script>
                        alert('Erreur lors de la création de session');
                        window.history.back();
                    </script>
                    """)
        else:
            if request.is_json:
                return jsonify({'success': False, 'error': message}), 401
            else:
                return render_template_string(f"""
                <script>
                    alert('Erreur : {message}');
                    window.history.back();
                </script>
                """)
            
    except Exception as e:
        print(f"Erreur login: {e}")
        if request.is_json:
            return jsonify({'success': False, 'error': 'Erreur lors de la connexion'}), 500
        else:
            return render_template_string("""
            <script>
                alert('Erreur lors de la connexion');
                window.history.back();
            </script>
            """)

@app.route("/logout", methods=["POST", "GET"])
def logout():
    """Déconnexion d'un utilisateur"""
    session.pop('session_token', None)
    resp = make_response(redirect('/'))
    resp.set_cookie('session_token', '', expires=0)
    return resp

@app.route("/api/trial", methods=["POST"])
def start_trial():
    """Démarrage d'un essai gratuit rapide"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip().lower()
        name = data.get('name', '').strip()
        company = data.get('company', '').strip()
        
        if not email or not name:
            return jsonify({'success': False, 'error': 'Email et nom requis'}), 400
        
        # Générer un mot de passe temporaire
        temp_password = secrets.token_urlsafe(12)
        
        # Créer l'utilisateur d'essai
        success, message = create_user(email, name, company, temp_password)
        
        if success:
            # Authentifier automatiquement
            auth_success, user_data, auth_message = authenticate_user(email, temp_password)
            
            if auth_success:
                session_token = create_session(
                    user_data['id'], 
                    request.remote_addr, 
                    request.headers.get('User-Agent')
                )
                
                # Stocker le token de session
                session['session_token'] = session_token
                
                return jsonify({
                    'success': True, 
                    'message': f'Essai gratuit activé ! {message}',
                    'session_token': session_token,
                    'temp_password': temp_password
                }), 201
            else:
                return jsonify({'success': False, 'error': 'Erreur lors de l\'authentification automatique'}), 500
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        print(f"Erreur trial: {e}")
        return jsonify({'success': False, 'error': 'Erreur lors de l\'activation de l\'essai'}), 500

@app.route("/profile")
@require_auth
def profile():
    """Page de profil utilisateur"""
    user = request.current_user
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Profil - AgriWeb 2.0</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header">
                            <h3>👤 Profil Utilisateur</h3>
                        </div>
                        <div class="card-body">
                            <p><strong>Nom:</strong> {{ user.name }}</p>
                            <p><strong>Email:</strong> {{ user.email }}</p>
                            <p><strong>Statut:</strong> 
                                <span class="badge bg-{{ 'warning' if user.subscription_status == 'trial' else 'success' }}">
                                    {{ 'Essai gratuit' if user.subscription_status == 'trial' else 'Abonnement actif' }}
                                </span>
                            </p>
                            {% if user.subscription_status == 'trial' %}
                            <p><strong>Fin d'essai:</strong> {{ user.trial_end_date[:10] }}</p>
                            <div class="alert alert-warning">
                                <h5>🎯 Votre essai se termine bientôt !</h5>
                                <p>Souscrivez à un abonnement pour continuer à utiliser AgriWeb 2.0.</p>
                                <a href="/subscribe" class="btn btn-primary">Voir les abonnements</a>
                            </div>
                            {% endif %}
                            
                            <div class="mt-4">
                                <a href="/app" class="btn btn-success me-2">🗺️ Retour à la carte</a>
                                <a href="/logout" class="btn btn-outline-danger">Déconnexion</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """, user=user)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                           INTÉGRATION STRIPE PAIEMENTS                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# Configuration Stripe (clés Railway)
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')  # Clé publique via variables d'environnement
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')  # Clé secrète via variables d'environnement

stripe = None
try:
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY
    print("✅ Stripe configuré")
except Exception as e:
    print(f"⚠️ Erreur configuration Stripe: {e}")
    stripe = None

@app.route("/api/create-checkout-session", methods=["POST"])
def create_checkout_session():
    """Crée une session de paiement Stripe"""
    if not stripe:
        return jsonify({'error': 'Stripe non configuré'}), 500
        
    try:
        # Accepter JSON et données de formulaire
        data = request.get_json(silent=True) or request.form
        if not data:
            return jsonify({'error': 'Aucune donnée reçue'}), 400
            
        plan = data.get('plan')
        
        if not plan:
            return jsonify({'error': 'Plan requis'}), 400
        
        # Configuration des plans avec prix Railway
        prices = {
            'basic': {
                'price_id': os.environ.get('STRIPE_PRICE_ID', 'price_1Q8trfBqUIVxhYa82QzGpK3L'),
                'name': 'AgriWeb Pro - Plan Basic',
                'amount': 3500,  # 35€ en centimes
            },
            'professional': {
                'price_id': os.environ.get('STRIPE_PRICE_ID', 'price_1Q8trfBqUIVxhYa82QzGpK3L'),
                'name': 'AgriWeb Pro - Plan Professionnel',
                'amount': 19900,  # 199€ en centimes
            },
            'team': {
                'price_id': os.environ.get('STRIPE_PRICE_ID', 'price_1Q8trfBqUIVxhYa82QzGpK3L'),
                'name': 'AgriWeb Pro - Plan Team',
                'amount': 29900,  # 299€ en centimes
            }
        }
        
        # Le plan Enterprise nécessite un devis personnalisé
        if plan == 'enterprise':
            return jsonify({'error': 'Le plan Enterprise nécessite un devis personnalisé. Veuillez nous contacter.'}), 400
        
        if plan not in prices:
            return jsonify({'error': 'Plan invalide'}), 400
            
        plan_config = prices[plan]
        
        # Créer la session Stripe Checkout
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': plan_config['name'],
                            'description': 'Accès mensuel à la plateforme AgriWeb Pro'
                        },
                        'unit_amount': plan_config['amount'],
                    },
                    'quantity': 1,
                }],
                mode='payment',  # Mode paiement unique pour commencer
                success_url=request.url_root + 'payment-success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.url_root + '?payment_cancelled=1',
                metadata={
                    'plan': plan
                }
            )
        except stripe.error.AuthenticationError as e:
            print(f"Erreur d'authentification Stripe: {e}")
            return jsonify({'error': 'Configuration Stripe invalide - vérifiez vos clés API'}), 500
        except stripe.error.StripeError as e:
            print(f"Erreur Stripe: {e}")
            return jsonify({'error': f'Erreur Stripe: {str(e)}'}), 500
        
        return jsonify({'url': checkout_session.url})
        
    except Exception as e:
        print(f"Erreur Stripe détaillée: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de la création de la session de paiement'}), 500

@app.route("/api/stripe/create-checkout", methods=["POST"])
def create_stripe_checkout():
    """Route alternative pour créer une session de paiement Stripe (compatibilité JavaScript)"""
    try:
        print("=== DEBUG /api/stripe/create-checkout ===")
        print(f"Méthode: {request.method}")
        print(f"Content-Type: {request.content_type}")
        print(f"Headers: {dict(request.headers)}")
        
        # Accepter JSON et données de formulaire
        data = request.get_json(silent=True) or request.form
        print(f"Données reçues (JSON): {request.get_json(silent=True)}")
        print(f"Données reçues (form): {dict(request.form)}")
        print(f"Données finales: {data}")
        
        if not data:
            print("ERREUR: Aucune donnée reçue")
            return jsonify({'error': 'Aucune donnée reçue'}), 400
            
        plan = data.get('plan') or data.get('price_type')
        print(f"Plan extrait: {plan}")
        
        if not plan:
            print("ERREUR: Plan requis")
            return jsonify({'error': 'Plan requis'}), 400
        
        # Configuration des liens de paiement Stripe directs
        payment_links = {
            'basic': 'https://buy.stripe.com/fZucN74w7cM59Z5ehL63K02',     # 35€/mois
            'professional': 'https://buy.stripe.com/28EcN71jVdQ9c7dehL63K01', # 199€/mois  
            'team': 'https://buy.stripe.com/dRm8wR9Qr4fz5IPb5z63K00',        # 299€/mois
            'enterprise': 'https://buy.stripe.com/00w3cx0fR3bv5IPddH63K03'    # 1620€/an (Crowdfunding -50%)
        }
        
        # Retourner le lien direct correspondant au plan
        if plan in payment_links:
            return jsonify({'url': payment_links[plan]})
        else:
            return jsonify({'error': f'Plan "{plan}" non reconnu'}), 400
            
    except Exception as e:
        print(f"Erreur création checkout: {type(e).__name__}: {e}")
        return jsonify({'error': 'Erreur lors de la création de la session de paiement'}), 500

@app.route("/subscription")
def subscription_page():
    """Page de sélection des plans d'abonnement"""
    return render_template_string(SUBSCRIPTION_TEMPLATE, stripe_public_key=STRIPE_PUBLIC_KEY)

@app.route("/demo")
@app.route("/demo-real")
def demo_page():
    """Page de démonstration ultra-moderne et interactive"""
    return render_template("demo_new.html")

@app.route("/demo-old")
def demo_page_old():
    """Ancienne page de démonstration (backup)"""
    return render_template("demo.html")

@app.route("/demo/adresses")
def demo_adresses():
    """Page démo avec exemples d'adresses"""
    return render_template("demo_adresses.html")

@app.route("/demo/communes")
def demo_communes():
    """Page démo avec exemples de communes"""
    return render_template("demo_communes.html")

@app.route("/demo/departements")
def demo_departements():
    """Page démo avec exemples de départements"""
    return render_template("demo_departements.html")

@app.route("/demo/rapports")
def demo_rapports():
    """Page démo avec exemples de rapports"""
    return render_template("demo_rapports.html")

@app.route("/demo/autocomplete")
def demo_autocomplete():
    """Page démo de l'autocomplétion intelligente pour adresses et communes"""
    return render_template("demo_autocomplete.html")

# === ROUTES DEMO INSTANTANÉES AVEC CARTES PRÉ-GÉNÉRÉES ===

@app.route("/demo/exemple/adresse")
def demo_exemple_adresse():
    """Exemple de recherche par adresse - Carte pré-générée pour 15 Rue de Nice, Toulouse"""
    # Carte pré-générée spécifique
    carte_demo = "recherche_15_Rue_de_Nice_31400_Toulouse_f6c02eb1_20251010_181958.html"
    cartes_dir = os.path.join(app.static_folder, 'cartes')
    
    # Vérifier que la carte existe
    carte_path = os.path.join(cartes_dir, carte_demo)
    if os.path.exists(carte_path):
        return send_from_directory(cartes_dir, carte_demo)
    
    # Fallback: chercher n'importe quelle carte de recherche
    if os.path.exists(cartes_dir):
        cartes_recherche = [f for f in os.listdir(cartes_dir) if f.startswith('recherche_') and f.endswith('.html')]
        if cartes_recherche:
            return send_from_directory(cartes_dir, cartes_recherche[0])
    
    # Si pas de carte, rediriger vers /app avec recherche
    return redirect("/app?search=15 Rue de Nice, Toulouse")

@app.route("/demo/exemple/commune-carte")
def demo_exemple_commune_carte():
    """Exemple de carte par commune - Carte pré-générée pour Toulouse"""
    exemple_commune = "Toulouse"
    
    # Chercher une carte commune existante
    cartes_dir = os.path.join(app.static_folder, 'cartes')
    if os.path.exists(cartes_dir):
        cartes = [f for f in os.listdir(cartes_dir) if f.endswith('.html')]
        if len(cartes) >= 2:
            # Retourner la 2ème carte comme exemple de commune
            return send_from_directory(cartes_dir, cartes[1])
    
    return redirect(f"/app?search={exemple_commune}")

@app.route("/demo/exemple/commune-rapport")
def demo_exemple_commune_rapport():
    """Exemple de rapport par commune - Rapport pré-généré pour Bordeaux"""
    exemple_commune = "Bordeaux"
    
    # Chercher un rapport existant dans static/cartes/
    cartes_dir = os.path.join(app.static_folder, 'cartes')
    if os.path.exists(cartes_dir):
        rapports = [f for f in os.listdir(cartes_dir) if 'rapport' in f.lower() and f.endswith('.html')]
        if rapports:
            return send_from_directory(cartes_dir, rapports[0])
        
        # Sinon, prendre n'importe quelle carte comme exemple
        cartes = [f for f in os.listdir(cartes_dir) if f.endswith('.html')]
        if len(cartes) >= 3:
            return send_from_directory(cartes_dir, cartes[2])
    
    return redirect(f"/app?search={exemple_commune}")

@app.route("/demo/exemple/departement")
def demo_exemple_departement():
    """Exemple d'analyse départementale - Rapport pré-généré pour la Gironde"""
    exemple_dept = "Gironde"
    
    # Chercher un rapport de département
    cartes_dir = os.path.join(app.static_folder, 'cartes')
    if os.path.exists(cartes_dir):
        rapports_dept = [f for f in os.listdir(cartes_dir) if 'departement' in f.lower() and f.endswith('.html')]
        if rapports_dept:
            return send_from_directory(cartes_dir, rapports_dept[0])
        
        # Sinon, prendre une carte comme exemple
        cartes = [f for f in os.listdir(cartes_dir) if f.endswith('.html')]
        if len(cartes) >= 4:
            return send_from_directory(cartes_dir, cartes[3])
    
    return redirect(f"/app?search={exemple_dept}")

@app.route("/payment-success")
def payment_success():
    """Page de confirmation de paiement réussi"""
    session_id = request.args.get('session_id')
    
    if not stripe or not session_id:
        return redirect('/?payment_cancelled=1')
    
    try:
        # Récupérer les détails de la session Stripe
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        if checkout_session.payment_status == 'paid':
            # Ici vous pourriez mettre à jour l'abonnement de l'utilisateur
            # update_user_subscription(checkout_session.customer_email, 'active')
            
            return redirect('/app?payment_success=1')
        else:
            return redirect('/?payment_cancelled=1')
            
    except Exception as e:
        print(f"Erreur vérification paiement: {e}")
        return redirect('/?payment_cancelled=1')

@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    """Webhook Stripe pour gérer les événements de paiement"""
    if not stripe:
        return jsonify({'error': 'Stripe non configuré'}), 500
        
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Gérer les événements Stripe
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # Activer l'abonnement utilisateur
        print(f"Paiement réussi pour session: {session['id']}")
        
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        # Renouvellement d'abonnement
        print(f"Renouvellement réussi: {invoice['id']}")
        
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        # Désactiver l'abonnement
        print(f"Abonnement annulé: {subscription['id']}")
    
    return jsonify({'status': 'success'})

@app.route('/test-couches')
def test_couches_diagnostic():
    """Page de diagnostic des couches de carte"""
    try:
        import folium
        
        # Créer une carte de test simple
        test_map = folium.Map(location=[46.8, 2.0], zoom_start=8)
        
        # Ajouter couche Esri
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri World Imagery",
            name="Satellite",
            overlay=False,
            control=True,
            show=True
        ).add_to(test_map)
        
        # Ajouter OSM
        folium.TileLayer(
            "OpenStreetMap",
            name="Fond OSM",
            overlay=False,
            control=True,
            show=False
        ).add_to(test_map)
        
        # Test polygones colorés
        test_polygons = [
            {"coords": [[[2.0, 46.0], [2.2, 46.0], [2.2, 46.2], [2.0, 46.2], [2.0, 46.0]]], "color": "red", "name": "Rouge"},
            {"coords": [[[2.4, 46.0], [2.6, 46.0], [2.6, 46.2], [2.4, 46.2], [2.4, 46.0]]], "color": "blue", "name": "Bleu"},
            {"coords": [[[2.8, 46.0], [3.0, 46.0], [3.0, 46.2], [2.8, 46.2], [2.8, 46.0]]], "color": "green", "name": "Vert"},
            {"coords": [[[3.2, 46.0], [3.4, 46.0], [3.4, 46.2], [3.2, 46.2], [3.2, 46.0]]], "color": "orange", "name": "Orange"},
            {"coords": [[[3.6, 46.0], [3.8, 46.0], [3.8, 46.2], [3.6, 46.2], [3.6, 46.0]]], "color": "purple", "name": "Violet"}
        ]
        
        for poly in test_polygons:
            geom = {"type": "Polygon", "coordinates": poly["coords"]}
            
            # Style avec closure pour capturer la couleur
            def make_style(color):
                return lambda x: {
                    "color": color,
                    "weight": 3,
                    "fillColor": color,
                    "fillOpacity": 0.4,
                    "opacity": 0.8
                }
            
            folium.GeoJson(
                geom,
                style_function=make_style(poly["color"]),
                tooltip=f"Test {poly['name']} - Couleur: {poly['color']}"
            ).add_to(test_map)
        
        # Ajouter LayerControl
        folium.LayerControl().add_to(test_map)
        
        # Générer HTML
        map_html = test_map._repr_html_()
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Diagnostic Couches</title>
    <style>
        body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
        .info {{ background: #f0f0f0; padding: 10px; margin-bottom: 10px; border-radius: 5px; }}
        .map-container {{ height: 600px; border: 1px solid #ccc; }}
    </style>
</head>
<body>
    <h1>🔍 Diagnostic des Couches de Carte</h1>
    
    <div class="info">
        <h3>🎯 Test des éléments suivants :</h3>
        <ul>
            <li>✅ Couche Esri Satellite (par défaut)</li>
            <li>✅ Couche OpenStreetMap (désactivée)</li>
            <li>🎨 Polygones : Rouge, Bleu, Vert, Orange, Violet</li>
            <li>🎛️ LayerControl pour basculer entre couches</li>
        </ul>
        
        <p><strong>Si tous les polygones apparaissent en orange :</strong> problème de style fonction</p>
        <p><strong>Si pas de couche Esri :</strong> problème de tuiles</p>
        <p><strong>Si pas de LayerControl :</strong> problème d'affichage des contrôles</p>
    </div>
    
    <div class="map-container">
        {map_html}
    </div>
    
    <div class="info">
        <h3>🔗 Actions :</h3>
        <a href="/app">← Retour à l'application</a> | 
        <a href="/test-couches">🔄 Recharger le test</a>
    </div>
</body>
</html>
        """
        
    except Exception as e:
        return f"""
<h1>❌ Erreur Test Couches</h1>
<p>Erreur : {str(e)}</p>
<pre>{traceback.format_exc()}</pre>
<a href="/app">← Retour à l'application</a>
        """

@app.route('/qrcode')
def qr_code_page():
    """Page avec QR code pour partager l'application"""
    try:
        import qrcode
        import base64
        from io import BytesIO
        
        # URL de l'application
        app_url = request.url_root
        
        # Créer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(app_url)
        qr.make(fit=True)
        
        # Générer l'image
        img = qr.make_image(fill_color="#2d5a27", back_color="white")
        
        # Convertir en base64 pour l'affichage web
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return render_template_string("""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QR Code - AgriWeb</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .qr-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .qr-card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 2rem;
            max-width: 500px;
            text-align: center;
        }
        .qr-image {
            border-radius: 15px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            max-width: 100%;
        }
        .share-buttons .btn {
            margin: 0.5rem;
            border-radius: 50px;
        }
    </style>
</head>
<body>
    <div class="qr-container">
        <div class="qr-card">
            <div class="mb-4">
                <h1 class="text-success mb-2">
                    <i class="fas fa-seedling me-2"></i>AgriWeb
                </h1>
                <p class="text-muted">Partagez votre application facilement</p>
            </div>
            
            <div class="mb-4">
                <img src="data:image/png;base64,{{ qr_code }}" 
                     class="qr-image" 
                     alt="QR Code AgriWeb">
            </div>
            
            <div class="mb-4">
                <h5><i class="fas fa-mobile-alt me-2 text-primary"></i>Comment scanner ?</h5>
                <ol class="list-unstyled text-start">
                    <li class="mb-2">📱 <strong>Ouvrez l'appareil photo</strong> de votre téléphone</li>
                    <li class="mb-2">🎯 <strong>Pointez vers le QR code</strong> ci-dessus</li>
                    <li class="mb-2">🔗 <strong>Appuyez sur la notification</strong> qui apparaît</li>
                    <li class="mb-2">🌾 <strong>Accédez directement</strong> à AgriWeb !</li>
                </ol>
            </div>
            
            <div class="mb-4">
                <small class="text-muted">
                    <i class="fas fa-link me-1"></i>{{ app_url }}
                </small>
            </div>
            
            <div class="share-buttons">
                <a href="/" class="btn btn-success">
                    <i class="fas fa-home me-2"></i>Retour Accueil
                </a>
                <button class="btn btn-primary" onclick="shareQR()">
                    <i class="fas fa-share-alt me-2"></i>Partager
                </button>
                <button class="btn btn-info" onclick="downloadQR()">
                    <i class="fas fa-download me-2"></i>Télécharger
                </button>
            </div>
            
            <div class="mt-4">
                <small class="text-muted">
                    <i class="fas fa-clock me-1"></i>Généré le {{ now.strftime('%d/%m/%Y à %H:%M') }}
                </small>
            </div>
        </div>
    </div>
    
    <script>
        function shareQR() {
            if (navigator.share) {
                navigator.share({
                    title: 'AgriWeb - Application Agricole',
                    text: 'Découvrez AgriWeb, l\\'application pour l\\'agriculture moderne',
                    url: '{{ app_url }}'
                });
            } else {
                // Fallback: copier l'URL
                navigator.clipboard.writeText('{{ app_url }}').then(() => {
                    alert('URL copiée dans le presse-papier !');
                });
            }
        }
        
        function downloadQR() {
            const link = document.createElement('a');
            link.download = 'AgriWeb_QRCode.png';
            link.href = 'data:image/png;base64,{{ qr_code }}';
            link.click();
        }
    </script>
</body>
</html>
        """, qr_code=qr_code_base64, app_url=app_url, now=datetime.now())
        
    except Exception as e:
        return f"Erreur génération QR code: {e}", 500

# Page d'accueil avec authentification commerciale
@app.route("/")
def index():
    """Page d'accueil avec authentification commerciale - Collecte emails et essais gratuits"""
    
    # Vérifier si l'utilisateur est déjà connecté
    session_token = session.get('session_token') or request.cookies.get('session_token')
    is_admin = False
    current_user = None
    
    if session_token:
        user = get_user_by_session(session_token)
        if user:
            current_user = user
            # Vérifier si l'utilisateur est admin
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user['id'],))
                admin_result = cursor.fetchone()
                is_admin = bool(admin_result[0]) if admin_result else False
                conn.close()
            except Exception as e:
                print(f"[WARN] Erreur vérification admin: {e}")
                is_admin = False
    
    # Version simplifiée pour diagnostiquer le timeout
    try:
        return render_template("homepage.html", 
                             stripe_public_key=STRIPE_PUBLIC_KEY or "", 
                             is_admin=is_admin,
                             current_user=current_user)
    except Exception as e:
        print(f"❌ [INDEX] Erreur dans index(): {e}")
        return f"Erreur page d'accueil: {e}", 500

# Route de test simple
@app.route("/test")
def test_route():
    """Route de test simple pour vérifier que le serveur fonctionne"""
    return "✅ Serveur fonctionne correctement"

# Page d'accueil ORIGINALE (temporairement commentée)
@app.route("/index_original")
def index_original():
    """Page d'accueil avec authentification commerciale - Version originale"""
    
    # Vérifier si l'utilisateur est déjà connecté
    session_token = session.get('session_token') or request.cookies.get('session_token')
    is_admin = False
    current_user = None
    
    if session_token:
        user = get_user_by_session(session_token)
        if user:
            current_user = user
            # Vérifier si l'utilisateur est admin
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user['id'],))
            admin_result = cursor.fetchone()
            is_admin = bool(admin_result[0]) if admin_result else False
            conn.close()

    return render_template("homepage.html", 
                         stripe_public_key=STRIPE_PUBLIC_KEY or "", 
                         is_admin=is_admin,
                         current_user=current_user)

# Interface complète AgriWeb (après authentification)
@app.route("/app")
@require_auth
def app_interface():
    """Interface complète AgriWeb - Nécessite authentification
    
    Accepte les paramètres d'URL suivants pour zoom automatique:
    - lat: latitude du point à centrer
    - lon: longitude du point à centrer  
    - address: nom/description du point
    """
    
    # Récupérer les paramètres de zoom depuis l'URL
    lat = request.args.get('lat')
    lon = request.args.get('lon') 
    address = request.args.get('address', 'Point d\'intérêt')
    
    # Vérifier d'abord le nouveau système d'authentification
    session_token = session.get('session_token') or request.cookies.get('session_token')
    
    if session_token:
        user = get_user_by_session(session_token)
        if user:
            # Utilisateur connecté avec le nouveau système - Interface complète
            try:
                # Préparer les options de culture pour le menu déroulant
                culture_options = sorted(list(set(rpg_culture_mapping.values())))
                
                # Passer les paramètres de zoom au template
                return render_template("index.html", 
                                       culture_options=culture_options,
                                       zoom_lat=lat,
                                       zoom_lon=lon,
                                       zoom_address=address)
            except:
                return redirect("/app")
    
    # Vérifier l'ancien système (rétrocompatibilité)
    user_authenticated = request.cookies.get('user_authenticated') or request.args.get('demo')
    if user_authenticated:
        # Ancien système - Interface complète
        try:
            # Préparer les options de culture pour le menu déroulant
            culture_options = sorted(list(set(rpg_culture_mapping.values())))
            
            # Passer les paramètres de zoom au template
            return render_template("index.html", 
                                   culture_options=culture_options,
                                   zoom_lat=lat,
                                   zoom_lon=lon,
                                   zoom_address=address)
        except:
            return redirect("/app")
    
    # Nouveaux utilisateurs - Redirection vers authentification
    return redirect("/?login_required=1")

@app.route("/auth")
def auth():
    """Page de connexion/inscription"""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🔐 Connexion - AgriWeb</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #2c5f41 0%, #4a8b3b 100%);
                min-height: 100vh; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
            }
            .login-container { 
                background: white; 
                padding: 2.5rem; 
                border-radius: 16px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                width: 100%; 
                max-width: 450px; 
            }
            .logo { 
                text-align: center; 
                margin-bottom: 2rem; 
                font-size: 2.5rem; 
                color: #2c5f41; 
                font-weight: 700;
            }
            .demo-notice {
                background: #fff3cd;
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 2rem;
                border-left: 4px solid #ffc107;
                font-size: 0.9rem;
            }
            .btn { 
                width: 100%; 
                padding: 1rem; 
                background: #28a745; 
                color: white; 
                border: none; 
                border-radius: 8px; 
                font-size: 1rem; 
                font-weight: 600; 
                cursor: pointer; 
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-block;
                text-align: center;
                margin: 0.5rem 0;
            }
            .btn:hover { 
                background: #218838; 
                transform: translateY(-2px);
            }
            .btn-secondary {
                background: transparent;
                color: #2c5f41;
                border: 2px solid #2c5f41;
            }
            .btn-secondary:hover {
                background: #2c5f41;
                color: white;
            }
            .back-link { 
                text-align: center; 
                margin-top: 2rem; 
            }
            .back-link a { 
                color: #2c5f41; 
                text-decoration: none; 
                font-weight: 600;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">🔐 AgriWeb</div>
            
            <div class="demo-notice">
                💡 <strong>En développement :</strong> L'authentification sera bientôt disponible. 
                Utilisez l'accès direct pour tester la plateforme.
            </div>
            
            <a href="/?demo=1" class="btn">🚀 Accès direct (Démo)</a>
            <a href="#" class="btn btn-secondary" onclick="alert('Fonctionnalité en développement')">📝 Créer un compte</a>
            
            <div class="back-link">
                <a href="/">← Retour à l'accueil</a>
            </div>
        </div>
    </body>
    </html>
    """)

os.makedirs("cartes", exist_ok=True)

# Session HTTP avec retry exponentiel
http_session = requests.Session()
http_session.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=3,
            backoff_factor=1,               # 1 s, 2 s, 4 s
            status_forcelist=[429, 500, 502, 503, 504],
            respect_retry_after_header=True
        )
    )
)
# Vérification de la licence
# statut = check_access()
# if statut == "LICENSED":
#     print("Licence valide, vous avez accès à toutes les fonctions.")
# elif statut == "TRIAL":
#     print("Période d'essai en cours.")
# else:
#     print("EXPIRED: veuillez acheter ou renouveler votre licence.")


# === Configuration GeoServer ===
# GEOSERVER_URL est défini plus haut avec la variable d'environnement Railway
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
SIRENE_LAYER = "gpu:GeolocalisationEtablissement_Sirene france"  # Sirène (~50 m)
GEOSERVER_WFS_URL = f"{GEOSERVER_URL}/rest/layers"  # Pour lister les couches
GEOSERVER_OWS_URL = f"{GEOSERVER_URL}/ows"  # Pour les requêtes WFS/GetFeature
ELEVEURS_LAYER = "gpu:etablissements_eleveurs"
# Ajout couche PPRI (adapter le nom si besoin)
PPRI_LAYER = "gpu:ppri"  # <-- Vérifiez le nom exact dans votre GeoServer

# Configuration Elevation API
ELEVATION_API_URL = "https://api.elevationapi.com/api/Elevation"

# === Dictionnaires de mapping ===
rpg_culture_mapping = {
    "BTH": "Blé tendre d’hiver",
    "BTP": "Blé tendre de printemps",
    "MID": "Maïs doux",
    "MIE": "Maïs ensilage",
    "MIS": "Maïs",
    "ORH": "Orge d'hiver",
    "ORP": "Orge de printemps",
    "AVH": "Avoine d’hiver",
    "AVP": "Avoine de printemps",
    "BDH": "Blé dur d’hiver",
    "BDP": "Blé dur de printemps",
    "BDT": "Blé dur de printemps semé tardivement (après le 31/05)",
    "CAG": "Autre céréale d’un autre genre",
    "CGF": "Autre céréale de genre Fagopyrum",
    "CGH": "Autre céréale de genre Phalaris",
    "CGO": "Autre céréale de genre Sorghum",
    "CGP": "Autre céréale de genre Panicum",
    "CGS": "Autre céréale de genre Setaria",
    "CHA": "Autre céréale d’hiver de genre Avena",
    "CHH": "Autre céréale d’hiver de genre Hordeum",
    "CHS": "Autre céréale d’hiver de genre Secale",
    "CHT": "Autre céréale d’hiver de genre Triticum",
    "CPA": "Autre céréale de printemps de genre Avena",
    "CPH": "Autre céréale de printemps de genre Hordeum",
    "CPS": "Autre céréale de printemps de genre Secale",
    "CPT": "Autre céréale de printemps de genre Triticum",
    "CPZ": "Autre céréale de printemps de genre Zea",
    "EPE": "Épeautre",
    "MCR": "Mélange de céréales",
    "MLT": "Millet",
    "SGH": "Seigle d’hiver",
    "SGP": "Seigle de printemps",
    "SOG": "Sorgho",
    "SRS": "Sarrasin",
    "TTH": "Triticale d’hiver",
    "TTP": "Triticale de printemps",
    "CZH": "Colza d’hiver",
    "CZP": "Colza de printemps",
    "TRN": "Tournesol",
    "ARA": "Arachide",
    "LIH": "Lin non textile d’hiver",
    "LIP": "Lin non textile de printemps",
    "MOL": "Mélange d’oléagineux",
    "NVE": "Navette d’été",
    "NVH": "Navette d’hiver",
    "OAG": "Autre oléagineux d’un autre genre",
    "OEH": "Autre oléagineux d’espèce Helianthus",
    "OEI": "Œillette",
    "OHN": "Autre oléagineux d’hiver d’espèce Brassica napus",
    "OHR": "Autre oléagineux d’hiver d’espèce Brassica rapa",
    "OPN": "Autre oléagineux de printemps d’espèce Brassica napus",
    "OPR": "Autre oléagineux de printemps d’espèce Brassica rapa",
    "SOJ": "Soja",
    "FEV": "Fève",
    "FVL": "Féverole semée avant le 31/05",
    "FVT": "Féverole semée tardivement (après le 31/05)",
    "LDH": "Lupin doux d’hiver",
    "LDP": "Lupin doux de printemps semé avant le 31/05",
    "LDT": "Lupin doux de printemps semé tardivement (après le 31/05)",
    "MPC": "Mélange de protéagineux prépondérants semés avant le 31/05 et de céréales",
    "MPP": "Mélange de protéagineux",
    "MPT": "Mélange de protéagineux semés tardivement (après le 31/05)",
    "PAG": "Autre protéagineux d’un autre genre",
    "PHI": "Pois d’hiver",
    "PPR": "Pois de printemps semé avant le 31/05",
    "PPT": "Pois de printemps semé tardivement (après le 31/05)",
    "CHV": "Chanvre",
    "LIF": "Lin fibres",
    "J5M": "Jachère de 5 ans ou moins",
    "J6P": "Jachère de 6 ans ou plus",
    "J6S": "Jachère de 6 ans ou plus déclarée comme Surface d’intérêt écologique",
    "JNO": "Jachère noire",
    "RIZ": "Riz",
    "LEC": "Lentille cultivée (non fourragère)",
    "PCH": "Pois chiche",
    "BVF": "Betterave fourragère",
    "CAF": "Carotte fourragère",
    "CHF": "Chou fourrager",
    "CPL": "Fourrage composé de céréales et/ou de protéagineux (en proportion < 50%)",
    "DTY": "Dactyle de 5 ans ou moins",
    "FAG": "Autre fourrage annuel d’un autre genre",
    "FET": "Fétuque de 5 ans ou moins",
    "FF5": "Féverole fourragère implantée pour la récolte 2015",
    "FF6": "Féverole fourragère implantée pour la récolte 2016",
    "FF7": "Féverole fourragère implantée pour la récolte 2017",
    "FF8": "Féverole fourragère implantée pour la récolte 2018",
    "FFO": "Autre féverole fourragère",
    "FLO": "Fléole de 5 ans ou moins",
    "FSG": "Autre plante fourragère sarclée d’un autre genre",
    "GAI": "Gaillet",
    "GES": "Gesse",
    "GFP": "Autre graminée fourragère pure de 5 ans ou moins",
    "JO5": "Jarosse implantée pour la récolte 2015",
    "JO6": "Jarosse implantée pour la récolte 2016",
    "JO7": "Jarosse implantée pour la récolte 2017",
    "JO8": "Jarosse implantée pour la récolte 2018",
    "JOD": "Jarosse déshydratée",
    "JOS": "Autre jarosse",
    "LEF": "Lentille fourragère",
    "LFH": "Autre lupin fourrager d’hiver",
    "LFP": "Autre lupin fourrager de printemps",
    "LH5": "Lupin fourrager d’hiver implanté pour la récolte 2015",
    "LH6": "Lupin fourrager d’hiver implanté pour la récolte 2016",
    "LH7": "Lupin fourrager d’hiver implanté pour la récolte 2017",
    "LH8": "Lupin fourrager d'hiver implanté pour la récolte 2018",
    "LO7": "Lotier implanté pour la récolte 2017",
    "LO8": "Lotier implanté pour la récolte 2018",
    "LOT": "Lotier",
    "LP5": "Lupin fourrager de printemps implanté pour la récolte 2015",
    "LP6": "Lupin fourrager de printemps implanté pour la récolte 2016",
    "LP7": "Lupin fourrager de printemps implanté pour la récolte 2017",
    "LP8": "Lupin fourrager de printemps implanté pour la récolte 2018",
    "LU5": "Luzerne implantée pour la récolte 2015",
    "LU6": "Luzerne implantée pour la récolte 2016",
    "LU7": "Luzerne implantée pour la récolte 2017",
    "LU8": "Luzerne implantée pour la récolte 2018",
    "LUD": "Luzerne déshydratée",
    "LUZ": "Autre luzerne",
    "MC5": "Mélange de légumineuses fourragères implantées pour la récolte 2015 (entre elles)",
    "MC6": "Mélange de légumineuses fourragères implantées pour la récolte 2016 (entre elles)",
    "MC7": "Mélange de légumineuses fourragères implantées pour la récolte 2017 (entre elles)",
    "MC8": "Mélange de légumineuses fourragères implantées pour la récolte 2018 (entre elles)",
    "ME5": "Mélilot implanté pour la récolte 2015",
    "ME6": "Mélilot implanté pour la récolte 2016",
    "ME7": "Mélilot implanté pour la récolte 2017",
    "ME8": "Mélilot implanté pour la récolte 2018",
    "MED": "Mélilot déshydraté",
    "MEL": "Autre mélilot",
    "MH5": "Mélange de légumineuses fourragères implantées pour la récolte 2015 et d’herbacées ou de graminées fourragères",
    "MH6": "Mélange de légumineuses fourragères implantées pour la récolte 2016 et d’herbacées ou de graminées fourragères",
    "MH7": "Mélange de légumineuses fourragères implantées pour la récolte 2017 et d’herbacées ou de graminées fourragères",
    "MI7": "Minette implanté pour la récolte 2017",
    "MI8": "Minette implanté pour la récolte 2018",
    "MIN": "Minette",
    "ML5": "Mélange de légumineuses fourragères implantées pour la récolte 2015 (entre elles)",
    "ML6": "Mélange de légumineuses fourragères implantées pour la récolte 2016 (entre elles)",
    "ML7": "Mélange de légumineuses fourragères implantées pour la récolte 2017 (entre elles)",
    "ML8": "Mélange de légumineuses fourragères implantées pour la récolte 2018 (entre elles)",
    "MLC": "Mélange de légumineuses fourragères prépondérantes et de céréales et/ou d’oléagineux",
    "MLD": "Mélange de légumineuses déshydratées (entre elles)",
    "MLF": "Mélange de légumineuses fourragères (entre elles)",
    "MLG": "Mélange de légumineuses prépondérantes au semis et de graminées fourragères de 5 ans ou moins",
    "MOH": "Moha",
    "NVF": "Navet fourrager",
    "PAT": "Pâturin commun de 5 ans ou moins",
    "PFH": "Autre pois fourrager d’hiver",
    "PFP": "Autre pois fourrager de printemps",
    "PH5": "Pois fourrager d’hiver implanté pour la récolte 2015",
    "PH6": "Pois fourrager d’hiver implanté pour la récolte 2016",
    "PH7": "Pois fourrager d’hiver implanté pour la récolte 2017",
    "PH8": "Pois fourrager d’hiver implanté pour la récolte 2018",
    "PP5": "Pois fourrager de printemps implanté pour la récolte 2015",
    "PP6": "Pois fourrager de printemps implanté pour la récolte 2016",
    "PP7": "Pois fourrager de printemps implanté pour la récolte 2017",
    "PP8": "Pois fourrager de printemps implanté pour la récolte 2018",
    "RDF": "Radis fourrager",
    "SA5": "Sainfoin implanté pour la récolte 2015",
    "SA6": "Sainfoin implanté pour la récolte 2016",
    "SA7": "Sainfoin implanté pour la récolte 2017",
    "SA8": "Sainfoin implanté pour la récolte 2018",
    "SAD": "Sainfoin déshydraté",
    "SAI": "Autre sainfoin",
    "SE5": "Serradelle implantée pour la récolte 2015",
    "SE6": "Serradelle implantée pour la récolte 2016",
    "SE7": "Serradelle implantée pour la récolte 2017",
    "SE8": "Serradelle implantée pour la récolte 2018",
    "SED": "Serradelle déshydratée",
    "SER": "Autre serradelle",
    "TR5": "Trèfle implanté pour la récolte 2015",
    "TR6": "Trèfle implanté pour la récolte 2016",
    "TR7": "Trèfle implanté pour la récolte 2017",
    "TR8": "Trèfle implanté pour la récolte 2018",
    "TRD": "Trèfle déshydraté",
    "TRE": "Autre trèfle",
    "VE5": "Vesce implantée pour la récolte 2015",
    "VE6": "Vesce implantée pour la récolte 2016",
    "VE7": "Vesce implantée pour la récolte 2017",
    "VE8": "Vesce implantée pour la récolte 2018",
    "VED": "Vesce déshydratée",
    "VES": "Autre vesce",
    "XFE": "X-Felium de 5 ans ou moins",
    "BOP": "Bois pâturé",
    "SPH": "Surface pastorale - herbe prédominante et ressources fourragères ligneuses présentes",
    "SPL": "Surface pastorale - ressources fourragères ligneuses prédominantes",
    "PPH": "Prairie permanente - herbe prédominante (ressources fourragères ligneuses absentes ou peu présentes)",
    "PRL": "Prairie en rotation longue (6 ans ou plus)",
    "PTR": "Autre prairie temporaire de 5 ans ou moins",
    "RGA": "Ray-grass de 5 ans ou moins",
    "AGR": "Agrume",
    "ANA": "Ananas",
    "AVO": "Avocat",
    "BCA": "Banane créole (fruit et légume) - autre",
    "BCF": "Banane créole (fruit et légume) - fermage",
    "BCI": "Banane créole (fruit et légume) - indivision",
    "BCP": "Banane créole (fruit et légume) - propriété ou faire valoir direct",
    "BCR": "Banane créole (fruit et légume) - réforme foncière",
    "BEA": "Banane export - autre",
    "BEF": "Banane export - fermage",
    "BEI": "Banane export - indivision",
    "BEP": "Banane export - propriété ou faire valoir direct",
    "BER": "Banane export - réforme foncière",
    "CAC": "Café / Cacao",
    "CBT": "Cerise bigarreau pour transformation",
    "PFR": "Petit fruit rouge",
    "PRU": "Prune d’Ente pour transformation",
    "PVT": "Pêche Pavie pour transformation",
    "PWT": "Poire Williams pour transformation",
    "VGD": "Verger (DROM)",
    "VRG": "Verger",
    "RVI": "Restructuration du vignoble",
    "VRC": "Vigne : raisins de cuve",
    "VRN": "Vigne : raisins de cuve non en production",
    "VRT": "Vigne : raisins de table",
    "CAB": "Caroube",
    "CTG": "Châtaigne",
    "NOS": "Noisette",
    "NOX": "Noix",
    "PIS": "Pistache",
    "OLI": "Oliveraie",
    "ANE": "Aneth",
    "ANG": "Angélique",
    "ANI": "Anis",
    "BAR": "Bardane",
    "BAS": "Basilic",
    "DBM": "Brôme",
    "DBR": "Bourrache",
    "DCF": "Chou fourrager",
    "DCM": "Cameline",
    "DCR": "Cresson alénois",
    "DCZ": "Colza",
    "DDC": "Dactyle",
    "DFL": "Fléole",
    "DFN": "Fenugrec",
    "DFT": "Fétuque",
    "DFV": "Féverole",
    "DGS": "Gesse cultivée",
    "DLN": "Lin",
    "DLL": "Lentille",
    "DLP": "Lupin (blanc, bleu, jaune)",
    "DLT": "Lotier corniculé",
    "DLZ": "Luzerne cultivée",
    "DMD": "Moutarde",
    "DMH": "Moha",
    "DML": "Millet jaune, perlé",
    "DMN": "Minette",
    "DMT": "Mélilot",
    "DNG": "Nyger",
    "DNT": "Navette",
    "DNV": "Navet",
    "DPC": "Pois chiche",
    "DPH": "Phacélie",
    "DPS": "Pois",
    "DPT": "Pâturin commun",
    "DRD": "Radis (fourrager, chinois)",
    "DRG": "Ray-grass",
    "DRQ": "Roquette",
    "DSD": "Serradelle",
    "DSF": "Sorgho fourrager"
}
# Variable globale pour stocker les paramètres de la dernière recherche
last_map_params = {}

ELEVEUR_LABELS = {
    "siret":       "SIRET",
    "dateCreati":  "Date de création",
    "denominati":  "Dénomination",
    "nomUniteLe":  "Nom unité légale",
    "nomUsageUn":  "Nom d’usage",
    "prenom1Uni":  "Prénom",
    "activite_1":  "Activité principale",
    "numeroVoie":  "N° voie",
    "typeVoieEt":  "Type voie",
    "libelleVoi":  "Libellé voie",
    "codePostal":  "CP",
    "libelleCom":  "Commune",
    "codeCommun":  "Code commune",
    "x":           "X (m, EPSG:2154)",
    "y":           "Y (m, EPSG:2154)",
}
ELEVEUR_FIELDS_TO_SHOW = [
    "siret",
    "dateCreati",
    "denominati",
    "nomUniteLe",
    "nomUsageUn",
    "prenom1Uni",
    "activite_1",
    "numeroVoie",
    "typeVoieEt",
    "libelleVoi",
    "codePostal",
    "libelleCom",
    "codeCommun",
    "x",
    "y",
]
# === Mapping pour les informations HTA ===
hta_mapping = {
    "Code": "Code",
    "Nom": "Nom",
    "S3REnR": "S3REnR",
    "Taux d'affectation": "Taux d'aff",
    "Coordonnée X": "X",
    "Coordonnée Y": "Y",
    "Puissance": "Puissance",
    "Puissance projets": "Puissanc_1",
    "Puissance EnR connectée": "Puissanc_2",
    "Capacité": "CapacitÃ©",  # Corrigé selon les données réelles
    "Capacité suppl.": "CapacitÃ©_1",
    "Attention": "Attention_",
    "Quote-Part unitaire": "Quote-Part",
    "Convention signée": "dont la co",
    "Capacité RT": "CapacitÃ©_2",
    "Travaux RT": "Travaux RT",
    "RTE Capacité": "RTE - Capa",
    "RTE Capacité 1": "RTE - Ca_1",
    "Capacité suppl. 2": "CapacitÃ©_3",
    "Puissance 2": "Puissanc_4",
    "Nombre": "Nombre de",
    "Nombre suppl.": "Nombre d_1",
    "Consommation": "Consommati",
    "Tension Avant": "Tension av",
    "Tension Après": "Tension am",
    "Travaux GR": "Travaux GR",
    "Puissance 3": "Puissanc_5",
    "Puissance EnR projets": "Puissanc_6",
    "Capacité suppl. 3": "CapacitÃ©_4",
    "Capacité suppl. 4": "CapacitÃ©_5",
    "Puissance 4": "Puissanc_7",
    "Nombre suppl. 2": "Nombre d_2",
    "Nombre suppl. 3": "Nombre d_3",
    "Consommation suppl.": "Consomma_1",
    "Tension 1": "Tension _1",
    "Tension 2": "Tension _2",
    "Travaux suppl.": "Travaux _1",
    "Puissance 5": "Puissanc_8",
    "Puissance 6": "Puissanc_9",
    "Capacité suppl. 5": "CapacitÃ©_6",
    "Travaux in": "Travaux in",
    "Capacité suppl. 6": "CapacitÃ©_7",
    "GRDHTB - C": "GRDHTB - C",
    "GRDHTB - 1": "GRDHTB -_1"
}

def on_import_license():
    filename = filedialog.askopenfilename(
        title="Sélectionnez votre fichier licence",
        filetypes=[("Licence files", "*.lic"), ("All files", "*.*")]
    )
    # if filename:
    #     with open(filename, "rb") as src, open(LICENSE_FILE, "wb") as dst:
    #         dst.write(src.read())
    #     print("Licence importée avec succès !")
    if filename:
        print("Licence importée avec succès ! (fonctionnalité désactivée, module manquant)")

def main_license():
    root = tk.Tk()
    root.title("Mon Application - Import Licence")
    btn = tk.Button(root, text="Importer licence", command=on_import_license)
    btn.pack(padx=20, pady=20)
    root.mainloop()

def get_communes_for_dept(dept):
    """
    Retourne une liste de features (GeoJSON) représentant les communes
    du département donné, avec leur nom, leur centre et leur contour.
    """
    # On demande au service Geo API Gouv le nom, le centre et le contour
    url = (
        f"https://geo.api.gouv.fr/departements/{dept}/communes"
        "?fields=nom,centre,contour"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        communes = resp.json()
        features = []
        for c in communes:
            centre  = c.get("centre")
            contour = c.get("contour")
            # on choisit le contour si dispo, sinon le centre
            geom = contour or centre
            if geom:
                features.append({
                    "type": "Feature",
                    "properties": {
                        "nom": c.get("nom"),
                        "centre": centre
                    },
                    "geometry": geom
                })
        return features
    except Exception as e:
        print(f"[get_communes_for_dept] Erreur : {e}")
        return []
    
def fetch_gpu_data(endpoint, geom, partition=None, categorie=None, limit=1000):
    base_url = "https://apicarto.ign.fr/api/gpu"
    url = f"{base_url}/{endpoint}"
    params = {"geom": json.dumps(geom), "_limit": limit}
    if partition:
        params["partition"] = partition
    if categorie:
        params["categorie"] = categorie
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"[fetch_gpu_data] Erreur {resp.status_code} sur {endpoint}: {resp.text}")
            return None
    except Exception as e:
        print(f"[fetch_gpu_data] Exception lors de l'appel à {endpoint}: {e}")
        return None
def get_all_gpu_data(geom):
    endpoints = [
        "municipality",
        "document",
        "zone-urba",
        "secteur-cc",
        "prescription-surf",
        "prescription-lin",
        "prescription-pct",
        "info-surf",
        "info-lin",
        "info-pct",
        "acte-sup",
        "assiette-sup-s",
        "assiette-sup-l",
        "assiette-sup-p",
        "generateur-sup-s",
        "generateur-sup-l",
        "generateur-sup-p"
    ]
    results = {}
    for ep in endpoints:
        data = fetch_gpu_data(ep, geom)
        results[ep] = data
    return results

# Fonction supprimée - conservé seulement main() à la fin du fichier
def get_api_cadastre_data(point_geojson):
    url = "https://apicarto.ign.fr/api/cadastre/parcelle"
    params = {
        "geom": json.dumps(point_geojson),
        "_limit": 1000,
        "source_ign": "PCI"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.ok:
            return response.json()
        return None
    except Exception as e:
        print("Erreur API cadastre IGN:", e)
        return None  # ou {} selon ton code

def build_report_data(lat, lon, address=None, ht_radius_km=1.0, sirene_radius_km=0.05):
    if address is None:
        address = f"{lat}, {lon}"

    ht_radius_deg = ht_radius_km / 111
    sirene_radius_deg = sirene_radius_km / 111

    parcelle = get_parcelle_info(lat, lon)
    if not parcelle:
        all_parcelles = get_all_parcelles(lat, lon, radius=0.03)
        if all_parcelles.get("features"):
            parcelle = all_parcelles["features"][0]["properties"]
    parcelles_all = get_all_parcelles(lat, lon, radius=0.03)

    postes = get_nearest_postes(lat, lon, radius_deg=0.1)
    ht_postes = get_nearest_ht_postes(lat, lon)
    plu_info = get_plu_info(lat, lon, radius=0.03)
    zaer_data = get_zaer_info(lat, lon, radius=0.03)
    rpg_data = get_rpg_info(lat, lon, radius=0.0027)

    from shapely.geometry import shape
    for feat in rpg_data:
        feat = decode_rpg_feature(feat)
        centroid = shape(feat["geometry"]).centroid.coords[0]
        min_bt = calculate_min_distance((centroid[0], centroid[1]), postes)
        feat["properties"]["distance_au_poste"] = round(min_bt, 2) if min_bt is not None else "N/A"

    sirene_data = get_sirene_info(lat, lon, radius=sirene_radius_deg)
    parkings_data = get_parkings_info(lat, lon, radius=0.03)
    friches_data = get_friches_info(lat, lon, radius=0.03)
    potentiel_solaire_data = get_potentiel_solaire_info(lat, lon)

    eleveurs_bbox = f"{lon-0.03},{lat-0.03},{lon+0.03},{lat+0.03},EPSG:4326"
    eleveurs_data = fetch_wfs_data(ELEVEURS_LAYER, eleveurs_bbox)

    altitude_m = get_elevation_at_point(lat, lon)

    search_radius = 0.03
    geom = {"type": "Point", "coordinates": [lon, lat]}
    api_cadastre = get_api_cadastre_data(geom)
    api_nature = get_all_api_nature_data(geom)
    api_urbanisme = get_all_gpu_data(geom)

    geoportail_url = (
        f"https://www.geoportail-urbanisme.gouv.fr/map/#tile=1&lon={lon}&lat={lat}"
        f"&zoom=19&mlon={lon}&mlat={lat}"
    )

    capacites_reseau = get_nearest_capacites_reseau(lat, lon, count=3, radius_deg=ht_radius_deg)
    hta_serializable = []
    for item in capacites_reseau:
        props = item["properties"]
        ht_item = {dk: props.get(sk, "Non défini") for dk, sk in hta_mapping.items()}
        ht_item["distance"] = item["distance"]
        hta_serializable.append(ht_item)

    default_tilt = 30
    default_azimuth = 180
    kwh_an = get_pvgis_production(float(lat), float(lon), default_tilt, default_azimuth, peakpower=1.0)

    # Récupérer les données GeoRisques
    georisques_risks = fetch_georisques_risks(lat, lon)
    print(f"🔍 [BUILD_REPORT] GeoRisques reçues: {type(georisques_risks)} avec {len(georisques_risks) if georisques_risks else 0} catégories")

    return {
        "lat": lat,
        "lon": lon,
        "address": address,
        "geoportail_url": geoportail_url,
        "parcelle": parcelle,
        "postes": postes,
        "ht_postes": ht_postes,
        "hta": hta_serializable,
        "plu_info": plu_info,
        "zaer": zaer_data,
        "rpg": rpg_data,
        "sirene": sirene_data,
        "parkings": parkings_data,
        "friches": friches_data,
        "potentiel_solaire": potentiel_solaire_data,
        "api_cadastre": api_cadastre,
        "api_nature": api_nature,
        "api_urbanisme": api_urbanisme,
        "eleveurs": eleveurs_data,
        "altitude_m": altitude_m,
        "kwh_per_kwc": round(kwh_an, 2) if kwh_an is not None else "N/A",
        "ht_radius_km": ht_radius_km,
        "sirene_radius_km": sirene_radius_km,
        "search_radius": search_radius,
        "georisques_risks": georisques_risks
    }


def wrap_geometry_as_feature(geom):
    if not geom or not isinstance(geom, dict):
        return None
    gtype = geom.get("type")
    if not gtype:
        return None
    if gtype in ["FeatureCollection", "Feature"]:
        return geom
    if gtype in ["MultiPolygon", "Polygon", "MultiLineString", "LineString", "Point", "MultiPoint"]:
        return {
            "type": "Feature",
            "properties": {},
            "geometry": geom
        }
    return None

##############################
# Fonctions utilitaires
##############################
def geocode_address(address):
    """
    Géocodage avec double sécurité : API IGN française puis fallback Nominatim
    Validation de cohérence pour éviter les résultats incorrects
    """
    
    def extract_city_from_address(addr):
        """Extrait le nom de la ville depuis une adresse"""
        # Patterns courants : "..., Ville" ou "Ville" en fin
        addr_clean = addr.strip().lower()
        for separator in [',', ' - ', ' / ']:
            if separator in addr_clean:
                parts = addr_clean.split(separator)
                return parts[-1].strip()
        return addr_clean
    
    def is_result_relevant(result_label, search_address):
        """Vérifie si le résultat trouvé correspond à l'adresse recherchée"""
        search_city = extract_city_from_address(search_address)
        result_lower = result_label.lower()
        
        # Vérifie si la ville recherchée apparaît dans le résultat
        return search_city in result_lower
    
    # Tentative 1: API IGN Géoplateforme (optimisée pour la France)
    try:
        url = "https://data.geopf.fr/geocodage/search"
        params = {
            "q": address,
            "limit": 3,  # Plus de résultats pour validation
            "index": "address"
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            
            # Cherche le meilleur résultat avec validation
            for feature in features:
                coords = feature["geometry"]["coordinates"]
                props = feature["properties"]
                result_label = props.get('label', '')
                
                if is_result_relevant(result_label, address):
                    print(f"[DEBUG] Geocodage IGN validé: {result_label} -> {coords[1]:.6f}, {coords[0]:.6f}")
                    return coords[1], coords[0]  # lat, lon
            
            # Si aucun résultat validé, prend le premier (fallback)
            if features:
                feature = features[0]
                coords = feature["geometry"]["coordinates"]
                props = feature["properties"]
                print(f"[DEBUG] Geocodage IGN (non validé): {props.get('label', address)} -> {coords[1]:.6f}, {coords[0]:.6f}")
                # Ne retourne pas le résultat non validé, passe à Nominatim
                
    except Exception as e:
        print(f"[WARN] Erreur API IGN geocodage: {e}")
    
    # Tentative 2: Fallback vers Nominatim avec restriction France
    try:
        geolocator = Nominatim(user_agent="geoapp", timeout=10)
        location = geolocator.geocode(f"{address}, France", country_codes="fr")
        if location:
            print(f"[DEBUG] Geocodage Nominatim: {location.address} -> {location.latitude:.6f}, {location.longitude:.6f}")
            return location.latitude, location.longitude
        
    except Exception as e:
        print(f"[WARN] Erreur Nominatim geocodage: {e}")
    
    print(f"[ERROR] Aucun geocodage trouve pour: {address}")
    return None

def get_address_from_coordinates(lat, lon):
    """
    Géocodage inverse avec l'API IGN Géoplateforme
    Récupère l'adresse la plus proche à partir de coordonnées lat/lon
    API sans clé, limite 50 req/s
    """
    try:
        url = "https://data.geopf.fr/geocodage/reverse"
        params = {
            'lat': lat,
            'lon': lon,
            'limit': 1,
            'index': 'address'  # Focus sur les adresses
        }
        
        response = http_session.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])
            if features:
                props = features[0].get('properties', {})
                # Construire l'adresse complète
                parts = []
                if props.get('housenumber'):
                    parts.append(props['housenumber'])
                if props.get('street'):
                    parts.append(props['street'])
                elif props.get('name'):
                    parts.append(props['name'])
                if props.get('postcode'):
                    parts.append(props['postcode'])
                if props.get('city'):
                    parts.append(props['city'])
                
                address = ' '.join(parts) if parts else None
                distance = props.get('distance', 0)
                
                return {
                    'address': address,
                    'distance': distance,
                    'postcode': props.get('postcode'),
                    'city': props.get('city'),
                    'citycode': props.get('citycode'),
                    'context': props.get('context'),
                    'score': props.get('score', 0)
                }
        return None
    except Exception as e:
        safe_print(f"🔴 [ADRESSE IGN] Erreur géocodage inverse: {e}")
        return None
    
# Cache pour les résultats Sirene (éviter appels répétés)
_sirene_cache = {}
_sirene_failures = set()  # SIRET qui ont échoué (ne pas réessayer)

def fetch_sirene_info(siret, max_retries=0, timeout=0.5):
    """
    Récupère les infos Sirene avec la NOUVELLE API Recherche Entreprises
    https://recherche-entreprises.api.gouv.fr
    
    Optimisé pour être RAPIDE: timeout court et pas de retry par défaut
    
    Args:
        siret: Numéro SIRET à rechercher
        max_retries: Nombre de tentatives (défaut: 0 = 1 seule tentative)
        timeout: Timeout en secondes (défaut: 0.5s)
    
    Returns:
        dict: Données Sirene ou None si erreur
    """
    # Vérifier le cache
    if siret in _sirene_cache:
        return _sirene_cache[siret]
    
    # Ne pas réessayer les SIRET qui ont échoué
    if siret in _sirene_failures:
        return None
    
    # NOUVELLE API: recherche-entreprises.api.gouv.fr
    # On recherche par SIRET dans le paramètre q
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={siret}"
    
    for attempt in range(max_retries + 1):
        try:
            response = http_session.get(url, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier si on a des résultats
                if data.get('total_results', 0) > 0 and data.get('results'):
                    result = data['results'][0]
                    
                    # Adapter la structure au format attendu par le code
                    # (compatibilité avec l'ancienne API Sirene)
                    formatted_data = {
                        'etablissement': {
                            'siret': result.get('siege', {}).get('siret', siret),
                            'siren': result.get('siren', siret[:9] if len(siret) >= 9 else ''),
                            'uniteLegale': {
                                'denominationUniteLegale': result.get('nom_complet') or result.get('nom_raison_sociale'),
                                'activitePrincipaleUniteLegale': result.get('activite_principale'),
                                'categorieJuridiqueUniteLegale': result.get('nature_juridique'),
                            },
                            'adresseEtablissement': result.get('siege', {}).get('adresse', '')
                        }
                    }
                    
                    # Mettre en cache le succès
                    _sirene_cache[siret] = formatted_data
                    return formatted_data
                else:
                    # Aucun résultat = SIRET invalide ou non trouvé
                    _sirene_failures.add(siret)
                    return None
                    
            elif response.status_code == 404:
                # 404 = SIRET invalide, ne pas réessayer
                _sirene_failures.add(siret)
                return None
            else:
                # Autre erreur HTTP
                _sirene_failures.add(siret)
                return None
                
        except requests.exceptions.Timeout:
            # Timeout = API lente ou down, ne pas réessayer
            _sirene_failures.add(siret)
            return None
            
        except requests.exceptions.ConnectionError:
            # Connexion impossible, ne pas réessayer
            _sirene_failures.add(siret)
            return None
            
        except Exception:
            # Erreur autre, ne pas réessayer
            _sirene_failures.add(siret)
            return None
    
    # Si on arrive ici, aucune tentative n'a réussi
    _sirene_failures.add(siret)
    return None

# Par exemple, à la fin de la fusion des rapports:
def fusion_communes(communes_reports):
    merged = {}
    for rpt in communes_reports:
        for k, v in rpt.items():
            if k not in merged: merged[k] = []
            # v = liste de features OU propriétés → normalise ici
            if isinstance(v, list) and v and "geometry" in v[0]:
                merged[k].extend(v)
            elif isinstance(v, dict) and v.get("type") == "FeatureCollection":
                merged[k].extend(v.get("features", []))
            # else: ignorer ou traiter cas spéciaux
    # Emballe tout en FeatureCollection pour chaque clé
    return {k: {"type": "FeatureCollection", "features": v} for k, v in merged.items()}


# (Suppressed duplicate fetch_wfs_data definition to avoid conflicts)

    
def get_parcelle_info(lat, lon):
    bbox = f"{lon-0.001},{lat-0.001},{lon+0.001},{lat+0.001},EPSG:4326"
    features = fetch_wfs_data(CADASTRE_LAYER, bbox)
    point = Point(lon, lat)
    for feature in features:
        geom = shape(feature["geometry"])
        if geom.contains(point):
            parcelle_info = feature["properties"]
            parcelle_info["geometry"] = feature["geometry"]
            return parcelle_info
    return None

def get_all_parcelles(lat, lon, radius=0.03):
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
    x, y = transformer.transform(lon, lat)
    bbox = f"{x - radius * 111000},{y - radius * 111000},{x + radius * 111000},{y + radius * 111000},EPSG:2154"
    url = f"{GEOSERVER_URL}/cite/wfs"
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": PARCELLE_LAYER,
        "outputFormat": "application/json",
        "bbox": bbox
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # Silencieux pour éviter spam - GeoServer ngrok probablement inactif
        # print(f"[get_all_parcelles] Erreur : {e}")
        return {"type": "FeatureCollection", "features": []}
        print(f"   Layer: {PARCELLE_LAYER}")
        if response is not None:
            print(f"   Status Code: {response.status_code}")
            print(f"   Réponse (300 premiers caractères): {response.text[:300]}")
        # Toujours respecter le standard GeoJSON pour éviter les plantages en aval
        return {"type": "FeatureCollection", "features": []}


def get_all_postes(lat, lon, radius_deg=0.1):
    bbox = f"{lon-radius_deg},{lat-radius_deg},{lon+radius_deg},{lat+radius_deg},EPSG:4326"
    features = fetch_wfs_data(POSTE_LAYER, bbox)
    if not features:
        # print(f"[DEBUG] Aucun poste trouvé dans le bbox {bbox}")  # Optimisé pour performance
        return []
    
    point = Point(lon, lat)
    postes = []
    for feature in features:
        geom_shp = shape(feature["geometry"])
        dist = geom_shp.distance(point) * 111000  # Conversion en mètres
        props = feature["properties"].copy() if feature.get("properties") else {}
        props["distance"] = round(dist, 2)
        postes.append({
            "type": "Feature",
            "properties": props,
            "geometry": mapping(geom_shp)
        })
    # print(f"[DEBUG] {len(postes)} postes trouvés, distances: {[p['distance'] for p in postes[:3]]}")  # Optimisé pour performance
    return postes  # Pas de slicing ici

def get_all_ht_postes(lat, lon, radius_deg=0.5):
    bbox = f"{lon-radius_deg},{lat-radius_deg},{lon+radius_deg},{lat+radius_deg},EPSG:4326"
    features = fetch_wfs_data(HT_POSTE_LAYER, bbox)
    point = Point(lon, lat)
    postes = []
    for feature in features:
        geom = shape(feature["geometry"])
        distance = geom.distance(point) * 111000
        props = feature["properties"].copy() if feature.get("properties") else {}
        props["distance"] = round(distance, 2)
        postes.append({
            "type": "Feature",
            "properties": props,
            "geometry": mapping(geom)
        })
    return postes  # Pas de slicing ici])[:3]

def get_all_capacites_reseau(lat, lon, radius_deg=0.1):
    bbox = f"{lon-radius_deg},{lat-radius_deg},{lon+radius_deg},{lat+radius_deg},EPSG:4326"
    # print(f"[DEBUG CAPACITES] bbox: {bbox}")  # Optimisé pour performance
    # print(f"[DEBUG CAPACITES] layer: {CAPACITES_RESEAU_LAYER}")  # Optimisé pour performance
    
    features = fetch_wfs_data(CAPACITES_RESEAU_LAYER, bbox)
    # print(f"[DEBUG CAPACITES] features brutes trouvées: {len(features) if features else 0}")  # Optimisé pour performance
    
    if features and len(features) > 0:
        # print(f"[DEBUG CAPACITES] Premier exemple: {list(features[0].get('properties', {}).keys())[:10]}")  # Optimisé pour performance
        pass
    
    capacites = []
    point = Point(lon, lat)
    for feature in features:
        try:
            geom = shape(feature["geometry"])
            distance = geom.distance(point) * 111000
            props = feature["properties"].copy() if feature.get("properties") else {}
            props["distance"] = round(distance, 2)
            capacites.append({
                "type": "Feature",
                "properties": props,
                "geometry": mapping(geom)
            })
        except Exception as e:
            # print(f"[DEBUG CAPACITES] Erreur traitement feature: {e}")  # Optimisé pour performance
            continue
    
    # print(f"[DEBUG CAPACITES] capacités finales: {len(capacites)}")  # Optimisé pour performance
    return sorted(capacites, key=lambda x: x.get("properties", {}).get("distance", float('inf')))


def get_plu_info(lat, lon, radius=0.03):
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    features = fetch_wfs_data(PLU_LAYER, bbox)
    plu_info = []
    for feature in features:
        props = feature["properties"]
        plu_info.append({
            "insee": props.get("insee"),
            "typeref": props.get("typeref"),
            "archive_url": props.get("archiveUrl"),
            "files": props.get("files", "").split(", ")
        })
    return plu_info

def get_sirene_info(lat, lon, radius):
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    return fetch_wfs_data(SIRENE_LAYER, bbox)

def get_rpg_info(lat, lon, radius=0.0027):
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    # print(f"[DEBUG RPG] BBOX: {bbox}")  # Optimisé pour performance
    # print(f"[DEBUG RPG] Layer: {PARCELLES_GRAPHIQUES_LAYER}")  # Optimisé pour performance
    
    features = fetch_wfs_data(PARCELLES_GRAPHIQUES_LAYER, bbox)
    # print(f"[DEBUG RPG] Features trouvées: {len(features) if features else 0}")  # Optimisé pour performance
    
    if features:
        # print(f"[DEBUG RPG] Première feature: {list(features[0].get('properties', {}).keys())}")  # Optimisé pour performance
        pass
    
    return features

def get_parkings_info(lat, lon, radius=0.03):
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    return fetch_wfs_data(PARKINGS_LAYER, bbox)

def get_friches_info(lat, lon, radius=0.03):
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    return fetch_wfs_data(FRICHES_LAYER, bbox)

def get_potentiel_solaire_info(lat, lon, radius=1.0):
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    return fetch_wfs_data(POTENTIEL_SOLAIRE_LAYER, bbox)

def get_zaer_info(lat, lon, radius=0.03):
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    return fetch_wfs_data(ZAER_LAYER, bbox)

def get_friches_specialisees(lat, lon, radius=0.05):
    """
    Récupère les données des 3 couches spécialisées de friches pour recherche par département
    - gpu:L_FRICHES_AGRI_DDT_2020_S_019 : Friches agricoles DDT 2020
    - gpu:friches-standard : Friches standard
    - gpu:POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93 : Potentiel solaire sur friches
    """
    bbox = f"{lon - radius},{lat - radius},{lon + radius},{lat + radius},EPSG:4326"
    
    friches_data = {
        'friches_agri_ddt': [],
        'friches_standard': [],
        'friches_solaires': []
    }
    
    try:
        # Couche 1: Friches agricoles DDT 2020
        # print(f"🏚️ [FRICHES] Récupération friches agricoles DDT...")  # Optimisé pour performance
        friches_data['friches_agri_ddt'] = fetch_wfs_data("gpu:L_FRICHES_AGRI_DDT_2020_S_019", bbox) or []
        # print(f"   → {len(friches_data['friches_agri_ddt'])} friches agricoles DDT trouvées")  # Optimisé pour performance
    except Exception as e:
        # print(f"⚠️ [WARN] Erreur friches agricoles DDT: {e}")  # Optimisé pour performance
        pass
    
    try:
        # Couche 2: Friches standard
        # print(f"🏚️ [FRICHES] Récupération friches standard...")  # Optimisé pour performance
        friches_data['friches_standard'] = fetch_wfs_data("gpu:friches-standard", bbox) or []
        # print(f"   → {len(friches_data['friches_standard'])} friches standard trouvées")  # Optimisé pour performance
    except Exception as e:
        # print(f"⚠️ [WARN] Erreur friches standard: {e}")  # Optimisé pour performance
        pass
    
    try:
        # Couche 3: Potentiel solaire sur friches
        # print(f"☀️ [SOLAIRE] Récupération potentiel solaire friches...")  # Optimisé pour performance
        friches_data['friches_solaires'] = fetch_wfs_data("gpu:POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93", bbox) or []
        # print(f"   → {len(friches_data['friches_solaires'])} sites à potentiel solaire trouvés")  # Optimisé pour performance
    except Exception as e:
        # print(f"⚠️ [WARN] Erreur potentiel solaire friches: {e}")  # Optimisé pour performance
        pass
    
    total = len(friches_data['friches_agri_ddt']) + len(friches_data['friches_standard']) + len(friches_data['friches_solaires'])
    # print(f"✅ [FRICHES] Total: {total} éléments récupérés")  # Optimisé pour performance
    
    return friches_data

# ===== NOUVELLES FONCTIONS POUR RECHERCHE PAR POLYGONE COMMUNE =====
def get_data_by_commune_polygon(geom_geojson, api_endpoint, layer_name=None):
    """
    Récupère des données en utilisant directement le polygone de la commune
    via l'API Carto selon la documentation officielle
    """
    import json
    import requests
    
    try:
        if layer_name:
            # Pour les données WFS (parkings, friches, etc.)
            # On utilise une approche hybride : bbox + filtrage géométrique
            if isinstance(geom_geojson, dict):
                from shapely.geometry import shape
                commune_poly = shape(geom_geojson)
                minx, miny, maxx, maxy = commune_poly.bounds
                bbox = f"{minx},{miny},{maxx},{maxy},EPSG:4326"
                
                # print(f"🔍 [POLYGON_SEARCH] {layer_name}: bbox {bbox}")  # Optimisé pour performance
                features = fetch_wfs_data(layer_name, bbox)
                
                # Filtrage géométrique précis
                if features:
                    filtered = []
                    for f in features:
                        if "geometry" not in f:
                            continue
                        try:
                            geom = shape(f["geometry"])
                            if not geom.is_valid:
                                geom = geom.buffer(0)
                            if geom.intersects(commune_poly):
                                filtered.append(f)
                        except Exception as e:
                            continue
                    # print(f"✅ [POLYGON_SEARCH] {layer_name}: {len(filtered)}/{len(features)} features dans la commune")  # Optimisé pour performance
                    return filtered
                return features
        else:
            # Pour l'API Carto directe (cadastre, etc.)
            params = {
                "geom": json.dumps(geom_geojson) if isinstance(geom_geojson, dict) else geom_geojson,
                "_limit": 1000
            }
            
            # print(f"🔍 [API_CARTO] {api_endpoint} avec géométrie commune")  # Optimisé pour performance
            resp = requests.get(api_endpoint, params=params, timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                features = data.get('features', [])
                # print(f"✅ [API_CARTO] {api_endpoint}: {len(features)} features trouvées")  # Optimisé pour performance
                return features
            else:
                # print(f"⚠️ [API_CARTO] {api_endpoint}: erreur {resp.status_code}")  # Optimisé pour performance
                return []
                
    except Exception as e:
        # print(f"❌ [POLYGON_SEARCH] Erreur {api_endpoint}: {e}")  # Optimisé pour performance
        return []

def get_rpg_info_by_polygon(commune_geom):
    """Récupère les données RPG en utilisant le polygone exact de la commune"""
    return get_data_by_commune_polygon(commune_geom, "https://apicarto.ign.fr/api/rpg/parcelles", PARCELLES_GRAPHIQUES_LAYER)

def get_parkings_info_by_polygon(commune_geom):
    """Récupère les données parkings en utilisant le polygone exact de la commune"""
    return get_data_by_commune_polygon(commune_geom, None, PARKINGS_LAYER)

def get_friches_info_by_polygon(commune_geom):
    """Récupère les données friches en utilisant le polygone exact de la commune"""
    return get_data_by_commune_polygon(commune_geom, None, FRICHES_LAYER)

def get_solaire_info_by_polygon(commune_geom):
    """Récupère les données solaires en utilisant le polygone exact de la commune"""
    return get_data_by_commune_polygon(commune_geom, None, POTENTIEL_SOLAIRE_LAYER)

def get_zaer_info_by_polygon(commune_geom):
    """Récupère les données ZAER en utilisant le polygone exact de la commune"""
    return get_data_by_commune_polygon(commune_geom, None, ZAER_LAYER)

def get_plu_info_by_polygon(commune_geom):
    """Récupère les données PLU en utilisant le polygone exact de la commune"""
    return get_data_by_commune_polygon(commune_geom, None, PLU_LAYER)

def get_sirene_info_by_polygon(commune_geom):
    """Récupère les données Sirene en utilisant le polygone exact de la commune"""
    return get_data_by_commune_polygon(commune_geom, None, SIRENE_LAYER)

def get_batiments_info_by_polygon(commune_geom):
    """
    Récupère TOUS les bâtiments d'une commune en utilisant OpenStreetMap via l'API Overpass
    
    Cette fonction utilise la même méthodologie robuste que les parkings :
    - API Cadastre pour les contours de commune ✅
    - OpenStreetMap pour les bâtiments ✅
    """
    import json
    import requests
    from shapely.geometry import shape, Polygon
    from shapely.ops import transform as shp_transform
    from pyproj import Transformer
    
    # print(f"🏠 [BATIMENTS_OSM] Récupération via OpenStreetMap (Overpass API)")  # Optimisé pour performance
    
    try:
        commune_poly = shape(commune_geom)
        bounds = commune_poly.bounds
        minx, miny, maxx, maxy = bounds
        
        # Calculer la taille de la commune
        total_area = (maxx - minx) * (maxy - miny)
        # print(f"📐 [BATIMENTS] Superficie bbox: {total_area:.6f}° (~{total_area*12100:.0f}km²)")  # Optimisé pour performance
        
        # Centroïde pour les requêtes par rayon si nécessaire
        centroid = commune_poly.centroid
        center_lat, center_lon = centroid.y, centroid.x
        
        # Calculer un rayon approximatif pour couvrir toute la commune
        # Distance du centre au coin le plus éloigné
        import math
        max_distance = max(
            math.sqrt((maxx - center_lon)**2 + (maxy - center_lat)**2),
            math.sqrt((minx - center_lon)**2 + (miny - center_lat)**2)
        )
        radius_meters = int(max_distance * 111000)  # Conversion degrés -> mètres
        
        # print(f"🎯 [BATIMENTS] Centre: ({center_lat:.4f}, {center_lon:.4f}), Rayon: {radius_meters}m")  # Optimisé pour performance
        
        # Requête Overpass pour récupérer tous les bâtiments dans la zone
        overpass_query = f"""
        [out:json][timeout:60];
        (
          way["building"](around:{radius_meters},{center_lat},{center_lon});
          relation["building"](around:{radius_meters},{center_lat},{center_lon});
        );
        out geom;
        """
        
        # print(f"🌐 [BATIMENTS] Envoi requête Overpass...")  # Optimisé pour performance
        
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=overpass_query,
            timeout=120  # Timeout plus long pour les grandes communes
        )
        
        if response.status_code != 200:
            # print(f"❌ [BATIMENTS] Erreur Overpass: {response.status_code}")  # Optimisé pour performance
            return {"type": "FeatureCollection", "features": []}
        
        data = response.json()
        elements = data.get("elements", [])
        # print(f"📊 [BATIMENTS] {len(elements)} éléments OSM bruts récupérés")  # Optimisé pour performance
        
        # Convertir les éléments OSM en GeoJSON
        all_features = []
        
        for elem in elements:
            try:
                if elem.get("type") == "way" and elem.get("geometry"):
                    # Construire le polygone du bâtiment
                    coords = [[node["lon"], node["lat"]] for node in elem["geometry"]]
                    
                    if len(coords) >= 3:
                        # Fermer le polygone si nécessaire
                        if coords[0] != coords[-1]:
                            coords.append(coords[0])
                        
                        # Créer la géométrie Shapely pour test d'intersection
                        building_poly = Polygon(coords)
                        
                        # Vérifier que le bâtiment est vraiment dans la commune
                        if commune_poly.contains(building_poly) or commune_poly.intersects(building_poly):
                            # Propriétés du bâtiment OSM
                            props = elem.get("tags", {}).copy()
                            props.update({
                                "osm_id": elem.get("id"),
                                "osm_type": elem.get("type"),
                                "source": "OpenStreetMap"
                            })
                            
                            feature = {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [coords]
                                },
                                "properties": props
                            }
                            all_features.append(feature)
                            
                elif elem.get("type") == "relation" and elem.get("members"):
                    # Relations plus complexes (bâtiments multipolygones)
                    # Pour l'instant on les ignore, mais on pourrait les traiter
                    continue
                    
            except Exception as e:
                # print(f"⚠️ [BATIMENTS] Erreur conversion élément OSM: {e}")  # Optimisé pour performance
                continue
        
        # print(f"✅ [BATIMENTS_OSM] {len(all_features)} bâtiments filtrés dans la commune")  # Optimisé pour performance
        
        # Calcul des surfaces pour statistiques
        to_l93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True).transform
        surfaces = []
        
        for feat in all_features[:100]:  # Échantillon pour stats
            try:
                geom = shape(feat["geometry"])
                surface_m2 = shp_transform(to_l93, geom).area
                surfaces.append(surface_m2)
            except:
                continue
        
        if surfaces:
            avg_surface = sum(surfaces) / len(surfaces)
            surfaces_100m2_plus = [s for s in surfaces if s >= 100]
            ratio_100m2 = len(surfaces_100m2_plus) / len(surfaces) if surfaces else 0
            estimated_100m2 = int(len(all_features) * ratio_100m2)
            
            # print(f"📊 [STATS] Surface moyenne: {avg_surface:.1f}m² (échantillon)")  # Optimisé pour performance
            # print(f"📊 [STATS] Estimation bâtiments >100m²: {estimated_100m2}/{len(all_features)} ({100*ratio_100m2:.1f}%)")  # Optimisé pour performance
        
        return {
            "type": "FeatureCollection",
            "features": all_features,
            "metadata": {
                "method": "openstreetmap_overpass",
                "radius_meters": radius_meters,
                "center": [center_lat, center_lon],
                "osm_elements_raw": len(elements),
                "buildings_filtered": len(all_features)
            }
        }
        
    except Exception as e:
        # print(f"❌ [BATIMENTS_OSM] Erreur globale: {e}")  # Optimisé pour performance
        return {"type": "FeatureCollection", "features": []}

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

def calculate_min_distance_to_lines(centroid, lines_features):
    """
    Calcule la distance minimale d'un point (centroïde) aux lignes HTA.
    
    Args:
        centroid: [longitude, latitude] du point
        lines_features: Liste des features de lignes (GeoJSON LineString)
    
    Returns:
        float: Distance minimale en mètres, ou None si pas de lignes
    """
    if not lines_features:
        return None
    
    from pyproj import Transformer
    from shapely.ops import transform as shp_transform
    
    # Transformer pour projection métrique (EPSG:2154 pour la France)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
    
    point_wgs84 = Point(centroid)
    point_metric = shp_transform(transformer.transform, point_wgs84)
    
    distances = []
    
    for line_feature in lines_features:
        try:
            line_geom_wgs84 = shape(line_feature["geometry"])
            # Transformer la ligne en coordonnées métriques
            line_geom_metric = shp_transform(transformer.transform, line_geom_wgs84)
            # Calcul de la distance en mètres (projection métrique)
            dist_meters = line_geom_metric.distance(point_metric)
            distances.append(dist_meters)
        except Exception as e:
            print(f"⚠️ Erreur calcul distance ligne: {e}")
            continue
    
    return min(distances) if distances else None

def flatten_gpu_dict_to_featurecollection(gpu_dict):
    features = []
    for key, value in gpu_dict.items():
        # Chaque "value" devrait être une FeatureCollection
        if isinstance(value, dict) and value.get("type") == "FeatureCollection":
            features += value.get("features", [])
    return {"type": "FeatureCollection", "features": features}

########################################
# Appels API (cadastre, nature, GPU)
########################################


def get_batiments_data(geom):
    """
    Récupère les empreintes de bâtiments via OpenStreetMap Overpass API.
    L'API Cadastre bâtiment n'existant pas, nous utilisons directement OSM.
    
    Args:
        geom: Géométrie GeoJSON (Point, Polygon, etc.)
    
    Returns:
        dict: FeatureCollection des bâtiments ou None si erreur
    """
    # Méthode 1: OpenStreetMap Overpass API (source principale pour les bâtiments)
    try:
        from shapely.geometry import shape
        
        if geom.get("type") == "Point":
            lon, lat = geom["coordinates"]
            # Requête Overpass pour les bâtiments dans un rayon de 500m
            overpass_query = f"""
            [out:json][timeout:25];
            (
              way["building"](around:500,{lat},{lon});
              relation["building"](around:500,{lat},{lon});
            );
            out geom;
            """
        else:
            # CORRECTION: Pour un polygone, utiliser le polygone complet avec la syntaxe poly
            try:
                print("🔄 [BATIMENTS] Utilisation du polygone complet pour OSM Overpass")
                
                # Convertir le polygone en coordonnées pour Overpass
                # Overpass utilise la syntaxe poly:"lat1 lon1 lat2 lon2 ..."
                if geom.get("type") == "Polygon":
                    polygon_coords = geom["coordinates"][0]  # Premier ring du polygone
                elif geom.get("type") == "MultiPolygon":
                    # Pour MultiPolygon, prendre le premier polygone
                    polygon_coords = geom["coordinates"][0][0]
                else:
                    raise ValueError(f"Type de géométrie non supporté: {geom.get('type')}")
                
                # Limiter le nombre de points pour éviter les URLs trop longues
                max_points = 50  # Réduire pour éviter les timeouts
                if len(polygon_coords) > max_points:
                    # Simplifier plus agressivement pour éviter les échecs
                    step = max(2, len(polygon_coords) // max_points)
                    polygon_coords = polygon_coords[::step]
                    # S'assurer que le polygone est fermé
                    if polygon_coords[0] != polygon_coords[-1]:
                        polygon_coords.append(polygon_coords[0])
                
                # Convertir en format Overpass: "lat lon lat lon ..."
                poly_string = " ".join([f"{coord[1]} {coord[0]}" for coord in polygon_coords])
                
                print(f"🔍 [BATIMENTS] Requête OSM avec polygone de {len(polygon_coords)} points (simplifié)")
                
                # Vérifier que la chaîne n'est pas trop longue
                if len(poly_string) > 8000:  # Limite sécuritaire pour URL
                    print(f"⚠️ [BATIMENTS] Polygone trop complexe ({len(poly_string)} chars), utilisation bbox")
                    raise ValueError("Polygone trop complexe")
                
                overpass_query = f"""
                [out:json][timeout:30];
                (
                  way["building"](poly:"{poly_string}");
                  relation["building"](poly:"{poly_string}");
                );
                out geom;
                """
            except Exception as e:
                print(f"⚠️ [BATIMENTS] Erreur construction requête polygone: {e}")
                print("🔄 [BATIMENTS] Fallback vers méthode BBOX au lieu de centroïde")
                # Fallback vers bbox au lieu de centroïde pour couvrir toute la commune
                try:
                    # Utiliser la bbox de la commune entière
                    geom_shape = shape(geom)
                    minx, miny, maxx, maxy = geom_shape.bounds
                    
                    print(f"🔍 [BATIMENTS] Utilisation bbox: {minx:.4f},{miny:.4f},{maxx:.4f},{maxy:.4f}")
                    
                    overpass_query = f"""
                    [out:json][timeout:30];
                    (
                      way["building"]({miny},{minx},{maxy},{maxx});
                      relation["building"]({miny},{minx},{maxy},{maxx});
                    );
                    out geom;
                    """
                except Exception as e2:
                    print(f"⚠️ [BATIMENTS] Impossible de calculer la bbox: {e2}")
                    return None
        
        overpass_url = "https://overpass-api.de/api/interpreter"
        response = requests.post(overpass_url, data=overpass_query, timeout=30)
        
        if response.status_code == 200:
            osm_data = response.json()
            # Convertir les données OSM en GeoJSON
            features = []
            for element in osm_data.get("elements", []):
                if element.get("type") == "way" and element.get("geometry"):
                    coords = [[node["lon"], node["lat"]] for node in element["geometry"]]
                    if len(coords) > 2:
                        # Fermer le polygone si nécessaire
                        if coords[0] != coords[-1]:
                            coords.append(coords[0])
                        
                        feature = {
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [coords]
                            },
                            "properties": {
                                "source": "OpenStreetMap",
                                "building": element.get("tags", {}).get("building", "yes"),
                                "osm_id": element.get("id")
                            }
                        }
                        features.append(feature)
            
            if features:
                print(f"✅ [BATIMENTS] {len(features)} bâtiments trouvés via OpenStreetMap")
                return {"type": "FeatureCollection", "features": features}
        else:
            print(f"⚠️ [BATIMENTS] Overpass API: {response.status_code}")
    except Exception as e:
        print(f"⚠️ [BATIMENTS] Erreur OpenStreetMap: {e}")
    
    print("❌ [BATIMENTS] Aucune source de données bâtiments disponible")
    return None

def calculate_surface_libre_parcelle(parcelle_geom, batiments_data):
    """
    Calcule la surface libre d'une parcelle en soustrayant les surfaces bâties.
    
    Args:
        parcelle_geom: Géométrie GeoJSON de la parcelle
        batiments_data: FeatureCollection des bâtiments
    
    Returns:
        dict: {"surface_totale_m2": float, "surface_batie_m2": float, "surface_libre_m2": float, "surface_libre_pct": float}
    """
    try:
        from shapely.geometry import shape
        from shapely.ops import transform as shp_transform
        from pyproj import Transformer
        
        # Transformer vers Lambert 93 pour calculs de surface précis
        to_l93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True).transform
        
        # Géométrie de la parcelle en Lambert 93
        parcelle_shp = shape(parcelle_geom)
        parcelle_l93 = shp_transform(to_l93, parcelle_shp)
        surface_totale_m2 = parcelle_l93.area
        
        # Calculer la surface bâtie
        surface_batie_m2 = 0.0
        batiments_count = 0
        
        if batiments_data and batiments_data.get("features"):
            for batiment in batiments_data["features"]:
                batiment_geom = batiment.get("geometry")
                if not batiment_geom:
                    continue
                
                try:
                    batiment_shp = shape(batiment_geom)
                    batiment_l93 = shp_transform(to_l93, batiment_shp)
                    
                    # Intersection entre la parcelle et le bâtiment
                    intersection = parcelle_l93.intersection(batiment_l93)
                    if intersection.area > 0:
                        surface_batie_m2 += intersection.area
                        batiments_count += 1
                except Exception as e:
                    print(f"⚠️ [SURFACE_LIBRE] Erreur intersection bâtiment: {e}")
                    continue
        
        # Calculs finaux
        surface_libre_m2 = max(0, surface_totale_m2 - surface_batie_m2)
        surface_libre_pct = (surface_libre_m2 / surface_totale_m2 * 100) if surface_totale_m2 > 0 else 0
        
        result = {
            "surface_totale_m2": round(surface_totale_m2, 2),
            "surface_batie_m2": round(surface_batie_m2, 2),
            "surface_libre_m2": round(surface_libre_m2, 2),
            "surface_libre_pct": round(surface_libre_pct, 1),
            "batiments_count": batiments_count
        }
        
        print(f"📊 [SURFACE_LIBRE] Parcelle: {result['surface_totale_m2']}m² total, {result['surface_batie_m2']}m² bâti ({batiments_count} bât.), {result['surface_libre_m2']}m² libre ({result['surface_libre_pct']}%)")
        
        return result
        
    except Exception as e:
        print(f"❌ [SURFACE_LIBRE] Erreur calcul surface libre: {e}")
        return {
            "surface_totale_m2": 0,
            "surface_batie_m2": 0,
            "surface_libre_m2": 0,
            "surface_libre_pct": 0,
            "batiments_count": 0,
            "error": str(e)
        }

def get_api_nature_data(geom, endpoint="/nature/natura-habitat"):
    url = f"https://apicarto.ign.fr/api{endpoint}"
    params = {"geom": json.dumps(geom), "_limit": 1000}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    print(f"Erreur API Nature: {response.status_code} - {response.text}")
    return None

def get_all_api_nature_data(geom):
    """
    Interroge tous les endpoints nature disponibles selon la documentation officielle API Nature v2.9.0
    """
    endpoints = [
        # Natura 2000
        ("/nature/natura-habitat", "Natura 2000 Directive Habitat"),
        ("/nature/natura-oiseaux", "Natura 2000 Directive Oiseaux"),
        
        # ZNIEFF
        ("/nature/znieff1", "ZNIEFF Type 1"),
        ("/nature/znieff2", "ZNIEFF Type 2"),
        
        # Parcs
        ("/nature/pn", "Parcs Nationaux"),
        ("/nature/pnr", "Parcs Naturels Régionaux"),
        
        # Réserves naturelles
        ("/nature/rnn", "Réserves Naturelles Nationales"),
        ("/nature/rnc", "Réserves Naturelles de Corse"),
        
        # Chasse et faune sauvage
        ("/nature/rncf", "Réserves Nationales de Chasse et Faune Sauvage")
    ]
    
    all_features = []
    
    for endpoint, type_name in endpoints:
        try:
            data = get_api_nature_data(geom, endpoint)
            if data and data.get("features"):
                # Ajouter le type de protection aux propriétés
                for feature in data["features"]:
                    if "properties" not in feature:
                        feature["properties"] = {}
                    feature["properties"]["TYPE_PROTECTION"] = type_name
                
                all_features.extend(data["features"])
                # print(f"[API NATURE] {type_name}: {len(data['features'])} zones trouvées")  # Optimisé pour performance
            else:
                # print(f"[API NATURE] {type_name}: 0 zones trouvées")  # Optimisé pour performance
                pass
        except Exception as e:
            # print(f"[API NATURE] Erreur {endpoint}: {e}")  # Optimisé pour performance
            pass
    
    if all_features:
        # print(f"[API NATURE] Total: {len(all_features)} zones naturelles protégées")  # Optimisé pour performance
        return {
            "type": "FeatureCollection",
            "features": all_features
        }
    else:
        # print(f"[API NATURE] Aucune zone naturelle trouvée")  # Optimisé pour performance
        return {"type": "FeatureCollection", "features": []}

def flatten_feature_collections(fc):
    """
    Prend un FeatureCollection qui peut contenir des FeatureCollection imbriquées à plusieurs niveaux
    et retourne un vrai FeatureCollection à plat (liste de Features uniquement).
    """
    out = []
    if not fc or "features" not in fc:
        return {"type": "FeatureCollection", "features": []}
    for f in fc["features"]:
        if isinstance(f, dict) and f.get("type") == "FeatureCollection":
            # recursion pour aplatir tous les niveaux
            out.extend(flatten_feature_collections(f).get("features", []))
        elif isinstance(f, dict) and f.get("type") == "Feature":
            out.append(f)
        # Optionnel : tu peux logger ou ignorer les cas non dict/geojson
    return {"type": "FeatureCollection", "features": out}

def fetch_wfs_data(layer_name, bbox, srsname="EPSG:4326"):
    layer_q = quote(layer_name, safe=':')
    url = f"{GEOSERVER_OWS_URL}?service=WFS&version=2.0.0&request=GetFeature&typeName={layer_q}&outputFormat=application/json&bbox={bbox}&srsname={srsname}"
    try:
        resp = http_session.get(url, auth=get_geoserver_auth(), timeout=10)
        resp.raise_for_status()
        if 'xml' in resp.headers.get('Content-Type', ''):
            print(f"[fetch_wfs_data] GeoServer error XML for {layer_name}:\n{resp.text[:200]}")
            return []
        return resp.json().get('features', [])
    except Exception as e:
        print(f"[fetch_wfs_data] Erreur {layer_name}: {e}")
        return []

def get_elevation_profile(points):
    geojson = {
        "type": "MultiPoint",
        "coordinates": [[lon, lat] for lat, lon in points]
    }
    payload = {"points": geojson, "dataSetName": "SRTM_GL3"}
    url = f"{ELEVATION_API_URL}/points"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print("Erreur Elevation API:", e)
    return None

def get_commune_report(commune_name, culture="", min_area_ha=0, max_area_ha=1e9, ht_max_km=5.0, bt_max_km=5.0, sirene_km=5.0):
    # 1) Récupère infos de la commune (nom, insee, centre, contour, population)
    commune_infos = requests.get(
        f"https://geo.api.gouv.fr/communes?nom={quote_plus(commune_name)}&fields=centre,contour,code,population,surface"
    ).json()
    if not commune_infos or not commune_infos[0].get("contour"):
        return None
    info = commune_infos[0]
    contour = info["contour"]
    centre = info["centre"]
    insee = info.get("code")
    population = info.get("population")
    surface = round(info.get("surface", 0) / 100, 2)  # m² → ha
    centroid = [centre["coordinates"][1], centre["coordinates"][0]]

    # 2) Emprise bbox pour limiter les requêtes WFS
    from shapely.geometry import shape
    commune_poly = shape(contour)
    minx, miny, maxx, maxy = commune_poly.bounds
    bbox = f"{minx},{miny},{maxx},{maxy},EPSG:4326"

    # 3) Récupère toutes les entités dans le bbox puis filtre par intersection
    def filter_in_commune(features):
        return [
            f for f in features
            if "geometry" in f and shape(f["geometry"]).intersects(commune_poly)
        ]

    rpg_raw         = filter_in_commune(get_rpg_info(centroid[0], centroid[1], radius=0.1))
    postes_bt_data  = filter_in_commune(fetch_wfs_data(POSTE_LAYER, bbox))
    postes_hta_data = filter_in_commune(fetch_wfs_data(HT_POSTE_LAYER, bbox))
    eleveurs_data   = filter_in_commune(fetch_wfs_data(ELEVEURS_LAYER, bbox))
    sirene_data     = filter_in_commune(get_sirene_info(centroid[0], centroid[1], radius=sirene_km / 111.0))
    hta_capacites   = filter_in_commune(fetch_wfs_data(CAPACITES_RESEAU_LAYER, bbox))
    api_nature      = get_api_nature_data(contour)
    api_cadastre    = get_api_cadastre_data(contour)

    # 4) RPG filtré (culture, surface, distances)
    from shapely.ops import transform as shp_transform
    from pyproj import Transformer
    to_l93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True).transform

    rpg_parcelles = []
    for feat in (rpg_raw or []):
        dec   = decode_rpg_feature(feat)
        poly  = shape(dec["geometry"])
        props = dec["properties"]

        # a) culture
        if culture and culture.lower() not in props.get("Culture", "").lower():
            continue

        # b) surface (ha)
        ha = shp_transform(to_l93, poly).area / 10_000.0
        if ha < min_area_ha or ha > max_area_ha:
            continue

        # c) distances réseaux (m)
        cent   = poly.centroid.coords[0]
        d_bt   = calculate_min_distance(cent, postes_bt_data)
        d_hta  = calculate_min_distance(cent, postes_hta_data)

        props.update({
            "surface": round(ha, 3),
            "coords": [cent[1], cent[0]],
            "distance_bt": round(d_bt, 2) if d_bt is not None else None,
            "distance_hta": round(d_hta, 2) if d_hta is not None else None,
            "lien_geoportail": f"https://www.geoportail.gouv.fr/carte?c={cent[0]},{cent[1]}&z=18"
        })
        rpg_parcelles.append(props)

    # 5) Prépare les éleveurs (liens annuaire/entreprise)
    for eleveur in eleveurs_data:
        props = eleveur.get("properties", {})
        nom_url = (props.get("nomUniteLe", "") + " " + props.get("denominati", "")).strip().replace(" ", "+")
        ville_url = (props.get("libelleCom", "") or "").replace(" ", "+")
        props["lien_annuaire"] = f"https://www.pagesjaunes.fr/recherche/{ville_url}/{nom_url}"
        siret = props.get("siret", "")
        props["lien_entreprise"] = f"https://annuaire-entreprises.data.gouv.fr/etablissement/{siret}" if siret else "#"

    # 6) Prépare les postes BT/HTA (distance, nom)
    def poste_label(poste):
        props = poste.get("properties", {})
        nom = props.get("Nom") or props.get("nom") or props.get("NOM") or "Poste"
        dist = poste.get("distance", "")
        return {"nom": nom, "distance": dist}

    postes_bt = [poste_label(p) for p in postes_bt_data]
    postes_hta = [poste_label(p) for p in postes_hta_data]

    # 7) Rapport final
    return {
        "nom": commune_name,
        "insee": insee,
        "surface": surface,
        "population": population,
        "centroid": centroid,
        "rpg_parcelles": rpg_parcelles,
        "postes_bt": postes_bt,
        "postes_hta": postes_hta,
        "eleveurs": [e.get("properties", {}) for e in eleveurs_data],
        "hta_capacites": hta_capacites,
        "api_nature": api_nature,
        "api_cadastre": api_cadastre,
        "sirene": [s.get("properties", {}) for s in sirene_data]
    }



##############################
# Production PV simplifiée
##############################
def get_pvgis_production(lat, lon, tilt, azimuth, peakpower=1.0):
    url = "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc"
    aspect_pvgis = 180.0 - azimuth
    params = {
        "lat": lat,
        "lon": lon,
        "peakpower": peakpower,
        "loss": 14,
        "angle": tilt,
        "aspect": aspect_pvgis,
        "outputformat": "json"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        production_annual = data["outputs"]["totals"]["fixed"]["E_y"]
        return production_annual
    except Exception as e:
        print("Erreur PVGIS:", e)
        return None
def get_elevation_at_point(lat, lon):
    """
    Récupère l'altitude d'un point en utilisant l'API Open-Elevation (gratuite).
    Fallback sur l'API IGN si disponible.
    """
    # Méthode 1: Open-Elevation (API gratuite et fiable)
    try:
        url = "https://api.open-elevation.com/api/v1/lookup"
        params = {
            "locations": f"{lat},{lon}"
        }
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results and len(results) > 0:
                elevation = results[0].get("elevation")
                if elevation is not None:
                    print(f"✅ Altitude Open-Elevation: {elevation}m pour {lat}, {lon}")
                    return round(float(elevation), 2)
    except Exception as e:
        print(f"❌ Erreur Open-Elevation: {e}")
    
    # Méthode 2: API IGN (France uniquement)
    try:
        if 41.0 <= lat <= 51.5 and -5.5 <= lon <= 10.0:  # Approximativement la France
            url = "https://wxs.ign.fr/calcul/alti/rest/elevation.json"
            params = {
                "lon": lon,
                "lat": lat,
                "zonly": True
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                elevations = data.get("elevations", [])
                if elevations and len(elevations) > 0:
                    elevation = elevations[0].get("z")
                    if elevation is not None:
                        print(f"✅ Altitude IGN: {elevation}m pour {lat}, {lon}")
                        return round(float(elevation), 2)
    except Exception as e:
        print(f"❌ Erreur API IGN altitude: {e}")
    
    # Méthode 3: USGS Elevation Point Query Service (backup)
    try:
        url = "https://nationalmap.gov/epqs/pqs.php"
        params = {
            "x": lon,
            "y": lat,
            "units": "Meters",
            "output": "json"
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            result = data.get("USGS_Elevation_Point_Query_Service", {})
            result_data = result.get("Elevation_Query", {})
            elevation = result_data.get("Elevation")
            if elevation is not None and elevation != -1000000:  # -1000000 = pas de données
                print(f"✅ Altitude USGS: {elevation}m pour {lat}, {lon}")
                return round(float(elevation), 2)
    except Exception as e:
        print(f"❌ Erreur USGS: {e}")
    
    print(f"⚠️ Aucune API altitude n'a fonctionné pour {lat}, {lon}")
    return None  # Retourner None pour permettre le fallback à 150m

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
def get_nearest_postes(lat, lon, count=3, radius_deg=0.1):
    postes = get_all_postes(lat, lon, radius_deg=radius_deg)
    return sorted(postes, key=lambda x: x.get("properties", {}).get("distance", float('inf')))[:count]

def get_nearest_ht_postes(lat, lon, count=3, radius_deg=0.5):
    postes = get_all_ht_postes(lat, lon, radius_deg=radius_deg)
    return sorted(postes, key=lambda x: x.get("properties", {}).get("distance", float('inf')))[:count]

def get_nearest_capacites_reseau(lat, lon, count=3, radius_deg=0.1):
    capacites = get_all_capacites_reseau(lat, lon, radius_deg=radius_deg)
    return sorted(capacites, key=lambda x: x.get("properties", {}).get("distance", float('inf')))[:count]

def to_geojson_feature(obj, layer_name=None):
    if not obj:
        return None
    # Si déjà un Feature
    if isinstance(obj, dict) and obj.get("type") == "Feature":
        return obj
    # Si déjà FeatureCollection
    if isinstance(obj, dict) and obj.get("type") == "FeatureCollection":
        return obj
    # Si l’objet contient une géométrie, construis un Feature
    if isinstance(obj, dict) and ("geometry" in obj or "geom" in obj):
        geom = obj.get("geometry") or obj.get("geom")
        properties = {k: v for k, v in obj.items() if k not in ("geometry", "geom")}
        if layer_name:
            properties["_layer"] = layer_name
        return {
            "type": "Feature",
            "geometry": geom,
            "properties": properties
        }
    # Si tu as des coordonnées
    if "coordinates" in obj and "type" in obj:
        return {"type": "Feature", "geometry": obj, "properties": {}}
    return None
def enrich_rpg_with_cadastre_num(rpg_features):
    """
    Pour chaque parcelle RPG (Feature), récupère le numéro cadastral via l'API Cadastre IGN.
    Ajoute le numéro à properties["numero_parcelle"].
    """
    enriched = []
    for feat in rpg_features:
        # Utilise le centroïde pour l'API, ou la géométrie entière
        geom = feat.get("geometry")
        if not geom:
            enriched.append(feat)
            continue
        props = feat.get("properties", {})
        # Préfère un polygone précis
        api_resp = get_api_cadastre_data(geom)
        num_parcelle = None
        # L’API IGN retourne une FeatureCollection, va chercher le numéro
        if api_resp and "features" in api_resp and len(api_resp["features"]) > 0:
            # On prend le premier, mais tu peux faire mieux si plusieurs results
            num_parcelle = api_resp["features"][0]["properties"].get("numero", None)
        props["numero_parcelle"] = num_parcelle or "N/A"
        feat["properties"] = props
        enriched.append(feat)
    return enriched
def synthese_departement(reports):
    """
    Synthèse départementale corrigée pour agréger correctement les données
    """
    print(f"[SYNTHESE_DEPT] Traitement de {len(reports)} rapports communaux")
    
    # Fusionne toutes les parcelles rpg et éleveurs
    all_rpg = []
    all_eleveurs = []
    
    for i, rpt in enumerate(reports):
        print(f"[SYNTHESE_DEPT] Rapport {i+1}: {rpt.get('commune', 'N/A')}")
        
        # Traitement RPG
        fc_rpg = rpt.get("rpg_parcelles", {})
        if fc_rpg and isinstance(fc_rpg, dict) and "features" in fc_rpg:
            features_rpg = fc_rpg.get("features", [])
            all_rpg.extend(features_rpg)
            print(f"[SYNTHESE_DEPT]   - Ajout {len(features_rpg)} parcelles RPG")
        else:
            print(f"[SYNTHESE_DEPT]   - Aucune parcelle RPG")
            
        # Traitement éleveurs  
        fc_e = rpt.get("eleveurs", {})
        if fc_e and isinstance(fc_e, dict) and "features" in fc_e:
            features_eleveurs = fc_e.get("features", [])
            all_eleveurs.extend(features_eleveurs)
            print(f"[SYNTHESE_DEPT]   - Ajout {len(features_eleveurs)} éleveurs")
        else:
            print(f"[SYNTHESE_DEPT]   - Aucun éleveur")

    print(f"[SYNTHESE_DEPT] Total agrégé: {len(all_rpg)} parcelles RPG, {len(all_eleveurs)} éleveurs")

    # Fonction de tri par distance améliorée
    def get_dist(feat):
        props = feat.get("properties", {})
        # Cherche dans tous les champs de distance possibles
        for key in ["distance_bt", "distance_au_poste", "distance_hta", "min_distance_bt_m", "min_distance_hta_m"]:
            v = props.get(key)
            if v is not None and isinstance(v, (int, float)) and v > 0:
                return v
        return 999999

    # Déduplication des parcelles RPG (évite les doublons entre communes)
    def deduplicate_parcelles(features):
        seen = set()
        unique = []
        for p in features:
            props = p.get("properties", {})
            # Clé unique basée sur plusieurs identifiants
            key = (
                props.get("ID_PARCEL") or props.get("id"),
                props.get("code_com"),
                props.get("com_abs"),
                props.get("section") or props.get("cadastre_section"),
                props.get("numero") or props.get("cadastre_numero")
            )
            if key not in seen:
                seen.add(key)
                unique.append(p)
        return unique

    # Déduplication et tri
    all_rpg_unique = deduplicate_parcelles(all_rpg)
    all_rpg_sorted = sorted(all_rpg_unique, key=get_dist)
    top50 = all_rpg_sorted[:50]

    print(f"[SYNTHESE_DEPT] Après déduplication: {len(all_rpg_unique)} parcelles uniques")
    print(f"[SYNTHESE_DEPT] TOP 50 sélectionné")

    # Enrichissement cadastre avec gestion d'erreur
    try:
        top50 = enrich_rpg_with_cadastre_num(top50)
        print(f"[SYNTHESE_DEPT] Enrichissement cadastre terminé")
    except Exception as e:
        print(f"[SYNTHESE_DEPT] Erreur enrichissement cadastre: {e}")

    synthese_result = {
        "nb_agriculteurs": len(all_eleveurs),  # Correspond au template
        "nb_parcelles": len(all_rpg_unique),   # Correspond au template
        "total_eleveurs": len(all_eleveurs),   # Backup pour la compatibilité
        "total_parcelles": len(all_rpg_unique), # Backup pour la compatibilité
        "top50_parcelles": top50,             # Backup pour la compatibilité
        "top50": top50                        # Correspond au template
    }
    
    print(f"[SYNTHESE_DEPT] Synthèse finale: {synthese_result['total_eleveurs']} éleveurs, {synthese_result['total_parcelles']} parcelles")
    
    return synthese_result
def get_commune_mairie(nom_commune):
    url = f"https://geo.api.gouv.fr/communes?nom={quote_plus(nom_commune)}&fields=mairie"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 200:
        info = resp.json()
        if info and "mairie" in info[0]:
            return info[0]["mairie"]  # Peut contenir adresse, nom, etc.
    return None

##############################
# Profil d'élévation
##############################
@app.route("/altitude_point", methods=["GET"])
def altitude_point_route():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)

    if lat is None or lon is None:
        return jsonify({"error": "Paramètres lat et lon requis."}), 400

    altitude = get_elevation_at_point(lat, lon)
    if altitude is None:
        return jsonify({"error": "Impossible d'obtenir l'altitude."}), 500

    return jsonify({"lat": lat, "lon": lon, "altitude_m": altitude})

@app.route("/elevation_profile", methods=["GET"])
def elevation_profile_route():
    start_lat = request.args.get("start_lat", type=float)
    start_lon = request.args.get("start_lon", type=float)
    end_lat = request.args.get("end_lat", type=float)
    end_lon = request.args.get("end_lon", type=float)
    n = request.args.get("n", 50, type=int)
    if None in [start_lat, start_lon, end_lat, end_lon]:
        return jsonify({"error": "Paramètres manquants."}), 400

    points = []
    for i in range(n):
        t = i / (n - 1)
        lat_point = start_lat + t * (end_lat - start_lat)
        lon_point = start_lon + t * (end_lon - start_lon)
        points.append((lat_point, lon_point))

    profile = get_elevation_profile(points)
    if profile is None:
        return jsonify({"error": "Erreur API Elevation"}), 500
    return jsonify(profile)


from shapely.geometry import shape, MultiPolygon
def build_simple_map(
    lat, lon, address,
    parcelle_props, parcelles_data,
    postes_data, plu_info,
    api_cadastre=None
):
    """
    Version simplifiée de build_map qui affiche seulement :
    - Le numéro de parcelle cadastrale avec son contour
    - La zone PLU avec documents liés
    - La distance au poste le plus proche
    """
    import folium
    from folium.plugins import Draw, MeasureControl
    from pyproj import Transformer
    from shapely.geometry import shape, mapping
    
    # Initialisation des données
    if parcelles_data is None or not isinstance(parcelles_data, dict):
        parcelles_data = {"type": "FeatureCollection", "features": []}
    if postes_data is None:
        postes_data = []
    if plu_info is None:
        plu_info = []
    if api_cadastre is None or not isinstance(api_cadastre, dict):
        api_cadastre = {"type": "FeatureCollection", "features": []}
    
    # Création de la carte avec zoom étendu
    map_obj = folium.Map(location=[lat, lon], zoom_start=16, tiles=None, max_zoom=22)
    
    # Fonds de carte
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite",
        overlay=False, control=True, show=True, max_zoom=22
    ).add_to(map_obj)
    folium.TileLayer("OpenStreetMap", name="Fond OSM", overlay=False, control=True, show=False, max_zoom=19).add_to(map_obj)
    
    # Outils
    from folium.plugins import Draw
    Draw(export=True).add_to(map_obj)
    MeasureControl(position="topright").add_to(map_obj)
    
    # 1. PARCELLE CADASTRALE CENTRALE avec numéro
    cadastre_group = folium.FeatureGroup(name="Parcelle Cadastrale", show=True)
    
    # Parcelle principale (WFS)
    if parcelle_props and parcelle_props.get("geometry"):
        section = parcelle_props.get("section", "")
        numero = parcelle_props.get("numero", "")
        code_com = parcelle_props.get("code_com", "")
        numero_parcelle = f"{code_com}{section}{numero}" if all([code_com, section, numero]) else "N/A"
        
        tooltip_html = f"<b>Parcelle:</b> {numero_parcelle}<br>"
        tooltip_html += f"<b>Section:</b> {section}<br>"
        tooltip_html += f"<b>Numéro:</b> {numero}<br>"
        tooltip_html += f"<b>Commune:</b> {code_com}"
        
        folium.GeoJson(
            parcelle_props["geometry"], 
            style_function=lambda _: {"color": "red", "weight": 3, "fillColor": "yellow", "fillOpacity": 0.3},
            tooltip=folium.Tooltip(tooltip_html)
        ).add_to(cadastre_group)
        
        # Ajout du numéro de parcelle au centre
        try:
            centroid = shape(parcelle_props["geometry"]).centroid
            folium.Marker(
                [centroid.y, centroid.x],
                popup=f"<b>Parcelle {numero_parcelle}</b>",
                icon=folium.DivIcon(
                    html=f'<div style="font-size: 12px; font-weight: bold; color: red; text-shadow: 1px 1px 1px white;">{numero_parcelle}</div>',
                    icon_size=(100, 20),
                    icon_anchor=(50, 10)
                )
            ).add_to(cadastre_group)
        except Exception:
            pass
    
    # Parcelles API Cadastre IGN
    if api_cadastre.get("features"):
        for feat in api_cadastre["features"]:
            props = feat.get("properties", {})
            numero = props.get("numero", "N/A")
            section = props.get("section", "N/A")
            
            tooltip_html = f"<b>Parcelle:</b> {section}{numero}<br>"
            for k, v in props.items():
                if k not in ["numero", "section"]:
                    tooltip_html += f"<b>{k}:</b> {v}<br>"
            
            folium.GeoJson(
                feat["geometry"],
                style_function=lambda _: {"color": "blue", "weight": 2, "fillColor": "lightblue", "fillOpacity": 0.2},
                tooltip=folium.Tooltip(tooltip_html)
            ).add_to(cadastre_group)
    
    map_obj.add_child(cadastre_group)
    
    # 2. POSTE LE PLUS PROCHE
    if postes_data:
        # Trouve le poste le plus proche
        closest_poste = min(postes_data, key=lambda p: p.get("distance", float('inf')))
        
        poste_group = folium.FeatureGroup(name="Poste le plus proche", show=True)
        
        props = closest_poste.get("properties", {})
        dist_m = closest_poste.get("distance")
        
        try:
            coords = closest_poste["geometry"]["coordinates"]
            lat_p, lon_p = coords[1], coords[0]
            
            popup_html = f"<b>Poste le plus proche</b><br>"
            if dist_m is not None:
                popup_html += f"<b>Distance:</b> {dist_m:.1f} m<br>"
            else:
                popup_html += f"<b>Distance:</b> Non calculée<br>"
            
            for k, v in props.items():
                popup_html += f"<b>{k}:</b> {v}<br>"
            
            streetview_url = f"https://www.google.com/maps?q=&layer=c&cbll={lat_p},{lon_p}"
            popup_html += f"<a href='{streetview_url}' target='_blank'>Voir sur Street View</a>"
            
            folium.Marker(
                [lat_p, lon_p],
                popup=popup_html,
                icon=folium.Icon(color="green", icon="flash", prefix="fa")
            ).add_to(poste_group)
            
            # Cercle autour du poste
            folium.Circle(
                [lat_p, lon_p],
                radius=50,
                color="green",
                fill=True,
                fill_opacity=0.2
            ).add_to(poste_group)
            
            # Ligne entre la parcelle et le poste
            line_popup = f"Distance: {dist_m:.1f} m" if dist_m is not None else "Distance: Non calculée"
            folium.PolyLine(
                locations=[[lat, lon], [lat_p, lon_p]],
                color="green",
                weight=3,
                opacity=0.8,
                popup=line_popup
            ).add_to(poste_group)
            
        except Exception:
            pass
        
        map_obj.add_child(poste_group)
    
    # 3. ZONE PLU avec documents
    if plu_info:
        plu_group = folium.FeatureGroup(name="Zone PLU", show=True)
        
        for item in plu_info:
            if item.get("geometry"):
                typeref = item.get("typeref", "N/A")
                insee = item.get("insee", "N/A")
                files = item.get("files", [])
                archive_url = item.get("archive_url", "")
                
                popup_html = f"""
                <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 350px;">
                  <div style="color: #0000FF; border-bottom: 2px solid #0000FF; padding-bottom: 5px; margin-bottom: 10px; font-weight: bold;">
                    🏗️ Zone d'Urbanisme
                  </div>
                  <table style="width: 100%; border-collapse: collapse;">
                """
                
                # Type de zone avec description explicite
                zone_description = ""
                if typeref.upper().startswith('U'):
                    zone_description = "Zone urbaine - Constructions autorisées"
                elif typeref.upper().startswith('AU'):
                    zone_description = "Zone à urbaniser - Développement futur"
                elif typeref.upper().startswith('A'):
                    zone_description = "Zone agricole - Protection des terres"
                elif typeref.upper().startswith('N'):
                    zone_description = "Zone naturelle - Protection environnementale"
                else:
                    zone_description = "Zone spécifique"
                
                popup_html += f"""
                  <tr><td style="font-weight: bold; padding: 3px;">🎯 Type de zone:</td><td style="padding: 3px;"><strong>{typeref}</strong></td></tr>
                  <tr><td style="font-weight: bold; padding: 3px;">📋 Classification:</td><td style="padding: 3px;">{zone_description}</td></tr>
                  <tr><td style="font-weight: bold; padding: 3px;">🏘️ Code INSEE:</td><td style="padding: 3px;">{insee}</td></tr>
                """
                
                # Potentiel selon le type
                if typeref.upper().startswith('U') or typeref.upper().startswith('AU'):
                    popup_html += f"<tr><td style='font-weight: bold; padding: 3px;'>💡 Potentiel:</td><td style='padding: 3px;'>Zone favorable pour projets urbains et énergétiques</td></tr>"
                elif typeref.upper().startswith('A'):
                    popup_html += f"<tr><td style='font-weight: bold; padding: 3px;'>🌾 Potentiel:</td><td style='padding: 3px;'>Zone adaptée pour l'agrivoltaïsme et projets agricoles</td></tr>"
                elif typeref.upper().startswith('N'):
                    popup_html += f"<tr><td style='font-weight: bold; padding: 3px;'>🌿 Contraintes:</td><td style='padding: 3px;'>Zone protégée - Réglementation stricte</td></tr>"
                
                if files:
                    popup_html += f"<tr><td style='font-weight: bold; padding: 3px;'>📄 Documents:</td><td style='padding: 3px;'>"
                    for file in files[:3]:  # Limite à 3 documents
                        popup_html += f"• {file}<br>"
                    if len(files) > 3:
                        popup_html += f"... et {len(files) - 3} autres<br>"
                    popup_html += "</td></tr>"
                
                popup_html += "</table>"
                
                if archive_url:
                    popup_html += f"""
                    <div style="margin-top: 10px; text-align: center;">
                      <a href='{archive_url}' target='_blank' style="background: #007bff; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; font-size: 0.9em;">
                        📋 Consulter le PLU
                      </a>
                    </div>
                    """
                
                popup_html += f"""
                  <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #eee; font-size: 0.85em; color: #666;">
                    💼 <strong>Source :</strong> Géoportail de l'Urbanisme (GPU)
                  </div>
                </div>
                """
                
                folium.GeoJson(
                    item.get("geometry"),
                    style_function=lambda _: {"color": "red", "weight": 2, "fillColor": "lavender", "fillOpacity": 0.4},
                    tooltip=f"Zone PLU - {typeref}",
                    popup=safe_folium_popup(popup_html, max_width=300)
                ).add_to(plu_group)
        
        map_obj.add_child(plu_group)
    
    # Marqueur du point de recherche
    folium.Marker(
        [lat, lon],
        popup=f"<b>Point de recherche</b><br>{address}",
        icon=folium.Icon(color="red", icon="search", prefix="fa")
    ).add_to(map_obj)
    
    # Contrôle des couches - AJOUT EXPLICITE AVEC PARAMÈTRES
    # Placeholders HTA pour la version simple
    try:
        hta_a_simple = folium.FeatureGroup(name="HTA Aériennes", show=True)
        hta_s_simple = folium.FeatureGroup(name="HTA Souterraines", show=True)
        map_obj.add_child(hta_a_simple)
        map_obj.add_child(hta_s_simple)
    except Exception as _e:
        print('[HTA][build_simple_map] Impossible d\'ajouter placeholders:', _e)

    layer_control = folium.LayerControl(position='topright', collapsed=False)
    layer_control.add_to(map_obj)
    print("🎛️ [LAYER CONTROL] Ajouté en position topright, non collapsed")
    
    # Zoom approprié
    map_obj.fit_bounds([[lat-0.002, lon-0.002], [lat+0.002, lon+0.002]])
    
    # Injection dynamique HTA si non déjà présent (version simple)
    try:
        from folium import Element
        helper_js_hta_simple = """
        <script>(function(){
        if (window.__HTA_DYNAMIC_SIMPLE__) { return; }
        window.__HTA_DYNAMIC_SIMPLE__ = true;
        var mapInstance = (function(){ for (var k in window){ if(window[k] instanceof L.Map){ return window[k]; } } return null; })();
        if(!mapInstance){ console.warn('[HTA][simple] map introuvable'); return; }
        function detectDepartmentFromContext(){ 
            // Cette fonction n'est plus utilisée - on utilise maintenant les coordonnées de la commune directement
            console.log('[HTA] detectDepartmentFromContext() désactivée - utilisation des coordonnées de commune');
            return null; 
        }
        function styleHta(f){ var t=f&&f.properties&&f.properties.type_ligne; if(t==='aerienne') return {color:'#ff6600',weight:2,opacity:0.9}; if(t==='souterraine') return {color:'#0055ff',weight:2,opacity:0.8,dashArray:'4,4'}; return {color:'#888',weight:1}; }
        function popupHta(f,l){ var p=(f&&f.properties)||{}; l.bindPopup('<strong>Ligne HTA '+(p.type_ligne||'?')+'</strong><br/>'+'Commune: '+(p.nom_commune||'–')+'<br/>'+'Département: '+(p.code_departement||'–')); }
    async function loadHtaDynamic(){ 
        console.log('[HTA][simple] start loadHtaDynamic pour commune recherchée'); 
        try { 
            const center = mapInstance.getCenter();
            const bounds = mapInstance.getBounds();
            const bbox = bounds.getSouth() + ',' + bounds.getWest() + ',' + bounds.getNorth() + ',' + bounds.getEast();
            console.log('[HTA][simple] Recherche pour commune - bbox:', bbox);
            const url='/api/hta-lignes?bbox='+encodeURIComponent(bbox)+'&include_aerienne=true&include_souterraine=true&limit=800'; 
            const r=await fetch(url); 
            if(!r.ok) throw new Error('HTTP '+r.status); 
            const data=await r.json(); 
            function findGroup(name){ 
                var g=null; 
                mapInstance.eachLayer(function(l){ 
                    if(l && l.options && l.options.name===name){ g=l; } 
                }); 
                return g; 
            } 
            var grpA=findGroup('HTA Aériennes')||L.featureGroup(); 
            var grpS=findGroup('HTA Souterraines')||L.featureGroup(); 
            try{ grpA.clearLayers(); }catch(_){ } 
            try{ grpS.clearLayers(); }catch(_){ } 
            if(!mapInstance.hasLayer(grpA)) grpA.addTo(mapInstance); 
            if(!mapInstance.hasLayer(grpS)) grpS.addTo(mapInstance); 
            if(data.aerienne&&data.aerienne.features){ 
                L.geoJSON(data.aerienne,{style:styleHta,onEachFeature:popupHta}).addTo(grpA); 
            } 
            if(data.souterraine&&data.souterraine.features){ 
                L.geoJSON(data.souterraine,{style:styleHta,onEachFeature:popupHta}).addTo(grpS); 
            } 
            var countA=data.aerienne&&data.aerienne.features?data.aerienne.features.length:0; 
            var countS=data.souterraine&&data.souterraine.features?data.souterraine.features.length:0; 
            var total=countA+countS; 
            function updateLabels(){ 
                var lc=document.querySelector('.leaflet-control-layers-overlays'); 
                if(!lc) return; 
                lc.querySelectorAll('label').forEach(function(l){ 
                    var t=l.textContent.trim(); 
                    if(t.startsWith('HTA Aériennes')){ 
                        l.childNodes.forEach(n=>{ if(n.nodeType===3) n.textContent='HTA Aériennes ('+countA+')'; }); 
                    } 
                    if(t.startsWith('HTA Souterraines')){ 
                        l.childNodes.forEach(n=>{ if(n.nodeType===3) n.textContent='HTA Souterraines ('+countS+')'; }); 
                    } 
                }); 
            }
            updateLabels();
            
            // Marquer comme chargé
            if (!window.htaLoadState) window.htaLoadState = { aerienne: false, souterraine: false };
            window.htaLoadState.aerienne = true;
            window.htaLoadState.souterraine = true;
            
            window.refreshHtaLayersSimple=function(){ 
                try{ mapInstance.removeLayer(grpA); }catch(_){ } 
                try{ mapInstance.removeLayer(grpS); }catch(_){ } 
                setTimeout(loadHtaDynamic,50); 
            };
            console.log('[HTA][simple] OK', data.summary); 
        } catch(e){ 
            console.error('[HTA][simple] erreur', e); 
        } 
    }
    
    // Initialisation des placeholders avec chargement à la demande
    function initHtaPlaceholdersSimple() {
        console.log('[HTA][simple] Initialisation placeholders avec chargement à la demande');
        
        function findGroup(name){ 
            var g=null; 
            mapInstance.eachLayer(function(l){ 
                if(l && l.options && l.options.name===name){ g=l; } 
            }); 
            return g; 
        } 
        
        var grpA=findGroup('HTA Aériennes')||L.featureGroup(); 
        var grpS=findGroup('HTA Souterraines')||L.featureGroup(); 
        
        if(!mapInstance.hasLayer(grpA)) grpA.addTo(mapInstance); 
        if(!mapInstance.hasLayer(grpS)) grpS.addTo(mapInstance);
        
        // Ajouter les handlers de clic
        setTimeout(function() {
            var lc=document.querySelector('.leaflet-control-layers-overlays'); 
            if(!lc) return;
            
            lc.querySelectorAll('label').forEach(function(l){ 
                var t=l.textContent.trim(); 
                var input = l.querySelector('input[type="checkbox"]');
                
                if(input && t.startsWith('HTA Aériennes') && !t.includes('(')){
                    l.childNodes.forEach(n=>{ if(n.nodeType===3) n.textContent='HTA Aériennes (cliquez pour charger)'; });
                    input.addEventListener('change', function(e) {
                        if (e.target.checked && (!window.htaLoadState || !window.htaLoadState.aerienne)) {
                            loadHtaDynamic();
                        }
                    });
                } 
                if(input && t.startsWith('HTA Souterraines') && !t.includes('(')){
                    l.childNodes.forEach(n=>{ if(n.nodeType===3) n.textContent='HTA Souterraines (cliquez pour charger)'; });
                    input.addEventListener('change', function(e) {
                        if (e.target.checked && (!window.htaLoadState || !window.htaLoadState.souterraine)) {
                            loadHtaDynamic();
                        }
                    });
                }
            }); 
        }, 300);
    }
    
    setTimeout(initHtaPlaceholdersSimple, 200);
        })();</script>
        """
        map_obj.get_root().html.add_child(Element(helper_js_hta_simple))
    except Exception as _e:
        try: print('[HTA] Injection build_simple_map échouée', _e)
        except Exception: pass

    return map_obj

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
    ppri_data=None,  # Ajout PPRI
    hta_lignes_data=None  # Ajout lignes HTA
):
    import folium
    from folium.plugins import Draw, MeasureControl, MarkerCluster
    from pyproj import Transformer
    from shapely.geometry import shape, mapping, MultiPolygon
    from utils import decode_rpg_feature, bbox_to_polygon, shp_transform

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
    if hta_lignes_data is None:
        hta_lignes_data = {"aerienne": {"features": []}, "souterraine": {"features": []}}
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
    
    # === CRÉATION DE LA CARTE avec zoom adapté (16 pour parcelle) ===
    map_obj = folium.Map(location=[lat, lon], zoom_start=16, tiles=None, max_zoom=22)
    
    # Ajouter les couches de base
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite",
        overlay=False, control=True, show=True, max_zoom=22
    ).add_to(map_obj)
    folium.TileLayer("OpenStreetMap", name="Fond OSM", overlay=False, control=True, show=False, max_zoom=19).add_to(map_obj)
    
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
    cadastre_group = folium.FeatureGroup(name="Cadastre (WFS)", show=False)
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

    # Note: Cadastre (API IGN) supprimé car parasite - les données cadastrales sont déjà dans la couche principale

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
        
        # Bouton KPI pour poste BT
        import json
        props_json_escaped = json.dumps(props).replace("'", "\\'").replace('"', '\\"')
        popup += f"""<br><button onclick="var data = {{action: 'sendToKPI', lat: {lat_p}, lon: {lon_p}, type: 'poste_bt', properties: JSON.parse('{props_json_escaped}')}}; window.top.postMessage(data, '*');" 
            style="background: #28a745; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: bold; margin-top: 8px; width: 100%;">
            📤 Envoyer vers KPI
        </button>"""
        
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
        
        # Bouton KPI pour poste HTA
        import json
        props_json_escaped = json.dumps(props).replace("'", "\\'").replace('"', '\\"')
        popup += f"""<br><button onclick="var data = {{action: 'sendToKPI', lat: {lat_p}, lon: {lon_p}, type: 'poste_hta', properties: JSON.parse('{props_json_escaped}')}}; window.top.postMessage(data, '*');" 
            style="background: #28a745; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: bold; margin-top: 8px; width: 100%;">
            📤 Envoyer vers KPI
        </button>"""
        
        streetview_url = f"https://www.google.com/maps?q=&layer=c&cbll={lat_p},{lon_p}"
        popup += f"<br><a href='{streetview_url}' target='_blank'>Voir sur Street View</a>"
        folium.Marker([lat_p, lon_p], popup=popup, icon=folium.Icon(color="orange", icon="bolt", prefix="fa")).add_to(hta_group)
    map_obj.add_child(hta_group)

    # --- Éleveurs avec liens hypertexte ---
    eleveurs_group = folium.FeatureGroup(name="Éleveurs", show=True)
    if eleveurs_data:  # Vérification que eleveurs_data n'est pas None
        for eleveur in eleveurs_data:
            props = eleveur.get("properties", {})
            geom = eleveur.get("geometry")
            
            if not geom or geom.get("type") != "Point":
                continue
                
            try:
                coords = geom["coordinates"]
                lat_e, lon_e = coords[1], coords[0]
            except Exception:
                continue
            
            # Construction du popup enrichi
            nom = props.get("nomUniteLe", "") or props.get("denominati", "") or "Éleveur"
            commune = props.get("libelleCom", "")
            siret = props.get("siret", "")
            
            popup_html = f"<b>🐄 Éleveur</b><br>"
            popup_html += f"<b>Nom:</b> {nom}<br>"
            if commune:
                popup_html += f"<b>Commune:</b> {commune}<br>"
            if siret:
                popup_html += f"<b>SIRET:</b> {siret}<br>"
                
            # Liens externes: SIRENE (annuaire-entreprises) et Pages Jaunes
            lien_annuaire = props.get("lien_annuaire")
            lien_entreprise = props.get("lien_entreprise")

            # Fallback si non préparés en amont (encodage sécurisé)
            if not lien_annuaire:
                try:
                    from urllib.parse import quote_plus
                    nom_mix = (props.get("nomUniteLe", "").strip() + " " + props.get("denominati", "").strip()).strip()
                    ville_mix = (props.get("libelleCom", "") or "").strip()
                    nom_url = quote_plus(nom_mix) if nom_mix else ""
                    ville_url = quote_plus(ville_mix) if ville_mix else ""
                    lien_annuaire = (
                        f"https://www.pagesjaunes.fr/recherche/{ville_url}/{nom_url}"
                        if (nom_url or ville_url) else None
                    )
                except Exception:
                    lien_annuaire = None
            if not lien_entreprise and siret:
                lien_entreprise = f"https://annuaire-entreprises.data.gouv.fr/etablissement/{siret}"

            links_html = []
            if lien_entreprise:
                links_html.append(
                    f"<a href=\"{lien_entreprise}\" target=\"_blank\" style=\"color:#1474fa; text-decoration:none; padding:4px 8px; background:#f0f8ff; border-radius:4px; display:inline-block; margin-right:6px;\">📇 Annuaire Entreprises (SIRENE)</a>"
                )
            if lien_annuaire:
                links_html.append(
                    f"<a href=\"{lien_annuaire}\" target=\"_blank\" style=\"color:#ff8c00; text-decoration:none; padding:4px 8px; background:#fff8dc; border-radius:4px; display:inline-block; margin-right:6px;\">📞 Pages Jaunes</a>"
                )

            # Lien Street View
            streetview_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat_e},{lon_e}"
            links_html.append(
                f"<a href=\"{streetview_url}\" target=\"_blank\" style=\"color:#444; text-decoration:none; padding:4px 8px; background:#f7f7f7; border-radius:4px; display:inline-block;\">📍 Street View</a>"
            )

            if links_html:
                popup_html += "<br>" + " ".join(links_html)

            # Nettoyer le HTML pour éviter les erreurs JavaScript
            popup_html = sanitize_popup_html(popup_html)

            # Utiliser un IFrame pour éviter les problèmes de quotes dans le JS généré par Folium
            try:
                iframe = folium.IFrame(html=popup_html, width=300, height=150)
                popup_obj = safe_folium_popup(iframe, max_width=300)
            except Exception:
                popup_obj = safe_folium_popup(popup_html, max_width=300)

            folium.Marker(
                [lat_e, lon_e],
                popup=popup_obj,
                icon=folium.Icon(color="green", icon="home", prefix="fa")
            ).add_to(eleveurs_group)
    
    map_obj.add_child(eleveurs_group)

    # PLU
    plu_group = folium.FeatureGroup(name="PLU", show=True)
    for item in plu_info:
        if item.get("geometry"):
            # Créer une pop-up améliorée pour les zones PLU
            props = item.get("properties", {})
            typeref = props.get("typezone", props.get("type", "N/A"))
            insee = props.get("insee", "N/A")
            commune = props.get("commune", props.get("nom_commune", ""))
            
            popup_html = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 300px;">
              <div style="color: #0000FF; border-bottom: 2px solid #0000FF; padding-bottom: 5px; margin-bottom: 10px; font-weight: bold;">
                🏗️ Zone d'Urbanisme
              </div>
              <table style="width: 100%; border-collapse: collapse;">
            """
            
            # Type de zone avec description explicite
            zone_description = ""
            if typeref.upper().startswith('U'):
                zone_description = "Zone urbaine - Constructions autorisées"
            elif typeref.upper().startswith('AU'):
                zone_description = "Zone à urbaniser - Développement futur"
            elif typeref.upper().startswith('A'):
                zone_description = "Zone agricole - Protection des terres"
            elif typeref.upper().startswith('N'):
                zone_description = "Zone naturelle - Protection environnementale"
            else:
                zone_description = "Zone spécifique"
            
            popup_html += f"""
              <tr><td style="font-weight: bold; padding: 3px;">🎯 Type de zone:</td><td style="padding: 3px;"><strong>{typeref}</strong></td></tr>
              <tr><td style="font-weight: bold; padding: 3px;">📋 Classification:</td><td style="padding: 3px;">{zone_description}</td></tr>
            """
            
            if commune:
                popup_html += f'<tr><td style="font-weight: bold; padding: 3px;">🏘️ Commune:</td><td style="padding: 3px;">{commune}</td></tr>'
            
            if insee != "N/A":
                popup_html += f'<tr><td style="font-weight: bold; padding: 3px;">🏘️ Code INSEE:</td><td style="padding: 3px;">{insee}</td></tr>'
            
            # Potentiel selon le type
            if typeref.upper().startswith('U') or typeref.upper().startswith('AU'):
                popup_html += f"<tr><td style='font-weight: bold; padding: 3px;'>💡 Potentiel:</td><td style='padding: 3px;'>Zone favorable pour projets urbains et énergétiques</td></tr>"
            elif typeref.upper().startswith('A'):
                popup_html += f"<tr><td style='font-weight: bold; padding: 3px;'>🌾 Potentiel:</td><td style='padding: 3px;'>Zone adaptée pour l'agrivoltaïsme et projets agricoles</td></tr>"
            elif typeref.upper().startswith('N'):
                popup_html += f"<tr><td style='font-weight: bold; padding: 3px;'>🌿 Contraintes:</td><td style='padding: 3px;'>Zone protégée - Réglementation stricte</td></tr>"
            
            popup_html += f"""
              </table>
              <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #eee; font-size: 0.85em; color: #666;">
                💼 <strong>Source :</strong> Géoportail de l'Urbanisme (GPU)
              </div>
            </div>
            """
            
            folium.GeoJson(
                item.get("geometry"), 
                style_function=lambda _: {"color": "red", "weight": 2, "fillColor": "lavender", "fillOpacity": 0.4},
                tooltip=f"Zone PLU - {typeref}",
                popup=safe_folium_popup(popup_html, max_width=350)
            ).add_to(plu_group)
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
        # print(f"🎨 [COUCHE {name}] Affichage {len(data)} éléments en couleur {color}")  # Optimisé pour performance
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
                    # Création d'un tooltip enrichi pour parkings, friches et toitures avec références cadastrales
                    props = f.get("properties", {})
                    tooltip_lines = []
                    
                    # Calculer le centroïde pour le lien Google Street View (pour parkings, friches et toitures)
                    street_view_link = ""
                    pages_jaunes_link = ""
                    
                    if name in ["Parkings", "Friches", "Potentiel Solaire"]:
                        try:
                            from shapely.geometry import shape
                            geom_shape = shape(geom)
                            centroid = geom_shape.centroid
                            lat_center = centroid.y
                            lon_center = centroid.x
                            
                            street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat_center},{lon_center}"
                            
                            # Emoji différent selon le type
                            if name == "Potentiel Solaire":  # Toitures
                                icon = "🏠"
                                text = "Voir la toiture"
                                
                                # Lien Pages Jaunes spécifique pour les toitures
                                adresse = props.get("adresse")
                                if adresse and adresse != "Adresse non trouvée" and adresse != "Erreur géocodage":
                                    from urllib.parse import quote_plus
                                    adresse_encoded = quote_plus(adresse)
                                    pages_jaunes_url = f"https://www.pagesjaunes.fr/annuaire/chercherlespros?quoiqui=&ou={adresse_encoded}&univers=pagesjaunes&idOu="
                                    pages_jaunes_link = f"<br><a href='{pages_jaunes_url}' target='_blank' style='color: #ff8c00; text-decoration: none; padding: 4px 8px; background: #fff8dc; border-radius: 4px; display: inline-block;'>📞 Pages Jaunes</a>"
                                
                            elif name == "Parkings":
                                icon = "🅿️"
                                text = "Voir le parking"
                                
                                # Lien Pages Jaunes spécifique pour les parkings
                                adresse = props.get("adresse")
                                if adresse and adresse != "Adresse non trouvée" and adresse != "Erreur géocodage":
                                    from urllib.parse import quote_plus
                                    adresse_encoded = quote_plus(adresse)
                                    pages_jaunes_url = f"https://www.pagesjaunes.fr/annuaire/chercherlespros?quoiqui=parking&ou={adresse_encoded}&univers=pagesjaunes&idOu="
                                    pages_jaunes_link = f"<br><a href='{pages_jaunes_url}' target='_blank' style='color: #ff8c00; text-decoration: none; padding: 4px 8px; background: #fff8dc; border-radius: 4px; display: inline-block;'>📞 Pages Jaunes - Parkings</a>"
                                
                            else:  # Friches
                                icon = "🌾"
                                text = "Voir la friche"
                                
                                # Lien Pages Jaunes spécifique pour les friches
                                adresse = props.get("adresse")
                                if adresse and adresse != "Adresse non trouvée" and adresse != "Erreur géocodage":
                                    from urllib.parse import quote_plus
                                    adresse_encoded = quote_plus(adresse)
                                    pages_jaunes_url = f"https://www.pagesjaunes.fr/annuaire/chercherlespros?quoiqui=terrain&ou={adresse_encoded}&univers=pagesjaunes&idOu="
                                    pages_jaunes_link = f"<br><a href='{pages_jaunes_url}' target='_blank' style='color: #ff8c00; text-decoration: none; padding: 4px 8px; background: #fff8dc; border-radius: 4px; display: inline-block;'>📞 Pages Jaunes - Terrains</a>"
                                
                            street_view_link = f"<br><br><a href='{street_view_url}' target='_blank' style='color: #1474fa; text-decoration: none; padding: 4px 8px; background: #f0f8ff; border-radius: 4px; display: inline-block;'>{icon} {text}</a>"
                        except Exception as e:
                            print(f"[DEBUG] Impossible de calculer le centroïde pour {name}: {e}")
                    
                    # Debug : Vérifier si on a des références cadastrales
                    if name in ["Parkings", "Friches", "Potentiel Solaire"]:
                        cadastre_refs = props.get("parcelles_cadastrales", [])
                        # print(f"🏛️ [DEBUG {name}] Feature avec {len(cadastre_refs)} références cadastrales")  # Optimisé pour production multi-user
                    
                    # Traitement uniforme et complet pour toutes les couches avec adresses et liens
                    if name in ["Potentiel Solaire", "Parkings", "Friches"]:
                        # 📍 ADRESSE (priorité 1) - Essayer plusieurs clés possibles
                        adresse = props.get("adresse") or props.get("addr:full") or props.get("addr:street")
                        if adresse and adresse not in ["Adresse non trouvée", "Erreur géocodage", "", "N/A"]:
                            emoji = "🏠" if name == "Potentiel Solaire" else ("🅿️" if name == "Parkings" else "🌾")
                            tooltip_lines.append(f"<b>{emoji} Adresse:</b> {adresse}")
                            
                            # Informations complémentaires sur l'adresse
                            distance = props.get("adresse_distance") or props.get("addr_distance")
                            score = props.get("adresse_score") or props.get("addr_score")
                            if distance is not None:
                                tooltip_lines.append(f"<b>📏 Distance adresse:</b> {distance}m")
                            if score:
                                tooltip_lines.append(f"<b>🎯 Précision:</b> {score:.1f}")
                        
                        # Essayer aussi d'autres champs d'adresse OSM
                        ville = props.get("ville") or props.get("addr:city") or props.get("addr:municipality")
                        code_postal = props.get("code_postal") or props.get("addr:postcode")
                        if ville and ville not in ["", "N/A"]:
                            tooltip_lines.append(f"<b>�️ Ville:</b> {ville}")
                        if code_postal and code_postal not in ["", "N/A"]:
                            tooltip_lines.append(f"<b>📮 Code postal:</b> {code_postal}")
                        
                        # 📐 SURFACE (priorité 2)
                        surface = props.get("area") or props.get("surface") or props.get("surface_m2")
                        if surface:
                            type_label = "toiture" if name == "Potentiel Solaire" else ("parking" if name == "Parkings" else "terrain")
                            emoji = "🏠" if name == "Potentiel Solaire" else ("🅿️" if name == "Parkings" else "🌾")
                            tooltip_lines.append(f"<b>{emoji} Surface {type_label}:</b> {surface:.0f} m²")
                        
                        # 🏛️ RÉFÉRENCES CADASTRALES (priorité 3)
                        refs_cadastrales = props.get("parcelles_cadastrales", [])
                        if refs_cadastrales and isinstance(refs_cadastrales, list):
                            tooltip_lines.append(f"<b>🏛️ Parcelles cadastrales ({len(refs_cadastrales)}):</b>")
                            for ref in refs_cadastrales[:5]:  # Limite à 5 pour éviter les pop-ups trop longs
                                if isinstance(ref, dict):
                                    ref_complete = ref.get('reference_complete', 'N/A')
                                    tooltip_lines.append(f"  • {ref_complete}")
                                else:
                                    tooltip_lines.append(f"  • {str(ref)}")
                            if len(refs_cadastrales) > 5:
                                tooltip_lines.append(f"  ... et {len(refs_cadastrales)-5} autres")
                        
                        # ⚡ DISTANCES AUX POSTES (priorité 4)
                        dist_bt = props.get("distance_poste_bt") or props.get("min_poste_distance_m")
                        dist_hta = props.get("distance_poste_hta")
                        if dist_bt is not None:
                            tooltip_lines.append(f"<b>⚡ Distance poste BT:</b> {dist_bt:.0f}m" if isinstance(dist_bt, (int, float)) else f"<b>⚡ Distance poste BT:</b> {dist_bt}")
                        if dist_hta is not None:
                            tooltip_lines.append(f"<b>⚡ Distance poste HTA:</b> {dist_hta:.0f}m" if isinstance(dist_hta, (int, float)) else f"<b>⚡ Distance poste HTA:</b> {dist_hta}")
                        
                        # 📊 AUTRES PROPRIÉTÉS IMPORTANTES
                        excluded_keys = {
                            "adresse", "addr:full", "addr:street", "addr:city", "addr:municipality", "addr:postcode",
                            "adresse_distance", "addr_distance", "adresse_score", "addr_score", 
                            "ville", "code_postal", "code_commune", "area", "surface", "surface_m2",
                            "parcelles_cadastrales", "nb_parcelles_cadastrales", 
                            "distance_poste_bt", "distance_poste_hta", "min_poste_distance_m"
                        }
                        
                        for k, v in props.items():
                            if k not in excluded_keys and v not in [None, "", "N/A", "Erreur géocodage", "Adresse non trouvée"]:
                                # Formatage spécial pour certaines clés importantes
                                if "distance" in k.lower():
                                    tooltip_lines.append(f"<b>📏 {k}:</b> {v:.0f}m" if isinstance(v, (int, float)) else f"<b>📏 {k}:</b> {v}")
                                elif k in ["puissance", "power", "watt"]:
                                    tooltip_lines.append(f"<b>⚡ {k}:</b> {v}")
                                elif k in ["type", "category", "amenity"]:
                                    tooltip_lines.append(f"<b>🏷️ {k}:</b> {v}")
                                else:
                                    tooltip_lines.append(f"<b>{k}:</b> {v}")
                    
                    else:
                        # Traitement standard pour les autres couches
                        for k, v in props.items():
                            if k == "parcelles_cadastrales" and isinstance(v, list) and v:
                                tooltip_lines.append(f"<b>🏛️ Références cadastrales ({len(v)}):</b>")
                                for ref in v[:5]:
                                    if isinstance(ref, dict):
                                        ref_complete = ref.get('reference_complete', 'N/A')
                                        tooltip_lines.append(f"  • {ref_complete}")
                                    else:
                                        tooltip_lines.append(f"  • {str(ref)}")
                                if len(v) > 5:
                                    tooltip_lines.append(f"  ... et {len(v)-5} autres")
                            elif k not in ["parcelles_cadastrales", "nb_parcelles_cadastrales"] and v not in [None, "", "N/A"]:
                                tooltip_lines.append(f"<b>{k}:</b> {v}")
                    
                    tooltip_text = "<br>".join(tooltip_lines)
                    
                    # Bouton KPI pour toitures, parkings, friches
                    kpi_button = ""
                    if name in ["Parkings", "Friches", "Potentiel Solaire"]:
                        try:
                            from shapely.geometry import shape
                            geom_shape = shape(geom)
                            centroid = geom_shape.centroid
                            lat_center = centroid.y
                            lon_center = centroid.x
                            
                            # Déterminer le type pour KPI
                            kpi_type = "toiture" if name == "Potentiel Solaire" else name.lower().rstrip('s')
                            
                            # Échapper les propriétés pour JavaScript
                            import json
                            props_json_escaped = json.dumps(props).replace("'", "\\'").replace('"', '\\"')
                            
                            # Utiliser postMessage avec une chaîne JSON échappée
                            kpi_button = f"""<br><button onclick="var data = {{action: 'sendToKPI', lat: {lat_center}, lon: {lon_center}, type: '{kpi_type}', properties: JSON.parse('{props_json_escaped}')}}; window.top.postMessage(data, '*');" 
                                style="background: #28a745; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: bold; margin-top: 8px; width: 100%;">
                                📤 Envoyer vers KPI
                            </button>"""
                        except Exception as e:
                            print(f"[DEBUG] Erreur création bouton KPI: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # Créer le popup avec les liens Street View et Pages Jaunes si disponibles
                    popup_content = tooltip_text + kpi_button + street_view_link + pages_jaunes_link
                    
                    # SOLUTION SIMPLE ET ROBUSTE: Utiliser les fonctions prédéfinies
                    if name == "Parkings":
                        style_func = style_parkings
                    elif name == "Friches":
                        style_func = style_friches
                    elif name == "Potentiel Solaire":
                        style_func = style_solaire
                    else:  # ZAER
                        style_func = style_zaer
                    
                    folium.GeoJson(
                        geom, 
                        style_function=style_func,
                        tooltip=tooltip_text,
                        popup=safe_folium_popup(popup_content, max_width=400) if name in ["Parkings", "Friches", "Potentiel Solaire"] else None
                    ).add_to(group)
                except Exception as e:
                    print(f"[ERROR] Exception while adding {name} geometry: {e}\nGeom: {geom}")
            else:
                print(f"[DEBUG] Invalid {name} geometry: type={geom.get('type') if geom else None}, coords={geom.get('coordinates') if geom else None}")
        map_obj.add_child(group)

    # Couche cadastre des parkings/friches sélectionnés
    parking_friches_cadastre = []
    
    # Collecter toutes les références cadastrales des parkings
    for parking in parkings_data:
        parcelles = parking.get("properties", {}).get("parcelles_cadastrales", [])
        for parcelle in parcelles:
            if parcelle.get("reference_complete"):
                parking_friches_cadastre.append({
                    "reference": parcelle.get("reference_complete"),
                    "type": "parking",
                    "source_surface": parking.get("properties", {}).get("surface_m2", "N/A"),
                    "source_distance": parking.get("properties", {}).get("min_poste_distance_m", "N/A")
                })
    
    # Collecter toutes les références cadastrales des friches
    for friche in friches_data:
        parcelles = friche.get("properties", {}).get("parcelles_cadastrales", [])
        for parcelle in parcelles:
            if parcelle.get("reference_complete"):
                parking_friches_cadastre.append({
                    "reference": parcelle.get("reference_complete"),
                    "type": "friche", 
                    "source_surface": friche.get("properties", {}).get("surface_m2", "N/A"),
                    "source_distance": friche.get("properties", {}).get("min_poste_distance_m", "N/A")
                })
    
    if parking_friches_cadastre:
        cadastre_filtered_group = folium.FeatureGroup(name="🏛️ Cadastre Parkings/Friches", show=False)
        
        # Compter les références par type
        parking_refs = [r for r in parking_friches_cadastre if r["type"] == "parking"]
        friche_refs = [r for r in parking_friches_cadastre if r["type"] == "friche"]
        
        # Créer un marker informatif
        info_popup = f"""
        <b>📊 Références Cadastrales Collectées</b><br>
        🅿️ Parkings: {len(parking_refs)} références<br>
        🏭 Friches: {len(friche_refs)} références<br>
        📋 Total: {len(parking_friches_cadastre)} références<br><br>
        
        <b>Exemples de références:</b><br>
        """
        
        for i, ref_info in enumerate(parking_friches_cadastre):
            icon = "🅿️" if ref_info["type"] == "parking" else "🏭"
            info_popup += f"{icon} {ref_info['reference']}<br>"
        
        # Ajouter un marker central avec la liste
        folium.Marker(
            [lat, lon],
            popup=safe_folium_popup(info_popup, max_width=400),
            icon=folium.Icon(color="purple", icon="list", prefix="fa")
        ).add_to(cadastre_filtered_group)
        
        map_obj.add_child(cadastre_filtered_group)
        # print(f"[CARTE] Couche cadastre: {len(parking_friches_cadastre)} références affichées")  # Optimisé pour performance

    # RPG
    rpg_group = folium.FeatureGroup(name="RPG", show=True)
    valid_rpg_count = 0
    invalid_rpg_count = 0
    # Optimisé pour performance
    # print(f"🌾 [BUILD_MAP_RPG] Traitement de {len(rpg_data)} parcelles RPG")
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
            dist_bt = props.get("min_distance_bt_m", props.get("distance_bt", "N/A"))
            dist_hta = props.get("min_distance_hta_m", props.get("distance_hta", "N/A"))
            dist_hta_aerial = props.get("min_distance_hta_aerial_m", props.get("distance_ligne_aerienne", "N/A"))
            dist_hta_underground = props.get("min_distance_hta_underground_m", props.get("distance_ligne_souterraine", "N/A"))
            popup_html = (
                f"<b>ID Parcelle :</b> {id_parcel}<br>"
                f"<b>Surface :</b> {surf_ha}<br>"
                f"<b>Code culture :</b> {code_cultu}<br>"
                f"<b>Culture :</b> {culture_label}<br>"
                f"<b>Distance au poste BT :</b> {dist_bt} m<br>"
                f"<b>Distance au poste HTA :</b> {dist_hta} m<br>"
                f"<b>Distance ligne HTA aérienne :</b> {dist_hta_aerial} m<br>"
                f"<b>Distance ligne HTA souterraine :</b> {dist_hta_underground} m"
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
                    valid_rpg_count += 1
                    # print(f"[DEBUG] Parcelle RPG {idx} ajoutée avec succès")  # Optimisé pour performance
                except Exception as e:
                    # print(f"[ERROR] Exception while adding RPG geometry: {e}\nGeom: {geom}")  # Optimisé pour performance
                    invalid_rpg_count += 1
            else:
                # print(f"[DEBUG] Invalid RPG geometry: type={geom.get('type') if geom else None}, coords={geom.get('coordinates') if geom else None}")  # Optimisé pour performance
                invalid_rpg_count += 1
        except Exception as e:
            # print(f"❌ [ERROR] Exception while processing RPG feature at index {idx}: {e}\nFeature: {repr(feat)[:200]}")  # Optimisé pour performance
            invalid_rpg_count += 1
    
    # print(f"🌾 [BUILD_MAP_RPG] RÉSUMÉ: {valid_rpg_count} parcelles valides, {invalid_rpg_count} invalides")  # Optimisé pour performance
    # print(f"🌾 [DEBUG_GROUP] Nombre d'enfants dans rpg_group avant ajout: {len(rpg_group._children)}")  # Optimisé pour performance
    map_obj.add_child(rpg_group)
    # print(f"🌾 [DEBUG_MAP] Nombre total d'enfants dans map_obj après ajout: {len(map_obj._children)}")  # Optimisé pour performance

    # Capacités réseau HTA
    caps_group = folium.FeatureGroup(name="Postes HTA (Capacités)", show=True)
    for item in capacites_reseau:
        props = item.get('properties', {})
        
        # ⚡ POPUP FORMATÉ POUR CAPACITÉS RÉSEAU
        popup_content = f"<div style='max-width: 350px; font-family: Arial, sans-serif;'>"
        popup_content += f"<h5 style='color: #6f42c1; margin-bottom: 15px;'><i class='fa fa-bolt'></i> ⚡ Poste HTA</h5>"
        
        # Informations principales
        if 'nom_station' in props or 'nom_poste' in props or 'libelle' in props:
            nom = props.get('nom_station') or props.get('nom_poste') or props.get('libelle', 'Poste HTA')
            popup_content += f"<p><strong>📍 Nom:</strong> {nom}</p>"
        
        if 'capacite_accueil' in props:
            capacite = props['capacite_accueil']
            popup_content += f"<p><strong>⚡ Capacité d'accueil:</strong> <span style='color: #28a745; font-weight: bold;'>{capacite} MW</span></p>"
        
        if 'tension' in props:
            tension = props['tension']
            popup_content += f"<p><strong>🔌 Tension:</strong> {tension} kV</p>"
        
        if 'commune' in props:
            commune = props['commune']
            popup_content += f"<p><strong>🏘️ Commune:</strong> {commune}</p>"
        
        if 'gestionnaire' in props:
            gestionnaire = props['gestionnaire']
            popup_content += f"<p><strong>🏢 Gestionnaire:</strong> {gestionnaire}</p>"
        
        # Distance si disponible
        if 'distance_m' in props:
            distance = props['distance_m']
            if distance < 1000:
                popup_content += f"<p><strong>📏 Distance:</strong> <span style='color: #007bff;'>{distance:.0f}m</span></p>"
            else:
                popup_content += f"<p><strong>📏 Distance:</strong> <span style='color: #007bff;'>{distance/1000:.1f}km</span></p>"
        
        # Informations techniques supplémentaires
        tech_info = []
        for key, value in props.items():
            if key not in ['nom_station', 'nom_poste', 'libelle', 'capacite_accueil', 'tension', 'commune', 'gestionnaire', 'distance_m', 'geometry']:
                if str(value).strip() and str(value) not in ['None', 'null', '']:
                    tech_info.append(f"<small><strong>{key.replace('_', ' ').title()}:</strong> {value}</small>")
        
        if tech_info:
            popup_content += "<hr style='margin: 10px 0;'>"
            popup_content += "<h6 style='color: #6c757d;'>Informations techniques:</h6>"
            popup_content += "<br>".join(tech_info[:5])  # Limiter à 5 infos techniques
        
        popup_content += "</div>"
        
        # Attention : parfois la géométrie peut être un dict ou un shapely, adapte si besoin
        try:
            lon_c, lat_c = shape(item['geometry']).centroid.coords[0]
        except Exception:
            coords = item.get("geometry", {}).get("coordinates", [0, 0])
            lon_c, lat_c = coords[0], coords[1]
        folium.Marker([lat_c, lon_c], popup=safe_folium_popup(popup_content, max_width=400), icon=folium.Icon(color="purple", icon="flash")).add_to(caps_group)
    map_obj.add_child(caps_group)

    # Sirene - Couche décochée par défaut pour éviter l'encombrement
    sir_group = folium.FeatureGroup(name="Entreprises Sirene", show=False)
    for feat in sirene_data:
        if feat.get('geometry', {}).get('type') == 'Point':
            lon_s, lat_s = feat['geometry']['coordinates']
            folium.Marker([lat_s, lon_s], popup="<br>".join(f"{k}: {v}" for k, v in feat['properties'].items()), icon=folium.Icon(color="darkred", icon="building")).add_to(sir_group)
    map_obj.add_child(sir_group)
    # Défini bbox_poly avant d'utiliser get_all_gpu_data(bbox_poly)
    delta = 5.0 / 111.0  # 5km en degrés ~
    bbox_poly = bbox_to_polygon(lon, lat, delta)
    # GPU Urbanisme : Ajout dynamique de toutes les couches du GPU urbanisme (zone-urba, prescription-surf, ...)
    # GPU Urbanisme : Ajout dynamique de toutes les couches du GPU urbanisme (zone-urba, prescription-surf, ...)
    # GPU Urbanisme : Ajout dynamique de toutes les couches du GPU urbanisme (zone-urba, prescription-surf, ...)
    COLOR_GPU = {
        "zone-urba": "#0055FF",
        "prescription-surf": "#FF9900",
        "prescription-lin": "#44AA44",
        "prescription-pct": "#AA44AA",
        "secteur-cc": "#666666",
        # Ajoute ici d'autres types si besoin
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
                        popup=safe_folium_popup(popup_html, max_width=400)
                    ).add_to(group)
                except Exception as e:
                    print(f"[ERROR] Exception while adding GPU geometry for {ep}: {e}\nGeom: {geom}")
            else:
                print(f"[DEBUG] Invalid GPU geometry for {ep}: type={geom.get('type') if geom else None}, coords={geom.get('coordinates') if geom else None}")

        map_obj.add_child(group)

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
                    popup=safe_folium_popup(popup_content, max_width=400),
                    tooltip=f"🌿 {props.get('NOM', 'Zone naturelle')} ({type_protection})"
                ).add_to(nat_grp)
        
        map_obj.add_child(nat_grp)

    # --- Placeholders HTA (affichés immédiatement dans LayerControl) ---
    try:
        hta_a_fg = folium.FeatureGroup(name="HTA Aériennes", show=True)
        hta_s_fg = folium.FeatureGroup(name="HTA Souterraines", show=True)
        map_obj.add_child(hta_a_fg)
        map_obj.add_child(hta_s_fg)
        
        # --- Ajout des lignes HTA réelles si disponibles ---
        if hta_lignes_data:
            # Lignes aériennes
            aerienne_features = hta_lignes_data.get("aerienne", {}).get("features", [])
            for feature in aerienne_features:
                try:
                    if feature.get("geometry") and feature["geometry"]["type"] == "LineString":
                        coords = feature["geometry"]["coordinates"]
                        # Convertir en format Leaflet [lat, lon]
                        leaflet_coords = [[coord[1], coord[0]] for coord in coords]
                        
                        props = feature.get("properties", {})
                        popup_content = f"<b>🔌 Ligne HTA Aérienne</b><br>"
                        popup_content += f"Commune: {props.get('nom_commune', 'N/A')}<br>"
                        popup_content += f"Département: {props.get('nom_departement', 'N/A')} ({props.get('code_departement', 'N/A')})<br>"
                        popup_content += f"Région: {props.get('nom_region', 'N/A')}<br>"
                        popup_content += f"Source: {props.get('source', 'ENEDIS')}"
                        
                        folium.PolyLine(
                            locations=leaflet_coords,
                            color='red',
                            weight=3,
                            opacity=0.8,
                            popup=safe_folium_popup(popup_content, max_width=300),
                            tooltip="Ligne HTA Aérienne"
                        ).add_to(hta_a_fg)
                except Exception as e:
                    # Optimisé pour performance
                    # print(f"[HTA] Erreur ajout ligne aérienne: {e}")
                    pass
            
            # Lignes souterraines
            souterraine_features = hta_lignes_data.get("souterraine", {}).get("features", [])
            for feature in souterraine_features:
                try:
                    if feature.get("geometry") and feature["geometry"]["type"] == "LineString":
                        coords = feature["geometry"]["coordinates"]
                        # Convertir en format Leaflet [lat, lon]
                        leaflet_coords = [[coord[1], coord[0]] for coord in coords]
                        
                        props = feature.get("properties", {})
                        popup_content = f"<b>🔌 Ligne HTA Souterraine</b><br>"
                        popup_content += f"Commune: {props.get('nom_commune', 'N/A')}<br>"
                        popup_content += f"Département: {props.get('nom_departement', 'N/A')} ({props.get('code_departement', 'N/A')})<br>"
                        popup_content += f"Région: {props.get('nom_region', 'N/A')}<br>"
                        popup_content += f"Source: {props.get('source', 'ENEDIS')}"
                        
                        folium.PolyLine(
                            locations=leaflet_coords,
                            color='blue',
                            weight=3,
                            opacity=0.8,
                            popup=safe_folium_popup(popup_content, max_width=300),
                            tooltip="Ligne HTA Souterraine"
                        ).add_to(hta_s_fg)
                except Exception as e:
                    # Optimisé pour performance
                    # print(f"[HTA] Erreur ajout ligne souterraine: {e}")
                    pass
            
            # Optimisé pour performance - Ce log causait des dumps massifs de coordonnées
            # print(f"[HTA] Ajouté {len(aerienne_features)} lignes aériennes et {len(souterraine_features)} lignes souterraines")
        
    except Exception as _e:
        # Optimisé pour performance
        # print("[HTA][build_map] Impossible d'ajouter placeholders:", _e)
        pass

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

    from folium import Element
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
    // ──────────────────────────────────────────────────────────────
    // Chargement dynamique Lignes HTA (aériennes / souterraines)
    // ──────────────────────────────────────────────────────────────
    function detectDepartmentFromContext() {
        // Cette fonction n'est plus utilisée pour HTA - on utilise maintenant les coordonnées de la commune directement
        console.log('[HTA] detectDepartmentFromContext() désactivée - utilisation des coordonnées de commune');
        return null;
    }

    function styleHta(f) {
        const t = f && f.properties && f.properties.type_ligne;
        if (t === 'aerienne') return { color: '#ff6600', weight: 2, opacity: 0.9 };
        if (t === 'souterraine') return { color: '#0055ff', weight: 2, opacity: 0.8, dashArray: '4,4' };
        return { color: '#888', weight: 1 };
    }
    function popupHta(f, layer) {
        const p = (f && f.properties) || {};
        layer.bindPopup('<strong>Ligne HTA ' + (p.type_ligne||'?') + '</strong><br/>' +
            'Commune: ' + (p.nom_commune||'–') + '<br/>' +
            'Département: ' + (p.code_departement||'–'));
    }

    async function loadHtaDynamic() {
        try {
            console.log('[HTA] start loadHtaDynamic pour commune recherchée');
            
            // Afficher un message de chargement
            function updateHtaLabels(aerienneText, souterraineText) {
                var lcEl = document.querySelector('.leaflet-control-layers-overlays');
                if (lcEl) {
                    var labels = lcEl.querySelectorAll('label');
                    labels.forEach(function(l) {
                        var t = l.textContent.trim();
                        if (t.startsWith('HTA Aériennes')) {
                            l.childNodes.forEach(function(n){ if(n.nodeType===3){ n.textContent = aerienneText; }});
                        } else if (t.startsWith('HTA Souterraines')) {
                            l.childNodes.forEach(function(n){ if(n.nodeType===3){ n.textContent = souterraineText; }});
                        }
                    });
                }
            }
            
            // Message de chargement
            updateHtaLabels('HTA Aériennes (chargement...)', 'HTA Souterraines (chargement...)');
            
            // Utiliser les coordonnées de la commune recherchée au lieu d'un département
            const center = mapInstance.getCenter();
            const bounds = mapInstance.getBounds();
            const bbox = bounds.getSouth() + ',' + bounds.getWest() + ',' + bounds.getNorth() + ',' + bounds.getEast();
            
            console.log('[HTA] Recherche pour commune - bbox:', bbox);
            const url = '/api/hta-lignes?bbox=' + encodeURIComponent(bbox) + '&include_aerienne=true&include_souterraine=true&limit=800';
            const r = await fetch(url);
            if (!r.ok) throw new Error('HTTP ' + r.status);
            const data = await r.json();
            
            // Vérifier s'il y a des données
            var countA = (data.aerienne && data.aerienne.features) ? data.aerienne.features.length : 0;
            var countS = (data.souterraine && data.souterraine.features) ? data.souterraine.features.length : 0;
            var totalHTA = countA + countS;
            
            console.log('[HTA] Données reçues:', { aerienne: countA, souterraine: countS, total: totalHTA, bbox: bbox });
            
            // Réutiliser les placeholders HTA existants créés côté serveur
            function findGroupByName(name){
                var found = null;
                mapInstance.eachLayer(function(l){
                    if (l && l.options && l.options.name === name) { found = l; }
                });
                return found;
            }
            var grpAerienne = findGroupByName('HTA Aériennes') || L.featureGroup();
            var grpSouterraine = findGroupByName('HTA Souterraines') || L.featureGroup();
            
            // Nettoyer les couches existantes
            try { grpAerienne.clearLayers(); } catch(_){ }
            try { grpSouterraine.clearLayers(); } catch(_){ }
            if (!mapInstance.hasLayer(grpAerienne)) grpAerienne.addTo(mapInstance);
            if (!mapInstance.hasLayer(grpSouterraine)) grpSouterraine.addTo(mapInstance);
            
            // Ajouter les données si disponibles
            if (data.aerienne && data.aerienne.features && data.aerienne.features.length > 0) {
                L.geoJSON(data.aerienne, { style: styleHta, onEachFeature: popupHta }).addTo(grpAerienne);
            }
            if (data.souterraine && data.souterraine.features && data.souterraine.features.length > 0) {
                L.geoJSON(data.souterraine, { style: styleHta, onEachFeature: popupHta }).addTo(grpSouterraine);
            }
            
            // Mettre à jour les labels avec les vrais compteurs ou des messages appropriés
            if (totalHTA === 0) {
                // Aucune donnée HTA trouvée
                updateHtaLabels(
                    'HTA Aériennes (aucune donnée)', 
                    'HTA Souterraines (aucune donnée)'
                );
                console.log('[HTA] Aucune donnée HTA trouvée pour la zone recherchée');
            } else {
                // Données trouvées
                updateHtaLabels(
                    'HTA Aériennes (' + countA + ')', 
                    'HTA Souterraines (' + countS + ')'
                );
                console.log('[HTA] Données HTA chargées avec succès:', totalHTA, 'lignes pour la zone recherchée');
            }

            // Intégrer dans LayerControl existant (ajout dynamique) + mise à jour labels
            function ensureInLayerControl(){
                // Rechercher l'instance de LayerControl
                var lcEl = document.querySelector('.leaflet-control-layers-overlays');
                if (!lcEl) return false;
                // Ajouter entrées si absentes
                function addOverlayOnce(group, labelBase){
                    // Vérifie si déjà présent
                    var exists = Array.from(lcEl.querySelectorAll('span, label')).some(e=>e.textContent && e.textContent.trim().startsWith(labelBase));
                    if (!exists) {
                        // Utilise API Leaflet si possible
                        try { mapInstance.addLayer(group); } catch(_){ }
                        // Insertion DOM bricolée: on laisse Leaflet générer via addOverlay côté Python normalement
                        // Ici on se contente de laisser le groupe actif; sans re-générer le panneau (Leaflet ne reconstruit pas). Option alternative: custom control déjà remplacé.
                        // Fallback DOM: si l'entrée n'apparaît toujours pas, on crée un label manuel
                        setTimeout(function(){
                            var stillMissing = !Array.from(lcEl.querySelectorAll('span, label')).some(e=>e.textContent && e.textContent.trim().startsWith(labelBase));
                            if(stillMissing){
                                try {
                                    var label = document.createElement('label');
                                    label.style.display='block';
                                    var input = document.createElement('input');
                                    input.type='checkbox';
                                    input.checked = true;
                                    input.onchange = function(){ if(this.checked){ mapInstance.addLayer(group); } else { mapInstance.removeLayer(group); } };
                                    var span = document.createElement('span');
                                    span.appendChild(document.createTextNode(labelBase));
                                    label.appendChild(input); label.appendChild(span);
                                    lcEl.appendChild(label);
                                } catch(err){ console.warn('[HTA][fallback] erreur creation label', err); }
                            }
                        },60);
                    }
                }
                addOverlayOnce(grpAerienne, 'HTA Aériennes');
                addOverlayOnce(grpSouterraine, 'HTA Souterraines');
                // Mise à jour/ajout des compteurs dans labels existants
                var labels = lcEl.querySelectorAll('label');
                labels.forEach(function(l){
                    var t = l.textContent.trim();
                    if (t.startsWith('HTA Aériennes')) {
                        l.childNodes.forEach(function(n){ if(n.nodeType===3){ n.textContent = 'HTA Aériennes ('+countA+')'; }});
                    } else if (t.startsWith('HTA Souterraines')) {
                        l.childNodes.forEach(function(n){ if(n.nodeType===3){ n.textContent = 'HTA Souterraines ('+countS+')'; }});
                    }
                });
                return true;
            }
            ensureInLayerControl();

            // NOUVELLE GESTION ÉVÉNEMENTS CLIC - Connecter les clics LayerControl au chargement HTA
            function setupClickHandlers() {
                console.log('[HTA] Configuration des gestionnaires de clic LayerControl');
                
                // Stocker l'état de chargement
                if (!window.htaLoadState) {
                    window.htaLoadState = { aerienne: false, souterraine: false };
                }
                
                // Fonction pour détecter et gérer les clics sur les checkboxes HTA
                function handleLayerControlClick() {
                    setTimeout(function() {
                        var lcEl = document.querySelector('.leaflet-control-layers-overlays');
                        if (!lcEl) return;
                        
                        var labels = lcEl.querySelectorAll('label');
                        labels.forEach(function(label) {
                            var input = label.querySelector('input[type="checkbox"]');
                            var text = label.textContent.trim();
                            
                            if (input && (text.startsWith('HTA Aériennes') || text.startsWith('HTA Souterraines'))) {
                                // Supprimer les anciens listeners pour éviter les doublons
                                input.removeEventListener('change', input._htaHandler);
                                
                                // Créer le nouveau handler
                                input._htaHandler = function(e) {
                                    var isChecked = e.target.checked;
                                    var layerName = text.startsWith('HTA Aériennes') ? 'aerienne' : 'souterraine';
                                    var groupRef = layerName === 'aerienne' ? grpAerienne : grpSouterraine;
                                    
                                    console.log('[HTA] Clic détecté:', layerName, 'checked:', isChecked);
                                    
                                    if (isChecked) {
                                        // Charger les données si pas encore fait
                                        if (!window.htaLoadState[layerName]) {
                                            console.log('[HTA] Premier chargement de', layerName);
                                            loadHtaDynamic(); // Recharger toutes les données HTA
                                            window.htaLoadState[layerName] = true;
                                        } else {
                                            // Réafficher la couche déjà chargée
                                            if (!mapInstance.hasLayer(groupRef)) {
                                                mapInstance.addLayer(groupRef);
                                            }
                                        }
                                    } else {
                                        // Masquer la couche
                                        if (mapInstance.hasLayer(groupRef)) {
                                            mapInstance.removeLayer(groupRef);
                                        }
                                    }
                                };
                                
                                // Attacher le nouveau listener
                                input.addEventListener('change', input._htaHandler);
                                console.log('[HTA] Handler configuré pour:', text);
                            }
                        });
                    }, 100); // Délai pour s'assurer que le LayerControl est bien rendu
                }
                
                // Appeler une première fois
                handleLayerControlClick();
                
                // Observer les changements dans le LayerControl au cas où il se regenere
                var observer = new MutationObserver(function(mutations) {
                    mutations.forEach(function(mutation) {
                        if (mutation.type === 'childList') {
                            handleLayerControlClick();
                        }
                    });
                });
                
                var lcContainer = document.querySelector('.leaflet-control-layers');
                if (lcContainer) {
                    observer.observe(lcContainer, { childList: true, subtree: true });
                }
            }
            
            // Configurer les handlers après un délai pour s'assurer que tout est rendu
            setTimeout(setupClickHandlers, 200);

            // Expose un rafraîchissement global
            window.refreshHtaLayers = function(){
                try { mapInstance.removeLayer(grpAerienne); } catch(_){ }
                try { mapInstance.removeLayer(grpSouterraine); } catch(_){ }
                setTimeout(loadHtaDynamic, 50);
            };
            // Ajouter un hotkey (R) pour refresh HTA (optionnel)
            window.addEventListener('keydown', function(ev){ if(ev.key==='R' && ev.altKey){ window.refreshHtaLayers(); } });
            console.log('[HTA] intégrées LayerControl', {a:countA,s:countS,total:totalHTA});
            console.log('[HTA] dynamique OK', data.summary);
        } catch(e) {
            console.error('[HTA] dynamique erreur', e);
        }
    }
    
    // MODIFICATION: Chargement à la demande plutôt qu'automatique
    // Initialiser d'abord les placeholders vides, le chargement se fera au clic
    function initHtaPlaceholders() {
        console.log('[HTA] Initialisation des placeholders vides');
        
        // Créer les groupes vides s'ils n'existent pas
        var grpAerienne = findGroupByName('HTA Aériennes') || L.featureGroup();
        var grpSouterraine = findGroupByName('HTA Souterraines') || L.featureGroup();
        
        // S'assurer qu'ils sont dans le LayerControl mais vides
        if (!mapInstance.hasLayer(grpAerienne)) grpAerienne.addTo(mapInstance);
        if (!mapInstance.hasLayer(grpSouterraine)) grpSouterraine.addTo(mapInstance);
        
        // Mettre à jour les labels avec (0) initialement
        setTimeout(function() {
            var lcEl = document.querySelector('.leaflet-control-layers-overlays');
            if (lcEl) {
                var labels = lcEl.querySelectorAll('label');
                labels.forEach(function(l) {
                    var t = l.textContent.trim();
                    if (t.startsWith('HTA Aériennes') && !t.includes('(')) {
                        l.childNodes.forEach(function(n){ if(n.nodeType===3){ n.textContent = 'HTA Aériennes (cliquez pour charger)'; }});
                    } else if (t.startsWith('HTA Souterraines') && !t.includes('(')) {
                        l.childNodes.forEach(function(n){ if(n.nodeType===3){ n.textContent = 'HTA Souterraines (cliquez pour charger)'; }});
                    }
                });
            }
        }, 300);
        
        // Configurer les handlers de clic immédiatement
        setTimeout(function() {
            var lcEl = document.querySelector('.leaflet-control-layers-overlays');
            if (lcEl) {
                var labels = lcEl.querySelectorAll('label');
                labels.forEach(function(label) {
                    var input = label.querySelector('input[type="checkbox"]');
                    var text = label.textContent.trim();
                    
                    if (input && (text.startsWith('HTA Aériennes') || text.startsWith('HTA Souterraines'))) {
                        input.addEventListener('change', function(e) {
                            if (e.target.checked) {
                                console.log('[HTA] Chargement déclenché pour:', text);
                                loadHtaDynamic(); // Charger les données à la demande
                            }
                        });
                    }
                });
            }
        }, 400);
    }
    
    // Utiliser l'initialisation des placeholders au lieu du chargement automatique
    setTimeout(initHtaPlaceholders, 200);
    
    // Fonction helper pour trouver les groupes par nom
    function findGroupByName(name){
        var found = null;
        mapInstance.eachLayer(function(l){
            if (l && l.options && l.options.name === name) { found = l; }
        });
        return found;
    }
    })();
    </script>
    """
    map_obj.get_root().html.add_child(Element(helper_js))

    map_obj.fit_bounds(bounds)
    if not mode_light:
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
            <b style="color: #d63031;">📍 Localisation</b><br>
            <span style="color: #2d3436;">{address}</span><br>
            <small style="color: #636e72;">Lat: {lat:.6f}, Lon: {lon:.6f}</small>
        </div>
        """
        folium.Marker(
            [lat, lon], 
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color="red", icon="map-marker", prefix="fa")
        ).add_to(map_obj)
    # Ajout d'un paramètre save_to_disk (par défaut True)
    if getattr(map_obj, '_no_save', False):
        print("💡 Carte non sauvegardée sur disque (mode _no_save)")
    else:
        # Ajouter timestamp pour éviter le cache
        import time
        timestamp = int(time.time())
        save_map_html(map_obj, f"cartes_{timestamp}.html")
    return map_obj
# Endpoint d'administration pour purger toutes les cartes
@app.route("/purge_cartes", methods=["POST"])
def purge_cartes():
    import os
    cartes_dir = os.path.join(app.root_path, "static", "cartes")
    count = 0
    if os.path.exists(cartes_dir):
        for f in os.listdir(cartes_dir):
            if f.endswith('.html'):
                try:
                    os.remove(os.path.join(cartes_dir, f))
                    count += 1
                except Exception as e:
                    print(f"Erreur suppression {f}: {e}")
    return {"purged": count}

def save_map_to_cache(map_obj, search_data=None):
    # Réactivation du cache mémoire : on stocke le HTML de la carte générée
    last_map_params["html"] = map_obj._repr_html_()
    
    # Sauvegarder aussi les données de recherche pour les réutiliser dans le zoom
    if search_data:
        last_map_params["search_data"] = search_data
        print("✅ Cache mémoire des cartes activé (HTML + données en mémoire)")
    else:
        print("✅ Cache mémoire des cartes activé (HTML en mémoire)")



########################################
# Routes
########################################

@app.route("/generated_map")
def generated_map():
    """
    Renvoie l'HTML de la carte Folium.
    1. S'il existe une carte générée par une recherche (last_map_params['html']),
    on renvoie cette version.
    2. Sinon on produit une carte par défaut (Satellite centré sur la France).
    3. Si des paramètres de zoom sont fournis (lat, lng, zoom), centre la carte sur ces coordonnées.
    """
    from flask import request
    import folium
    
    # Récupérer les paramètres de zoom depuis l'URL
    zoom_lat = request.args.get('lat', type=float)
    zoom_lng = request.args.get('lng', type=float)
    zoom_level = request.args.get('zoom', type=int, default=17)
    marker_name = request.args.get('name', 'Point de zoom')
    
    html = last_map_params.get("html")

    # --- Cas spécial : zoom demandé avec coordonnées ---
    if zoom_lat and zoom_lng:
        # Récupérer les données de la dernière recherche pour les afficher aussi
        search_data = last_map_params.get("search_data", {})
        
        # Créer une carte centrée sur les coordonnées demandées
        map_obj = folium.Map(
            location=[zoom_lat, zoom_lng],
            zoom_start=zoom_level,
            tiles=None
        )
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri World Imagery",
            name="Satellite",
            overlay=False,
            control=True,
            show=True
        ).add_to(map_obj)

        folium.TileLayer(
            "OpenStreetMap",
            name="Fond OSM",
            overlay=False,
            control=True,
            show=False
        ).add_to(map_obj)

        # Ajouter les données de la recherche si disponibles
        if search_data:
            try:
                # Reconstruire la carte avec toutes les données en utilisant la fonction existante
                map_obj = build_map(
                    zoom_lat, zoom_lng, marker_name,
                    search_data.get('parcelle', {}),
                    search_data.get('parcelles', {}),
                    search_data.get('postes_bt', []),
                    search_data.get('postes_hta', []),
                    search_data.get('plu', []),
                    search_data.get('parkings', {}).get('features', []),
                    search_data.get('friches', {}).get('features', []),
                    search_data.get('toitures', {}).get('features', []),
                    search_data.get('zaer', []),
                    search_data.get('rpg', []),
                    search_data.get('sirene', []),
                    0.5,  # search_radius
                    0.01,  # ht_radius_deg
                    api_cadastre=search_data.get('api_cadastre'),
                    api_nature=search_data.get('api_nature'),
                    api_urbanisme=search_data.get('api_urbanisme'),
                    eleveurs_data=search_data.get('eleveurs', []),
                    capacites_reseau=search_data.get('capacites_reseau'),
                    ppri_data=search_data.get('ppri_data', [])
                )
                print(f"[DEBUG] Carte de zoom reconstruite avec toutes les données")
            except Exception as e:
                print(f"[DEBUG] Erreur reconstruction carte avec données: {e}")
                # Fallback : carte simple avec marqueur seulement

        # Ajouter un marqueur sur le point demandé
        folium.Marker(
            [zoom_lat, zoom_lng],
            popup=f"<b>{marker_name}</b><br>Lat: {zoom_lat:.6f}<br>Lng: {zoom_lng:.6f}",
            tooltip=marker_name,
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(map_obj)

        folium.LayerControl().add_to(map_obj)
        html = map_obj._repr_html_()

    # --- Corriger le DOCTYPE pour toute carte existante aussi ---
    elif html and not html.strip().startswith('<!DOCTYPE'):
        # Ajouter le DOCTYPE HTML5 si manquant
        if '<html' in html:
            html = '<!DOCTYPE html>\n' + html
        else:
            # Si pas de balise html, wrapper complètement
            html = f'<!DOCTYPE html>\n<html><head><meta charset="UTF-8"></head><body>{html}</body></html>'
        
        # S'assurer que le HTML a les bonnes balises meta pour éviter Quirks Mode
        if 'charset' not in html.lower():
            html = html.replace('<head>', '<head>\n<meta charset="UTF-8">')
        
        # Mettre à jour la carte corrigée dans le cache
        last_map_params["html"] = html

    # --- Cas : aucune recherche encore faite ---
    elif not html:
        # Carte par défaut
        map_obj = folium.Map(
            location=[46.603354, 1.888334],   # centre France
            zoom_start=6,
            tiles=None
        )
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri World Imagery",
            name="Satellite",
            overlay=False,
            control=True,
            show=True          # active par défaut
        ).add_to(map_obj)

        folium.TileLayer(
            "OpenStreetMap",
            name="Fond OSM",
            overlay=False,
            control=True,
            show=False
        ).add_to(map_obj)

        folium.LayerControl().add_to(map_obj)
        html = map_obj._repr_html_()

    # --- Corriger le DOCTYPE pour éviter le mode Quirks ---
    if html and not html.strip().startswith('<!DOCTYPE'):
        # Ajouter le DOCTYPE HTML5 si manquant
        if '<html' in html:
            html = '<!DOCTYPE html>\n' + html
        else:
            # Si pas de balise html, wrapper complètement
            html = f'<!DOCTYPE html>\n<html><head><meta charset="UTF-8"></head><body>{html}</body></html>'
    
    # --- S'assurer que le HTML a les bonnes balises meta pour éviter Quirks Mode ---
    if 'charset' not in html.lower():
        html = html.replace('<head>', '<head>\n<meta charset="UTF-8">')

    # --- On renvoie toujours un objet Response ---
    resp = make_response(html)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp
from flask import Flask, Response


from flask import url_for, redirect

# Import HTA integration (diagnostic)
try:
    from enedis_integration import get_lignes_hta
except Exception as _e_imp:
    print('[HTA][import] Impossible d\'importer get_lignes_hta:', _e_imp)

@app.route("/commune_search_sse")
def commune_search_sse():
    """
    Diffuse en temps réel des logs de progression lors d'une recherche par commune,
    via Server-Sent Events (SSE). À la fin, envoie un évènement 'redirect' vers le
    rapport complet HTML afin de ne pas dupliquer la génération.

    Utilisation côté client: EventSource('/commune_search_sse?...')
    """
    from flask import request as flask_request
    from urllib.parse import quote_plus
    import json as _json
    
    print(f"🚨 [DEBUG_SSE] /commune_search_sse appelée")
    print(f"🚨 [DEBUG_SSE] Args: {dict(flask_request.args)}")

    def sse_format(event: str | None, data: str):
        chunks = []
        if event:
            chunks.append(f"event: {event}")
        for line in data.splitlines() or [""]:
            chunks.append(f"data: {line}")
        return "\n".join(chunks) + "\n\n"

    @stream_with_context
    def event_stream():
        # Récupération des paramètres minimaux - Version robuste
        try:
            commune = flask_request.args.get("commune", "").strip()
        except:
            commune = ""
            
        if not commune:
            yield sse_format("error", "Veuillez fournir une commune.")
            return

        # Transmettre quelques filtres utiles (optionnels)
        try:
            filter_rpg       = flask_request.args.get("filter_rpg", "true").lower() == "true"
            filter_parkings  = flask_request.args.get("filter_parkings", "false").lower() == "true"
            filter_friches   = flask_request.args.get("filter_friches", "false").lower() == "true"
            filter_toitures  = flask_request.args.get("filter_toitures", "false").lower() == "true"
            filter_by_dist   = flask_request.args.get("filter_by_distance", "false").lower() == "true"
        except:
            # Valeurs par défaut en cas d'erreur
            filter_rpg = True
            filter_parkings = False
            filter_friches = False
            filter_toitures = False
            filter_by_dist = False

        try:
            yield sse_format(None, f"🔎 Démarrage analyse pour: {commune}")
            yield sse_format(None, "⏳ Récupération du contour de la commune…")

            # Vérifie accès au contour pour feedback utilisateur
            resp = requests.get(
                f"https://geo.api.gouv.fr/communes?nom={quote_plus(commune)}&fields=centre,contour",
                timeout=12
            )
            if resp.status_code != 200:
                yield sse_format("error", f"Erreur Geo API Gouv: {resp.status_code}")
                return
            infos = resp.json() or []
            if not infos or not infos[0].get("contour"):
                yield sse_format("error", "Contour de la commune introuvable.")
                return
            centre = infos[0].get("centre", {}).get("coordinates", [None, None])
            yield sse_format(None, f"✅ Contour récupéré (centre: lat={centre[1]}, lon={centre[0]})")

            # Feedback sur filtres sélectionnés
            selected = []
            if filter_rpg:      selected.append("RPG")
            if filter_parkings: selected.append("Parkings")
            if filter_friches:  selected.append("Friches")
            if filter_toitures: selected.append("Toitures")
            if selected:
                yield sse_format(None, "🧰 Couches activées: " + ", ".join(selected))
            if filter_by_dist:
                yield sse_format(None, "📏 Filtrage par distance aux postes activé")

            # Étapes principales (indicatives, la génération réelle est faite sur l'URL de rapport)
            yield sse_format(None, "📡 Préparation de la génération du rapport complet…")
            yield sse_format(None, "🗺️ La carte et les analyses détaillées seront générées…")

            # Fin: ne pas rediriger automatiquement. Le rapport sera généré
            # uniquement via le bouton "Générer rapport commune".
            yield sse_format(None, "✅ Analyse terminée. Utilisez le bouton 'Générer rapport commune' pour créer le rapport.")
            yield sse_format("done", "done")
        except Exception as e:
            safe_print(f"❌ [SSE COMMUNE] Erreur: {e}")
            yield sse_format("error", f"Erreur inattendue: {e}")

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Connection": "keep-alive",
        # Autorise le SSE depuis même origine
        "X-Accel-Buffering": "no",
    }
    return Response(event_stream(), headers=headers)

@app.route("/search_by_commune", methods=["GET", "POST"])
def search_by_commune():
    import uuid
    call_id = str(uuid.uuid4())[:8]
    # #  print("="  # Optimisé pour performance*80)  # Optimisé pour performance
    # print(f"🚨🚨🚨 DEBUT SEARCH_BY_COMMUNE #{call_id} - PROTECTION RENFORCÉE 🚨🚨🚨")  # Optimisé pour performance
    # #  print("="  # Optimisé pour performance*80)  # Optimisé pour performance
    
    import requests
    import json
    from urllib.parse import quote_plus
    from flask import request as flask_request
    from shapely.geometry import shape, Point
    from shapely.ops import transform as shp_transform
    from pyproj import Transformer
    import hashlib
    import time
    import traceback
    
    # Affichage de la stack trace pour voir d'où vient l'appel
    # Stack trace rendue conditionnelle pour réduire le bruit et le coût I/O
    try:
        import os
        from flask import request as _r
        debug_stack = (
            os.environ.get("AGRIWEB_DEBUG_STACK", "0") == "1" or
            _r.args.get("debug_stack") == "1"
        )
    except Exception:
        debug_stack = False
    if debug_stack:
        lines = traceback.format_stack(limit=40)
        # #  print(f"📞 [CALL  # Optimisé pour performance #{call_id}] Stack trace (activée) lignes={len(lines)}")  # Optimisé pour performance
        for line in lines:
            pass # print("    " + line.strip())  # Optimisé pour performance
    # else:
        # #  print(f"📞 [CALL  # Optimisé pour performance #{call_id}] Stack trace désactivée (set AGRIWEB_DEBUG_STACK=1 ou ?debug_stack=1 pour l'afficher)")  # Optimisé pour performance
    
    # ╔══════════════════════════════════════════════════════════════════════════╗
    # ║                    CIRCUIT BREAKER ANTI-LOOP ULTRA-ROBUSTE              ║
    # ╚══════════════════════════════════════════════════════════════════════════╝
    
    # Compteur global de requêtes par IP
    if not hasattr(search_by_commune, 'request_counter'):
        search_by_commune.request_counter = {}
    if not hasattr(search_by_commune, 'blocked_ips'):
        search_by_commune.blocked_ips = {}
    
    # Récupération IP client
    client_ip = flask_request.environ.get('HTTP_X_FORWARDED_FOR', 
                                        flask_request.environ.get('REMOTE_ADDR', 'unknown'))
    if ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()
    
    current_time = time.time()
    
    # Vérifier si IP est bloquée
    if client_ip in search_by_commune.blocked_ips:
        block_time, block_reason = search_by_commune.blocked_ips[client_ip]
        if current_time - block_time < 300:  # 5 minutes de blocage
            # print(f"[BLOCKED_IP] IP {client_ip} bloquée pour: {block_reason}")  # Optimisé pour performance
            return jsonify({
                "error": "IP temporairement bloquée - loop détecté",
                "retry_after": 300 - (current_time - block_time),
                "blocked_reason": block_reason
            }), 429
        else:
            # Débloquer après 5 minutes
            del search_by_commune.blocked_ips[client_ip]
            # print(f"[UNBLOCKED] IP {client_ip} débloquée après timeout")  # Optimisé pour performance
    
    # Compter les requêtes par IP
    if client_ip not in search_by_commune.request_counter:
        search_by_commune.request_counter[client_ip] = []
    
    # Nettoyer les requêtes anciennes (> 60 secondes)
    search_by_commune.request_counter[client_ip] = [
        req_time for req_time in search_by_commune.request_counter[client_ip]
        if current_time - req_time < 60
    ]
    
    # Ajouter la requête actuelle
    search_by_commune.request_counter[client_ip].append(current_time)
    
    # Vérifier le nombre de requêtes
    request_count = len(search_by_commune.request_counter[client_ip])
    # print(f"[IP_TRACKING] IP: {client_ip}, Requêtes/minute: {request_count}")  # Optimisé pour performance
    
    # Bloquer si trop de requêtes (plus de 20 par minute = suspect - AUGMENTÉ pour usage normal)
    if request_count > 20:
        search_by_commune.blocked_ips[client_ip] = (current_time, f"Trop de requêtes: {request_count}/min")
        # print(f"[AUTO_BLOCK] IP {client_ip} bloquée automatiquement")  # Optimisé pour performance
        return jsonify({
            "error": "Trop de requêtes détectées - IP bloquée temporairement",
            "retry_after": 300,
            "requests_detected": request_count
        }), 429
    
    # print("[CIRCUIT_BREAKER] Protection active - requête autorisée")  # Optimisé pour performance
    
    # Récupération des paramètres de base
    request_params = dict(flask_request.values)
    # print(f"[PARAMS] Paramètres reçus: {request_params}")  # Optimisé pour performance
    
    # === PROTECTION ANTI-LOOP STANDARD (en plus du circuit breaker) ===
    # Cache global pour éviter les requêtes en loop
    if not hasattr(search_by_commune, 'anti_loop_cache'):
        search_by_commune.anti_loop_cache = {}
        
    # 1️⃣ GÉNÉRATION SIGNATURE UNIQUE DE LA REQUÊTE
    request_signature = hashlib.md5(
        json.dumps(request_params, sort_keys=True).encode('utf-8')
    ).hexdigest()
    
    cache_window = 120  # 120 secondes (2 minutes) pour éviter les boucles infinies
    
    # print(f"[ANTI-LOOP] === PROTECTION DOUBLE ACTIVE ===")  # Optimisé pour performance
    # print(f"[SIGNATURE] Signature requête: {request_signature}")  # Optimisé pour performance
    # print(f"[CACHE] Taille cache actuel: {len(search_by_commune.anti_loop_cache)}")  # Optimisé pour performance
    
    # 2️⃣ VÉRIFICATION CACHE HIT/MISS
    if request_signature in search_by_commune.anti_loop_cache:
        last_request_time = search_by_commune.anti_loop_cache[request_signature]
        time_diff = current_time - last_request_time
        
        # print(f"[CACHE_HIT] Requête identique détectée!")  # Optimisé pour performance
        # print(f"[TIMING] Différence temps: {time_diff:.2f}s")  # Optimisé pour performance
        
        if time_diff < cache_window:
            # print(f"[BLOCKED] Loop détecté - requête bloquée (< {cache_window}s)")  # Optimisé pour performance
            return jsonify({
                "error": "Loop détecté - veuillez patienter", 
                "retry_after": cache_window - time_diff
            }), 429
        else:
            # print(f"[ALLOWED] Requête autorisée (> {cache_window}s)")  # Optimisé pour performance
            pass
    else:
        # print(f"[CACHE_MISS] Nouvelle signature - requête autorisée")  # Optimisé pour performance
        pass
    
    # 3️⃣ ENREGISTREMENT DE LA REQUÊTE ACTUELLE
    search_by_commune.anti_loop_cache[request_signature] = current_time
    
    # 4️⃣ NETTOYAGE DU CACHE (garde seulement les 10 dernières)
    if len(search_by_commune.anti_loop_cache) > 10:
        oldest_keys = sorted(
            search_by_commune.anti_loop_cache.items(), 
            key=lambda x: x[1]
        )[:5]  # Retire les 5 plus anciennes
        for key, _ in oldest_keys:
            del search_by_commune.anti_loop_cache[key]
    
    # print(f"[STATS] Cache final: {len(search_by_commune.anti_loop_cache)} entrées")  # Optimisé pour performance
    # print("="*80)  # Optimisé pour performance
    
    # Log immédiat pour diagnostiquer si la requête arrive
    # print(f"[DEBUG_FETCH] Requête reçue sur /search_by_commune")  # Optimisé pour performance
    # print(f"[DEBUG_FETCH] Méthode: {flask_request.method}")  # Optimisé pour performance
    # print(f"[DEBUG_FETCH] Args: {dict(flask_request.args)}")  # Optimisé pour performance
    # print(f"[DEBUG_FETCH] Values: {dict(flask_request.values)}")  # Optimisé pour performance
    
    # Headers CORS pour éviter les problèmes de fetch
    from flask import make_response
    
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Connection'] = 'keep-alive'
        return response
    
    # 1) Paramètres - Récupération sécurisée pour éviter les erreurs OSError
    try:
        commune = flask_request.values.get("commune", "").strip()
        culture = flask_request.values.get("culture", "")
        ht_max_km = float(flask_request.values.get("ht_max_distance", 1.0))
        bt_max_km = float(flask_request.values.get("bt_max_distance", 1.0))
        sir_km    = float(flask_request.values.get("sirene_radius", 0.05))
        min_ha    = float(flask_request.values.get("min_area_ha", 0))
        max_ha    = float(flask_request.values.get("max_area_ha", 1e9))

        # Nouveaux filtres par type de données
        filter_rpg = flask_request.values.get("filter_rpg", "false").lower() == "true"
        rpg_min_area = float(flask_request.values.get("rpg_min_area", 1.0))
        rpg_max_area = float(flask_request.values.get("rpg_max_area", 1000.0))
        
        # DEBUG: Log des paramètres RPG reçus (optimisé pour performance)
        # print(f"🚨 [DEBUG_RPG] filter_rpg reçu: '{flask_request.values.get('filter_rpg', 'PAS_TROUVE')}' -> {filter_rpg}")
        # print(f"🚨 [DEBUG_RPG] rpg_min_area: {rpg_min_area}, rpg_max_area: {rpg_max_area}")
        # print(f"🚨 [DEBUG_RPG] Tous paramètres reçus: {dict(flask_request.values)}")

        filter_parkings = flask_request.values.get("filter_parkings", "false").lower() == "true"
        parking_min_area = float(flask_request.values.get("parking_min_area", 1500.0))

        filter_friches = flask_request.values.get("filter_friches", "false").lower() == "true"
        friches_min_area = float(flask_request.values.get("friches_min_area", 1000.0))

        filter_zones = flask_request.values.get("filter_zones", "false").lower() == "true"
        zones_min_area = float(flask_request.values.get("zones_min_area", 1000.0))
        zones_type_filter = flask_request.values.get("zones_type_filter", "")

        # Filtres toitures
        filter_toitures = flask_request.values.get("filter_toitures", "false").lower() == "true"
        toitures_min_surface = float(flask_request.values.get("toitures_min_surface", 100.0))

        # Filtres de distance UNIFIÉS pour tous les filtres (hors zones)
        filter_by_distance = flask_request.values.get("filter_by_distance", "false").lower() == "true"
        max_distance_bt = float(flask_request.values.get("max_distance_bt", 500.0))  # mètres
        max_distance_hta = float(flask_request.values.get("max_distance_hta", 2000.0))  # mètres
        distance_logic = flask_request.values.get("distance_logic", "OR").upper()  # OR/AND ou ET/OU
        # Normaliser les valeurs françaises ET/OU vers AND/OR
        if distance_logic in ("ET", "AND"):
            distance_logic = "AND"
        elif distance_logic in ("OU", "OR"):
            distance_logic = "OR"
        else:
            distance_logic = "OR"
        poste_type_filter = flask_request.values.get("poste_type_filter", "ALL").upper()  # ALL, BT, HTA

        # Nouveau filtre pour calculer la surface non bâtie
        calculate_surface_libre = flask_request.values.get("calculate_surface_libre", "false").lower() == "true"
        
        # Filtres pour les lignes HTA aériennes et souterraines
        filter_hta_lines_aerial = flask_request.values.get("filter_hta_lines_aerial", "false").lower() == "true"
        filter_hta_lines_underground = flask_request.values.get("filter_hta_lines_underground", "false").lower() == "true"
        hta_aerial_max_km = float(flask_request.values.get("hta_aerial_max_km", 2.0))
        hta_underground_max_km = float(flask_request.values.get("hta_underground_max_km", 2.0))
        
        # Log détaillé du début de la recherche
        params_log = {
            'filter_rpg': filter_rpg, 'rpg_min_area': rpg_min_area, 'rpg_max_area': rpg_max_area,
            'filter_parkings': filter_parkings, 'parking_min_area': parking_min_area,
            'filter_friches': filter_friches, 'friches_min_area': friches_min_area,
            'filter_zones': filter_zones, 'zones_min_area': zones_min_area, 'zones_type_filter': zones_type_filter,
            'filter_toitures': filter_toitures, 'toitures_min_surface': toitures_min_surface,
            'filter_by_distance': filter_by_distance, 'max_distance_bt': max_distance_bt, 
            'max_distance_hta': max_distance_hta, 'distance_logic': distance_logic,
            'ht_max_km': ht_max_km, 'bt_max_km': bt_max_km, 'sir_km': sir_km
        }
        log_search_start(commune, params_log)
        
    except OSError as e:
        # Erreur de canal fermé (WinError 233) - utiliser des valeurs par défaut
        safe_print(f"⚠️ [PARAMÈTRES] Erreur lecture paramètres: {e}, utilisation valeurs par défaut")
        # CORRECTION CRITIQUE: Préserver commune s'il a été lu avec succès
        if 'commune' not in locals():
            commune = ""
        culture = ""
        ht_max_km = 1.0
        bt_max_km = 1.0
        sir_km = 0.05
        min_ha = 0
        max_ha = 1e9
        filter_rpg = False
        rpg_min_area = 1.0
        rpg_max_area = 1000.0
        filter_parkings = False
        parking_min_area = 1500.0
        filter_friches = False
        friches_min_area = 1000.0
        filter_zones = False
        zones_min_area = 1000.0
        zones_type_filter = ""
        filter_toitures = False
        toitures_min_surface = 100.0
        filter_by_distance = False
        max_distance_bt = 500.0
        max_distance_hta = 2000.0
        distance_logic = "OR"
        poste_type_filter = "ALL"
        calculate_surface_libre = False
        filter_hta_lines_aerial = False
        filter_hta_lines_underground = False
        hta_aerial_max_km = 2.0
        hta_underground_max_km = 2.0

    if not commune:
        return jsonify({"error": "Veuillez fournir une commune."}), 400

    # Logging sécurisé pour éviter les erreurs de canal fermé
    try:
        safe_print(f"🔍 [COMMUNE] Recherche filtrée pour {commune}")
        if filter_rpg:
            safe_print(f"    RPG: {rpg_min_area}-{rpg_max_area} ha")
        if filter_parkings:
            safe_print(f"    Parkings: >{parking_min_area}m², BT<{max_distance_bt}m, HTA<{max_distance_hta}m")
        if filter_friches:
            safe_print(f"    Friches: >{friches_min_area}m², BT<{max_distance_bt}m, HTA<{max_distance_hta}m")
        if filter_zones:
            safe_print(f"    Zones: >{zones_min_area}m², type: {zones_type_filter or 'toutes'}")
        if filter_toitures:
            safe_print(f"    Toitures: >{toitures_min_surface}m², BT<{max_distance_bt}m, HTA<{max_distance_hta}m")
        if filter_by_distance:
            safe_print(f"    Distance postes: BT<{max_distance_bt}m, HTA<{max_distance_hta}m, type: {poste_type_filter}")
        if calculate_surface_libre:
            safe_print(f"🏠 [SURFACE_LIBRE] Calcul de surface libre activé - soustraction des empreintes bâties")
    except OSError:
        # Ignorer les erreurs de canal fermé (WinError 233)
        pass

    # 2) Récupère le contour de la commune via Geo API Gouv
    commune_infos = requests.get(
        f"https://geo.api.gouv.fr/communes?nom={quote_plus(commune)}&fields=centre,contour"
    ).json()
    if not commune_infos or not commune_infos[0].get("contour"):
        return jsonify({"error": "Contour de la commune introuvable."}), 404
    contour = commune_infos[0]["contour"]
    centre = commune_infos[0]["centre"]
    lat, lon = centre["coordinates"][1], centre["coordinates"][0]

    # 3) Emprise bbox englobant le polygone (pour limiter la requête WFS)
    try:
        commune_poly = shape(contour)
        minx, miny, maxx, maxy = commune_poly.bounds
        bbox = f"{minx},{miny},{maxx},{maxy},EPSG:4326"
        # print(f"[BBOX] Bbox calculée: {bbox}")  # Optimisé pour performance
    except Exception as e:
        # print(f"[BBOX] Erreur calcul bbox: {e}")  # Optimisé pour performance
        # Fallback avec des coordonnées par défaut autour du centre
        margin = 0.01  # ~1km de marge
        minx, maxx = lon - margin, lon + margin
        miny, maxy = lat - margin, lat + margin
        bbox = f"{minx},{miny},{maxx},{maxy},EPSG:4326"
        # print(f"[BBOX] Fallback bbox: {bbox}")  # Optimisé pour performance
        commune_poly = None

    # 4) Récupère toutes les features dans le bbox puis filtre par intersection avec le polygone
    def filter_in_commune(features):
        filtered = []
        for f in features:
            if "geometry" not in f:
                continue
            try:
                # Créer la géométrie et la valider
                geom = shape(f["geometry"])
                if not geom.is_valid:
                    # Tenter de corriger la géométrie invalide
                    geom = geom.buffer(0)
                    if not geom.is_valid:
                        continue
                
                # Vérifier l'intersection
                if geom.intersects(commune_poly):
                    filtered.append(f)
            except Exception as e:
                # Ignorer les géométries qui causent des erreurs
                # print(f"Géométrie ignorée à cause d'une erreur: {e}")  # Optimisé pour performance
                continue
        return filtered

    # NOUVELLE APPROCHE: Utilisation du polygone exact de la commune selon la doc API Carto
    # print(f"🆕 [NOUVELLE_APPROCHE] Utilisation du polygone exact de la commune (API Carto)")  # Optimisé pour performance
    # print(f"🆕 [COMMUNE_POLYGON] Récupération exhaustive sur toute la commune: {commune}")  # Optimisé pour performance
    
    # Utilisation des nouvelles fonctions qui exploitent le polygone complet de la commune
    log_data_collection("DÉBUT", "Collecte des données géographiques")
    
    rpg_raw = []
    if filter_rpg:
        log_data_collection("RPG", f"Récupération parcelles RPG (surface {rpg_min_area}-{rpg_max_area} ha)")
        rpg_raw = get_rpg_info_by_polygon(contour)
        log_data_collection("RPG", f"✅ {len(rpg_raw)} parcelles RPG récupérées")
    else:
        log_data_collection("RPG", "❌ Récupération RPG désactivée")
    
    log_data_collection("POSTES", "Récupération des postes électriques")
    postes_bt_data = filter_in_commune(fetch_wfs_data(POSTE_LAYER, bbox))
    postes_hta_data = filter_in_commune(fetch_wfs_data(HT_POSTE_LAYER, bbox))
    log_data_collection("POSTES", f"✅ {len(postes_bt_data)} postes BT, {len(postes_hta_data)} postes HTA")
    
    # Récupération des lignes HTA (aériennes et souterraines)
    log_data_collection("LIGNES HTA", "Récupération des lignes électriques HTA")
    hta_lignes_data = {"aerienne": {"features": []}, "souterraine": {"features": []}}
    try:
        from enedis_integration import get_lignes_hta
        
        # Utiliser le bbox pour récupérer les lignes HTA
        hta_lignes_data = get_lignes_hta(
            bbox=[minx, miny, maxx, maxy],
            include_aerienne=True,
            include_souterraine=True,
            limit=800
        )
        aerienne_count = len(hta_lignes_data.get("aerienne", {}).get("features", []))
        souterraine_count = len(hta_lignes_data.get("souterraine", {}).get("features", []))
        log_data_collection("LIGNES HTA", f"✅ {aerienne_count} lignes aériennes, {souterraine_count} lignes souterraines")
    except Exception as e:
        log_data_collection("LIGNES HTA", f"❌ Erreur récupération: {e}")
        # print(f"[LIGNES HTA] Erreur lors de la récupération: {e}")  # Optimisé pour performance
    
    log_data_collection("ÉLEVEURS", "Récupération des données éleveurs")
    eleveurs_data = filter_in_commune(fetch_wfs_data(ELEVEURS_LAYER, bbox, srsname="EPSG:4326"))
    log_data_collection("ÉLEVEURS", f"✅ {len(eleveurs_data)} exploitants trouvés")
    
    # plu_info sera remplacé par filtered_zones après l'optimisation des zones
    log_data_collection("PLU", "Récupération des zones d'urbanisme")
    plu_info_temp = get_plu_info_by_polygon(contour)
    log_data_collection("PLU", f"✅ {len(plu_info_temp)} zones PLU récupérées")
    
    log_data_collection("ZAER", "Récupération des zones ZAER")
    zaer_data = get_zaer_info_by_polygon(contour)
    log_data_collection("ZAER", f"✅ {len(zaer_data)} zones ZAER trouvées")
    
    # Récupération conditionnelle des données avec filtrage - NOUVELLE MÉTHODE POLYGONE
    parkings_data = []
    if filter_parkings:
        log_data_collection("PARKINGS", f"Récupération parkings (surface min {parking_min_area} m²)")
        parkings_data = get_parkings_info_by_polygon(contour)
        log_data_collection("PARKINGS", f"✅ {len(parkings_data)} parkings récupérés")
    else:
        log_data_collection("PARKINGS", "❌ Récupération parkings désactivée")
    
    friches_data = []
    if filter_friches:
        log_data_collection("FRICHES", f"Récupération friches (surface min {friches_min_area} m²)")
        friches_data = get_friches_info_by_polygon(contour)
        log_data_collection("FRICHES", f"✅ {len(friches_data)} friches récupérées")
    else:
        log_data_collection("FRICHES", "❌ Récupération friches désactivée")
    
    # Données toujours récupérées pour les calculs de distance - NOUVELLE MÉTHODE POLYGONE
    log_data_collection("SOLAIRE", "Récupération du potentiel solaire")
    solaire_data = get_solaire_info_by_polygon(contour)
    log_data_collection("SOLAIRE", f"✅ {len(solaire_data)} données solaires récupérées")
    
    # 🏠 ENRICHISSEMENT ADRESSES pour solaire_data (toitures) - OPTIMISÉ PRODUCTION
    if solaire_data:
        # print(f"🏠 [SOLAIRE-ADRESSES] Enrichissement de {len(solaire_data)} toitures avec adresses IGN")  # Optimisé pour production
        from urllib.parse import quote_plus
        
        for i, toiture in enumerate(solaire_data):
            # Log de progression réduit pour production
            # if (i + 1) % 20 == 0 or i == 0:
            #     print(f"    📍 [SOLAIRE] Progression adresses: {i+1}/{len(solaire_data)} toitures...")
            
            # Enrichissement avec l'adresse IGN (géocodage inverse)
            geom = toiture.get("geometry", {})
            if geom and geom.get("type") in ["Polygon", "MultiPolygon"]:
                try:
                    # Calculer le centroïde de la toiture pour obtenir lat/lon
                    from shapely.geometry import shape
                    shp_geom = shape(geom)
                    centroid = shp_geom.centroid
                    
                    # Géocodage inverse IGN
                    adresse_info = get_address_from_coordinates(centroid.y, centroid.x)
                    
                    if adresse_info and adresse_info.get('address'):
                        toiture["properties"]["adresse"] = adresse_info['address']
                        toiture["properties"]["adresse_distance"] = adresse_info.get('distance', 0)
                        toiture["properties"]["adresse_score"] = adresse_info.get('score', 0)
                        toiture["properties"]["code_postal"] = adresse_info.get('postcode', '')
                        toiture["properties"]["ville"] = adresse_info.get('city', '')
                        toiture["properties"]["code_commune"] = adresse_info.get('citycode', '')
                        # Lien Pages Jaunes spécifique pour les toitures avec adresse complète
                        try:
                            adresse_complete = adresse_info.get('address', '')
                            adresse_encoded = quote_plus(adresse_complete)
                            toiture["properties"]["lien_annuaire"] = f"https://www.pagesjaunes.fr/annuaire/chercherlespros?quoiqui=&ou={adresse_encoded}&univers=pagesjaunes&idOu="
                        except Exception:
                            pass
                    else:
                        toiture["properties"]["adresse"] = "Adresse non trouvée"
                        toiture["properties"]["adresse_distance"] = None
                        toiture["properties"]["adresse_score"] = 0
                except Exception as e:
                    # print(f"🔴 [SOLAIRE-ADRESSE] Erreur enrichissement toiture {i}: {e}")  # Optimisé pour production
                    toiture["properties"]["adresse"] = "Erreur géocodage"
        
        # print(f"✅ [SOLAIRE-ADRESSES] Enrichissement terminé pour {len(solaire_data)} toitures")  # Optimisé pour production
    
    log_data_collection("SIRENE", f"Récupération entreprises SIRENE (rayon {sir_km} km)")
    sirene_data = get_sirene_info_by_polygon(contour)
    log_data_collection("SIRENE", f"✅ {len(sirene_data)} entreprises trouvées")

    point = {"type": "Point", "coordinates": [lon, lat]}
    
    # Fonction d'optimisation pour éviter les erreurs 414 "Request-URI Too Large"
    def optimize_geometry_for_api(geom):
        """
        Optimise une géométrie pour éviter les erreurs 414 en la simplifiant si nécessaire
        """
        from shapely.geometry import shape
        try:
            # Vérifier la taille du JSON de la géométrie
            geom_json = json.dumps(geom)
            # Réduire le seuil pour déclencher l'optimisation plus tôt
            if len(geom_json) > 4000:  # Seuil réduit pour éviter les erreurs 414
                # print(f"[OPTIMISATION] Géométrie trop complexe ({len(geom_json)} chars), simplification en bbox")  # Optimisé pour performance
                # Convertir en bounding box simple
                shp_geom = shape(geom)
                minx, miny, maxx, maxy = shp_geom.bounds
                bbox_geom = {
                    "type": "Polygon",
                    "coordinates": [[
                        [minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy], [minx, miny]
                    ]]
                }
                return bbox_geom
            else:
                # print(f"[OPTIMISATION] Géométrie OK ({len(geom_json)} chars)")  # Optimisé pour performance
                return geom
        except Exception as e:
            # print(f"[OPTIMISATION] Erreur, utilisation géométrie originale: {e}")  # Optimisé pour performance
            return geom
    
    # Récupération enrichie des données API avec optimisation géométrique
    # print(f"🔍 [COMMUNE] Utilisation du polygone pour les APIs avec optimisation anti-414")
    contour_optimise = optimize_geometry_for_api(contour)
    
    api_cadastre   = get_api_cadastre_data(contour_optimise)  # Utilise le polygone optimisé
    api_nature     = get_all_api_nature_data(contour_optimise)  # Utilise le polygone optimisé
    api_urbanisme  = get_all_gpu_data(contour_optimise)  # Utilise le polygone optimisé
    
    # Enrichissement des données si l'option zones est activée
    if filter_zones and api_urbanisme.get("success"):
        # print(f"🔍 [COMMUNE] Enrichissement des détails de zones GPU pour {commune}")
        # Ajouter des informations détaillées sur les zones trouvées
        zones_summary = {}
        if api_urbanisme.get("details"):
            for zone_key, zone_data in api_urbanisme["details"].items():
                if zone_data.get("features"):
                    zones_summary[zone_key] = {
                        "count": zone_data.get("count", 0),
                        "name_fr": zone_data.get("name_fr", zone_key),
                        "features_sample": zone_data["features"][:3] if len(zone_data["features"]) > 3 else zone_data["features"]
                    }
        api_urbanisme["zones_summary"] = zones_summary

    # 5) Filtrage RPG (culture, surface, distances)
    to_l93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True).transform

    final_rpg = []
    rejected_surface_count = 0
    rejected_distance_count = 0
    processed_count = 0
    
    total_rpg = len(rpg_raw or [])
    # print(f"🔍 [RPG] Début filtrage sur {total_rpg} parcelles")  # Optimisé pour performance
    
    for feat in (rpg_raw or []):
        processed_count += 1
        
        # Limite de sécurité pour éviter les loops infinies
        if processed_count > 1000:
            # print(f"[RPG] Limite de sécurité atteinte: {processed_count} parcelles traitées")  # Optimisé pour performance
            break
            
        dec   = decode_rpg_feature(feat)
        poly  = shape(dec["geometry"])
        props = dec["properties"]

        # a) culture
        if culture and culture.lower() not in props.get("Culture", "").lower():
            continue

        # b) surface (ha) - CORRECTION: Utiliser les paramètres RPG spécifiques
        ha = shp_transform(to_l93, poly).area / 10_000.0
        if ha < rpg_min_area or ha > rpg_max_area:
            rejected_surface_count += 1
            continue

        # c) distances réseaux : utiliser la logique unifiée de filtrage par distance
        cent = poly.centroid.coords[0]
        d_bt = calculate_min_distance(cent, postes_bt_data)
        d_hta = calculate_min_distance(cent, postes_hta_data)

        # Calcul des distances aux lignes HTA (pour affichage dans les popups)
        d_ligne_aerienne = None
        d_ligne_souterraine = None
        
        if hta_lignes_data.get("aerienne", {}).get("features"):
            d_ligne_aerienne = calculate_min_distance_to_lines(cent, hta_lignes_data["aerienne"]["features"])
            
        if hta_lignes_data.get("souterraine", {}).get("features"):
            d_ligne_souterraine = calculate_min_distance_to_lines(cent, hta_lignes_data["souterraine"]["features"])

        # Appliquer le filtrage par distance unifié (même logique que les autres éléments)
        if filter_by_distance:
            # Logique de filtrage par type de poste (BT/HTA/Tous)
            bt_ok = (d_bt is not None and d_bt <= max_distance_bt) if d_bt is not None else False
            hta_ok = (d_hta is not None and d_hta <= max_distance_hta) if d_hta is not None else False
            
            if poste_type_filter == "BT":
                distance_ok = bt_ok
            elif poste_type_filter == "HTA":
                distance_ok = hta_ok
            else:  # ALL
                distance_ok = bt_ok or hta_ok
                
            if not distance_ok:
                rejected_distance_count += 1
                continue

        props.update({
            "SURF_HA": round(ha, 3),
            "min_distance_bt_m": round(d_bt, 2) if d_bt is not None else None,
            "min_distance_hta_m": round(d_hta, 2) if d_hta is not None else None,
            "min_distance_hta_aerial_m": round(d_ligne_aerienne, 2) if d_ligne_aerienne is not None else None,
            "min_distance_hta_underground_m": round(d_ligne_souterraine, 2) if d_ligne_souterraine is not None else None,
        })
        final_rpg.append({
            "type":       "Feature",
            "geometry":   dec["geometry"],
            "properties": props
        })

    # Résumé du filtrage RPG
    accepted_count = len(final_rpg)
    total_rejected = rejected_surface_count + rejected_distance_count
    # print(f"[RPG] Filtrage terminé: {accepted_count} gardées, {total_rejected} rejetées ({rejected_surface_count} surface, {rejected_distance_count} distance)")  # Optimisé pour performance

    # Filtrage avancé pour les nouvelles couches
    
    # Initialisation des listes filtrées
    filtered_parkings = []
    filtered_friches = []
    filtered_zones = []
    filtered_parcelles_in_zones = []
    
    # 5b) Filtrage des parkings selon les critères (utilise les sliders unifiés)
    if filter_parkings and parkings_data:
        log_data_collection("FILTRAGE PARKINGS", f"✅ Début filtrage sur {len(parkings_data)} parkings")
        # print(f"🔍 [PARKINGS] Filtrage: >{parking_min_area}m², BT<{max_distance_bt}m, HTA<{max_distance_hta}m")
        # print(f"🔍 [PARKINGS] Parkings bruts récupérés: {len(parkings_data)}")
        
        surfaces_rejetees = 0
        distances_rejetees = 0
        
        for feat in parkings_data:
            if "geometry" not in feat:
                continue
            try:
                poly = shape(feat["geometry"])
                props = feat.get("properties", {})

                # Calcul de la surface en m²
                area_m2 = shp_transform(to_l93, poly).area
                if area_m2 < parking_min_area:
                    surfaces_rejetees += 1
                    continue

                # Calcul de la distance aux postes BT/HTA
                cent = poly.centroid.coords[0]
                d_bt = calculate_min_distance(cent, postes_bt_data)
                d_hta = calculate_min_distance(cent, postes_hta_data)

                # Logique de filtrage portée par le type de poste sélectionné (Tous/BT/HTA)
                bt_ok = (d_bt is not None and d_bt <= max_distance_bt) if d_bt is not None else False
                hta_ok = (d_hta is not None and d_hta <= max_distance_hta) if d_hta is not None else False
                if filter_by_distance:
                    if poste_type_filter == "BT":
                        distance_ok = bt_ok
                    elif poste_type_filter == "HTA":
                        distance_ok = hta_ok
                    else:  # ALL
                        distance_ok = bt_ok or hta_ok
                else:
                    # Pas de filtrage par distance lorsque l'option n'est pas cochée
                    distance_ok = True
                if not distance_ok:
                    distances_rejetees += 1
                    continue

                # Enrichissement des propriétés
                props.update({
                    "surface_m2": round(area_m2, 2),
                    "min_distance_bt_m": round(d_bt, 2) if d_bt is not None else None,
                    "min_distance_hta_m": round(d_hta, 2) if d_hta is not None else None
                })

                # Calcul de la surface libre si demandé
                if calculate_surface_libre:
                    try:
                        # print(f"[SURFACE_LIBRE] Calcul pour parking...")  # Optimisé pour performance
                        batiments_data = get_batiments_data(feat["geometry"])
                        surface_libre_result = calculate_surface_libre_parcelle(feat["geometry"], batiments_data)
                        props.update({
                            'surface_batie_m2': surface_libre_result.get('surface_batie_m2', 0),
                            'surface_libre_m2': surface_libre_result.get('surface_libre_m2', 0),
                            'surface_libre_pct': surface_libre_result.get('surface_libre_pct', 0),
                            'batiments_count': surface_libre_result.get('batiments_count', 0)
                        })
                    except Exception as e:
                        # print(f"[SURFACE_LIBRE] Erreur parking: {e}")  # Optimisé pour performance
                        props['surface_libre_error'] = str(e)

                filtered_parkings.append({
                    "type": "Feature",
                    "geometry": feat["geometry"],
                    "properties": props
                })
            except Exception as e:
                # print(f"Erreur filtrage parking: {e}")  # Optimisé pour performance
                continue
        
        # Log détaillé des résultats de filtrage
        total_rejets = surfaces_rejetees + distances_rejetees
        log_data_collection("FILTRAGE PARKINGS", 
                          f"✅ {len(filtered_parkings)} retenus / {len(parkings_data)} analysés")
        log_data_collection("FILTRAGE PARKINGS", 
                          f"❌ Rejetés: {surfaces_rejetees} (surface), {distances_rejetees} (distance)")
        # print(f"[PARKINGS] {len(filtered_parkings)} parkings trouvés après filtrage")  # Optimisé pour performance
        
        # 5b-bis) Récupération optimisée des références cadastrales pour les parkings sélectionnés
        if filtered_parkings:
            # print(f"🏛️ [CADASTRE-PARKINGS] Récupération des références cadastrales pour {len(filtered_parkings)} parkings...")  # Optimisé pour production multi-user
            
            def get_parcelles_for_parking(parking_geometry):
                """Récupère les parcelles cadastrales intersectant un parking spécifique"""
                try:
                    api_url = "https://apicarto.ign.fr/api/cadastre/parcelle"
                    params = {
                        "geom": json.dumps(parking_geometry),
                        "_limit": 50  # Limite raisonnable pour un parking
                    }
                    
                    resp = requests.get(api_url, params=params, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        return data.get('features', [])
                    else:
                        # print(f"Erreur API cadastre: {resp.status_code}")  # Optimisé pour performance
                        return []
                except Exception as e:
                    # print(f"Exception cadastre parking: {e}")  # Optimisé pour performance
                    return []
            
            # Enrichir chaque parking avec ses références cadastrales
            for i, parking in enumerate(filtered_parkings):
                # print(f"    📍 Parking {i+1}/{len(filtered_parkings)}: recherche cadastre...")  # Optimisé pour production multi-user
                parcelles_parking = get_parcelles_for_parking(parking["geometry"])
                
                if parcelles_parking:
                    # print(f"      🔍 [DEBUG] Structure API cadastre - première parcelle: {parcelles_parking[0] if parcelles_parking else 'Aucune'}")  # Optimisé pour production multi-user
                    
                    # Extraire les références cadastrales
                    refs_cadastrales = []
                    for parcelle in parcelles_parking:
                        props = parcelle.get('properties', {})
                        # print(f"      🔍 [DEBUG] Propriétés parcelle: {props}")  # Optimisé pour production multi-user
                        
                        # Tester différents noms d'attributs possibles selon l'API
                        numero = props.get('numero') or props.get('numero_parcelle') or props.get('num_parc') or ''
                        section = props.get('section') or props.get('code_section') or ''
                        commune = props.get('commune') or props.get('code_commune') or props.get('insee') or ''
                        prefixe = props.get('prefixe') or props.get('code_arr') or ''
                        
                        ref = {
                            'numero': numero,
                            'section': section,
                            'commune': commune,
                            'prefixe': prefixe,
                            'reference_complete': f"{commune}{prefixe}{section}{numero}".strip()
                        }
                        
                        # print(f"[DEBUG] Référence créée: {ref}")  # Optimisé pour performance
                        refs_cadastrales.append(ref)
                    
                    # Ajouter aux propriétés du parking
                    parking["properties"]["parcelles_cadastrales"] = refs_cadastrales
                    parking["properties"]["nb_parcelles_cadastrales"] = len(refs_cadastrales)
                    # print(f"{len(refs_cadastrales)} parcelles cadastrales trouvées")  # Optimisé pour performance
                else:
                    parking["properties"]["parcelles_cadastrales"] = []
                    parking["properties"]["nb_parcelles_cadastrales"] = 0
                    # print(f"Aucune parcelle cadastrale trouvée")  # Optimisé pour performance
                
                # 🏠 ENRICHISSEMENT ADRESSE IGN pour le parking - OPTIMISÉ PRODUCTION
                # print(f"      🔍 [DEBUG_ADRESSE] Début enrichissement adresse parking {i+1}")  # Optimisé pour production
                geom = parking.get("geometry", {})
                # print(f"      🔍 [DEBUG_ADRESSE] Géométrie: {geom.get('type') if geom else 'None'}")  # Optimisé pour production
                if geom and geom.get("type") in ["Polygon", "MultiPolygon"]:
                    try:
                        # Calculer le centroïde du parking pour obtenir lat/lon
                        from shapely.geometry import shape
                        shp_geom = shape(geom)
                        centroid = shp_geom.centroid
                        
                        # Géocodage inverse IGN
                        adresse_info = get_address_from_coordinates(centroid.y, centroid.x)
                        
                        if adresse_info and adresse_info.get('address'):
                            parking["properties"]["adresse"] = adresse_info['address']
                            parking["properties"]["adresse_distance"] = adresse_info.get('distance', 0)
                            parking["properties"]["adresse_score"] = adresse_info.get('score', 0)
                            parking["properties"]["code_postal"] = adresse_info.get('postcode', '')
                            parking["properties"]["ville"] = adresse_info.get('city', '')
                            parking["properties"]["code_commune"] = adresse_info.get('citycode', '')
                            # print(f"      🏠 [ADRESSE] {adresse_info['address']}")  # Optimisé pour production
                        else:
                            parking["properties"]["adresse"] = "Adresse non trouvée"
                            # print(f"      ❌ [ADRESSE] Géocodage inverse impossible pour ce parking")  # Optimisé pour production
                            
                    except Exception as e:
                        parking["properties"]["adresse"] = "Erreur géocodage"
                        # print(f"      🔴 [ADRESSE] Erreur géocodage parking: {e}")  # Optimisé pour production
            
            # print(f"✅ [CADASTRE-PARKINGS] Enrichissement terminé pour tous les parkings")  # Optimisé pour production multi-user
    else:
        # print(f"[PARKINGS] Filtre parkings non activé ou aucune donnée: filter_parkings={filter_parkings}, parkings_data={len(parkings_data) if parkings_data else 0}")  # Optimisé pour performance
        pass
    
    # 5c) Filtrage des friches selon les critères (utilise les sliders unifiés)
    if filter_friches and friches_data:
        log_data_collection("FRICHES", f"🎯 Début filtrage: {len(friches_data)} friches à analyser")
        # print(f"[FRICHES] Filtrage: >{friches_min_area}m², BT<{max_distance_bt}m, HTA<{max_distance_hta}m")  # Optimisé pour performance
        
        # Compteurs de rejet
        surfaces_rejetees = 0
        distances_rejetees = 0
        
        for feat in friches_data:
            if "geometry" not in feat:
                continue
            try:
                poly = shape(feat["geometry"])
                props = feat.get("properties", {})

                # Calcul de la surface en m²
                area_m2 = shp_transform(to_l93, poly).area
                if area_m2 < friches_min_area:
                    surfaces_rejetees += 1
                    continue

                # Calcul de la distance aux postes BT/HTA
                cent = poly.centroid.coords[0]
                d_bt = calculate_min_distance(cent, postes_bt_data)
                d_hta = calculate_min_distance(cent, postes_hta_data)

                # Logique de filtrage portée par le type de poste sélectionné (Tous/BT/HTA)
                bt_ok = (d_bt is not None and d_bt <= max_distance_bt) if d_bt is not None else False
                hta_ok = (d_hta is not None and d_hta <= max_distance_hta) if d_hta is not None else False
                if filter_by_distance:
                    if poste_type_filter == "BT":
                        distance_ok = bt_ok
                    elif poste_type_filter == "HTA":
                        distance_ok = hta_ok
                    else:  # ALL
                        distance_ok = bt_ok or hta_ok
                else:
                    # Pas de filtrage par distance lorsque l'option n'est pas cochée
                    distance_ok = True
                if not distance_ok:
                    distances_rejetees += 1
                    continue

                # Enrichissement des propriétés
                props.update({
                    "surface_m2": round(area_m2, 2),
                    "min_distance_bt_m": round(d_bt, 2) if d_bt is not None else None,
                    "min_distance_hta_m": round(d_hta, 2) if d_hta is not None else None
                })

                # Calcul de la surface libre si demandé
                if calculate_surface_libre:
                    try:
                        # print(f"[SURFACE_LIBRE] Calcul pour friche...")  # Optimisé pour performance
                        batiments_data = get_batiments_data(feat["geometry"])
                        surface_libre_result = calculate_surface_libre_parcelle(feat["geometry"], batiments_data)
                        props.update({
                            'surface_batie_m2': surface_libre_result.get('surface_batie_m2', 0),
                            'surface_libre_m2': surface_libre_result.get('surface_libre_m2', 0),
                            'surface_libre_pct': surface_libre_result.get('surface_libre_pct', 0),
                            'batiments_count': surface_libre_result.get('batiments_count', 0)
                        })
                    except Exception as e:
                        # print(f"[SURFACE_LIBRE] Erreur friche: {e}")  # Optimisé pour performance
                        props['surface_libre_error'] = str(e)

                filtered_friches.append({
                    "type": "Feature",
                    "geometry": feat["geometry"],
                    "properties": props
                })
            except Exception as e:
                # print(f"Erreur filtrage friche: {e}")  # Optimisé pour performance
                continue
        
        # Log détaillé des résultats de filtrage
        log_data_collection("FILTRAGE FRICHES", 
                          f"✅ {len(filtered_friches)} retenues / {len(friches_data)} analysées")
        log_data_collection("FILTRAGE FRICHES", 
                          f"❌ Rejetées: {surfaces_rejetees} (surface), {distances_rejetees} (distance)")
        # print(f"[FRICHES] {len(filtered_friches)} friches trouvées après filtrage")  # Optimisé pour performance
        
        # 5c-bis) Récupération optimisée des références cadastrales pour les friches sélectionnées
        if filtered_friches:
            # print(f"🏛️ [CADASTRE-FRICHES] Récupération des références cadastrales pour {len(filtered_friches)} friches...")  # Optimisé pour production multi-user
            
            def get_parcelles_for_friche(friche_geometry):
                """Récupère les parcelles cadastrales intersectant une friche spécifique"""
                try:
                    api_url = "https://apicarto.ign.fr/api/cadastre/parcelle"
                    params = {
                        "geom": json.dumps(friche_geometry),
                        "_limit": 100  # Limite raisonnable pour une friche
                    }
                    
                    resp = requests.get(api_url, params=params, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        return data.get('features', [])
                    else:
                        # print(f"Erreur API cadastre: {resp.status_code}")  # Optimisé pour performance
                        return []
                except Exception as e:
                    # print(f"Exception cadastre friche: {e}")  # Optimisé pour performance
                    return []
            
            # Enrichir chaque friche avec ses références cadastrales
            for i, friche in enumerate(filtered_friches):
                # print(f"Friche {i+1}/{len(filtered_friches)}: recherche cadastre...")  # Optimisé pour performance
                parcelles_friche = get_parcelles_for_friche(friche["geometry"])
                
                if parcelles_friche:
                    # Extraire les références cadastrales
                    refs_cadastrales = []
                    for parcelle in parcelles_friche:
                        props = parcelle.get('properties', {})
                        ref = {
                            'numero': props.get('numero', ''),
                            'section': props.get('section', ''),
                            'commune': props.get('commune', ''),
                            'prefixe': props.get('prefixe', ''),
                            'reference_complete': f"{props.get('commune', '')}{props.get('prefixe', '')}{props.get('section', '')}{props.get('numero', '')}"
                        }
                        refs_cadastrales.append(ref)
                    
                    # Ajouter aux propriétés de la friche
                    friche["properties"]["parcelles_cadastrales"] = refs_cadastrales
                    friche["properties"]["nb_parcelles_cadastrales"] = len(refs_cadastrales)
                    # print(f"{len(refs_cadastrales)} parcelles cadastrales trouvées")  # Optimisé pour performance
                else:
                    friche["properties"]["parcelles_cadastrales"] = []
                    friche["properties"]["nb_parcelles_cadastrales"] = 0
                    # print(f"Aucune parcelle cadastrale trouvée")  # Optimisé pour performance
            
            # print(f"[CADASTRE-FRICHES] Enrichissement terminé pour toutes les friches")  # Optimisé pour performance
    
    # 5d) Filtrage optimisé des zones avec croisement parcelles
    filtered_zones = []
    filtered_parcelles_in_zones = []
    
    if filter_zones:
        log_data_collection("ZONES PLU", f"🎯 Début filtrage zones: type={zones_type_filter or 'toutes'}, surface min={zones_min_area}m²")
        # print(f"[ZONES OPTIMISÉ] Recherche zones {zones_type_filter or 'toutes'} + parcelles >{zones_min_area}m²")  # Optimisé pour performance
        
        # Utiliser l'API GPU pour récupérer les zones autour du centre de la commune
        def get_zones_around_commune(lat, lon, radius_km=2.0):
            api_url = "https://apicarto.ign.fr/api/gpu/zone-urba"
            
            # Créer un polygone autour du centre de commune
            delta = radius_km / 111.0  # Conversion km -> degrés
            bbox_geojson = {
                "type": "Polygon",
                "coordinates": [[
                    [lon - delta, lat - delta],
                    [lon + delta, lat - delta],
                    [lon + delta, lat + delta],
                    [lon - delta, lat + delta],
                    [lon - delta, lat - delta]
                ]]
            }
            
            params = {
                "geom": json.dumps(bbox_geojson),
                "_limit": 1000
            }
            
            try:
                resp = requests.get(api_url, params=params, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get('features', [])
                else:
                    # print(f"Erreur API GPU zones: {resp.status_code}")  # Optimisé pour performance
                    return []
            except Exception as e:
                # print(f"Exception API GPU zones: {e}")  # Optimisé pour performance
                return []
        
        # Récupérer les parcelles dans une zone donnée - OPTIMISÉ
        def get_parcelles_in_zone(zone_feature):
            api_url = "https://apicarto.ign.fr/api/cadastre/parcelle"
            zone_geom = zone_feature.get('geometry')
            
            if not zone_geom:
                return []
            
            params = {
                "geom": json.dumps(zone_geom)
                # Limite retirée pour analyse complète de la commune
            }
            
            try:
                resp = requests.get(api_url, params=params, timeout=60)  # Timeout augmenté pour traitement complet
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get('features', [])
                else:
                    # 414 = URI trop longue, zone trop grande
                    if resp.status_code == 414:
                        # print(f"Zone trop grande (414), passage au suivant")  # Optimisé pour performance
                        pass
                    return []
            except Exception as e:
                # print(f"Exception parcelles: {e}")  # Optimisé pour performance
                return []
        
        # 1. Récupérer toutes les zones autour de la commune
        all_zones = get_zones_around_commune(lat, lon, radius_km=3.0)
        log_data_collection("ZONES PLU", f"📍 {len(all_zones)} zones trouvées dans un rayon de 3km")
        # print(f"{len(all_zones)} zones trouvées autour de la commune")  # Optimisé pour performance
        
        # 2. Filtrer par type de zone
        target_zones = []
        for zone in all_zones:
            props = zone.get('properties', {})
            zone_type = props.get('typezone', '')
            
            # Filtrage par type si spécifié
            if zones_type_filter and not zone_type.upper().startswith(zones_type_filter.upper()):
                continue
            
            target_zones.append(zone)
        
        log_data_collection("ZONES PLU", f"🎯 {len(target_zones)} zones de type '{zones_type_filter or 'toutes'}' sélectionnées")
        # print(f"{len(target_zones)} zones de type '{zones_type_filter or 'toutes'}' sélectionnées")  # Optimisé pour performance
        
        # 3. Pour chaque zone cible, récupérer et filtrer les parcelles
        total_parcelles_trouvees = 0
        
        for i, zone in enumerate(target_zones):
            props = zone.get('properties', {})
            zone_libelle = props.get('libelle', f"Zone_{i}")
            
            # print(f"Zone {i+1}/{len(target_zones)}: {props.get('typezone', 'N/A')} - {zone_libelle}")  # Optimisé pour performance
            
            # Récupérer les parcelles de cette zone
            parcelles = get_parcelles_in_zone(zone)
            
            if not parcelles:
                continue
            
            # print(f"{len(parcelles)} parcelles trouvées")  # Optimisé pour performance
            
            # Filtrer par surface
            parcelles_grandes = []
            for parcelle in parcelles:
                geometry = parcelle.get('geometry')
                if not geometry:
                    continue
                
                # Calcul surface en m²
                try:
                    area_m2 = shp_transform(to_l93, shape(geometry)).area
                except Exception:
                    continue
                
                if area_m2 >= zones_min_area:
                    parcelle_props = parcelle.get('properties', {})
                    
                    # Calculer systématiquement les distances aux postes et la superficie
                    min_distance_bt = None
                    min_distance_hta = None
                    min_distance_total = None
                    
                    # Nouvelles variables pour les distances aux lignes HTA
                    min_distance_hta_aerial = None
                    min_distance_hta_underground = None
                    
                    try:
                        # Calculer le centroïde de la parcelle
                        centroid = shape(geometry).centroid.coords[0]
                        
                        # Calculer les distances minimales aux postes
                        min_distance_bt = calculate_min_distance(centroid, postes_bt_data)
                        min_distance_hta = calculate_min_distance(centroid, postes_hta_data)
                        
                        # Calculer les distances minimales aux lignes HTA
                        if hta_lignes_data and isinstance(hta_lignes_data, dict):
                            # Lignes aériennes
                            if 'aerienne' in hta_lignes_data and hta_lignes_data['aerienne'].get('features'):
                                min_distance_hta_aerial = calculate_min_distance_to_lines(
                                    centroid, hta_lignes_data['aerienne']['features']
                                )
                                # print(f"[HTA DEBUG] Distance aérienne calculée: {min_distance_hta_aerial}m")  # Optimisé pour performance
                            else:
                                # print(f"[HTA DEBUG] Pas de lignes aériennes disponibles")  # Optimisé pour performance
                                pass
                            
                            # Lignes souterraines
                            if 'souterraine' in hta_lignes_data and hta_lignes_data['souterraine'].get('features'):
                                min_distance_hta_underground = calculate_min_distance_to_lines(
                                    centroid, hta_lignes_data['souterraine']['features']
                                )
                                # print(f"[HTA DEBUG] Distance souterraine calculée: {min_distance_hta_underground}m")  # Optimisé pour performance
                            else:
                                # print(f"[HTA DEBUG] Pas de lignes souterraines disponibles")  # Optimisé pour performance
                                pass
                        else:
                            # print(f"[HTA DEBUG] hta_lignes_data non disponible: {type(hta_lignes_data)}")  # Optimisé pour performance
                            pass
                        
                        # Distance minimale globale (le poste le plus proche, qu'il soit BT ou HTA)
                        distances = [d for d in [min_distance_bt, min_distance_hta] if d is not None]
                        min_distance_total = min(distances) if distances else None
                        
                    except Exception as e:
                        # print(f"Erreur calcul distances: {e}")  # Optimisé pour performance
                        pass
                    
                    # Calcul des distances aux postes si le filtrage par distance est activé
                    distance_ok = True
                    
                    if filter_by_distance:
                        try:
                            # Appliquer la logique de filtrage selon le type de poste
                            if poste_type_filter == "BT":
                                # Seulement les postes BT
                                distance_ok = (min_distance_bt is not None and min_distance_bt <= max_distance_bt)
                            elif poste_type_filter == "HTA":
                                # Seulement les postes HTA
                                distance_ok = (min_distance_hta is not None and min_distance_hta <= max_distance_hta)
                            else:  # ALL (par défaut)
                                # Considérer les deux types de postes
                                bt_ok = (min_distance_bt is not None and min_distance_bt <= max_distance_bt)
                                hta_ok = (min_distance_hta is not None and min_distance_hta <= max_distance_hta)
                                
                                # Par défaut, en mode "Tous", on accepte si BT OU HTA est proche
                                distance_ok = bt_ok or hta_ok
                                
                        except Exception as e:
                            # print(f"Erreur calcul distance: {e}")  # Optimisé pour performance
                            distance_ok = True  # En cas d'erreur, on garde la parcelle
                    
                    # Filtrage additionnel par distance aux lignes HTA (même logique que les postes)
                    hta_lines_distance_ok = True
                    
                    # Appliquer le filtrage HTA lignes seulement si activé par les checkboxes
                    if filter_hta_lines_aerial or filter_hta_lines_underground:
                        try:
                            aerial_ok = True
                            underground_ok = True
                            
                            # Vérifier les lignes aériennes si le filtre est activé
                            if filter_hta_lines_aerial:
                                max_distance_aerial_m = hta_aerial_max_km * 1000
                                aerial_ok = (min_distance_hta_aerial is not None and min_distance_hta_aerial <= max_distance_aerial_m)
                                # print(f"[HTA AERIAL] Distance: {min_distance_hta_aerial}m, Max: {max_distance_aerial_m}m, OK: {aerial_ok}")  # Optimisé pour performance
                            
                            # Vérifier les lignes souterraines si le filtre est activé
                            if filter_hta_lines_underground:
                                max_distance_underground_m = hta_underground_max_km * 1000
                                underground_ok = (min_distance_hta_underground is not None and min_distance_hta_underground <= max_distance_underground_m)
                                # print(f"[HTA UNDERGROUND] Distance: {min_distance_hta_underground}m, Max: {max_distance_underground_m}m, OK: {underground_ok}")  # Optimisé pour performance
                            
                            # Si les deux filtres sont activés, il faut que les deux soient OK
                            # Si un seul filtre est activé, il faut juste que celui-ci soit OK
                            if filter_hta_lines_aerial and filter_hta_lines_underground:
                                hta_lines_distance_ok = aerial_ok and underground_ok
                                # print(f"[HTA BOTH] Final OK: {hta_lines_distance_ok} (aerial: {aerial_ok}, underground: {underground_ok})")  # Optimisé pour performance
                            elif filter_hta_lines_aerial:
                                hta_lines_distance_ok = aerial_ok
                                # print(f"[HTA AERIAL ONLY] Final OK: {hta_lines_distance_ok}")  # Optimisé pour performance
                            elif filter_hta_lines_underground:
                                hta_lines_distance_ok = underground_ok
                                # print(f"[HTA UNDERGROUND ONLY] Final OK: {hta_lines_distance_ok}")  # Optimisé pour performance
                                
                        except Exception as e:
                            # print(f"Erreur calcul distance lignes HTA: {e}")  # Optimisé pour performance
                            hta_lines_distance_ok = True  # En cas d'erreur, on garde la parcelle
                    
                    # Condition finale : respecter les deux types de filtres
                    if not distance_ok or not hta_lines_distance_ok:
                        # if not distance_ok:
                        #     print(f"[RPG REJECTED] Parcelle rejetée - distance postes: {distance_ok}")  # Optimisé pour performance
                        # if not hta_lines_distance_ok:
                        #     print(f"[RPG REJECTED] Parcelle rejetée - distance lignes HTA: {hta_lines_distance_ok}")  # Optimisé pour performance
                        continue
                    
                    # Enrichir les propriétés avec les informations systématiques
                    parcelle_props.update({
                        'surface_m2': round(area_m2, 2),
                        'surface_ha': round(area_m2 / 10000, 4),
                        'zone_typezone': props.get('typezone', 'N/A'),
                        'zone_libelle': zone_libelle,
                        'zone_filter_applied': zones_type_filter or 'toutes',
                        # Distances systématiques
                        'min_distance_bt_m': round(min_distance_bt, 2) if min_distance_bt is not None else None,
                        'min_distance_hta_m': round(min_distance_hta, 2) if min_distance_hta is not None else None,
                        'min_distance_total_m': round(min_distance_total, 2) if min_distance_total is not None else None,
                        # Distances aux lignes HTA
                        'min_distance_hta_aerial_m': round(min_distance_hta_aerial, 2) if min_distance_hta_aerial is not None else None,
                        'min_distance_hta_underground_m': round(min_distance_hta_underground, 2) if min_distance_hta_underground is not None else None
                    })
                    
                    # Calcul de la surface libre si demandé
                    if calculate_surface_libre:
                        try:
                            # print(f"[SURFACE_LIBRE] Calcul pour parcelle {parcelle_props.get('numero', 'N/A')}...")  # Optimisé pour performance
                            
                            # Récupérer les bâtiments sur cette parcelle
                            batiments_data = get_batiments_data(geometry)
                            
                            # Calculer la surface libre
                            surface_libre_result = calculate_surface_libre_parcelle(geometry, batiments_data)
                            
                            # Ajouter les résultats aux propriétés
                            parcelle_props.update({
                                'surface_totale_calculee_m2': surface_libre_result.get('surface_totale_m2', 0),
                                'surface_batie_m2': surface_libre_result.get('surface_batie_m2', 0),
                                'surface_libre_m2': surface_libre_result.get('surface_libre_m2', 0),
                                'surface_libre_pct': surface_libre_result.get('surface_libre_pct', 0),
                                'batiments_count': surface_libre_result.get('batiments_count', 0),
                                'surface_libre_calculee': True
                            })
                            
                            if surface_libre_result.get('error'):
                                parcelle_props['surface_libre_error'] = surface_libre_result['error']
                                
                        except Exception as e:
                            # print(f"[SURFACE_LIBRE] Erreur calcul pour parcelle: {e}")  # Optimisé pour performance
                            parcelle_props.update({
                                'surface_libre_calculee': False,
                                'surface_libre_error': str(e)
                            })
                    
                    # Ajouter les distances si calculées
                    if filter_by_distance:
                        distance_filter_desc = f"Type: {poste_type_filter}"
                        if poste_type_filter == "BT":
                            distance_filter_desc += f", BT<{max_distance_bt}m"
                            parcelle_props.update({
                                'min_distance_bt_m': round(min_distance_bt, 2) if min_distance_bt is not None else None,
                                'distance_filter_applied': distance_filter_desc
                            })
                        elif poste_type_filter == "HTA":
                            distance_filter_desc += f", HTA<{max_distance_hta}m"
                            parcelle_props.update({
                                'min_distance_hta_m': round(min_distance_hta, 2) if min_distance_hta is not None else None,
                                'distance_filter_applied': distance_filter_desc
                            })
                        else:  # ALL
                            distance_filter_desc += f", BT<{max_distance_bt}m OU HTA<{max_distance_hta}m"
                            parcelle_props.update({
                                'min_distance_bt_m': round(min_distance_bt, 2) if min_distance_bt is not None else None,
                                'min_distance_hta_m': round(min_distance_hta, 2) if min_distance_hta is not None else None,
                                'distance_filter_applied': distance_filter_desc
                            })
                    
                    parcelles_grandes.append({
                        "type": "Feature",
                        "geometry": geometry,
                        "properties": parcelle_props
                    })
            
            # print(f"{len(parcelles_grandes)} parcelles >{zones_min_area}m²")  # Optimisé pour performance
            total_parcelles_trouvees += len(parcelles_grandes)
            filtered_parcelles_in_zones.extend(parcelles_grandes)
            
            # Ajouter la zone aux zones filtrées (pour affichage)
            try:
                zone_area_m2 = shp_transform(to_l93, shape(zone.get('geometry'))).area
                zone_props_enriched = props.copy()
                zone_props_enriched.update({
                    'surface_m2': round(zone_area_m2, 2),
                    'surface_ha': round(zone_area_m2 / 10000, 4),
                    'parcelles_count': len(parcelles_grandes)
                })
                
                filtered_zones.append({
                    "type": "Feature",
                    "geometry": zone.get('geometry'),
                    "properties": zone_props_enriched
                })
            except Exception:
                pass
        
        log_data_collection("FILTRAGE ZONES", f"✅ {len(target_zones)} zones analysées")
        log_data_collection("FILTRAGE ZONES", f"✅ {total_parcelles_trouvees} parcelles retenues (>{zones_min_area}m²)")
        log_data_collection("FILTRAGE ZONES", f"✅ {len(filtered_zones)} zones avec parcelles qualifiées")
        # print(f"[ZONES OPTIMISÉ] {len(target_zones)} zones analysées, {total_parcelles_trouvees} parcelles trouvées")  # Optimisé pour performance

    # Utiliser les zones optimisées pour plu_info, sinon fallback
    plu_info = filtered_zones if filtered_zones else plu_info_temp

    # 6) Carte interactive
    # PPRI récupération via la nouvelle fonction GeoRisques unifiée
    def fetch_ppri_georisques(lat, lon, rayon_km=1.0):
        # Utilise maintenant la nouvelle fonction unifiée
        # print(f"[PPRI] Utilisation des données GeoRisques unifiées")  # Optimisé pour performance
        return {"type": "FeatureCollection", "features": []}

    # On ne garde que les polygones qui contiennent le point exact
    raw_ppri = fetch_ppri_georisques(lat, lon, rayon_km=1.0)
    pt = Point(lon, lat)
    filtered_features = [f for f in raw_ppri.get("features", []) if f.get("geometry") and shape(f["geometry"]).contains(pt)]
    ppri_data = {"type": "FeatureCollection", "features": filtered_features}
    
    # Initialisation parcelles_data pour la carte (pas utilisé avec la nouvelle logique optimisée)
    parcelles_data = {"type": "FeatureCollection", "features": []}
    
    # 6b) Traitement des toitures si demandé - Nouvelle méthode basée sur le polygone de la commune (utilise sliders unifiés)
    toitures_data = []
    if filter_toitures:
        # print(f"[TOITURES] Recherche activée - utilisation du polygone de la commune")  # Optimisé pour performance
        # print(f"[TOITURES] Postes disponibles - BT: {len(postes_bt_data)}, HTA: {len(postes_hta_data)}")  # Optimisé pour performance
        try:
            from shapely.geometry import mapping, Point
            from shapely.ops import transform as shp_transform
            from pyproj import Transformer

            # Définir la transformation vers Lambert 93 pour le calcul des surfaces
            to_l93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True).transform

            # Utiliser le contour exact de la commune au lieu d'un rayon
            search_geom_geojson = contour

            # Utiliser la fonction existante get_batiments_data avec le polygone de la commune
            batiments_features = get_batiments_data(search_geom_geojson)
            batiments_data = batiments_features.get("features", []) if batiments_features else []
            # print(f"🏠 [TOITURES] {len(batiments_data)} bâtiments récupérés dans la commune")  # Optimisé pour performance

            # ANALYSE COMPLÈTE: Traitement de tous les bâtiments de la commune
            # print(f"[TOITURES] Analyse complète de tous les {len(batiments_data)} bâtiments")  # Optimisé pour performance
            # print(f"[TOITURES] Traitement complet activé pour une analyse exhaustive")  # Optimisé pour performance

            # Filtrer et enrichir les toitures avec intersection géométrique précise
            for idx, batiment in enumerate(batiments_data):
                try:
                    geom = shape(batiment["geometry"])
                    if not geom.is_valid:
                        geom = geom.buffer(0)
                        if not geom.is_valid:
                            continue

                    # Vérifier que le bâtiment est bien dans la commune (double filtrage)
                    if not (commune_poly.contains(geom) or commune_poly.intersects(geom)):
                        continue

                    # Calculer la surface
                    surface_m2 = shp_transform(to_l93, geom).area
                    if surface_m2 < toitures_min_surface:
                        continue

                    # Calculer les distances aux postes
                    centroid = geom.centroid.coords[0]
                    d_bt = calculate_min_distance(centroid, postes_bt_data) if postes_bt_data else None
                    d_hta = calculate_min_distance(centroid, postes_hta_data) if postes_hta_data else None

                    # Logique de filtrage portée par le type de poste sélectionné (Tous/BT/HTA)
                    bt_ok = (d_bt is not None and d_bt <= max_distance_bt) if d_bt is not None else False
                    hta_ok = (d_hta is not None and d_hta <= max_distance_hta) if d_hta is not None else False
                    if filter_by_distance:
                        if poste_type_filter == "BT":
                            distance_ok = bt_ok
                        elif poste_type_filter == "HTA":
                            distance_ok = hta_ok
                        else:  # ALL
                            distance_ok = bt_ok or hta_ok
                    else:
                        # Pas de filtrage par distance lorsque l'option n'est pas cochée
                        distance_ok = True
                    if not distance_ok:
                        continue

                    # Ajouter à la liste filtrée (enrichissement cadastral sera fait après)
                    toitures_data.append({
                        "type": "Feature",
                        "geometry": batiment["geometry"],
                        "properties": {
                            "surface_toiture_m2": round(surface_m2, 2),
                            "min_distance_bt_m": round(d_bt, 2) if d_bt else None,
                            "min_distance_hta_m": round(d_hta, 2) if d_hta else None,
                            "commune": commune,
                            "search_method": "polygon_commune",
                            "source": "OpenStreetMap",
                            "building": batiment.get("properties", {}).get("building", "yes"),
                            "osm_id": batiment.get("properties", {}).get("osm_id"),
                            # Liens utiles
                            "lien_streetview": f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={centroid[1]},{centroid[0]}",
                            "lien_annuaire": f"https://www.pagesjaunes.fr/annuaire/chercherlespros?quoiqui=&ou={quote_plus(commune)}&univers=pagesjaunes&idOu="
                        }
                    })

                except Exception as e:
                    print(f"⚠️ [TOITURES] Erreur traitement bâtiment {idx}: {e}")
                    continue

            print(f"✅ [TOITURES] {len(toitures_data)} toitures filtrées trouvées (méthode polygone)")
            
            # Enrichissement cadastral OPTIMISÉ avec limite intelligente
            if toitures_data:
                # OPTIMISATION PERFORMANCE: Toutes les toitures sont enrichies
                # Note: Peut être lent pour les grandes communes (>500 toitures)
                toitures_a_enrichir = toitures_data  # Toutes les toitures
                
                print(f"🏛️ [CADASTRE-TOITURES] Enrichissement optimisé : {len(toitures_a_enrichir)} toitures")
                print(f"🔍 [CADASTRE-TOITURES] Traitement individuel avec timeout réduit")
                
                def get_parcelles_for_toiture(toiture_geometry):
                    """Récupère les parcelles cadastrales intersectant une toiture spécifique avec limite optimisée"""
                    try:
                        api_url = "https://apicarto.ign.fr/api/cadastre/parcelle"
                        params = {
                            "geom": json.dumps(toiture_geometry),
                            "_limit": 5  # Limite réduite pour plus de rapidité
                        }
                        
                        resp = requests.get(api_url, params=params, timeout=3)  # Timeout réduit
                        if resp.status_code == 200:
                            data = resp.json()
                            return data.get('features', [])
                        else:
                            return []
                    except Exception:
                        return []
                
                # Traitement individuel mais optimisé
                total_enrichies = 0
                total_erreurs = 0
                
                for i, toiture in enumerate(toitures_a_enrichir):
                    # Log de progression moins verbeux - seulement chaque 100
                    if (i + 1) % 100 == 0 or i == 0:
                        # print(f"    📍 Progression: {i+1}/{len(toitures_a_enrichir)} toitures traitées...")  # Optimisé pour production multi-user
                        pass
                    
                    # 1. Enrichissement cadastral
                    parcelles_toiture = get_parcelles_for_toiture(toiture["geometry"])
                    
                    if parcelles_toiture:
                        # Extraire les références cadastrales
                        refs_cadastrales = []
                        for parcelle in parcelles_toiture:
                            props = parcelle.get('properties', {})
                            
                            numero = props.get('numero', '')
                            section = props.get('section', '')
                            commune_code = props.get('commune', '')
                            prefixe = props.get('prefixe', '')
                            
                            if section and numero:
                                ref = {
                                    'numero': numero,
                                    'section': section,
                                    'commune': commune_code,
                                    'prefixe': prefixe,
                                    'reference_complete': f"{commune_code}{prefixe}{section}{numero}".strip()
                                }
                                refs_cadastrales.append(ref)
                        
                        toiture["properties"]["parcelles_cadastrales"] = refs_cadastrales
                        toiture["properties"]["nb_parcelles_cadastrales"] = len(refs_cadastrales)
                        total_enrichies += 1
                    else:
                        toiture["properties"]["parcelles_cadastrales"] = []
                        toiture["properties"]["nb_parcelles_cadastrales"] = 0
                        total_erreurs += 1
                    
                    # 2. Enrichissement avec l'adresse IGN (géocodage inverse)
                    geom = toiture.get("geometry", {})
                    if geom and geom.get("type") in ["Polygon", "MultiPolygon"]:
                        try:
                            # Calculer le centroïde de la toiture pour obtenir lat/lon
                            from shapely.geometry import shape
                            shp_geom = shape(geom)
                            centroid = shp_geom.centroid
                            
                            # Géocodage inverse IGN
                            adresse_info = get_address_from_coordinates(centroid.y, centroid.x)
                            
                            if adresse_info and adresse_info.get('address'):
                                toiture["properties"]["adresse"] = adresse_info['address']
                                toiture["properties"]["adresse_distance"] = adresse_info.get('distance', 0)
                                toiture["properties"]["adresse_score"] = adresse_info.get('score', 0)
                                toiture["properties"]["code_postal"] = adresse_info.get('postcode', '')
                                toiture["properties"]["ville"] = adresse_info.get('city', '')
                                toiture["properties"]["code_commune"] = adresse_info.get('citycode', '')
                                # Mettre à jour le lien annuaire avec la ville si disponible
                                try:
                                    ville = adresse_info.get('city', '') or commune
                                    toiture["properties"]["lien_annuaire"] = f"https://www.pagesjaunes.fr/annuaire/chercherlespros?quoiqui=&ou={quote_plus(ville)}&univers=pagesjaunes&idOu="
                                except Exception:
                                    pass
                            else:
                                toiture["properties"]["adresse"] = "Adresse non trouvée"
                                toiture["properties"]["adresse_distance"] = None
                                toiture["properties"]["adresse_score"] = 0
                        except Exception as e:
                            safe_print(f"🔴 [ADRESSE] Erreur enrichissement toiture {i}: {e}")
                            toiture["properties"]["adresse"] = "Erreur géocodage"
                
                # print(f"[CADASTRE-TOITURES] Enrichissement individuel optimisé terminé:")  # Optimisé pour performance
                # print(f"{total_enrichies} toitures enrichies avec succès")  # Optimisé pour performance
                # print(f"{total_erreurs} toitures sans données cadastrales")  # Optimisé pour performance
                # print(f"{len(toitures_data)} toitures disponibles au total sur la carte")  # Optimisé pour performance
            
        except Exception as e:
            # print(f"[TOITURES] Erreur recherche: {e}")  # Optimisé pour performance
            import traceback
            traceback.print_exc()
            toitures_data = []
    
    # Optimisé pour performance
    # print(f"🗺️ [BUILD_MAP] Appel avec {len(filtered_parkings)} parkings, {len(filtered_friches)} friches et {len(toitures_data)} toitures")
    # print(f"🌾 [DEBUG_RPG] Parcelles RPG passées à build_map: {len(final_rpg)}")
    
    # Optimisé pour performance
    # print(f"🎯 [DEBUG] AVANT appel build_map...")
    
    try:
        map_obj = build_map(
            lat, lon, commune,
            parcelle_props={}, parcelles_data=parcelles_data,
            postes_data=postes_bt_data,
            ht_postes_data=postes_hta_data,
            plu_info=plu_info,
            parkings_data=filtered_parkings,
            friches_data=filtered_friches,
            potentiel_solaire_data=toitures_data if filter_toitures else solaire_data,  # Remplacer temporairement par les toitures
            zaer_data=zaer_data,
            rpg_data=final_rpg,
            sirene_data=sirene_data,
            search_radius=0.1,
            ht_radius_deg=ht_max_km/111.0,
            api_cadastre=api_cadastre,
            api_nature=api_nature,
            api_urbanisme=api_urbanisme,
            eleveurs_data=eleveurs_data,
            ppri_data=ppri_data,
            hta_lignes_data=hta_lignes_data  # Ajout des lignes HTA
        )
        # Optimisé pour performance
        # print(f"🎯 [DEBUG] APRÈS appel build_map - Résultat: {type(map_obj)} / {map_obj is not None}")
        
    except Exception as e:
        # print(f"[ERREUR] Exception dans build_map: {str(e)}")  # Optimisé pour performance
        # print(f"[ERREUR] Type d'erreur: {type(e)}")  # Optimisé pour performance
        import traceback
        # print(f"[ERREUR] Traceback: {traceback.format_exc()}")  # Optimisé pour performance
        traceback.print_exc()
        map_obj = None
    
    # ⚠️ Ne plus générer carte_html (inutile et très lourd)
    # carte_html = map_obj._repr_html_() if map_obj else ""
    
    # Sauvegarder la carte comme dans rapport_commune qui fonctionne
    carte_url = None
    if map_obj:
        from datetime import datetime
        import glob
        
        # 🧹 NETTOYAGE: Supprimer les anciennes cartes de cette commune
        cartes_dir = os.path.join(os.path.dirname(__file__), "static", "cartes")
        commune_clean = clean_filename(commune, max_length=30)
        
        # Rechercher toutes les cartes existantes pour cette commune
        pattern = os.path.join(cartes_dir, f"commune_{commune_clean}_*.html")
        old_maps = glob.glob(pattern)
        
        if old_maps:
            # print(f"🧹 [CLEANUP] Suppression de {len(old_maps)} ancienne(s) carte(s) pour {commune}")  # Optimisé pour performance
            for old_map in old_maps:
                try:
                    os.remove(old_map)
                    print(f"   ✓ Supprimé: {os.path.basename(old_map)}")
                except Exception as e:
                    print(f"   ⚠️ Erreur suppression {os.path.basename(old_map)}: {e}")
        
        # 🔒 Utilisation du nom de fichier sécurisé avec UUID
        carte_filename = generate_secure_filename("commune", commune)
        carte_path = save_map_html(map_obj, carte_filename)
        carte_url = carte_path  # Utiliser directement le chemin retourné
        print(f"✅ [CARTE] Carte sauvegardée: {carte_path}, carte_url: {carte_url}")
    else:
        print(f"❌ [DEBUG] map_obj est None - carte non générée")

    # Ajouter _layer aux éleveurs pour la détection côté client
    eleveurs_with_layer = []
    for eleveur in eleveurs_data:
        if eleveur.get("properties"):
            eleveur["properties"]["_layer"] = "eleveurs"
        eleveurs_with_layer.append(eleveur)
    
    # 7) Réponse JSON avec données filtrées
    # print(f"🔧 [DEBUG_RPG_PARCELLES] Création response_data avec filter_rpg={filter_rpg}, final_rpg count={len(final_rpg) if final_rpg else 0}")
    response_data = {
        "lat": lat, "lon": lon,
        "rpg": final_rpg if filter_rpg else [],
        "rpg_parcelles": {"type": "FeatureCollection", "features": final_rpg} if filter_rpg else {"type": "FeatureCollection", "features": []},
        "eleveurs": eleveurs_with_layer,
        "postes_bt": postes_bt_data,
        "postes_hta": postes_hta_data,
        "hta_lignes": hta_lignes_data,  # Ajout des lignes HTA pour le frontend
        "parcelles": parcelles_data,
        "api_cadastre": api_cadastre,
        "api_nature": api_nature,
        "api_urbanisme": api_urbanisme,
        "plu": filtered_zones if filter_zones else plu_info,
        "parkings": {"type": "FeatureCollection", "features": filtered_parkings} if filter_parkings else {"type": "FeatureCollection", "features": []},
        "friches": {"type": "FeatureCollection", "features": filtered_friches} if filter_friches else {"type": "FeatureCollection", "features": []},
        "toitures": {"type": "FeatureCollection", "features": toitures_data} if filter_toitures else {"type": "FeatureCollection", "features": []},
        "parcelles_in_zones": {"type": "FeatureCollection", "features": filtered_parcelles_in_zones},
        "solaire": toitures_data if filter_toitures else solaire_data,
        "zaer": zaer_data,
        "sirene": sirene_data,
        # ⚠️ NE PAS ENVOYER carte_html - provoque freeze navigateur (154MB!)
        # "carte_html": carte_html,  # ❌ DÉSACTIVÉ - trop volumineux
        "carte_url": carte_url,    # ✅ Seule l'URL est nécessaire pour l'iframe
        # Métadonnées de filtrage
        "filters_applied": {
            "rpg": {"active": filter_rpg, "count": len(final_rpg) if filter_rpg else 0},
            "parkings": {"active": filter_parkings, "count": len(filtered_parkings) if filter_parkings else 0},
            "friches": {"active": filter_friches, "count": len(filtered_friches) if filter_friches else 0},
            "toitures": {"active": filter_toitures, "count": len(toitures_data) if filter_toitures else 0},
            "zones": {"active": filter_zones, "count": len(filtered_zones) if filter_zones else 0},
            "parcelles_in_zones": {"active": filter_zones, "count": len(filtered_parcelles_in_zones)},
            "distance_filter": {
                "active": filter_by_distance,
                "max_distance_bt": max_distance_bt if filter_by_distance else None,
                "max_distance_hta": max_distance_hta if filter_by_distance else None,
                "poste_type": poste_type_filter if filter_by_distance else None
            }
        }
    }
    
    # DEBUG: Vérifier le contenu de response_data (optimisé)
    # print(f"🔧 [DEBUG_RPG_PARCELLES] response_data créé avec clés: {list(response_data.keys())}")
    # if 'rpg_parcelles' in response_data:
    #     rpg_p = response_data['rpg_parcelles']
    #     print(f"✅ [DEBUG_RPG_PARCELLES] rpg_parcelles présent, type: {type(rpg_p)}, features: {len(rpg_p.get('features', [])) if isinstance(rpg_p, dict) else 'N/A'}")
    # else:
    #     print(f"❌ [DEBUG_RPG_PARCELLES] rpg_parcelles MANQUANT dans response_data!")
    
    # Log final détaillé des résultats de recherche
    log_search_results(commune, response_data)
    
    # Ajouter cache bust comme dans search_by_address - DIAGNOSTIC DÉTAILLÉ
    print(f"🔍 [DEBUG_FINAL] carte_url avant traitement: '{carte_url}' (type: {type(carte_url)})")
    if carte_url and "commune_" in carte_url:  # ⚠️ CORRECTION: "commune_" au lieu de "commune_map_"
        response_data["carte_url"] = f"/static/{carte_url}?t={int(time.time())}"
        print(f"✅ [DEBUG_FINAL] URL carte avec cache bust: {response_data['carte_url']}")
    elif carte_url:
        response_data["carte_url"] = f"/static/{carte_url}"
        print(f"✅ [DEBUG_FINAL] URL carte finale: {response_data['carte_url']}")
    else:
        print(f"❌ [DEBUG_FINAL] PROBLÈME: carte_url est None/vide - utilisation fallback")
        print(f"❌ [DEBUG_FINAL] Cette ligne cause le problème du pointage vers map.html statique")
        response_data["carte_url"] = "/static/map.html"
        print(f"⚠️ [DEBUG_FINAL] Fallback sur carte statique: {response_data['carte_url']}")
    
    # Sauvegarder la carte avec toutes les données de recherche pour permettre le zoom
    save_map_to_cache(map_obj, response_data)
    
    # Diagnostics de taille de réponse pour éviter les timeouts
    try:
        import json
        response_size = len(json.dumps(response_data, default=str))
        print(f"📊 [RESPONSE_SIZE] Taille de la réponse: {response_size/1024:.2f} KB")
        
        if response_size > 5 * 1024 * 1024:  # Plus de 5MB
            print(f"⚠️ [RESPONSE_SIZE] ALERTE: Réponse très volumineuse ({response_size/1024/1024:.2f} MB)")
            print(f"🔧 [OPTIMIZATION] Considérer une réduction des données pour éviter les timeouts")
            
    except Exception as e:
        print(f"❌ [RESPONSE_SIZE] Erreur calcul taille: {e}")
    
    try:
        # print(f"✅ [FINAL_RESPONSE] Retour de la réponse JSON pour {commune}")  # Optimisé pour performance
        safe_response_data = ensure_json_safe(response_data)
        response = make_response(jsonify(safe_response_data))
        return add_cors_headers(response)
    except Exception as e:
        print(f"❌ [JSONIFY_ERROR] Erreur lors de la sérialisation JSON: {e}")
        # Retour d'une réponse simplifiée en cas d'erreur
        error_response = make_response(jsonify({
            "error": "Erreur lors de la génération de la réponse",
            "commune": commune,
            "lat": lat, "lon": lon,
            "carte_url": response_data.get("carte_url", "/static/map.html")
        }), 500)
        return add_cors_headers(error_response)

@app.route("/search_toitures_commune_polygon", methods=["GET", "POST"])
def search_toitures_commune_polygon():
    """
    Recherche de toitures utilisant le polygone exact de la commune
    au lieu d'un rayon fixe pour une couverture complète
    """
    from urllib.parse import quote_plus
    from flask import request as flask_request
    from shapely.geometry import shape, Point
    from shapely.ops import transform as shp_transform
    from pyproj import Transformer
    
    print("🏠 [TOITURES POLYGON] === DÉBUT RECHERCHE PAR POLYGONE COMMUNE ===")
    
    # 1) Paramètres de la requête - Version robuste
    try:
        commune = flask_request.values.get("commune", "").strip()
    except:
        commune = ""
        
    if not commune:
        return jsonify({"error": "Veuillez fournir une commune."}), 400
    
    try:
        min_surface_toiture = float(flask_request.values.get("min_surface_toiture", 100.0))
        max_distance_bt = float(flask_request.values.get("max_distance_bt", 500.0))
        max_distance_hta = float(flask_request.values.get("max_distance_hta", 1000.0))
        max_results = int(flask_request.values.get("max_results", 100))  # Augmenté pour polygon complet
    except:
        # Valeurs par défaut en cas d'erreur
        min_surface_toiture = 100.0
        max_distance_bt = 500.0
        max_distance_hta = 1000.0
        max_results = 100

    print(f"🏠 [TOITURES POLYGON] Commune: {commune}")
    print(f"    Surface mini: {min_surface_toiture}m², max résultats: {max_results}")

    try:
        # 2) Récupération du contour exact de la commune
        commune_infos = requests.get(
            f"https://geo.api.gouv.fr/communes?nom={quote_plus(commune)}&fields=centre,contour,code,surface",
            timeout=15
        ).json()
        
        if not commune_infos or not commune_infos[0].get("contour"):
            return jsonify({"error": "Commune introuvable ou contour non disponible."}), 404
            
        info = commune_infos[0]
        contour = info["contour"]
        centre = info["centre"]
        insee = info.get("code")
        surface_commune_ha = round(info.get("surface", 0) / 10000, 2)  # m² → ha
        
        lat, lon = centre["coordinates"][1], centre["coordinates"][0]
        
        print(f"🏠 [TOITURES POLYGON] Centre: {lat:.4f}, {lon:.4f}")
        print(f"    Surface commune: {surface_commune_ha} ha, Code INSEE: {insee}")
        print(f"    Contour type: {contour['type']}")
        
        # 3) Utiliser le polygone exact de la commune
        search_polygon = contour
        
        # Calculer la bbox pour les requêtes WFS
        commune_shape = shape(contour)
        minx, miny, maxx, maxy = commune_shape.bounds
        bbox = f"{minx},{miny},{maxx},{maxy},EPSG:4326"
        
        print(f"🏠 [TOITURES POLYGON] Bbox commune: {minx:.4f},{miny:.4f},{maxx:.4f},{maxy:.4f}")
        
        # 4) Récupération des postes dans la commune
        try:
            postes_bt_raw = fetch_wfs_data(POSTE_LAYER, bbox)
            postes_hta_raw = fetch_wfs_data(HT_POSTE_LAYER, bbox)
            
            # Filtrer les postes qui sont réellement dans la commune
            postes_bt_data = []
            postes_hta_data = []
            
            for poste in postes_bt_raw:
                if poste.get("geometry"):
                    poste_point = shape(poste["geometry"])
                    if commune_shape.contains(poste_point) or commune_shape.intersects(poste_point):
                        postes_bt_data.append(poste)
            
            for poste in postes_hta_raw:
                if poste.get("geometry"):
                    poste_point = shape(poste["geometry"])
                    if commune_shape.contains(poste_point) or commune_shape.intersects(poste_point):
                        postes_hta_data.append(poste)
            
            print(f"    📍 {len(postes_bt_data)} postes BT, {len(postes_hta_data)} postes HTA dans la commune")
        except Exception as e:
            print(f"⚠️ [TOITURES POLYGON] Erreur récupération postes: {e}")
            postes_bt_data = []
            postes_hta_data = []
        
        # 5) Récupération des bâtiments dans le polygone de la commune
        print(f"🏠 [TOITURES POLYGON] Récupération bâtiments dans polygone commune...")
        batiments_data = get_batiments_data(search_polygon)
        
        if not batiments_data or not batiments_data.get("features"):
            return jsonify({
                "error": f"Aucun bâtiment trouvé dans la commune de {commune}",
                "commune": commune,
                "insee": insee,
                "lat": lat,
                "lon": lon,
                "surface_commune_ha": surface_commune_ha
            }), 404

        # print(f"📍 [TOITURES POLYGON] {len(batiments_data['features'])} bâtiments trouvés")  # Optimisé pour production multi-user

        # 6) Filtrage et enrichissement des toitures avec intersection commune
        to_l93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True).transform
        toitures_filtrees = []
        
        for i, batiment in enumerate(batiments_data["features"]):
            if "geometry" not in batiment:
                continue
                
            try:
                # Vérifier que le bâtiment est bien dans la commune
                bat_geom = shape(batiment["geometry"])
                if not bat_geom.is_valid:
                    bat_geom = bat_geom.buffer(0)
                    if not bat_geom.is_valid:
                        continue
                
                # Filtrage géographique : le bâtiment doit être dans la commune
                if not (commune_shape.contains(bat_geom) or commune_shape.intersects(bat_geom)):
                    continue
                
                # Surface en m²
                surface_m2 = shp_transform(to_l93, bat_geom).area
                
                # Filtrage par surface minimale
                if surface_m2 < min_surface_toiture:
                    continue
                
                # Calcul des distances aux postes
                centroid = bat_geom.centroid.coords[0]
                min_distance_bt = calculate_min_distance(centroid, postes_bt_data) if postes_bt_data else None
                min_distance_hta = calculate_min_distance(centroid, postes_hta_data) if postes_hta_data else None
                
                # Filtrage par distance (optionnel, car on a déjà le filtrage par commune)
                if min_distance_bt is not None and min_distance_bt > max_distance_bt and \
                   min_distance_hta is not None and min_distance_hta > max_distance_hta:
                    continue
                
                # Enrichissement des propriétés
                props = batiment.get("properties", {}).copy()
                props.update({
                    "surface_toiture_m2": round(surface_m2, 2),
                    "min_distance_bt_m": round(min_distance_bt, 2) if min_distance_bt is not None else None,
                    "min_distance_hta_m": round(min_distance_hta, 2) if min_distance_hta is not None else None,
                    "commune": commune,
                    "insee": insee,
                    "search_method": "polygon_commune"
                })
                
                toitures_filtrees.append({
                    "type": "Feature",
                    "geometry": batiment["geometry"],
                    "properties": props
                })
                
                # Limitation pendant le traitement
                if len(toitures_filtrees) >= max_results:
                    break
                    
            except Exception as e:
                continue

        print(f"✅ [TOITURES POLYGON] {len(toitures_filtrees)} toitures filtrées dans la commune")

        # Ajouter liens hypertextes utiles aux toitures (Street View et Annuaire)
        try:
            for f in toitures_filtrees:
                try:
                    geom = f.get("geometry")
                    from shapely.geometry import shape as _shape
                    c = _shape(geom).centroid
                    f.setdefault("properties", {})
                    f["properties"]["lien_streetview"] = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={c.y},{c.x}"
                    f["properties"]["lien_annuaire"] = f"https://www.pagesjaunes.fr/annuaire/chercherlespros?quoiqui=&ou={quote_plus(commune)}&univers=pagesjaunes&idOu="
                except Exception:
                    continue
        except Exception:
            pass

        # 7) Récupération des parcelles pour les toitures trouvées
        print(f"🏠 [TOITURES POLYGON] Récupération des parcelles pour les toitures...")
        parcelles_toitures = []
        
        if toitures_filtrees:
            try:
                # Récupérer les parcelles dans le polygone de la commune
                parcelles_data = get_api_cadastre_data(search_polygon, endpoint="/cadastre/parcelle", source_ign="PCI")
                
                if parcelles_data and parcelles_data.get("features"):
                    print(f"    📦 {len(parcelles_data['features'])} parcelles récupérées dans la commune")
                    
                    # Pour chaque toiture, trouver la parcelle correspondante
                    for toiture in toitures_filtrees:
                        toiture_geom = shape(toiture["geometry"])
                        toiture_centroid = toiture_geom.centroid
                        
                        # Chercher la parcelle qui contient cette toiture
                        for parcelle in parcelles_data["features"]:
                            if "geometry" in parcelle:
                                try:
                                    parcelle_geom = shape(parcelle["geometry"])
                                    if parcelle_geom.contains(toiture_centroid):
                                        # Enrichir la parcelle avec les informations de la toiture
                                        parcelle_props = parcelle.get("properties", {}).copy()
                                        parcelle_props.update({
                                            "toiture_surface_m2": toiture["properties"]["surface_toiture_m2"],
                                            "toiture_distance_bt_m": toiture["properties"]["min_distance_bt_m"],
                                            "toiture_distance_hta_m": toiture["properties"]["min_distance_hta_m"],
                                            "has_toiture": True,
                                            "commune_recherche": commune,
                                            "insee": insee
                                        })
                                        
                                        parcelle_enrichie = {
                                            "type": "Feature",
                                            "geometry": parcelle["geometry"],
                                            "properties": parcelle_props
                                        }
                                        
                                        # Éviter les doublons de parcelles
                                        parcelle_id = parcelle_props.get("numero", f"parcelle_{len(parcelles_toitures)}")
                                        if not any(p["properties"].get("numero") == parcelle_id for p in parcelles_toitures):
                                            parcelles_toitures.append(parcelle_enrichie)
                                        break
                                except Exception as e:
                                    continue
                    
                    print(f"    ✅ {len(parcelles_toitures)} parcelles associées aux toitures")
                
            except Exception as e:
                print(f"⚠️ [TOITURES POLYGON] Erreur récupération parcelles: {e}")

        # 8) Statistiques
        if toitures_filtrees and len(toitures_filtrees) > 0:
            surfaces = [t["properties"]["surface_toiture_m2"] for t in toitures_filtrees]
            stats = {
                "count": len(toitures_filtrees),
                "surface_totale_m2": round(sum(surfaces), 2) if surfaces else 0,
                "surface_moyenne_m2": round(sum(surfaces) / len(surfaces), 2) if surfaces else 0,
                "surface_max_m2": round(max(surfaces), 2) if surfaces else 0,
                "surface_min_m2": round(min(surfaces), 2) if surfaces else 0
            }
        else:
            stats = {
                "count": 0,
                "surface_totale_m2": 0,
                "surface_moyenne_m2": 0,
                "surface_max_m2": 0,
                "surface_min_m2": 0
            }

        # 9) Réponse finale
        return jsonify({
            "success": True,
            "commune": commune,
            "insee": insee,
            "surface_commune_ha": surface_commune_ha,
            "search_method": "polygon_commune",
            "filters": {
                "min_surface_toiture_m2": min_surface_toiture,
                "max_distance_bt_m": max_distance_bt,
                "max_distance_hta_m": max_distance_hta,
                "max_results": max_results
            },
            "statistics": stats,
            "toitures": toitures_filtrees[:5],  # Exemples
            "all_toitures": toitures_filtrees,
            "parcelles": parcelles_toitures,
            "postes_info": {
                "postes_bt_count": len(postes_bt_data),
                "postes_hta_count": len(postes_hta_data)
            }
        })

    except Exception as e:
        print(f"❌ [TOITURES POLYGON] Erreur: {e}")
        return jsonify({"error": f"Erreur lors de la recherche: {str(e)}"}), 500

        print(f"✅ [TOITURES SIMPLE] {len(toitures_filtrees)} toitures filtrées")

        # 6.5) Récupération des parcelles pour les toitures trouvées
        print(f"🏠 [TOITURES SIMPLE] Récupération des parcelles pour les toitures...")
        parcelles_toitures = []
        
        if toitures_filtrees:
            try:
                # Récupérer les parcelles dans la même zone de recherche
                parcelles_data = get_api_cadastre_data(search_bbox, endpoint="/cadastre/parcelle", source_ign="PCI")
                
                if parcelles_data and parcelles_data.get("features"):
                    print(f"    📦 {len(parcelles_data['features'])} parcelles récupérées dans la zone")
                    
                    # Pour chaque toiture, trouver la parcelle correspondante
                    for toiture in toitures_filtrees:
                        toiture_geom = shape(toiture["geometry"])
                        toiture_centroid = toiture_geom.centroid
                        
                        # Chercher la parcelle qui contient cette toiture
                        for parcelle in parcelles_data["features"]:
                            if "geometry" in parcelle:
                                try:
                                    parcelle_geom = shape(parcelle["geometry"])
                                    if parcelle_geom.contains(toiture_centroid):
                                        # Enrichir la parcelle avec les informations de la toiture
                                        parcelle_props = parcelle.get("properties", {}).copy()
                                        parcelle_props.update({
                                            "toiture_surface_m2": toiture["properties"]["surface_toiture_m2"],
                                            "toiture_distance_bt_m": toiture["properties"]["min_distance_bt_m"],
                                            "toiture_distance_hta_m": toiture["properties"]["min_distance_hta_m"],
                                            "has_toiture": True,
                                            "commune_recherche": commune
                                        })
                                        
                                        parcelle_enrichie = {
                                            "type": "Feature",
                                            "geometry": parcelle["geometry"],
                                            "properties": parcelle_props
                                        }
                                        
                                        # Éviter les doublons de parcelles
                                        parcelle_id = parcelle_props.get("numero", f"parcelle_{len(parcelles_toitures)}")
                                        if not any(p["properties"].get("numero") == parcelle_id for p in parcelles_toitures):
                                            parcelles_toitures.append(parcelle_enrichie)
                                        break
                                except Exception as e:
                                    continue
                    
                    print(f"    ✅ {len(parcelles_toitures)} parcelles associées aux toitures")
                
            except Exception as e:
                print(f"⚠️ [TOITURES SIMPLE] Erreur récupération parcelles: {e}")

        # 7) Statistiques
        if toitures_filtrees and len(toitures_filtrees) > 0:
            surfaces = [t["properties"]["surface_toiture_m2"] for t in toitures_filtrees]
            stats = {
                "count": len(toitures_filtrees),
                "surface_totale_m2": round(sum(surfaces), 2) if surfaces else 0,
                "surface_moyenne_m2": round(sum(surfaces) / len(surfaces), 2) if surfaces else 0,
                "surface_max_m2": round(max(surfaces), 2) if surfaces else 0,
                "surface_min_m2": round(min(surfaces), 2) if surfaces else 0
            }
        else:
            stats = {"count": 0}

        # 8) Tri par surface décroissante
        toitures_filtrees.sort(key=lambda x: x["properties"].get("surface_toiture_m2", 0), reverse=True)

        # 9) Réponse JSON
        response_data = {
            "commune": commune,
            "lat": lat,
            "lon": lon,
            "search_radius_km": radius_km,
            "toitures": {
                "type": "FeatureCollection",
                "features": toitures_filtrees
            },
            "parcelles_toitures": {
                "type": "FeatureCollection",
                "features": parcelles_toitures
            },
            "postes_bt": {
                "type": "FeatureCollection", 
                "features": postes_bt_data
            },
            "postes_hta": {
                "type": "FeatureCollection",
                "features": postes_hta_data
            },
            "statistics": stats,
            "filters_applied": {
                "min_surface_toiture_m2": min_surface_toiture,
                "max_distance_bt_m": max_distance_bt,
                "max_distance_hta_m": max_distance_hta,
                "max_results": max_results
            },
            "metadata": {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "method": "simplified_radius_search",
                "total_batiments_analyses": len(batiments_data.get("features", [])),
                "parcelles_trouvees": len(parcelles_toitures)
            },
            # Données pour l'affichage sur la carte
            "map_data": {
                "center": [lat, lon],
                "zoom": 15,
                "layers": {
                    "toitures": {
                        "name": "Toitures trouvées",
                        "color": "#ff4444",
                        "features": toitures_filtrees
                    },
                    "parcelles": {
                        "name": "Parcelles avec toitures", 
                        "color": "#44ff44",
                        "features": parcelles_toitures
                    },
                    "postes_bt": {
                        "name": "Postes BT",
                        "color": "#4444ff",
                        "features": postes_bt_data
                    },
                    "postes_hta": {
                        "name": "Postes HTA", 
                        "color": "#ff44ff",
                        "features": postes_hta_data
                    }
                }
            }
        }
        
        print(f"🏠 [TOITURES SIMPLE] === FIN RECHERCHE - {len(toitures_filtrees)} toitures ===")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ [TOITURES SIMPLE] Erreur: {e}")
        return jsonify({"error": f"Erreur lors de la recherche: {str(e)}"}), 500

@app.route("/search_toitures_commune", methods=["GET", "POST"])
def search_toitures_commune():
    """
    Recherche spécialisée pour les toitures dans une commune avec filtres:
    - Surface minimale des toitures (m²)
    - Distance maximale aux postes BT/HTA (mètres)
    - Logique de filtrage par distance (OR/AND)
    - Type de poste (BT/HTA/ALL)
    """
    from urllib.parse import quote_plus
    from flask import request as flask_request
    from shapely.geometry import shape
    from shapely.ops import transform as shp_transform
    from pyproj import Transformer
    
    print("🏠 [TOITURES] === DÉBUT RECHERCHE TOITURES COMMUNE ===")
    
    # 1) Paramètres de la requête - Version robuste
    try:
        commune = flask_request.values.get("commune", "").strip()
    except:
        commune = ""
        
    if not commune:
        return jsonify({"error": "Veuillez fournir une commune."}), 400
    
    try:
        # Filtres spécifiques aux toitures
        min_surface_toiture = float(flask_request.values.get("min_surface_toiture", 50.0))  # m²
        max_distance_bt = float(flask_request.values.get("max_distance_bt", 300.0))  # mètres
        max_distance_hta = float(flask_request.values.get("max_distance_hta", 1000.0))  # mètres
        distance_logic = flask_request.values.get("distance_logic", "OR").upper()  # OR ou AND
        poste_type_filter = flask_request.values.get("poste_type_filter", "ALL").upper()  # ALL, BT, HTA
        
        # Filtres optionnels
        max_results = int(flask_request.values.get("max_results", 1000000))  # Limite de résultats augmentée
        sort_by = flask_request.values.get("sort_by", "surface").lower()  # surface, distance
    except:
        # Valeurs par défaut en cas d'erreur
        min_surface_toiture = 50.0
        max_distance_bt = 300.0
        max_distance_hta = 1000.0
        distance_logic = "OR"
        poste_type_filter = "ALL"
        max_results = 1000000
        sort_by = "surface"
        return jsonify({"error": "Veuillez fournir une commune."}), 400

    print(f"🏠 [TOITURES] Commune: {commune}")
    print(f"    Surface mini toiture: {min_surface_toiture}m²")
    print(f"    Distance max BT: {max_distance_bt}m, HTA: {max_distance_hta}m")
    print(f"    Logique distance: {distance_logic}, Type poste: {poste_type_filter}")
    print(f"    Max résultats: {max_results}, Tri: {sort_by}")

    # 2) Récupération du contour de la commune
    try:
        commune_infos = requests.get(
            f"https://geo.api.gouv.fr/communes?nom={quote_plus(commune)}&fields=centre,contour",
            timeout=15
        ).json()
        
        if not commune_infos or not commune_infos[0].get("contour"):
            return jsonify({"error": "Contour de la commune introuvable."}), 404
            
        contour = commune_infos[0]["contour"]
        centre = commune_infos[0]["centre"]
        lat, lon = centre["coordinates"][1], centre["coordinates"][0]
        
    except Exception as e:
        print(f"❌ [TOITURES] Erreur récupération commune: {e}")
        return jsonify({"error": "Erreur lors de la récupération des données de la commune."}), 500

    # 3) Création du polygone de la commune et bbox
    from shapely.geometry import shape
    commune_poly = shape(contour)
    minx, miny, maxx, maxy = commune_poly.bounds
    bbox = f"{minx},{miny},{maxx},{maxy},EPSG:4326"
    
    print(f"🏠 [TOITURES] Bbox commune: {bbox}")

    # 4) Récupération des postes pour calculs de distance
    def filter_in_commune(features):
        """Filtre les features qui intersectent avec la commune"""
        filtered = []
        for f in features:
            if "geometry" not in f:
                continue
            try:
                geom = shape(f["geometry"])
                if not geom.is_valid:
                    geom = geom.buffer(0)
                    if not geom.is_valid:
                        continue
                if geom.intersects(commune_poly):
                    filtered.append(f)
            except Exception as e:
                print(f"⚠️ [TOITURES] Géométrie ignorée: {e}")
                continue
        return filtered

    print(f"🏠 [TOITURES] Récupération des postes...")
    postes_bt_data = filter_in_commune(fetch_wfs_data(POSTE_LAYER, bbox))
    postes_hta_data = filter_in_commune(fetch_wfs_data(HT_POSTE_LAYER, bbox))
    
    print(f"    📍 {len(postes_bt_data)} postes BT trouvés")
    print(f"    📍 {len(postes_hta_data)} postes HTA trouvés")

    # 5) Récupération des bâtiments de toute la commune - NOUVELLE MÉTHODE OPTIMISÉE PAR CHUNKS
    print(f"🏠 [TOITURES] Récupération optimisée des bâtiments par chunks...")
    print(f"🏠 [TOITURES] Application de la méthode chunk comme les parkings (contournement erreur 414)")
    
    # Utiliser la nouvelle fonction optimisée par chunks
    batiments_data = get_batiments_info_by_polygon(contour)
    
    if not batiments_data or not batiments_data.get("features"):
        return jsonify({
            "error": "Aucun bâtiment trouvé dans cette commune",
            "commune": commune,
            "lat": lat,
            "lon": lon,
            "method": "openstreetmap_overpass"
        }), 404

    # print(f"📍 [TOITURES] {len(batiments_data['features'])} bâtiments trouvés via méthode chunk optimisée")  # Optimisé pour production multi-user

    # 6) Filtrage et enrichissement des toitures avec intersection géométrique précise
    to_l93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True).transform
    toitures_filtrees = []
    
    for i, batiment in enumerate(batiments_data["features"]):
        if "geometry" not in batiment:
            continue
            
        try:
            # Vérifier que le bâtiment est bien dans la commune (filtrage géométrique précis)
            bat_geom = shape(batiment["geometry"])
            if not bat_geom.is_valid:
                bat_geom = bat_geom.buffer(0)
                if not bat_geom.is_valid:
                    continue
            
            # Filtrage géographique : le bâtiment doit être dans la commune
            if not (commune_poly.contains(bat_geom) or commune_poly.intersects(bat_geom)):
                continue
            
            # Calculer la surface de la toiture (= surface du bâtiment)
            surface_m2 = shp_transform(to_l93, bat_geom).area
            
            # Filtrage par surface minimale
            if surface_m2 < min_surface_toiture:
                continue
            
            # Calcul des distances aux postes
            centroid = bat_geom.centroid.coords[0]
            min_distance_bt = calculate_min_distance(centroid, postes_bt_data)
            min_distance_hta = calculate_min_distance(centroid, postes_hta_data)
            
            # Application du filtre de distance
            distance_ok = True
            
            if poste_type_filter == "BT":
                distance_ok = (min_distance_bt is not None and min_distance_bt <= max_distance_bt)
            elif poste_type_filter == "HTA":
                distance_ok = (min_distance_hta is not None and min_distance_hta <= max_distance_hta)
            else:  # ALL
                bt_ok = (min_distance_bt is not None and min_distance_bt <= max_distance_bt)
                hta_ok = (min_distance_hta is not None and min_distance_hta <= max_distance_hta)
                
                if distance_logic == "AND":
                    distance_ok = bt_ok and hta_ok
                else:  # OR
                    distance_ok = bt_ok or hta_ok
            
            if not distance_ok:
                continue
            
            # Enrichissement des propriétés
            props = batiment.get("properties", {}).copy()
            props.update({
                "surface_toiture_m2": round(surface_m2, 2),
                "surface_toiture_ha": round(surface_m2 / 10000, 4),
                "min_distance_bt_m": round(min_distance_bt, 2) if min_distance_bt is not None else None,
                "min_distance_hta_m": round(min_distance_hta, 2) if min_distance_hta is not None else None,
                "min_distance_total_m": round(min(min_distance_bt or 1e12, min_distance_hta or 1e12), 2),
                "commune": commune,
                "search_method": "openstreetmap_overpass",
                "filter_applied": {
                    "min_surface_m2": min_surface_toiture,
                    "distance_logic": distance_logic,
                    "poste_type": poste_type_filter
                }
            })
            
            toitures_filtrees.append({
                "type": "Feature",
                "geometry": batiment["geometry"],
                "properties": props
            })
            
            # Affichage progression pour grandes communes
            if (i + 1) % 500 == 0:
                print(f"    🔄 Analysé {i + 1}/{len(batiments_data['features'])} bâtiments, {len(toitures_filtrees)} toitures validées")
                
        except Exception as e:
            print(f"⚠️ [TOITURES] Erreur analyse bâtiment {i}: {e}")
            continue

    print(f"✅ [TOITURES] {len(toitures_filtrees)} toitures après filtrage (méthode polygone complète)")

    # 7) Tri des résultats
    if sort_by == "surface":
        toitures_filtrees.sort(key=lambda x: x["properties"].get("surface_toiture_m2", 0), reverse=True)
    elif sort_by == "distance":
        toitures_filtrees.sort(key=lambda x: x["properties"].get("min_distance_total_m", 1e12))
    
    # Limitation du nombre de résultats
    if len(toitures_filtrees) > max_results:
        toitures_filtrees = toitures_filtrees[:max_results]
        print(f"🔄 [TOITURES] Résultats limités à {max_results}")

    # 9) Statistiques
    if toitures_filtrees and len(toitures_filtrees) > 0:
        surfaces = [t["properties"]["surface_toiture_m2"] for t in toitures_filtrees]
        distances_bt = [t["properties"]["min_distance_bt_m"] for t in toitures_filtrees if t["properties"]["min_distance_bt_m"] is not None]
        distances_hta = [t["properties"]["min_distance_hta_m"] for t in toitures_filtrees if t["properties"]["min_distance_hta_m"] is not None]
        
        stats = {
            "count": len(toitures_filtrees),
            "surface_totale_m2": round(sum(surfaces), 2) if surfaces else 0,
            "surface_moyenne_m2": round(sum(surfaces) / len(surfaces), 2) if surfaces else 0,
            "surface_max_m2": round(max(surfaces), 2) if surfaces else 0,
            "surface_min_m2": round(min(surfaces), 2) if surfaces else 0,
            "distance_bt_moyenne_m": round(sum(distances_bt) / len(distances_bt), 2) if distances_bt else None,
            "distance_hta_moyenne_m": round(sum(distances_hta) / len(distances_hta), 2) if distances_hta else None
        }
    else:
        stats = {"count": 0}

    # 10) Réponse JSON
    response_data = {
        "commune": commune,
        "lat": lat,
        "lon": lon,
        "toitures": {
            "type": "FeatureCollection",
            "features": toitures_filtrees
        },
        "postes_bt": {
            "type": "FeatureCollection", 
            "features": postes_bt_data
        },
        "postes_hta": {
            "type": "FeatureCollection",
            "features": postes_hta_data
        },
        "statistics": stats,
        "filters_applied": {
            "min_surface_toiture_m2": min_surface_toiture,
            "max_distance_bt_m": max_distance_bt,
            "max_distance_hta_m": max_distance_hta,
            "distance_logic": distance_logic,
            "poste_type_filter": poste_type_filter,
            "max_results": max_results,
            "sort_by": sort_by
        },
        "metadata": {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "method": "polygon_complet_comme_parkings",
            "total_batiments_analyses": len(batiments_data.get("features", [])),
            "toitures_apres_filtrage": len(toitures_filtrees)
        }
    }
    
    print(f"🏠 [TOITURES] === FIN RECHERCHE - {len(toitures_filtrees)} toitures trouvées ===")
    
    return jsonify(response_data)

@app.route("/rapport_map")
def rapport_map_point():
    print("🚨🚨🚨 FONCTION RAPPORT_MAP_POINT CORRIGÉE EN COURS D'EXÉCUTION 🚨🚨🚨")
    """
    Route pour générer le rapport du point courant avec recherche au point exact
    Recherche par intersection géographique (données qui croisent le point précis)
    """
    
    def log_step(step_name, message, status="INFO"):
        """Helper pour logging standardisé"""
        status_icon = {"INFO": "🔍", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}
        print(f"{status_icon.get(status, '📝')} [{step_name}] {message}")
    
    def safe_float(value, default=0.0):
        """Conversion sécurisée en float"""
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    # === INITIALISATION ET VALIDATION ===
    log_step("INIT", "Démarrage génération rapport point exact")
    
    try:
        lat = request.args.get("lat") or request.form.get("lat")
        lon = request.args.get("lon") or request.form.get("lon")
        address = request.args.get("address", "") or request.form.get("address", "")
        prospect_id = request.args.get("prospect_id") or request.form.get("prospect_id")
        
        if not lat or not lon:
            log_step("VALIDATION", "Coordonnées manquantes", "ERROR")
            return jsonify({"error": "Coordonnées lat/lon manquantes"}), 400
        
        lat_float = float(lat)
        lon_float = float(lon)
        
        log_step("VALIDATION", f"Coordonnées validées: {lat_float}, {lon_float}", "SUCCESS")
        if prospect_id:
            log_step("VALIDATION", f"Prospect ID: {prospect_id}", "SUCCESS")
        
        if not address:
            address = f"{lat_float}, {lon_float}"
            
    except ValueError as e:
        log_step("VALIDATION", f"Erreur conversion coordonnées: {e}", "ERROR")
        return jsonify({"error": "Coordonnées invalides"}), 400
    except Exception as e:
        log_step("VALIDATION", f"Erreur inattendue: {e}", "ERROR")
        return jsonify({"error": "Erreur de validation"}), 500
    
    # === INITIALISATION STRUCTURE DONNÉES ===
    from datetime import datetime
    import json
    import os
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report_data = {
        "lat": lat_float,
        "lon": lon_float,
        "address": address,
        "prospect_id": prospect_id,
        "timestamp": timestamp,
        "version": "3.2.1",
        "data_update": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "commune_name": None,
        "departement": None,
        "code_postal": None,
        "altitude": 0,
        "altitude_m": 0,
        "parcelles": [],
        "parcelle": None,
        "eleveurs": [],
        "postes": [],
        "ht_postes": [],
        "postes_bt": [],
        "postes_hta": [],
        "rpg": [],
        "hta": [],
        "plu_info": [],
        "zaer": [],
        "sirene": [],
        "parkings": [],
        "friches": [],
        "potentiel_solaire": [],
        "api_cadastre": None,
        "api_nature": None,
        "api_urbanisme": None,
        "api_externe": {"cadastre": None, "nature": None, "gpu": None},
        "surface_parcelle": None,
        "kwh_per_kwc": "N/A",
        "pvgis_data": None,
        "carte_url": None,
        "road_access": True,
        "flood_risk": False,
        "protected_area": False,
        "api_details": {}
    }
    
    point_geojson = {"type": "Point", "coordinates": [lon_float, lat_float]}
    
    # === FONCTION: COLLECTE AU POINT EXACT ===
    def collect_data_at_point():
        """Collecte toutes les données qui INTERSECTENT le point exact"""
        log_step("POINT", f"=== RECHERCHE AU POINT EXACT ({lat_float}, {lon_float}) ===")
        
        from shapely.geometry import Point, shape
        search_point = Point(lon_float, lat_float)
        
        intersecting_data = {
            "rpg_parcelles": [],
            "plu_zones": [],
            "zaer_zones": [],
            "friches": [],
            "potentiel_solaire": [],
            "parkings": []
        }
        
        # === PARCELLES RPG ===
        try:
            rpg_candidates = get_rpg_info(lat_float, lon_float, radius=0.01) or []
            for rpg_feat in rpg_candidates:
                try:
                    rpg_decoded = decode_rpg_feature(rpg_feat)
                    rpg_geom = shape(rpg_decoded["geometry"])
                    if rpg_geom.contains(search_point) or rpg_geom.intersects(search_point):
                        parcelle_data = {
                            "id_parcel": rpg_decoded["properties"].get("ID_PARCEL", "N/A"),
                            "surface_ha": rpg_decoded["properties"].get("SURF_PARC", "N/A"),
                            "code_culture": rpg_decoded["properties"].get("CODE_CULTU", "N/A"), 
                            "culture": rpg_decoded["properties"].get("Culture", "N/A"),
                            "commune": rpg_decoded["properties"].get("commune", "N/A"),
                            "properties": rpg_decoded["properties"],
                            "geometry": rpg_decoded["geometry"]
                        }
                        intersecting_data["rpg_parcelles"].append(parcelle_data)
                        log_step("POINT", f"✅ Parcelle RPG trouvée: {parcelle_data['id_parcel']}")
                except Exception as e:
                    log_step("POINT", f"Erreur traitement parcelle RPG: {e}", "WARNING")
                    
        except Exception as e:
            log_step("POINT", f"❌ Erreur recherche RPG: {e}", "ERROR")
        
        # === ZONES PLU ===
        try:
            plu_candidates = get_plu_info(lat_float, lon_float, radius=0.01) or []
            for plu_feat in plu_candidates:
                try:
                    if plu_feat.get("geometry"):
                        plu_geom = shape(plu_feat["geometry"])
                        if plu_geom.contains(search_point) or plu_geom.intersects(search_point):
                            zone_data = {
                                "libelle": plu_feat.get("libelle", "N/A"),
                                "typezone": plu_feat.get("typezone", "N/A"),
                                "properties": plu_feat,
                                "geometry": plu_feat["geometry"]
                            }
                            intersecting_data["plu_zones"].append(zone_data)
                            log_step("POINT", f"✅ Zone PLU trouvée: {zone_data['libelle']}")
                except Exception as e:
                    log_step("POINT", f"Erreur traitement zone PLU: {e}", "WARNING")
                    
        except Exception as e:
            log_step("POINT", f"❌ Erreur recherche PLU: {e}", "ERROR")
        
        # === ZONES ZAER ===
        try:
            zaer_candidates = get_zaer_info(lat_float, lon_float, radius=0.01) or []
            if zaer_candidates:
                for zaer_feat in zaer_candidates:
                    try:
                        if zaer_feat.get("geometry"):
                            zaer_geom = shape(zaer_feat["geometry"])
                            if zaer_geom.contains(search_point) or zaer_geom.intersects(search_point):
                                zone_data = {
                                    "nom": zaer_feat.get("properties", {}).get("nom", "N/A"),
                                    "filiere": zaer_feat.get("properties", {}).get("filiere", "N/A"),
                                    "properties": zaer_feat.get("properties", {}),
                                    "geometry": zaer_feat["geometry"]
                                }
                                intersecting_data["zaer_zones"].append(zone_data)
                                log_step("POINT", f"✅ Zone ZAER trouvée: {zone_data['nom']}")
                    except Exception as e:
                        log_step("POINT", f"Erreur traitement zone ZAER: {e}", "WARNING")
            
            if not intersecting_data["zaer_zones"]:
                log_step("POINT", "❌ Aucune zone ZAER ne contient ce point exact", "WARNING")
                
        except Exception as e:
            log_step("POINT", f"❌ Erreur recherche ZAER: {e}", "ERROR")
        
        log_step("POINT", "=== FIN RECHERCHE AU POINT EXACT ===")
        return intersecting_data
    
    # === FONCTION: INTÉGRATION DONNÉES ===
    def integrate_point_data_to_report(point_data):
        """Intègre les données du point exact dans la structure de rapport"""
        log_step("INTEGRATION", "Intégration des données du point exact")
        
        # PARCELLES RPG
        if point_data["rpg_parcelles"]:
            main_parcelle = point_data["rpg_parcelles"][0]
            
            report_data["parcelle"] = {
                "properties": {
                    "ID_PARCEL": main_parcelle['id_parcel'],
                    "SURF_PARC": main_parcelle['surface_ha'],
                    "CODE_CULTU": main_parcelle['code_culture'],
                    "Culture": main_parcelle['culture'],
                    "commune": main_parcelle['commune'],
                    **main_parcelle['properties']
                }
            }
            report_data["surface_parcelle"] = main_parcelle['surface_ha']
            
            # Toutes les parcelles pour le template
            all_rpg = []
            for parcelle in point_data["rpg_parcelles"]:
                rpg_feature = {
                    "type": "Feature",
                    "properties": parcelle['properties'],
                    "geometry": parcelle['geometry']
                }
                all_rpg.append(rpg_feature)
            
            report_data["rpg"] = all_rpg
            report_data["parcelles"] = point_data["rpg_parcelles"]
            
            log_step("INTEGRATION", f"✅ {len(point_data['rpg_parcelles'])} parcelle(s) RPG intégrée(s)")
        else:
            log_step("INTEGRATION", "⚠️ Aucune parcelle RPG au point exact", "WARNING")
        
        # ZONES PLU
        if point_data["plu_zones"]:
            report_data["plu_info"] = []
            for zone in point_data["plu_zones"]:
                plu_feature = {
                    "type": "Feature",
                    "properties": zone['properties'],
                    "geometry": zone['geometry']
                }
                report_data["plu_info"].append(plu_feature)
            
            log_step("INTEGRATION", f"✅ {len(point_data['plu_zones'])} zone(s) PLU intégrée(s)")
        else:
            log_step("INTEGRATION", "⚠️ Aucune zone PLU au point exact", "WARNING")
            report_data["plu_info"] = []
        
        # ZONES ZAER
        if point_data["zaer_zones"]:
            report_data["zaer"] = []
            for zone in point_data["zaer_zones"]:
                zaer_feature = {
                    "type": "Feature", 
                    "properties": zone['properties'],
                    "geometry": zone['geometry']
                }
                report_data["zaer"].append(zaer_feature)
            
            log_step("INTEGRATION", f"✅ {len(point_data['zaer_zones'])} zone(s) ZAER intégrée(s)")
        else:
            log_step("INTEGRATION", "⚠️ Aucune zone ZAER au point exact", "WARNING")
            report_data["zaer"] = []
        
        # MISE À JOUR DU TITRE
        if point_data["rpg_parcelles"]:
            main_parcelle = point_data["rpg_parcelles"][0]
            report_data["address"] = f"{address} - Parcelle {main_parcelle['id_parcel']} ({main_parcelle['culture']})"
        elif point_data["plu_zones"]:
            main_zone = point_data["plu_zones"][0]
            report_data["address"] = f"{address} - Zone {main_zone['libelle']}"
        else:
            report_data["address"] = f"{address} - Point exact"
    # === FONCTION: COLLECTE DONNÉES CONTEXTUELLES ===
    def collect_context_data():
        # PPRI GeoRisques (toujours injecté pour le template)
        try:
            def fetch_ppri_georisques(lat, lon, rayon_km=1.0):
                url = "https://www.georisques.gouv.fr/api/v1/zonage/pprn"
                params = {
                    "lat": lat,
                    "lon": lon,
                    "rayon": int(rayon_km * 1000),
                    "format": "geojson"
                }
                try:
                    resp = requests.get(url, params=params, timeout=10)
                    if resp.status_code == 200:
                        return resp.json()
                    else:
                        print(f"[PPRI] Erreur GeoRisques: {resp.status_code} {resp.text}")
                except Exception as e:
                    print(f"[PPRI] Exception GeoRisques: {e}")
                return {"type": "FeatureCollection", "features": []}

            from shapely.geometry import shape, Point
            raw_ppri = fetch_ppri_georisques(lat_float, lon_float, rayon_km=1.0)
            pt = Point(lon_float, lat_float)
            filtered_features = [f for f in raw_ppri.get("features", []) if f.get("geometry") and shape(f["geometry"]).contains(pt)]
            ppri_data = {"type": "FeatureCollection", "features": filtered_features}
            report_data["ppri"] = ppri_data
            log_step("CONTEXT", f"PPRI (GeoRisques): {len(filtered_features)} zone(s) trouvée(s)", "SUCCESS")
        except Exception as e:
            report_data["ppri"] = {"type": "FeatureCollection", "features": []}
            log_step("CONTEXT", f"Erreur PPRI GeoRisques: {e}", "ERROR")
        """Collecte les données contextuelles (postes, éleveurs, APIs) avec format template"""
        log_step("CONTEXT", "=== DÉBUT COLLECTE DONNÉES CONTEXTUELLES ===")
        
        # POSTES ÉLECTRIQUES - GARDER L'EXISTANT CAR ÇA FONCTIONNE
        try:
            postes_bt = get_nearest_postes(lat_float, lon_float, radius_deg=0.1) or []
            if postes_bt:
                report_data["postes"] = postes_bt
                report_data["postes_bt"] = postes_bt
                log_step("CONTEXT", f"Postes BT trouvés: {len(postes_bt)}", "SUCCESS")
            
            postes_hta = get_nearest_ht_postes(lat_float, lon_float) or []
            if postes_hta:
                report_data["ht_postes"] = postes_hta
                report_data["postes_hta"] = postes_hta
                log_step("CONTEXT", f"Postes HTA trouvés: {len(postes_hta)}", "SUCCESS")
                
        except Exception as e:
            log_step("CONTEXT", f"Erreur postes électriques: {e}", "ERROR")
        
        # CAPACITÉS RÉSEAU HTA - COLLECTE AVEC MAPPING COMPLET
        try:
            log_step("CONTEXT", "Collecte capacités réseau HTA...")
            
            # Essayons avec plusieurs rayons de recherche
            rayons_test = [0.05, 0.1, 0.2, 0.5]  # 5, 11, 22, 55 km
            capacites_reseau = []
            
            for rayon in rayons_test:
                log_step("CONTEXT", f"Test rayon {rayon}° (~{int(rayon*111)}km)...")
                capacites_test = get_nearest_capacites_reseau(lat_float, lon_float, count=10, radius_deg=rayon) or []
                if capacites_test:
                    capacites_reseau = capacites_test
                    log_step("CONTEXT", f"✅ Capacités trouvées avec rayon {rayon}°: {len(capacites_test)}", "SUCCESS")
                    break
                else:
                    log_step("CONTEXT", f"⚠️ Aucune capacité avec rayon {rayon}°", "WARNING")
            
            # Test direct de la couche
            if not capacites_reseau:
                log_step("CONTEXT", "Test direct de la couche CAPACITES_RESEAU_LAYER...")
                bbox_large = f"{lon_float-1},{lat_float-1},{lon_float+1},{lat_float+1},EPSG:4326"
                capacites_raw = fetch_wfs_data(CAPACITES_RESEAU_LAYER, bbox_large) or []
                log_step("CONTEXT", f"Test couche directe: {len(capacites_raw)} features trouvées", "INFO")
            
            if capacites_reseau:
                # Application du mapping HTA pour chaque capacité
                hta_enriched = []
                for item in capacites_reseau:
                    if isinstance(item, dict) and 'properties' in item:
                        props = item['properties']
                        
                        # Application du mapping avec gestion distance
                        ht_item = {display_name: props.get(field_name, "Non défini") 
                                  for display_name, field_name in hta_mapping.items()}
                        
                        # Ajout des données géométriques et de distance si disponibles
                        if 'geometry' in item:
                            ht_item['geometry'] = item['geometry']
                        if 'distance' in item:
                            ht_item['distance'] = round(item['distance'], 1)
                        
                        # Calcul distance si pas déjà présente
                        if 'distance' not in ht_item and item.get('geometry', {}).get('coordinates'):
                            try:
                                from geopy.distance import geodesic
                                coords = item['geometry']['coordinates']
                                if len(coords) >= 2:
                                    capacity_lon, capacity_lat = coords[0], coords[1]
                                    distance = geodesic((lat_float, lon_float), (capacity_lat, capacity_lon)).meters
                                    ht_item['distance'] = round(distance, 1)
                            except Exception as e:
                                log_step("CONTEXT", f"Erreur calcul distance capacité: {e}", "WARNING")
                        
                        # Log des propriétés trouvées pour débogage
                        non_empty_props = {k: v for k, v in props.items() if v and str(v).strip()}
                        log_step("CONTEXT", f"Capacité trouvée: {len(non_empty_props)} propriétés non-vides", "INFO")
                        
                        hta_enriched.append(ht_item)
                
                # Tri par distance si disponible
                hta_enriched.sort(key=lambda x: x.get('distance', 999999))
                
                report_data["hta"] = hta_enriched
                log_step("CONTEXT", f"✅ Capacités HTA enrichies: {len(hta_enriched)}", "SUCCESS")
                
                # Debug: affichage des capacités enrichies
                # print(f"🔍 [DEBUG HTA] Capacités HTA enrichies pour le rapport:")  # Optimisé pour production multi-user
                # for i, cap in enumerate(hta_enriched[:3]):  # Afficher les 3 premières
                    # print(f"🔍 [DEBUG HTA] Capacité {i+1}: {cap.get('Nom', 'N/A')} - Distance: {cap.get('distance', 'N/A')}m")  # Optimisé pour production multi-user
                    # print(f"🔍 [DEBUG HTA] - Capacité: {cap.get('Capacité', 'N/A')} - S3REnR: {cap.get('S3REnR', 'N/A')}")  # Optimisé pour production multi-user
            else:
                report_data["hta"] = []
                log_step("CONTEXT", "⚠️ Aucune capacité HTA trouvée après tous les tests", "WARNING")
                
        except Exception as e:
            report_data["hta"] = []
            log_step("CONTEXT", f"❌ Erreur capacités HTA: {e}", "ERROR")
        
        # ÉLEVEURS - ENRICHISSEMENT AVEC DISTANCES (avec gestion d'erreur robuste)
        try:
            eleveurs_bbox = f"{lon_float-0.03},{lat_float-0.03},{lon_float+0.03},{lat_float+0.03},EPSG:4326"
            eleveurs_raw = fetch_wfs_data(ELEVEURS_LAYER, eleveurs_bbox) or []
            
            if eleveurs_raw and isinstance(eleveurs_raw, dict) and eleveurs_raw.get('features'):
                eleveurs_features = eleveurs_raw['features']
            elif isinstance(eleveurs_raw, list):
                eleveurs_features = eleveurs_raw
            else:
                eleveurs_features = []
            
            # Calcul des distances pour les éleveurs
            eleveurs_enriched = []
            for eleveur in eleveurs_features:
                try:
                    geom = eleveur.get('geometry', {})
                    if geom and geom.get('type') == 'Point':
                        coords = geom.get('coordinates', [])
                        if len(coords) >= 2:
                            eleveur_lon, eleveur_lat = coords[0], coords[1]
                            
                            # Calcul distance
                            from geopy.distance import geodesic
                            distance = geodesic((lat_float, lon_float), (eleveur_lat, eleveur_lon)).meters
                            
                            # Enrichissement avec distance
                            eleveur_enriched = {
                                "type": "Feature",
                                "geometry": geom,
                                "properties": eleveur.get('properties', {}),
                                "distance": round(distance, 1)
                            }
                            eleveurs_enriched.append(eleveur_enriched)
                            
                except Exception as e:
                    log_step("CONTEXT", f"Erreur traitement éleveur: {e}", "WARNING")
                    continue
            
            # Tri par distance
            eleveurs_enriched.sort(key=lambda x: x.get('distance', 999999))
            eleveurs_final = eleveurs_enriched[:20]  # Max 20 éleveurs
            
            report_data["eleveurs"] = eleveurs_final
            log_step("CONTEXT", f"Éleveurs enrichis: {len(eleveurs_final)}", "SUCCESS")
            
        except Exception as e:
            log_step("CONTEXT", f"Erreur éleveurs: {e}", "ERROR")
            report_data["eleveurs"] = []
        
        # MÉTRIQUES ALTITUDE ET PVGIS - CRUCIAL POUR LE TEMPLATE
        try:
            # Altitude avec gestion d'erreur
            log_step("CONTEXT", "Appel API altitude...")
            try:
                altitude = get_elevation_at_point(lat_float, lon_float)
                if altitude is not None and altitude > 0:
                    report_data["altitude"] = round(altitude, 1)
                    report_data["altitude_m"] = round(altitude, 1)
                    log_step("CONTEXT", f"✅ Altitude: {altitude}m", "SUCCESS")
                else:
                    raise Exception("Altitude non valide")
            except:
                # Valeur par défaut si l'API altitude échoue
                report_data["altitude"] = 150.0  # Altitude approximative pour France
                report_data["altitude_m"] = 150.0
                log_step("CONTEXT", "⚠️ Altitude par défaut utilisée: 150m", "WARNING")
            
            # Production PVGIS avec gestion d'erreur
            log_step("CONTEXT", "Appel API PVGIS...")
            try:
                kwh_per_kwc = get_pvgis_production(lat_float, lon_float, 30, 180, 1.0)
                if kwh_per_kwc and kwh_per_kwc > 0:
                    report_data["kwh_per_kwc"] = round(kwh_per_kwc, 2)
                    report_data["pvgis_data"] = {"yearly_pv_energy_production": kwh_per_kwc}
                    log_step("CONTEXT", f"✅ Production PV: {kwh_per_kwc} kWh/kWc/an", "SUCCESS")
                else:
                    raise Exception("PVGIS non valide")
            except:
                # Valeur par défaut pour la France
                report_data["kwh_per_kwc"] = 1200.0
                report_data["pvgis_data"] = {"yearly_pv_energy_production": 1200.0}
                log_step("CONTEXT", "⚠️ Production PV par défaut utilisée: 1200 kWh/kWc/an", "WARNING")
                
        except Exception as e:
            log_step("CONTEXT", f"❌ Erreur métriques: {e}", "ERROR")
            # Valeurs par défaut en cas d'erreur
            report_data["altitude"] = 150.0
            report_data["altitude_m"] = 150.0
            report_data["kwh_per_kwc"] = 1200.0
            report_data["pvgis_data"] = {"yearly_pv_energy_production": 1200.0}
        
        # === APIs EXTERNES AVEC FORMAT TEMPLATE COMPLET ===
        api_details = {
            "cadastre": {"success": False, "data": None, "details": {}, "error": None},
            "gpu": {"success": False, "data": None, "details": {}, "layers_count": 0, "features_count": 0, "error": None},
            "codes_postaux": {"success": False, "data": None, "details": {}, "error": None},
            "nature": {"success": False, "data": None, "details": {}, "count": 0, "error": None}
        }
        
        try:
            # API Cadastre
            log_step("CONTEXT", "Appel API Cadastre...")
            try:
                cadastre_data = get_api_cadastre_data(point_geojson)
                if cadastre_data and cadastre_data.get('features'):
                    cadastre_props = cadastre_data['features'][0].get('properties', {})
                    report_data["api_cadastre"] = cadastre_data
                    report_data["api_externe"]["cadastre"] = cadastre_props
                    if cadastre_props.get('nom_com'):
                        report_data["commune_name"] = cadastre_props.get('nom_com')
                    if cadastre_props.get('code_postal'):
                        report_data["code_postal"] = cadastre_props.get('code_postal')
                    
                    # Structure pour template
                    api_details["cadastre"]["success"] = True
                    api_details["cadastre"]["data"] = cadastre_props
                    api_details["cadastre"]["details"] = {
                        "parcelle_numero": cadastre_props.get('numero', 'N/A'),
                        "section": cadastre_props.get('section', 'N/A'),
                        "commune": cadastre_props.get('nom_com', 'N/A'),
                        "code_insee": cadastre_props.get('code_insee', 'N/A'),
                        "departement": cadastre_props.get('code_dep', 'N/A'),
                        "contenance": f"{cadastre_props.get('contenance', 0)} m²" if cadastre_props.get('contenance') else 'N/A',
                        "idu": cadastre_props.get('idu', 'N/A')
                    }
                    
                    log_step("CONTEXT", f"✅ API Cadastre: {report_data.get('commune_name', 'OK')}", "SUCCESS")
                else:
                    api_details["cadastre"]["error"] = "Aucune donnée cadastrale trouvée"
                    log_step("CONTEXT", "⚠️ API Cadastre: Aucune donnée", "WARNING")
            except Exception as e:
                api_details["cadastre"]["error"] = str(e)
                log_step("CONTEXT", f"❌ Erreur API Cadastre: {e}", "ERROR")
            
            # API GPU
            log_step("CONTEXT", "Appel API GPU Urbanisme...")
            try:
                gpu_data = get_all_gpu_data(point_geojson)
                if gpu_data and isinstance(gpu_data, dict):
                    report_data["api_urbanisme"] = gpu_data
                    report_data["api_externe"]["gpu"] = gpu_data
                    
                    # Analyse détaillée pour template
                    layers_details = {}
                    total_features = 0
                    
                    for layer_name, layer_data in gpu_data.items():
                        if isinstance(layer_data, dict) and layer_data.get('features'):
                            layer_count = len(layer_data['features'])
                            total_features += layer_count
                            
                            layers_details[layer_name] = {
                                "count": layer_count,
                                "name_fr": layer_name.replace("-", " ").replace("_", " ").title(),
                                "features": []
                            }
                            
                            # Extraction des propriétés importantes
                            for feature in layer_data['features']:  # Affichage de toutes les features au lieu de [:3]
                                props = feature.get('properties', {})
                                if props:
                                    important_props = {k: v for k, v in props.items() 
                                                     if v and str(v).strip() and k not in ['geometry', 'geom']}
                                    if important_props:
                                        layers_details[layer_name]["features"].append(important_props)
                    
                    # Structure pour template
                    api_details["gpu"]["success"] = True
                    api_details["gpu"]["data"] = gpu_data
                    api_details["gpu"]["layers_count"] = len(gpu_data)
                    api_details["gpu"]["features_count"] = total_features
                    api_details["gpu"]["details"] = layers_details
                    
                    log_step("CONTEXT", f"✅ API GPU: {len(gpu_data)} couches, {total_features} features", "SUCCESS")
                else:
                    api_details["gpu"]["error"] = "Aucune donnée d'urbanisme trouvée"
                    log_step("CONTEXT", "⚠️ API GPU: Aucune donnée", "WARNING")
            except Exception as e:
                api_details["gpu"]["error"] = str(e)
                log_step("CONTEXT", f"❌ Erreur API GPU: {e}", "ERROR")
            
            # API Annuaire de l'Administration et des Services Publics
            log_step("CONTEXT", "🏛️ Appel API Annuaire Administration...")
            try:
                import json
                from urllib.parse import quote
                
                # Rechercher les services publics dans la commune
                # Utiliser le code INSEE si disponible via l'API Cadastre, sinon le nom de commune
                code_insee = None
                if api_details.get("cadastre", {}).get("success") and api_details["cadastre"]["details"].get("code_insee") != "N/A":
                    code_insee = api_details["cadastre"]["details"]["code_insee"]
                
                commune_name = report_data.get("commune_name", "")
                
                if code_insee or commune_name:
                    # URL de l'API Annuaire Administration
                    admin_url = "https://api-lannuaire.service-public.fr/api/explore/v2.1/catalog/datasets/api-lannuaire-administration/records"
                    
                    # Paramètres de recherche : priorité au code INSEE, sinon nom de commune
                    if code_insee:
                        admin_params = {
                            'where': f'code_insee_commune="{code_insee}"',
                            'limit': 20,
                            'order_by': 'nom'
                        }
                        log_step("CONTEXT", f"Recherche services publics par code INSEE: {code_insee}", "INFO")
                    else:
                        # Fallback: recherche par nom dans l'adresse (format JSON)
                        admin_params = {
                            'where': f'adresse like "*{commune_name}*"',
                            'limit': 20,
                            'order_by': 'nom'
                        }
                        log_step("CONTEXT", f"Recherche services publics par nom commune: {commune_name}", "INFO")
                    
                    admin_response = requests.get(admin_url, params=admin_params, timeout=15)
                    
                    if admin_response.status_code == 200:
                        admin_json = admin_response.json()
                        services = admin_json.get('results', [])
                        
                        if services:
                            # Traitement des services publics trouvés
                            services_list = []
                            for service in services:
                                # Parser l'adresse (qui est un JSON string)
                                adresse_raw = service.get('adresse', '[]')
                                if isinstance(adresse_raw, str):
                                    try:
                                        adresses = json.loads(adresse_raw)
                                        adresse_principale = adresses[0] if adresses else {}
                                    except:
                                        adresse_principale = {}
                                else:
                                    adresse_principale = adresse_raw[0] if isinstance(adresse_raw, list) and adresse_raw else {}
                                
                                # Parser téléphone
                                telephone_raw = service.get('telephone', '[]')
                                if isinstance(telephone_raw, str):
                                    try:
                                        telephones = json.loads(telephone_raw)
                                        telephone = telephones[0]['valeur'] if telephones and telephones[0].get('valeur') else None
                                    except:
                                        telephone = None
                                else:
                                    telephone = telephone_raw[0]['valeur'] if isinstance(telephone_raw, list) and telephone_raw and telephone_raw[0].get('valeur') else None
                                
                                # Parser site internet
                                site_raw = service.get('site_internet', '[]')
                                if isinstance(site_raw, str):
                                    try:
                                        sites = json.loads(site_raw)
                                        site_web = sites[0]['valeur'] if sites and sites[0].get('valeur') else None
                                    except:
                                        site_web = None
                                else:
                                    site_web = site_raw[0]['valeur'] if isinstance(site_raw, list) and site_raw and site_raw[0].get('valeur') else None
                                
                                service_info = {
                                    'nom': service.get('nom', 'N/A'),
                                    'type_organisme': service.get('type_organisme', 'N/A'),
                                    'categorie': service.get('categorie', 'N/A'),
                                    'mission': service.get('mission', '')[:300] + '...' if service.get('mission', '') and len(service.get('mission', '')) > 300 else service.get('mission', ''),
                                    'telephone': telephone,
                                    'email': service.get('adresse_courriel'),
                                    'site_web': site_web,
                                    'adresse': {
                                        'numero_voie': adresse_principale.get('numero_voie', ''),
                                        'code_postal': adresse_principale.get('code_postal', ''),
                                        'commune': adresse_principale.get('nom_commune', ''),
                                        'longitude': adresse_principale.get('longitude', ''),
                                        'latitude': adresse_principale.get('latitude', '')
                                    },
                                    'url_service_public': service.get('url_service_public'),
                                    'horaires': service.get('plage_ouverture')
                                }
                                services_list.append(service_info)
                            
                            # Stocker les données
                            report_data["api_externe"]["services_publics"] = services_list
                            
                            api_details["codes_postaux"]["success"] = True
                            api_details["codes_postaux"]["data"] = services_list
                            api_details["codes_postaux"]["details"] = {
                                "total_services": len(services_list),
                                "types_organismes": list(set([s['type_organisme'] for s in services_list if s['type_organisme'] != 'N/A'])),
                                "services_avec_telephone": len([s for s in services_list if s['telephone']]),
                                "services_avec_site_web": len([s for s in services_list if s['site_web']]),
                                "commune": commune_name
                            }
                            
                            log_step("CONTEXT", f"✅ API Administration: {len(services_list)} services publics trouvés", "SUCCESS")
                        else:
                            api_details["codes_postaux"]["error"] = "Aucun service public trouvé dans cette commune"
                            log_step("CONTEXT", "⚠️ API Administration: Aucun service trouvé", "WARNING")
                    else:
                        api_details["codes_postaux"]["error"] = f"Erreur HTTP {admin_response.status_code}"
                        log_step("CONTEXT", f"❌ API Administration erreur {admin_response.status_code}", "ERROR")
                else:
                    api_details["codes_postaux"]["error"] = "Code INSEE et nom de commune non disponibles pour la recherche"
                    log_step("CONTEXT", "⚠️ API Administration: Identifiants commune manquants", "WARNING")
                    
            except Exception as e:
                api_details["codes_postaux"]["error"] = str(e)
                log_step("CONTEXT", f"❌ Erreur API Administration: {e}", "ERROR")
                
            # API Nature (Espaces naturels protégés)
            try:
                log_step("CONTEXT", "🌿 Collecte données API Nature...", "INFO")
                # Debug: afficher les coordonnées utilisées
                # print(f"🔍 [DEBUG RAPPORT] Coordonnées pour API Nature: lat={lat_float}, lon={lon_float}")  # Optimisé pour production multi-user
                
                # Créer une géométrie point pour l'API Nature - CORRECTION: utiliser float au lieu de string
                geom = {"type": "Point", "coordinates": [lon_float, lat_float]}
                # print(f"🔍 [DEBUG RAPPORT] Géométrie API Nature: {geom}")  # Optimisé pour production multi-user
                
                nature_data = get_all_api_nature_data(geom)
                # print(f"🔍 [DEBUG RAPPORT] Résultat get_all_api_nature_data: {type(nature_data)}")  # Optimisé pour production multi-user
                
                if nature_data and "features" in nature_data and nature_data["features"]:
                    # print(f"🔍 [DEBUG RAPPORT] API Nature SUCCESS: {len(nature_data['features'])} features trouvées")  # Optimisé pour production multi-user
                    api_details["nature"]["success"] = True
                    api_details["nature"]["data"] = nature_data
                    api_details["nature"]["count"] = len(nature_data["features"])
                    
                    # AJOUT: Remplir report_data["api_nature"] pour le template
                    report_data["api_nature"] = nature_data
                    report_data["api_externe"]["nature"] = nature_data
                    
                    log_step("CONTEXT", f"✅ API Nature: {len(nature_data['features'])} espaces naturels trouvés", "SUCCESS")
                    
                    # Debug: afficher les noms des zones trouvées
                    for i, feature in enumerate(nature_data["features"][:3]):
                        props = feature.get("properties", {})
                        nom = props.get("NOM") or props.get("nom") or "Sans nom"
                        type_prot = props.get("TYPE_PROTECTION", "Non défini")
                        print(f"🔍 [DEBUG RAPPORT] Zone {i+1}: {nom} ({type_prot})")
                else:
                    print(f"🔍 [DEBUG RAPPORT] API Nature AUCUNE: nature_data={bool(nature_data)}")
                    if nature_data:
                        print(f"🔍 [DEBUG RAPPORT] features in nature_data: {'features' in nature_data}")
                        if 'features' in nature_data:
                            print(f"🔍 [DEBUG RAPPORT] len(features): {len(nature_data['features'])}")
                    
                    api_details["nature"]["success"] = False
                    api_details["nature"]["data"] = {"type": "FeatureCollection", "features": []}
                    api_details["nature"]["count"] = 0
                    log_step("CONTEXT", "ℹ️ API Nature: Aucun espace naturel trouvé", "INFO")
            except Exception as e:
                print(f"🔍 [DEBUG RAPPORT] API Nature EXCEPTION: {e}")
                import traceback
                traceback.print_exc()
                api_details["nature"]["success"] = False
                api_details["nature"]["error"] = str(e)
                log_step("CONTEXT", f"❌ Erreur API Nature: {e}", "ERROR")
                
        except Exception as e:
            log_step("CONTEXT", f"❌ Erreur APIs globale: {e}", "ERROR")
        
        # === CRUCIAL: Intégration des détails API pour le template ===
        report_data["api_details"] = api_details
        
        # === DONNÉES CONTEXTUELLES SUPPLÉMENTAIRES ===
        try:
            # Sirene (contexte économique)
            try:
                sirene_data = get_sirene_info(lat_float, lon_float, radius=0.05/111) or []
                report_data["sirene"] = sirene_data
                log_step("CONTEXT", f"Entreprises Sirene: {len(sirene_data)}", "SUCCESS")
            except:
                report_data["sirene"] = []
            
            # Friches (contexte si pas au point exact)
            if not report_data.get("friches"):
                try:
                    friches_data = get_friches_info(lat_float, lon_float, radius=0.01) or []
                    report_data["friches"] = friches_data
                    log_step("CONTEXT", f"Friches (contexte): {len(friches_data)}", "SUCCESS")
                except:
                    report_data["friches"] = []
            
            # Parkings (contexte si pas au point exact)
            if not report_data.get("parkings"):
                try:
                    parkings_data = get_parkings_info(lat_float, lon_float, radius=0.01) or []
                    report_data["parkings"] = parkings_data
                    log_step("CONTEXT", f"Parkings (contexte): {len(parkings_data)}", "SUCCESS")
                except:
                    report_data["parkings"] = []
            
            # Potentiel solaire
            if not report_data.get("potentiel_solaire"):
                try:
                    solaire_data = get_potentiel_solaire_info(lat_float, lon_float, radius=0.01) or []
                    report_data["potentiel_solaire"] = solaire_data
                    log_step("CONTEXT", f"Zones solaires: {len(solaire_data)}", "SUCCESS")
                except:
                    report_data["potentiel_solaire"] = []
                    
        except Exception as e:
            log_step("CONTEXT", f"Erreur données contextuelles: {e}", "ERROR")
        
        # === INFORMATIONS ADMINISTRATIVES - ENRICHISSEMENT ===
        try:
            # S'assurer qu'on a au moins un nom de commune
            if not report_data.get("commune_name"):
                # Fallback avec géocodage inverse
                try:
                    reverse_url = f"https://api-adresse.data.gouv.fr/reverse/?lon={lon_float}&lat={lat_float}"
                    response = requests.get(reverse_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('features'):
                            props = data['features'][0].get('properties', {})
                            report_data["commune_name"] = props.get('city', 'Commune inconnue')
                            report_data["code_postal"] = props.get('postcode', 'N/A')
                            log_step("CONTEXT", f"Géocodage inverse: {report_data['commune_name']}", "SUCCESS")
                except:
                    pass
            
            # Valeurs par défaut si toujours pas de commune
            if not report_data.get("commune_name"):
                report_data["commune_name"] = "Commune non identifiée"
            if not report_data.get("code_postal"):
                report_data["code_postal"] = "N/A"
            if not report_data.get("departement"):
                report_data["departement"] = "N/A"
                
            # Contraintes et accessibilité - valeurs par défaut
            if "road_access" not in report_data:
                report_data["road_access"] = True
            if "flood_risk" not in report_data:
                report_data["flood_risk"] = False
            if "protected_area" not in report_data:
                report_data["protected_area"] = False
                
            log_step("CONTEXT", f"Infos admin finales: {report_data['commune_name']} ({report_data['code_postal']})", "SUCCESS")
            
        except Exception as e:
            log_step("CONTEXT", f"Erreur infos administratives: {e}", "ERROR")
        
        log_step("CONTEXT", "=== FIN COLLECTE DONNÉES CONTEXTUELLES ===")    

    # === FONCTION: GÉNÉRATION CARTE ===
    def generate_map():
        """Génération de la carte"""
        try:
            parcelles_fc = {"type": "FeatureCollection", "features": report_data.get("rpg", [])}
            
            # Ajout récupération PPRI via l'API officielle GeoRisques
            def fetch_ppri_georisques(lat, lon, rayon_km=1.0):
                url = "https://www.georisques.gouv.fr/api/v1/zonage/pprn"
                params = {
                    "lat": lat,
                    "lon": lon,
                    "rayon": int(rayon_km * 1000),
                    "format": "geojson"
                }
                try:
                    resp = requests.get(url, params=params, timeout=10)
                    if resp.status_code == 200:
                        return resp.json()
                    else:
                        print(f"[PPRI] Erreur GeoRisques: {resp.status_code} {resp.text}")
                except Exception as e:
                    print(f"[PPRI] Exception GeoRisques: {e}")
                return {"type": "FeatureCollection", "features": []}

            # On ne garde que les polygones qui contiennent le point exact
            from shapely.geometry import shape, Point
            raw_ppri = fetch_ppri_georisques(lat_float, lon_float, rayon_km=1.0)
            pt = Point(lon_float, lat_float)
            filtered_features = [f for f in raw_ppri.get("features", []) if f.get("geometry") and shape(f["geometry"]).contains(pt)]
            ppri_data = {"type": "FeatureCollection", "features": filtered_features}
            map_obj = build_map(
                lat_float, lon_float, address,
                report_data.get("parcelle", {}),
                parcelles_fc,
                report_data.get("postes", []),
                report_data.get("ht_postes", []),
                report_data.get("plu_info", []),
                report_data.get("parkings", []),
                report_data.get("friches", []),
                report_data.get("potentiel_solaire", []),
                report_data.get("zaer", []),
                report_data.get("rpg", []),
                report_data.get("sirene", []),
                0.03,
                0.01,
                report_data.get("api_cadastre"),
                report_data.get("api_nature"),
                report_data.get("api_urbanisme"),
                eleveurs_data=report_data.get("eleveurs", []),
                ppri_data=ppri_data
            )
            
            # 🧹 NETTOYAGE: Supprimer les anciens rapports pour cette adresse
            import glob
            carte_path = os.path.join(app.root_path, "static", "cartes")
            os.makedirs(carte_path, exist_ok=True)
            
            address_clean = clean_filename(address, max_length=30)
            pattern = os.path.join(carte_path, f"rapport_{address_clean}_*.html")
            old_reports = glob.glob(pattern)
            
            if old_reports:
                print(f"🧹 [CLEANUP] Suppression de {len(old_reports)} ancien(s) rapport(s) pour {address}")
                for old_report in old_reports:
                    try:
                        os.remove(old_report)
                        print(f"   ✓ Supprimé: {os.path.basename(old_report)}")
                    except Exception as e:
                        print(f"   ⚠️ Erreur suppression {os.path.basename(old_report)}: {e}")
            
            # 🔒 Créer un nom de fichier sécurisé avec UUID
            carte_filename = generate_secure_filename("rapport", address)
            
            carte_fullpath = os.path.join(carte_path, carte_filename)
            map_obj.save(carte_fullpath)
            
            report_data["carte_url"] = f"/static/cartes/{carte_filename}"
            save_map_to_cache(map_obj, report_data)
            
            log_step("CARTE", f"✅ Carte sauvée: {carte_fullpath}", "SUCCESS")
            return map_obj
        except Exception as e:
            log_step("CARTE", f"❌ Erreur génération carte: {e}", "ERROR")
            return None

    # === EXÉCUTION PRINCIPALE ===
    try:
        # 1. Collecte au point exact
        log_step("EXEC", "🚀 Début exécution - Collecte au point exact")
        try:
            point_data = collect_data_at_point()
        except Exception as e:
            log_step("EXEC", f"❌ Erreur collecte point: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            point_data = {'rpg_parcelles': [], 'plu_zones': [], 'zaer_zones': []}
        
        # 2. Intégration dans le rapport
        log_step("EXEC", "🚀 Intégration des données du point exact")
        try:
            integrate_point_data_to_report(point_data)
        except Exception as e:
            log_step("EXEC", f"❌ Erreur intégration: {e}", "ERROR")
            import traceback
            traceback.print_exc()
        
        # 3. CRUCIAL : Collecte données contextuelles (altitude, PVGIS, APIs)
        log_step("EXEC", "🚀 Collecte des données contextuelles")
        try:
            collect_context_data()
        except Exception as e:
            log_step("EXEC", f"❌ Erreur collecte contexte: {e}", "ERROR")
            import traceback
            traceback.print_exc()
        
        # 4. Génération carte
        log_step("EXEC", "🚀 Génération de la carte")
        try:
            map_obj = generate_map()
            # Toujours fournir une carte, même si la génération échoue
            if not report_data.get("carte_url"):
                # Fallback: carte par défaut si la génération a échoué
                report_data["carte_url"] = "/map.html"
        except Exception as e:
            log_step("EXEC", f"❌ Erreur génération carte: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            report_data["carte_url"] = "/map.html"
        
        # === RÉSUMÉ FINAL DÉTAILLÉ ===
        log_step("SUMMARY", "=== RÉSUMÉ FINAL - RAPPORT COMPLET ===")
        log_step("SUMMARY", f"📍 Point: {lat_float}, {lon_float}")
        log_step("SUMMARY", f"📊 Parcelles RPG au point: {len(point_data.get('rpg_parcelles', []))}")
        log_step("SUMMARY", f"🏗️ Zones PLU au point: {len(point_data.get('plu_zones', []))}")
        log_step("SUMMARY", f"⚡ Zones ZAER au point: {len(point_data.get('zaer_zones', []))}")
        log_step("SUMMARY", f"⚡ Postes BT (contexte): {len(report_data.get('postes', []))}")
        log_step("SUMMARY", f"🔌 Postes HTA (contexte): {len(report_data.get('ht_postes', []))}")
        log_step("SUMMARY", f"👨‍🌾 Éleveurs (contexte): {len(report_data.get('eleveurs', []))}")
        log_step("SUMMARY", f"🏔️ Altitude: {report_data.get('altitude', 'N/A')}m")
        log_step("SUMMARY", f"☀️ Production PV: {report_data.get('kwh_per_kwc', 'N/A')} kWh/kWc/an")
        log_step("SUMMARY", f"🗺️ Commune: {report_data.get('commune_name', 'N/A')}")
        log_step("SUMMARY", f"🔗 APIs: {len(report_data.get('api_details', {}))}")
        
        # LOGS DÉTAILLÉS
        if point_data.get('rpg_parcelles'):
            for parcelle in point_data['rpg_parcelles']:
                log_step("POINT_RPG", f"   └── Parcelle {parcelle['id_parcel']}: {parcelle['culture']} ({parcelle['surface_ha']} ha)")
        
        if point_data.get('plu_zones'):
            for zone in point_data['plu_zones']:
                log_step("POINT_PLU", f"   └── Zone PLU: {zone['libelle']} ({zone['typezone']})")
        
        if point_data.get('zaer_zones'):
            for zone in point_data['zaer_zones']:
                log_step("POINT_ZAER", f"   └── Zone ZAER: {zone['nom']} - {zone['filiere']}")
        
        # LOG FINAL DES DONNÉES DISPONIBLES POUR LE TEMPLATE
        log_step("TEMPLATE", "=== DONNÉES DISPONIBLES POUR LE TEMPLATE ===")
        log_step("TEMPLATE", f"✅ report_data.altitude: {report_data.get('altitude', 'MISSING')}")
        log_step("TEMPLATE", f"✅ report_data.pvgis_data: {bool(report_data.get('pvgis_data'))}")
        log_step("TEMPLATE", f"✅ report_data.api_details: {bool(report_data.get('api_details'))}")
        log_step("TEMPLATE", f"✅ report_data.eleveurs: {len(report_data.get('eleveurs', []))}")
        log_step("TEMPLATE", f"✅ report_data.commune_name: {report_data.get('commune_name', 'MISSING')}")
        
        # === AJOUT DONNÉES GEORISQUES ===
        log_step("GEORISQUES", "Récupération des données GeoRisques...")
        try:
            georisques_risks = fetch_georisques_risks(lat_float, lon_float)
            if georisques_risks:
                report_data["georisques_risks"] = georisques_risks
                log_step("TEMPLATE", f"✅ report_data.georisques_risks: {len(georisques_risks)} catégories")
                # Comptage des risques pour debug
                total = sum(len(risks) for risks in georisques_risks.values() if risks)
                log_step("TEMPLATE", f"✅ Total risques: {total}")
            else:
                report_data["georisques_risks"] = {}
                log_step("TEMPLATE", "⚠️ Aucun risque GeoRisques retourné")
        except Exception as geo_e:
            log_step("GEORISQUES", f"❌ Erreur récupération GeoRisques: {geo_e}", "ERROR")
            report_data["georisques_risks"] = {}
        
        # 🎯 CRUCIAL: Return du template avec les données
        return render_template("rapport_point.html", report=report_data)
        
    except Exception as e:
        log_step("EXECUTION", f"❌ Erreur critique: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur génération rapport au point exact: {str(e)}"}), 500
    
@app.route("/test_capacites_hta")
def test_capacites_hta():
    """Route de test pour déboguer les capacités HTA"""
    lat, lon = 48.636, -1.511  # Mont-Saint-Michel
    
    print(f"🔍 [TEST CAPACITES] === TEST DIRECT CAPACITÉS HTA ===")
    print(f"🔍 [TEST CAPACITES] Coordonnées: {lat}, {lon}")
    
    # Test avec différents rayons
    rayons = [0.05, 0.1, 0.2, 0.5]
    capacites = None
    rayon_utilise = None
    
    for rayon in rayons:
        print(f"🔍 [TEST CAPACITES] Test rayon {rayon}° (~{int(rayon*111)}km)...")
        capacites = get_all_capacites_reseau(lat, lon, radius_deg=rayon)
        print(f"🔍 [TEST CAPACITES] Résultat: {len(capacites)} capacités trouvées")
        if capacites:
            rayon_utilise = rayon
            break
    
    # Test de mapping si on a des données
    non_empty = {}
    if capacites:
        print(f"🔍 [TEST CAPACITES] Exemple première capacité:")
        first_cap = capacites[0]
        props = first_cap.get('properties', {})
        print(f"🔍 [TEST CAPACITES] Properties keys: {list(props.keys())[:10]}")
        
        # Test mapping
        mapped = {display_name: props.get(field_name, "Non défini") 
                 for display_name, field_name in hta_mapping.items()}
        non_empty = {k: v for k, v in mapped.items() if v != "Non défini"}
        print(f"🔍 [TEST CAPACITES] Mapping non-vide: {len(non_empty)} champs")
        print(f"🔍 [TEST CAPACITES] Exemples: {list(non_empty.items())[:5]}")
    
    return jsonify({
        "success": True,
        "total_capacites": len(capacites) if capacites else 0,
        "rayon_utilise": rayon_utilise,
        "mapping_fields": len(non_empty),
        "sample_data": list(non_empty.items())[:10]
    })

@app.route("/rapport_point")
def rapport_point():
    """Route de compatibilité qui redirige vers rapport_map"""
    print("🔄 REDIRECTION DE /rapport_point VERS /rapport_map")
    return rapport_map_point()

@app.route("/rapport_point_complet")
def rapport_point_complet():
    """Route pour rapport point complet - redirige vers rapport_map"""
    print("🔄 REDIRECTION DE /rapport_point_complet VERS /rapport_map")
    return rapport_map_point()

from flask import Response, request, stream_with_context
import json
from shapely.geometry import shape, mapping
from shapely.ops import transform as shapely_transform
from pyproj import Transformer

# ——————————————————————————————————————————————————————————————
# 1) Fonction qui construit le rapport pour une commune donnée
# ——————————————————————————————————————————————————————————————
# ——————————————————————————————————————————————————————————————
# 1) Fonction qui construit le rapport pour une commune donnée
# ——————————————————————————————————————————————————————————————
from shapely.geometry import shape, mapping
from shapely.ops import transform as shp_transform
from pyproj import Transformer
import requests
from urllib.parse import quote_plus

def get_commune_mairie(nom_commune):
    url = f"https://geo.api.gouv.fr/communes?nom={quote_plus(nom_commune)}&fields=mairie"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            info = resp.json()
            if info and "mairie" in info[0]:
                return info[0]["mairie"]  # Peut contenir adresse, nom, téléphone, etc.
    except Exception:
        pass
    return None

def compute_commune_report(
    commune_name: str,
    culture: str,
    min_area_ha: float,
    max_area_ha: float,
    ht_max_km: float = 5.0,
    bt_max_km: float = 5.0,
    hta_aerial_max_km: float = 3.0,
    hta_underground_max_km: float = 1.5,
    filter_hta_lines_aerial: bool = False,
    filter_hta_lines_underground: bool = False,
    sirene_km: float = 5.0,
    want_eleveurs: bool = False,
    reseau_types: list = ["HTA", "BT"],
    commune_geometry: dict = None
) -> dict:
    """Calcule le rapport pour une commune avec gestion d'erreur renforcée"""
    try:
        print(f"🚀 [COMPUTE_COMMUNE] Début traitement commune: {commune_name}")
        
        # 1) Géocodage de la commune
        coords = geocode_address(commune_name)
        if not coords:
            print(f"❌ [ERREUR] Impossible de géocoder la commune: {commune_name}")
            return {"error": f"Géocodage impossible pour {commune_name}"}

        lat, lon = coords
        print(f"📍 [DEBUG] Commune {commune_name} géocodée: {lat}, {lon}")
        
        point_geojson = {"type": "Point", "coordinates": [lon, lat]}
        r_deg = 5.0 / 111.0

        # 2) Chargement des données brutes avec gestion d'erreur
        try:
            raw_rpg = get_rpg_info(lat, lon, radius=r_deg) or []
            print(f"📊 [DEBUG] RPG: {len(raw_rpg)} parcelles trouvées")
        except Exception as e:
            print(f"❌ [ERREUR] Récupération RPG: {e}")
            raw_rpg = []
            
        try:
            postes_bt = get_all_postes(lat, lon, radius_deg=r_deg) if "BT" in reseau_types else []
            print(f"⚡ [DEBUG] Postes BT: {len(postes_bt)} trouvés")
        except Exception as e:
            print(f"❌ [ERREUR] Récupération postes BT: {e}")
            postes_bt = []
            
        try:
            postes_hta = get_all_ht_postes(lat, lon, radius_deg=r_deg) if "HTA" in reseau_types else []
            print(f"🔌 [DEBUG] Postes HTA: {len(postes_hta)} trouvés")
        except Exception as e:
            print(f"❌ [ERREUR] Récupération postes HTA: {e}")
            postes_hta = []

        try:
            parcelles = get_all_parcelles(lat, lon, radius=sirene_km/111.0)
            print(f"🏠 [DEBUG] Parcelles: {len(parcelles)} trouvées")
        except Exception as e:
            print(f"❌ [ERREUR] Récupération parcelles: {e}")
            parcelles = []

        # 3) Récupération des lignes HTA AVANT le traitement des parcelles RPG
        hta_lignes_data = {"aerienne": {"features": []}, "souterraine": {"features": []}}
        try:
            from enedis_integration import get_lignes_hta
            from shapely.geometry import Point, LineString
            from shapely.ops import nearest_points
            
            # Utiliser le polygone de la commune pour un filtrage précis
            if commune_geometry:
                commune_shape = shape(commune_geometry)
                minx, miny, maxx, maxy = commune_shape.bounds
                
                print(f"🏛️ [DEBUG] Commune {commune_name}: polygone type={commune_shape.geom_type}, bounds=({minx:.4f},{miny:.4f},{maxx:.4f},{maxy:.4f})")
                print(f"🏛️ [DEBUG] Commune {commune_name}: area={commune_shape.area:.6f}°², valid={commune_shape.is_valid}")
                
                # Utiliser un bbox large basé sur les bounds de la commune + marge généreuse
                # pour être sûr de capturer toutes les lignes qui pourraient traverser la commune
                margin_large = 0.02  # ~2km de marge pour capturer les lignes qui traversent
                bbox_lignes = [minx - margin_large, miny - margin_large, maxx + margin_large, maxy + margin_large]
                print(f"🗺️ [DEBUG] Bbox large pour commune {commune_name}: {minx-margin_large:.4f},{miny-margin_large:.4f},{maxx+margin_large:.4f},{maxy+margin_large:.4f}")
                
                # Récupérer toutes les lignes dans le bbox large
                print(f"📡 [DEBUG] Requête lignes HTA dans bbox: {bbox_lignes}")
                hta_lignes_raw = get_lignes_hta(
                    bbox=bbox_lignes,
                    include_aerienne=True,
                    include_souterraine=True,
                    limit=2000  # Limite haute car on filtre ensuite par intersection
                )
                print(f"📦 [DEBUG] Lignes HTA reçues de l'API: {len(hta_lignes_raw.get('aerienne', {}).get('features', []))} aériennes, {len(hta_lignes_raw.get('souterraine', {}).get('features', []))} souterraines")
                
                # Fonction pour filtrer les lignes qui intersectent réellement la commune
                def filter_lignes_in_commune(lignes_features):
                    filtered = []
                    for i, feature in enumerate(lignes_features):
                        if "geometry" not in feature:
                            continue
                        try:
                            ligne_geom = shape(feature["geometry"])
                            if not ligne_geom.is_valid:
                                ligne_geom = ligne_geom.buffer(0)
                                if not ligne_geom.is_valid:
                                    continue
                            
                            # Vérifier l'intersection avec le polygone réel de la commune
                            if ligne_geom.intersects(commune_shape):
                                filtered.append(feature)
                                # Log pour debug : quelle ligne intersecte
                                ligne_id = feature.get("properties", {}).get("id", f"ligne_{i}")
                                print(f"✅ [DEBUG LIGNE] Ligne {ligne_id} intersecte la commune {commune_name}")
                            else:
                                ligne_id = feature.get("properties", {}).get("id", f"ligne_{i}")
                                print(f"❌ [DEBUG LIGNE] Ligne {ligne_id} N'intersecte PAS la commune {commune_name}")
                        except Exception as e:
                            print(f"⚠️ [DEBUG LIGNE] Erreur traitement ligne: {e}")
                            continue
                    return filtered
                
                # Filtrer les lignes par intersection réelle avec le polygone de la commune
                lignes_aeriennes_raw = hta_lignes_raw.get("aerienne", {}).get("features", [])
                lignes_souterraines_raw = hta_lignes_raw.get("souterraine", {}).get("features", [])
                
                lignes_aeriennes_filtered = filter_lignes_in_commune(lignes_aeriennes_raw)
                lignes_souterraines_filtered = filter_lignes_in_commune(lignes_souterraines_raw)
                
                hta_lignes_data = {
                    "aerienne": {"features": lignes_aeriennes_filtered},
                    "souterraine": {"features": lignes_souterraines_filtered}
                }
                
                aerienne_count = len(lignes_aeriennes_filtered)
                souterraine_count = len(lignes_souterraines_filtered) 
                print(f"🔌 [DEBUG] Lignes HTA qui intersectent la commune {commune_name}: {aerienne_count} aériennes, {souterraine_count} souterraines")
                print(f"📊 [DEBUG] Avant filtrage par polygone: {len(lignes_aeriennes_raw)} aériennes, {len(lignes_souterraines_raw)} souterraines")
            else:
                # Fallback vers bbox approximatif si pas de géométrie
                margin = 0.02  # ~2km de marge
                bbox_lignes = [lon - margin, lat - margin, lon + margin, lat + margin]
                print(f"🗺️ [DEBUG] Bbox approximatif commune {commune_name}: {bbox_lignes}")
                
                hta_lignes_data = get_lignes_hta(
                    bbox=bbox_lignes,
                    include_aerienne=True,
                    include_souterraine=True,
                    limit=500
                )
                
                aerienne_count = len(hta_lignes_data.get("aerienne", {}).get("features", []))
                souterraine_count = len(hta_lignes_data.get("souterraine", {}).get("features", []))
                print(f"🔌 [DEBUG] Lignes HTA récupérées (bbox approx): {aerienne_count} aériennes, {souterraine_count} souterraines")
            
        except Exception as e:
            print(f"⚠️ [WARN] Erreur lignes HTA: {e}")

        # 4) Parcelles RPG filtrées avec gestion d'erreur et accès aux lignes HTA
        proj_metric = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True).transform
        rpg_features = []
        
        try:
            for feat in raw_rpg:
                try:
                    dec = decode_rpg_feature(feat)
                    poly = shape(dec["geometry"])
                    props = dec["properties"]

                    if culture and culture.lower() not in props.get("Culture", "").lower():
                        continue
                    ha = shp_transform(proj_metric, poly).area / 10_000.0
                    if ha < min_area_ha or ha > max_area_ha:
                        continue
                    cent = poly.centroid.coords[0]

                    # Distance aux réseaux
                    d_bt = calculate_min_distance(cent, postes_bt) if "BT" in reseau_types else None
                    d_hta = calculate_min_distance(cent, postes_hta) if "HTA" in reseau_types else None

                    # Distance aux lignes HTA (nouveau filtrage)
                    d_ligne_aerienne = None
                    d_ligne_souterraine = None
                    
                    if filter_hta_lines_aerial and hta_lignes_data.get("aerienne", {}).get("features"):
                        d_ligne_aerienne = calculate_min_distance_to_lines(cent, hta_lignes_data["aerienne"]["features"])
                        print(f"🔧 [DEBUG RPG] Distance ligne aérienne: {d_ligne_aerienne:.1f}m (seuil: {hta_aerial_max_km*1000}m)")
                        
                    if filter_hta_lines_underground and hta_lignes_data.get("souterraine", {}).get("features"):
                        d_ligne_souterraine = calculate_min_distance_to_lines(cent, hta_lignes_data["souterraine"]["features"])
                        print(f"🔧 [DEBUG RPG] Distance ligne souterraine: {d_ligne_souterraine:.1f}m (seuil: {hta_underground_max_km*1000}m)")

                    # Filtrage selon le(s) type(s) de réseau sélectionné(s)
                    # Logique OU : la parcelle est retenue SI elle respecte AU MOINS UN critère
                    reseau_standard = [t for t in reseau_types if t in ["BT", "HTA"]]
                    reseau_lignes = [t for t in reseau_types if t.startswith("HTA_LINES_")]
                    
                    ok = False
                    raisons_ok = []
                    
                    # Vérification des réseaux standards (postes)
                    if reseau_standard:
                        if "BT" in reseau_standard:
                            if d_bt is not None and d_bt <= bt_max_km * 1000:
                                ok = True
                                raisons_ok.append(f"BT:{d_bt:.0f}m")
                        if "HTA" in reseau_standard:
                            if d_hta is not None and d_hta <= ht_max_km * 1000:
                                ok = True
                                raisons_ok.append(f"HTA:{d_hta:.0f}m")
                    
                    # Vérification des lignes HTA (critères additionnels OU)
                    if filter_hta_lines_aerial and d_ligne_aerienne is not None:
                        if d_ligne_aerienne <= hta_aerial_max_km * 1000:
                            ok = True
                            raisons_ok.append(f"LigneAér:{d_ligne_aerienne:.0f}m")
                            
                    if filter_hta_lines_underground and d_ligne_souterraine is not None:
                        if d_ligne_souterraine <= hta_underground_max_km * 1000:
                            ok = True
                            raisons_ok.append(f"LigneSout:{d_ligne_souterraine:.0f}m")
                    
                    if not ok:
                        print(f"❌ [DEBUG RPG] Parcelle éliminée: aucun critère respecté (BT:{d_bt}, HTA:{d_hta}, LigneAér:{d_ligne_aerienne}, LigneSout:{d_ligne_souterraine})")
                        continue
                    else:
                        print(f"✅ [DEBUG RPG] Parcelle retenue: critères OK → {', '.join(raisons_ok)}")

                    # Plus besoin du filtrage additionnel car intégré dans la logique OU ci-dessus

                    # Croisement API Cadastre avec gestion d'erreur
                    try:
                        centroid = poly.centroid
                        geom_query = {
                            "type": "Point",
                            "coordinates": [centroid.x, centroid.y]
                        }
                        cadastre_data = get_api_cadastre_data(geom_query)
                        if cadastre_data and "features" in cadastre_data and cadastre_data["features"]:
                            cad = cadastre_data["features"][0]["properties"]
                            code_com = cad.get("code_com", "")
                            com_abs = cad.get("com_abs", "000")
                            section = cad.get("section", "")
                            numero = cad.get("numero", "")
                            nom_commune = cad.get("nom_com", "") or cad.get("nom_commune", commune_name)
                        else:
                            code_com, com_abs, section, numero, nom_commune = "", "000", "", "", commune_name
                    except Exception as e:
                        print(f"⚠️ [WARN] Erreur cadastre pour parcelle: {e}")
                        code_com, com_abs, section, numero, nom_commune = "", "000", "", "", commune_name

                    props["code_com"] = code_com
                    props["com_abs"] = com_abs
                    props["section"] = section
                    props["numero"] = numero
                    props["nom_com"] = nom_commune

                    props.update({
                        "surface": round(ha, 3),
                        "coords": [cent[1], cent[0]],
                        "distance_bt": round(d_bt, 2) if d_bt is not None else None,
                        "distance_hta": round(d_hta, 2) if d_hta is not None else None,
                        "distance_ligne_aerienne": round(d_ligne_aerienne, 2) if d_ligne_aerienne is not None else None,
                        "distance_ligne_souterraine": round(d_ligne_souterraine, 2) if d_ligne_souterraine is not None else None,
                        "commune": commune_name
                    })
                    rpg_features.append({
                        "type": "Feature",
                        "geometry": mapping(poly),
                        "properties": props
                    })
                except Exception as e:
                    print(f"⚠️ [WARN] Erreur traitement parcelle RPG: {e}")
                    continue
        except Exception as e:
            print(f"❌ [ERREUR] Traitement RPG global: {e}")
            rpg_features = []
            
        rpg_fc = {"type": "FeatureCollection", "features": rpg_features}
        print(f"✅ [DEBUG] RPG filtré: {len(rpg_features)} parcelles retenues")

        # 4) Postes BT/HTA en FeatureCollection si demandés
        def poste_to_feature(poste):
            """Convertit un poste en Feature GeoJSON valide."""
            geometry = poste.get("geometry")
            
            # Validation stricte de la géométrie
            if not geometry or not isinstance(geometry, dict):
                return None
            
            if "type" not in geometry or "coordinates" not in geometry:
                return None
                
            # Vérifier que les coordonnées sont valides
            coords = geometry.get("coordinates")
            if not coords or not isinstance(coords, (list, tuple)) or len(coords) < 2:
                return None
                
            # Pour un Point, vérifier que les coordonnées sont numériques
            if geometry["type"] == "Point":
                try:
                    float(coords[0])  # longitude
                    float(coords[1])  # latitude
                except (ValueError, TypeError, IndexError):
                    return None
            
            return {
                "type": "Feature",
                "geometry": geometry,
                "properties": poste.get("properties", {})
            }
        
        result = {
            "nom": commune_name,
        }

        # Infos générales (surface, population, etc.)
        try:
            resp = requests.get(
                f"https://geo.api.gouv.fr/communes?nom={quote_plus(commune_name)}&fields=centre,contour,code,population,surface"
            )
            if resp.status_code == 200:
                commune_infos = resp.json()
                if commune_infos and len(commune_infos) > 0 and commune_infos[0].get("centre"):
                    info = commune_infos[0]
                    result["insee"] = info.get("code", "")
                    result["surface"] = round(info.get("surface", 0) / 100, 2) if info.get("surface") else 0
                    result["population"] = info.get("population", "")
                    centre_coords = info["centre"]["coordinates"]
                    result["centroid"] = [centre_coords[1], centre_coords[0]]  # [lat, lon]
                else:
                    result["insee"] = ""
                    result["surface"] = 0
                    result["population"] = ""
                    result["centroid"] = [lat, lon]
            else:
                print(f"⚠️ [WARN] API communes retourne status {resp.status_code} pour {commune_name}")
                result["insee"] = ""
                result["surface"] = 0
                result["population"] = ""
                result["centroid"] = [lat, lon]
        except Exception as e:
            print(f"⚠️ [WARN] Erreur API communes pour {commune_name}: {e}")
            result["insee"] = ""
            result["surface"] = 0
            result["population"] = ""
            result["centroid"] = [lat, lon]

        # Ajout mairie
        result["mairie"] = get_commune_mairie(commune_name)

        # Ajoute les couches réseau SEULEMENT si demandées
        if "BT" in reseau_types:
            result["postes_bt"] = {
                "type": "FeatureCollection",
                "features": [f for f in [poste_to_feature(p) for p in postes_bt] if f is not None]
            }
        if "HTA" in reseau_types:
            result["postes_hta"] = {
                "type": "FeatureCollection",
                "features": [f for f in [poste_to_feature(p) for p in postes_hta] if f is not None]
            }

        # 5) Éleveurs (toujours présent, mais filtré par want_eleveurs)
        eleveurs_fc = {"type": "FeatureCollection", "features": []}
        if want_eleveurs:
            try:
                bbox = f"{lon-0.05},{lat-0.05},{lon+0.05},{lat+0.05},EPSG:4326"
                eleveurs_data = fetch_wfs_data(ELEVEURS_LAYER, bbox, srsname="EPSG:4326") or []
                print(f"🐄 [DEBUG] Éleveurs trouvés: {len(eleveurs_data)}")
                
                for e in eleveurs_data:
                    try:
                        props = e.get("properties", {})
                        geom = e.get("geometry")
                        nom = props.get("nomUniteLe") or props.get("denominati") or ""
                        prenom = props.get("prenom1Uni") or props.get("prenomUsue") or ""
                        denomination = props.get("denominati") or ""
                        activite = props.get("activite_1") or ""
                        adresse = (
                            f"{props.get('numeroVoie','') or ''} "
                            f"{props.get('typeVoieEt','') or ''} "
                            f"{props.get('libelleVoi','') or ''}, "
                            f"{props.get('codePostal','') or ''} "
                            f"{props.get('libelleCom','') or ''}"
                        ).replace(" ,", "").strip()
                        ville_url = (props.get("libelleCom", "") or "").replace(" ", "+")
                        nom_url = (nom + " " + denomination).strip().replace(" ", "+")
                        siret = props.get("siret", "")
                        eleveur_props = {
                            # Nouvelles propriétés (normalisées)
                            "nom": nom,
                            "prenom": prenom,
                            "denomination": denomination,
                            "activite": activite,
                            "adresse": adresse,
                            "commune": commune_name,
                            "lien_annuaire": f"https://www.pagesjaunes.fr/recherche/{ville_url}/{nom_url}" if nom else "",
                            "lien_entreprise": f"https://annuaire-entreprises.data.gouv.fr/etablissement/{siret}" if siret else "",
                            "lien_pages_blanches": f"https://www.pagesjaunes.fr/pagesblanches/recherche?quoiqui={nom}+{prenom}&ou={props.get('libelleCom','')}",
                            
                            # Propriétés de compatibilité (pour JavaScript)
                            "nomUniteLe": nom,
                            "prenom1Uni": prenom, 
                            "denominati": denomination,
                            "activite_1": activite,
                            "siret": siret
                        }
                        eleveurs_fc["features"].append({
                            "type": "Feature",
                            "geometry": geom,
                            "properties": eleveur_props
                        })
                    except Exception as e:
                        print(f"⚠️ [WARN] Erreur traitement éleveur: {e}")
                        continue
                    
            except Exception as e:
                print(f"❌ [ERREUR] Récupération éleveurs: {e}")
        result["eleveurs"] = eleveurs_fc

        # 6) Capacités réseau HTA via WFS
        try:
            bbox = f"{lon-0.05},{lat-0.05},{lon+0.05},{lat+0.05},EPSG:4326"
            capa_fc = fetch_wfs_data(CAPACITES_RESEAU_LAYER, bbox, srsname="EPSG:4326")
            result["hta_capacites"] = capa_fc or {"type": "FeatureCollection", "features": []}
        except Exception as e:
            print(f"⚠️ [WARN] Erreur capacités réseau: {e}")
            result["hta_capacites"] = {"type": "FeatureCollection", "features": []}

        # 6b) Ajout des lignes HTA au résultat (déjà récupérées plus tôt)
        result["hta_lignes"] = hta_lignes_data

        # 7) RPG
        result["rpg_parcelles"] = rpg_fc

        print(f"✅ [SUCCESS] Rapport commune {commune_name} généré avec succès")
        return result
        
    except Exception as e:
        print(f"❌ [ERREUR CRITIQUE] compute_commune_report pour {commune_name}: {e}")
        import traceback
        print(traceback.format_exc())
        return {"error": f"Erreur lors du traitement de {commune_name}: {str(e)}"}
    

@app.route("/generate_reports_by_dept_sse")
def generate_reports_by_dept_sse():
    def event_stream():
        try:
            department = request.args.get("department")
            if not department:
                yield "event: error\ndata: " + json.dumps({"error": "Paramètre 'department' manquant"}) + "\n\n"
                return

            print(f"🚀 [SSE START] Début traitement département: {department}")

            # Lecture des paramètres
            culture = request.args.get("culture", "")
            min_area = float(request.args.get("rpg_min_area", request.args.get("min_area_ha", 0)))
            max_area = float(request.args.get("rpg_max_area", request.args.get("max_area_ha", 99999)))
            ht_max_km = float(request.args.get("ht_max_distance", 10))
            bt_max_km = float(request.args.get("bt_max_distance", 10))
            hta_aerial_max_km = float(request.args.get("hta_aerial_max_distance", 5))
            hta_underground_max_km = float(request.args.get("hta_underground_max_distance", 2))
            
            # Paramètres d'activation des filtres HTA lignes
            filter_hta_lines_aerial = request.args.get("filter_hta_lines_aerial", "false").lower() == "true"
            filter_hta_lines_underground = request.args.get("filter_hta_lines_underground", "false").lower() == "true"
            
            sirene_km = float(request.args.get("sirene_radius", 5))
            want_elev = request.args.get("want_eleveurs", "false").lower() == "true"
            reseau_types_str = request.args.get("reseau_types", "HTA,BT")
            reseau_types = [t.strip().upper() for t in reseau_types_str.split(",") if t.strip()]
            
            print(f"📊 [SSE PARAMS] Culture: {culture}, Area: {min_area}-{max_area}, Eleveurs: {want_elev}, Réseaux: {reseau_types}")
            print(f"📏 [SSE DISTANCES] HTA postes: {ht_max_km}km, BT: {bt_max_km}km, Lignes HTA aér: {hta_aerial_max_km}km, Lignes HTA sout: {hta_underground_max_km}km")
            print(f"🔲 [SSE FILTERS] Filtres HTA lignes: aériennes={filter_hta_lines_aerial}, souterraines={filter_hta_lines_underground}")

            communes = get_communes_for_dept(department)
            total = len(communes)
            
            print(f"🏘️ [SSE COMMUNES] {total} communes trouvées pour le département {department}")

            # CUMULATEURS pour toutes les couches
            def fc_init(): 
                return {"type": "FeatureCollection", "features": []}
            all_rpg = fc_init()
            all_postes_bt = fc_init()
            all_postes_hta = fc_init()
            all_eleveurs = fc_init()
            all_hta_lignes_aerienne = fc_init()
            all_hta_lignes_souterraine = fc_init()

            communes_avec_donnees = 0
            communes_avec_erreurs = 0

            for idx, feat in enumerate(communes, start=1):
                nom = feat["properties"]["nom"]
                print(f"🔍 [SSE COMMUNE {idx}/{total}] Traitement de {nom}")
                
                try:
                    # Récupérer la géométrie de la commune pour calculer le bbox réel
                    commune_geom = feat.get("geometry")
                    
                    rpt = compute_commune_report(
                        commune_name=nom,
                        commune_geometry=commune_geom,
                        culture=culture,
                        min_area_ha=min_area,
                        max_area_ha=max_area,
                        ht_max_km=ht_max_km,
                        bt_max_km=bt_max_km,
                        hta_aerial_max_km=hta_aerial_max_km,
                        hta_underground_max_km=hta_underground_max_km,
                        filter_hta_lines_aerial=filter_hta_lines_aerial,
                        filter_hta_lines_underground=filter_hta_lines_underground,
                        sirene_km=sirene_km,
                        want_eleveurs=want_elev,
                        reseau_types=reseau_types
                    )
                    
                    # Vérifier si la commune a retourné une erreur
                    if "error" in rpt:
                        print(f"⚠️ [SSE WARN] Commune {nom}: {rpt['error']}")
                        communes_avec_erreurs += 1
                        yield f"event: progress\ndata: [{idx}/{total}] {nom} (erreur: {rpt['error']})\n\n"
                        continue
                    
                    communes_avec_donnees += 1
                    
                    # CUMULER les couches
                    for fc_key, fc_var in [
                        ("rpg_parcelles", all_rpg),
                        ("postes_bt", all_postes_bt),
                        ("postes_hta", all_postes_hta),
                        ("eleveurs", all_eleveurs),
                    ]:
                        layer = rpt.get(fc_key)
                        if layer and isinstance(layer, dict) and layer.get("features"):
                            fc_var["features"].extend(layer["features"])
                            print(f"📊 [SSE CUMUL] {fc_key}: +{len(layer['features'])} features")

                    # CUMULER les lignes HTA (structure spéciale)
                    hta_lignes = rpt.get("hta_lignes", {})
                    if hta_lignes:
                        aerienne_data = hta_lignes.get("aerienne", {})
                        if aerienne_data and aerienne_data.get("features"):
                            all_hta_lignes_aerienne["features"].extend(aerienne_data["features"])
                            print(f"📊 [SSE CUMUL] hta_lignes_aerienne: +{len(aerienne_data['features'])} features")
                        
                        souterraine_data = hta_lignes.get("souterraine", {})
                        if souterraine_data and souterraine_data.get("features"):
                            all_hta_lignes_souterraine["features"].extend(souterraine_data["features"])
                            print(f"📊 [SSE CUMUL] hta_lignes_souterraine: +{len(souterraine_data['features'])} features")

                    yield f"event: progress\ndata: [{idx}/{total}] {nom} ✓\n\n"
                    yield f"event: result\ndata: {json.dumps(rpt, ensure_ascii=False)}\n\n"
                    
                except Exception as e:
                    print(f"❌ [SSE ERROR] Erreur commune {nom}: {e}")
                    communes_avec_erreurs += 1
                    yield f"event: progress\ndata: [{idx}/{total}] {nom} (ERREUR: {str(e)})\n\n"
                    continue

            # Résumé final
            print(f"✅ [SSE SUMMARY] {communes_avec_donnees} communes traitées, {communes_avec_erreurs} erreurs")
            print(f"📊 [SSE SUMMARY] Total features - RPG: {len(all_rpg['features'])}, Postes BT: {len(all_postes_bt['features'])}, Postes HTA: {len(all_postes_hta['features'])}, Éleveurs: {len(all_eleveurs['features'])}")
            print(f"🔌 [SSE SUMMARY] Lignes HTA - Aériennes: {len(all_hta_lignes_aerienne['features'])}, Souterraines: {len(all_hta_lignes_souterraine['features'])}")
            
            yield f"event: end\ndata: Traitement terminé: {communes_avec_donnees} communes, {communes_avec_erreurs} erreurs\n\n"
            
        except Exception as e:
            print(f"❌ [SSE CRITICAL] Erreur critique SSE: {e}")
            import traceback
            print(traceback.format_exc())
            yield f"event: error\ndata: {json.dumps({'error': f'Erreur serveur: {str(e)}'})}\n\n"

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")


@app.route("/rapport_departement")
def rapport_departement():
    dept = request.args.get("dept")
    if not dept:
        return "Département requis", 400

    communes = get_communes_for_dept(dept)
    all_reports = []
    for feat in communes:
        nom = feat["properties"]["nom"]
        rpt = compute_commune_report(
            commune_name=nom,
            culture=request.args.get("culture", ""),
            min_area_ha=float(request.args.get("rpg_min_area", request.args.get("min_area_ha", 0))),
            max_area_ha=float(request.args.get("rpg_max_area", request.args.get("max_area_ha", 1e9))),
            ht_max_km=float(request.args.get("ht_max_distance", 5.0)),
            bt_max_km=float(request.args.get("bt_max_distance", 5.0)),
            sirene_km=float(request.args.get("sirene_radius", 5.0)),
            want_eleveurs=True
        )
        # Structure des données complète pour la synthèse
        all_reports.append(rpt)

    # Calcul de la synthèse départementale
    synthese = synthese_departement(all_reports)
    
    print(f"[RAPPORT_DEPT_GET] Synthèse calculée: {synthese['total_eleveurs']} éleveurs, {synthese['total_parcelles']} parcelles")

    return render_template("rapport_departement_complet.html", dept=dept, reports=all_reports, synthese=synthese)


@app.route("/rapport_commune")
def rapport_commune():
    commune = request.args.get("commune")
    if not commune:
        return "Commune requise", 400

    # Utilise la fonction générique déjà définie
    report = compute_commune_report(
        commune_name=commune,
        culture=request.args.get("culture", ""),
        min_area_ha=float(request.args.get("rpg_min_area", request.args.get("min_area_ha", 0))),
        max_area_ha=float(request.args.get("rpg_max_area", request.args.get("max_area_ha", 1e9))),
        ht_max_km=float(request.args.get("ht_max_distance", 5.0)),
        bt_max_km=float(request.args.get("bt_max_distance", 5.0)),
        sirene_km=float(request.args.get("sirene_radius", 5.0)),
        want_eleveurs=True
    )
    if not report:
        return "Aucune donnée pour cette commune", 404

    # === Génération de la carte interactive ===
    centroid = report.get("centroid", [48.858, 2.294])
    import folium
    m = folium.Map(location=centroid, zoom_start=13)

    # Parcelles RPG (polygones)
    if report.get("rpg_parcelles", {}).get("features"):
        # Choisir dynamiquement des champs existants pour éviter l'AssertionError de Folium
        try:
            first_props = (report["rpg_parcelles"]["features"][0] or {}).get("properties", {})
            available_keys = set(first_props.keys())
        except Exception:
            available_keys = set()

        desired_fields = ["section", "numero", "surface", "SURF_PARC", "Culture"]
        tooltip_fields = [f for f in desired_fields if f in available_keys]

        if tooltip_fields:
            folium.GeoJson(
                report["rpg_parcelles"],
                name="Parcelles RPG",
                tooltip=folium.GeoJsonTooltip(fields=tooltip_fields)
            ).add_to(m)
        else:
            # Aucun champ attendu disponible, ajouter sans tooltip
            folium.GeoJson(
                report["rpg_parcelles"],
                name="Parcelles RPG"
            ).add_to(m)

    # Postes BT (orange)
    for poste in report.get("postes_bt", {}).get("features", []):
        coords = poste["geometry"]["coordinates"]
        folium.Marker(
            location=[coords[1], coords[0]],
            icon=folium.Icon(color="orange", icon="bolt", prefix="fa"),
            tooltip=poste["properties"].get("nom", "Poste BT")
        ).add_to(m)

    # Postes HTA (violet)
    for poste in report.get("postes_hta", {}).get("features", []):
        coords = poste["geometry"]["coordinates"]
        folium.Marker(
            location=[coords[1], coords[0]],
            icon=folium.Icon(color="purple", icon="bolt", prefix="fa"),
            tooltip=poste["properties"].get("nom", "Poste HTA")
        ).add_to(m)

    # Éleveurs (vert)
    for eleveur in report.get("eleveurs", {}).get("features", []):
        geom = eleveur.get("geometry", {})
        if geom.get("type") == "Point":
            coords = geom["coordinates"]
            folium.Marker(
                location=[coords[1], coords[0]],
                icon=folium.Icon(color="green", icon="leaf", prefix="fa"),
                tooltip=eleveur["properties"].get("nom", "Éleveur")
            ).add_to(m)

    # Lignes HTA (aériennes en bleu, souterraines en gris)
    hta_lignes = report.get("hta_lignes", {})
    
    # Lignes aériennes
    aerienne_data = hta_lignes.get("aerienne", {})
    if aerienne_data and aerienne_data.get("features"):
        for ligne in aerienne_data["features"]:
            if ligne.get("geometry") and ligne["geometry"].get("type") == "LineString":
                props = ligne.get("properties", {})
                folium.PolyLine(
                    locations=[[coord[1], coord[0]] for coord in ligne["geometry"]["coordinates"]],
                    color="blue",
                    weight=2,
                    opacity=0.8,
                    tooltip=f"Ligne HTA Aérienne - {props.get('nom_commune', 'N/A')}"
                ).add_to(m)
    
    # Lignes souterraines  
    souterraine_data = hta_lignes.get("souterraine", {})
    if souterraine_data and souterraine_data.get("features"):
        for ligne in souterraine_data["features"]:
            if ligne.get("geometry") and ligne["geometry"].get("type") == "LineString":
                props = ligne.get("properties", {})
                folium.PolyLine(
                    locations=[[coord[1], coord[0]] for coord in ligne["geometry"]["coordinates"]],
                    color="gray",
                    weight=2,
                    opacity=0.6,
                    tooltip=f"Ligne HTA Souterraine - {props.get('nom_commune', 'N/A')}"
                ).add_to(m)

    # Sauvegarde et URL de la carte
    carte_path = save_map_html(m, f"carte_{commune}.html")
    carte_url = "/" + carte_path if carte_path.startswith("static/") else carte_path

    # Passage au template (n'oublie pas carte_url dans rapport_commune.html)
    return render_template("rapport_commune.html", report=report, carte_url=carte_url)



@app.route("/toitures")
def recherche_toitures():
    """Interface de recherche de toitures par commune"""
    return render_template("recherche_toitures.html")

@app.route('/test_geoserver', methods=['GET'])
def test_geoserver():
    """Test de connexion GeoServer pour debug"""
    try:
        print("\n🔧 [TEST GEOSERVER] === DÉBUT TEST ===")
        
        # Test détection automatique
        detected_url = detect_working_geoserver()
        print(f"🔧 [TEST] URL détectée: {detected_url}")
        
        # Test direct du GeoServer détecté
        if detected_url:
            test_url = f"{detected_url}/wfs?service=WFS&version=1.0.0&request=GetCapabilities"
            print(f"🔧 [TEST] Test URL: {test_url}")
            
            response = requests.get(test_url, timeout=10)
            print(f"🔧 [TEST] Status: {response.status_code}")
            print(f"🔧 [TEST] Content length: {len(response.text)}")
            print(f"🔧 [TEST] Content preview: {response.text[:200]}...")
            
            # Test d'une requête réelle comme celle utilisée dans build_map
            test_wfs_url = f"{detected_url}/wfs"
            test_params = {
                'service': 'WFS',
                'version': '1.0.0', 
                'request': 'GetFeature',
                'typeName': 'geoserver:parkings_sup500m2',
                'outputFormat': 'application/json',
                'maxFeatures': 1
            }
            
            print(f"🔧 [TEST] Test requête WFS réelle...")
            wfs_response = requests.get(test_wfs_url, params=test_params, timeout=15)
            print(f"🔧 [TEST] WFS Status: {wfs_response.status_code}")
            print(f"🔧 [TEST] WFS Content: {wfs_response.text[:300]}...")
            
            return jsonify({
                'success': True,
                'detected_url': detected_url,
                'capabilities_status': response.status_code,
                'capabilities_content_length': len(response.text),
                'wfs_test_status': wfs_response.status_code,
                'wfs_test_content': wfs_response.text[:500],
                'environment': 'railway' if os.environ.get('RAILWAY_ENVIRONMENT') else 'local'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Aucun GeoServer détecté',
                'environment': 'railway' if os.environ.get('RAILWAY_ENVIRONMENT') else 'local'
            })
            
    except Exception as e:
        print(f"🔧 [TEST ERROR]: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'environment': 'railway' if os.environ.get('RAILWAY_ENVIRONMENT') else 'local'
        })

# ==================== AUTOCOMPLETE API ====================
@app.route("/api/autocomplete/address", methods=["GET"])
def autocomplete_address():
    """
    Autocomplétion d'adresses avec l'API BAN (Base Adresse Nationale)
    Supporte la recherche floue et tolère les fautes de frappe
    
    Exemples:
    - "montiers d'ahun" → trouve "Moutiers-d'Ahun"
    - "verdun 55" → trouve les adresses à Verdun (55)
    - "10 rue de la paix pari" → trouve "10 Rue de la Paix 75002 Paris"
    """
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 3:
        return jsonify({'suggestions': []})
    
    try:
        # API BAN - Base Adresse Nationale (gratuite, française, excellente précision)
        url = "https://api-adresse.data.gouv.fr/search/"
        params = {
            'q': query,
            'limit': 8,  # Nombre de suggestions
            'autocomplete': 1  # Mode autocomplétion
        }
        
        response = requests.get(url, params=params, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            suggestions = []
            
            for feature in data.get('features', []):
                props = feature.get('properties', {})
                coords = feature.get('geometry', {}).get('coordinates', [])
                
                # Construction du label avec formatage
                label = props.get('label', '')
                city = props.get('city', '')
                postcode = props.get('postcode', '')
                context = props.get('context', '')
                score = props.get('score', 0)
                
                # Icône selon le type
                type_addr = props.get('type', 'housenumber')
                icon = '📍' if type_addr == 'housenumber' else '🏘️' if type_addr == 'street' else '🏛️'
                
                suggestion = {
                    'label': label,
                    'value': label,
                    'city': city,
                    'postcode': postcode,
                    'context': context,
                    'lat': coords[1] if len(coords) > 1 else None,
                    'lon': coords[0] if len(coords) > 0 else None,
                    'score': score,
                    'type': type_addr,
                    'icon': icon,
                    'display': f"{icon} {label}"
                }
                suggestions.append(suggestion)
            
            # Trier par score décroissant
            suggestions.sort(key=lambda x: x['score'], reverse=True)
            
            return jsonify({'suggestions': suggestions})
        else:
            print(f"[AUTOCOMPLETE] Erreur API BAN: {response.status_code}")
            return jsonify({'suggestions': []})
            
    except Exception as e:
        print(f"[AUTOCOMPLETE] Erreur: {e}")
        return jsonify({'suggestions': [], 'error': str(e)})


@app.route("/api/get_parcel_coords", methods=["GET"])
def get_parcel_coords():
    """
    Récupère les coordonnées du centroïde de la parcelle cadastrale 
    la plus proche d'un point d'adresse donné.
    
    Cette API corrige le problème où l'adresse pointe dans la rue
    au lieu de pointer sur la parcelle.
    
    Paramètres:
    - lat: latitude du point d'adresse (depuis BAN)
    - lon: longitude du point d'adresse (depuis BAN)
    - buffer: distance de recherche en mètres (défaut: 20m)
    
    Retourne:
    - parcel_lat: latitude du centroïde de la parcelle
    - parcel_lon: longitude du centroïde de la parcelle
    - parcel_id: identifiant de la parcelle
    - distance: distance entre le point d'origine et la parcelle
    """
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        buffer_meters = request.args.get('buffer', 20, type=int)
        
        if not lat or not lon:
            return jsonify({'error': 'Paramètres lat et lon requis'}), 400
        
        # Étape 1: Interroger l'API Cadastre pour trouver les parcelles proches
        # API WFS du cadastre (service gratuit IGN)
        wfs_url = "https://data.geopf.fr/wfs"
        
        # Créer un buffer en degrés (approximatif: 1° ≈ 111km)
        # Pour 20m, buffer ≈ 0.0002 degrés
        buffer_deg = buffer_meters / 111000.0
        
        # BBox autour du point
        bbox = f"{lon - buffer_deg},{lat - buffer_deg},{lon + buffer_deg},{lat + buffer_deg}"
        
        params = {
            'SERVICE': 'WFS',
            'VERSION': '2.0.0',
            'REQUEST': 'GetFeature',
            'TYPENAME': 'CADASTRALPARCELS.PARCELLAIRE_EXPRESS:parcelle',
            'OUTPUTFORMAT': 'application/json',
            'SRSNAME': 'EPSG:4326',
            'BBOX': bbox,
            'COUNT': 10  # Limiter à 10 parcelles max
        }
        
        response = requests.get(wfs_url, params=params, timeout=5)
        
        if response.status_code != 200:
            print(f"[PARCEL_COORDS] Erreur WFS: {response.status_code}")
            # Fallback: retourner les coordonnées d'origine
            return jsonify({
                'parcel_lat': lat,
                'parcel_lon': lon,
                'parcel_id': None,
                'distance': 0,
                'fallback': True,
                'message': 'Utilisation des coordonnées d\'adresse (parcelle non trouvée)'
            })
        
        data = response.json()
        features = data.get('features', [])
        
        if not features:
            print(f"[PARCEL_COORDS] Aucune parcelle trouvée près de {lat},{lon}")
            # Fallback: retourner les coordonnées d'origine
            return jsonify({
                'parcel_lat': lat,
                'parcel_lon': lon,
                'parcel_id': None,
                'distance': 0,
                'fallback': True,
                'message': 'Aucune parcelle trouvée à proximité'
            })
        
        # Étape 2: Trouver la parcelle la plus proche du point d'adresse
        from math import radians, cos, sin, asin, sqrt
        
        def haversine(lon1, lat1, lon2, lat2):
            """Calcule la distance en mètres entre deux points GPS"""
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371000  # Rayon de la Terre en mètres
            return c * r
        
        closest_parcel = None
        min_distance = float('inf')
        
        for feature in features:
            geom = feature.get('geometry', {})
            geom_type = geom.get('type', '')
            
            # Calculer le centroïde de la parcelle
            if geom_type == 'Polygon':
                coords = geom.get('coordinates', [[]])[0]
            elif geom_type == 'MultiPolygon':
                coords = geom.get('coordinates', [[[]]])[0][0]
            else:
                continue
            
            if not coords:
                continue
            
            # Centroïde simple (moyenne des coordonnées)
            centroid_lon = sum(c[0] for c in coords) / len(coords)
            centroid_lat = sum(c[1] for c in coords) / len(coords)
            
            # Distance du point d'adresse au centroïde de la parcelle
            distance = haversine(lon, lat, centroid_lon, centroid_lat)
            
            if distance < min_distance:
                min_distance = distance
                closest_parcel = {
                    'lat': centroid_lat,
                    'lon': centroid_lon,
                    'id': feature.get('id', ''),
                    'properties': feature.get('properties', {}),
                    'distance': distance
                }
        
        if not closest_parcel:
            # Fallback
            return jsonify({
                'parcel_lat': lat,
                'parcel_lon': lon,
                'parcel_id': None,
                'distance': 0,
                'fallback': True,
                'message': 'Impossible de calculer le centroïde'
            })
        
        print(f"[PARCEL_COORDS] ✅ Parcelle trouvée à {closest_parcel['distance']:.1f}m")
        print(f"[PARCEL_COORDS]    ID: {closest_parcel['id']}")
        print(f"[PARCEL_COORDS]    Centroïde: {closest_parcel['lat']:.6f}, {closest_parcel['lon']:.6f}")
        
        return jsonify({
            'parcel_lat': closest_parcel['lat'],
            'parcel_lon': closest_parcel['lon'],
            'parcel_id': closest_parcel['id'],
            'distance': round(closest_parcel['distance'], 2),
            'fallback': False,
            'original_lat': lat,
            'original_lon': lon,
            'message': f'Parcelle trouvée à {round(closest_parcel["distance"], 1)}m de l\'adresse'
        })
        
    except Exception as e:
        print(f"[PARCEL_COORDS] Erreur: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback: retourner les coordonnées d'origine
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        return jsonify({
            'parcel_lat': lat or 0,
            'parcel_lon': lon or 0,
            'parcel_id': None,
            'distance': 0,
            'fallback': True,
            'error': str(e),
            'message': 'Erreur lors de la recherche de parcelle'
        })


@app.route("/api/autocomplete/commune", methods=["GET"])
def autocomplete_commune():
    """
    Autocomplétion de communes avec l'API Geo.data.gouv.fr
    Supporte la recherche par nom, code postal, code INSEE
    Tolère les fautes de frappe
    
    Exemples:
    - "montiers" → trouve "Moutiers-d'Ahun"
    - "verdun" → trouve "Verdun (55100, 55)" et "Verdun-sur-Garonne (82600, 82)"
    - "75001" → trouve "Paris 1er Arrondissement"
    """
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({'suggestions': []})
    
    try:
        # API Geo - communes (gratuite, française)
        url = "https://geo.api.gouv.fr/communes"
        params = {
            'nom': query,
            'fields': 'nom,code,codesPostaux,codeDepartement,population,centre',
            'format': 'json',
            'limit': 10
        }
        
        response = requests.get(url, params=params, timeout=3)
        
        if response.status_code == 200:
            communes = response.json()
            suggestions = []
            
            for commune in communes:
                nom = commune.get('nom', '')
                code_insee = commune.get('code', '')
                codes_postaux = commune.get('codesPostaux', [])
                code_dept = commune.get('codeDepartement', '')
                population = commune.get('population', 0)
                centre = commune.get('centre', {})
                
                # Label avec code postal et département
                cp_str = codes_postaux[0] if codes_postaux else ''
                label = f"{nom} ({cp_str}, {code_dept})"
                
                # Formattage population
                pop_str = f"{population:,}".replace(',', ' ') if population else 'N/A'
                
                suggestion = {
                    'label': label,
                    'value': nom,
                    'nom': nom,
                    'code_insee': code_insee,
                    'codes_postaux': codes_postaux,
                    'code_postal': cp_str,
                    'code_departement': code_dept,
                    'population': population,
                    'lat': centre.get('coordinates', [None, None])[1],
                    'lon': centre.get('coordinates', [None, None])[0],
                    'display': f"🏛️ {nom} ({cp_str}, {code_dept}) - {pop_str} hab."
                }
                suggestions.append(suggestion)
            
            return jsonify({'suggestions': suggestions})
        else:
            print(f"[AUTOCOMPLETE] Erreur API Geo: {response.status_code}")
            return jsonify({'suggestions': []})
            
    except Exception as e:
        print(f"[AUTOCOMPLETE] Erreur: {e}")
        return jsonify({'suggestions': [], 'error': str(e)})


@app.route("/search_by_address", methods=["GET", "POST"])
def search_by_address_route():
    # Debug prints moved after parcelle assignment to avoid UnboundLocalError
    # Utility to ensure a list of valid GeoJSON Feature dicts
    # Fonctions utilitaires locales supprimées - utilisation des fonctions globales
    from shapely.geometry import shape, Point
    import time

    # --- Fonctions utilitaires ---
    def safe_float(value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def to_feature_collection(features):
        if not features:
            return {"type": "FeatureCollection", "features": []}
        if isinstance(features, dict) and features.get("type") == "FeatureCollection":
            return features
        return {"type": "FeatureCollection", "features": features}

    values = request.values
    lat_str = values.get("lat")
    lon_str = values.get("lon")
    address = values.get("address")

    # 1. Parse coordonnées ou adresse
    if lat_str not in (None, "") and lon_str not in (None, ""):
        try:
            lat, lon = float(lat_str), float(lon_str)
        except ValueError:
            return jsonify({"error": "Les coordonnées doivent être des nombres."}), 400
    elif address:
        print(f"🔍 [GEOCODE] Tentative de géocodage pour: {address}")
        coords = geocode_address(address)
        if not coords:
            print(f"❌ [GEOCODE] Adresse non trouvée: {address}")
            return jsonify({"error": "Adresse non trouvée."}), 404
        lat, lon = coords
        print(f"✅ [GEOCODE] Coordonnées trouvées: {lat}, {lon}")
    else:
        return jsonify({"error": "Veuillez fournir une adresse ou des coordonnées."}), 400

    # 2. Rayons et bbox
    ht_radius_km     = safe_float(values.get("ht_radius"),     1.0)
    bt_radius_km     = safe_float(values.get("bt_radius"),     1.0)
    sirene_radius_km = safe_float(values.get("sirene_radius"), 0.05)
    search_radius = 0.0027  # 300 mètres (300m / 111000m par degré)
    bt_radius_deg = bt_radius_km / 111
    ht_radius_deg = ht_radius_km / 111
    sirene_radius_deg = sirene_radius_km / 111

    # 3. Données principales (toujours FeatureCollection)
    print(f"📍 [DEBUG] Récupération des données pour lat={lat}, lon={lon}")
    
    try:
        print("🔄 [DEBUG] Appel get_all_parcelles...")
        parcelles_data = get_all_parcelles(lat, lon, radius=search_radius)
        print(f"✅ [DEBUG] get_all_parcelles OK: {len(parcelles_data.get('features', []))} parcelles")
    except Exception as e:
        print(f"❌ [DEBUG] ERREUR get_all_parcelles: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur parcelles: {str(e)}"}), 500

    def get_parcelle_info(lat, lon):
        bbox = f"{lon-0.001},{lat-0.001},{lon+0.001},{lat+0.001},EPSG:4326"
        features = fetch_wfs_data(CADASTRE_LAYER, bbox)
        point = Point(lon, lat)
        for feature in features:
            geom = shape(feature["geometry"])
            if geom.contains(point):
                parcelle_info = feature["properties"]
                parcelle_info["geometry"] = feature["geometry"]
                return parcelle_info
        return None

    # 4. Postes, réseaux, couches métiers
    try:
        print("🔄 [DEBUG] Appel get_nearest_postes (BT)...")
        postes_bt_raw = ensure_feature_list(get_nearest_postes(lat, lon, count=1, radius_deg=bt_radius_deg))
        print(f"✅ [DEBUG] get_nearest_postes OK: {len(postes_bt_raw)} postes BT")
    except Exception as e:
        print(f"❌ [DEBUG] ERREUR get_nearest_postes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur postes BT: {str(e)}"}), 500
    
    try:
        print("🔄 [DEBUG] Appel get_nearest_ht_postes (HTA)...")
        postes_hta_raw = ensure_feature_list(get_nearest_ht_postes(lat, lon, count=1, radius_deg=ht_radius_deg))
        print(f"✅ [DEBUG] get_nearest_ht_postes OK: {len(postes_hta_raw)} postes HTA")
    except Exception as e:
        print(f"❌ [DEBUG] ERREUR get_nearest_ht_postes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur postes HTA: {str(e)}"}), 500
    
    try:
        print("🔄 [DEBUG] Appel get_nearest_capacites_reseau...")
        capacites_reseau_raw = ensure_feature_list(get_nearest_capacites_reseau(lat, lon, count=1, radius_deg=ht_radius_deg))
        print(f"✅ [DEBUG] get_nearest_capacites_reseau OK: {len(capacites_reseau_raw)} capacités")
    except Exception as e:
        print(f"❌ [DEBUG] ERREUR get_nearest_capacites_reseau: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur capacités réseau: {str(e)}"}), 500
    
    postes_bt = to_feature_collection(postes_bt_raw)
    postes_hta = to_feature_collection(postes_hta_raw)
    capacites_reseau = to_feature_collection(capacites_reseau_raw)

    # Debug: vérifier les données des postes
    if postes_bt_raw:
        print(f"[DEBUG] Poste BT trouvé avec distance: {postes_bt_raw[0].get('distance', 'N/A')}")
    else:
        print("[DEBUG] Aucun poste BT trouvé")

    plu_info    = to_feature_collection(ensure_feature_list(get_plu_info(lat, lon, radius=search_radius)))
    parkings    = to_feature_collection(ensure_feature_list(get_parkings_info(lat, lon, radius=search_radius)))
    friches     = to_feature_collection(ensure_feature_list(get_friches_info(lat, lon, radius=search_radius)))
    solaire     = to_feature_collection(ensure_feature_list(get_potentiel_solaire_info(lat, lon, radius=search_radius)))
    zaer        = to_feature_collection(ensure_feature_list(get_zaer_info(lat, lon, radius=search_radius)))
    rpg_data    = to_feature_collection(ensure_feature_list(get_rpg_info(lat, lon, radius=0.0027)))
    sirene_data = to_feature_collection(ensure_feature_list(get_sirene_info(lat, lon, radius=sirene_radius_deg)))

    # 5. APIs externes
    geom_point = {"type": "Point", "coordinates": [lon, lat]}
    radius_km = 0.3  # 300 mètres
    delta = radius_km / 111.0
    search_poly = bbox_to_polygon(lon, lat, delta)
    api_nature = get_api_nature_data(search_poly)
    api_urbanisme_dict = get_all_gpu_data(search_poly)
    # CORRECTION: Utiliser geom_point pour l'API cadastre
    print("🟢 [DEBUG] AVANT APPEL API CADASTRE - CETTE LIGNE DEVRAIT APPARAITRE")
    api_cadastre = get_api_cadastre_data(geom_point)
    print(f"🟢 [DEBUG] APRÈS APPEL API CADASTRE - Résultat: {type(api_cadastre)}")
    api_urbanisme = {k: to_feature_collection(v) for k, v in (api_urbanisme_dict or {}).items()}

    # 6. Validation (avant build_map)
    def validate_feature_list(lst, name):
        if not isinstance(lst, list):
            raise TypeError(f"[VALIDATION] {name} n'est pas une liste: {type(lst)}")
        for i, item in enumerate(lst):
            if not (isinstance(item, dict) and 'geometry' in item and 'properties' in item):
                raise TypeError(f"[VALIDATION] {name}[{i}] n'est pas un Feature dict: {repr(item)[:200]}")

    try:
        validate_feature_list(postes_bt_raw, 'postes_bt_raw')
        validate_feature_list(postes_hta_raw, 'postes_hta_raw')
        validate_feature_list(plu_info.get("features", []), 'plu_info')
        validate_feature_list(parkings.get("features", []), 'parkings')
        validate_feature_list(friches.get("features", []), 'friches')
        validate_feature_list(solaire.get("features", []), 'solaire')
        validate_feature_list(zaer.get("features", []), 'zaer')
        validate_feature_list(rpg_data.get("features", []), 'rpg_data')
        validate_feature_list(sirene_data.get("features", []), 'sirene_data')
    except Exception as e:
        print(f"[VALIDATION ERROR avant build_map] : {e}")
        return jsonify({"error": f"Erreur de validation des données pour build_map: {e}"}), 500

    parcelle = None
    # 7. Recherche info parcelle
    parcelle = get_parcelle_info(lat, lon)
    # Debug: print types and samples of all build_map arguments (now that parcelle is assigned)
    # print("[DEBUG build_map args] parcelle:", type(parcelle or {}), (parcelle or {}) if isinstance(parcelle or {}, dict) else str(parcelle or {})[:200])  # Optimisé pour performance
    # print("[DEBUG build_map args] parcelles_data:", type(parcelles_data), ensure_feature_list(parcelles_data)[:1])  # Optimisé pour performance
    # print("[DEBUG build_map args] postes_bt:", type(postes_bt), ensure_feature_list(postes_bt)[:1])  # Optimisé pour performance
    # print("[DEBUG build_map args] postes_hta:", type(postes_hta), ensure_feature_list(postes_hta)[:1])  # Optimisé pour performance
    # print("[DEBUG build_map args] plu_info:", type(plu_info), ensure_feature_list(plu_info)[:1])  # Optimisé pour performance
    # print("[DEBUG build_map args] parkings:", type(parkings), ensure_feature_list(parkings)[:1])  # Optimisé pour performance
    # print("[DEBUG build_map args] friches:", type(friches), ensure_feature_list(friches)[:1])  # Optimisé pour performance
    # print("[DEBUG build_map args] solaire:", type(solaire), ensure_feature_list(solaire)[:1])  # Optimisé pour performance
    # print("[DEBUG build_map args] zaer:", type(zaer), ensure_feature_list(zaer)[:1])  # Optimisé pour performance
    # print("[DEBUG build_map args] rpg_data:", type(rpg_data), ensure_feature_list(rpg_data)[:1])  # Optimisé pour performance
    # print("[DEBUG build_map args] sirene_data:", type(sirene_data), ensure_feature_list(sirene_data)[:1])  # Optimisé pour performance
    # print("[DEBUG build_map args] capacites_reseau:", type(capacites_reseau), ensure_feature_list(capacites_reseau)[:1])  # Optimisé pour performance

    # 8. GeoRisques: fetch risks for this point
    georisques_risks = fetch_georisques_risks(lat, lon)

    # 8b. Récupération des lignes HTA (aériennes et souterraines) - comme dans search_by_commune
    # print(f"🔌 [HTA] Récupération des lignes HTA pour l'adresse {address}")  # Optimisé pour performance
    hta_lignes_data = {"aerienne": {"features": []}, "souterraine": {"features": []}}
    try:
        from enedis_integration import get_lignes_hta
        
        # Calculer une bbox autour du point de recherche
        delta_hta = 0.05  # Environ 5 km de rayon
        minx = lon - delta_hta
        maxx = lon + delta_hta
        miny = lat - delta_hta
        maxy = lat + delta_hta
        
        # Récupérer les lignes HTA dans cette zone
        hta_lignes_data = get_lignes_hta(
            bbox=[minx, miny, maxx, maxy],
            include_aerienne=True,
            include_souterraine=True,
            limit=800
        )
        aerienne_count = len(hta_lignes_data.get("aerienne", {}).get("features", []))
        souterraine_count = len(hta_lignes_data.get("souterraine", {}).get("features", []))
        # print(f"✅ [HTA] {aerienne_count} lignes aériennes, {souterraine_count} lignes souterraines récupérées")  # Optimisé pour performance
    except Exception as e:
        # print(f"⚠️ [HTA] Erreur lors de la récupération: {e}")  # Optimisé pour performance
        pass

    # 9. Réponse complète
    info_response = {
        "lat": lat, "lon": lon, "address": address,
        "summary": {
            "parcelle_numero": "N/A",
            "distance_poste_proche": "N/A",
            "zone_plu": "N/A",
            "documents_plu": []
        },
        "parcelles": to_feature_collection(parcelles_data),
        "parcelle": parcelle or {},
        "rpg": to_feature_collection(rpg_data),
        "postes_bt": postes_bt,
        "postes_hta": postes_hta,
        "capacites_reseau": capacites_reseau,
        "hta_lignes": hta_lignes_data,  # 🔌 Ajout des lignes HTA pour le frontend
        "plu": to_feature_collection(plu_info),
        "parkings": to_feature_collection(parkings),
        "friches": to_feature_collection(friches),
        "solaire": to_feature_collection(solaire),
        "zaer": to_feature_collection(zaer),
        "sirene": to_feature_collection(sirene_data),
        "api_cadastre": flatten_feature_collections(api_cadastre),
        "api_nature": flatten_feature_collections(api_nature),
        "api_urbanisme": api_urbanisme,   # dict {nom: FeatureCollection}
        "georisques_risks": georisques_risks,
    }

    # 9. Remplissage du résumé
    if parcelle:
        section = parcelle.get("section", "")
        numero = parcelle.get("numero", "")
        code_com = parcelle.get("code_com", "")
        if all([code_com, section, numero]):
            info_response["summary"]["parcelle_numero"] = f"{code_com}{section}{numero}"
    elif api_cadastre.get("features"):
        first_cadastre = api_cadastre["features"][0].get("properties", {})
        print(f"🔍 [DEBUG] Premier cadastre properties: {first_cadastre}")
        section = first_cadastre.get("section", "")
        numero = first_cadastre.get("numero", "")
        print(f"🔍 [DEBUG] Section: '{section}', Numero: '{numero}'")
        if section and numero:
            info_response["summary"]["parcelle_numero"] = f"{section}{numero}"

    if postes_bt_raw:
        closest_bt = postes_bt_raw[0]
        distance = closest_bt.get("distance", "N/A")
        if distance != "N/A":
            info_response["summary"]["distance_poste_proche"] = f"{distance:.1f} m"

    if plu_info and isinstance(plu_info, dict):
        features = plu_info.get("features", [])
        plu_types = [item.get("typeref", "") for item in features if item.get("typeref")]
        if plu_types:
            info_response["summary"]["zone_plu"] = ", ".join(set(plu_types))
        for item in features:
            files = item.get("files", [])
            if files:
                info_response["summary"]["documents_plu"].extend(files)
        info_response["summary"]["documents_plu"] = list(set(info_response["summary"]["documents_plu"]))

    # 10. Carte Folium complète avec tous les calques métiers
    carte_url = None
    map_obj = None
    try:
        print(f"[DEBUG] Génération carte pour {address} - Lat: {lat}, Lon: {lon}")
        print(f"[DEBUG] Données à traiter:")
        print(f"  - Parcelles: {len(ensure_feature_list(parcelles_data))}")
        print(f"  - Postes BT: {len(ensure_feature_list(postes_bt))}")
        print(f"  - Postes HTA: {len(ensure_feature_list(postes_hta))}")
        print(f"  - PLU: {len(ensure_feature_list(plu_info))}")
        print(f"  - Parkings: {len(ensure_feature_list(parkings))}")
        print(f"  - Friches: {len(ensure_feature_list(friches))}")
        print(f"  - Solaire: {len(ensure_feature_list(solaire))}")
        print(f"  - Lignes HTA: {len(hta_lignes_data.get('aerienne', {}).get('features', []))} aériennes, {len(hta_lignes_data.get('souterraine', {}).get('features', []))} souterraines")
        
        map_obj = build_map(
            lat, lon, address,
            parcelle or {},
            ensure_feature_list(parcelles_data),
            ensure_feature_list(postes_bt),
            ensure_feature_list(postes_hta),
            ensure_feature_list(plu_info),
            ensure_feature_list(parkings),
            ensure_feature_list(friches),
            ensure_feature_list(solaire),
            ensure_feature_list(zaer),
            ensure_feature_list(rpg_data),
            ensure_feature_list(sirene_data),
            search_radius, ht_radius_deg,
            api_cadastre=api_cadastre,
            api_nature=api_nature,
            api_urbanisme=api_urbanisme,
            eleveurs_data=None,
            capacites_reseau=ensure_feature_list(capacites_reseau),
            hta_lignes_data=hta_lignes_data  # 🔌 Ajout des lignes HTA comme dans search_by_commune
        )
        
        # 🔒 Créer un nom de fichier sécurisé avec UUID
        carte_filename = generate_secure_filename("recherche", address)
        
        try:
            carte_url = save_map_html(map_obj, carte_filename)
            print(f"[DEBUG] Carte Folium sauvée: {carte_url}")
        except Exception as save_error:
            logging.error(f"[search_by_address] Erreur save_map_html: {save_error}")
            print(f"[DEBUG] Erreur save_map_html: {save_error}")
            carte_url = None
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("[search_by_address] Erreur build_map :", e)
        logging.error(f"[search_by_address] Erreur build_map: {e}\nTraceback:\n{tb}")
        return jsonify({"error": f"Erreur build_map: {e}", "traceback": tb}), 500

    # Validation JSON avant retour pour éviter les erreurs de sérialisation
    try:
        import json
        json.dumps(info_response)
    except (TypeError, ValueError) as json_error:
        logging.error(f"[search_by_address] Erreur JSON serialization: {json_error}")
        return jsonify({"error": "Erreur de sérialisation des données", "details": str(json_error)}), 500

    # Validation et correction: s'assurer qu'une carte Folium soit toujours générée
    if not carte_url:
        print(f"[WARNING] Génération carte échouée, retry avec carte simple...")
        try:
            # Régénérer une carte Folium avec au moins les données de base et zoom étendu
            import folium
            simple_map = folium.Map(location=[lat, lon], zoom_start=13, tiles=None, max_zoom=22)
            
            # Fonds de carte
            folium.TileLayer(
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri World Imagery", name="Satellite", overlay=False, control=True, show=True, max_zoom=22
            ).add_to(simple_map)
            folium.TileLayer("OpenStreetMap", name="OSM", overlay=False, control=True, show=False, max_zoom=19).add_to(simple_map)
            
            # Point de recherche
            folium.Marker([lat, lon], popup=f"📍 {address}").add_to(simple_map)
            
            # Ajouter LayerControl
            folium.LayerControl().add_to(simple_map)
            
            simple_filename = f"simple_map_{int(time.time())}.html"
            carte_url = save_map_html(simple_map, simple_filename)
            print(f"[DEBUG] Carte simple générée: {carte_url}")
        except Exception as e:
            print(f"[ERROR] Impossible de générer même une carte simple: {e}")
            carte_url = None

    info_response["carte_url"] = f"/static/{carte_url}" if carte_url else "/static/map.html"
    print(f"[DEBUG] URL finale de carte: {info_response['carte_url']}")
    
    # Force le rechargement en ajoutant un timestamp pour éviter le cache
    import time
    if carte_url and "map_" in carte_url:
        info_response["carte_url"] += f"?t={int(time.time())}"
        print(f"[DEBUG] URL avec cache bust: {info_response['carte_url']}")
    
    # Sauvegarder la carte avec toutes les données de recherche pour permettre le zoom  
    try:
        save_map_to_cache(map_obj, info_response)
    except Exception as cache_error:
        logging.error(f"[search_by_address] Erreur save_map_to_cache: {cache_error}")
    
    return jsonify(info_response)


@app.route('/rapport_departement_post', methods=['POST'])
@app.route("/rapport_departement", methods=["POST"])
def rapport_departement_post():
    """
    Route POST corrigée pour le rapport départemental avec limitation de données
    """
    import time
    
    try:
        data = request.get_json()
        reports = data.get("data", [])
        
        print(f"[RAPPORT_DEPT] Traitement de {len(reports)} rapports communaux")
        
        # Détection du département
        dept = None
        for rpt in reports:
            if "dept" in rpt and rpt["dept"]:
                dept = rpt["dept"]
                break
        
        print(f"[RAPPORT_DEPT] Département détecté: {dept}")
        
        # LIMITATION: Réduire les données dans chaque rapport pour éviter HTTP/2 protocol error
        # Ne garder que les premières parcelles de chaque commune (max 20)
        limited_reports = []
        for rpt in reports:
            limited_rpt = rpt.copy()
            
            # Limiter les parcelles RPG
            if "rpg_parcelles" in limited_rpt and isinstance(limited_rpt["rpg_parcelles"], dict):
                features = limited_rpt["rpg_parcelles"].get("features", [])
                if len(features) > 20:
                    limited_rpt["rpg_parcelles"]["features"] = features[:20]
                    print(f"[RAPPORT_DEPT] {rpt.get('commune', 'N/A')}: Limité à 20 parcelles (sur {len(features)})")
            
            # Limiter les éleveurs
            if "eleveurs" in limited_rpt and isinstance(limited_rpt["eleveurs"], dict):
                features = limited_rpt["eleveurs"].get("features", [])
                if len(features) > 10:
                    limited_rpt["eleveurs"]["features"] = features[:10]
                    print(f"[RAPPORT_DEPT] {rpt.get('commune', 'N/A')}: Limité à 10 éleveurs (sur {len(features)})")
            
            # Limiter les postes BT
            if "postes_bt" in limited_rpt and isinstance(limited_rpt["postes_bt"], dict):
                features = limited_rpt["postes_bt"].get("features", [])
                if len(features) > 10:
                    limited_rpt["postes_bt"]["features"] = features[:10]
            
            # Limiter les postes HTA
            if "postes_hta" in limited_rpt and isinstance(limited_rpt["postes_hta"], dict):
                features = limited_rpt["postes_hta"].get("features", [])
                if len(features) > 10:
                    limited_rpt["postes_hta"]["features"] = features[:10]
            
            # Limiter les capacités HTA
            if "hta_capacites" in limited_rpt and isinstance(limited_rpt["hta_capacites"], dict):
                features = limited_rpt["hta_capacites"].get("features", [])
                if len(features) > 10:
                    limited_rpt["hta_capacites"]["features"] = features[:10]
            
            limited_reports.append(limited_rpt)
        
        # Utilisation de la fonction synthese_departement corrigée
        synthese = synthese_departement(limited_reports)
        
        # Enrichissement SIRET limité (max 10 pour éviter timeout)
        def enrich_eleveurs_with_siret(eleveurs_features):
            """
            Enrichit les éleveurs avec les données SIRET
            Utilise le threading pour paralléliser les appels (beaucoup plus rapide)
            """
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            print(f"[RAPPORT_DEPT] Début enrichissement SIRET pour {len(eleveurs_features)} éleveurs")
            start_time = time.time()
            
            def enrich_one(feat):
                """Enrichit un seul éleveur (appelé en parallèle)"""
                props = feat.get("properties", {})
                siret = props.get("siret") or props.get("SIRET")
                
                if siret:
                    try:
                        # Timeout très court (0.5s) et pas de retry
                        sirene_info = fetch_sirene_info(siret, max_retries=0, timeout=0.5)
                        if sirene_info:
                            props.update(sirene_info)
                            props["siret_enriched"] = True
                            return feat, True
                        else:
                            props["siret_enriched"] = False
                    except Exception:
                        props["siret_enriched"] = False
                else:
                    props["siret_enriched"] = False
                
                return feat, False
            
            enriched = []
            success_count = 0
            
            # Utiliser 20 threads pour paralléliser (20 appels simultanés)
            with ThreadPoolExecutor(max_workers=20) as executor:
                # Soumettre tous les enrichissements
                future_to_feat = {executor.submit(enrich_one, feat): feat for feat in eleveurs_features}
                
                # Récupérer les résultats au fur et à mesure
                for future in as_completed(future_to_feat):
                    feat, success = future.result()
                    enriched.append(feat)
                    if success:
                        success_count += 1
            
            elapsed = time.time() - start_time
            print(f"[RAPPORT_DEPT] Enrichissement terminé: {success_count}/{len(eleveurs_features)} en {elapsed:.1f}s")
            return enriched
        
        # Correction des distances "N/A m" dans le TOP 50
        def fix_distances_in_top50(top50_features):
            """Corrige les distances affichées comme 'N/A m'"""
            fixed = []
            for feat in top50_features:
                props = feat.get("properties", {})
                
                # Calcul de la distance minimale
                min_distance = None
                distance_sources = ["distance_bt", "distance_au_poste", "distance_hta", "min_distance_bt_m", "min_distance_hta_m"]
                
                for key in distance_sources:
                    val = props.get(key)
                    if val is not None and isinstance(val, (int, float)) and val > 0:
                        if min_distance is None or val < min_distance:
                            min_distance = val
                
                # Mise à jour des propriétés de distance
                if min_distance is not None:
                    props["distance_formatted"] = f"{int(min_distance)} m"
                    props["distance_valid"] = True
                else:
                    props["distance_formatted"] = "Distance non calculée"
                    props["distance_valid"] = False
                
                fixed.append(feat)
            return fixed
        
        # Application des corrections
        top50_corrected = fix_distances_in_top50(synthese["top50_parcelles"])
        synthese["top50_parcelles"] = top50_corrected
        
        # Enrichissement des éleveurs du département (limité)
        all_eleveurs = []
        for rpt in limited_reports:
            fc_e = rpt.get("eleveurs", {})
            if fc_e and isinstance(fc_e, dict) and "features" in fc_e:
                all_eleveurs.extend(fc_e.get("features", []))
        
        # Limiter à 100 éleveurs max pour l'enrichissement
        if len(all_eleveurs) > 100:
            print(f"[RAPPORT_DEPT] Limitation des éleveurs: {len(all_eleveurs)} -> 100")
            all_eleveurs = all_eleveurs[:100]
        
        all_eleveurs_enriched = enrich_eleveurs_with_siret(all_eleveurs)
        
        # Correction des liens cadastre dans le TOP 50
        def fix_cadastre_links(top50_features):
            """Corrige les liens vers le cadastre"""
            for feat in top50_features:
                props = feat.get("properties", {})
                
                # Construction du lien cadastre
                code_commune = props.get("code_com") or props.get("com_abs")
                section = props.get("section") or props.get("cadastre_section")
                numero = props.get("numero") or props.get("cadastre_numero") or props.get("numero_parcelle")
                
                if code_commune and section and numero and numero != "N/A":
                    cadastre_url = f"https://www.cadastre.gouv.fr/scpc/accueil.do#c={code_commune}&sec={section}&n={numero}"
                    props["cadastre_link"] = cadastre_url
                    props["cadastre_link_valid"] = True
                else:
                    props["cadastre_link"] = None
                    props["cadastre_link_valid"] = False
            
            return top50_features
        
        synthese["top50_parcelles"] = fix_cadastre_links(synthese["top50_parcelles"])
        
        print(f"[RAPPORT_DEPT] Synthèse finale: {synthese['total_eleveurs']} éleveurs, {synthese['total_parcelles']} parcelles")
        print(f"[RAPPORT_DEPT] TOP 50 avec {len(synthese['top50_parcelles'])} parcelles")
        print(f"[RAPPORT_DEPT] Clés synthèse: {list(synthese.keys())}")
        print(f"[RAPPORT_DEPT] nb_agriculteurs: {synthese.get('nb_agriculteurs')}")
        print(f"[RAPPORT_DEPT] nb_parcelles: {synthese.get('nb_parcelles')}")
        print(f"[RAPPORT_DEPT] Transmission au template: synthese={bool(synthese)}, dept={dept}")
        print(f"[RAPPORT_DEPT] Nombre de rapports limités: {len(limited_reports)}")
        
        # Générer le rapport avec données limitées
        try:
            html = render_template(
                "rapport_departement_complet.html",
                reports=limited_reports,
                dept=dept,
                synthese=synthese,
                eleveurs_enriched=all_eleveurs_enriched
            )
            
            # Vérifier la taille du HTML généré
            html_size_mb = len(html.encode('utf-8')) / (1024 * 1024)
            print(f"[RAPPORT_DEPT] Taille HTML générée: {html_size_mb:.2f} MB")
            
            if html_size_mb > 10:
                print(f"[RAPPORT_DEPT] ATTENTION: HTML très volumineux ({html_size_mb:.2f} MB)")
                # Si trop volumineux, générer un rapport simplifié
                return render_template(
                    "rapport_departement_simple.html",
                    reports=limited_reports,
                    dept=dept,
                    synthese=synthese
                )
            
            return html
            
        except Exception as template_error:
            print(f"[RAPPORT_DEPT] Erreur template: {template_error}")
            import traceback
            traceback.print_exc()
            
            # Fallback: Rapport minimal en cas d'erreur
            return f"""
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <title>Rapport département {dept or ''}</title>
            </head>
            <body>
                <h1>Rapport du département {dept or ''}</h1>
                <p><strong>Erreur lors de la génération du rapport détaillé.</strong></p>
                <p>Nombre de communes: {len(limited_reports)}</p>
                <p>Total parcelles: {synthese.get('total_parcelles', 0)}</p>
                <p>Total agriculteurs: {synthese.get('total_eleveurs', 0)}</p>
                <p>Erreur: {str(template_error)}</p>
            </body>
            </html>
            """
        
    except Exception as e:
        print(f"[RAPPORT_DEPT] Erreur globale: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/export_map")
def export_map():
    # Supposons que last_map_params["html"] ou map_obj existent
    map_obj = ...  # Génère ou récupère la carte courante
    save_map_html(map_obj, "cartes.html")
    return send_file("cartes.html")

@app.route("/carte_risques")
def carte_risques():
    """Génère une carte interactive des risques GeoRisques pour un point donné"""
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    
    if not lat or not lon:
        return jsonify({"error": "Paramètres lat et lon requis"}), 400
    
    try:
        # Récupérer les risques GeoRisques
        georisques_risks = fetch_georisques_risks(lat, lon)
        
        # Couleurs par catégorie de risque
        risk_colors = {
            'sismique': 'purple',
            'tri_zonage': 'blue', 
            'tri_gaspar': 'lightblue',
            'ssp_casias': 'orange',
            'ssp_instructions': 'red',
            'ssp_conclusions_sis': 'darkred',
            'ssp_conclusions_sup': 'pink',
            'casias_detaille': 'cadetblue',
            'tim': 'green',
            'azi': 'lightgreen',
            'catnat': 'beige',
            'cavites': 'gray',
            'mvt': 'darkgreen',
            'argiles': 'brown',
            'radon': 'yellow',
            'installations': 'black',
            'nucleaire': 'darkblue'
        }
        
        # Ajouter les risques géolocalisés
        risks_added = 0
        for category, risks in georisques_risks.items():
            if not risks:
                continue
                
            color = risk_colors.get(category, 'gray')
            
            for risk in risks:
                if not risk.get('geom'):
                    continue
                    
                geom = risk['geom']
                risk_name = (risk.get('libelle_risque_long') or 
                           risk.get('libelle_tri') or 
                           risk.get('nom') or 
                           risk.get('zone_sismicite') or 
                           risk.get('libelle') or 
                           f'Risque {category}')
                
                popup_content = f"""
                <div style="min-width: 200px;">
                    <h6><strong>{risk_name}</strong></h6>
                    <p><strong>Catégorie:</strong> {category}</p>
                    <p><strong>Type géométrie:</strong> {geom['type']}</p>
                """
                
                if risk.get('code_insee'):
                    popup_content += f"<p><strong>Commune:</strong> {risk.get('libelle_commune', risk['code_insee'])}</p>"
                if risk.get('date_transmission'):
                    popup_content += f"<p><strong>Date:</strong> {risk['date_transmission']}</p>"
                    
                popup_content += "</div>"
                
                if geom['type'] == 'Point':
                    folium.CircleMarker(
                        location=[geom['coordinates'][1], geom['coordinates'][0]],
                        radius=8,
                        popup=safe_folium_popup(popup_content, max_width=250),
                        color=color,
                        fillColor=color,
                        fillOpacity=0.7,
                        weight=2
                    ).add_to(carte)
                    risks_added += 1
                    
                elif geom['type'] in ['Polygon', 'MultiPolygon']:
                    try:
                        # Convertir les coordonnées pour Folium
                        if geom['type'] == 'Polygon':
                            coords = [[coord[1], coord[0]] for coord in geom['coordinates'][0]]
                            folium.Polygon(
                                locations=coords,
                                popup=safe_folium_popup(popup_content, max_width=250),
                                color=color,
                                fillColor=color,
                                fillOpacity=0.3,
                                weight=2
                            ).add_to(carte)
                        else:  # MultiPolygon
                            for polygon in geom['coordinates']:
                                coords = [[coord[1], coord[0]] for coord in polygon[0]]
                                folium.Polygon(
                                    locations=coords,
                                    popup=safe_folium_popup(popup_content, max_width=250),
                                    color=color,
                                    fillColor=color,
                                    fillOpacity=0.3,
                                    weight=2
                                ).add_to(carte)
                        risks_added += 1
                    except Exception as e:
                        print(f"Erreur lors de l'ajout du polygone {category}: {e}")
        
        # Ajouter une légende
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h5>Risques GeoRisques</h5>
        <p><i class="fa fa-crosshairs" style="color:red"></i> Point de référence</p>
        <p><i class="fa fa-circle" style="color:orange"></i> Sites pollués</p>
        <p><i class="fa fa-circle" style="color:blue"></i> Inondations</p>
        <p><i class="fa fa-circle" style="color:purple"></i> Risque sismique</p>
        <p><i class="fa fa-circle" style="color:green"></i> Autres risques</p>
        <small>Total: ''' + str(risks_added) + ''' risques géolocalisés</small>
        </div>
        '''
        carte.get_root().html.add_child(folium.Element(legend_html))
        
        # Sauvegarder et retourner
        filename = f"carte_risques_{lat}_{lon}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        map_path = save_map_html(carte, filename)
        
        return render_template('display_map.html', map_path=map_path, 
                             title=f"Carte des Risques - {lat}, {lon}",
                             risks_count=risks_added)
        
    except Exception as e:
        print(f"Erreur création carte risques: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/test_api_nature")
def test_api_nature():
    """Route de test pour l'API Nature IGN"""
    try:
        lat = float(request.args.get("lat", 43.00))
        lon = float(request.args.get("lon", 6.39))
        
        # Créer une géométrie point
        geom = {
            "type": "Point", 
            "coordinates": [lon, lat]
        }
        
        print(f"🔍 [TEST API NATURE] === TEST API NATURE IGN ===")
        print(f"🔍 [TEST API NATURE] Coordonnées: {lat}, {lon}")
        
        # Test des différents endpoints nature selon la documentation officielle
        endpoints = [
            "/nature/natura-habitat",
            "/nature/natura-oiseaux", 
            "/nature/znieff1",
            "/nature/znieff2",
            "/nature/pn",
            "/nature/pnr",
            "/nature/rnn",
            "/nature/rnc",
            "/nature/rncf"
        ]
        
        results = {}
        for endpoint in endpoints:
            print(f"🔍 [TEST API NATURE] Test endpoint: {endpoint}")
            data = get_api_nature_data(geom, endpoint)
            if data and data.get("features"):
                results[endpoint] = {
                    "count": len(data["features"]),
                    "features": data["features"][:3]  # Premiers résultats seulement
                }
                print(f"🔍 [TEST API NATURE] {endpoint}: {len(data['features'])} résultats")
            else:
                results[endpoint] = {"count": 0, "features": []}
                print(f"🔍 [TEST API NATURE] {endpoint}: aucun résultat")
        
        return jsonify(results)
        
    except Exception as e:
        print(f"🔍 [TEST API NATURE] Erreur: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/test_rapport_nature")
def test_rapport_nature():
    """Route de test pour vérifier l'affichage des données nature dans le rapport"""
    
    # Simuler des données API Nature telles qu'elles devraient être dans api_details
    test_api_details = {
        "nature": {
            "success": True,
            "data": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "NOM": "ÎLE DE PORT-CROS ET DE BAGAUD",
                            "TYPE_PROTECTION": "ZNIEFF Type 1",
                            "TYPE": "Zone naturelle d'intérêt écologique",
                            "STATUT": "Protégée",
                            "SUPERFICIE": "650 ha"
                        },
                        "geometry": {"type": "Point", "coordinates": [6.396759, 43.006497]}
                    },
                    {
                        "type": "Feature", 
                        "properties": {
                            "NOM": "Port-Cros",
                            "TYPE_PROTECTION": "Parcs Nationaux",
                            "TYPE": "Parc National",
                            "STATUT": "Protégé",
                            "SUPERFICIE": "1700 ha"
                        },
                        "geometry": {"type": "Point", "coordinates": [6.396759, 43.006497]}
                    }
                ]
            },
            "count": 2,
            "error": None
        }
    }
    
    # Créer un rapport minimal pour tester le template
    test_report = {
        "lat": 43.006497,
        "lon": 6.396759,
        "address": "Test Hyères API Nature",
        "api_details": test_api_details
    }
    
    return render_template("rapport_point.html", report=test_report)

@app.route("/debug_api_nature")
def debug_api_nature():
    """Route de debug pour tester les API Nature avec plusieurs coordonnées test"""
    
    # Points de test avec des zones naturelles connues
    test_points = [
        (43.006497, 6.396759, "Hyères - Point utilisateur"),
        (44.12, 7.24, "Parc National du Mercantour"),
        (43.93, 4.75, "Camargue - Réserve de Biosphère"),
        (46.34, 6.03, "Réserve Naturelle du Bout du Lac"),
        (43.95, 6.95, "Parc National des Écrins - Zone Sud"),
    ]
    
    results = {}
    
    for lat, lon, location_name in test_points:
        print(f"🔍 [DEBUG API NATURE] === TEST {location_name} ===")
        print(f"🔍 [DEBUG API NATURE] Coordonnées: {lat}, {lon}")
        
        geom = {"type": "Point", "coordinates": [lon, lat]}
        point_results = {}
        all_features = []
        
        # Test de quelques endpoints clés
        key_endpoints = [
            ("/nature/pn", "Parcs Nationaux"),
            ("/nature/pnr", "Parcs Naturels Régionaux"),
            ("/nature/natura-habitat", "Natura 2000 Directive Habitat"),
            ("/nature/znieff1", "ZNIEFF Type 1"),
            ("/nature/rnn", "Réserves Naturelles Nationales")
        ]
        
        for endpoint, type_name in key_endpoints:
            try:
                url = f"https://apicarto.ign.fr/api{endpoint}"
                params = {"geom": json.dumps(geom), "_limit": 100}
                
                import requests
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    feature_count = len(data.get("features", []))
                    point_results[endpoint] = {
                        "status": "success",
                        "count": feature_count
                    }
                    
                    if feature_count > 0:
                        print(f"🔍 [DEBUG API NATURE] {location_name} - {endpoint}: {feature_count} zones trouvées")
                        for feature in data["features"]:
                            if "properties" not in feature:
                                feature["properties"] = {}
                            feature["properties"]["TYPE_PROTECTION"] = type_name
                        all_features.extend(data["features"])
                    else:
                        print(f"🔍 [DEBUG API NATURE] {location_name} - {endpoint}: 0 zones")
                else:
                    point_results[endpoint] = {
                        "status": "error",
                        "code": response.status_code
                    }
                    print(f"🔍 [DEBUG API NATURE] {location_name} - {endpoint}: Erreur {response.status_code}")
                    
            except Exception as e:
                point_results[endpoint] = {
                    "status": "exception",
                    "error": str(e)
                }
                print(f"🔍 [DEBUG API NATURE] {location_name} - {endpoint}: Exception {e}")
        
        # Test de la fonction complète pour ce point
        try:
            print(f"🔍 [DEBUG API NATURE] Test get_all_api_nature_data pour {location_name}...")
            nature_data = get_all_api_nature_data(geom)
            final_count = len(nature_data.get('features', [])) if nature_data else 0
            print(f"🔍 [DEBUG API NATURE] {location_name} - get_all_api_nature_data: {final_count} features totales")
            
            point_results["total_from_function"] = final_count
        except Exception as e:
            print(f"🔍 [DEBUG API NATURE] {location_name} - get_all_api_nature_data: Erreur {e}")
            point_results["total_from_function"] = 0
            
        results[location_name] = {
            "coordinates": [lat, lon],
            "endpoints": point_results,
            "total_features_manual": len(all_features)
        }
    
    return jsonify({
        "status": "multi_point_debug_complete",
        "test_results": results
    })

@app.route("/debug_capacites_fields")
def debug_capacites_fields():
    """Route de debug pour voir tous les champs disponibles dans les capacités HTA"""
    try:
        lat = float(request.args.get("lat", 43.13))
        lon = float(request.args.get("lon", 6.37))
        
        print(f"🔍 [DEBUG FIELDS] === DEBUG CHAMPS CAPACITÉS HTA ===")
        print(f"🔍 [DEBUG FIELDS] Coordonnées: {lat}, {lon}")
        
        # Récupération des capacités brutes
        capacites_raw = get_all_capacites_reseau(lat, lon, radius_deg=0.5)
        
        if capacites_raw:
            print(f"🔍 [DEBUG FIELDS] {len(capacites_raw)} capacités trouvées")
            
            # Analyse du premier élément pour voir tous les champs
            first_capacity = capacites_raw[0]
            props = first_capacity.get('properties', {})
            
            print(f"🔍 [DEBUG FIELDS] Tous les champs disponibles:")
            fields_info = {}
            for key, value in props.items():
                print(f"🔍 [DEBUG FIELDS] - {key}: {value}")
                fields_info[key] = str(value)
            
            # Recherche de champs liés aux coûts
            cost_fields = {}
            for key, value in props.items():
                key_lower = key.lower()
                if any(cost_word in key_lower for cost_word in ['cout', 'cost', 'prix', 'price', 'euro', '€', 'quote', 'tarif']):
                    cost_fields[key] = str(value)
                    print(f"💰 [DEBUG FIELDS] Champ coût potentiel: {key} = {value}")
            
            return jsonify({
                "total_capacities": len(capacites_raw),
                "all_fields": fields_info,
                "potential_cost_fields": cost_fields,
                "hta_mapping_keys": list(hta_mapping.keys())
            })
        else:
            return jsonify({"error": "Aucune capacité trouvée"})
        
    except Exception as e:
        print(f"🔍 [DEBUG FIELDS] Erreur: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/debug_cout_hta")
def debug_cout_hta():
    """Route de debug spécifique pour analyser les coûts HTA"""
    try:
        lat = float(request.args.get("lat", 43.13))
        lon = float(request.args.get("lon", 6.37))
        
        print(f"💰 [DEBUG COUT] === ANALYSE COÛTS HTA ===")
        print(f"💰 [DEBUG COUT] Coordonnées: {lat}, {lon}")
        
        # Récupération des capacités brutes
        capacites_raw = get_all_capacites_reseau(lat, lon, radius_deg=0.5)
        
        if capacites_raw:
            print(f"💰 [DEBUG COUT] {len(capacites_raw)} capacités trouvées")
            
            cost_analysis = []
            for i, capacity in enumerate(capacites_raw[:3]):  # Analyser les 3 premières
                props = capacity.get('properties', {})
                
                # Recherche de tous les champs potentiellement liés aux coûts
                cost_info = {
                    "capacity_index": i + 1,
                    "nom": props.get('Nom', 'N/A'),
                    "code": props.get('Code', 'N/A')
                }
                
                # Champs de coût potentiels
                cost_fields = [
                    'Quote-Part', 'Quote_Part', 'QuotePart',
                    'Cout', 'Cost', 'Prix', 'Price', 
                    'Tarif', 'Euro', '€'
                ]
                
                for field in props.keys():
                    if any(cost_word.lower() in field.lower() for cost_word in cost_fields):
                        cost_info[f"field_{field}"] = props[field]
                        print(f"💰 [DEBUG COUT] Capacité {i+1} - {field}: {props[field]}")
                
                # Champs spécifiques du mapping
                for display_name, db_field in hta_mapping.items():
                    if 'quote' in display_name.lower() or 'cout' in display_name.lower() or 'prix' in display_name.lower():
                        value = props.get(db_field, 'N/A')
                        cost_info[f"mapping_{display_name}"] = value
                        print(f"💰 [DEBUG COUT] Mapping {display_name} ({db_field}): {value}")
                
                cost_analysis.append(cost_info)
            
            return jsonify({
                "total_capacities": len(capacites_raw),
                "cost_analysis": cost_analysis,
                "hta_mapping_cost_fields": {k: v for k, v in hta_mapping.items() if 'quote' in k.lower() or 'cout' in k.lower()}
            })
        else:
            return jsonify({"error": "Aucune capacité trouvée"})
        
    except Exception as e:
        print(f"💰 [DEBUG COUT] Erreur: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# SYSTÈME CRM - INITIALISATION BASE DE DONNÉES
# ============================================================================

# 🔗 INTÉGRATION AVEC KPI SUNSTICE - Utiliser la base CRM existante
# Sur Railway, utiliser une variable d'environnement ou créer la base dans un dossier persistant
CRM_DB_PATH = os.getenv('KPI_DATABASE_PATH', os.path.join(os.path.dirname(__file__), '..', 'KPI', 'kpi_sunstice.db'))

def init_crm_database():
    """Initialise la table agriweb_prospects dans la base KPI Sunstice existante"""
    crm_db_path = CRM_DB_PATH
    
    # Sur Railway, créer le dossier si nécessaire
    db_dir = os.path.dirname(crm_db_path)
    if not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
            print(f"📁 [CRM] Dossier créé: {db_dir}")
        except Exception as e:
            print(f"⚠️ [CRM] Erreur création dossier {db_dir}: {e}")
    
    if not os.path.exists(crm_db_path):
        print(f"⚠️ Base KPI non trouvée à {crm_db_path}")
        print(f"   Création d'une nouvelle base de données CRM")
        # Créer une nouvelle base si elle n'existe pas
        # crm_db_path reste inchangé pour utiliser le chemin défini
    
    conn = sqlite3.connect(crm_db_path)
    cursor = conn.cursor()
    
    # Créer la table pour les prospects AgriWeb dans la base KPI
    print(f"📊 [CRM] Initialisation table agriweb_prospects dans {crm_db_path}")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agriweb_prospects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            commune TEXT NOT NULL,
            departement TEXT,
            adresse TEXT,
            latitude REAL,
            longitude REAL,
            surface_m2 REAL,
            surface_ha REAL,
            parcelles_cadastrales TEXT,
            poste_bt_distance_m REAL,
            poste_hta_distance_m REAL,
            lien_streetview TEXT,
            lien_annuaire TEXT,
            statut TEXT DEFAULT 'nouveau',
            priorite TEXT DEFAULT 'moyenne',
            notes TEXT,
            nom_prospect TEXT,
            contact_nom TEXT,
            contact_email TEXT,
            contact_telephone TEXT,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_json TEXT
        )
    ''')
    
    # Index pour recherches rapides sur la table agriweb_prospects
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_agriweb_commune ON agriweb_prospects(commune)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_agriweb_type ON agriweb_prospects(type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_agriweb_statut ON agriweb_prospects(statut)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_agriweb_departement ON agriweb_prospects(departement)')
    
    # Tables complémentaires pour le CRM
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prospect_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER NOT NULL,
            type_action TEXT NOT NULL,
            description TEXT,
            date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prospect_id) REFERENCES agriweb_prospects(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prospect_appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER NOT NULL,
            date_rdv TEXT NOT NULL,
            type_rdv TEXT NOT NULL,
            notes TEXT,
            statut TEXT DEFAULT 'prevu',
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prospect_id) REFERENCES agriweb_prospects(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prospect_proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER NOT NULL,
            puissance_kwc REAL,
            prix_kwc REAL,
            production_kwh_kwc REAL,
            tarif_rachat REAL,
            investissement_total REAL,
            production_annuelle REAL,
            revenus_annuels REAL,
            rentabilite_pct REAL,
            roi_annees REAL,
            notes TEXT,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prospect_id) REFERENCES agriweb_prospects(id) ON DELETE CASCADE
        )
    ''')
    
    # Table des fiches projets autoconsommation
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_fiches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER NOT NULL,
            nom_projet TEXT NOT NULL,
            type_projet TEXT DEFAULT 'autoconsommation',
            client_nom TEXT,
            client_email TEXT,
            client_telephone TEXT,
            client_adresse TEXT,
            adresse_projet TEXT,
            parcelles_cadastrales TEXT,
            statut_global TEXT DEFAULT 'en_cours',
            date_debut TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_fin_prevue TEXT,
            date_fin_reelle TEXT,
            responsable TEXT,
            notes TEXT,
            FOREIGN KEY (prospect_id) REFERENCES agriweb_prospects(id) ON DELETE CASCADE
        )
    ''')
    
    # Ajouter les colonnes si elles n'existent pas (migration)
    try:
        cursor.execute('ALTER TABLE project_fiches ADD COLUMN adresse_projet TEXT')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE project_fiches ADD COLUMN parcelles_cadastrales TEXT')
    except:
        pass
    
    # Table des étapes du projet (workflow autoconsommation)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            etape_nom TEXT NOT NULL,
            etape_ordre INTEGER NOT NULL,
            statut TEXT DEFAULT 'a_faire',
            date_debut TEXT,
            date_fin TEXT,
            responsable TEXT,
            notes TEXT,
            FOREIGN KEY (project_id) REFERENCES project_fiches(id) ON DELETE CASCADE
        )
    ''')
    
    # Table des documents du projet
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            etape_id INTEGER,
            type_document TEXT NOT NULL,
            nom_fichier TEXT NOT NULL,
            chemin_fichier TEXT,
            url_document TEXT,
            statut TEXT DEFAULT 'brouillon',
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            version INTEGER DEFAULT 1,
            notes TEXT,
            FOREIGN KEY (project_id) REFERENCES project_fiches(id) ON DELETE CASCADE,
            FOREIGN KEY (etape_id) REFERENCES project_steps(id) ON DELETE SET NULL
        )
    ''')
    
    # Index pour les projets
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_prospect ON project_fiches(prospect_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_statut ON project_fiches(statut_global)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_steps ON project_steps(project_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_docs ON project_documents(project_id)')
    
    conn.commit()
    conn.close()
    print("✅ [CRM] Tables CRM et Projets prêtes dans la base KPI Sunstice!")

# ============================================================================

def open_browser():
    # Protection contre l'ouverture multiple de navigateurs
    if hasattr(open_browser, '_opened'):
        return
    open_browser._opened = True
    webbrowser.open_new("http://127.0.0.1:5000")

def main():
    try:
        # Import des utilisateurs existants au démarrage
        print("🔄 Import des utilisateurs existants...")
        import_existing_users()
        
        # Initialisation de la base CRM
        init_crm_database()
        
        print("Routes disponibles:")
        pprint.pprint(list(app.url_map.iter_rules()))
        
        # Vérification si on est en mode Railway
        port = int(os.environ.get("PORT", 5000))
        host = "0.0.0.0" if "PORT" in os.environ else "127.0.0.1"
        
        # Pas d'ouverture de navigateur en production
        if host == "127.0.0.1":
            Timer(1, open_browser).start()
            
        print(f"🚀 Démarrage AgriWeb sur {host}:{port}")
        
        # Lancer le serveur Flask
        app.run(host=host, port=port, debug=False)  # Debug False pour éviter les reloads multiples
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("[main] Startup error:", e)
        logging.error(f"[main] Startup error: {e}\nTraceback:\n{tb}")

@app.route("/debug_toitures_ui")
def debug_toitures_ui():
    """Interface de debug pour la recherche de toitures"""
    try:
        with open("debug_toitures_ui.html", "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"<h1>Erreur</h1><p>Impossible de charger l'interface de debug: {e}</p>", 500

@app.route("/test_toitures_debug")
def test_toitures_debug():
    """Interface de test détaillé pour diagnostiquer les problèmes de toitures"""
    try:
        with open("test_toitures_debug.html", "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"<h1>Erreur</h1><p>Impossible de charger l'interface de test: {e}</p>", 500

@app.route("/test_sliders_toitures")
def test_sliders_toitures():
    """Interface de test spécifique pour les sliders de toitures"""
    try:
        with open("test_sliders_toitures.html", "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"<h1>Erreur</h1><p>Impossible de charger l'interface de test sliders: {e}</p>", 500

def generate_integrated_commune_report(commune_name, filters=None):
    """
    Génère un rapport complet intégré utilisant les fonctions existantes d'agriweb_source.py
    Cette version fallback fonctionne même si rapport_commune_complet.py n'est pas disponible
    """
    from datetime import datetime
    import json
    import time
    import re
    from urllib.parse import quote_plus
    from shapely.geometry import shape, Point
    from shapely.ops import transform as shp_transform
    from pyproj import Transformer
    import folium
    
    if filters is None:
        filters = {}
    
    print(f"📊 [RAPPORT_INTÉGRÉ] Génération du rapport pour {commune_name}")
    
    try:
        start_ts = time.time()
        # 1. Récupération des informations de base de la commune
        commune_infos = requests.get(
            f"https://geo.api.gouv.fr/communes?nom={quote_plus(commune_name)}&fields=centre,contour,population,codesPostaux,departement"
        ).json()
        
        if not commune_infos:
            return {"error": f"Commune '{commune_name}' introuvable"}
        
        commune_info = commune_infos[0]
        contour = commune_info.get("contour")
        centre = commune_info.get("centre")
        
        if not contour or not centre:
            return {"error": f"Données géographiques manquantes pour {commune_name}"}
        
        lat, lon = centre["coordinates"][1], centre["coordinates"][0]
        commune_poly = shape(contour)
        
        # Transformer pour calculer la superficie
        to_l93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True).transform
        superficie_ha = shp_transform(to_l93, commune_poly).area / 10000.0
        
        # 2. Optimisation géométrique pour éviter les erreurs 414
        def optimize_geometry_for_api(geom):
            geom_json = json.dumps(geom)
            if len(geom_json) > 4000:
                print(f"🔧 [RAPPORT_INTÉGRÉ] Géométrie optimisée ({len(geom_json)} chars)")
                shp_geom = shape(geom)
                minx, miny, maxx, maxy = shp_geom.bounds
                return {
                    "type": "Polygon",
                    "coordinates": [[
                        [minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy], [minx, miny]
                    ]]
                }
            return geom
        
        contour_optimise = optimize_geometry_for_api(contour)
        
    # 3. Collecte des données avec les fonctions existantes
        print(f"📊 [RAPPORT_INTÉGRÉ] Collecte des données...")
        
        # Données de base
        minx, miny, maxx, maxy = commune_poly.bounds
        bbox = f"{minx},{miny},{maxx},{maxy},EPSG:4326"
        
        def filter_in_commune(features):
            filtered = []
            for f in features:
                if "geometry" not in f:
                    continue
                try:
                    geom = shape(f["geometry"])
                    if not geom.is_valid:
                        geom = geom.buffer(0)
                    if geom.intersects(commune_poly):
                        filtered.append(f)
                except Exception:
                    continue
            return filtered
        
        # Récupération des données
        rpg_data = get_rpg_info_by_polygon(contour) if filters.get("filter_rpg", True) else []
        postes_bt_data = filter_in_commune(fetch_wfs_data(POSTE_LAYER, bbox))
        postes_hta_data = filter_in_commune(fetch_wfs_data(HT_POSTE_LAYER, bbox))
        parkings_data = get_parkings_info_by_polygon(contour) if filters.get("filter_parkings", False) else []
        friches_data = get_friches_info_by_polygon(contour) if filters.get("filter_friches", False) else []
        
        # Éleveurs sur la commune
        eleveurs_data = []
        try:
            eleveurs_raw = filter_in_commune(fetch_wfs_data(ELEVEURS_LAYER, bbox))
            for e in eleveurs_raw:
                props = e.get("properties", {})
                geom = e.get("geometry")
                
                # Construction des informations formatées
                nom = props.get("nomUniteLe") or props.get("denominati") or ""
                prenom = props.get("prenom1Uni") or props.get("prenomUsue") or ""
                denomination = props.get("denominati") or ""
                activite = props.get("activite_1") or ""
                
                # Adresse complète
                adresse = (
                    f"{props.get('numeroVoie','') or ''} "
                    f"{props.get('typeVoieEt','') or ''} "
                    f"{props.get('libelleVoi','') or ''}, "
                    f"{props.get('codePostal','') or ''} "
                    f"{props.get('libelleCom','') or ''}"
                ).replace(" ,", "").strip()
                
                # Liens d'annuaire
                ville_url = (props.get("libelleCom", "") or "").replace(" ", "+")
                nom_url = (nom + " " + prenom + " " + denomination).strip().replace(" ", "+")
                siret = props.get("siret", "")
                
                eleveur_props = {
                    # Nouveaux noms (normalisés)
                    "nom": nom,
                    "prenom": prenom,
                    "denomination": denomination,
                    "activite": activite,
                    "adresse": adresse,
                    "siret": siret,
                    "lien_annuaire": f"https://www.pagesjaunes.fr/annuaire/chercherlespros?quoiqui={nom_url}&ou={ville_url}&univers=pagesjaunes&idOu=" if nom or prenom or denomination else "",
                    "lien_entreprise": f"https://www.societe.com/societe/{denomination.lower().replace(' ', '-')}-{siret[:9]}.html#__establishments" if siret and denomination and len(siret) >= 9 else "",
                    "lien_pages_blanches": f"https://www.pagesjaunes.fr/pagesblanches/recherche?quoiqui={nom}+{prenom}&ou={props.get('libelleCom','')}" if nom or prenom else "",
                    
                    # Anciens noms (compatibilité JavaScript)
                    "nomUniteLe": nom,
                    "prenom1Uni": prenom,
                    "denominati": denomination,
                    "activite_1": activite
                }
                
                # Debug: afficher le lien généré
                if siret and denomination:
                    print(f"🔗 [DEBUG_LIEN] Dénomination: {denomination}")
                    print(f"🔗 [DEBUG_LIEN] SIRET: {siret} -> SIREN: {siret[:9]}")
                    print(f"🔗 [DEBUG_LIEN] Lien généré: {eleveur_props['lien_entreprise']}")
                
                eleveurs_data.append({
                    "type": "Feature",
                    "geometry": geom,
                    "properties": eleveur_props
                })
        except Exception as e:
            print(f"⚠️ [RAPPORT_INTÉGRÉ] Erreur collecte éleveurs: {e}")
            eleveurs_data = []
        
        sirene_data = get_sirene_info_by_polygon(contour)
        
        # =========================================================================
        # 🏛️ FONCTION UTILITAIRE ENRICHISSEMENT CADASTRAL
        # (Définie ici pour être disponible pour toitures, parkings, friches, RPG)
        # =========================================================================
        print(f"🏛️ [CADASTRE] Préparation de la fonction d'enrichissement cadastral...")
        
        def get_parcelles_for_feature(geom):
            """
            Récupère les parcelles cadastrales pour une géométrie donnée
            (même logique que pour les zones urbaines qui fonctionne bien)
            """
            parcelles = []
            try:
                cadastre_data = get_api_cadastre_data(geom)
                if cadastre_data and cadastre_data.get("features"):
                    for parcelle_feat in cadastre_data["features"]:
                        parcelle_props = parcelle_feat.get("properties", {})
                        ref_cadastrale = f"{parcelle_props.get('section', '')}{parcelle_props.get('numero', '')}"
                        if ref_cadastrale.strip():
                            parcelles.append({
                                "section": parcelle_props.get("section", ""),
                                "numero": parcelle_props.get("numero", ""),
                                "ref": ref_cadastrale,
                                "commune": parcelle_props.get("commune", ""),
                                "prefixe": parcelle_props.get("prefixe", "")
                            })
            except Exception as e:
                pass  # Silent - pas besoin d'afficher chaque erreur
            return parcelles
        
        print(f"🏛️ [CADASTRE] Fonction d'enrichissement cadastral prête")
        
        # Toitures: utiliser OSM bâtiments + filtres surface/distance au lieu du WFS "POTENTIEL_SOLAIRE"
        toitures_data = []
        if filters.get("filter_toitures", False):
            try:
                # Paramètres de filtre
                min_surface = float(filters.get("toitures_min_surface", 100.0))
                filter_by_distance = bool(filters.get("filter_by_distance", False))
                max_distance_bt = float(filters.get("max_distance_bt", 500.0))
                max_distance_hta = float(filters.get("max_distance_hta", 2000.0))
                poste_type_filter = str(filters.get("poste_type_filter", "ALL")).upper()

                # Bâtiments via OSM (Overpass) sur le polygone communal
                batiments_fc = get_batiments_data(contour) or {"type": "FeatureCollection", "features": []}
                batiments = batiments_fc.get("features", [])
                print(f"    🏠 Bâtiments OSM bruts: {len(batiments)}")

                for b in batiments:
                    try:
                        geom = shape(b.get("geometry"))
                        if not geom.is_valid:
                            geom = geom.buffer(0)
                            if not geom.is_valid:
                                continue
                        # Double garde: doit intersecter la commune
                        if not (commune_poly.contains(geom) or commune_poly.intersects(geom)):
                            continue

                        # Surface en m²
                        surface_m2 = shp_transform(to_l93, geom).area
                        if surface_m2 < min_surface:
                            continue

                        # Distances aux postes
                        centroid = geom.centroid.coords[0]
                        d_bt = calculate_min_distance(centroid, postes_bt_data) if postes_bt_data else None
                        d_hta = calculate_min_distance(centroid, postes_hta_data) if postes_hta_data else None

                        # Filtrage distance suivant le type de poste sélectionné
                        if filter_by_distance:
                            bt_ok = (d_bt is not None and d_bt <= max_distance_bt)
                            hta_ok = (d_hta is not None and d_hta <= max_distance_hta)
                            if poste_type_filter == "BT":
                                distance_ok = bt_ok
                            elif poste_type_filter == "HTA":
                                distance_ok = hta_ok
                            else:
                                distance_ok = bt_ok or hta_ok
                            if not distance_ok:
                                continue
                        # Sinon, pas de filtre distance

                        props_src = (b.get("properties") or {}).copy()
                        props = {
                            "surface_toiture_m2": round(surface_m2, 2),
                            "min_distance_bt_m": round(d_bt, 2) if d_bt is not None else None,
                            "min_distance_hta_m": round(d_hta, 2) if d_hta is not None else None,
                            "source": props_src.get("source", "OpenStreetMap"),
                            "building": props_src.get("building", "yes"),
                            "osm_id": props_src.get("osm_id"),
                        }

                        toitures_data.append({
                            "type": "Feature",
                            "geometry": b.get("geometry"),
                            "properties": props
                        })
                    except Exception as _e:
                        continue
                print(f"    ✅ Toitures retenues après filtres: {len(toitures_data)}")
                
                # Enrichissement cadastral des toitures (méthode simplifiée - comme zones urbaines)
                if toitures_data:
                    print(f"🏛️ [CADASTRE-TOITURES] Enrichissement : {len(toitures_data)} toitures")
                    
                    for i, toiture in enumerate(toitures_data):
                        try:
                            geom_toiture = toiture.get("geometry")
                            if not geom_toiture:
                                continue
                            
                            # Récupération directe des parcelles via API (même méthode que zones urbaines)
                            parcelles_cadastrales = get_parcelles_for_feature(geom_toiture)
                            
                            # Ajouter les parcelles aux propriétés de la toiture
                            if parcelles_cadastrales:
                                toiture['properties']['parcelles_cadastrales'] = parcelles_cadastrales
                                toiture['properties']['nb_parcelles_cadastrales'] = len(parcelles_cadastrales)
                            
                            # Debug occasionnel
                            if (i + 1) <= 3 or parcelles_cadastrales:
                                print(f"      🏛️ Toiture {i+1}: {len(parcelles_cadastrales)} parcelles trouvées")
                                
                        except Exception as e:
                            print(f"      ⚠️ Toiture {i+1}: {e}")
                            continue
                    
                    print(f"✅ [CADASTRE-TOITURES] Enrichissement terminé")
                
            except Exception as e:
                print(f"⚠️ [RAPPORT_INTÉGRÉ] Erreur génération toitures: {e}")
                toitures_data = []

        # Initialisation vide pour compatibilité avec les anciennes fonctions helper
        # (qui ne sont plus utilisées mais existent encore dans le code)
        cadastre_features = []

        # Appliquer filtres de surface et de distance sur parkings/friches si demandé
        filter_by_distance = bool(filters.get("filter_by_distance", False))
        max_distance_bt = float(filters.get("max_distance_bt", 500.0))
        max_distance_hta = float(filters.get("max_distance_hta", 2000.0))
        poste_type_filter = str(filters.get("poste_type_filter", "ALL")).upper()

        def _distance_ok(d_bt, d_hta):
            if not filter_by_distance:
                return True
            bt_ok = (d_bt is not None and d_bt <= max_distance_bt)
            hta_ok = (d_hta is not None and d_hta <= max_distance_hta)
            if poste_type_filter == "BT":
                return bt_ok
            if poste_type_filter == "HTA":
                return hta_ok
            return bt_ok or hta_ok

        # Parkings: surface minimale et distance
        if parkings_data:
            parking_min_area = float(filters.get("parking_min_area", 1500.0))
            filtered_pk = []
            for feat in parkings_data:
                try:
                    geom = feat.get("geometry")
                    if not geom:
                        continue
                    shp = shape(geom)
                    if not shp.is_valid:
                        shp = shp.buffer(0)
                        if not shp.is_valid:
                            continue
                    area_m2 = shp_transform(to_l93, shp).area
                    if area_m2 < parking_min_area:
                        continue
                    c = shp.centroid
                    lat_c, lon_c = c.y, c.x
                    d_bt = calculate_min_distance((lon_c, lat_c), postes_bt_data) if postes_bt_data else None
                    d_hta = calculate_min_distance((lon_c, lat_c), postes_hta_data) if postes_hta_data else None
                    if not _distance_ok(d_bt, d_hta):
                        continue
                    # Annoter pour réutiliser ensuite
                    props = (feat.get('properties') or {}).copy()
                    props.update({
                        'surface_m2': round(area_m2, 2),
                        'min_distance_bt_m': round(d_bt, 2) if d_bt is not None else None,
                        'min_distance_hta_m': round(d_hta, 2) if d_hta is not None else None,
                    })
                    feat = {**feat, 'properties': props}
                    filtered_pk.append(feat)
                except Exception:
                    continue
            parkings_data = filtered_pk
            
            # Enrichissement cadastral des parkings (méthode simplifiée - comme zones urbaines)
            if parkings_data:
                print(f"🏛️ [CADASTRE-PARKINGS] Enrichissement : {len(parkings_data)} parkings")
                
                for i, parking in enumerate(parkings_data):
                    try:
                        geom_parking = parking.get("geometry")
                        if not geom_parking:
                            continue
                        
                        # Récupération directe des parcelles via API (même méthode que zones urbaines)
                        parcelles_cadastrales = get_parcelles_for_feature(geom_parking)
                        
                        # Ajouter les parcelles aux propriétés
                        if parcelles_cadastrales:
                            parking['properties']['parcelles_cadastrales'] = parcelles_cadastrales
                            parking['properties']['nb_parcelles_cadastrales'] = len(parcelles_cadastrales)
                        
                        # Debug occasionnel
                        if (i + 1) <= 3 or parcelles_cadastrales:
                            print(f"      🏛️ Parking {i+1}: {len(parcelles_cadastrales)} parcelles trouvées")
                            
                    except Exception as e:
                        print(f"      ⚠️ Parking {i+1}: {e}")
                        continue
                
                print(f"✅ [CADASTRE-PARKINGS] Enrichissement terminé")

        # Friches: surface minimale et distance
        if friches_data:
            friches_min_area = float(filters.get("friches_min_area", 1000.0))
            filtered_fr = []
            for feat in friches_data:
                try:
                    geom = feat.get("geometry")
                    if not geom:
                        continue
                    shp = shape(geom)
                    if not shp.is_valid:
                        shp = shp.buffer(0)
                        if not shp.is_valid:
                            continue
                    area_m2 = shp_transform(to_l93, shp).area
                    # NB: friches_min_area est exprimé côté UI en m² (par cohérence avec parkings/toitures)
                    if area_m2 < friches_min_area:
                        continue
                    c = shp.centroid
                    lat_c, lon_c = c.y, c.x
                    d_bt = calculate_min_distance((lon_c, lat_c), postes_bt_data) if postes_bt_data else None
                    d_hta = calculate_min_distance((lon_c, lat_c), postes_hta_data) if postes_hta_data else None
                    if not _distance_ok(d_bt, d_hta):
                        continue
                    props = (feat.get('properties') or {}).copy()
                    props.update({
                        'surface_m2': round(area_m2, 2),
                        'min_distance_bt_m': round(d_bt, 2) if d_bt is not None else None,
                        'min_distance_hta_m': round(d_hta, 2) if d_hta is not None else None,
                    })
                    feat = {**feat, 'properties': props}
                    filtered_fr.append(feat)
                except Exception:
                    continue
            friches_data = filtered_fr
            
            # Enrichissement cadastral des friches (méthode simplifiée - comme zones urbaines)
            if friches_data:
                print(f"🏛️ [CADASTRE-FRICHES] Enrichissement : {len(friches_data)} friches")
                
                for i, friche in enumerate(friches_data):
                    try:
                        geom_friche = friche.get("geometry")
                        if not geom_friche:
                            continue
                        
                        # Récupération directe des parcelles via API (même méthode que zones urbaines)
                        parcelles_cadastrales = get_parcelles_for_feature(geom_friche)
                        
                        # Ajouter les parcelles aux propriétés
                        if parcelles_cadastrales:
                            friche['properties']['parcelles_cadastrales'] = parcelles_cadastrales
                            friche['properties']['nb_parcelles_cadastrales'] = len(parcelles_cadastrales)
                        
                        # Debug occasionnel
                        if (i + 1) <= 3 or parcelles_cadastrales:
                            print(f"      🏛️ Friche {i+1}: {len(parcelles_cadastrales)} parcelles trouvées")
                            
                    except Exception as e:
                        print(f"      ⚠️ Friche {i+1}: {e}")
                        continue
                
                print(f"✅ [CADASTRE-FRICHES] Enrichissement terminé")

        sirene_data = get_sirene_info_by_polygon(contour)

        # Calcul rapide d'une valeur d'irradiation (kWh/kWc/an) via PVGIS au centre de la commune
        pvgis_kwh_per_kwc = None
        try:
            pvgis_kwh_per_kwc = get_pvgis_production(lat, lon, 30, 180, peakpower=1.0)
        except Exception:
            pvgis_kwh_per_kwc = None
        
        # APIs enrichies pour le rapport (données cadastrales, nature, urbanisme)
        api_cadastre = get_api_cadastre_data(contour_optimise)
        api_nature = get_all_api_nature_data(contour_optimise)
        api_urbanisme = get_all_gpu_data(contour_optimise)

        # Collecte et analyse des zones d'urbanisme (PLU/GPU)
        # Utiliser la logique d'optimisation des zones directement
        plu_info = []
        
        zones_data = []
        if filters.get("filter_zones", False):
            try:
                # Récupérer les zones optimisées avec la même logique que build_map
                zones_min_area = float(filters.get("zones_min_area", 1000.0))
                zones_type_filter = filters.get("zones_type_filter", "")
                
                # API GPU pour zones autour de la commune  
                def get_zones_around_commune_simple(lat, lon, radius_km=2.0):
                    api_url = "https://apicarto.ign.fr/api/gpu/zone-urba"
                    delta = radius_km / 111.0
                    bbox_geojson = {
                        "type": "Polygon",
                        "coordinates": [[
                            [lon - delta, lat - delta],
                            [lon + delta, lat - delta], 
                            [lon + delta, lat + delta],
                            [lon - delta, lat + delta],
                            [lon - delta, lat - delta]
                        ]]
                    }
                    params = {"geom": json.dumps(bbox_geojson), "_limit": 1000}
                    
                    try:
                        resp = requests.get(api_url, params=params, timeout=30)
                        if resp.status_code == 200:
                            return resp.json().get('features', [])
                        return []
                    except Exception:
                        return []
                
                # Récupérer toutes les zones autour de la commune
                all_zones = get_zones_around_commune_simple(lat, lon, 2.0)
                print(f"    📍 {len(all_zones)} zones trouvées autour de la commune")
                
                # Filtrer les zones par type 'U' si spécifié
                target_zones = []
                for zone in all_zones:
                    props = zone.get('properties', {})
                    typologie = props.get('typezone', '').upper()
                    
                    if not zones_type_filter or zones_type_filter.upper() in typologie:
                        target_zones.append(zone)
                
                if zones_type_filter:
                    print(f"    🎯 {len(target_zones)} zones de type '{zones_type_filter}' sélectionnées")
                
                # Traiter chaque zone pour enrichir avec les données
                for i, zone_feat in enumerate(target_zones):
                    try:
                        geom = zone_feat.get("geometry")
                        if not geom:
                            continue
                        props = zone_feat.get("properties", {})
                        
                        # Calcul de la surface de la zone
                        shp_zone = shape(geom)
                        if not shp_zone.is_valid:
                            shp_zone = shp_zone.buffer(0)
                            if not shp_zone.is_valid:
                                continue
                        
                        # Intersection avec la commune
                        if not (commune_poly.contains(shp_zone) or commune_poly.intersects(shp_zone)):
                            continue
                        
                        # Surface en m²
                        surface_m2 = shp_transform(to_l93, shp_zone).area
                        if surface_m2 < zones_min_area:
                            continue
                        
                        # Distances aux postes
                        centroid = shp_zone.centroid
                        lat_c, lon_c = centroid.y, centroid.x
                        d_bt = calculate_min_distance((lon_c, lat_c), postes_bt_data) if postes_bt_data else None
                        d_hta = calculate_min_distance((lon_c, lat_c), postes_hta_data) if postes_hta_data else None
                        
                        # Récupération des parcelles cadastrales pour cette zone
                        parcelles_cadastrales = []
                        try:
                            cadastre_data = get_api_cadastre_data(geom)
                            if cadastre_data and cadastre_data.get("features"):
                                for parcelle_feat in cadastre_data["features"]:
                                    parcelle_props = parcelle_feat.get("properties", {})
                                    ref_cadastrale = f"{parcelle_props.get('section', '')}{parcelle_props.get('numero', '')}"
                                    if ref_cadastrale.strip():
                                        parcelles_cadastrales.append({
                                            "id": parcelle_props.get("id", ""),
                                            "section": parcelle_props.get("section", ""),
                                            "numero": parcelle_props.get("numero", ""),
                                            "ref": ref_cadastrale,
                                            "commune": parcelle_props.get("commune", ""),
                                            "prefixe": parcelle_props.get("prefixe", "")
                                        })
                            print(f"      🏛️ {len(parcelles_cadastrales)} parcelles cadastrales trouvées pour la zone")
                        except Exception as e:
                            print(f"      ⚠️ Erreur récupération parcelles cadastrales: {e}")
                        
                        # Debug: vérifier le contenu des parcelles pour cette zone
                        if parcelles_cadastrales:
                            print(f"      🔍 [DEBUG ZONE] Première parcelle: {parcelles_cadastrales[0]}")
                        
                        # Enrichissement des propriétés
                        props_enrichies = props.copy()
                        props_enrichies.update({
                            "surface_m2": round(surface_m2, 2),
                            "surface_ha": round(surface_m2 / 10000.0, 4),
                            "coords": [lat_c, lon_c],
                            "distance_bt": round(d_bt, 2) if d_bt is not None else None,
                            "distance_hta": round(d_hta, 2) if d_hta is not None else None,
                            "nom_commune": commune_name,
                            "parcelles_cadastrales": parcelles_cadastrales,
                            "nb_parcelles_cadastrales": len(parcelles_cadastrales)
                        })
                        
                        # Debug: vérifier les propriétés enrichies
                        print(f"      🔍 [DEBUG ZONE] Propriétés enrichies - parcelles: {len(props_enrichies.get('parcelles_cadastrales', []))} parcelles")
                        
                        zones_data.append({
                            "type": "Feature",
                            "geometry": geom,
                            "properties": props_enrichies
                        })
                        
                    except Exception:
                        continue
                
                print(f"    ✅ {len(zones_data)} zones filtrées et enrichies")
                
            except Exception as e:
                print(f"    ⚠️ Erreur lors du traitement des zones: {e}")
                zones_data = []
        else:
            print(f"    🏗️ Zones d'urbanisme: filtrage désactivé")
            zones_data = []

        # Préparation des listes de détails par rubrique (position, surface, parcelles, postes proches, liens)
        def _format_parcelles_refs(props: dict) -> dict:
            try:
                numero = props.get('numero') or props.get('numero_parcelle') or props.get('num_parc') or ''
                section = props.get('section') or props.get('code_section') or ''
                commune_code = props.get('commune') or props.get('code_commune') or props.get('insee') or ''
                prefixe = props.get('prefixe') or props.get('code_arr') or ''
                return {
                    'numero': numero,
                    'section': section,
                    'commune': commune_code,
                    'prefixe': prefixe,
                    'reference_complete': f"{commune_code}{prefixe}{section}{numero}".strip()
                }
            except Exception:
                return {}

        def _find_nearest_poste(pt_lon: float, pt_lat: float, postes: list) -> dict:
            try:
                p = Point(pt_lon, pt_lat)
                best = None
                best_d = None
                for poste in (postes or []):
                    try:
                        g = poste.get('geometry')
                        if not g:
                            continue
                        d = shape(g).distance(p) * 111000
                        if best_d is None or (d < best_d):
                            best = poste
                            best_d = d
                    except Exception:
                        continue
                if best is None:
                    return {}
                coords = best.get('geometry', {}).get('coordinates', [None, None])
                pr = best.get('properties', {})
                return {
                    'distance_m': round(best_d, 2) if best_d is not None else None,
                    'lon': coords[0],
                    'lat': coords[1],
                    'id': pr.get('id') or pr.get('identifiant') or pr.get('code') or pr.get('nom') or '',
                    'nom': pr.get('nom') or pr.get('libelle') or '',
                    'tension': pr.get('tension') or pr.get('Tension') or '',
                    'fonction': pr.get('fonction') or pr.get('Fonction') or '',
                    'puissance': pr.get('puissance') or pr.get('Puissance') or pr.get('Capacité') or pr.get('capacite') or '',
                    'etat': pr.get('etat') or pr.get('Etat') or pr.get('statut') or '',
                    'type': pr.get('type') or pr.get('Type') or ''
                }
            except Exception:
                return {}

        # Note: cadastre_features déjà récupéré plus haut pour l'enrichissement

        def _parcelles_for_point(lon: float, lat: float, max_match: int = 3) -> list:
            out = []
            try:
                p = Point(lon, lat)
                for parc in cadastre_features:
                    try:
                        g = parc.get('geometry')
                        if not g:
                            continue
                        # intersects is more tolerant than contains for points on borders
                        if shape(g).intersects(p):
                            out.append(_format_parcelles_refs(parc.get('properties', {})))
                            if len(out) >= max_match:
                                break
                    except Exception:
                        continue
            except Exception:
                pass
            return out

        def _parcelles_for_geom(feature_geom: dict, max_match: int = 3) -> list:
            """Retourne les références de parcelles cadastrales qui intersectent la géométrie complète.
            Utilisé de préférence au centroïde pour éviter les faux négatifs en bordure.
            """
            out = []
            try:
                if not feature_geom:
                    return out
                shp_feat = shape(feature_geom)
                for parc in cadastre_features:
                    try:
                        g = parc.get('geometry')
                        if not g:
                            continue
                        if shape(g).intersects(shp_feat):
                            out.append(_format_parcelles_refs(parc.get('properties', {})))
                            if len(out) >= max_match:
                                break
                    except Exception:
                        continue
            except Exception:
                pass
            return out

        def _parcelles_from_api_near(lon: float, lat: float, tol: float = 0.0006, max_match: int = 3) -> list:
            """Fallback: interroge l'API Cadastre autour d'un point (petit carré ~60m) pour récupérer des parcelles."""
            try:
                ring = [
                    [lon - tol, lat - tol],
                    [lon + tol, lat - tol],
                    [lon + tol, lat + tol],
                    [lon - tol, lat + tol],
                    [lon - tol, lat - tol],
                ]
                geom_query = {"type": "Polygon", "coordinates": [ring]}
                resp = get_api_cadastre_data(geom_query, endpoint="/cadastre/parcelle", source_ign="PCI")
                feats = (resp or {}).get('features', [])
                out = []
                for parc in feats:
                    try:
                        out.append(_format_parcelles_refs((parc.get('properties') or {})))
                        if len(out) >= max_match:
                            break
                    except Exception:
                        continue
                return out
            except Exception:
                return []

        # Reverse géocodage rapide et lien PagesJaunes à partir de l'adresse exacte
        _rev_cache = {}
        def _reverse_address_quick(lon_f: float, lat_f: float) -> str:
            try:
                if lon_f is None or lat_f is None:
                    return ""
                key = (round(lon_f, 5), round(lat_f, 5))
                if key in _rev_cache:
                    return _rev_cache[key]
                url = f"https://api-adresse.data.gouv.fr/reverse/?lon={lon_f}&lat={lat_f}"
                r = requests.get(url, timeout=0.9)
                if r.ok:
                    js = r.json() or {}
                    feats = js.get("features") or []
                    if feats:
                        label = (feats[0].get("properties") or {}).get("label") or ""
                        _rev_cache[key] = label
                        return label
            except Exception:
                pass
            return ""

        def _build_annuaire_link(address: str) -> str:
            addr = (address or "").strip()
            if not addr:
                return f"https://www.pagesjaunes.fr/annuaire/chercherlespros?quoiqui=&ou={quote_plus(commune_name)}&univers=pagesjaunes&idOu="
            return f"https://www.pagesjaunes.fr/annuaire/chercherlespros?quoiqui=&ou={quote_plus(addr)}&univers=pagesjaunes&idOu="

        # Limiter le volume des détails pour préserver les perfs sur très grandes communes
        max_details = int((filters or {}).get('max_details', 200))

        # Détails Parkings
        parkings_details = []
        for feat in (parkings_data or [])[:max_details]:
            try:
                geom = feat.get('geometry')
                if not geom:
                    continue
                shp = shape(geom)
                c = shp.centroid
                lat_c, lon_c = c.y, c.x
                area_m2 = shp_transform(to_l93, shp).area
                d_bt = calculate_min_distance((lon_c, lat_c), postes_bt_data) if postes_bt_data else None
                d_hta = calculate_min_distance((lon_c, lat_c), postes_hta_data) if postes_hta_data else None
                addr_txt = _reverse_address_quick(lon_c, lat_c)
                details = {
                    'lat': lat_c,
                    'lon': lon_c,
                    'surface_m2': round(area_m2, 2),
                    'min_distance_bt_m': round(d_bt, 2) if d_bt is not None else None,
                    'min_distance_hta_m': round(d_hta, 2) if d_hta is not None else None,
                    'poste_bt_proche': _find_nearest_poste(lon_c, lat_c, postes_bt_data),
                    'poste_hta_proche': _find_nearest_poste(lon_c, lat_c, postes_hta_data),
                    'parcelles': feat.get('properties', {}).get('parcelles_cadastrales', []),
                    'adresse': addr_txt,
                    'lien_streetview': f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat_c},{lon_c}"
                }
                details['lien_annuaire'] = _build_annuaire_link(addr_txt)
                parkings_details.append(details)
            except Exception:
                continue

        # Détails Friches
        friches_details = []
        for feat in (friches_data or [])[:max_details]:
            try:
                geom = feat.get('geometry')
                if not geom:
                    continue
                shp = shape(geom)
                c = shp.centroid
                lat_c, lon_c = c.y, c.x
                area_m2 = shp_transform(to_l93, shp).area
                d_bt = calculate_min_distance((lon_c, lat_c), postes_bt_data) if postes_bt_data else None
                d_hta = calculate_min_distance((lon_c, lat_c), postes_hta_data) if postes_hta_data else None
                addr_txt = _reverse_address_quick(lon_c, lat_c)
                details = {
                    'lat': lat_c,
                    'lon': lon_c,
                    'surface_m2': round(area_m2, 2),
                    'surface_ha': round(area_m2 / 10000.0, 4),
                    'min_distance_bt_m': round(d_bt, 2) if d_bt is not None else None,
                    'min_distance_hta_m': round(d_hta, 2) if d_hta is not None else None,
                    'poste_bt_proche': _find_nearest_poste(lon_c, lat_c, postes_bt_data),
                    'poste_hta_proche': _find_nearest_poste(lon_c, lat_c, postes_hta_data),
                    'parcelles': feat.get('properties', {}).get('parcelles_cadastrales', []),
                    'adresse': addr_txt,
                    'lien_streetview': f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat_c},{lon_c}"
                }
                details['lien_annuaire'] = _build_annuaire_link(addr_txt)
                friches_details.append(details)
            except Exception:
                continue

        # Détails Toitures
        toitures_details = []
        for feat in (toitures_data or [])[:max_details]:
            try:
                geom = feat.get('geometry')
                if not geom:
                    continue
                shp = shape(geom)
                c = shp.centroid
                lat_c, lon_c = c.y, c.x
                area_m2 = shp_transform(to_l93, shp).area
                props = feat.get('properties', {})
                d_bt = props.get('min_distance_bt_m')
                d_hta = props.get('min_distance_hta_m')
                if d_bt is None:
                    d_bt = calculate_min_distance((lon_c, lat_c), postes_bt_data) if postes_bt_data else None
                if d_hta is None:
                    d_hta = calculate_min_distance((lon_c, lat_c), postes_hta_data) if postes_hta_data else None
                addr_txt = _reverse_address_quick(lon_c, lat_c)
                pv = {
                    'lat': lat_c,
                    'lon': lon_c,
                    'surface_m2': round(area_m2, 2),
                    'min_distance_bt_m': round(d_bt, 2) if d_bt is not None else None,
                    'min_distance_hta_m': round(d_hta, 2) if d_hta is not None else None,
                    'poste_bt_proche': _find_nearest_poste(lon_c, lat_c, postes_bt_data),
                    'poste_hta_proche': _find_nearest_poste(lon_c, lat_c, postes_hta_data),
                    'parcelles': props.get('parcelles_cadastrales', []),
                    'lien_streetview': props.get('lien_streetview') or f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat_c},{lon_c}",
                    'lien_annuaire': _build_annuaire_link(addr_txt),
                    'osm_id': props.get('osm_id'),
                    'building': props.get('building', 'yes')
                }
                if addr_txt:
                    pv['adresse'] = addr_txt
                toitures_details.append(pv)
            except Exception:
                continue

        print(f"📊 [RAPPORT_INTÉGRÉ] Données collectées:")
        print(f"    🌾 RPG: {len(rpg_data)} parcelles")
        print(f"    🐄 Éleveurs: {len(eleveurs_data)} exploitants")
        print(f"    �️ Zones: {len(zones_data)} zones d'urbanisme")
        print(f"    �🅿️ Parkings: {len(parkings_data)} emplacements")
        print(f"    🏚️ Friches: {len(friches_data)} sites")
        print(f"    🏠 Toitures: {len(toitures_data)} bâtiments")
        print(f"    ⚡ Postes BT: {len(postes_bt_data)}, HTA: {len(postes_hta_data)}")
        print(f"    🏢 SIRENE: {len(sirene_data)} établissements")

        # 4. Analyses statistiques
        
        # Analyse RPG avec détails des parcelles
        rpg_analysis = {"resume_executif": {"total_parcelles": 0, "surface_totale_ha": 0}}
        rpg_parcelles_detaillees = []
        
        if rpg_data:
            total_surface_rpg = 0
            cultures = {}
            
            for parcelle in rpg_data:
                try:
                    geom = shape(parcelle["geometry"])
                    surface_ha = shp_transform(to_l93, geom).area / 10000.0
                    total_surface_rpg += surface_ha
                    
                    props = parcelle.get("properties", {})
                    culture = props.get("CODE_CULTU", "Inconnue")
                    cultures[culture] = cultures.get(culture, 0) + surface_ha
                    
                    # Enrichir les propriétés de la parcelle avec distances et références
                    centroid = geom.centroid
                    lat_c, lon_c = centroid.y, centroid.x
                    
                    # Distances aux postes
                    d_bt = calculate_min_distance((lon_c, lat_c), postes_bt_data) if postes_bt_data else None
                    d_hta = calculate_min_distance((lon_c, lat_c), postes_hta_data) if postes_hta_data else None
                    
                    # Références cadastrales (méthode simplifiée - comme zones urbaines)
                    parcelles_refs = get_parcelles_for_feature(parcelle["geometry"])
                    
                    # Décodage de la culture
                    code_culture = props.get("CODE_CULTU", "")
                    culture_decoded = rpg_culture_mapping.get(code_culture, code_culture or "Non définie")
                    
                    # Enrichissement des propriétés
                    props_enrichies = props.copy()
                    props_enrichies.update({
                        "Culture": culture_decoded,
                        "surface": round(surface_ha, 3),
                        "coords": [lat_c, lon_c],
                        "distance_bt": round(d_bt, 2) if d_bt is not None else None,
                        "distance_hta": round(d_hta, 2) if d_hta is not None else None,
                        "code_culture": code_culture,
                        "section": parcelles_refs[0].get("section", "") if parcelles_refs else "",
                        "numero": parcelles_refs[0].get("numero", "") if parcelles_refs else "",
                        "nom_com": commune_name
                    })
                    
                    rpg_parcelles_detaillees.append({
                        "type": "Feature",
                        "geometry": parcelle["geometry"],
                        "properties": props_enrichies
                    })
                    
                except Exception:
                    continue
            
            rpg_analysis = {
                "resume_executif": {
                    "total_parcelles": len(rpg_data),
                    "surface_totale_ha": round(total_surface_rpg, 2),
                    "surface_moyenne_parcelle_ha": round(total_surface_rpg / len(rpg_data), 2) if rpg_data else 0,
                    "cultures_principales": sorted(cultures.items(), key=lambda x: x[1], reverse=True)[:5]
                }
            }
        
        # Analyse parkings
        # Valeurs par défaut robustes pour éviter les clés manquantes côté template
        parkings_analysis = {
            "resume_executif": {
                "total_parkings": 0,
                "surface_totale_m2": 0,
                "surface_moyenne_m2": 0,
                "potentiel_photovoltaique_mwc": 0,
                "production_annuelle_mwh": 0,
            }
        }
        if parkings_data:
            total_surface_parkings = 0
            
            for parking in parkings_data:
                try:
                    geom = shape(parking["geometry"])
                    surface_m2 = shp_transform(to_l93, geom).area
                    total_surface_parkings += surface_m2
                except Exception:
                    continue
            
            potentiel_mwc = round(total_surface_parkings * 0.15 / 1000, 2)  # Estimation 150W/m²
            production_mwh = round(potentiel_mwc * 1200)  # ~1200 MWh/an par MWc
            parkings_analysis = {
                "resume_executif": {
                    "total_parkings": len(parkings_data),
                    "surface_totale_m2": round(total_surface_parkings, 2),
                    "surface_moyenne_m2": round(total_surface_parkings / len(parkings_data), 2) if parkings_data else 0,
                    "potentiel_photovoltaique_mwc": potentiel_mwc,
                    "production_annuelle_mwh": production_mwh
                },
                "details": parkings_details
            }
        
        # Analyse friches
        friches_analysis = {
            "resume_executif": {
                "total_friches": 0,
                "surface_totale_ha": 0
            }
        }
        if friches_data:
            total_surface_friches = 0
            for friche in friches_data:
                try:
                    geom = shape(friche["geometry"])
                    surface_ha = shp_transform(to_l93, geom).area / 10000.0
                    total_surface_friches += surface_ha
                except Exception:
                    continue
            friches_analysis = {
                "resume_executif": {
                    "total_friches": len(friches_data),
                    "surface_totale_ha": round(total_surface_friches, 2),
                    "surface_moyenne_ha": round(total_surface_friches / len(friches_data), 2) if friches_data else 0,
                    "potentiel_reconversion_ha": round(total_surface_friches * 0.8, 2)
                },
                "details": friches_details
            }

        # Analyse toitures
        toitures_analysis = {
            "resume_executif": {
                "total_toitures": 0,
                "surface_totale_m2": 0,
                "surface_exploitable_pv_m2": 0,
                "potentiel_total_mwc": 0,
                "production_annuelle_mwh": 0
            }
        }
        if toitures_data:
            total_surface_toitures = 0
            for toiture in toitures_data:
                try:
                    geom = shape(toiture["geometry"])
                    surface_m2 = shp_transform(to_l93, geom).area
                    total_surface_toitures += surface_m2
                except Exception:
                    continue
            toitures_analysis = {
                "resume_executif": {
                    "total_toitures": len(toitures_data),
                    "surface_totale_m2": round(total_surface_toitures, 2),
                    "surface_exploitable_pv_m2": round(total_surface_toitures * 0.7, 2),
                    "potentiel_total_mwc": round(total_surface_toitures * 0.7 * 0.2 / 1000, 2),
                    "production_annuelle_mwh": round(total_surface_toitures * 0.7 * 0.2 * 1.2, 2)
                },
                "details": toitures_details
            }
        
        # Analyse zones d'urbanisme
        zones_analysis = {
            "resume_executif": {
                "total_zones": 0,
                "surface_totale_ha": 0,
                "types_zones": []
            }
        }
        if zones_data:
            total_surface_zones = 0
            types_zones = {}
            for zone in zones_data:
                try:
                    props = zone.get("properties", {})
                    surface_ha = props.get("surface_ha", 0)
                    total_surface_zones += surface_ha
                    
                    typologie = props.get("typezone", "Autre")
                    types_zones[typologie] = types_zones.get(typologie, 0) + surface_ha
                except Exception:
                    continue
            
            zones_analysis = {
                "resume_executif": {
                    "total_zones": len(zones_data),
                    "surface_totale_ha": round(total_surface_zones, 2),
                    "surface_moyenne_ha": round(total_surface_zones / len(zones_data), 2) if zones_data else 0,
                    "types_zones": sorted(types_zones.items(), key=lambda x: x[1], reverse=True)[:5]
                }
            }
        
        # 5. Assemblage du rapport final
        rapport = {
            "metadata": {
                "commune_nom": commune_name,
                "date_generation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version_rapport": "2.1_integre",
                "methodes_analyse": ["polygon_intersection", "api_integration", "statistical_analysis"],
                "sources_donnees": ["IGN", "OSM", "Cadastre", "RPG", "GeoRisques", "SIRENE"],
                "optimisation_geometrique": True,
                "pvgis_kwh_per_kwc": round(pvgis_kwh_per_kwc, 1) if isinstance(pvgis_kwh_per_kwc, (int, float)) else None
            },
            
            "commune_info": {
                "caracteristiques_generales": {
                    "nom": commune_info.get("nom", commune_name),
                    "code_insee": commune_info.get("code", ""),
                    "codes_postaux": commune_info.get("codesPostaux", []),
                    "departement": commune_info.get("departement", {})
                },
                "superficie_total_ha": round(superficie_ha, 2),
                "population": commune_info.get("population", 0),
                "densite_habitants_km2": round((commune_info.get("population", 0) / superficie_ha * 100), 2) if superficie_ha > 0 else 0,
                "centroid_lat": lat,
                "centroid_lon": lon
            },
            
            "rpg_analysis": rpg_analysis,
            "rpg_parcelles": {
                "type": "FeatureCollection",
                "features": rpg_parcelles_detaillees
            },
            "eleveurs": {
                "type": "FeatureCollection", 
                "features": eleveurs_data
            },
            "zones_analysis": zones_analysis,
        }
        
        # Debug: vérifier le contenu des zones_data avant ajout au rapport
        print(f"🔍 [DEBUG RAPPORT] {len(zones_data)} zones dans zones_data avant ajout au rapport")
        if zones_data:
            first_zone = zones_data[0]
            props = first_zone.get("properties", {})
            print(f"🔍 [DEBUG RAPPORT] Première zone - parcelles: {len(props.get('parcelles_cadastrales', []))} cadastrales")
            if props.get('parcelles_cadastrales'):
                print(f"🔍 [DEBUG RAPPORT] Première parcelle: {props['parcelles_cadastrales'][0]}")
        
        rapport["zones"] = {
            "type": "FeatureCollection",
            "features": zones_data
        }
        rapport["parkings_analysis"] = parkings_analysis
        rapport["friches_analysis"] = friches_analysis
        rapport["toitures_analysis"] = toitures_analysis
            
        rapport["infrastructures_analysis"] = {
            "energie": {
                "postes_electriques": {
                    "postes_bt": {"count": len(postes_bt_data)},
                    "postes_hta": {"count": len(postes_hta_data)}
                }
            }
        }
            
        rapport["environnement_analysis"] = {
            "zones_protegees": api_nature.get("summary", {}),
            "biodiversite": {
                "zones_natura2000": api_nature.get("details", {}).get("natura2000_directive_habitat", {}).get("count", 0) + 
                                   api_nature.get("details", {}).get("natura2000_directive_oiseaux", {}).get("count", 0),
                "znieff": api_nature.get("details", {}).get("znieff_type1", {}).get("count", 0) + 
                         api_nature.get("details", {}).get("znieff_type2", {}).get("count", 0)
            }
        }
            
        rapport["socioeconomique_analysis"] = {
            "economie": {
                "entreprises": {"total": len(sirene_data)}
            }
        }
            
        rapport["synthese_recommandations"] = {
            "points_forts": [],
            "recommandations_strategiques": {
                "court_terme": ["Analyser le potentiel photovoltaïque des toitures"],
                "moyen_terme": ["Développer la valorisation des friches"],
                "long_terme": ["Optimiser l'usage des terres agricoles"]
            },
            "potentiel_global": {
                "score_potentiel_energetique": min(100, (toitures_analysis["resume_executif"]["total_toitures"] * 2)),
                "score_potentiel_economique": min(100, (len(sirene_data) / 10)),
                "score_qualite_environnementale": min(100, (api_nature.get("summary", {}).get("total_zones", 0) * 10))
            }
        }
            
        rapport["api_data"] = {
            "cadastre": api_cadastre,
            "nature": api_nature,
            "urbanisme": api_urbanisme
        }

        # Génération d'une carte Folium dédiée au rapport (parkings, friches, toitures, postes)
        # MAIS si une carte de recherche vient d'être générée et est en cache, on l'utilise en priorité
        try:
            # Si une carte existe déjà en cache (issue de la recherche), on l'intègre directement
            if (last_map_params or {}).get("html"):
                # Utilise l'endpoint /generated_map qui renvoie le HTML en mémoire
                rapport["carte_url"] = "/generated_map"
                try:
                    rapport["carte_static_url"] = (
                        f"https://staticmap.openstreetmap.de/staticmap.php?center={lat},{lon}&zoom=13&size=800x500&maptype=mapnik"
                    )
                except Exception:
                    pass
                # On saute la (re)génération d'une autre carte
                raise StopIteration()

            m = folium.Map(location=[lat, lon], zoom_start=13, tiles=None, max_zoom=22)
            folium.TileLayer(
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri World Imagery",
                name="Satellite",
                overlay=False, control=True, show=True, max_zoom=22
            ).add_to(m)
            folium.TileLayer("OpenStreetMap", name="Fond OSM", overlay=False, control=True, show=False, max_zoom=19).add_to(m)

            # Lightweight reverse geocode using BAN for nicer popups (guarded + timeout)
            import requests as _rq
            def _reverse_address(lon_f: float, lat_f: float) -> str:
                try:
                    url = f"https://api-adresse.data.gouv.fr/reverse/?lon={lon_f}&lat={lat_f}"
                    r = _rq.get(url, timeout=0.8)
                    if r.ok:
                        js = r.json() or {}
                        feats = js.get("features") or []
                        if feats:
                            return (feats[0].get("properties") or {}).get("label") or ""
                except Exception:
                    pass
                return ""

            def _join_parcelles(refs: list) -> str:
                try:
                    vals = [d.get("reference_complete") for d in (refs or []) if d.get("reference_complete")]
                    return ", ".join(vals[:4])
                except Exception:
                    return ""
            def add_fc_as_layer(fc, name, color):
                group = folium.FeatureGroup(name=name, show=True)
                # Normalize FeatureCollection/list into a list of features
                try:
                    features_iter = ensure_feature_list(fc)
                except Exception:
                    features_iter = (fc or [])
                for f in features_iter:
                    geom = f.get("geometry") if isinstance(f, dict) else None
                    props = (f.get("properties") or {}) if isinstance(f, dict) else {}
                    if not geom:
                        continue
                    try:
                        # compute centroid for parcelles/address
                        try:
                            shp = shape(geom)
                            c = shp.centroid
                            lat_c, lon_c = c.y, c.x
                        except Exception:
                            lat_c = props.get("lat")
                            lon_c = props.get("lon")

                        # Try geometry-based parcel matching first; fallback to centroid-based
                        parc_refs = _parcelles_for_geom(geom) or (
                            _parcelles_for_point(lon_c, lat_c) if (lat_c is not None and lon_c is not None) else []
                        )
                        # Fallback API query around the feature if cache missed parcels
                        if not parc_refs and (lat_c is not None and lon_c is not None):
                            parc_refs = _parcelles_from_api_near(lon_c, lat_c)
                        parcelles_txt = _join_parcelles(parc_refs)
                        addr_txt = _reverse_address(lon_c, lat_c) if (lat_c is not None and lon_c is not None) else ""

                        # enrich props for popup/tooltip fields
                        enriched = props.copy()
                        if parcelles_txt and not enriched.get("parcelles"):
                            enriched["parcelles"] = parcelles_txt
                        if addr_txt and not enriched.get("adresse"):
                            enriched["adresse"] = addr_txt

                        gj = folium.GeoJson(
                            {"type": "Feature", "geometry": geom, "properties": enriched},
                            name=name,
                            style_function=lambda _:
                                {"color": color, "weight": 2, "fillColor": color, "fillOpacity": 0.2},
                            tooltip=folium.GeoJsonTooltip(
                                fields=[k for k in [
                                    "surface_m2", "surface_toiture_m2", "parcelles", "adresse",
                                    "min_distance_bt_m", "min_distance_hta_m"
                                ] if k in enriched],
                                aliases=[
                                    "Surface (m²)", "Surface toiture (m²)", "Parcelles", "Adresse",
                                    "Dist. BT (m)", "Dist. HTA (m)"
                                ],
                                sticky=True
                            ),
                            popup=folium.GeoJsonPopup(
                                fields=[k for k in [
                                    "surface_m2", "surface_toiture_m2", "parcelles", "adresse",
                                    "min_distance_bt_m", "min_distance_hta_m"
                                ] if k in enriched],
                                aliases=[
                                    "Surface (m²)", "Surface toiture (m²)", "Parcelles", "Adresse",
                                    "Dist. BT (m)", "Dist. HTA (m)"
                                ],
                                labels=True,
                                localize=True
                            )
                        )
                        gj.add_to(group)
                    except Exception:
                        continue
                m.add_child(group)

            # Ajouter couches
            # Parkings en violet (#800080)
            add_fc_as_layer(parkings_data, "Parkings", "#800080")
            add_fc_as_layer(friches_data, "Friches", "#8B4513")
            add_fc_as_layer(toitures_data, "Toitures (OSM)", "#FFD700")

            # Postes (points)
            def add_postes(postes, name, color):
                group = folium.FeatureGroup(name=name, show=True)
                for p in postes:
                    try:
                        coords = p.get("geometry", {}).get("coordinates", [])
                        if isinstance(coords, (list, tuple)) and len(coords) == 2:
                            folium.CircleMarker(
                                location=[coords[1], coords[0]], radius=4,
                                color=color, fill=True, fill_opacity=0.9
                            ).add_to(group)
                    except Exception:
                        continue
                m.add_child(group)

            add_postes(postes_bt_data, "Postes BT", "#006400")
            add_postes(postes_hta_data, "Postes HTA", "#FF8C00")

            folium.LayerControl().add_to(m)

            # Sauvegarder la carte
            def _slugify(txt: str) -> str:
                return re.sub(r"[^a-z0-9]+", "-", txt.lower()).strip("-")

            filename = f"carte_{_slugify(commune_name)}_{int(time.time())}.html"
            try:
                carte_rel = save_map_html(m, filename)  # e.g. "cartes/....html"
                rapport["carte_url"] = f"/static/{carte_rel}"
            except Exception as _:
                rapport.setdefault("carte_url", "/static/map.html")
            # Provide a simple static map URL for printing fallback
            try:
                rapport["carte_static_url"] = (
                    f"https://staticmap.openstreetmap.de/staticmap.php?center={lat},{lon}&zoom=13&size=800x500&maptype=mapnik"
                )
            except Exception:
                pass
        except StopIteration:
            # Carte de recherche utilisée, rien d'autre à faire
            pass
        except Exception as e:
            print(f"⚠️ [RAPPORT_INTÉGRÉ] Erreur génération carte: {e}")
            rapport.setdefault("carte_url", "/static/map.html")
        
        # Durée
        try:
            rapport.setdefault("metadata", {})["duree_generation_sec"] = round(time.time() - start_ts, 2)
        except Exception:
            pass

        print(f"✅ [RAPPORT_INTÉGRÉ] Rapport généré avec succès pour {commune_name}")
        return rapport
        
    except Exception as e:
        print(f"❌ [RAPPORT_INTÉGRÉ] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Erreur lors de la génération du rapport: {str(e)}"}

@app.route("/rapport_commune_complet", methods=["GET", "POST"])
def rapport_commune_complet():
    """
    Génère un rapport complet et exhaustif pour une commune.
    Cette route utilise le module rapport_commune_complet ou la version intégrée en fallback.
    """
    from flask import request as flask_request
    
    try:
        # Récupération des paramètres - Version robuste
        try:
            commune = flask_request.values.get("commune", "").strip()
        except:
            commune = ""
            
        if not commune:
            return jsonify({"error": "Veuillez fournir une commune."}), 400
        
        print(f"📊 [RAPPORT_COMPLET] Génération du rapport exhaustif pour {commune}")
        
        # Récupération des filtres optionnels
        try:
            filters = {
                # Filtres RPG
                "filter_rpg": flask_request.values.get("filter_rpg", "true").lower() == "true",
                "rpg_min_area": float(flask_request.values.get("rpg_min_area", 1.0)),
                "rpg_max_area": float(flask_request.values.get("rpg_max_area", 1000.0)),
            
            # Filtres parkings
            "filter_parkings": flask_request.values.get("filter_parkings", "false").lower() == "true",
            "parking_min_area": float(flask_request.values.get("parking_min_area", 1500.0)),

            # Filtres friches
            "filter_friches": flask_request.values.get("filter_friches", "false").lower() == "true",
            "friches_min_area": float(flask_request.values.get("friches_min_area", 1000.0)),

            # Filtres toitures
            "filter_toitures": flask_request.values.get("filter_toitures", "false").lower() == "true",
            "toitures_min_surface": float(flask_request.values.get("toitures_min_surface", 100.0)),
            
            # Filtres zones
            "filter_zones": flask_request.values.get("filter_zones", "false").lower() == "true",
            "zones_min_area": float(flask_request.values.get("zones_min_area", 1000.0)),
            "zones_type_filter": flask_request.values.get("zones_type_filter", ""),
            
            # Filtres de distance UNIFIÉS (hors zones)
            "filter_by_distance": flask_request.values.get("filter_by_distance", "false").lower() == "true",
            "max_distance_bt": float(flask_request.values.get("max_distance_bt", 500.0)),
            "max_distance_hta": float(flask_request.values.get("max_distance_hta", 2000.0)),
            "poste_type_filter": flask_request.values.get("poste_type_filter", "ALL").upper(),
            "distance_logic": (
                (lambda v: "AND" if v in ("ET", "AND") else ("OR" if v in ("OU", "OR") else "OR"))
            )(flask_request.values.get("distance_logic", "OR").upper()),

            # Autres options
            "calculate_surface_libre": flask_request.values.get("calculate_surface_libre", "false").lower() == "true",
            "include_detailed_analysis": flask_request.values.get("include_detailed_analysis", "true").lower() == "true",
            "export_format": flask_request.values.get("export_format", "json").lower()  # json, html, pdf
        }
        except:
            # Valeurs par défaut en cas d'erreur de lecture des paramètres
            filters = {
                "filter_rpg": True, "rpg_min_area": 1.0, "rpg_max_area": 1000.0,
                "filter_parkings": False, "parking_min_area": 1500.0,
                "filter_friches": False, "friches_min_area": 1000.0,
                "filter_toitures": False, "toitures_min_surface": 100.0,
                "filter_zones": False, "zones_min_area": 1000.0, "zones_type_filter": "",
                "filter_by_distance": False, "max_distance_bt": 500.0, "max_distance_hta": 2000.0,
                "poste_type_filter": "ALL", "distance_logic": "OR",
                "calculate_surface_libre": False, "include_detailed_analysis": True, "export_format": "json"
            }
        
        print(f"📊 [RAPPORT_COMPLET] Filtres appliqués: {len([k for k, v in filters.items() if k.startswith('filter_') and v])} activés")
        
        # Tentative d'utilisation du module complet, sinon fallback vers la version intégrée
        rapport = None
        
        if RAPPORT_COMPLET_AVAILABLE:
            try:
                print(f"📊 [RAPPORT_COMPLET] Utilisation du module rapport_commune_complet.py")
                rapport = generate_comprehensive_commune_report(commune, filters)
            except Exception as e:
                print(f"⚠️ [RAPPORT_COMPLET] Erreur module externe: {e}, utilisation version intégrée")
                rapport = None
        
        # Si le rapport externe est vide (valeurs toutes à 0), basculer sur la version intégrée
        def _is_empty_report(r: dict) -> bool:
            try:
                r = r or {}
                info = r.get("commune_info", {})
                if info.get("superficie_total_ha", 0) > 0:
                    return False
                rpg = r.get("rpg_analysis", {}).get("resume_executif", {})
                pk = r.get("parkings_analysis", {}).get("resume_executif", {})
                fr = r.get("friches_analysis", {}).get("resume_executif", {})
                toi = r.get("toitures_analysis", {}).get("resume_executif", {})
                ent = r.get("socioeconomique_analysis", {}).get("economie", {}).get("entreprises", {})
                if (
                    rpg.get("total_parcelles", 0) > 0 or
                    pk.get("total_parkings", 0) > 0 or
                    fr.get("total_friches", 0) > 0 or
                    toi.get("total_toitures", 0) > 0 or
                    ent.get("total", 0) > 0
                ):
                    return False
                return True
            except Exception:
                return False

        if (not rapport or rapport.get("error") or _is_empty_report(rapport)):
            if rapport and not rapport.get("error"):
                print("⚠️ [RAPPORT_COMPLET] Rapport externe sans données utiles, bascule vers la version intégrée")
            print(f"📊 [RAPPORT_COMPLET] Utilisation de la version intégrée")
            rapport = generate_integrated_commune_report(commune, filters)
        
        # Vérification du succès
        if not rapport or rapport.get("error"):
            error_msg = rapport.get("error", "Erreur inconnue lors de la génération du rapport") if rapport else "Aucun rapport généré"
            print(f"❌ [RAPPORT_COMPLET] Erreur: {error_msg}")
            return jsonify({
                "error": "Erreur lors de la génération du rapport",
                "details": error_msg
            }), 500
        
        # Logging des résultats principaux
        metadata = rapport.get("metadata", {})
        print(f"✅ [RAPPORT_COMPLET] Rapport généré avec succès")
        print(f"    📅 Date: {metadata.get('date_generation', 'N/A')}")
        print(f"    📝 Version: {metadata.get('version_rapport', 'N/A')}")
        print(f"    🔍 Sources: {len(metadata.get('sources_donnees', []))} sources")
        
        # Statistiques rapides
        stats = {
            "commune_info": rapport.get("commune_info", {}).get("superficie_total_ha", 0),
            "rpg_parcelles": rapport.get("rpg_analysis", {}).get("resume_executif", {}).get("total_parcelles", 0),
            "parkings_count": rapport.get("parkings_analysis", {}).get("resume_executif", {}).get("total_parkings", 0),
            "friches_count": rapport.get("friches_analysis", {}).get("resume_executif", {}).get("total_friches", 0),
            "toitures_count": rapport.get("toitures_analysis", {}).get("resume_executif", {}).get("total_toitures", 0),
            "entreprises_count": rapport.get("socioeconomique_analysis", {}).get("economie", {}).get("entreprises", {}).get("total", 0)
        }
        
        print(f"    🌾 Superficie: {stats['commune_info']} ha")
        for key, count in stats.items():
            if key != "commune_info" and count > 0:
                print(f"    📊 {key}: {count} éléments")
        
        # Retour selon le format demandé ou le type de requête
        export_format = filters.get("export_format", "json")
        
        # Détecter si c'est une requête depuis un navigateur (HTML attendu)
        accept_header = flask_request.headers.get('Accept', '')
        is_browser_request = 'text/html' in accept_header and 'application/json' not in accept_header
        
        # Ajouter une URL de carte par défaut pour intégration dans le template
        try:
            if isinstance(rapport, dict) and not rapport.get("carte_url"):
                # Générer une carte dynamique avec les données de la commune au lieu d'utiliser le fichier statique
                # Utiliser la route de génération de carte dynamique
                carte_params = f"commune={commune}"
                if filters.get("filter_rpg"):
                    carte_params += f"&filter_rpg=true&rpg_min_area={filters.get('rpg_min_area', 1.0)}&rpg_max_area={filters.get('rpg_max_area', 1000.0)}"
                if filters.get("filter_parkings"):
                    carte_params += f"&filter_parkings=true&parking_min_area={filters.get('parking_min_area', 1500.0)}"
                if filters.get("filter_friches"):
                    carte_params += f"&filter_friches=true&friches_min_area={filters.get('friches_min_area', 1000.0)}"
                if filters.get("filter_toitures"):
                    carte_params += f"&filter_toitures=true&toitures_min_surface={filters.get('toitures_min_surface', 100.0)}"
                
                rapport["carte_url"] = f"/search_by_commune?{carte_params}"
        except Exception:
            pass

        if export_format == "html" or is_browser_rmaisequest:
            # Retourner une page HTML avec le rapport
            from flask import render_template
            return render_template('rapport_commune_complet.html', rapport=rapport, filters=filters)
        elif export_format == "pdf":
            # TODO: Implémenter la génération PDF
            return jsonify({
                "message": "Format PDF en développement", 
                "rapport": rapport
            })
        else:
            # Format JSON par défaut (pour les appels API)
            return jsonify(rapport)
        
    except Exception as e:
        print(f"❌ [RAPPORT_COMPLET] Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Erreur inattendue lors de la génération du rapport",
            "details": str(e)
        }), 500

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                           PANEL D'ADMINISTRATION                         ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def require_admin(f):
    """Décorateur pour vérifier les droits administrateur"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('session_token'):
            return redirect('/?admin_required=1')
            
        # Vérifier si l'utilisateur est admin
        session_token = session.get('session_token')
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.email, u.is_admin FROM users u
            JOIN user_sessions s ON u.id = s.user_id
            WHERE s.session_token = ? AND s.expires_at > datetime('now')
        """, (session_token,))
        
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data or user_data[1] != 1:  # is_admin = 1
            return redirect('/?admin_required=1')
            
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/sessions')
@require_admin
def admin_sessions():
    """Page de gestion des sessions actives"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Nettoyer les sessions expirées
        cursor.execute('''
            DELETE FROM user_sessions 
            WHERE expires_at < datetime('now')
        ''')
        conn.commit()
        
        # Récupérer toutes les sessions actives avec infos utilisateur
        cursor.execute('''
            SELECT us.user_id, u.email, us.session_token, us.created_at, 
                   us.expires_at, us.ip_address, us.user_agent,
                   COUNT(*) OVER (PARTITION BY us.user_id) as session_count
            FROM user_sessions us
            JOIN users u ON us.user_id = u.id
            WHERE us.expires_at > datetime('now')
            ORDER BY us.created_at DESC
        ''')
        
        sessions = cursor.fetchall()
        conn.close()
        
        return render_template('admin_sessions.html', sessions=sessions)
        
    except Exception as e:
        flash(f'Erreur lors de la récupération des sessions: {e}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/session/revoke/<session_token>', methods=['POST'])
@require_admin
def revoke_session(session_token):
    """Révoquer une session spécifique"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM user_sessions WHERE session_token = ?', (session_token,))
        conn.commit()
        conn.close()
        
        flash('Session révoquée avec succès', 'success')
        
    except Exception as e:
        flash(f'Erreur lors de la révocation: {e}', 'error')
    
    return redirect(url_for('admin_sessions'))

@app.route("/admin", methods=["GET", "POST"])
@require_admin
def admin_dashboard():
    """Tableau de bord administrateur avec tracking Stripe"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Statistiques principales
    stats = {}
    
    # Total utilisateurs
    cursor.execute("SELECT COUNT(*) FROM users")
    stats['total_users'] = cursor.fetchone()[0]
    
    # Nouveaux utilisateurs aujourd'hui
    cursor.execute("SELECT COUNT(*) FROM users WHERE date(created_at) = date('now')")
    stats['new_users_today'] = cursor.fetchone()[0]
    
    # Abonnements par statut
    cursor.execute("SELECT subscription_status, COUNT(*) FROM users GROUP BY subscription_status")
    subscription_stats = dict(cursor.fetchall())
    stats['active_subscriptions'] = subscription_stats.get('active', 0)
    stats['trial_subscriptions'] = subscription_stats.get('trial', 0)
    stats['cancelled_subscriptions'] = subscription_stats.get('cancelled', 0)
    stats['pending_subscriptions'] = subscription_stats.get('pending', 0)
    
    # Essais en cours (valides)
    cursor.execute("SELECT COUNT(*) FROM users WHERE subscription_status = 'trial' AND datetime(trial_end_date) > datetime('now')")
    stats['active_trials'] = cursor.fetchone()[0]
    
    # Essais expirés
    cursor.execute("SELECT COUNT(*) FROM users WHERE subscription_status = 'trial' AND datetime(trial_end_date) <= datetime('now')")
    stats['expired_trials'] = cursor.fetchone()[0]
    
    # Calcul revenus réels basé sur les plans
    revenue_query = """
        SELECT 
            COUNT(CASE WHEN subscription_status = 'active' AND subscription_plan = 'basic' THEN 1 END) * 35 +
            COUNT(CASE WHEN subscription_status = 'active' AND subscription_plan = 'professional' THEN 1 END) * 199 +
            COUNT(CASE WHEN subscription_status = 'active' AND subscription_plan = 'team' THEN 1 END) * 299
        FROM users
    """
    cursor.execute(revenue_query)
    stats['revenue_month'] = cursor.fetchone()[0] or 0
    
    # Taux de conversion essai -> abonnement
    cursor.execute("SELECT COUNT(*) FROM users WHERE subscription_status = 'active' AND created_at >= date('now', '-30 days')")
    conversions = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= date('now', '-30 days')")
    total_signups = cursor.fetchone()[0]
    stats['trial_conversions'] = round((conversions / max(total_signups, 1)) * 100, 1)
    
    # Données Stripe si disponible
    stripe_stats = {}
    if stripe:
        try:
            # Récupérer les derniers paiements
            payments = stripe.PaymentIntent.list(limit=10)
            stripe_stats['recent_payments'] = len([p for p in payments.data if p.status == 'succeeded'])
            stripe_stats['failed_payments'] = len([p for p in payments.data if p.status == 'payment_failed'])
            
            # Calculer le total des paiements réussis aujourd'hui
            today_payments = [p for p in payments.data 
                            if p.status == 'succeeded' and 
                            datetime.fromtimestamp(p.created).date() == datetime.now().date()]
            stripe_stats['today_revenue'] = sum(p.amount for p in today_payments) / 100  # Convertir centimes en euros
            
        except Exception as e:
            print(f"Erreur Stripe stats: {e}")
            stripe_stats = {'error': str(e)}
    
    stats.update(stripe_stats)
    
    # Vues de pages (simulation améliorée)
    stats['page_views_today'] = stats['new_users_today'] * 8 + 47
    stats['unique_visitors'] = stats['new_users_today'] + 23
    
    # Liste des utilisateurs avec infos d'abonnement
    cursor.execute("""
        SELECT id, email, name as username, subscription_status, subscription_plan,
               created_at, last_login, trial_end_date, stripe_customer_id,
               CASE WHEN subscription_status IN ('active', 'trial') THEN 1 ELSE 0 END as is_active
        FROM users 
        ORDER BY created_at DESC 
        LIMIT 50
    """)
    
    users = []
    for row in cursor.fetchall():
        user = {
            'id': row[0],
            'email': row[1],
            'username': row[2],
            'subscription_status': row[3],
            'subscription_plan': row[4] or 'Aucun',
            'created_at': datetime.fromisoformat(row[5]) if row[5] else None,
            'last_login': datetime.fromisoformat(row[6]) if row[6] else None,
            'trial_end_date': datetime.fromisoformat(row[7]) if row[7] else None,
            'stripe_customer_id': row[8],
            'is_active': bool(row[9])
        }
        
        # Ajouter infos Stripe si disponible
        if stripe and user['stripe_customer_id']:
            try:
                customer = stripe.Customer.retrieve(user['stripe_customer_id'])
                subscriptions = stripe.Subscription.list(customer=user['stripe_customer_id'])
                
                if subscriptions.data:
                    sub = subscriptions.data[0]
                    user['stripe_subscription_id'] = sub.id
                    user['stripe_status'] = sub.status
                    user['current_period_end'] = datetime.fromtimestamp(sub.current_period_end)
                    user['monthly_amount'] = sub.items.data[0].price.unit_amount / 100 if sub.items.data else 0
                    
            except Exception as e:
                user['stripe_error'] = str(e)
        
        users.append(user)
    
    conn.close()
    
    # Données pour les graphiques
    chart_data = {
        'users_labels': ['J-6', 'J-5', 'J-4', 'J-3', 'J-2', 'Hier', "Aujourd'hui"],
        'users_data': [2, 1, 3, 0, 1, 2, stats['new_users_today']],
        'revenue_labels': ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun'],
        'revenue_data': [1200, 1800, 2400, 2100, 2700, stats['revenue_month']]
    }
    
    return render_template('admin_dashboard.html', 
                         stats=stats, 
                         users=users, 
                         chart_data=chart_data)

@app.route("/admin/user/<int:user_id>")
@require_admin
def admin_view_user(user_id):
    """Voir les détails d'un utilisateur"""
    c = get_db_connection().cursor()
    c.execute("""
        SELECT id, email, username, subscription_status, created_at, last_login, trial_end_date
        FROM users WHERE id = ?
    """, (user_id,))
    
    user = c.fetchone()
    if not user:
        return "Utilisateur non trouvé", 404
    
    # Sessions de l'utilisateur
    c.execute("""
        SELECT created_at, ip_address, user_agent, expires_at
        FROM sessions WHERE user_id = ?
        ORDER BY created_at DESC LIMIT 10
    """, (user_id,))
    sessions = c.fetchall()
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Utilisateur {{ user[1] }} - Admin</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb">
                    <li class="breadcrumb-item"><a href="/admin">Administration</a></li>
                    <li class="breadcrumb-item active">Utilisateur {{ user[1] }}</li>
                </ol>
            </nav>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5>Informations Utilisateur</h5>
                        </div>
                        <div class="card-body">
                            <p><strong>ID:</strong> {{ user[0] }}</p>
                            <p><strong>Email:</strong> {{ user[1] }}</p>
                            <p><strong>Nom:</strong> {{ user[2] or 'Non défini' }}</p>
                            <p><strong>Statut:</strong> 
                                <span class="badge bg-{{ 'warning' if user[3] == 'trial' else 'success' if user[3] == 'active' else 'secondary' }}">
                                    {{ user[3] }}
                                </span>
                            </p>
                            <p><strong>Inscription:</strong> {{ user[4] }}</p>
                            <p><strong>Dernière connexion:</strong> {{ user[5] or 'Jamais' }}</p>
                            {% if user[6] %}
                            <p><strong>Fin d'essai:</strong> {{ user[6] }}</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5>Sessions Récentes</h5>
                        </div>
                        <div class="card-body">
                            {% for session in sessions %}
                            <div class="border-bottom pb-2 mb-2">
                                <small>
                                    <strong>{{ session[0] }}</strong><br>
                                    IP: {{ session[1] }}<br>
                                    Navigateur: {{ session[2][:50] }}...<br>
                                    Expire: {{ session[3] }}
                                </small>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-3">
                <a href="/admin" class="btn btn-secondary">Retour</a>
                <button class="btn btn-warning" onclick="resetPassword()">Réinitialiser mot de passe</button>
                 <button class="btn btn-primary" onclick="extendTrial()">Prolonger essai</button>
            </div>
        </div>
        
        <script>
            function resetPassword() {
                if (confirm('Réinitialiser le mot de passe de cet utilisateur ?')) {
                    fetch('/admin/user/{{ user[0] }}/reset-password', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => alert(data.message));
                }
            }
            
            function extendTrial() {
                if (confirm('Prolonger l\'essai de 7 jours ?')) {
                    fetch('/admin/user/{{ user[0] }}/extend-trial', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        location.reload();
                    });
                }
            }
        </script>
    </body>
    </html>
    """, user=user, sessions=sessions)

@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@require_admin
def admin_delete_user(user_id):
    """Supprimer un utilisateur"""
    c = get_db_connection().cursor()
    
    # Vérifier que ce n'est pas un compte admin/demo
    c.execute("SELECT email FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    
    if user and user[0] in ['admin@test.com', 'demo@test.com']:
        return jsonify({'error': 'Impossible de supprimer les comptes système'}), 400
    
    # Supprimer les sessions
    c.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    # Supprimer l'utilisateur
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    c.connection.commit()
    
    return jsonify({'success': True, 'message': 'Utilisateur supprimé'})

@app.route("/admin/user/<int:user_id>/reset-password", methods=["POST"])
@require_admin
def admin_reset_password(user_id):
    """Réinitialiser le mot de passe d'un utilisateur"""
    import secrets
    import string
    
    # Générer un nouveau mot de passe
    alphabet = string.ascii_letters + string.digits
    new_password = ''.join(secrets.choice(alphabet) for i in range(8))
    
    # Hasher le mot de passe
    from passlib.hash import pbkdf2_sha256
    hashed_password = pbkdf2_sha256.hash(new_password)
    
    # Mettre à jour en base
    c = get_db_connection().cursor()
    c.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed_password, user_id))
    c.connection.commit()
    
    return jsonify({
        'success': True, 
        'message': f'Nouveau mot de passe: {new_password}',
        'password': new_password
    })

@app.route("/admin/user/<int:user_id>/extend-trial", methods=["POST"])
@require_admin
def admin_extend_trial(user_id):
    """Prolonger l'essai d'un utilisateur"""
    from datetime import datetime, timedelta
    
    # Nouvelle date de fin d'essai (+7 jours)
    new_trial_end = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    
    c = get_db_connection().cursor()
    c.execute("""
        UPDATE users 
        SET trial_end_date = ?, subscription_status = 'trial'
        WHERE id = ?
    """, (new_trial_end, user_id))
    c.connection.commit()
    
    return jsonify({
        'success': True,
        'message': f'Essai prolongé jusqu\'au {new_trial_end[:10]}'
    })

@app.route("/admin/export/users")
@require_admin
def admin_export_users():
    """Exporter la liste des utilisateurs en CSV"""
    import csv
    from io import StringIO
    
    c = get_db_connection().cursor()
    c.execute("""
        SELECT email, username, subscription_status, subscription_plan, created_at, last_login, stripe_customer_id
        FROM users ORDER BY created_at DESC
    """)
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Email', 'Nom', 'Statut', 'Plan', 'Inscription', 'Dernière connexion', 'ID Stripe'])
    
    for row in c.fetchall():
        writer.writerow(row)
    
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=users.csv'}
    )

@app.route("/admin/stripe/dashboard")
@require_admin
def admin_stripe_dashboard():
    """Dashboard spécifique Stripe"""
    if not stripe:
        return jsonify({'error': 'Stripe non configuré'}), 500
    
    try:
        # Récupérer les statistiques Stripe
        stripe_data = {}
        
        # Derniers paiements
        payments = stripe.PaymentIntent.list(limit=20)
        stripe_data['recent_payments'] = []
        for payment in payments.data:
            stripe_data['recent_payments'].append({
                'id': payment.id,
                'amount': payment.amount / 100,
                'currency': payment.currency.upper(),
                'status': payment.status,
                'created': datetime.fromtimestamp(payment.created),
                'customer': payment.customer
            })
        
        # Abonnements actifs
        subscriptions = stripe.Subscription.list(limit=50, status='active')
        stripe_data['active_subscriptions'] = []
        total_mrr = 0
        
        for sub in subscriptions.data:
            amount = sub.items.data[0].price.unit_amount / 100 if sub.items.data else 0
            total_mrr += amount
            
            # Récupérer infos client
            customer = stripe.Customer.retrieve(sub.customer)
            
            stripe_data['active_subscriptions'].append({
                'id': sub.id,
                'customer_email': customer.email,
                'amount': amount,
                'status': sub.status,
                'current_period_end': datetime.fromtimestamp(sub.current_period_end),
                'plan': sub.items.data[0].price.nickname if sub.items.data else 'Inconnu'
            })
        
        stripe_data['total_mrr'] = total_mrr
        stripe_data['subscription_count'] = len(stripe_data['active_subscriptions'])
        
        # Statistiques des paiements échoués
        failed_payments = [p for p in payments.data if p.status == 'payment_failed']
        stripe_data['failed_payments_count'] = len(failed_payments)
        
        return render_template_string(ADMIN_STRIPE_TEMPLATE, stripe_data=stripe_data)
        
    except Exception as e:
        return jsonify({'error': f'Erreur Stripe: {str(e)}'}), 500

@app.route("/admin/user/<int:user_id>/stripe-sync", methods=["POST"])
@require_admin  
def admin_sync_stripe_user(user_id):
    """Synchroniser les données Stripe d'un utilisateur"""
    if not stripe:
        return jsonify({'error': 'Stripe non configuré'}), 500
        
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Récupérer l'utilisateur
        cursor.execute("SELECT email, stripe_customer_id FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
            
        email, stripe_customer_id = user
        
        if stripe_customer_id:
            # Récupérer les données Stripe
            customer = stripe.Customer.retrieve(stripe_customer_id)
            subscriptions = stripe.Subscription.list(customer=stripe_customer_id)
            
            if subscriptions.data:
                sub = subscriptions.data[0]
                
                # Mettre à jour la base de données
                cursor.execute("""
                    UPDATE users SET 
                        subscription_status = ?,
                        subscription_plan = ?,
                        stripe_subscription_id = ?
                    WHERE id = ?
                """, (
                    'active' if sub.status == 'active' else sub.status,
                    sub.items.data[0].price.nickname if sub.items.data else 'professional',
                    sub.id,
                    user_id
                ))
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Données Stripe synchronisées',
                    'subscription_status': sub.status,
                    'plan': sub.items.data[0].price.nickname if sub.items.data else 'professional'
                })
            else:
                return jsonify({'error': 'Aucun abonnement Stripe trouvé'}), 404
        else:
            return jsonify({'error': 'Aucun ID client Stripe'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Erreur: {str(e)}'}), 500
    finally:
        conn.close()

@app.route("/admin/system/check")
@require_admin
def admin_system_check():
    """Vérification du système"""
    status = {
        'status': 'OK',
        'database': 'Connectée',
        'servers': 'En ligne'
    }
    
    try:
        # Test base de données
        c = get_db_connection().cursor()
        c.execute("SELECT COUNT(*) FROM users")
        c.fetchone()
    except:
        status['database'] = 'Erreur'
        status['status'] = 'ERREUR'
    
    return jsonify(status)

@app.route("/admin/logs")
@require_admin
def admin_logs():
    """Afficher les logs système"""
    try:
        with open('error.log', 'r') as f:
            logs = f.read()
    except:
        logs = "Aucun log disponible"
    
    return f"<pre>{logs}</pre>"

# Fonction pour créer un utilisateur admin au démarrage
def create_admin_user():
    """Créer un utilisateur admin si nécessaire"""
    c = get_db_connection().cursor()
    
    # Vérifier si admin existe déjà
    c.execute("SELECT id FROM users WHERE email = 'admin@test.com'")
    if c.fetchone():
        # Mettre à jour pour s'assurer qu'il est admin
        c.execute("UPDATE users SET is_admin = 1 WHERE email = 'admin@test.com'")
        c.connection.commit()
        return
    
    # Créer l'utilisateur admin
    from passlib.hash import pbkdf2_sha256
    admin_password = pbkdf2_sha256.hash('admin123')
    
    c.execute("""
        INSERT INTO users (email, username, password_hash, subscription_status, is_admin, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ('admin@test.com', 'Administrateur', admin_password, 'active', 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    c.connection.commit()
    print("✅ Utilisateur admin créé: admin@test.com / admin123")

# Template pour la page de sélection des plans
SUBSCRIPTION_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plans d'abonnement - AgriWeb Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .pricing-card { 
            border: 2px solid #e9ecef; border-radius: 16px; transition: all 0.3s ease; 
            position: relative; overflow: hidden; background: white;
        }
        .pricing-card:hover { transform: translateY(-5px); box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
        .pricing-card.featured { border-color: #007bff; transform: scale(1.05); }
        .pricing-card.featured::before {
            content: "Le plus populaire"; position: absolute; top: 0; left: 0; right: 0;
            background: linear-gradient(135deg, #007bff, #0056b3); color: white; text-align: center;
            padding: 8px; font-size: 0.875rem; font-weight: 600;
        }
        .price { font-size: 3rem; font-weight: 700; color: #007bff; }
        .price-period { font-size: 1rem; color: #6c757d; }
        .btn-subscribe {
            background: linear-gradient(135deg, #007bff, #0056b3); border: none; border-radius: 12px;
            padding: 1rem 2rem; font-weight: 600; font-size: 1.1rem; transition: all 0.3s ease;
        }
        .btn-subscribe:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,123,255,0.3); }
        .trial-badge { background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.875rem; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container py-5">
        <div class="text-center mb-5 text-white">
            <h1 class="display-4 fw-bold mb-3">Choisissez votre plan AgriWeb Pro</h1>
            <p class="lead mb-4">Accédez à l'analyse territoriale la plus avancée pour vos projets agricoles et énergétiques</p>
            <div class="trial-badge d-inline-block">
                <i class="fas fa-gift me-2"></i>7 jours d'essai gratuit sur tous les plans
            </div>
        </div>

        <div class="row g-4 mb-5">
            <!-- Plan Basic -->
            <div class="col-lg-4">
                <div class="card pricing-card h-100">
                    <div class="card-body p-4">
                        <div class="text-center mb-4">
                            <h3 class="card-title h4 fw-bold">Basic</h3>
                            <p class="text-muted">Pour débuter</p>
                            <div class="price">35€<span class="price-period">/mois</span></div>
                        </div>
                        <ul class="list-unstyled mb-4">
                            <li><i class="fas fa-check text-success me-2"></i>Recherche par coordonnées</li>
                            <li><i class="fas fa-check text-success me-2"></i>Rapports de base</li>
                            <li><i class="fas fa-check text-success me-2"></i>Export PDF</li>
                            <li><i class="fas fa-check text-success me-2"></i>Support email</li>
                            <li><i class="fas fa-check text-success me-2"></i>1 utilisateur</li>
                        </ul>
                        <button class="btn btn-outline-primary btn-subscribe w-100" onclick="selectPlan('basic')" data-plan="basic">
                            <span class="btn-text">Commencer l'essai gratuit</span>
                            <span class="loading d-none"><i class="fas fa-spinner fa-spin"></i> Redirection...</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Plan Professional -->
            <div class="col-lg-4">
                <div class="card pricing-card featured h-100">
                    <div class="card-body p-4" style="margin-top: 40px;">
                        <div class="text-center mb-4">
                            <h3 class="card-title h4 fw-bold">Professional</h3>
                            <p class="text-muted">Le plus populaire</p>
                            <div class="price">199€<span class="price-period">/mois</span></div>
                        </div>
                        <ul class="list-unstyled mb-4">
                            <li><i class="fas fa-check text-success me-2"></i>Toutes les fonctionnalités</li>
                            <li><i class="fas fa-check text-success me-2"></i>Recherches illimitées</li>
                            <li><i class="fas fa-check text-success me-2"></i>Rapports complets</li>
                            <li><i class="fas fa-check text-success me-2"></i>Exports avancés</li>
                            <li><i class="fas fa-check text-success me-2"></i>Support prioritaire</li>
                            <li><i class="fas fa-check text-success me-2"></i>1 poste utilisateur</li>
                        </ul>
                        <button class="btn btn-primary btn-subscribe w-100" onclick="selectPlan('professional')" data-plan="professional">
                            <span class="btn-text">Commencer l'essai gratuit</span>
                            <span class="loading d-none"><i class="fas fa-spinner fa-spin"></i> Redirection...</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Plan Team -->
            <div class="col-lg-4">
                <div class="card pricing-card h-100">
                    <div class="card-body p-4">
                        <div class="text-center mb-4">
                            <h3 class="card-title h4 fw-bold">Team</h3>
                            <p class="text-muted">Pour les équipes</p>
                            <div class="price">299€<span class="price-period">/mois</span></div>
                        </div>
                        <ul class="list-unstyled mb-4">
                            <li><i class="fas fa-check text-success me-2"></i>Tout Professional +</li>
                            <li><i class="fas fa-check text-success me-2"></i>Recherches illimitées</li>
                            <li><i class="fas fa-check text-success me-2"></i>Rapports complets</li>
                            <li><i class="fas fa-check text-success me-2"></i>Exports avancés</li>
                            <li><i class="fas fa-check text-success me-2"></i>Support prioritaire</li>
                            <li><i class="fas fa-check text-success me-2"></i>3 postes utilisateurs</li>
                            <li><i class="fas fa-check text-success me-2"></i>Gestion d'équipe</li>
                        </ul>
                        <button class="btn btn-outline-primary btn-subscribe w-100" onclick="selectPlan('team')" data-plan="team">
                            <span class="btn-text">Commencer l'essai gratuit</span>
                            <span class="loading d-none"><i class="fas fa-spinner fa-spin"></i> Redirection...</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <div class="text-center text-white">
            <p class="mb-2"><i class="fas fa-shield-alt me-2"></i>Paiements sécurisés par Stripe</p>
            <p class="mb-0"><i class="fas fa-undo me-2"></i>Annulation facile à tout moment</p>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        async function selectPlan(plan) {
            try {
                const response = await fetch('/api/stripe/create-checkout', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ plan: plan })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                
                if (result.url) {
                    // Ouvrir dans un nouvel onglet au lieu d'une redirection
                    window.open(result.url, '_blank');
                } else {
                    alert('Erreur: Pas d\'URL de paiement reçue');
                }
                
            } catch (error) {
                alert('Erreur: ' + error.message);
            }
        }
    </script>
</body>
</html>
"""

# Template pour le dashboard admin Stripe
ADMIN_STRIPE_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Stripe - AgriWeb Pro Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container-fluid py-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1 class="h3"><i class="fab fa-stripe me-2"></i>Dashboard Stripe</h1>
            <a href="/admin" class="btn btn-outline-primary">← Retour Admin</a>
        </div>

        <!-- Statistiques principales -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card text-white bg-success">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h4 class="card-title">{{ stripe_data.total_mrr }}€</h4>
                                <p class="card-text">MRR Total</p>
                            </div>
                            <i class="fas fa-euro-sign fa-2x opacity-75"></i>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-white bg-primary">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h4 class="card-title">{{ stripe_data.subscription_count }}</h4>
                                <p class="card-text">Abonnements Actifs</p>
                            </div>
                            <i class="fas fa-users fa-2x opacity-75"></i>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-white bg-info">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h4 class="card-title">{{ stripe_data.recent_payments|length }}</h4>
                                <p class="card-text">Paiements Récents</p>
                            </div>
                            <i class="fas fa-credit-card fa-2x opacity-75"></i>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-white bg-warning">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h4 class="card-title">{{ stripe_data.failed_payments_count }}</h4>
                                <p class="card-text">Paiements Échoués</p>
                            </div>
                            <i class="fas fa-exclamation-triangle fa-2x opacity-75"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <!-- Abonnements actifs -->
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Abonnements Actifs</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Client</th>
                                        <th>Plan</th>
                                        <th>Montant</th>
                                        <th>Statut</th>
                                        <th>Prochaine facturation</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for sub in stripe_data.active_subscriptions %}
                                    <tr>
                                        <td>{{ sub.customer_email }}</td>
                                        <td><span class="badge bg-primary">{{ sub.plan }}</span></td>
                                        <td><strong>{{ sub.amount }}€</strong></td>
                                        <td>
                                            <span class="badge bg-success">{{ sub.status }}</span>
                                        </td>
                                        <td>{{ sub.current_period_end.strftime('%d/%m/%Y') }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Paiements récents -->
            <div class="col-lg-4">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Paiements Récents</h5>
                    </div>
                    <div class="card-body">
                        {% for payment in stripe_data.recent_payments[:10] %}
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <div>
                                <div class="fw-bold">{{ payment.amount }}{{ payment.currency }}</div>
                                <small class="text-muted">{{ payment.created.strftime('%d/%m %H:%M') }}</small>
                            </div>
                            <span class="badge {% if payment.status == 'succeeded' %}bg-success{% elif payment.status == 'pending' %}bg-warning{% else %}bg-danger{% endif %}">
                                {{ payment.status }}
                            </span>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

def import_existing_users():
    """Import des utilisateurs existants pour préserver leurs authentifications"""
    existing_users = [
        {
            'id': 16,
            'email': 'ismailolafimihan@gmail.com',
            'name': 'Olaf Ismail',
            'company': '',
            'created_at': '2025-09-12',
            'last_login': '2025-09-12 09:31',
            'subscription_status': 'active'
        },
        {
            'id': 15,
            'email': 'lilian.bortolotto@techniquesolaire.com',
            'name': 'LILIAN BORTOLOTTO',
            'company': 'Technique Solaire',
            'created_at': '2025-09-12',
            'last_login': '2025-09-12 09:30',
            'subscription_status': 'active'
        },
        {
            'id': 14,
            'email': 'bappel@energiesdeloire.com',
            'name': 'BÉRÉNICE APPEL',
            'company': 'Énergies de Loire',
            'created_at': '2025-09-12',
            'last_login': '2025-09-12 07:54',
            'subscription_status': 'active'
        },
        {
            'id': 13,
            'email': 'farid.moucer@enoe-energie.fr',
            'name': 'Farid MOUCER',
            'company': 'ENOE Énergie',
            'created_at': '2025-09-12',
            'last_login': '2025-09-12 07:22',
            'subscription_status': 'active'
        },
        {
            'id': 12,
            'email': 'demo@test.com',
            'name': 'Utilisateur Demo',
            'company': 'Demo',
            'created_at': '2025-09-08',
            'last_login': None,
            'subscription_status': 'active'
        },
        {
            'id': 3,
            'email': 'admin@test.com',
            'name': 'Administrateur',
            'company': 'Admin',
            'created_at': '2025-08-20',
            'last_login': '2025-09-11 19:41',
            'subscription_status': 'active'
        }
    ]
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        for user in existing_users:
            # Vérifier si l'utilisateur existe déjà
            cursor.execute('SELECT id FROM users WHERE email = ?', (user['email'],))
            existing = cursor.fetchone()
            
            if not existing:
                # Créer un hash de mot de passe temporaire (ils devront le changer)
                temp_password = f"temp_{user['id']}_password"
                password_hash, salt = hash_password(temp_password)
                
                # Insérer l'utilisateur avec l'ID spécifique
                cursor.execute('''
                    INSERT OR IGNORE INTO users 
                    (id, email, name, company, password_hash, salt, created_at, 
                     last_login, subscription_status, is_active, login_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 
                            CASE WHEN ? IS NULL THEN 0 ELSE 1 END)
                ''', (
                    user['id'], user['email'], user['name'], user['company'],
                    password_hash, salt, user['created_at'], user['last_login'],
                    user['subscription_status'], user['last_login']
                ))
                
                print(f"✅ Utilisateur importé: {user['name']} ({user['email']})")
            else:
                print(f"ℹ️ Utilisateur existe déjà: {user['email']}")
        
        conn.commit()
        conn.close()
        print("🎉 Import des utilisateurs existants terminé!")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'import des utilisateurs: {e}")

# ========== API POUR GESTION DES CARTES SAUVEGARDÉES ==========

@app.route("/saved_maps")
def saved_maps_page():
    """Page pour gérer les cartes sauvegardées"""
    return render_template("saved_maps.html")

@app.route("/api/list_saved_maps")
def list_saved_maps():
    """Liste toutes les cartes HTML sauvegardées dans static/cartes/"""
    import os
    import time
    
    cartes_dir = os.path.join(os.path.dirname(__file__), "static", "cartes")
    
    if not os.path.exists(cartes_dir):
        return jsonify({"maps": []})
    
    maps = []
    for filename in os.listdir(cartes_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(cartes_dir, filename)
            stat = os.stat(filepath)
            
            # Formater la date
            mtime = time.localtime(stat.st_mtime)
            date_formatted = time.strftime("%d/%m/%Y %H:%M", mtime)
            date_iso = time.strftime("%Y-%m-%d %H:%M:%S", mtime)
            
            # Nom d'affichage amélioré
            # Format fichier: commune_NomCommune_uuid_timestamp.html ou rapport_Adresse_uuid_timestamp.html
            display_name = filename.replace('.html', '')
            
            # Extraire le nom lisible (entre le type et l'UUID)
            parts = display_name.split('_')
            if len(parts) >= 3:
                # parts[0] = type (commune/rapport)
                # parts[1...-2] = nom de la commune/adresse
                # parts[-2] = UUID (8 caractères)
                # parts[-1] = timestamp
                type_carte = parts[0].capitalize()
                
                # Reconstruire le nom sans UUID et timestamp
                # On prend tout sauf le premier (type), les 2 derniers (UUID + timestamp)
                if len(parts) > 3:
                    nom_lieu = ' '.join(parts[1:-2])
                else:
                    nom_lieu = parts[1] if len(parts) > 1 else display_name
                
                display_name = f"{type_carte}: {nom_lieu}"
            else:
                # Fallback: simple remplacement underscores
                display_name = display_name.replace('_', ' ')
            
            # Limiter la longueur
            if len(display_name) > 40:
                display_name = display_name[:37] + '...'
            
            maps.append({
                "name": filename,
                "displayName": display_name,
                "url": f"/static/cartes/{filename}",
                "size": stat.st_size,
                "date": date_iso,
                "dateFormatted": date_formatted,
                "timestamp": stat.st_mtime
            })
    
    return jsonify({"maps": maps, "total": len(maps)})

@app.route("/api/delete_saved_map", methods=["POST"])
def delete_saved_map():
    """Supprimer une carte sauvegardée"""
    import os
    
    data = request.get_json()
    filename = data.get("filename")
    
    if not filename or not filename.endswith('.html'):
        return jsonify({"success": False, "error": "Nom de fichier invalide"})
    
    cartes_dir = os.path.join(os.path.dirname(__file__), "static", "cartes")
    filepath = os.path.join(cartes_dir, filename)
    
    # Sécurité: vérifier que le fichier est bien dans le dossier cartes
    if not filepath.startswith(cartes_dir):
        return jsonify({"success": False, "error": "Accès non autorisé"})
    
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Fichier introuvable"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/save_dept_map", methods=["POST"])
def save_dept_map():
    """
    Générer et sauvegarder une carte pour une recherche départementale
    """
    import glob
    
    try:
        data = request.get_json()
        department = data.get("department")
        results = data.get("results", [])
        
        if not department or not results:
            return jsonify({"success": False, "error": "Données manquantes"})
        
        print(f"🗺️ [SAVE_DEPT] Génération carte département {department} avec {len(results)} résultats")
        
        # Agréger toutes les données de toutes les communes
        all_parcelles = []
        all_postes_bt = []
        all_postes_hta = []
        all_hta_lignes = []
        center_lat, center_lon = None, None
        
        for result in results:
            if result.get("rpg"):
                all_parcelles.extend(result["rpg"])
            if result.get("postes_bt"):
                all_postes_bt.extend(result["postes_bt"])
            if result.get("postes_hta"):
                all_postes_hta.extend(result["postes_hta"])
            if result.get("hta_lignes"):
                all_hta_lignes.extend(result["hta_lignes"])
            
            # Utiliser la première coordonnée comme centre
            if center_lat is None and result.get("lat"):
                center_lat = result["lat"]
                center_lon = result["lon"]
        
        if center_lat is None:
            center_lat, center_lon = 46.5, 2.5  # Centre France par défaut
        
        # Créer une carte simple avec toutes les données
        map_obj = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles="OpenStreetMap")
        
        # Ajouter les couches (simplifié)
        if all_parcelles:
            parcelles_group = folium.FeatureGroup(name="Parcelles RPG")
            for p in all_parcelles[:1000]:  # Limiter à 1000 pour performance
                if p.get("geometry"):
                    folium.GeoJson(p, style_function=lambda x: {"color": "green", "weight": 1}).add_to(parcelles_group)
            map_obj.add_child(parcelles_group)
        
        if all_postes_bt:
            bt_group = folium.FeatureGroup(name="Postes BT")
            for poste in all_postes_bt[:500]:  # Limiter
                if poste.get("lat") and poste.get("lon"):
                    folium.CircleMarker(
                        [poste["lat"], poste["lon"]],
                        radius=5,
                        color="orange",
                        fill=True
                    ).add_to(bt_group)
            map_obj.add_child(bt_group)
        
        if all_postes_hta:
            hta_group = folium.FeatureGroup(name="Postes HTA")
            for poste in all_postes_hta[:500]:
                if poste.get("lat") and poste.get("lon"):
                    folium.CircleMarker(
                        [poste["lat"], poste["lon"]],
                        radius=7,
                        color="red",
                        fill=True
                    ).add_to(hta_group)
            map_obj.add_child(hta_group)
        
        # Ajouter contrôle des couches
        folium.LayerControl().add_to(map_obj)
        
        # 🧹 Nettoyage: supprimer anciennes cartes du même département
        cartes_dir = os.path.join(os.path.dirname(__file__), "static", "cartes")
        os.makedirs(cartes_dir, exist_ok=True)
        
        pattern = os.path.join(cartes_dir, f"departement_{department}_*.html")
        old_maps = glob.glob(pattern)
        
        for old_map in old_maps:
            try:
                os.remove(old_map)
                print(f"   ✓ Supprimé ancienne carte: {os.path.basename(old_map)}")
            except Exception as e:
                print(f"   ⚠️ Erreur suppression: {e}")
        
        # Sauvegarder avec nom sécurisé
        filename = generate_secure_filename("departement", department)
        filepath = os.path.join(cartes_dir, filename)
        map_obj.save(filepath)
        
        print(f"✅ [SAVE_DEPT] Carte sauvegardée: {filename}")
        
        return jsonify({
            "success": True,
            "filename": filename,
            "url": f"/static/cartes/{filename}",
            "features_count": {
                "parcelles": len(all_parcelles),
                "postes_bt": len(all_postes_bt),
                "postes_hta": len(all_postes_hta)
            }
        })
        
    except Exception as e:
        import traceback
        print(f"❌ [SAVE_DEPT] Erreur: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/send_to_kpi", methods=["POST"])
def send_to_kpi():
    """
    Collecte TOUTES les données autour d'un point (toiture/parking/friche/poste)
    et envoie un dossier complet vers KPI
    """
    try:
        data = request.get_json()
        lat = data.get("lat")
        lon = data.get("lon")
        point_type = data.get("type")  # toiture, parking, friche, poste, plu
        properties = data.get("properties", {})
        
        if not lat or not lon:
            return jsonify({"success": False, "error": "Coordonnées manquantes"})
        
        print(f"📤 [KPI] Collecte données pour {point_type} à ({lat}, {lon})")
        
        # ÉTAPE 1: Collecter toutes les données environnantes
        rayon_analyse = 0.05  # ~5km
        
        # Postes électriques
        print("⚡ [KPI] Collecte postes BT/HTA...")
        postes_bt = get_postes_info(lat, lon, radius=0.02) or []
        postes_hta = get_ht_postes_info(lat, lon, radius=0.05) or []
        
        # PLU
        print("🏛️ [KPI] Collecte PLU...")
        plu_info = get_plu_info(lat, lon) or []
        
        # Cadastre
        print("📍 [KPI] Collecte cadastre...")
        cadastre = get_cadastre_info(lat, lon) or []
        
        # Risques GeoRisques
        print("⚠️ [KPI] Collecte risques...")
        risques = fetch_georisques_risks(lat, lon)
        
        # Lignes HTA
        print("🔌 [KPI] Collecte lignes HTA...")
        hta_lignes = get_hta_lignes(lat, lon, radius_km=5.0) or []
        
        # Zones naturelles protégées
        print("🌿 [KPI] Collecte zones naturelles...")
        znieff1 = get_znieff_type1(lat, lon) or []
        znieff2 = get_znieff_type2(lat, lon) or []
        
        # RPG (parcelles agricoles)
        print("🌾 [KPI] Collecte RPG...")
        rpg = get_rpg_info(lat, lon) or []
        
        # ÉTAPE 2: Calculer les distances aux postes les plus proches
        min_dist_bt = None
        closest_bt = None
        if postes_bt:
            from math import radians, cos, sin, asin, sqrt
            def haversine(lat1, lon1, lat2, lon2):
                R = 6371000  # Rayon Terre en mètres
                lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                return R * c
            
            for poste in postes_bt:
                if poste.get("lat") and poste.get("lon"):
                    dist = haversine(lat, lon, poste["lat"], poste["lon"])
                    if min_dist_bt is None or dist < min_dist_bt:
                        min_dist_bt = dist
                        closest_bt = poste
        
        min_dist_hta = None
        closest_hta = None
        if postes_hta:
            for poste in postes_hta:
                if poste.get("lat") and poste.get("lon"):
                    dist = haversine(lat, lon, poste["lat"], poste["lon"])
                    if min_dist_hta is None or dist < min_dist_hta:
                        min_dist_hta = dist
                        closest_hta = poste
        
        # ÉTAPE 3: Créer le dossier de prospection complet
        dossier = {
            "type_point": point_type,
            "localisation": {
                "latitude": lat,
                "longitude": lon,
                "adresse": properties.get("adresse", "Non définie"),
                "commune": properties.get("commune", "Non définie"),
                "code_postal": properties.get("code_postal", "Non défini")
            },
            "caracteristiques_site": {
                "surface_m2": properties.get("surface_m2") or properties.get("area") or properties.get("surface_toiture_m2"),
                "surface_ha": (properties.get("surface_m2") or properties.get("area") or 0) / 10000,
                "parcelles_cadastrales": properties.get("parcelles_cadastrales", [])
            },
            "reseau_electrique": {
                "poste_bt_proche": {
                    "distance_m": round(min_dist_bt) if min_dist_bt else None,
                    "nom": closest_bt.get("properties", {}).get("nom") if closest_bt else None,
                    "puissance": closest_bt.get("properties", {}).get("puissance") if closest_bt else None
                },
                "poste_hta_proche": {
                    "distance_m": round(min_dist_hta) if min_dist_hta else None,
                    "nom": closest_hta.get("properties", {}).get("nom") if closest_hta else None
                },
                "lignes_hta_proches": len(hta_lignes),
                "total_postes_bt_rayon": len(postes_bt),
                "total_postes_hta_rayon": len(postes_hta)
            },
            "urbanisme": {
                "zones_plu": [z.get("properties", {}).get("typezone") for z in plu_info] if plu_info else [],
                "nb_zones": len(plu_info)
            },
            "contraintes_environnementales": {
                "risques": {
                    "inondation": risques.get("inondation", []),
                    "argiles": risques.get("argiles", []),
                    "radon": risques.get("radon", []),
                    "seisme": risques.get("seisme", []),
                    "icpe": risques.get("icpe", [])
                },
                "zones_protegees": {
                    "znieff_type1": len(znieff1),
                    "znieff_type2": len(znieff2)
                }
            },
            "contexte_agricole": {
                "parcelles_rpg_proches": len(rpg),
                "cultures": list(set([p.get("properties", {}).get("code_cultu") for p in rpg if p.get("properties", {}).get("code_cultu")])) if rpg else []
            },
            "donnees_brutes": {
                "postes_bt": postes_bt[:10],  # Limiter à 10 pour ne pas surcharger
                "postes_hta": postes_hta[:10],
                "plu": plu_info,
                "cadastre": cadastre[:5],
                "risques_detail": risques
            },
            "date_collecte": datetime.now().isoformat(),
            "source": "AgriWeb Prospection"
        }
        
        # ÉTAPE 4: Créer un résumé texte
        summary_lines = []
        summary_lines.append(f"📍 {point_type.upper()}")
        summary_lines.append(f"📏 Surface: {dossier['caracteristiques_site']['surface_ha']:.2f} ha")
        if min_dist_bt:
            summary_lines.append(f"⚡ Poste BT: {round(min_dist_bt)}m")
        if min_dist_hta:
            summary_lines.append(f"⚡ Poste HTA: {round(min_dist_hta)}m")
        summary_lines.append(f"🏛️ Zones PLU: {dossier['urbanisme']['nb_zones']}")
        summary_lines.append(f"⚠️ Risques: {sum([len(v) if isinstance(v, list) else (1 if v else 0) for v in dossier['contraintes_environnementales']['risques'].values()])}")
        
        summary = " | ".join(summary_lines)
        
        # ÉTAPE 5: Envoyer vers KPI via kpi_integration
        print(f"📤 [KPI] Envoi vers module KPI...")
        try:
            from kpi_integration import sync_agriculteur_to_kpi
            
            # Adapter le format pour KPI
            kpi_data = {
                "nom": f"{point_type} - {properties.get('adresse', 'Sans adresse')[:50]}",
                "type": f"Prospection {point_type}",
                "email": "",
                "telephone": "",
                "adresse": properties.get("adresse", "Non définie"),
                "code_postal": properties.get("code_postal", ""),
                "ville": properties.get("commune", ""),
                "departement": properties.get("code_postal", "")[:2] if properties.get("code_postal") else "",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "notes": f"""DOSSIER PROSPECTION AUTOMATIQUE
                
{summary}

CARACTÉRISTIQUES:
- Surface: {dossier['caracteristiques_site']['surface_ha']:.2f} ha
- Parcelles cadastrales: {len(dossier['caracteristiques_site']['parcelles_cadastrales'])}

RÉSEAU ÉLECTRIQUE:
- Poste BT proche: {round(min_dist_bt) if min_dist_bt else 'N/A'}m
- Poste HTA proche: {round(min_dist_hta) if min_dist_hta else 'N/A'}m

URBANISME:
- Zones PLU: {', '.join(dossier['urbanisme']['zones_plu'][:3])}

CONTRAINTES:
- Risques identifiés: {sum([len(v) if isinstance(v, list) else (1 if v else 0) for v in dossier['contraintes_environnementales']['risques'].values()])}
- Zones protégées: ZNIEFF1={dossier['contraintes_environnementales']['zones_protegees']['znieff_type1']}, ZNIEFF2={dossier['contraintes_environnementales']['zones_protegees']['znieff_type2']}

Source: AgriWeb - Collecte automatique le {datetime.now().strftime('%d/%m/%Y %H:%M')}
Coordonnées: {lat}, {lon}
"""
            }
            
            result = sync_agriculteur_to_kpi(kpi_data)
            kpi_id = result.get("id") if result.get("status") == "success" else None
            
            print(f"✅ [KPI] Envoyé avec succès, ID: {kpi_id}")
            
        except ImportError:
            print(f"⚠️ [KPI] Module kpi_integration non disponible, sauvegarde locale uniquement")
            kpi_id = None
        except Exception as e:
            print(f"⚠️ [KPI] Erreur envoi KPI: {e}")
            kpi_id = None
        
        # ÉTAPE 6: Sauvegarder localement en backup JSON
        import json
        backup_dir = os.path.join(os.path.dirname(__file__), "kpi_exports")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"kpi_export_{point_type}_{timestamp}.json")
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(dossier, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 [KPI] Backup sauvegardé: {backup_file}")
        
        return jsonify({
            "success": True,
            "summary": summary,
            "kpi_id": kpi_id,
            "backup_file": os.path.basename(backup_file),
            "dossier": dossier,
            "stats": {
                "postes_bt": len(postes_bt),
                "postes_hta": len(postes_hta),
                "zones_plu": len(plu_info),
                "risques": sum([len(v) if isinstance(v, list) else (1 if v else 0) for v in risques.values()])
            }
        })
        
    except Exception as e:
        import traceback
        print(f"❌ [KPI] Erreur: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/clean_old_maps", methods=["POST"])
def clean_old_maps():
    """Supprimer les cartes de plus de X jours"""
    import os
    import time
    
    data = request.get_json()
    days = data.get("days", 7)
    
    cartes_dir = os.path.join(os.path.dirname(__file__), "static", "cartes")
    
    if not os.path.exists(cartes_dir):
        return jsonify({"success": True, "deleted": 0})
    
    now = time.time()
    cutoff = now - (days * 24 * 60 * 60)
    deleted = 0
    
    for filename in os.listdir(cartes_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(cartes_dir, filename)
            mtime = os.path.getmtime(filepath)
            
            if mtime < cutoff:
                try:
                    os.remove(filepath)
                    deleted += 1
                except Exception as e:
                    print(f"Erreur suppression {filename}: {e}")
    
    return jsonify({"success": True, "deleted": deleted})

# ========== FIN API CARTES SAUVEGARDÉES ==========

# ========== INTÉGRATION KPI ==========

@app.route("/kpi_sync")
def kpi_sync_page():
    """Page de synchronisation KPI"""
    return render_template("kpi_sync.html")

@app.route("/api/get_agriweb_prospects")
def get_agriweb_prospects():
    """
    Récupère tous les prospects depuis AgriWeb (éleveurs + entreprises)
    Format standardisé pour envoi vers KPI
    """
    try:
        # Vous pouvez adapter cette requête selon votre BDD
        # Ici on récupère depuis les résultats en session ou cache
        
        prospects = []
        
        # Si vous avez une session avec résultats département
        if 'last_dept_results' in session:
            results = session.get('last_dept_results', [])
            for result in results:
                if result.get('eleveurs'):
                    for eleveur in result['eleveurs']:
                        props = eleveur.get('properties', {})
                        prospects.append({
                            'id': f"elev_{props.get('siret', '')}_{len(prospects)}",
                            'nom': props.get('denomination') or f"{props.get('nom', '')} {props.get('prenom', '')}",
                            'type': 'Eleveur',
                            'email': props.get('email', ''),
                            'telephone': props.get('telephone', ''),
                            'adresse': props.get('adresse', ''),
                            'code_postal': props.get('code_postal', ''),
                            'ville': props.get('commune', ''),
                            'departement': props.get('departement', ''),
                            'siret': props.get('siret', ''),
                            'activite': props.get('activite', ''),
                            'synced': False  # À vérifier côté KPI
                        })
        
        # Alternative: récupérer depuis window.lastDeptResults côté client
        # ou d'une base de données locale
        
        return jsonify({"success": True, "prospects": prospects})
        
    except Exception as e:
        print(f"❌ [KPI] Erreur get prospects: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/kpi_stats")
def kpi_stats():
    """Stats de la base KPI"""
    try:
        from kpi_integration import test_kpi_connection, kpi_client
        
        if test_kpi_connection():
            stats = kpi_client.get_stats()
            total = stats.get('data', {}).get('agriculteurs', 0)
            return jsonify({"success": True, "total": total})
        else:
            return jsonify({"success": False, "error": "KPI non accessible"})
            
    except Exception as e:
        print(f"❌ [KPI] Erreur stats: {e}")
        return jsonify({"success": False, "total": 0})

@app.route("/api/sync_to_kpi", methods=["POST"])
def sync_to_kpi():
    """
    Synchroniser un prospect vers KPI
    """
    try:
        from kpi_integration import sync_agriculteur_to_kpi
        from datetime import datetime
        
        data = request.get_json()
        prospect = data.get("prospect")
        
        if not prospect:
            return jsonify({"success": False, "error": "Données manquantes"})
        
        # Ajouter date d'import
        prospect['date'] = datetime.now().strftime("%Y-%m-%d")
        
        # Synchroniser
        result = sync_agriculteur_to_kpi(prospect)
        
        if result.get('status') == 'duplicate':
            return jsonify({"success": False, "status": "duplicate", "message": "Doublon détecté"})
        elif result.get('status') == 'error':
            return jsonify({"success": False, "error": result.get('message')})
        else:
            return jsonify({"success": True, "kpi_id": result.get('id')})
            
    except Exception as e:
        import traceback
        print(f"❌ [KPI] Erreur sync: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)})

# ========== FIN INTÉGRATION KPI ==========

# ============================================================================

# Import des routes CRM avec support PostgreSQL Railway
try:
    import crm_routes
    crm_routes.register_crm_routes(app)
    print("✅ Routes CRM PostgreSQL enregistrées")
    
    # Initialiser les tables CRM PostgreSQL si on est sur Railway
    import database_adapter
    database_adapter.init_database()
    print("✅ Tables CRM PostgreSQL initialisées")
    
    # Ajouter les colonnes OSM si elles n'existent pas
    try:
        from database_adapter import execute_query
        # Vérifier et ajouter chaque colonne OSM individuellement
        osm_columns = [
            'osm_amenity', 'osm_shop', 'osm_building', 
            'osm_landuse', 'osm_office', 'osm_industrial'
        ]
        for col in osm_columns:
            try:
                execute_query(f"ALTER TABLE agriweb_prospects ADD COLUMN {col} TEXT")
                print(f"✅ Colonne {col} ajoutée")
            except Exception as col_err:
                # La colonne existe déjà ou autre erreur
                if "already exists" in str(col_err) or "duplicate column" in str(col_err):
                    print(f"ℹ️  Colonne {col} existe déjà")
                else:
                    print(f"⚠️ Erreur colonne {col}: {col_err}")
        print("✅ Migration OSM terminée")
    except Exception as e:
        print(f"⚠️ Erreur migration OSM: {e}")
except Exception as e:
    print(f"⚠️ Erreur import/init CRM: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# ROUTE ADMIN - MIGRATION MANUELLE OSM
# ============================================================================
@app.route('/admin/migrate-osm', methods=['GET'])
def admin_migrate_osm():
    """Endpoint pour exécuter la migration OSM manuellement"""
    try:
        from database_adapter import execute_query
        results = []
        
        osm_columns = [
            'osm_amenity', 'osm_shop', 'osm_building', 
            'osm_landuse', 'osm_office', 'osm_industrial'
        ]
        
        for col in osm_columns:
            try:
                execute_query(f"ALTER TABLE agriweb_prospects ADD COLUMN {col} TEXT")
                results.append(f"✅ Colonne {col} créée avec succès")
            except Exception as col_err:
                error_msg = str(col_err).lower()
                if "already exists" in error_msg or "duplicate column" in error_msg or "existe déjà" in error_msg:
                    results.append(f"ℹ️ Colonne {col} existe déjà")
                else:
                    results.append(f"❌ Erreur {col}: {str(col_err)}")
        
        # Vérifier les colonnes créées
        try:
            check_query = """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'agriweb_prospects' 
                AND column_name LIKE 'osm_%'
                ORDER BY column_name
            """
            columns = execute_query(check_query)
            results.append("\n📊 Colonnes OSM dans la base:")
            for col in columns:
                results.append(f"  • {col['column_name']} ({col['data_type']})")
        except Exception as e:
            results.append(f"⚠️ Impossible de vérifier les colonnes: {e}")
        
        return "<br>".join(results), 200
    except Exception as e:
        return f"❌ Erreur migration: {str(e)}", 500

app.config["TEMPLATES_AUTO_RELOAD"] = True

if __name__ == "__main__":
    main()  # Ceci inclut Timer + app.run()
