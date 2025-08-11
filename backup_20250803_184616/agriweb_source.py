# --- GeoRisques API: fetch risks for a point ---
import requests
def fetch_georisques_risks(lat, lon):
    """
    Appelle l'API GeoRisques pour obtenir les risques naturels et technologiques pour un point.
    Utilise tous les endpoints disponibles dans l'API v1.
    Voir doc: https://www.georisques.gouv.fr/doc-api
    """
    print(f"🔍 [GEORISQUES] === DÉBUT APPEL GEORISQUES pour point {lat}, {lon} ===")
    risques = {}
    latlon = f"{lon},{lat}"  # Format longitude,latitude pour l'API
    print(f"🔍 [GEORISQUES] Format latlon: {latlon}")
    
    # 1. Zonage sismique
    try:
        url = "https://www.georisques.gouv.fr/api/v1/zonage_sismique"
        params = {"latlon": latlon}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            risques["sismique"] = data.get("data", [])
        else:
            print(f"[GeoRisques Sismique] Erreur: {resp.status_code}")
            risques["sismique"] = []
    except Exception as e:
        print(f"[GeoRisques Sismique] Exception: {e}")
        risques["sismique"] = []
    
    # 2. TRI - Territoires à Risques importants d'Inondation (zonage réglementaire)
    try:
        url = "https://www.georisques.gouv.fr/api/v1/tri_zonage"
        params = {"latlon": latlon}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            risques["tri_zonage"] = data.get("data", [])
        elif resp.status_code == 404:
            risques["tri_zonage"] = []
        else:
            print(f"[GeoRisques TRI Zonage] Erreur: {resp.status_code}")
            risques["tri_zonage"] = []
    except Exception as e:
        print(f"[GeoRisques TRI Zonage] Exception: {e}")
        risques["tri_zonage"] = []

    # 3. TRI - Territoires à Risques importants d'Inondation (GASPAR)
    try:
        url = "https://www.georisques.gouv.fr/api/v1/gaspar/tri"
        params = {"latlon": latlon, "rayon": 1000}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            risques["tri_gaspar"] = data.get("data", [])
        else:
            print(f"[GeoRisques TRI GASPAR] Erreur: {resp.status_code}")
            risques["tri_gaspar"] = []
    except Exception as e:
        print(f"[GeoRisques TRI GASPAR] Exception: {e}")
        risques["tri_gaspar"] = []
    
    # 4. Sites et sols pollués - données complètes
    try:
        url = "https://www.georisques.gouv.fr/api/v1/ssp"
        params = {"latlon": latlon, "rayon": 1000}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # L'API retourne plusieurs types dans un seul objet
            risques["ssp_casias"] = data.get("casias", {}).get("data", [])
            risques["ssp_instructions"] = data.get("instructions", {}).get("data", [])
            risques["ssp_conclusions_sis"] = data.get("conclusions_sis", {}).get("data", [])
            risques["ssp_conclusions_sup"] = data.get("conclusions_sup", {}).get("data", [])
        else:
            print(f"[GeoRisques SSP] Erreur: {resp.status_code}")
            risques["ssp_casias"] = []
            risques["ssp_instructions"] = []
            risques["ssp_conclusions_sis"] = []
            risques["ssp_conclusions_sup"] = []
    except Exception as e:
        print(f"[GeoRisques SSP] Exception: {e}")
        risques["ssp_casias"] = []
        risques["ssp_instructions"] = []
        risques["ssp_conclusions_sis"] = []
        risques["ssp_conclusions_sup"] = []

    # 5. CASIAS - Cartes des Anciens Sites Industriels (endpoint dédié)
    try:
        url = "https://www.georisques.gouv.fr/api/v1/ssp/casias"
        params = {"latlon": latlon, "rayon": 1000}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            risques["casias_detaille"] = data.get("data", [])
        else:
            print(f"[GeoRisques CASIAS] Erreur: {resp.status_code}")
            risques["casias_detaille"] = []
    except Exception as e:
        print(f"[GeoRisques CASIAS] Exception: {e}")
        risques["casias_detaille"] = []

    # 6. TIM - Transmissions d'Informations au Maire
    try:
        url = "https://www.georisques.gouv.fr/api/v1/gaspar/tim"
        params = {"latlon": latlon, "rayon": 1000}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            risques["tim"] = data.get("data", [])
        else:
            print(f"[GeoRisques TIM] Erreur: {resp.status_code}")
            risques["tim"] = []
    except Exception as e:
        print(f"[GeoRisques TIM] Exception: {e}")
        risques["tim"] = []

    # 7. AZI - Atlas des Zones Inondables
    try:
        url = "https://www.georisques.gouv.fr/api/v1/gaspar/azi"
        params = {"latlon": latlon, "rayon": 1000}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            risques["azi"] = data.get("data", [])
        else:
            print(f"[GeoRisques AZI] Erreur: {resp.status_code}")
            risques["azi"] = []
    except Exception as e:
        print(f"[GeoRisques AZI] Exception: {e}")
        risques["azi"] = []

    # 8. CATNAT - Catastrophes naturelles
    try:
        url = "https://www.georisques.gouv.fr/api/v1/gaspar/catnat"
        params = {"latlon": latlon, "rayon": 1000}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            risques["catnat"] = data.get("data", [])
        else:
            print(f"[GeoRisques CATNAT] Erreur: {resp.status_code}")
            risques["catnat"] = []
    except Exception as e:
        print(f"[GeoRisques CATNAT] Exception: {e}")
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
            print(f"[GeoRisques Cavités] Erreur: {resp.status_code}")
            risques["cavites"] = []
    except Exception as e:
        print(f"[GeoRisques Cavités] Exception: {e}")
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
            print(f"[GeoRisques MVT] Erreur: {resp.status_code}")
            risques["mvt"] = []
    except Exception as e:
        print(f"[GeoRisques MVT] Exception: {e}")
        risques["mvt"] = []

    # 11. Retrait gonflement des argiles
    try:
        url = "https://www.georisques.gouv.fr/api/v1/argiles"
        params = {"latlon": latlon}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            risques["argiles"] = data.get("data", [])
        else:
            print(f"[GeoRisques Argiles] Erreur: {resp.status_code}")
            risques["argiles"] = []
    except Exception as e:
        print(f"[GeoRisques Argiles] Exception: {e}")
        risques["argiles"] = []

    # 12. Radon
    try:
        url = "https://www.georisques.gouv.fr/api/v1/radon"
        params = {"latlon": latlon}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            risques["radon"] = data.get("data", [])
        else:
            print(f"[GeoRisques Radon] Erreur: {resp.status_code}")
            risques["radon"] = []
    except Exception as e:
        print(f"[GeoRisques Radon] Exception: {e}")
        risques["radon"] = []

    # 13. Installations classées
    try:
        url = "https://www.georisques.gouv.fr/api/v1/installations"
        params = {"latlon": latlon, "rayon": 2000}  # Rayon plus large pour les installations
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            risques["installations"] = data.get("data", [])
        else:
            print(f"[GeoRisques Installations] Erreur: {resp.status_code}")
            risques["installations"] = []
    except Exception as e:
        print(f"[GeoRisques Installations] Exception: {e}")
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
            print(f"[GeoRisques Nucléaire] Erreur: {resp.status_code}")
            risques["nucleaire"] = []
    except Exception as e:
        print(f"[GeoRisques Nucléaire] Exception: {e}")
        risques["nucleaire"] = []

    print(f"🔍 [GEORISQUES] Risques récupérés pour {lat},{lon}: {len(risques)} catégories")
    
    # Comptons le nombre total de risques
    total_risks = 0
    for category, risks in risques.items():
        if risks and isinstance(risks, list):
            count = len(risks)
            total_risks += count
            print(f"🔍 [GEORISQUES] - {category}: {count} risque(s)")
        else:
            print(f"🔍 [GEORISQUES] - {category}: 0 risque(s)")
    
    print(f"🔍 [GEORISQUES] === TOTAL: {total_risks} risques trouvés ===")
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
    Flask, request, render_template, jsonify, send_file,
    make_response, Response, stream_with_context, redirect
)
import folium
from folium.plugins import Draw, MeasureControl, MarkerCluster, Search
from shapely.geometry import shape, mapping, Point
from shapely.ops import transform as shp_transform
from shapely.errors import GEOSException
from pyproj import Transformer
from urllib.parse import quote, quote_plus
import unicodedata, re
from threading import Timer
from datetime import datetime
import webbrowser
import os
import json
import io
import csv
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

# Add a global error handler for 500 errors to return JSON with error and traceback
from flask import jsonify
import traceback
@app.errorhandler(500)
def handle_500_error(e):
    tb = traceback.format_exc()
    return jsonify({"error": str(e), "traceback": tb}), 500


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
GEOSERVER_URL = "http://localhost:8080/geoserver"
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
GEOSERVER_WFS_URL = f"{GEOSERVER_URL}/ows"
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

def main_server():
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000")
    print("Démarrage du serveur Flask...")
    try:
        Timer(1, open_browser).start()
        app.run(host="127.0.0.1", port=5000, debug=False)  # Debug False pour éviter les reloads
    except Exception as e:
        print(f"Erreur serveur: {e}")
        import traceback
        traceback.print_exc()
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
    geolocator = Nominatim(user_agent="geoapp", timeout=10)
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None
    
def fetch_sirene_info(siret):
    try:
        url = f"https://entreprise.data.gouv.fr/api/sirene/v3/etablissements/{siret}"
        response = http_session.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[Sirene] Erreur SIRET {siret} : {e}")
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
    url = f"{GEOSERVER_URL}/wfs"
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
        print(f"[get_all_parcelles] Erreur : {e}")
        # Toujours respecter le standard GeoJSON pour éviter les plantages en aval
        return {"type": "FeatureCollection", "features": []}


def get_all_postes(lat, lon, radius_deg=0.1):
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
    return postes  # Pas de slicing ici

def get_all_ht_postes(lat, lon, radius_deg=0.5):
    bbox = f"{lon-radius_deg},{lat-radius_deg},{lon+radius_deg},{lat+radius_deg},EPSG:4326"
    features = fetch_wfs_data(HT_POSTE_LAYER, bbox)
    point = Point(lon, lat)
    postes = []
    for feature in features:
        geom = shape(feature["geometry"])
        distance = geom.distance(point) * 111000
        postes.append({
            "properties": feature["properties"],
            "distance": round(distance, 2),
            "geometry": mapping(geom)
        })
    return postes  # Pas de slicing ici])[:3]

def get_all_capacites_reseau(lat, lon, radius_deg=0.1):
    bbox = f"{lon-radius_deg},{lat-radius_deg},{lon+radius_deg},{lat+radius_deg},EPSG:4326"
    print(f"[DEBUG CAPACITES] bbox: {bbox}")
    print(f"[DEBUG CAPACITES] layer: {CAPACITES_RESEAU_LAYER}")
    
    features = fetch_wfs_data(CAPACITES_RESEAU_LAYER, bbox)
    print(f"[DEBUG CAPACITES] features brutes trouvées: {len(features) if features else 0}")
    
    if features and len(features) > 0:
        print(f"[DEBUG CAPACITES] Premier exemple: {list(features[0].get('properties', {}).keys())[:10]}")
    
    capacites = []
    point = Point(lon, lat)
    for feature in features:
        try:
            geom = shape(feature["geometry"])
            distance = geom.distance(point) * 111000
            capacites.append({
                "properties": feature["properties"],
                "distance": round(distance, 2),
                "geometry": mapping(geom)
            })
        except Exception as e:
            print(f"[DEBUG CAPACITES] Erreur traitement feature: {e}")
            continue
    
    print(f"[DEBUG CAPACITES] capacités finales: {len(capacites)}")
    return sorted(capacites, key=lambda x: x["distance"])


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
    print(f"[DEBUG RPG] BBOX: {bbox}")
    print(f"[DEBUG RPG] Layer: {PARCELLES_GRAPHIQUES_LAYER}")
    
    features = fetch_wfs_data(PARCELLES_GRAPHIQUES_LAYER, bbox)
    print(f"[DEBUG RPG] Features trouvées: {len(features) if features else 0}")
    
    if features:
        print(f"[DEBUG RPG] Première feature: {list(features[0].get('properties', {}).keys())}")
    
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

########################################
# Appels API (cadastre, nature, GPU)
########################################
def get_api_cadastre_data(geom, endpoint="/cadastre/parcelle", source_ign="PCI"):
    url = f"https://apicarto.ign.fr/api{endpoint}"
    params = {"geom": json.dumps(geom), "_limit": 1000, "source_ign": source_ign}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    print(f"Erreur API Cadastre: {response.status_code} - {response.text}")
    return None

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
                print(f"🌿 [API NATURE] {type_name}: {len(data['features'])} zones trouvées")
            else:
                print(f"🌿 [API NATURE] {type_name}: 0 zones trouvées")
        except Exception as e:
            print(f"🌿 [API NATURE] Erreur {endpoint}: {e}")
    
    if all_features:
        print(f"🌿 [API NATURE] Total: {len(all_features)} zones naturelles protégées")
        return {
            "type": "FeatureCollection",
            "features": all_features
        }
    else:
        print(f"🌿 [API NATURE] Aucune zone naturelle trouvée")
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
    url = f"{GEOSERVER_WFS_URL}?service=WFS&version=2.0.0&request=GetFeature&typeName={layer_q}&outputFormat=application/json&bbox={bbox}&srsname={srsname}"
    try:
        resp = http_session.get(url, timeout=10)
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
    return sorted(postes, key=lambda x: x["distance"])[:count]

def get_nearest_ht_postes(lat, lon, count=3, radius_deg=0.5):
    postes = get_all_ht_postes(lat, lon, radius_deg=radius_deg)
    return sorted(postes, key=lambda x: x["distance"])[:count]

def get_nearest_capacites_reseau(lat, lon, count=3, radius_deg=0.1):
    capacites = get_all_capacites_reseau(lat, lon, radius_deg=radius_deg)
    return sorted(capacites, key=lambda x: x["distance"])[:count]
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
    # Fusionne toutes les parcelles rpg
    all_rpg = []
    all_eleveurs = []
    for rpt in reports:
        fc = rpt.get("rpg_parcelles", {})
        if fc and isinstance(fc, dict):
            all_rpg.extend(fc.get("features", []))
        fc_e = rpt.get("eleveurs", {})
        if fc_e and isinstance(fc_e, dict):
            all_eleveurs.extend(fc_e.get("features", []))

    # Classement top 50 (distance au poste BT ou HTA)
    def get_dist(feat):
        # Préfère BT, sinon HTA, sinon grand nombre
        props = feat.get("properties", {})
        for key in ["distance_bt", "distance_au_poste", "distance_hta"]:
            v = props.get(key)
            if v is not None and isinstance(v, (int, float)):
                return v
        return 999999
    all_rpg_sorted = sorted(all_rpg, key=get_dist)
    top50 = all_rpg_sorted[:50]

    # Croisement avec cadastre
    top50 = enrich_rpg_with_cadastre_num(top50)

    return {
        "total_eleveurs": len(all_eleveurs),
        "total_parcelles": len(all_rpg),
        "top50_parcelles": top50
    }
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
    
    # Création de la carte
    map_obj = folium.Map(location=[lat, lon], zoom_start=16, tiles=None)
    
    # Fonds de carte
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite",
        overlay=False, control=True, show=True
    ).add_to(map_obj)
    folium.TileLayer("OpenStreetMap", name="Fond OSM", overlay=False, control=True, show=False).add_to(map_obj)
    
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
                
                popup_html = f"<b>Zone PLU</b><br>"
                popup_html += f"<b>Type:</b> {typeref}<br>"
                popup_html += f"<b>INSEE:</b> {insee}<br>"
                
                if files:
                    popup_html += f"<b>Documents:</b><br>"
                    for file in files[:5]:  # Limite à 5 documents
                        popup_html += f"- {file}<br>"
                
                if archive_url:
                    popup_html += f"<a href='{archive_url}' target='_blank'>Voir les documents PLU</a>"
                
                folium.GeoJson(
                    item.get("geometry"),
                    style_function=lambda _: {"color": "red", "weight": 2, "fillColor": "lavender", "fillOpacity": 0.4},
                    tooltip=f"Zone PLU - {typeref}",
                    popup=folium.Popup(popup_html, max_width=300)
                ).add_to(plu_group)
        
        map_obj.add_child(plu_group)
    
    # Marqueur du point de recherche
    folium.Marker(
        [lat, lon],
        popup=f"<b>Point de recherche</b><br>{address}",
        icon=folium.Icon(color="red", icon="search", prefix="fa")
    ).add_to(map_obj)
    
    # Contrôle des couches
    folium.LayerControl().add_to(map_obj)
    
    # Zoom approprié
    map_obj.fit_bounds([[lat-0.002, lon-0.002], [lat+0.002, lon+0.002]])
    
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
    ppri_data=None  # Ajout PPRI
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
    for name, data, color in [("Parkings", parkings_data, "darkgreen"), ("Friches", friches_data, "brown"), ("Potentiel Solaire", potentiel_solaire_data, "gold"), ("ZAER", zaer_data, "cyan")]:
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
                    folium.GeoJson(geom, style_function=lambda _: {"color": color, "weight": 2}, tooltip="<br>".join(f"{k}: {v}" for k, v in f.get("properties", {}).items())).add_to(group)
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
    sir_group = folium.FeatureGroup(name="Entreprises Sirene", show=True)
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
                        popup=folium.Popup(popup_html, max_width=400)
                    ).add_to(group)
                except Exception as e:
                    print(f"[ERROR] Exception while adding GPU geometry for {ep}: {e}\nGeom: {geom}")
            else:
                print(f"[DEBUG] Invalid GPU geometry for {ep}: type={geom.get('type') if geom else None}, coords={geom.get('coordinates') if geom else None}")

        map_obj.add_child(group)

    
    # Éleveurs
# Remplacez la section éleveurs dans build_map (lignes 1728-1770 environ) par :

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
            
            # CORRECTION: Définir ville_url et nom_url
            ville_url = (props.get("libelleCom", "") or "").replace(" ", "+")
            nom_url = (nom + " " + denomination).strip().replace(" ", "+")
            
            eleveur_props = {
                "nom": nom,
                "prenom": prenom,
                "denomination": denomination,
                "activite": props.get("activite_1", ""),
                "adresse": adresse,
                "telephone": props.get("telephone", ""),
                "email": props.get("email", ""),
                "site_web": props.get("site_web", ""),
                "lien_annuaire": f"https://www.pagesjaunes.fr/recherche/{ville_url}/{nom_url}" if nom else "",
                "lien_entreprise": f"https://annuaire-entreprises.data.gouv.fr/etablissement/{siret}" if siret else "",
                "lien_pages_blanches": f"https://www.pagesjaunes.fr/pagesblanches/recherche?quoiqui={nom}+{prenom}&ou={props.get('libelleCom','')}"
            }
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
    })();
    </script>
    """
    map_obj.get_root().html.add_child(Element(helper_js))

    map_obj.fit_bounds(bounds)
    if not mode_light:
        folium.Marker([lat, lon], popup="Test marker").add_to(map_obj)
    # Ajout d'un paramètre save_to_disk (par défaut True)
    if getattr(map_obj, '_no_save', False):
        print("💡 Carte non sauvegardée sur disque (mode _no_save)")
    else:
        save_map_html(map_obj, "cartes.html")
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

def save_map_to_cache(map_obj):
    # Réactivation du cache mémoire : on stocke le HTML de la carte générée
    last_map_params["html"] = map_obj._repr_html_()
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
    """
    html = last_map_params.get("html")

    # --- Cas : aucune recherche encore faite ---
    if not html:
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

    # --- On renvoie toujours un objet Response ---
    resp = make_response(html)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp
from flask import Flask, Response


from flask import url_for, redirect

@app.route("/search_by_commune", methods=["GET", "POST"])
def search_by_commune():
    # 1) Paramètres
    commune = request.values.get("commune", "").strip()
    culture = request.values.get("culture", "")
    ht_max_km = float(request.values.get("ht_max_distance", 1.0))
    bt_max_km = float(request.values.get("bt_max_distance", 1.0))
    sir_km    = float(request.values.get("sirene_radius", 0.05))
    min_ha    = float(request.values.get("min_area_ha", 0))
    max_ha    = float(request.values.get("max_area_ha", 1e9))

    if not commune:
        return jsonify({"error": "Veuillez fournir une commune."}), 400

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
    from shapely.geometry import shape
    commune_poly = shape(contour)
    minx, miny, maxx, maxy = commune_poly.bounds
    bbox = f"{minx},{miny},{maxx},{maxy},EPSG:4326"

    # 4) Récupère toutes les features dans le bbox puis filtre par intersection avec le polygone
    def filter_in_commune(features):
        return [
            f for f in features
            if "geometry" in f and shape(f["geometry"]).intersects(commune_poly)
        ]

    parcelles_data   = get_all_parcelles(lat, lon, radius=0.1)  # ou adapte si besoin
    rpg_raw          = filter_in_commune(get_rpg_info(lat, lon, radius=0.1))
    postes_bt_data   = filter_in_commune(fetch_wfs_data(POSTE_LAYER, bbox))
    postes_hta_data  = filter_in_commune(fetch_wfs_data(HT_POSTE_LAYER, bbox))
    eleveurs_data    = filter_in_commune(fetch_wfs_data(ELEVEURS_LAYER, bbox, srsname="EPSG:4326"))
    plu_info         = filter_in_commune(get_plu_info(lat, lon, radius=0.1))
    zaer_data        = filter_in_commune(get_zaer_info(lat, lon, radius=0.1))
    parkings_data    = filter_in_commune(get_parkings_info(lat, lon, radius=0.1))
    friches_data     = filter_in_commune(get_friches_info(lat, lon, radius=0.1))
    solaire_data     = filter_in_commune(get_potentiel_solaire_info(lat, lon, radius=0.1))
    sirene_data      = filter_in_commune(get_sirene_info(lat, lon, radius=sir_km / 111.0))

    point          = {"type": "Point", "coordinates": [lon, lat]}
    api_cadastre   = get_api_cadastre_data(geom)
    api_nature     = get_all_api_nature_data(geom)
    api_urbanisme  = get_all_gpu_data(geom)

    # 5) Filtrage RPG (culture, surface, distances)
    from shapely.ops import transform as shp_transform
    from pyproj import Transformer
    to_l93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True).transform

    final_rpg = []
    for feat in (rpg_raw or []):
        dec   = decode_rpg_feature(feat)
        poly  = shape(dec["geometry"])
        props = dec["properties"]

        # a) culture
        if culture and culture.lower() not in props.get("Culture", "").lower():
            continue

        # b) surface (ha)
        ha = shp_transform(to_l93, poly).area / 10_000.0
        if ha < min_ha or ha > max_ha:
            continue

        # c) distances réseaux (m) : on cherche le **minimum** dans CHAQUE liste
        cent   = poly.centroid.coords[0]
        d_bt   = calculate_min_distance(cent, postes_bt_data)
        d_hta  = calculate_min_distance(cent, postes_hta_data)

        if ((d_bt  or 1e12) / 1000.0) > bt_max_km \
        and ((d_hta or 1e12) / 1000.0) > ht_max_km:
            continue

        props.update({
            "SURF_HA":            round(ha, 3),
            "min_bt_distance_m":  round(d_bt,  2) if d_bt  is not None else None,
            "min_ht_distance_m":  round(d_hta, 2) if d_hta is not None else None,
        })
        final_rpg.append({
            "type":       "Feature",
            "geometry":   dec["geometry"],
            "properties": props
        })

    # 6) Carte interactive
    # PPRI récupération via la nouvelle fonction GeoRisques unifiée
    import requests
    def fetch_ppri_georisques(lat, lon, rayon_km=1.0):
        # Utilise maintenant la nouvelle fonction unifiée
        print(f"🔍 [PPRI] Utilisation des données GeoRisques unifiées")
        return {"type": "FeatureCollection", "features": []}

    # On ne garde que les polygones qui contiennent le point exact
    from shapely.geometry import shape, Point
    raw_ppri = fetch_ppri_georisques(lat, lon, rayon_km=1.0)
    pt = Point(lon, lat)
    filtered_features = [f for f in raw_ppri.get("features", []) if f.get("geometry") and shape(f["geometry"]).contains(pt)]
    ppri_data = {"type": "FeatureCollection", "features": filtered_features}
    map_obj = build_map(
        lat, lon, commune,
        parcelle_props={}, parcelles_data=parcelles_data,
        postes_data=postes_bt_data,
        ht_postes_data=postes_hta_data,
        plu_info=plu_info,
        parkings_data=parkings_data,
        friches_data=friches_data,
        potentiel_solaire_data=solaire_data,
        zaer_data=zaer_data,
        rpg_data=final_rpg,
        sirene_data=sirene_data,
        search_radius=0.1,
        ht_radius_deg=ht_max_km/111.0,
        api_cadastre=api_cadastre,
        api_nature=api_nature,
        api_urbanisme=api_urbanisme,
        eleveurs_data=eleveurs_data,
        ppri_data=ppri_data
    )
    save_map_to_cache(map_obj)

    # 7) Réponse JSON
    return jsonify({
        "lat": lat, "lon": lon,
        "rpg": final_rpg,
        "eleveurs": eleveurs_data,
        "postes_bt": postes_bt_data,
        "postes_hta": postes_hta_data,
        "parcelles": parcelles_data,
        "api_cadastre": api_cadastre,
        "api_nature": api_nature,
        "api_urbanisme": api_urbanisme,
        "plu": plu_info,
        "parkings": parkings_data,
        "friches": friches_data,
        "solaire": solaire_data,
        "zaer": zaer_data,
        "sirene": sirene_data
    })
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
        
        if not lat or not lon:
            log_step("VALIDATION", "Coordonnées manquantes", "ERROR")
            return jsonify({"error": "Coordonnées lat/lon manquantes"}), 400
        
        lat_float = float(lat)
        lon_float = float(lon)
        
        log_step("VALIDATION", f"Coordonnées validées: {lat_float}, {lon_float}", "SUCCESS")
        
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
    import requests
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report_data = {
        "lat": lat_float,
        "lon": lon_float,
        "address": address,
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
                print(f"🔍 [DEBUG HTA] Capacités HTA enrichies pour le rapport:")
                for i, cap in enumerate(hta_enriched[:3]):  # Afficher les 3 premières
                    print(f"🔍 [DEBUG HTA] Capacité {i+1}: {cap.get('Nom', 'N/A')} - Distance: {cap.get('distance', 'N/A')}m")
                    print(f"🔍 [DEBUG HTA] - Capacité: {cap.get('Capacité', 'N/A')} - S3REnR: {cap.get('S3REnR', 'N/A')}")
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
                print(f"🔍 [DEBUG RAPPORT] Coordonnées pour API Nature: lat={lat_float}, lon={lon_float}")
                
                # Créer une géométrie point pour l'API Nature - CORRECTION: utiliser float au lieu de string
                geom = {"type": "Point", "coordinates": [lon_float, lat_float]}
                print(f"🔍 [DEBUG RAPPORT] Géométrie API Nature: {geom}")
                
                nature_data = get_all_api_nature_data(geom)
                print(f"🔍 [DEBUG RAPPORT] Résultat get_all_api_nature_data: {type(nature_data)}")
                
                if nature_data and "features" in nature_data and nature_data["features"]:
                    print(f"🔍 [DEBUG RAPPORT] API Nature SUCCESS: {len(nature_data['features'])} features trouvées")
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
            
            carte_filename = f"rapport_point_{timestamp}.html"
            carte_path = os.path.join(app.root_path, "static", "cartes")
            os.makedirs(carte_path, exist_ok=True)
            
            carte_fullpath = os.path.join(carte_path, carte_filename)
            map_obj.save(carte_fullpath)
            
            report_data["carte_url"] = f"/static/cartes/{carte_filename}"
            save_map_to_cache(map_obj)
            
            log_step("CARTE", f"✅ Carte sauvée: {carte_fullpath}", "SUCCESS")
            return map_obj
        except Exception as e:
            log_step("CARTE", f"❌ Erreur génération carte: {e}", "ERROR")
            return None

    # === EXÉCUTION PRINCIPALE ===
    try:
        # 1. Collecte au point exact
        log_step("EXEC", "🚀 Début exécution - Collecte au point exact")
        point_data = collect_data_at_point()
        
        # 2. Intégration dans le rapport
        log_step("EXEC", "🚀 Intégration des données du point exact")
        integrate_point_data_to_report(point_data)
        
        # 3. CRUCIAL : Collecte données contextuelles (altitude, PVGIS, APIs)
        log_step("EXEC", "🚀 Collecte des données contextuelles")
        collect_context_data()
        
        # 4. Génération carte
        log_step("EXEC", "🚀 Génération de la carte")
        map_obj = generate_map()
        # Toujours fournir une carte, même si la génération échoue
        if not report_data.get("carte_url"):
            # Fallback: carte par défaut si la génération a échoué
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
        log_step("SUMMARY", f"🏔️ Altitude: {report_data['altitude']}m")
        log_step("SUMMARY", f"☀️ Production PV: {report_data['kwh_per_kwc']} kWh/kWc/an")
        log_step("SUMMARY", f"🗺️ Commune: {report_data['commune_name']}")
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
    sirene_km: float = 5.0,
    want_eleveurs: bool = False,
    reseau_types: list = ["HTA", "BT"]
) -> dict:
    # 1) Géocodage de la commune
    coords = geocode_address(commune_name)
    if not coords:
        return {}

    lat, lon = coords
    point_geojson = {"type": "Point", "coordinates": [lon, lat]}
    r_deg = 5.0 / 111.0

    # 2) Chargement des données brutes
    raw_rpg     = get_rpg_info(lat, lon, radius=r_deg) or []
    postes_bt   = get_all_postes(lat, lon, radius_deg=r_deg) if "BT" in reseau_types else []
    postes_hta  = get_all_ht_postes(lat, lon, radius_deg=r_deg) if "HTA" in reseau_types else []
    parcelles   = get_all_parcelles(lat, lon, radius=sirene_km/111.0)

    # 3) Parcelles RPG filtrées
    proj_metric = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True).transform
    rpg_features = []
    for feat in raw_rpg:
        dec   = decode_rpg_feature(feat)
        poly  = shape(dec["geometry"])
        props = dec["properties"]

        if culture and culture.lower() not in props.get("Culture", "").lower():
            continue
        ha = shp_transform(proj_metric, poly).area / 10_000.0
        if ha < min_area_ha or ha > max_area_ha:
            continue
        cent = poly.centroid.coords[0]

        # Distance aux réseaux
        d_bt  = calculate_min_distance(cent, postes_bt) if "BT" in reseau_types else None
        d_hta = calculate_min_distance(cent, postes_hta) if "HTA" in reseau_types else None

        # Filtrage selon le(s) type(s) de réseau sélectionné(s)
        ok = False
        if "BT" in reseau_types and "HTA" not in reseau_types:
            if d_bt is not None and d_bt <= bt_max_km * 1000:
                ok = True
        elif "HTA" in reseau_types and "BT" not in reseau_types:
            if d_hta is not None and d_hta <= ht_max_km * 1000:
                ok = True
        elif "BT" in reseau_types and "HTA" in reseau_types:
            if (d_bt is not None and d_bt <= bt_max_km * 1000) or (d_hta is not None and d_hta <= ht_max_km * 1000):
                ok = True
        if not reseau_types or not ok:
            continue

        # Croisement API Cadastre
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
            numero  = cad.get("numero", "")
            nom_commune = cad.get("nom_com", "") or cad.get("nom_commune", commune_name)
        else:
            code_com = ""
            com_abs = "000"
            section = ""
            numero = ""
            nom_commune = commune_name

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
        })
        rpg_features.append({
            "type": "Feature",
            "geometry": mapping(poly),
            "properties": props
        })
    rpg_fc = {"type": "FeatureCollection", "features": rpg_features}

    # 4) Postes BT/HTA en FeatureCollection si demandés
    def poste_to_feature(poste):
        return {
            "type": "Feature",
            "geometry": poste.get("geometry"),
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
            if commune_infos and commune_infos[0].get("centre"):
                info = commune_infos[0]
                result["insee"] = info.get("code", "")
                result["surface"] = round(info.get("surface", 0) / 100, 2)
                result["population"] = info.get("population", "")
                result["centroid"] = [info["centre"]["coordinates"][1], info["centre"]["coordinates"][0]]
            else:
                result["insee"] = ""
                result["surface"] = ""
                result["population"] = ""
                result["centroid"] = [lat, lon]
        else:
            result["insee"] = ""
            result["surface"] = ""
            result["population"] = ""
            result["centroid"] = [lat, lon]
    except Exception:
        result["insee"] = ""
        result["surface"] = ""
        result["population"] = ""
        result["centroid"] = [lat, lon]

    # Ajout mairie
    result["mairie"] = get_commune_mairie(commune_name)

    # Ajoute les couches réseau SEULEMENT si demandées
    if "BT" in reseau_types:
        result["postes_bt"] = {
            "type": "FeatureCollection",
            "features": [poste_to_feature(p) for p in postes_bt if p.get("geometry")]
        }
    if "HTA" in reseau_types:
        result["postes_hta"] = {
            "type": "FeatureCollection",
            "features": [poste_to_feature(p) for p in postes_hta if p.get("geometry")]
        }

    # 5) Éleveurs (toujours présent, mais filtré par want_eleveurs)
    eleveurs_fc = {"type": "FeatureCollection", "features": []}
    if want_eleveurs:
        bbox = f"{lon-0.05},{lat-0.05},{lon+0.05},{lat+0.05},EPSG:4326"
        for e in fetch_wfs_data(ELEVEURS_LAYER, bbox, srsname="EPSG:4326") or []:
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
                "nom": nom,
                "prenom": prenom,
                "denomination": denomination,
                "activite": activite,
                "adresse": adresse,
                "lien_annuaire": f"https://www.pagesjaunes.fr/recherche/{ville_url}/{nom_url}" if nom else "",
                "lien_entreprise": f"https://annuaire-entreprises.data.gouv.fr/etablissement/{siret}" if siret else "",
                "lien_pages_blanches": f"https://www.pagesjaunes.fr/pagesblanches/recherche?quoiqui={nom}+{prenom}&ou={props.get('libelleCom','')}"
            }
            eleveurs_fc["features"].append({
                "type": "Feature",
                "geometry": geom,
                "properties": eleveur_props
            })
    result["eleveurs"] = eleveurs_fc

    # 6) Capacités réseau HTA via WFS
    try:
        folium.GeoJson(result["hta_capacites"], name="Capacités HTA").add_to(m)
        bbox = f"{lon-0.05},{lat-0.05},{lon+0.05},{lat+0.05},EPSG:4326"
        capa_fc = fetch_wfs_data(CAPACITES_RESEAU_LAYER, bbox, srsname="EPSG:4326")
        result["hta_capacites"] = capa_fc or {"type": "FeatureCollection", "features": []}
    except Exception:
        result["hta_capacites"] = {"type": "FeatureCollection", "features": []}

    # 7) RPG
    result["rpg_parcelles"] = rpg_fc

    # 8) Génération de la carte Folium (à la toute fin de compute_commune_report)

    import folium

    # Point central pour centrer la carte
    lat_centre, lon_centre = result["centroid"]

    m = folium.Map(location=[lat_centre, lon_centre], zoom_start=12, tiles="OpenStreetMap")

    # Ajoute les couches principales
    folium.GeoJson(result["rpg_parcelles"], name="RPG Parcelles").add_to(m)

    if "postes_bt" in result:
        folium.GeoJson(result["postes_bt"], name="Postes BT").add_to(m)
    if "postes_hta" in result:
        folium.GeoJson(result["postes_hta"], name="Postes HTA").add_to(m)
    if "hta_capacites" in result:
        folium.GeoJson(result["hta_capacites"], name="Capacités HTA").add_to(m)
    if result["eleveurs"]["features"]:
        folium.GeoJson(result["eleveurs"], name="Éleveurs").add_to(m)

    folium.LayerControl().add_to(m)

    # Enregistre la carte dans static/cartes/
    from datetime import datetime
      # adapte selon ton import réel

    carte_filename = f"carte_{commune_name.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    carte_path = save_map_html(m, carte_filename)
    result["carte_path"] = carte_path    # <--- Ajoute ce chemin au résultat
    return result
    

@app.route("/generate_reports_by_dept_sse")
def generate_reports_by_dept_sse():
    def event_stream():
        department = request.args.get("department")
        if not department:
            yield "event: error\ndata: " + json.dumps({"error": "Paramètre 'department' manquant"}) + "\n\n"
            return

        # Lecture des paramètres
        culture     = request.args.get("culture", "")
        min_area    = float(request.args.get("min_area_ha", 0))
        max_area    = float(request.args.get("max_area_ha", 99999))
        ht_max_km   = float(request.args.get("ht_max_distance", 10))
        bt_max_km   = float(request.args.get("bt_max_distance", 10))
        sirene_km   = float(request.args.get("sirene_radius", 5))
        want_elev   = request.args.get("want_eleveurs", "false").lower() == "true"
        # Nouveau : lecture de la liste des types de réseau
        reseau_types_str = request.args.get("reseau_types", "HTA,BT")
        reseau_types = [t.strip().upper() for t in reseau_types_str.split(",") if t.strip()]

        communes = get_communes_for_dept(department)
        total = len(communes)

        # CUMULATEURS pour toutes les couches (FeatureCollection pour chaques)
        def fc_init(): return {"type": "FeatureCollection", "features": []}
        all_rpg = fc_init()
        all_postes_bt = fc_init()
        all_postes_hta = fc_init()
        all_eleveurs = fc_init()


        for idx, feat in enumerate(communes, start=1):
            nom = feat["properties"]["nom"]
            rpt = compute_commune_report(
                commune_name=nom,
                culture=culture,
                min_area_ha=min_area,
                max_area_ha=max_area,
                ht_max_km=ht_max_km,
                bt_max_km=bt_max_km,
                sirene_km=sirene_km,
                want_eleveurs=want_elev,
                reseau_types=reseau_types   # <-- Le nouveau paramètre
            )
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

            yield f"event: progress\ndata: [{idx}/{total}] {nom}\n\n"
            yield f"event: result\ndata: {json.dumps(rpt, ensure_ascii=False)}\n\n"

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
            min_area_ha=float(request.args.get("min_area_ha", 0)),
            max_area_ha=float(request.args.get("max_area_ha", 1e9)),
            ht_max_km=float(request.args.get("ht_max_distance", 5.0)),
            bt_max_km=float(request.args.get("bt_max_distance", 5.0)),
            sirene_km=float(request.args.get("sirene_radius", 5.0)),
            want_eleveurs=True
        )
        # Filtrage pour ne garder que les infos voulues (optionnel, mais utile pour ne pas surcharger la mémoire)
        # Ajoute tout ce que tu veux afficher dans le rapport
        all_reports.append({
            "commune": nom,
            "agriculteurs": rpt.get("eleveurs", []),
            "parcelles": rpt.get("rpg_parcelles", []),
            # Ajoute ici d'autres éléments si besoin (postes, distances, etc)
        })

    return render_template("rapport_departement.html", dept=dept, reports=all_reports)


@app.route("/rapport_commune")
def rapport_commune():
    commune = request.args.get("commune")
    if not commune:
        return "Commune requise", 400

    # Utilise la fonction générique déjà définie
    report = compute_commune_report(
        commune_name=commune,
        culture=request.args.get("culture", ""),
        min_area_ha=float(request.args.get("min_area_ha", 0)),
        max_area_ha=float(request.args.get("max_area_ha", 1e9)),
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
        folium.GeoJson(
            report["rpg_parcelles"],
            name="Parcelles RPG",
            tooltip=folium.GeoJsonTooltip(fields=[
                "cadastre_section", "cadastre_numero", "surface", "Culture"
            ])
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

    # Sauvegarde et URL de la carte
    carte_path = save_map_html(m, f"carte_{commune}.html")
    carte_url = "/" + carte_path if carte_path.startswith("static/") else carte_path

    # Passage au template (n'oublie pas carte_url dans rapport_commune.html)
    return render_template("rapport_commune.html", report=report, carte_url=carte_url)



@app.route("/", methods=["GET", "POST"])
def index():
    # Valeurs par défaut pour la carte d'accueil (France centre)
    lat, lon = 46.603354, 1.888334
    address = None
    parcelle_props = {}
    parcelles_data = {}
    postes_data = []
    ht_postes_data = []
    plu_info = []
    parkings_data = []
    friches_data = []
    potentiel_solaire_data = []
    zaer_data = []
    rpg_data = []
    sirene_data = []
    search_radius = 0.03
    coords = None
    ht_radius_km = 1.0
    bt_radius_km = 1.0
    sirene_radius_km = 0.05

    # Définir une zone de polygone de 5 km autour du centre par défaut
    radius_km = 5.0
    delta = radius_km / 111.0
    poly = bbox_to_polygon(lon, lat, delta)
    geom_point = {"type": "Point", "coordinates": [lon, lat]}

    # -- Par défaut : on charge déjà le contexte autour du point central
    api_cadastre = get_api_cadastre_data(poly)
    api_nature   = get_api_nature_data(poly)
    api_urbanisme= get_all_gpu_data(poly)

    if request.method == "POST":
        address = request.form.get("address")
        sr = request.form.get("sirene_radius")
        if sr:
            try:
                sirene_radius_km = float(sr)
            except ValueError:
                sirene_radius_km = 0.05

        ht_radius_input = request.form.get("ht_radius")
        bt_radius_input = request.form.get("bt_radius")
        if ht_radius_input:
            try:
                ht_radius_km = float(ht_radius_input)
            except ValueError:
                ht_radius_km = 1.0
        if bt_radius_input:
            try:
                bt_radius_km = float(bt_radius_input)
            except ValueError:
                bt_radius_km = 1.0

        # Géocodification de l'adresse
        coords = geocode_address(address)
        if coords:
            lat, lon = coords
            parcelle = get_parcelle_info(lat, lon)
            if not parcelle:
                all_parcelles = get_all_parcelles(lat, lon, radius=search_radius)
                if all_parcelles.get("features"):
                    parcelle = all_parcelles["features"][0]["properties"]
            if parcelle:
                parcelle_props = parcelle

            bt_radius_deg = bt_radius_km / 111
            ht_radius_deg = ht_radius_km / 111

            postes_data = get_nearest_postes(lat, lon, radius_deg=bt_radius_deg)
            ht_postes_data = get_nearest_ht_postes(lat, lon, radius_deg=ht_radius_deg)
            plu_info = get_plu_info(lat, lon, radius=search_radius)
            parkings_data = get_parkings_info(lat, lon, radius=search_radius)
            friches_data = get_friches_info(lat, lon, radius=search_radius)
            potentiel_solaire_data = get_potentiel_solaire_info(lat, lon)
            zaer_data = get_zaer_info(lat, lon, radius=search_radius)
            rpg_data = get_rpg_info(lat, lon, radius=0.0027)
            sirene_radius_deg = sirene_radius_km / 111
            sirene_data = get_sirene_info(lat, lon, radius=sirene_radius_deg)

            # -- PATCH: On recalcule le polygone centré sur la nouvelle recherche
            poly = bbox_to_polygon(lon, lat, delta)
            geom_point = {"type": "Point", "coordinates": [lon, lat]}

            api_cadastre = get_api_cadastre_data(poly)
            api_nature   = get_api_nature_data(poly)
            api_urbanisme= get_all_gpu_data(poly)
        else:
            api_cadastre = None
            api_nature = None
            api_urbanisme = None

    info_response = {
        "lat": lat,
        "lon": lon,
        "address": address,
        "parcelle": parcelle_props,
        "plu": get_plu_info(lat, lon, radius=search_radius),
        "sirene_radius_km": sirene_radius_km,
        "hta": [],
        "bt": [],
        "rpg": [],
        "zaer": [],
        "ht_radius_km": ht_radius_km,
        "bt_radius_km": bt_radius_km,
        "api_cadastre": api_cadastre,
        "api_nature": api_nature,
        "api_urbanisme": api_urbanisme
    }

    # -- On passe le contexte complet au template
    return render_template(
        "index.html",
        address=address,
        parcelle=parcelle_props,
        postes=postes_data,
        ht_postes=ht_postes_data,
        plu=info_response["plu"],
        parcelles_data={},  # Non utilisé ici, mais conservé pour compat
        lat=lat,
        lon=lon,
        rpg_data=rpg_data,
        sirene_data=sirene_data,
        info=info_response,
        parkings_data=get_parkings_info(lat, lon, radius=search_radius),
        culture_options=sorted(set(rpg_culture_mapping.values()))
    )

@app.route("/search_by_address", methods=["GET", "POST"])
def search_by_address_route():
    # Debug prints moved after parcelle assignment to avoid UnboundLocalError
    # Utility to ensure a list of valid GeoJSON Feature dicts
    def ensure_feature_list(features):
        if not features:
            return []
        if isinstance(features, dict) and features.get("type") == "FeatureCollection":
            features = features.get("features", [])
        if isinstance(features, list):
            return [f for f in features if isinstance(f, dict) and "geometry" in f and "properties" in f]
        return []
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
        coords = geocode_address(address)
        if not coords:
            return jsonify({"error": "Adresse non trouvée."}), 404
        lat, lon = coords
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
    parcelles_data = get_all_parcelles(lat, lon, radius=search_radius)

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
    postes_bt_raw = ensure_feature_list(get_nearest_postes(lat, lon, count=1, radius_deg=bt_radius_deg))
    postes_hta_raw = ensure_feature_list(get_nearest_ht_postes(lat, lon, count=1, radius_deg=ht_radius_deg))
    capacites_reseau_raw = ensure_feature_list(get_nearest_capacites_reseau(lat, lon, count=1, radius_deg=ht_radius_deg))
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
    api_cadastre = get_api_cadastre_data(geom_point)
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
    print("[DEBUG build_map args] parcelle:", type(parcelle or {}), (parcelle or {}) if isinstance(parcelle or {}, dict) else str(parcelle or {})[:200])
    print("[DEBUG build_map args] parcelles_data:", type(parcelles_data), ensure_feature_list(parcelles_data)[:1])
    print("[DEBUG build_map args] postes_bt:", type(postes_bt), ensure_feature_list(postes_bt)[:1])
    print("[DEBUG build_map args] postes_hta:", type(postes_hta), ensure_feature_list(postes_hta)[:1])
    print("[DEBUG build_map args] plu_info:", type(plu_info), ensure_feature_list(plu_info)[:1])
    print("[DEBUG build_map args] parkings:", type(parkings), ensure_feature_list(parkings)[:1])
    print("[DEBUG build_map args] friches:", type(friches), ensure_feature_list(friches)[:1])
    print("[DEBUG build_map args] solaire:", type(solaire), ensure_feature_list(solaire)[:1])
    print("[DEBUG build_map args] zaer:", type(zaer), ensure_feature_list(zaer)[:1])
    print("[DEBUG build_map args] rpg_data:", type(rpg_data), ensure_feature_list(rpg_data)[:1])
    print("[DEBUG build_map args] sirene_data:", type(sirene_data), ensure_feature_list(sirene_data)[:1])
    print("[DEBUG build_map args] capacites_reseau:", type(capacites_reseau), ensure_feature_list(capacites_reseau)[:1])

    # 8. GeoRisques: fetch risks for this point
    georisques_risks = fetch_georisques_risks(lat, lon)

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
        section = first_cadastre.get("section", "")
        numero = first_cadastre.get("numero", "")
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

    # 10. Diagnostics
    print("[DIAG build_map] lat:", lat, type(lat))
    print("[DIAG build_map] lon:", lon, type(lon))
    print("[DIAG build_map] address:", address, type(address))
    print("[DIAG build_map] parcelle:", type(parcelle), repr(parcelle)[:200])
    print("[DIAG build_map] parcelles_data:", type(parcelles_data), repr(parcelles_data)[:200])
    print("[DIAG build_map] postes_bt_raw:", type(postes_bt_raw), repr(postes_bt_raw)[:200])
    print("[DIAG build_map] postes_hta_raw:", type(postes_hta_raw), repr(postes_hta_raw)[:200])
    print("[DIAG build_map] plu_info:", type(plu_info), repr(plu_info)[:200])
    print("[DIAG build_map] parkings:", type(parkings), repr(parkings)[:200])
    print("[DIAG build_map] friches:", type(friches), repr(friches)[:200])
    print("[DIAG build_map] solaire:", type(solaire), repr(solaire)[:200])
    print("[DIAG build_map] zaer:", type(zaer), repr(zaer)[:200])
    print("[DIAG build_map] rpg_data:", type(rpg_data), repr(rpg_data)[:200])
    print("[DIAG build_map] sirene_data:", type(sirene_data), repr(sirene_data)[:200])
    print("[DIAG build_map] search_radius:", search_radius, type(search_radius))
    print("[DIAG build_map] ht_radius_deg:", ht_radius_deg, type(ht_radius_deg))
    print("[DIAG build_map] api_cadastre:", type(api_cadastre), repr(api_cadastre)[:200])
    print("[DIAG build_map] api_nature:", type(api_nature), repr(api_nature)[:200])
    print("[DIAG build_map] api_urbanisme:", type(api_urbanisme), repr(api_urbanisme)[:200])
    print("[DIAG build_map] eleveurs_data:", type(None))

    # 11. Carte Folium complète avec tous les calques métiers
    carte_url = None
    try:
        # Debug: print types and samples of all build_map arguments (after parcelle assignment)
        print("[DEBUG build_map args] parcelle:", type(parcelle or {}), (parcelle or {}) if isinstance(parcelle or {}, dict) else str(parcelle or {})[:200])
        print("[DEBUG build_map args] parcelles_data:", type(parcelles_data), ensure_feature_list(parcelles_data)[:1])
        print("[DEBUG build_map args] postes_bt:", type(postes_bt), ensure_feature_list(postes_bt)[:1])
        print("[DEBUG build_map args] postes_hta:", type(postes_hta), ensure_feature_list(postes_hta)[:1])
        print("[DEBUG build_map args] plu_info:", type(plu_info), ensure_feature_list(plu_info)[:1])
        print("[DEBUG build_map args] parkings:", type(parkings), ensure_feature_list(parkings)[:1])
        print("[DEBUG build_map args] friches:", type(friches), ensure_feature_list(friches)[:1])
        print("[DEBUG build_map args] solaire:", type(solaire), ensure_feature_list(solaire)[:1])
        print("[DEBUG build_map args] zaer:", type(zaer), ensure_feature_list(zaer)[:1])
        print("[DEBUG build_map args] rpg_data:", type(rpg_data), ensure_feature_list(rpg_data)[:1])
        print("[DEBUG build_map args] sirene_data:", type(sirene_data), ensure_feature_list(sirene_data)[:1])
        print("[DEBUG build_map args] capacites_reseau:", type(capacites_reseau), ensure_feature_list(capacites_reseau)[:1])
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
            capacites_reseau=ensure_feature_list(capacites_reseau)
        )
        carte_filename = f"map_{int(time.time())}_{abs(hash((lat, lon, address)))}.html"
        carte_url = save_map_html(map_obj, carte_filename)
        save_map_to_cache(map_obj)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("[search_by_address] Erreur build_map :", e)
        logging.error(f"[search_by_address] Erreur build_map: {e}\nTraceback:\n{tb}")
        return jsonify({"error": f"Erreur build_map: {e}", "traceback": tb}), 500

    info_response["carte_url"] = f"/static/{carte_url}" if carte_url else "/map.html"
    return jsonify(info_response)


@app.route('/rapport_departement_post', methods=['POST'])
def rapport_departement_post():
    import time

    data = request.get_json()
    reports = data.get("data", [])
    dept = None
    for rpt in reports:
        if "dept" in rpt and rpt["dept"]:
            dept = rpt["dept"]
            break
    if not dept:
        dept = None


    # 1. Fusionne tous les RPG et agriculteurs pour la synthèse
    all_rpg = []
    all_eleveurs = []
    for rpt in reports:
        fc_rpg = rpt.get("rpg_parcelles", {})
        if fc_rpg and isinstance(fc_rpg, dict):
            all_rpg.extend(fc_rpg.get("features", []))
        fc_e = rpt.get("eleveurs", {})
        if fc_e and isinstance(fc_e, dict):
            all_eleveurs.extend(fc_e.get("features", []))

    # --- Fonctions locales ---
    def get_dist(feat):
        props = feat.get("properties", {})
        for key in ["distance_bt", "distance_au_poste", "distance_hta", "min_bt_distance_m", "min_ht_distance_m"]:
            v = props.get(key)
            if v is not None and isinstance(v, (int, float)):
                return v
        return 999999

    def unique_parcelles(features):
        """Supprime les doublons sur ID parcelle + section + numero + commune"""
        seen = set()
        unique = []
        for p in features:
            props = p.get("properties", {})
            key = (
                props.get("ID_PARCEL") or props.get("id"),
                props.get("section") or props.get("cadastre_section"),
                props.get("numero") or props.get("cadastre_numero"),
                props.get("code_com"),
                props.get("com_abs"),
            )
            if key not in seen:
                seen.add(key)
                unique.append(p)
        return unique

    # 2. Trie, dédoublonnage et TOP 50
    all_rpg_sorted = sorted(all_rpg, key=get_dist)
    top50_unique = unique_parcelles(all_rpg_sorted)
    top50 = top50_unique[:50]

    # 3. Ajoute le numéro de parcelle Cadastre API (avec respect du rate-limit)
    def enrich_rpg_with_cadastre_num(rpg_features, delay=0.3):
        enriched = []
        for feat in rpg_features:
            geom = feat.get("geometry")
            props = feat.get("properties", {})
            try:
                api_resp = get_api_cadastre_data(geom)
                num_parcelle = None
                if api_resp and "features" in api_resp and len(api_resp["features"]) > 0:
                    num_parcelle = api_resp["features"][0]["properties"].get("numero", None)
                props["numero_parcelle"] = num_parcelle or "N/A"
            except Exception:
                props["numero_parcelle"] = "N/A"
    for rpt in reports:
        if "dept" in rpt and rpt["dept"]:
            pass  # TODO: implement logic or remove if not needed
    if not dept:
        dept = None

    # 1. Fusionne tous les RPG et agriculteurs pour la synthèse
    all_rpg = []
    all_eleveurs = []
    for rpt in reports:
        fc_rpg = rpt.get("rpg_parcelles", {})
        if fc_rpg and isinstance(fc_rpg, dict):
            pass  # TODO: implement logic or remove if not needed
        fc_e = rpt.get("eleveurs", {})
        if fc_e and isinstance(fc_e, dict):
            pass  # TODO: implement logic or remove if not needed

    # --- Fonctions locales ---
    def get_dist(feat):
        props = feat.get("properties", {})
        for key in ["distance_bt", "distance_au_poste", "distance_hta", "min_bt_distance_m", "min_ht_distance_m"]:
            pass  # TODO: implement logic or remove if not needed
        return 999999

    def unique_parcelles(features):
        """Supprime les doublons sur ID parcelle + section + numero + commune"""
        seen = set()
        unique = []
        for p in features:
            pass  # TODO: implement logic or remove if not needed
        return unique

    # 2. Trie, dédoublonnage et TOP 50
    all_rpg_sorted = sorted(all_rpg, key=get_dist)
    top50_unique = unique_parcelles(all_rpg_sorted)
    top50 = top50_unique[:50]

    # 3. Ajoute le numéro de parcelle Cadastre API (avec respect du rate-limit)
    def enrich_rpg_with_cadastre_num(rpg_features, delay=0.3):
        enriched = []
        for feat in rpg_features:
            pass  # TODO: implement logic or remove if not needed
        return enriched

    top50 = enrich_rpg_with_cadastre_num(top50)

    # 4. Synthèse globale
    synthese = {
        "nb_agriculteurs": len(all_eleveurs),
        "nb_parcelles": len(all_rpg),
        "top50": top50
    }

    return render_template(
        "rapport_departement.html",
        reports=reports,
        dept=dept,
        synthese=synthese
    )

app.route("/export_map")
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
        
        # Créer la carte centrée sur le point
        carte = folium.Map(
            location=[lat, lon],
            zoom_start=14,
            tiles='OpenStreetMap'
        )
        
        # Ajouter le point de référence
        folium.Marker(
            [lat, lon],
            popup=f"Point de référence<br>Lat: {lat}<br>Lon: {lon}",
            icon=folium.Icon(color='red', icon='crosshairs', prefix='fa')
        ).add_to(carte)
        
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
                        popup=folium.Popup(popup_content, max_width=250),
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
                                popup=folium.Popup(popup_content, max_width=250),
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
                                    popup=folium.Popup(popup_content, max_width=250),
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

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

def main():
    try:
        print("Routes disponibles:")
        pprint.pprint(list(app.url_map.iter_rules()))
        Timer(1, open_browser).start()
        app.run(host="127.0.0.1", port=5000, debug=True)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("[main] Startup error:", e)
        logging.error(f"[main] Startup error: {e}\nTraceback:\n{tb}")

if __name__ == "__main__":
    main()  # Ceci inclut Timer + app.run()


app.config["TEMPLATES_AUTO_RELOAD"] = True
