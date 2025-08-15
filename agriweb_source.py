# --- GeoRisques API: fetch risks for a point ---
import requests

# Fonction utilitaire pour logging sécurisé (évite les erreurs WinError 233)
def safe_print(*args, **kwargs):
    """Print sécurisé qui ignore les erreurs de canal fermé"""
    try:
        print(*args, **kwargs)
    except OSError:
        # Ignorer les erreurs de canal fermé (WinError 233)
        pass
def fetch_georisques_risks(lat, lon):
    """
    Appelle l'API GeoRisques pour obtenir les risques naturels et technologiques pour un point.
    Utilise tous les endpoints disponibles dans l'API v1.
    Voir doc: https://www.georisques.gouv.fr/doc-api
    """
    safe_print(f"🔍 [GEORISQUES] === DÉBUT APPEL GEORISQUES pour point {lat}, {lon} ===")
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
                    # cleaned corrupted pasted text block removed

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

# Import du module de rapport complet
try:
    from rapport_commune_complet import generate_comprehensive_commune_report
    RAPPORT_COMPLET_AVAILABLE = True
    print("📊 [RAPPORT] Module de rapport complet importé avec succès")
except ImportError as e:
    print(f"⚠️ [RAPPORT] Module de rapport complet non disponible: {e}")
    RAPPORT_COMPLET_AVAILABLE = False

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
    geolocator = Nominatim(user_agent="geoapp", timeout=10)
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
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
                
                print(f"🔍 [POLYGON_SEARCH] {layer_name}: bbox {bbox}")
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
                    print(f"✅ [POLYGON_SEARCH] {layer_name}: {len(filtered)}/{len(features)} features dans la commune")
                    return filtered
                return features
        else:
            # Pour l'API Carto directe (cadastre, etc.)
            params = {
                "geom": json.dumps(geom_geojson) if isinstance(geom_geojson, dict) else geom_geojson,
                "_limit": 1000
            }
            
            print(f"🔍 [API_CARTO] {api_endpoint} avec géométrie commune")
            resp = requests.get(api_endpoint, params=params, timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                features = data.get('features', [])
                print(f"✅ [API_CARTO] {api_endpoint}: {len(features)} features trouvées")
                return features
            else:
                print(f"⚠️ [API_CARTO] {api_endpoint}: erreur {resp.status_code}")
                return []
                
    except Exception as e:
        print(f"❌ [POLYGON_SEARCH] Erreur {api_endpoint}: {e}")
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
    
    print(f"🏠 [BATIMENTS_OSM] Récupération via OpenStreetMap (Overpass API)")
    
    try:
        commune_poly = shape(commune_geom)
        bounds = commune_poly.bounds
        minx, miny, maxx, maxy = bounds
        
        # Calculer la taille de la commune
        total_area = (maxx - minx) * (maxy - miny)
        print(f"📐 [BATIMENTS] Superficie bbox: {total_area:.6f}° (~{total_area*12100:.0f}km²)")
        
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
        
        print(f"🎯 [BATIMENTS] Centre: ({center_lat:.4f}, {center_lon:.4f}), Rayon: {radius_meters}m")
        
        # Requête Overpass pour récupérer tous les bâtiments dans la zone
        overpass_query = f"""
        [out:json][timeout:60];
        (
          way["building"](around:{radius_meters},{center_lat},{center_lon});
          relation["building"](around:{radius_meters},{center_lat},{center_lon});
        );
        out geom;
        """
        
        print(f"🌐 [BATIMENTS] Envoi requête Overpass...")
        
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=overpass_query,
            timeout=120  # Timeout plus long pour les grandes communes
        )
        
        if response.status_code != 200:
            print(f"❌ [BATIMENTS] Erreur Overpass: {response.status_code}")
            return {"type": "FeatureCollection", "features": []}
        
        data = response.json()
        elements = data.get("elements", [])
        print(f"📊 [BATIMENTS] {len(elements)} éléments OSM bruts récupérés")
        
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
                print(f"⚠️ [BATIMENTS] Erreur conversion élément OSM: {e}")
                continue
        
        print(f"✅ [BATIMENTS_OSM] {len(all_features)} bâtiments filtrés dans la commune")
        
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
            
            print(f"📊 [STATS] Surface moyenne: {avg_surface:.1f}m² (échantillon)")
            print(f"📊 [STATS] Estimation bâtiments >100m²: {estimated_100m2}/{len(all_features)} ({100*ratio_100m2:.1f}%)")
        
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
        print(f"❌ [BATIMENTS_OSM] Erreur globale: {e}")
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
    elif response.status_code == 414:
        print(f"⚠️ API Cadastre: 414 URI Too Large - polygone trop grand pour une requête directe")
    else:
        print(f"⚠️ API Cadastre: {response.status_code} - {response.text}")
    return None

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
                            else:  # Friches
                                icon = "🌾"
                                text = "Voir la friche"
                                
                            street_view_link = f"<br><br><a href='{street_view_url}' target='_blank' style='color: #1474fa; text-decoration: none; padding: 4px 8px; background: #f0f8ff; border-radius: 4px; display: inline-block;'>{icon} {text}</a>"
                        except Exception as e:
                            print(f"[DEBUG] Impossible de calculer le centroïde pour {name}: {e}")
                    
                    # Debug : Vérifier si on a des références cadastrales
                    if name in ["Parkings", "Friches", "Potentiel Solaire"]:
                        cadastre_refs = props.get("parcelles_cadastrales", [])
                        print(f"🏛️ [DEBUG {name}] Feature avec {len(cadastre_refs)} références cadastrales")
                    
                    # Traitement spécial pour les toitures (Potentiel Solaire)
                    if name == "Potentiel Solaire":
                        # Affichage prioritaire de l'adresse pour les toitures
                        adresse = props.get("adresse")
                        if adresse and adresse != "Adresse non trouvée" and adresse != "Erreur géocodage":
                            tooltip_lines.append(f"<b>📍 Adresse:</b> {adresse}")
                            
                            # Informations complémentaires sur l'adresse
                            distance = props.get("adresse_distance")
                            score = props.get("adresse_score")
                            if distance is not None:
                                tooltip_lines.append(f"<b>Distance adresse:</b> {distance}m")
                            if score:
                                tooltip_lines.append(f"<b>Précision:</b> {score:.1f}")
                        
                        # Surface de la toiture
                        surface = props.get("area", props.get("surface"))
                        if surface:
                            tooltip_lines.append(f"<b>🏠 Surface toiture:</b> {surface:.0f} m²")
                        
                        # Références cadastrales
                        refs_cadastrales = props.get("parcelles_cadastrales", [])
                        if refs_cadastrales:
                            tooltip_lines.append(f"<b>🏛️ Parcelles cadastrales ({len(refs_cadastrales)}):</b>")
                            for ref in refs_cadastrales[:3]:  # Limite à 3 pour les toitures
                                if isinstance(ref, dict):
                                    ref_complete = ref.get('reference_complete', 'N/A')
                                    tooltip_lines.append(f"  • {ref_complete}")
                            if len(refs_cadastrales) > 3:
                                tooltip_lines.append(f"  ... et {len(refs_cadastrales) - 3} autres")
                        
                        # Autres propriétés importantes pour les toitures
                        for k, v in props.items():
                            if k not in ["adresse", "adresse_distance", "adresse_score", "code_postal", "ville", "code_commune", 
                                       "parcelles_cadastrales", "nb_parcelles_cadastrales", "area", "surface"]:
                                if k in ["distance_poste_bt", "distance_poste_hta"]:
                                    tooltip_lines.append(f"<b>⚡ {k}:</b> {v:.0f}m" if isinstance(v, (int, float)) else f"<b>{k}:</b> {v}")
                                else:
                                    tooltip_lines.append(f"<b>{k}:</b> {v}")
                    
                    else:
                        # Traitement standard pour parkings et friches
                        for k, v in props.items():
                            if k == "parcelles_cadastrales" and isinstance(v, list) and v:
                                # Affichage formaté des références cadastrales
                                tooltip_lines.append(f"<b>Références cadastrales ({len(v)}):</b>")
                                for ref in v[:5]:  # Limite à 5 références pour la lisibilité
                                    if isinstance(ref, dict):
                                        ref_complete = ref.get('reference_complete', 'N/A')
                                        tooltip_lines.append(f"  • {ref_complete}")
                                    else:
                                        tooltip_lines.append(f"  • {str(ref)}")
                                if len(v) > 5:
                                    tooltip_lines.append(f"  ... et {len(v) - 5} autres")
                            elif k == "nb_parcelles_cadastrales":
                                tooltip_lines.append(f"<b>{k}:</b> {v}")
                            elif k not in ["parcelles_cadastrales"]:  # Exclure la liste brute
                                tooltip_lines.append(f"<b>{k}:</b> {v}")
                    
                    tooltip_text = "<br>".join(tooltip_lines)
                    
                    # Créer le popup avec les liens Street View et Pages Jaunes si disponibles
                    popup_content = tooltip_text + street_view_link + pages_jaunes_link
                    
                    # SOLUTION: Créer la style_function directement sans closure
                    if name == "Parkings":
                        style_func = lambda feature: {
                            "color": "orange", 
                            "weight": 3, 
                            "fillColor": "orange", 
                            "fillOpacity": 0.4,
                            "opacity": 0.8
                        }
                    elif name == "Friches":
                        style_func = lambda feature: {
                            "color": "brown", 
                            "weight": 3, 
                            "fillColor": "brown", 
                            "fillOpacity": 0.4,
                            "opacity": 0.8
                        }
                    elif name == "Potentiel Solaire":
                        style_func = lambda feature: {
                            "color": "gold", 
                            "weight": 3, 
                            "fillColor": "gold", 
                            "fillOpacity": 0.4,
                            "opacity": 0.8
                        }
                    else:  # ZAER
                        style_func = lambda feature: {
                            "color": "cyan", 
                            "weight": 3, 
                            "fillColor": "cyan", 
                            "fillOpacity": 0.4,
                            "opacity": 0.8
                        }
                    
                    folium.GeoJson(
                        geom, 
                        style_function=style_func,
                        tooltip=tooltip_text,
                        popup=folium.Popup(popup_content, max_width=400) if name in ["Parkings", "Friches", "Potentiel Solaire"] else None
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
        cadastre_filtered_group = folium.FeatureGroup(name="🏛️ Cadastre Parkings/Friches", show=True)
        
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
        
        for i, ref_info in enumerate(parking_friches_cadastre[:5]):
            icon = "🅿️" if ref_info["type"] == "parking" else "🏭"
            info_popup += f"{icon} {ref_info['reference']}<br>"
        
        if len(parking_friches_cadastre) > 5:
            info_popup += f"... et {len(parking_friches_cadastre) - 5} autres"
        
        # Ajouter un marker central avec la liste
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(info_popup, max_width=400),
            icon=folium.Icon(color="purple", icon="list", prefix="fa")
        ).add_to(cadastre_filtered_group)
        
        map_obj.add_child(cadastre_filtered_group)
        print(f"✅ [CARTE] Couche cadastre: {len(parking_friches_cadastre)} références affichées")

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

    def sse_format(event: str | None, data: str):
        chunks = []
        if event:
            chunks.append(f"event: {event}")
        for line in data.splitlines() or [""]:
            chunks.append(f"data: {line}")
        return "\n".join(chunks) + "\n\n"

    @stream_with_context
    def event_stream():
        # Récupération des paramètres minimaux
        commune = flask_request.args.get("commune", "").strip()
        if not commune:
            yield sse_format("error", "Veuillez fournir une commune.")
            return

        # Transmettre quelques filtres utiles (optionnels)
        filter_rpg       = flask_request.args.get("filter_rpg", "true").lower() == "true"
        filter_parkings  = flask_request.args.get("filter_parkings", "true").lower() == "true"
        filter_friches   = flask_request.args.get("filter_friches", "true").lower() == "true"
        filter_toitures  = flask_request.args.get("filter_toitures", "true").lower() == "true"
        filter_by_dist   = flask_request.args.get("filter_by_distance", "false").lower() == "true"

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
    import requests
    import json
    from urllib.parse import quote_plus
    from flask import request as flask_request
    from shapely.geometry import shape, Point
    from shapely.ops import transform as shp_transform
    from pyproj import Transformer
    
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
        
    except OSError as e:
        # Erreur de canal fermé (WinError 233) - utiliser des valeurs par défaut
        safe_print(f"⚠️ [PARAMÈTRES] Erreur lecture paramètres: {e}, utilisation valeurs par défaut")
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
    commune_poly = shape(contour)
    minx, miny, maxx, maxy = commune_poly.bounds
    bbox = f"{minx},{miny},{maxx},{maxy},EPSG:4326"

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
                print(f"⚠️ Géométrie ignorée à cause d'une erreur: {e}")
                continue
        return filtered

    # NOUVELLE APPROCHE: Utilisation du polygone exact de la commune selon la doc API Carto
    print(f"🆕 [NOUVELLE_APPROCHE] Utilisation du polygone exact de la commune (API Carto)")
    print(f"🆕 [COMMUNE_POLYGON] Récupération exhaustive sur toute la commune: {commune}")
    
    # Utilisation des nouvelles fonctions qui exploitent le polygone complet de la commune
    rpg_raw          = get_rpg_info_by_polygon(contour) if filter_rpg else []
    postes_bt_data   = filter_in_commune(fetch_wfs_data(POSTE_LAYER, bbox))
    postes_hta_data  = filter_in_commune(fetch_wfs_data(HT_POSTE_LAYER, bbox))
    eleveurs_data    = filter_in_commune(fetch_wfs_data(ELEVEURS_LAYER, bbox, srsname="EPSG:4326"))
    # plu_info sera remplacé par filtered_zones après l'optimisation des zones
    plu_info_temp    = get_plu_info_by_polygon(contour)
    zaer_data        = get_zaer_info_by_polygon(contour)
    
    # Récupération conditionnelle des données avec filtrage - NOUVELLE MÉTHODE POLYGONE
    parkings_data    = get_parkings_info_by_polygon(contour) if filter_parkings else []
    friches_data     = get_friches_info_by_polygon(contour) if filter_friches else []
    
    # Données toujours récupérées pour les calculs de distance - NOUVELLE MÉTHODE POLYGONE
    solaire_data     = get_solaire_info_by_polygon(contour)
    sirene_data      = get_sirene_info_by_polygon(contour)

    point          = {"type": "Point", "coordinates": [lon, lat]}
    
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
                print(f"🔧 [OPTIMISATION] Géométrie trop complexe ({len(geom_json)} chars), simplification en bbox")
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
                print(f"🔧 [OPTIMISATION] Géométrie OK ({len(geom_json)} chars)")
                return geom
        except Exception as e:
            print(f"⚠️ [OPTIMISATION] Erreur, utilisation géométrie originale: {e}")
            return geom
    
    # Récupération enrichie des données API avec optimisation géométrique
    print(f"🔍 [COMMUNE] Utilisation du polygone pour les APIs avec optimisation anti-414")
    contour_optimise = optimize_geometry_for_api(contour)
    
    api_cadastre   = get_api_cadastre_data(contour_optimise)  # Utilise le polygone optimisé
    api_nature     = get_all_api_nature_data(contour_optimise)  # Utilise le polygone optimisé
    api_urbanisme  = get_all_gpu_data(contour_optimise)  # Utilise le polygone optimisé
    
    # Enrichissement des données si l'option zones est activée
    if filter_zones and api_urbanisme.get("success"):
        print(f"🔍 [COMMUNE] Enrichissement des détails de zones GPU pour {commune}")
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

    # Filtrage avancé pour les nouvelles couches
    
    # Initialisation des listes filtrées
    filtered_parkings = []
    filtered_friches = []
    filtered_zones = []
    filtered_parcelles_in_zones = []
    
    # 5b) Filtrage des parkings selon les critères (utilise les sliders unifiés)
    if filter_parkings and parkings_data:
        print(f"🔍 [PARKINGS] Filtrage: >{parking_min_area}m², BT<{max_distance_bt}m, HTA<{max_distance_hta}m")
        print(f"🔍 [PARKINGS] Parkings bruts récupérés: {len(parkings_data)}")
        for feat in parkings_data:
            if "geometry" not in feat:
                continue
            try:
                poly = shape(feat["geometry"])
                props = feat.get("properties", {})

                # Calcul de la surface en m²
                area_m2 = shp_transform(to_l93, poly).area
                if area_m2 < parking_min_area:
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
                        print(f"🏠 [SURFACE_LIBRE] Calcul pour parking...")
                        batiments_data = get_batiments_data(feat["geometry"])
                        surface_libre_result = calculate_surface_libre_parcelle(feat["geometry"], batiments_data)
                        props.update({
                            'surface_batie_m2': surface_libre_result.get('surface_batie_m2', 0),
                            'surface_libre_m2': surface_libre_result.get('surface_libre_m2', 0),
                            'surface_libre_pct': surface_libre_result.get('surface_libre_pct', 0),
                            'batiments_count': surface_libre_result.get('batiments_count', 0)
                        })
                    except Exception as e:
                        print(f"❌ [SURFACE_LIBRE] Erreur parking: {e}")
                        props['surface_libre_error'] = str(e)

                filtered_parkings.append({
                    "type": "Feature",
                    "geometry": feat["geometry"],
                    "properties": props
                })
            except Exception as e:
                print(f"⚠️ Erreur filtrage parking: {e}")
                continue
        print(f"✅ [PARKINGS] {len(filtered_parkings)} parkings trouvés après filtrage")
        
        # 5b-bis) Récupération optimisée des références cadastrales pour les parkings sélectionnés
        if filtered_parkings:
            print(f"🏛️ [CADASTRE-PARKINGS] Récupération des références cadastrales pour {len(filtered_parkings)} parkings...")
            
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
                        print(f"    ⚠️ Erreur API cadastre: {resp.status_code}")
                        return []
                except Exception as e:
                    print(f"    ⚠️ Exception cadastre parking: {e}")
                    return []
            
            # Enrichir chaque parking avec ses références cadastrales
            for i, parking in enumerate(filtered_parkings):
                print(f"    📍 Parking {i+1}/{len(filtered_parkings)}: recherche cadastre...")
                parcelles_parking = get_parcelles_for_parking(parking["geometry"])
                
                if parcelles_parking:
                    print(f"      🔍 [DEBUG] Structure API cadastre - première parcelle: {parcelles_parking[0] if parcelles_parking else 'Aucune'}")
                    
                    # Extraire les références cadastrales
                    refs_cadastrales = []
                    for parcelle in parcelles_parking:
                        props = parcelle.get('properties', {})
                        print(f"      🔍 [DEBUG] Propriétés parcelle: {props}")
                        
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
                        
                        print(f"      🏛️ [DEBUG] Référence créée: {ref}")
                        refs_cadastrales.append(ref)
                    
                    # Ajouter aux propriétés du parking
                    parking["properties"]["parcelles_cadastrales"] = refs_cadastrales
                    parking["properties"]["nb_parcelles_cadastrales"] = len(refs_cadastrales)
                    print(f"      ✅ {len(refs_cadastrales)} parcelles cadastrales trouvées")
                else:
                    parking["properties"]["parcelles_cadastrales"] = []
                    parking["properties"]["nb_parcelles_cadastrales"] = 0
                    print(f"      ❌ Aucune parcelle cadastrale trouvée")
            
            print(f"✅ [CADASTRE-PARKINGS] Enrichissement terminé pour tous les parkings")
    else:
        print(f"⚠️ [PARKINGS] Filtre parkings non activé ou aucune donnée: filter_parkings={filter_parkings}, parkings_data={len(parkings_data) if parkings_data else 0}")
    
    # 5c) Filtrage des friches selon les critères (utilise les sliders unifiés)
    if filter_friches and friches_data:
        print(f"🔍 [FRICHES] Filtrage: >{friches_min_area}m², BT<{max_distance_bt}m, HTA<{max_distance_hta}m")
        for feat in friches_data:
            if "geometry" not in feat:
                continue
            try:
                poly = shape(feat["geometry"])
                props = feat.get("properties", {})

                # Calcul de la surface en m²
                area_m2 = shp_transform(to_l93, poly).area
                if area_m2 < friches_min_area:
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
                        print(f"🏠 [SURFACE_LIBRE] Calcul pour friche...")
                        batiments_data = get_batiments_data(feat["geometry"])
                        surface_libre_result = calculate_surface_libre_parcelle(feat["geometry"], batiments_data)
                        props.update({
                            'surface_batie_m2': surface_libre_result.get('surface_batie_m2', 0),
                            'surface_libre_m2': surface_libre_result.get('surface_libre_m2', 0),
                            'surface_libre_pct': surface_libre_result.get('surface_libre_pct', 0),
                            'batiments_count': surface_libre_result.get('batiments_count', 0)
                        })
                    except Exception as e:
                        print(f"❌ [SURFACE_LIBRE] Erreur friche: {e}")
                        props['surface_libre_error'] = str(e)

                filtered_friches.append({
                    "type": "Feature",
                    "geometry": feat["geometry"],
                    "properties": props
                })
            except Exception as e:
                print(f"⚠️ Erreur filtrage friche: {e}")
                continue
        print(f"✅ [FRICHES] {len(filtered_friches)} friches trouvées après filtrage")
        
        # 5c-bis) Récupération optimisée des références cadastrales pour les friches sélectionnées
        if filtered_friches:
            print(f"🏛️ [CADASTRE-FRICHES] Récupération des références cadastrales pour {len(filtered_friches)} friches...")
            
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
                        print(f"    ⚠️ Erreur API cadastre: {resp.status_code}")
                        return []
                except Exception as e:
                    print(f"    ⚠️ Exception cadastre friche: {e}")
                    return []
            
            # Enrichir chaque friche avec ses références cadastrales
            for i, friche in enumerate(filtered_friches):
                print(f"    📍 Friche {i+1}/{len(filtered_friches)}: recherche cadastre...")
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
                    print(f"      ✅ {len(refs_cadastrales)} parcelles cadastrales trouvées")
                else:
                    friche["properties"]["parcelles_cadastrales"] = []
                    friche["properties"]["nb_parcelles_cadastrales"] = 0
                    print(f"      ❌ Aucune parcelle cadastrale trouvée")
            
            print(f"✅ [CADASTRE-FRICHES] Enrichissement terminé pour toutes les friches")
    
    # 5d) Filtrage optimisé des zones avec croisement parcelles
    filtered_zones = []
    filtered_parcelles_in_zones = []
    
    if filter_zones:
        print(f"🔍 [ZONES OPTIMISÉ] Recherche zones {zones_type_filter or 'toutes'} + parcelles >{zones_min_area}m²")
        
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
                    print(f"⚠️ Erreur API GPU zones: {resp.status_code}")
                    return []
            except Exception as e:
                print(f"⚠️ Exception API GPU zones: {e}")
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
                        print(f"    ⚠️ Zone trop grande (414), passage au suivant")
                    return []
            except Exception as e:
                print(f"    ⚠️ Exception parcelles: {e}")
                return []
        
        # 1. Récupérer toutes les zones autour de la commune
        all_zones = get_zones_around_commune(lat, lon, radius_km=3.0)
        print(f"    📍 {len(all_zones)} zones trouvées autour de la commune")
        
        # 2. Filtrer par type de zone
        target_zones = []
        for zone in all_zones:
            props = zone.get('properties', {})
            zone_type = props.get('typezone', '')
            
            # Filtrage par type si spécifié
            if zones_type_filter and not zone_type.upper().startswith(zones_type_filter.upper()):
                continue
            
            target_zones.append(zone)
        
        print(f"    🎯 {len(target_zones)} zones de type '{zones_type_filter or 'toutes'}' sélectionnées")
        
        # 3. Pour chaque zone cible, récupérer et filtrer les parcelles
        total_parcelles_trouvees = 0
        
        for i, zone in enumerate(target_zones):
            props = zone.get('properties', {})
            zone_libelle = props.get('libelle', f"Zone_{i}")
            
            print(f"    🔍 Zone {i+1}/{len(target_zones)}: {props.get('typezone', 'N/A')} - {zone_libelle}")
            
            # Récupérer les parcelles de cette zone
            parcelles = get_parcelles_in_zone(zone)
            
            if not parcelles:
                continue
            
            print(f"        📦 {len(parcelles)} parcelles trouvées")
            
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
                    
                    try:
                        # Calculer le centroïde de la parcelle
                        centroid = shape(geometry).centroid.coords[0]
                        
                        # Calculer les distances minimales aux postes
                        min_distance_bt = calculate_min_distance(centroid, postes_bt_data)
                        min_distance_hta = calculate_min_distance(centroid, postes_hta_data)
                        
                        # Distance minimale globale (le poste le plus proche, qu'il soit BT ou HTA)
                        distances = [d for d in [min_distance_bt, min_distance_hta] if d is not None]
                        min_distance_total = min(distances) if distances else None
                        
                    except Exception as e:
                        print(f"        ⚠️ Erreur calcul distances: {e}")
                    
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
                            print(f"        ⚠️ Erreur calcul distance: {e}")
                            distance_ok = True  # En cas d'erreur, on garde la parcelle
                    
                    if not distance_ok:
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
                        'min_distance_total_m': round(min_distance_total, 2) if min_distance_total is not None else None
                    })
                    
                    # Calcul de la surface libre si demandé
                    if calculate_surface_libre:
                        try:
                            print(f"🏠 [SURFACE_LIBRE] Calcul pour parcelle {parcelle_props.get('numero', 'N/A')}...")
                            
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
                            print(f"❌ [SURFACE_LIBRE] Erreur calcul pour parcelle: {e}")
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
            
            print(f"        ✅ {len(parcelles_grandes)} parcelles >{zones_min_area}m²")
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
        
        print(f"✅ [ZONES OPTIMISÉ] {len(target_zones)} zones analysées, {total_parcelles_trouvees} parcelles trouvées")

    # Utiliser les zones optimisées pour plu_info, sinon fallback
    plu_info = filtered_zones if filtered_zones else plu_info_temp

    # 6) Carte interactive
    # PPRI récupération via la nouvelle fonction GeoRisques unifiée
    def fetch_ppri_georisques(lat, lon, rayon_km=1.0):
        # Utilise maintenant la nouvelle fonction unifiée
        print(f"🔍 [PPRI] Utilisation des données GeoRisques unifiées")
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
        print(f"🏠 [TOITURES] Recherche activée - utilisation du polygone de la commune")
        print(f"🏠 [TOITURES] Postes disponibles - BT: {len(postes_bt_data)}, HTA: {len(postes_hta_data)}")
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
            print(f"🏠 [TOITURES] {len(batiments_data)} bâtiments récupérés dans la commune")

            # ANALYSE COMPLÈTE: Traitement de tous les bâtiments de la commune
            print(f"🔍 [TOITURES] Analyse complète de tous les {len(batiments_data)} bâtiments")
            print(f"💡 [TOITURES] Traitement complet activé pour une analyse exhaustive")

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
            
            # Enrichissement cadastral OPTIMISÉ avec limite
            if toitures_data:
                # ENRICHISSEMENT COMPLET: Traitement de toutes les toitures de la commune
                toitures_a_enrichir = toitures_data  # Traitement complet sans limitation
                
                print(f"🏛️ [CADASTRE-TOITURES] Enrichissement complet : {len(toitures_a_enrichir)} toitures")
                print(f"🔍 [CADASTRE-TOITURES] Traitement individuel optimisé avec limite 1000")
                
                def get_parcelles_for_toiture(toiture_geometry):
                    """Récupère les parcelles cadastrales intersectant une toiture spécifique avec limite optimisée"""
                    try:
                        api_url = "https://apicarto.ign.fr/api/cadastre/parcelle"
                        params = {
                            "geom": json.dumps(toiture_geometry),
                            "_limit": 1000  # Limite maximale au lieu de 3
                        }
                        
                        resp = requests.get(api_url, params=params, timeout=10)
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
                    # Log de progression moins verbeux
                    if (i + 1) % 50 == 0 or i == 0:
                        print(f"    📍 Progression: {i+1}/{len(toitures_a_enrichir)} toitures traitées...")
                    
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
                
                print(f"✅ [CADASTRE-TOITURES] Enrichissement individuel optimisé terminé:")
                print(f"    📊 {total_enrichies} toitures enrichies avec succès")
                print(f"    ⚠️ {total_erreurs} toitures sans données cadastrales")
                print(f"    🎯 {len(toitures_data)} toitures disponibles au total sur la carte")
            
        except Exception as e:
            print(f"❌ [TOITURES] Erreur recherche: {e}")
            import traceback
            traceback.print_exc()
            toitures_data = []
    
    print(f"🗺️ [BUILD_MAP] Appel avec {len(filtered_parkings)} parkings, {len(filtered_friches)} friches et {len(toitures_data)} toitures")
    
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
        ppri_data=ppri_data
    )
    save_map_to_cache(map_obj)
    
    # Récupérer le HTML de la carte pour l'ajouter à la réponse
    carte_html = map_obj._repr_html_() if map_obj else ""

    # Ajouter _layer aux éleveurs pour la détection côté client
    eleveurs_with_layer = []
    for eleveur in eleveurs_data:
        if eleveur.get("properties"):
            eleveur["properties"]["_layer"] = "eleveurs"
        eleveurs_with_layer.append(eleveur)
    
    # 7) Réponse JSON avec données filtrées
    response_data = {
        "lat": lat, "lon": lon,
        "rpg": final_rpg if filter_rpg else [],
        "eleveurs": eleveurs_with_layer,
        "postes_bt": postes_bt_data,
        "postes_hta": postes_hta_data,
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
        "carte_html": carte_html,  # HTML de la carte avec les popups
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
    
    return jsonify(response_data)

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
    
    # 1) Paramètres de la requête
    commune = flask_request.values.get("commune", "").strip()
    min_surface_toiture = float(flask_request.values.get("min_surface_toiture", 100.0))
    max_distance_bt = float(flask_request.values.get("max_distance_bt", 500.0))
    max_distance_hta = float(flask_request.values.get("max_distance_hta", 1000.0))
    max_results = int(flask_request.values.get("max_results", 100))  # Augmenté pour polygon complet
    
    if not commune:
        return jsonify({"error": "Veuillez fournir une commune."}), 400

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

        print(f"📍 [TOITURES POLYGON] {len(batiments_data['features'])} bâtiments trouvés")

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
        if toitures_filtrees:
            surfaces = [t["properties"]["surface_toiture_m2"] for t in toitures_filtrees]
            stats = {
                "count": len(toitures_filtrees),
                "surface_totale_m2": round(sum(surfaces), 2),
                "surface_moyenne_m2": round(sum(surfaces) / len(surfaces), 2),
                "surface_max_m2": round(max(surfaces), 2),
                "surface_min_m2": round(min(surfaces), 2)
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
        if toitures_filtrees:
            surfaces = [t["properties"]["surface_toiture_m2"] for t in toitures_filtrees]
            stats = {
                "count": len(toitures_filtrees),
                "surface_totale_m2": round(sum(surfaces), 2),
                "surface_moyenne_m2": round(sum(surfaces) / len(surfaces), 2),
                "surface_max_m2": round(max(surfaces), 2),
                "surface_min_m2": round(min(surfaces), 2)
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
    
    # 1) Paramètres de la requête
    commune = flask_request.values.get("commune", "").strip()
    
    # Filtres spécifiques aux toitures
    min_surface_toiture = float(flask_request.values.get("min_surface_toiture", 50.0))  # m²
    max_distance_bt = float(flask_request.values.get("max_distance_bt", 300.0))  # mètres
    max_distance_hta = float(flask_request.values.get("max_distance_hta", 1000.0))  # mètres
    distance_logic = flask_request.values.get("distance_logic", "OR").upper()  # OR ou AND
    poste_type_filter = flask_request.values.get("poste_type_filter", "ALL").upper()  # ALL, BT, HTA
    
    # Filtres optionnels
    max_results = int(flask_request.values.get("max_results", 1000000))  # Limite de résultats augmentée
    sort_by = flask_request.values.get("sort_by", "surface").lower()  # surface, distance
    
    if not commune:
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

    print(f"📍 [TOITURES] {len(batiments_data['features'])} bâtiments trouvés via méthode chunk optimisée")

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
    if toitures_filtrees:
        surfaces = [t["properties"]["surface_toiture_m2"] for t in toitures_filtrees]
        distances_bt = [t["properties"]["min_distance_bt_m"] for t in toitures_filtrees if t["properties"]["min_distance_bt_m"] is not None]
        distances_hta = [t["properties"]["min_distance_hta_m"] for t in toitures_filtrees if t["properties"]["min_distance_hta_m"] is not None]
        
        stats = {
            "count": len(toitures_filtrees),
            "surface_totale_m2": round(sum(surfaces), 2),
            "surface_moyenne_m2": round(sum(surfaces) / len(surfaces), 2),
            "surface_max_m2": round(max(surfaces), 2),
            "surface_min_m2": round(min(surfaces), 2),
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

""" CORRUPTED BLOCK START — IGNORE BELOW UNTIL CORRUPTED BLOCK END
18	162	N/A	BT
72 m
46.17023, 1.87838	HTA
1907 m
46.18289, 1.89020	46.16990, 1.87894	 
19	214	N/A	BT
147 m
46.16963, 1.86758	HTA
2785 m
46.18289, 1.89020	46.16962, 1.86891	 
20	136	
000BC0105
BT
181 m
46.17063, 1.86653	HTA
2951 m
46.18289, 1.89020	46.17212, 1.86588	 
21	101	N/A	BT
59 m
46.17038, 1.87328	HTA
2354 m
46.18289, 1.89020	46.17069, 1.87285	 
22	112	N/A	BT
285 m
46.19532, 1.87453	HTA
2161 m
46.18289, 1.89020	46.19683, 1.87661	 
23	121	N/A	BT
137 m
46.17274, 1.86070	HTA
3460 m
46.18289, 1.89020	46.17159, 1.86114	 
24	171	N/A	BT
81 m
46.17486, 1.87338	HTA
2024 m
46.18289, 1.89020	46.17558, 1.87349	 
25	103	N/A	BT
229 m
46.16230, 1.87769	HTA
2528 m
46.18289, 1.89020	46.16427, 1.87707	 
26	145	N/A	BT
52 m
46.16483, 1.88120	HTA
2196 m
46.18289, 1.89020	46.16530, 1.88114	 
27	107	N/A	BT
257 m
46.15997, 1.88399	HTA
2437 m
46.18289, 1.89020	46.16137, 1.88584	 
28	100	N/A	BT
51 m
46.15920, 1.87444	HTA
3150 m
46.18289, 1.89020	46.15901, 1.87486	 
29	110	N/A	BT
201 m
46.17097, 1.87451	HTA
2152 m
46.18289, 1.89020	46.16980, 1.87589	 
30	286	N/A	BT
117 m
46.19270, 1.87471	HTA
1980 m
46.18289, 1.89020	46.19319, 1.87564	 
31	474	N/A	BT
178 m
46.17819, 1.87485	HTA
1851 m
46.18289, 1.89020	46.17659, 1.87476	 
32	111	N/A	BT
197 m
46.17724, 1.88441	HTA
800 m
46.18289, 1.89020	46.17693, 1.88615	 
33	749	N/A	BT
151 m
46.17924, 1.87028	HTA
2393 m
46.18289, 1.89020	46.17864, 1.86906	 
34	126	N/A	BT
216 m
46.15992, 1.87248	HTA
3402 m
46.18289, 1.89020	46.15929, 1.87064	 
35	126	
000AY0526
BT
215 m
46.17486, 1.87338	HTA
1878 m
46.18289, 1.89020	46.17482, 1.87533	 
36	156	N/A	BT
60 m
46.16519, 1.87330	HTA
2769 m
46.18289, 1.89020	46.16501, 1.87280	 
37	138	N/A	BT
105 m
46.17917, 1.88265	HTA
932 m
46.18289, 1.89020	46.18005, 1.88229	 
38	111	N/A	BT
170 m
46.17549, 1.88781	HTA
793 m
46.18289, 1.89020	46.17580, 1.88931	 
39	338	N/A	BT
35 m
46.17092, 1.86945	HTA
2690 m
46.18289, 1.89020	46.17066, 1.86927	 
40	415	N/A	BT
152 m
46.19432, 1.87825	HTA
1897 m
46.18289, 1.89020	46.19375, 1.87700	 
41	100	N/A	BT
61 m
46.17976, 1.88473	HTA
651 m
46.18289, 1.89020	46.18026, 1.88495	 
42	123	N/A	BT
111 m
46.17358, 1.88593	HTA
1204 m
46.18289, 1.89020	46.17339, 1.88495	 
43	105	N/A	BT
79 m
46.17764, 1.86259	HTA
3086 m
46.18289, 1.89020	46.17706, 1.86301	 
44	245	N/A	BT
228 m
46.16627, 1.85287	HTA
4677 m
46.18289, 1.89020	46.16725, 1.85107	 
45	1263	N/A	BT
47 m
46.19452, 1.87207	HTA
2394 m
46.18289, 1.89020	46.19418, 1.87182	 
46	421	
000AH0100
BT
105 m
46.18192, 1.89756	HTA
752 m
46.18289, 1.89020	46.18266, 1.89697	 
47	120	N/A	BT
129 m
46.17202, 1.87593	HTA
1962 m
46.18289, 1.89020	46.17131, 1.87685	 
48	173	N/A	BT
117 m
46.17084, 1.87046	HTA
2643 m
46.18289, 1.89020	46.16980, 1.87030	 
49	197	N/A	BT
100 m
46.17024, 1.85948	HTA
3766 m
46.18289, 1.89020	46.16946, 1.85904	 
50	355	N/A	BT
67 m
46.17202, 1.86851	HTA
2650 m
46.18289, 1.89020	46.17179, 1.86906	 
51	102	N/A	BT
80 m
46.17063, 1.86653	HTA
2878 m
46.18289, 1.89020	46.17102, 1.86714	 
52	1381	N/A	BT
131 m
46.17330, 1.87393	HTA
2215 m
46.18289, 1.89020	46.17232, 1.87327	 
53	106	N/A	BT
33 m
46.17024, 1.85948	HTA
3692 m
46.18289, 1.89020	46.17050, 1.85933	 
54	105	
000BH0010
BT
144 m
46.16961, 1.87173	HTA
2419 m
46.18289, 1.89020	46.17089, 1.87201	 
55	102	N/A	BT
117 m
46.15997, 1.88399	HTA
2580 m
46.18289, 1.89020	46.16022, 1.88502	 
56	104	N/A	BT
135 m
46.17997, 1.86506	HTA
2941 m
46.18289, 1.89020	46.18011, 1.86385	 
57	227	N/A	BT
228 m
46.16199, 1.87483	HTA
2906 m
46.18289, 1.89020	46.16307, 1.87308	 
58	139	N/A	BT
105 m
46.17897, 1.86133	HTA
3330 m
46.18289, 1.89020	46.17847, 1.86052	 
59	106	
000AV0109
BT
169 m
46.17549, 1.88781	HTA
783 m
46.18289, 1.89020	46.17668, 1.88685	 
60	164	N/A	BT
34 m
46.15920, 1.87444	HTA
3160 m
46.18289, 1.89020	46.15936, 1.87417	 
61	106	N/A	BT
103 m
46.17202, 1.87593	HTA
1994 m
46.18289, 1.89020	46.17275, 1.87536	 
62	143	N/A	BT
223 m
46.17904, 1.88677	HTA
540 m
46.18289, 1.89020	46.17828, 1.88863	 
63	163	N/A	BT
158 m
46.16483, 1.88120	HTA
2319 m
46.18289, 1.89020	46.16478, 1.87978	 
64	1179	N/A	BT
134 m
46.16199, 1.87483	HTA
2854 m
46.18289, 1.89020	46.16289, 1.87404	 
65	108	N/A	BT
126 m
46.14389, 1.86632	HTA
4952 m
46.18289, 1.89020	46.14496, 1.86671	 
66	372	N/A	BT
196 m
46.19270, 1.87471	HTA
1932 m
46.18289, 1.89020	46.19341, 1.87633	 
67	142	
000BD0010
BT
81 m
46.17202, 1.86851	HTA
2774 m
46.18289, 1.89020	46.17167, 1.86786	 
68	233	N/A	BT
192 m
46.16611, 1.86963	HTA
3137 m
46.18289, 1.89020	46.16517, 1.86817	 
69	159	N/A	BT
36 m
46.19532, 1.87453	HTA
2231 m
46.18289, 1.89020	46.19513, 1.87426	 
70	122	N/A	BT
72 m
46.17976, 1.88473	HTA
706 m
46.18289, 1.89020	46.17918, 1.88502	 
71	226	N/A	BT
57 m
46.17202, 1.87593	HTA
1969 m
46.18289, 1.89020	46.17177, 1.87638	 
72	194	N/A	BT
161 m
46.17360, 1.87049	HTA
2260 m
46.18289, 1.89020	46.17398, 1.87189	 
73	131	N/A	BT
105 m
46.16851, 1.86368	HTA
3365 m
46.18289, 1.89020	46.16927, 1.86312	 
74	114	N/A	BT
586 m
46.16627, 1.85287	HTA
4913 m
46.18289, 1.89020	46.16878, 1.84824	 
75	475	N/A	BT
112 m
46.16804, 1.86915	HTA
2839 m
46.18289, 1.89020	46.16734, 1.86988	 
76	117	N/A	BT
249 m
46.17360, 1.87049	HTA
2564 m
46.18289, 1.89020	46.17477, 1.86857	 
77	274	N/A	BT
17 m
46.16790, 1.87186	HTA
2631 m
46.18289, 1.89020	46.16777, 1.87194	 
78	100	N/A	BT
234 m
46.17627, 1.86120	HTA
3528 m
46.18289, 1.89020	46.17636, 1.85909	 
79	148	N/A	BT
180 m
46.18318, 1.88167	HTA
812 m
46.18289, 1.89020	46.18412, 1.88299	 
80	128	N/A	BT
138 m
46.17549, 1.88781	HTA
730 m
46.18289, 1.89020	46.17654, 1.88847	 
81	107	N/A	BT
76 m
46.16841, 1.87248	HTA
2576 m
46.18289, 1.89020	46.16774, 1.87262	 
82	160	N/A	BT
215 m
46.17888, 1.86670	HTA
2495 m
46.18289, 1.89020	46.17779, 1.86830	 
83	133	N/A	BT
120 m
46.17904, 1.88677	HTA
455 m
46.18289, 1.89020	46.17970, 1.88762	 
84	115	N/A	BT
46 m
46.17198, 1.88152	HTA
1582 m
46.18289, 1.89020	46.17190, 1.88111	 
85	307	N/A	BT
104 m
46.17141, 1.86365	HTA
3197 m
46.18289, 1.89020	46.17062, 1.86414	 
86	101	N/A	BT
257 m
46.18192, 1.89756	HTA
1023 m
46.18289, 1.89020	46.18333, 1.89941	 
87	103	N/A	BT
132 m
46.16961, 1.87399	HTA
2302 m
46.18289, 1.89020	46.16886, 1.87492	 
88	102	N/A	BT
85 m
46.16622, 1.86626	HTA
3168 m
46.18289, 1.89020	46.16624, 1.86702	 
89	159	N/A	BT
95 m
46.17372, 1.87927	HTA
1606 m
46.18289, 1.89020	46.17296, 1.87967	 
90	189	N/A	BT
64 m
46.16963, 1.86758	HTA
2879 m
46.18289, 1.89020	46.17020, 1.86758	 
91	114	N/A	BT
49 m
46.15997, 1.88399	HTA
2681 m
46.18289, 1.89020	46.15962, 1.88372	 
92	106	N/A	BT
245 m
46.16258, 1.88255	HTA
2169 m
46.18289, 1.89020	46.16444, 1.88375	 
93	402	N/A	BT
70 m
46.16804, 1.86915	HTA
2844 m
46.18289, 1.89020	46.16762, 1.86962	 
94	115	N/A	BT
40 m
46.17861, 1.87967	HTA
1300 m
46.18289, 1.89020	46.17856, 1.87931	 
95	187	N/A	BT
154 m
46.17724, 1.88441	HTA
1042 m
46.18289, 1.89020	46.17671, 1.88313	 
96	135	N/A	BT
86 m
46.16963, 1.86758	HTA
2826 m
46.18289, 1.89020	46.16984, 1.86833	 
97	150	N/A	BT
514 m
46.16273, 1.86622	HTA
3982 m
46.18289, 1.89020	46.16053, 1.86214	 
98	352	N/A	BT
106 m
46.16840, 1.86982	HTA
2712 m
46.18289, 1.89020	46.16812, 1.87073	 
99	128	N/A	BT
276 m
46.16833, 1.88609	HTA
1905 m
46.18289, 1.89020	46.16685, 1.88409	 
100	200	N/A	BT
213 m
46.17024, 1.85948	HTA
3499 m
46.18289, 1.89020	46.17008, 1.86139	 
101	103	N/A	BT
48 m
46.17657, 1.86601	HTA
2822 m
46.18289, 1.89020	46.17648, 1.86559	 
102	108	N/A	BT
60 m
46.16581, 1.88667	HTA
1993 m
46.18289, 1.89020	46.16534, 1.88639	 
103	749	N/A	BT
198 m
46.18635, 1.86933	HTA
2337 m
46.18289, 1.89020	46.18807, 1.86979	 
104	415	N/A	BT
116 m
46.17358, 1.88593	HTA
1027 m
46.18289, 1.89020	46.17435, 1.88664	 
105	176	N/A	BT
105 m
46.16199, 1.87483	HTA
2920 m
46.18289, 1.89020	46.16118, 1.87533	 
106	134	N/A	BT
229 m
46.19452, 1.87207	HTA
2610 m
46.18289, 1.89020	46.19504, 1.87007	 
107	124	N/A	BT
171 m
46.17531, 1.88196	HTA
1351 m
46.18289, 1.89020	46.17560, 1.88044	 
108	231	N/A	BT
64 m
46.17198, 1.88152	HTA
1517 m
46.18289, 1.89020	46.17251, 1.88129	 
109	100	N/A	BT
67 m
46.18035, 1.88096	HTA
997 m
46.18289, 1.89020	46.18058, 1.88151	 
110	150	N/A	BT
93 m
46.16782, 1.87797	HTA
2123 m
46.18289, 1.89020	46.16755, 1.87876	 
111	112	N/A	BT
102 m
46.17141, 1.86365	HTA
3261 m
46.18289, 1.89020	46.17049, 1.86356	 
112	203	N/A	BT
140 m
46.18318, 1.88167	HTA
1066 m
46.18289, 1.89020	46.18394, 1.88065	 
113	103	N/A	BT
58 m
46.17202, 1.86851	HTA
2714 m
46.18289, 1.89020	46.17150, 1.86856	 
114	288	N/A	BT
103 m
46.17063, 1.86653	HTA
3061 m
46.18289, 1.89020	46.17012, 1.86576	 
115	100	N/A	BT
111 m
46.16611, 1.86963	HTA
2957 m
46.18289, 1.89020	46.16683, 1.86895	 
116	109	N/A	BT
162 m
46.17549, 1.88781	HTA
918 m
46.18289, 1.89020	46.17557, 1.88635	 
117	128	
000BH0100
BT
71 m
46.16918, 1.87246	HTA
2423 m
46.18289, 1.89020	46.16975, 1.87276	 
118	115	N/A	BT
172 m
46.16650, 1.88156	HTA
1925 m
46.18289, 1.89020	46.16711, 1.88298	 
119	468	N/A	BT
167 m
46.17330, 1.87393	HTA
1941 m
46.18289, 1.89020	46.17449, 1.87486	 
120	118	
000BM0033
BT
283 m
46.16650, 1.88156	HTA
1944 m
46.18289, 1.89020	46.16646, 1.88411	 
121	117	N/A	BT
23 m
46.15920, 1.87444	HTA
3167 m
46.18289, 1.89020	46.15903, 1.87455	 
122	140	N/A	BT
74 m
46.16790, 1.87186	HTA
2624 m
46.18289, 1.89020	46.16742, 1.87232	 
123	1617	N/A	BT
45 m
46.19296, 1.87207	HTA
2331 m
46.18289, 1.89020	46.19281, 1.87169	 
124	104	N/A	BT
179 m
46.16519, 1.87330	HTA
2894 m
46.18289, 1.89020	46.16388, 1.87236	 
125	107	
000AO0105
BT
75 m
46.17997, 1.86506	HTA
2775 m
46.18289, 1.89020	46.18060, 1.86530	 
126	102	N/A	BT
167 m
46.16258, 1.88255	HTA
2496 m
46.18289, 1.89020	46.16234, 1.88107	 
127	220	N/A	BT
70 m
46.17549, 1.88781	HTA
849 m
46.18289, 1.89020	46.17544, 1.88844	 
128	174	N/A	BT
145 m
46.17198, 1.88152	HTA
1678 m
46.18289, 1.89020	46.17144, 1.88033	 
129	153	N/A	BT
173 m
46.19426, 1.86738	HTA
2663 m
46.18289, 1.89020	46.19396, 1.86892	 
130	116	N/A	BT
59 m
46.18035, 1.88096	HTA
1024 m
46.18289, 1.89020	46.18008, 1.88141	 
131	104	N/A	BT
69 m
46.16970, 1.88149	HTA
1796 m
46.18289, 1.89020	46.16967, 1.88086	 
132	330	N/A	BT
94 m
46.16627, 1.85287	HTA
4445 m
46.18289, 1.89020	46.16638, 1.85372	 
133	373	N/A	BT
154 m
46.17202, 1.87593	HTA
1953 m
46.18289, 1.89020	46.17120, 1.87705	 
134	187	N/A	BT
114 m
46.15567, 1.85750	HTA
4762 m
46.18289, 1.89020	46.15619, 1.85661	 
135	342	N/A	BT
121 m
46.17360, 1.87049	HTA
2304 m
46.18289, 1.89020	46.17371, 1.87157	 
136	1473	N/A	BT
55 m
46.18208, 1.88396	HTA
666 m
46.18289, 1.89020	46.18172, 1.88431	 
137	385	N/A	BT
158 m
46.17372, 1.87927	HTA
1741 m
46.18289, 1.89020	46.17278, 1.87821	 
138	112	N/A	BT
241 m
46.15908, 1.87264	HTA
3452 m
46.18289, 1.89020	46.15884, 1.87048	 
139	143	N/A	BT
151 m
46.17486, 1.87338	HTA
2213 m
46.18289, 1.89020	46.17396, 1.87236	 
140	184	N/A	BT
148 m
46.16956, 1.88390	HTA
1766 m
46.18289, 1.89020	46.16823, 1.88401	 
141	120	N/A	BT
223 m
46.19426, 1.86738	HTA
2741 m
46.18289, 1.89020	46.19226, 1.86735	 
142	120	N/A	BT
45 m
46.17724, 1.88441	HTA
900 m
46.18289, 1.89020	46.17694, 1.88468	 
143	103	N/A	BT
135 m
46.16650, 1.88156	HTA
2090 m
46.18289, 1.89020	46.16571, 1.88248	 
144	147	N/A	BT
138 m
46.17486, 1.87338	HTA
1930 m
46.18289, 1.89020	46.17543, 1.87449	 
145	101	N/A	BT
207 m
46.16782, 1.87797	HTA
2182 m
46.18289, 1.89020	46.16652, 1.87931	 
146	130	N/A	BT
178 m
46.15674, 1.87201	HTA
3393 m
46.18289, 1.89020	46.15727, 1.87352	 
147	734	N/A	BT
102 m
46.17202, 1.87593	HTA
2087 m
46.18289, 1.89020	46.17124, 1.87544	 
148	175	N/A	BT
213 m
46.18635, 1.89336	HTA
675 m
46.18289, 1.89020	46.18624, 1.89527	 
149	100	N/A	BT
110 m
46.14813, 1.86658	HTA
4770 m
46.18289, 1.89020	46.14750, 1.86582	 
150	112	N/A	BT
72 m
46.19038, 1.88172	HTA
1298 m
46.18289, 1.89020	46.19022, 1.88109	 
151	151	N/A	BT
94 m
46.17092, 1.86945	HTA
2742 m
46.18289, 1.89020	46.17020, 1.86900	 
152	535	N/A	BT
221 m
46.19270, 1.87471	HTA
1849 m
46.18289, 1.89020	46.19265, 1.87669	 
153	113	N/A	BT
235 m
46.17358, 1.88593	HTA
1126 m
46.18289, 1.89020	46.17473, 1.88415	 
154	152	N/A	BT
124 m
46.17141, 1.86365	HTA
3089 m
46.18289, 1.89020	46.17164, 1.86474	 
155	108	N/A	BT
239 m
46.16627, 1.85287	HTA
4773 m
46.18289, 1.89020	46.16545, 1.85088	 
156	380	N/A	BT
52 m
46.19452, 1.87207	HTA
2356 m
46.18289, 1.89020	46.19464, 1.87252	 
157	169	N/A	BT
119 m
46.18035, 1.88096	HTA
984 m
46.18289, 1.89020	46.18130, 1.88147	 
158	109	N/A	BT
184 m
46.17202, 1.87593	HTA
2038 m
46.18289, 1.89020	46.17052, 1.87663	 
159	175	N/A	BT
77 m
46.17063, 1.86653	HTA
2984 m
46.18289, 1.89020	46.17110, 1.86603	 
160	115	N/A	BT
96 m
46.16199, 1.87483	HTA
2885 m
46.18289, 1.89020	46.16144, 1.87550	 
161	103	N/A	BT
187 m
46.16581, 1.88667	HTA
2084 m
46.18289, 1.89020	46.16474, 1.88536	 
162	106	N/A	BT
96 m
46.16611, 1.86963	HTA
2927 m
46.18289, 1.89020	46.16688, 1.86924	 
163	106	N/A	BT
117 m
46.17202, 1.86851	HTA
2748 m
46.18289, 1.89020	46.17264, 1.86766	 
164	326	N/A	BT
95 m
46.16963, 1.86758	HTA
2840 m
46.18289, 1.89020	46.16946, 1.86842	 
165	134	N/A	BT
185 m
46.15614, 1.86872	HTA
3979 m
46.18289, 1.89020	46.15534, 1.86726	 
166	112	N/A	BT
129 m
46.17406, 1.86552	HTA
2994 m
46.18289, 1.89020	46.17465, 1.86451	 
167	422	N/A	BT
42 m
46.17058, 1.87406	HTA
2294 m
46.18289, 1.89020	46.17034, 1.87377	 
168	156	N/A	BT
114 m
46.16155, 1.87164	HTA
3067 m
46.18289, 1.89020	46.16256, 1.87149	 
169	108	N/A	BT
29 m
46.17819, 1.87485	HTA
1768 m
46.18289, 1.89020	46.17800, 1.87503	 
170	123	N/A	BT
168 m
46.17888, 1.86670	HTA
2517 m
46.18289, 1.89020	46.17815, 1.86802	 
171	311	N/A	BT
136 m
46.17084, 1.87046	HTA
2543 m
46.18289, 1.89020	46.17200, 1.87004	 
172	148	N/A	BT
125 m
46.16832, 1.87341	HTA
2364 m
46.18289, 1.89020	46.16847, 1.87452	 
173	214	N/A	BT
237 m
46.19051, 1.87229	HTA
2261 m
46.18289, 1.89020	46.18901, 1.87077	 
174	138	N/A	BT
108 m
46.17904, 1.88677	HTA
569 m
46.18289, 1.89020	46.17849, 1.88757	 
175	330	N/A	BT
131 m
46.18067, 1.87530	HTA
1659 m
46.18289, 1.89020	46.17953, 1.87564	 
176	311	N/A	BT
116 m
46.17092, 1.86945	HTA
2775 m
46.18289, 1.89020	46.17040, 1.86854	 
177	122	N/A	BT
177 m
46.16217, 1.86863	HTA
3271 m
46.18289, 1.89020	46.16140, 1.87003	 
178	255	N/A	BT
103 m
46.17372, 1.87927	HTA
1628 m
46.18289, 1.89020	46.17283, 1.87953	 
179	107	N/A	BT
191 m
46.17063, 1.86653	HTA
2872 m
46.18289, 1.89020	46.17235, 1.86656	 
180	125	N/A	BT
159 m
46.15997, 1.88399	HTA
2772 m
46.18289, 1.89020	46.15899, 1.88294	 
181	1872	N/A	BT
127 m
46.17861, 1.87967	HTA
1317 m
46.18289, 1.89020	46.17941, 1.87885	 
182	161	N/A	BT
139 m
46.17724, 1.88441	HTA
1008 m
46.18289, 1.89020	46.17599, 1.88429	 
183	114	N/A	BT
87 m
46.17202, 1.86851	HTA
2646 m
46.18289, 1.89020	46.17280, 1.86860	 
184	270	N/A	BT
141 m
46.17360, 1.87049	HTA
2298 m
46.18289, 1.89020	46.17347, 1.87175	 
185	107	N/A	BT
236 m
46.17718, 1.87696	HTA
1821 m
46.18289, 1.89020	46.17567, 1.87547	 
186	130	N/A	BT
72 m
46.16782, 1.87797	HTA
2171 m
46.18289, 1.89020	46.16810, 1.87739	 
187	128	N/A	BT
216 m
46.16519, 1.87330	HTA
2931 m
46.18289, 1.89020	46.16365, 1.87211	 
188	112	N/A	BT
211 m
46.17861, 1.87967	HTA
1413 m
46.18289, 1.89020	46.17682, 1.87900	 
189	192	
000AP0270
BT
142 m
46.17565, 1.87072	HTA
2392 m
46.18289, 1.89020	46.17637, 1.86966	 
190	2771	N/A	BT
168 m
46.18635, 1.86933	HTA
2440 m
46.18289, 1.89020	46.18775, 1.86875	 
191	172	N/A	BT
119 m
46.16840, 1.86982	HTA
2702 m
46.18289, 1.89020	46.16947, 1.86988	 
192	140	N/A	BT
114 m
46.16199, 1.87483	HTA
2954 m
46.18289, 1.89020	46.16099, 1.87507	 
193	113	
000AO0106
BT
57 m
46.17997, 1.86506	HTA
2776 m
46.18289, 1.89020	46.18041, 1.86531	 
194	273	N/A	BT
161 m
46.17531, 1.88196	HTA
1157 m
46.18289, 1.89020	46.17676, 1.88177	 
195	161	N/A	BT
79 m
46.16970, 1.88149	HTA
1675 m
46.18289, 1.89020	46.17028, 1.88190	 
196	122	N/A	BT
50 m
46.17531, 1.88196	HTA
1219 m
46.18289, 1.89020	46.17575, 1.88185	 
197	178	N/A	BT
143 m
46.16503, 1.85993	HTA
4044 m
46.18289, 1.89020	46.16439, 1.85880	 
198	189	N/A	BT
152 m
46.19426, 1.86738	HTA
2843 m
46.18289, 1.89020	46.19552, 1.86792	 
199	101	N/A	BT
43 m
46.19532, 1.87453	HTA
2248 m
46.18289, 1.89020	46.19570, 1.87452	 
200	218	N/A	BT
216 m
46.17372, 1.87927	HTA
1773 m
46.18289, 1.89020	46.17340, 1.87735	 
 Analyse Environnementale
Biodiversité:
Zones Natura 2000: 0
ZNIEFF Type I: 0
ZNIEFF Type II: 0

Espaces protégés:
Parcs Nationaux: 0
Parcs Naturels Régionaux: 0
Réserves: 0

 Synthèse et Recommandations
Scores de potentiel:
Score Potentiel Energetique:
100/100
Score Potentiel Economique:
100/100
            # cleaned corrupted pasted text block removed
Cultures principales:
PPH: 440.8 ha
PTR: 53.4 ha
TTH: 20.2 ha
BTH: 18.5 ha
ORP: 18.4 ha
Statistiques:
Surface moyenne: 3.4 ha
Diversité cultures: 5 types

 Analyse Parkings
Potentiel photovoltaïque:
Puissance installable: 38.43 MWc
Production annuelle: 46116 MWh/an
Surface totale: 256171 m²

Détails des parkings (114)
#	Surface (m²)	Parcelles	BT le plus proche	HTA le plus proche	Position	Liens
1	932	N/A	BT
31 m
46.16961, 1.87173	HTA
2542 m
46.18289, 1.89020	46.16970, 1.87147	
2	2830	N/A	BT
1670 m
46.14389, 1.86632	HTA
6737 m
46.18289, 1.89020	46.13028, 1.85993	
3	2070	N/A	BT
622 m
46.14813, 1.86658	HTA
5159 m
46.18289, 1.89020	46.14656, 1.86120	
4	713	N/A	BT
440 m
46.15325, 1.87327	HTA
3921 m
46.18289, 1.89020	46.15049, 1.87611	
5	859	
000BY0105
BT
38 m
46.15614, 1.86872	HTA
3790 m
46.18289, 1.89020	46.15607, 1.86906	
6	1666	N/A	BT
55 m
46.15781, 1.86779	HTA
3731 m
46.18289, 1.89020	46.15749, 1.86817	
7	582	
000BY0353
BT
64 m
46.15908, 1.87264	HTA
3347 m
46.18289, 1.89020	46.15859, 1.87235	
8	2850	N/A	BT
106 m
46.15781, 1.86779	HTA
3746 m
46.18289, 1.89020	46.15836, 1.86701	
9	9130	N/A	BT
189 m
46.15997, 1.88399	HTA
2738 m
46.18289, 1.89020	46.15950, 1.88235	
10	914	N/A	BT
114 m
46.16774, 1.88744	HTA
1823 m
46.18289, 1.89020	46.16672, 1.88727	
11	4467	N/A	BT
100 m
46.15992, 1.87248	HTA
3120 m
46.18289, 1.89020	46.16061, 1.87307	
12	1568	N/A	BT
135 m
46.16199, 1.87483	HTA
2816 m
46.18289, 1.89020	46.16309, 1.87432	
13	5701	N/A	BT
158 m
46.16519, 1.87330	HTA
2860 m
46.18289, 1.89020	46.16383, 1.87286	
14	503	N/A	BT
33 m
46.16483, 1.88120	HTA
2228 m
46.18289, 1.89020	46.16480, 1.88150	
15	1142	N/A	BT
9 m
46.16478, 1.86996	HTA
3023 m
46.18289, 1.89020	46.16471, 1.86992	
16	2606	N/A	BT
88 m
46.16478, 1.86996	HTA
2925 m
46.18289, 1.89020	46.16526, 1.87060	
17	766	N/A	BT
87 m
46.16613, 1.87070	HTA
2831 m
46.18289, 1.89020	46.16570, 1.87136	
18	1014	N/A	BT
164 m
46.16581, 1.88667	HTA
1886 m
46.18289, 1.89020	46.16602, 1.88813	
19	920	N/A	BT
107 m
46.16581, 1.88667	HTA
1888 m
46.18289, 1.89020	46.16608, 1.88759	
20	1321	N/A	BT
94 m
46.16519, 1.87330	HTA
2623 m
46.18289, 1.89020	46.16586, 1.87382	
21	709	N/A	BT
140 m
46.16581, 1.88667	HTA
1862 m
46.18289, 1.89020	46.16628, 1.88783	
22	703	N/A	BT
120 m
46.16581, 1.88667	HTA
1874 m
46.18289, 1.89020	46.16656, 1.88589	
23	684	
000BP0007
BT
170 m
46.16790, 1.87186	HTA
2690 m
46.18289, 1.89020	46.16646, 1.87238	
24	10374	N/A	BT
87 m
46.16627, 1.85287	HTA
4621 m
46.18289, 1.89020	46.16588, 1.85219	
25	628	N/A	BT
42 m
46.16622, 1.86626	HTA
3197 m
46.18289, 1.89020	46.16651, 1.86650	
26	591	N/A	BT
123 m
46.16622, 1.86626	HTA
3300 m
46.18289, 1.89020	46.16670, 1.86526	
27	582	N/A	BT
47 m
46.16718, 1.87493	HTA
2478 m
46.18289, 1.89020	46.16682, 1.87470	
28	2177	N/A	BT
172 m
46.16519, 1.87330	HTA
2637 m
46.18289, 1.89020	46.16667, 1.87284	
29	1405	N/A	BT
153 m
46.16718, 1.87493	HTA
2572 m
46.18289, 1.89020	46.16667, 1.87365	
30	583	N/A	BT
91 m
46.16611, 1.86963	HTA
2885 m
46.18289, 1.89020	46.16693, 1.86968	
31	2284	N/A	BT
158 m
46.16832, 1.87341	HTA
2591 m
46.18289, 1.89020	46.16691, 1.87318	
32	517	N/A	BT
218 m
46.16833, 1.88609	HTA
1821 m
46.18289, 1.89020	46.16759, 1.88427	
33	512	N/A	BT
26 m
46.16774, 1.88744	HTA
1685 m
46.18289, 1.89020	46.16793, 1.88757	
34	10660	N/A	BT
130 m
46.16833, 1.88609	HTA
1791 m
46.18289, 1.89020	46.16754, 1.88523	
35	4061	N/A	BT
54 m
46.16790, 1.87186	HTA
2682 m
46.18289, 1.89020	46.16763, 1.87146	
36	1187	N/A	BT
33 m
46.16841, 1.87248	HTA
2559 m
46.18289, 1.89020	46.16811, 1.87250	
37	582	N/A	BT
41 m
46.16832, 1.87341	HTA
2432 m
46.18289, 1.89020	46.16839, 1.87377	
38	1060	N/A	BT
112 m
46.16956, 1.88390	HTA
1726 m
46.18289, 1.89020	46.16858, 1.88411	
39	5135	N/A	BT
60 m
46.16803, 1.88730	HTA
1641 m
46.18289, 1.89020	46.16831, 1.88777	
40	1476	N/A	BT
90 m
46.16956, 1.88390	HTA
1722 m
46.18289, 1.89020	46.16876, 1.88379	
41	1662	N/A	BT
74 m
46.16901, 1.85756	HTA
4002 m
46.18289, 1.89020	46.16849, 1.85714	
42	7569	N/A	BT
108 m
46.16790, 1.87186	HTA
2629 m
46.18289, 1.89020	46.16867, 1.87126	
43	876	N/A	BT
56 m
46.16961, 1.87173	HTA
2571 m
46.18289, 1.89020	46.16914, 1.87155	
44	880	N/A	BT
88 m
46.16876, 1.88636	HTA
1541 m
46.18289, 1.89020	46.16954, 1.88635	
45	1230	N/A	BT
29 m
46.16963, 1.86758	HTA
2936 m
46.18289, 1.89020	46.16959, 1.86733	
46	767	N/A	BT
23 m
46.16961, 1.87399	HTA
2308 m
46.18289, 1.89020	46.16961, 1.87420	
47	1642	N/A	BT
66 m
46.17084, 1.87046	HTA
2579 m
46.18289, 1.89020	46.17029, 1.87067	
48	706	N/A	BT
40 m
46.17058, 1.87406	HTA
2258 m
46.18289, 1.89020	46.17027, 1.87424	
49	7287	N/A	BT
68 m
46.16956, 1.88390	HTA
1568 m
46.18289, 1.89020	46.17011, 1.88417	
50	637	N/A	BT
167 m
46.16956, 1.88390	HTA
1485 m
46.18289, 1.89020	46.17053, 1.88505	
51	12931	N/A	BT
32 m
46.17010, 1.88292	HTA
1607 m
46.18289, 1.89020	46.17023, 1.88317	
52	671	N/A	BT
70 m
46.17063, 1.86653	HTA
2889 m
46.18289, 1.89020	46.17079, 1.86715	
53	1705	N/A	BT
194 m
46.17198, 1.88152	HTA
1737 m
46.18289, 1.89020	46.17089, 1.88015	
54	737	N/A	BT
142 m
46.16963, 1.86758	HTA
2793 m
46.18289, 1.89020	46.17078, 1.86814	
55	2619	N/A	BT
72 m
46.17058, 1.87406	HTA
2260 m
46.18289, 1.89020	46.17106, 1.87363	
56	1063	N/A	BT
122 m
46.17219, 1.87207	HTA
2371 m
46.18289, 1.89020	46.17113, 1.87236	
57	724	N/A	BT
99 m
46.17198, 1.88152	HTA
1645 m
46.18289, 1.89020	46.17135, 1.88089	
58	970	N/A	BT
97 m
46.17063, 1.86653	HTA
2938 m
46.18289, 1.89020	46.17148, 1.86631	
59	644	N/A	BT
196 m
46.17198, 1.88152	HTA
1434 m
46.18289, 1.89020	46.17198, 1.88328	
60	560	N/A	BT
128 m
46.17097, 1.87451	HTA
2144 m
46.18289, 1.89020	46.17208, 1.87419	
61	915	N/A	BT
20 m
46.17202, 1.86851	HTA
2704 m
46.18289, 1.89020	46.17211, 1.86835	
62	2180	N/A	BT
67 m
46.17198, 1.88152	HTA
1486 m
46.18289, 1.89020	46.17225, 1.88206	
63	885	N/A	BT
34 m
46.17330, 1.87393	HTA
2076 m
46.18289, 1.89020	46.17318, 1.87421	
64	4496	N/A	BT
142 m
46.17198, 1.88152	HTA
1476 m
46.18289, 1.89020	46.17319, 1.88110	
65	2608	N/A	BT
83 m
46.17330, 1.87393	HTA
2095 m
46.18289, 1.89020	46.17396, 1.87357	
66	1301	N/A	BT
79 m
46.17360, 1.87049	HTA
2371 m
46.18289, 1.89020	46.17430, 1.87064	
67	1366	N/A	BT
174 m
46.17486, 1.87338	HTA
2241 m
46.18289, 1.89020	46.17436, 1.87190	
68	1815	N/A	BT
122 m
46.17565, 1.87072	HTA
2296 m
46.18289, 1.89020	46.17467, 1.87121	
69	699	N/A	BT
216 m
46.17627, 1.86120	HTA
3202 m
46.18289, 1.89020	46.17482, 1.86250	
70	2171	N/A	BT
74 m
46.17565, 1.87072	HTA
2258 m
46.18289, 1.89020	46.17533, 1.87131	
71	672	N/A	BT
50 m
46.17579, 1.89285	HTA
840 m
46.18289, 1.89020	46.17597, 1.89326	
72	512	N/A	BT
36 m
46.17942, 1.86630	HTA
2647 m
46.18289, 1.89020	46.17934, 1.86662	
73	1537	N/A	BT
207 m
46.17486, 1.87338	HTA
1869 m
46.18289, 1.89020	46.17607, 1.87481	
74	1445	N/A	BT
77 m
46.17565, 1.87072	HTA
2343 m
46.18289, 1.89020	46.17612, 1.87020	
75	612	N/A	BT
94 m
46.17611, 1.87161	HTA
2251 m
46.18289, 1.89020	46.17659, 1.87092	
76	2820	N/A	BT
10 m
46.17611, 1.87161	HTA
2192 m
46.18289, 1.89020	46.17605, 1.87167	
77	2556	N/A	BT
91 m
46.17611, 1.87161	HTA
2107 m
46.18289, 1.89020	46.17625, 1.87241	
78	2070	N/A	BT
84 m
46.17718, 1.87696	HTA
1677 m
46.18289, 1.89020	46.17719, 1.87620	
79	689	N/A	BT
127 m
46.17718, 1.87696	HTA
1477 m
46.18289, 1.89020	46.17737, 1.87809	
80	7810	N/A	BT
56 m
46.17763, 1.87146	HTA
2216 m
46.18289, 1.89020	46.17752, 1.87096	
81	688	N/A	BT
89 m
46.17764, 1.86259	HTA
3036 m
46.18289, 1.89020	46.17804, 1.86328	
82	1081	N/A	BT
191 m
46.17764, 1.86259	HTA
2929 m
46.18289, 1.89020	46.17778, 1.86431	
83	895	N/A	BT
121 m
46.17806, 1.89176	HTA
499 m
46.18289, 1.89020	46.17842, 1.89073	
84	1199	N/A	BT
71 m
46.17764, 1.86259	HTA
3153 m
46.18289, 1.89020	46.17813, 1.86219	
85	600	N/A	BT
127 m
46.17953, 1.87761	HTA
1395 m
46.18289, 1.89020	46.17867, 1.87836	
86	528	N/A	BT
112 m
46.17861, 1.87967	HTA
1149 m
46.18289, 1.89020	46.17897, 1.88061	
87	725	N/A	BT
48 m
46.17888, 1.86670	HTA
2599 m
46.18289, 1.89020	46.17887, 1.86713	
88	1034	N/A	BT
33 m
46.17924, 1.87028	HTA
2259 m
46.18289, 1.89020	46.17895, 1.87023	
89	1062	N/A	BT
69 m
46.17953, 1.87761	HTA
1409 m
46.18289, 1.89020	46.17912, 1.87807	
90	708	N/A	BT
52 m
46.17942, 1.86630	HTA
2730 m
46.18289, 1.89020	46.17918, 1.86589	
91	683	N/A	BT
91 m
46.17861, 1.87967	HTA
1195 m
46.18289, 1.89020	46.17934, 1.88003	
92	15763	N/A	BT
111 m
46.17953, 1.87761	HTA
1527 m
46.18289, 1.89020	46.17868, 1.87710	
93	1160	N/A	BT
155 m
46.18057, 1.87354	HTA
1973 m
46.18289, 1.89020	46.17941, 1.87276	
94	3111	N/A	BT
139 m
46.17953, 1.87761	HTA
1308 m
46.18289, 1.89020	46.17971, 1.87885	
95	1679	N/A	BT
96 m
46.17942, 1.86630	HTA
2591 m
46.18289, 1.89020	46.17984, 1.86706	
96	4034	N/A	BT
54 m
46.17953, 1.87761	HTA
1438 m
46.18289, 1.89020	46.18001, 1.87756	
97	2645	N/A	BT
66 m
46.18067, 1.87530	HTA
1632 m
46.18289, 1.89020	46.18026, 1.87573	
98	2424	N/A	BT
149 m
46.17976, 1.88473	HTA
750 m
46.18289, 1.89020	46.18072, 1.88380	
99	640	N/A	BT
116 m
46.17984, 1.87705	HTA
1544 m
46.18289, 1.89020	46.18070, 1.87646	
100	2304	N/A	BT
59 m
46.18067, 1.87530	HTA
1728 m
46.18289, 1.89020	46.18075, 1.87477	
101	1734	N/A	BT
63 m
46.18067, 1.87530	HTA
1654 m
46.18289, 1.89020	46.18123, 1.87539	
102	1680	N/A	BT
197 m
46.18035, 1.88096	HTA
1186 m
46.18289, 1.89020	46.18151, 1.87960	
103	1579	N/A	BT
52 m
46.18208, 1.88396	HTA
698 m
46.18289, 1.89020	46.18162, 1.88403	
104	1512	N/A	BT
150 m
46.18208, 1.88396	HTA
848 m
46.18289, 1.89020	46.18191, 1.88262	
105	2950	N/A	BT
194 m
46.18208, 1.88396	HTA
511 m
46.18289, 1.89020	46.18190, 1.88570	
106	3641	N/A	BT
89 m
46.18208, 1.88396	HTA
781 m
46.18289, 1.89020	46.18230, 1.88319	
107	2738	N/A	BT
29 m
46.18208, 1.88396	HTA
693 m
46.18289, 1.89020	46.18234, 1.88398	
108	1083	N/A	BT
74 m
46.18326, 1.88718	HTA
311 m
46.18289, 1.89020	46.18263, 1.88741	
109	4656	N/A	BT
171 m
46.18326, 1.88718	HTA
493 m
46.18289, 1.89020	46.18266, 1.88576	
110	11621	
000ZA0108
BT
138 m
46.18247, 1.88940	HTA
201 m
46.18289, 1.89020	46.18322, 1.88842	
111	1121	N/A	BT
275 m
46.18592, 1.87445	HTA
1599 m
46.18289, 1.89020	46.18386, 1.87583	
112	1182	N/A	BT
154 m
46.18869, 1.87337	HTA
2036 m
46.18289, 1.89020	46.18762, 1.87248	
113	670	N/A	BT
37 m
46.18862, 1.87973	HTA
1343 m
46.18289, 1.89020	46.18844, 1.87944	
114	3539	N/A	BT
181 m
46.18967, 1.89674	HTA
1222 m
46.18289, 1.89020	46.19052, 1.89814	
 Analyse Friches
8 friches identifiées
Surface totale: 0.0 ha
Potentiel de reconversion: 0.0 ha

Détails des friches (8)
#	Surface (ha)	Parcelles	BT le plus proche	HTA le plus proche	Position	Liens
1	0.00	N/A	BT
230 m
46.19919, 1.88951	HTA
1584 m
46.18289, 1.89020	46.19715, 1.88987	
2	0.00	N/A	BT
197 m
46.19432, 1.87825	HTA
2022 m
46.18289, 1.89020	46.19503, 1.87662	
3	0.00	N/A	BT
7 m
46.17024, 1.85948	HTA
3694 m
46.18289, 1.89020	46.17024, 1.85941	
4	0.00	N/A	BT
121 m
46.19534, 1.88075	HTA
1678 m
46.18289, 1.89020	46.19433, 1.88032	
5	0.00	N/A	BT
500 m
46.14813, 1.86658	HTA
4988 m
46.18289, 1.89020	46.14783, 1.86209	
6	0.00	N/A	BT
197 m
46.19432, 1.87825	HTA
2022 m
46.18289, 1.89020	46.19503, 1.87662	
7	0.00	N/A	BT
79 m
46.16840, 1.86982	HTA
2729 m
46.18289, 1.89020	46.16911, 1.86983	
8	0.00	N/A	BT
79 m
46.16840, 1.86982	HTA
2729 m
46.18289, 1.89020	46.16911, 1.86983	
 Analyse Toitures
Potentiel global:
Bâtiments: 3214
Surface exploitable: 665058 m²

Capacité installable:
Puissance: 133.0 MWc
Production: 159614 MWh/an

Typologie:
Détails des toitures (200)
#	Surface (m²)	Parcelles	BT le plus proche	HTA le plus proche	Position	Liens
1	658	N/A	BT
44 m
46.17372, 1.87927	HTA
1558 m
46.18289, 1.89020	46.17411, 1.87924	 
2	120	N/A	BT
162 m
46.17565, 1.87072	HTA
2458 m
46.18289, 1.89020	46.17566, 1.86926	 
3	637	N/A	BT
205 m
46.17372, 1.87927	HTA
1703 m
46.18289, 1.89020	46.17425, 1.87751	 
4	109	N/A	BT
45 m
46.16613, 1.87070	HTA
2897 m
46.18289, 1.89020	46.16578, 1.87049	 
5	126	N/A	BT
314 m
46.17942, 1.86630	HTA
2462 m
46.18289, 1.89020	46.18163, 1.86805	 
6	113	N/A	BT
142 m
46.17861, 1.87967	HTA
1404 m
46.18289, 1.89020	46.17815, 1.87847	 
7	116	N/A	BT
120 m
46.17549, 1.88781	HTA
962 m
46.18289, 1.89020	46.17486, 1.88693	 
8	112	N/A	BT
110 m
46.18869, 1.87337	HTA
1972 m
46.18289, 1.89020	46.18960, 1.87375	 
9	155	N/A	BT
146 m
46.17198, 1.88152	HTA
1693 m
46.18289, 1.89020	46.17090, 1.88077	 
10	140	N/A	BT
229 m
46.17358, 1.88593	HTA
1365 m
46.18289, 1.89020	46.17177, 1.88494	 
11	139	N/A	BT
29 m
46.17084, 1.87046	HTA
2594 m
46.18289, 1.89020	46.17079, 1.87021	 
12	269	N/A	BT
111 m
46.16718, 1.87493	HTA
2512 m
46.18289, 1.89020	46.16715, 1.87393	 
13	864	N/A	BT
159 m
46.18592, 1.87445	HTA
1625 m
46.18289, 1.89020	46.18534, 1.87576	 
14	145	N/A	BT
78 m
46.16970, 1.88149	HTA
1763 m
46.18289, 1.89020	46.17003, 1.88087	 
15	172	N/A	BT
43 m
46.18640, 1.87816	HTA
1384 m
46.18289, 1.89020	46.18674, 1.87834	 
16	214	N/A	BT
240 m
46.18318, 1.88167	HTA
1157 m
46.18289, 1.89020	46.18440, 1.87988	 
17	105	N/A	BT
132 m
46.17202, 1.86851	HTA
2798 m
46.18289, 1.89020	46.17093, 1.86801	 
18	162	N/A	BT
72 m
46.17023, 1.87838	HTA
1907 m
46.18289, 1.89020	46.16990, 1.87894	 
19	214	N/A	BT
147 m
46.16963, 1.86758	HTA
2785 m
46.18289, 1.89020	46.16962, 1.86891	 
20	136	
000BC0105
BT
181 m
46.17063, 1.86653	HTA
2951 m
46.18289, 1.89020	46.17212, 1.86588	 
21	101	N/A	BT
59 m
46.17038, 1.87328	HTA
2354 m
46.18289, 1.89020	46.17069, 1.87285	 
22	112	N/A	BT
285 m
46.19532, 1.87453	HTA
2161 m
46.18289, 1.89020	46.19683, 1.87661	 
23	121	N/A	BT
137 m
46.17274, 1.86070	HTA
3460 m
46.18289, 1.89020	46.17159, 1.86114	 
24	171	N/A	BT
81 m
46.17486, 1.87338	HTA
2024 m
46.18289, 1.89020	46.17558, 1.87349	 
25	103	N/A	BT
229 m
46.16230, 1.87769	HTA
2528 m
46.18289, 1.89020	46.16427, 1.87707	 
26	145	N/A	BT
52 m
46.16483, 1.88120	HTA
2196 m
46.18289, 1.89020	46.16530, 1.88114	 
27	107	N/A	BT
257 m
46.15997, 1.88399	HTA
2437 m
46.18289, 1.89020	46.16137, 1.88584	 
28	100	N/A	BT
51 m
46.15920, 1.87444	HTA
3150 m
46.18289, 1.89020	46.15901, 1.87486	 
29	110	N/A	BT
201 m
46.17097, 1.87451	HTA
2152 m
46.18289, 1.89020	46.16980, 1.87589	 
30	286	N/A	BT
117 m
46.19270, 1.87471	HTA
1980 m
46.18289, 1.89020	46.19319, 1.87564	 
31	474	N/A	BT
178 m
46.17819, 1.87485	HTA
1851 m
46.18289, 1.89020	46.17659, 1.87476	 
32	111	N/A	BT
197 m
46.17724, 1.88441	HTA
800 m
46.18289, 1.89020	46.17693, 1.88615	 
33	749	N/A	BT
151 m
46.17924, 1.87028	HTA
2393 m
46.18289, 1.89020	46.17864, 1.86906	 
34	126	N/A	BT
216 m
46.15992, 1.87248	HTA
3402 m
46.18289, 1.89020	46.15929, 1.87064	 
35	126	
000AY0526
BT
215 m
46.17486, 1.87338	HTA
1878 m
46.18289, 1.89020	46.17482, 1.87533	 
36	156	N/A	BT
60 m
46.16519, 1.87330	HTA
2769 m
46.18289, 1.89020	46.16501, 1.87280	 
37	138	N/A	BT
105 m
46.17917, 1.88265	HTA
932 m
46.18289, 1.89020	46.18005, 1.88229	 
38	111	N/A	BT
170 m
46.17549, 1.88781	HTA
793 m
46.18289, 1.89020	46.17580, 1.88931	 
39	338	N/A	BT
35 m
46.17092, 1.86945	HTA
2690 m
46.18289, 1.89020	46.17066, 1.86927	 
40	415	N/A	BT
152 m
46.19432, 1.87825	HTA
1897 m
46.18289, 1.89020	46.19375, 1.87700	 
41	100	N/A	BT
61 m
46.17976, 1.88473	HTA
651 m
46.18289, 1.89020	46.18026, 1.88495	 
42	123	N/A	BT
111 m
46.17358, 1.88593	HTA
1204 m
46.18289, 1.89020	46.17339, 1.88495	 
43	105	N/A	BT
79 m
46.17764, 1.86259	HTA
3086 m
46.18289, 1.89020	46.17706, 1.86301	 
44	245	N/A	BT
228 m
46.16627, 1.85287	HTA
4677 m
46.18289, 1.89020	46.16725, 1.85107	 
45	1263	N/A	BT
47 m
46.19452, 1.87207	HTA
2394 m
46.18289, 1.89020	46.19418, 1.87182	 
46	421	
000AH0100
BT
105 m
46.18192, 1.89756	HTA
752 m
46.18289, 1.89020	46.18266, 1.89697	 
47	120	N/A	BT
129 m
46.17202, 1.87593	HTA
1962 m
46.18289, 1.89020	46.17131, 1.87685	 
48	173	N/A	BT
117 m
46.17084, 1.87046	HTA
2643 m
46.18289, 1.89020	46.16980, 1.87030	 
49	197	N/A	BT
100 m
46.17024, 1.85948	HTA
3766 m
46.18289, 1.89020	46.16946, 1.85904	 
50	355	N/A	BT
67 m
46.17202, 1.86851	HTA
2650 m
46.18289, 1.89020	46.17179, 1.86906	 
51	102	N/A	BT
80 m
46.17063, 1.86653	HTA
2878 m
46.18289, 1.89020	46.17102, 1.86714	 
52	1381	N/A	BT
131 m
46.17330, 1.87393	HTA
2215 m
46.18289, 1.89020	46.17232, 1.87327	 
53	106	N/A	BT
33 m
46.17024, 1.85948	HTA
3692 m
46.18289, 1.89020	46.17050, 1.85933	 
54	105	
000BH0010
BT
144 m
46.16961, 1.87173	HTA
2419 m
46.18289, 1.89020	46.17089, 1.87201	 
55	102	N/A	BT
117 m
46.15997, 1.88399	HTA
2580 m
46.18289, 1.89020	46.16022, 1.88502	 
56	104	N/A	BT
135 m
46.17997, 1.86506	HTA
2941 m
46.18289, 1.89020	46.18011, 1.86385	 
57	227	N/A	BT
228 m
46.16199, 1.87483	HTA
2906 m
46.18289, 1.89020	46.16307, 1.87308	 
58	139	N/A	BT
105 m
46.17897, 1.86133	HTA
3330 m
46.18289, 1.89020	46.17847, 1.86052	 
59	106	
000AV0109
BT
169 m
46.17549, 1.88781	HTA
783 m
46.18289, 1.89020	46.17668, 1.88685	 
60	164	N/A	BT
34 m
46.15920, 1.87444	HTA
3160 m
46.18289, 1.89020	46.15936, 1.87417	 
61	106	N/A	BT
103 m
46.17202, 1.87593	HTA
1994 m
46.18289, 1.89020	46.17275, 1.87536	 
62	143	N/A	BT
223 m
46.17904, 1.88677	HTA
540 m
46.18289, 1.89020	46.17828, 1.88863	 
63	163	N/A	BT
158 m
46.16483, 1.88120	HTA
2319 m
46.18289, 1.89020	46.16478, 1.87978	 
64	1179	N/A	BT
134 m
46.16199, 1.87483	HTA
2854 m
46.18289, 1.89020	46.16289, 1.87404	 
65	108	N/A	BT
126 m
46.14389, 1.86632	HTA
4952 m
46.18289, 1.89020	46.14496, 1.86671	 
66	372	N/A	BT
196 m
46.19270, 1.87471	HTA
1932 m
46.18289, 1.89020	46.19341, 1.87633	 
67	142	
000BD0010
BT
81 m
46.17202, 1.86851	HTA
2774 m
46.18289, 1.89020	46.17167, 1.86786	 
68	233	N/A	BT
192 m
46.16611, 1.86963	HTA
3137 m
46.18289, 1.89020	46.16517, 1.86817	 
69	159	N/A	BT
36 m
46.19532, 1.87453	HTA
2231 m
46.18289, 1.89020	46.19513, 1.87426	 
70	122	N/A	BT
72 m
46.17976, 1.88473	HTA
706 m
46.18289, 1.89020	46.17918, 1.88502	 
71	226	N/A	BT
57 m
46.17202, 1.87593	HTA
1969 m
46.18289, 1.89020	46.17177, 1.87638	 
72	194	N/A	BT
161 m
46.17360, 1.87049	HTA
2260 m
46.18289, 1.89020	46.17398, 1.87189	 
73	131	N/A	BT
105 m
46.16851, 1.86368	HTA
3365 m
46.18289, 1.89020	46.16927, 1.86312	 
74	114	N/A	BT
586 m
46.16627, 1.85287	HTA
4913 m
46.18289, 1.89020	46.16878, 1.84824	 
75	475	N/A	BT
112 m
46.16804, 1.86915	HTA
2839 m
46.18289, 1.89020	46.16734, 1.86988	 
76	117	N/A	BT
249 m
46.17360, 1.87049	HTA
2564 m
46.18289, 1.89020	46.17477, 1.86857	 
77	274	N/A	BT
17 m
46.16790, 1.87186	HTA
2631 m
46.18289, 1.89020	46.16777, 1.87194	 
78	100	N/A	BT
234 m
46.17627, 1.86120	HTA
3528 m
46.18289, 1.89020	46.17636, 1.85909	 
79	148	N/A	BT
180 m
46.18318, 1.88167	HTA
812 m
46.18289, 1.89020	46.18412, 1.88299	 
80	128	N/A	BT
138 m
46.17549, 1.88781	HTA
730 m
46.18289, 1.89020	46.17654, 1.88847	 
81	107	N/A	BT
76 m
46.16841, 1.87248	HTA
2576 m
46.18289, 1.89020	46.16774, 1.87262	 
82	160	N/A	BT
215 m
46.17888, 1.86670	HTA
2495 m
46.18289, 1.89020	46.17779, 1.86830	 
83	133	N/A	BT
120 m
46.17904, 1.88677	HTA
455 m
46.18289, 1.89020	46.17970, 1.88762	 
84	115	N/A	BT
46 m
46.17198, 1.88152	HTA
1582 m
46.18289, 1.89020	46.17190, 1.88111	 
85	307	N/A	BT
104 m
46.17141, 1.86365	HTA
3197 m
46.18289, 1.89020	46.17062, 1.86414	 
86	101	N/A	BT
257 m
46.18192, 1.89756	HTA
1023 m
46.18289, 1.89020	46.18333, 1.89941	 
87	103	N/A	BT
132 m
46.16961, 1.87399	HTA
2302 m
46.18289, 1.89020	46.16886, 1.87492	 
88	102	N/A	BT
85 m
46.16622, 1.86626	HTA
3168 m
46.18289, 1.89020	46.16624, 1.86702	 
89	159	N/A	BT
95 m
46.17372, 1.87927	HTA
1606 m
46.18289, 1.89020	46.17296, 1.87967	 
90	189	N/A	BT
64 m
46.16963, 1.86758	HTA
2879 m
46.18289, 1.89020	46.17020, 1.86758	 
91	114	N/A	BT
49 m
46.15997, 1.88399	HTA
2681 m
46.18289, 1.89020	46.15962, 1.88372	 
92	106	N/A	BT
245 m
46.16258, 1.88255	HTA
2169 m
46.18289, 1.89020	46.16444, 1.88375	 
93	402	N/A	BT
70 m
46.16804, 1.86915	HTA
2844 m
46.18289, 1.89020	46.16762, 1.86962	 
94	115	N/A	BT
40 m
46.17861, 1.87967	HTA
1300 m
46.18289, 1.89020	46.17856, 1.87931	 
95	187	N/A	BT
154 m
46.17724, 1.88441	HTA
1042 m
46.18289, 1.89020	46.17671, 1.88313	 
96	135	N/A	BT
86 m
46.16963, 1.86758	HTA
2826 m
46.18289, 1.89020	46.16984, 1.86833	 
97	150	N/A	BT
514 m
46.16273, 1.86622	HTA
3982 m
46.18289, 1.89020	46.16053, 1.86214	 
98	352	N/A	BT
106 m
46.16840, 1.86982	HTA
2712 m
46.18289, 1.89020	46.16812, 1.87073	 
99	128	N/A	BT
276 m
46.16833, 1.88609	HTA
1905 m
46.18289, 1.89020	46.16685, 1.88409	 
100	200	N/A	BT
213 m
46.17024, 1.85948	HTA
3499 m
46.18289, 1.89020	46.17008, 1.86139	 
101	103	N/A	BT
48 m
46.17657, 1.86601	HTA
2822 m
46.18289, 1.89020	46.17648, 1.86559	 
102	108	N/A	BT
60 m
46.16581, 1.88667	HTA
1993 m
46.18289, 1.89020	46.16534, 1.88639	 
103	749	N/A	BT
198 m
46.18635, 1.86933	HTA
2337 m
46.18289, 1.89020	46.18807, 1.86979	 
104	415	N/A	BT
116 m
46.17358, 1.88593	HTA
1027 m
46.18289, 1.89020	46.17435, 1.88664	 
105	176	N/A	BT
105 m
46.16199, 1.87483	HTA
2920 m
46.18289, 1.89020	46.16118, 1.87533	 
106	134	N/A	BT
229 m
46.19452, 1.87207	HTA
2610 m
46.18289, 1.89020	46.19504, 1.87007	 
107	124	N/A	BT
171 m
46.17531, 1.88196	HTA
1351 m
46.18289, 1.89020	46.17560, 1.88044	 
108	231	N/A	BT
64 m
46.17198, 1.88152	HTA
1517 m
46.18289, 1.89020	46.17251, 1.88129	 
109	100	N/A	BT
67 m
46.18035, 1.88096	HTA
997 m
46.18289, 1.89020	46.18058, 1.88151	 
110	150	N/A	BT
93 m
46.16782, 1.87797	HTA
2123 m
46.18289, 1.89020	46.16755, 1.87876	 
111	112	N/A	BT
102 m
46.17141, 1.86365	HTA
3261 m
46.18289, 1.89020	46.17049, 1.86356	 
112	203	N/A	BT
140 m
46.18318, 1.88167	HTA
1066 m
46.18289, 1.89020	46.18394, 1.88065	 
113	103	N/A	BT
58 m
46.17202, 1.86851	HTA
2714 m
46.18289, 1.89020	46.17150, 1.86856	 
114	288	N/A	BT
103 m
46.17063, 1.86653	HTA
3061 m
46.18289, 1.89020	46.17012, 1.86576	 
115	100	N/A	BT
111 m
46.16611, 1.86963	HTA
2957 m
46.18289, 1.89020	46.16683, 1.86895	 
116	109	N/A	BT
162 m
46.17549, 1.88781	HTA
918 m
46.18289, 1.89020	46.17557, 1.88635	 
117	128	
000BH0100
BT
71 m
46.16918, 1.87246	HTA
2423 m
46.18289, 1.89020	46.16975, 1.87276	 
118	115	N/A	BT
172 m
46.16650, 1.88156	HTA
1925 m
46.18289, 1.89020	46.16711, 1.88298	 
119	468	N/A	BT
167 m
46.17330, 1.87393	HTA
1941 m
46.18289, 1.89020	46.17449, 1.87486	 
120	118	
000BM0033
BT
283 m
46.16650, 1.88156	HTA
1944 m
46.18289, 1.89020	46.16646, 1.88411	 
121	117	N/A	BT
23 m
46.15920, 1.87444	HTA
3167 m
46.18289, 1.89020	46.15903, 1.87455	 
122	140	N/A	BT
74 m
46.16790, 1.87186	HTA
2624 m
46.18289, 1.89020	46.16742, 1.87232	 
123	1617	N/A	BT
45 m
46.19296, 1.87207	HTA
2331 m
46.18289, 1.89020	46.19281, 1.87169	 
124	104	N/A	BT
179 m
46.16519, 1.87330	HTA
2894 m
46.18289, 1.89020	46.16388, 1.87236	 
125	107	
000AO0105
BT
75 m
46.17997, 1.86506	HTA
2775 m
46.18289, 1.89020	46.18060, 1.86530	 
126	102	N/A	BT
167 m
46.16258, 1.88255	HTA
2496 m
46.18289, 1.89020	46.16234, 1.88107	 
127	220	N/A	BT
70 m
46.17549, 1.88781	HTA
849 m
46.18289, 1.89020	46.17544, 1.88844	 
128	174	N/A	BT
145 m
46.17198, 1.88152	HTA
1678 m
46.18289, 1.89020	46.17144, 1.88033	 
129	153	N/A	BT
173 m
46.19426, 1.86738	HTA
2663 m
46.18289, 1.89020	46.19396, 1.86892	 
130	116	N/A	BT
59 m
46.18035, 1.88096	HTA
1024 m
46.18289, 1.89020	46.18008, 1.88141	 
131	104	N/A	BT
69 m
46.16970, 1.88149	HTA
1796 m
46.18289, 1.89020	46.16967, 1.88086	 
132	330	N/A	BT
94 m
46.16627, 1.85287	HTA
4445 m
46.18289, 1.89020	46.16638, 1.85372	 
133	373	N/A	BT
154 m
46.17202, 1.87593	HTA
1953 m
46.18289, 1.89020	46.17120, 1.87705	 
134	187	N/A	BT
114 m
46.15567, 1.85750	HTA
4762 m
46.18289, 1.89020	46.15619, 1.85661	 
135	342	N/A	BT
121 m
46.17360, 1.87049	HTA
2304 m
46.18289, 1.89020	46.17371, 1.87157	 
136	1473	N/A	BT
55 m
46.18208, 1.88396	HTA
666 m
46.18289, 1.89020	46.18172, 1.88431	 
137	385	N/A	BT
158 m
46.17372, 1.87927	HTA
1741 m
46.18289, 1.89020	46.17278, 1.87821	 
138	112	N/A	BT
241 m
46.15908, 1.87264	HTA
3452 m
46.18289, 1.89020	46.15884, 1.87048	 
139	143	N/A	BT
151 m
46.17486, 1.87338	HTA
2213 m
46.18289, 1.89020	46.17396, 1.87236	 
140	184	N/A	BT
148 m
46.16956, 1.88390	HTA
1766 m
46.18289, 1.89020	46.16823, 1.88401	 
141	120	N/A	BT
223 m
46.19426, 1.86738	HTA
2741 m
46.18289, 1.89020	46.19226, 1.86735	 
142	120	N/A	BT
45 m
46.17724, 1.88441	HTA
900 m
46.18289, 1.89020	46.17694, 1.88468	 
143	103	N/A	BT
135 m
46.16650, 1.88156	HTA
2090 m
46.18289, 1.89020	46.16571, 1.88248	 
144	147	N/A	BT
138 m
46.17486, 1.87338	HTA
1930 m
46.18289, 1.89020	46.17543, 1.87449	 
145	101	N/A	BT
207 m
46.16782, 1.87797	HTA
2182 m
46.18289, 1.89020	46.16652, 1.87931	 
146	130	N/A	BT
178 m
46.15674, 1.87201	HTA
3393 m
46.18289, 1.89020	46.15727, 1.87352	 
147	734	N/A	BT
102 m
46.17202, 1.87593	HTA
2087 m
46.18289, 1.89020	46.17124, 1.87544	 
148	175	N/A	BT
213 m
46.18635, 1.89336	HTA
675 m
46.18289, 1.89020	46.18624, 1.89527	 
149	100	N/A	BT
110 m
46.14813, 1.86658	HTA
4770 m
46.18289, 1.89020	46.14750, 1.86582	 
150	112	N/A	BT
72 m
46.19038, 1.88172	HTA
1298 m
46.18289, 1.89020	46.19022, 1.88109	 
151	151	N/A	BT
94 m
46.17092, 1.86945	HTA
2742 m
46.18289, 1.89020	46.17020, 1.86900	 
152	535	N/A	BT
221 m
46.19270, 1.87471	HTA
1849 m
46.18289, 1.89020	46.19265, 1.87669	 
153	113	N/A	BT
235 m
46.17358, 1.88593	HTA
1126 m
46.18289, 1.89020	46.17473, 1.88415	 
154	152	N/A	BT
124 m
46.17141, 1.86365	HTA
3089 m
46.18289, 1.89020	46.17164, 1.86474	 
155	108	N/A	BT
239 m
46.16627, 1.85287	HTA
4773 m
46.18289, 1.89020	46.16545, 1.85088	 
156	380	N/A	BT
52 m
46.19452, 1.87207	HTA
2356 m
46.18289, 1.89020	46.19464, 1.87252	 
157	169	N/A	BT
119 m
46.18035, 1.88096	HTA
984 m
46.18289, 1.89020	46.18130, 1.88147	 
158	109	N/A	BT
184 m
46.17202, 1.87593	HTA
2038 m
46.18289, 1.89020	46.17052, 1.87663	 
159	175	N/A	BT
77 m
46.17063, 1.86653	HTA
2984 m
46.18289, 1.89020	46.17110, 1.86603	 
160	115	N/A	BT
96 m
46.16199, 1.87483	HTA
2885 m
46.18289, 1.89020	46.16144, 1.87550	 
161	103	N/A	BT
187 m
46.16581, 1.88667	HTA
2084 m
46.18289, 1.89020	46.16474, 1.88536	 
162	106	N/A	BT
96 m
46.16611, 1.86963	HTA
2927 m
46.18289, 1.89020	46.16688, 1.86924	 
163	106	N/A	BT
117 m
46.17202, 1.86851	HTA
2748 m
46.18289, 1.89020	46.17264, 1.86766	 
164	326	N/A	BT
95 m
46.16963, 1.86758	HTA
2840 m
46.18289, 1.89020	46.16946, 1.86842	 
165	134	N/A	BT
185 m
46.15614, 1.86872	HTA
3979 m
46.18289, 1.89020	46.15534, 1.86726	 
166	112	N/A	BT
129 m
46.17406, 1.86552	HTA
2994 m
46.18289, 1.89020	46.17465, 1.86451	 
167	422	N/A	BT
42 m
46.17058, 1.87406	HTA
2294 m
46.18289, 1.89020	46.17034, 1.87377	 
168	156	N/A	BT
114 m
46.16155, 1.87164	HTA
3067 m
46.18289, 1.89020	46.16256, 1.87149	 
169	108	N/A	BT
29 m
46.17819, 1.87485	HTA
1768 m
46.18289, 1.89020	46.17800, 1.87503	 
170	123	N/A	BT
168 m
46.17888, 1.86670	HTA
2517 m
46.18289, 1.89020	46.17815, 1.86802	 
171	311	N/A	BT
136 m
46.17084, 1.87046	HTA
2543 m
46.18289, 1.89020	46.17200, 1.87004	 
172	148	N/A	BT
125 m
46.16832, 1.87341	HTA
2364 m
46.18289, 1.89020	46.16847, 1.87452	 
173	214	N/A	BT
237 m
46.19051, 1.87229	HTA
2261 m
46.18289, 1.89020	46.18901, 1.87077	 
174	138	N/A	BT
108 m
46.17904, 1.88677	HTA
569 m
46.18289, 1.89020	46.17849, 1.88757	 
175	330	N/A	BT
131 m
46.18067, 1.87530	HTA
1659 m
46.18289, 1.89020	46.17953, 1.87564	 
176	311	N/A	BT
116 m
46.17092, 1.86945	HTA
2775 m
46.18289, 1.89020	46.17040, 1.86854	 
177	122	N/A	BT
177 m
46.16217, 1.86863	HTA
3271 m
46.18289, 1.89020	46.16140, 1.87003	 
178	255	N/A	BT
103 m
46.17372, 1.87927	HTA
1628 m
46.18289, 1.89020	46.17283, 1.87953	 
179	107	N/A	BT
191 m
46.17063, 1.86653	HTA
2872 m
46.18289, 1.89020	46.17235, 1.86656	 
180	125	N/A	BT
159 m
46.15997, 1.88399	HTA
2772 m
46.18289, 1.89020	46.15899, 1.88294	 
181	1872	N/A	BT
127 m
46.17861, 1.87967	HTA
1317 m
46.18289, 1.89020	46.17941, 1.87885	 
182	161	N/A	BT
139 m
46.17724, 1.88441	HTA
1008 m
46.18289, 1.89020	46.17599, 1.88429	 
183	114	N/A	BT
87 m
46.17202, 1.86851	HTA
2646 m
46.18289, 1.89020	46.17280, 1.86860	 
184	270	N/A	BT
141 m
46.17360, 1.87049	HTA
2298 m
46.18289, 1.89020	46.17347, 1.87175	 
185	107	N/A	BT
236 m
46.17718, 1.87696	HTA
1821 m
46.18289, 1.89020	46.17567, 1.87547	 
186	130	N/A	BT
72 m
46.16782, 1.87797	HTA
2171 m
46.18289, 1.89020	46.16810, 1.87739	 
187	128	N/A	BT
216 m
46.16519, 1.87330	HTA
2931 m
46.18289, 1.89020	46.16365, 1.87211	 
188	112	N/A	BT
211 m
46.17861, 1.87967	HTA
1413 m
46.18289, 1.89020	46.17682, 1.87900	 
189	192	
000AP0270
BT
142 m
46.17565, 1.87072	HTA
2392 m
46.18289, 1.89020	46.17637, 1.86966	 
190	2771	N/A	BT
168 m
46.18635, 1.86933	HTA
2440 m
46.18289, 1.89020	46.18775, 1.86875	 
191	172	N/A	BT
119 m
46.16840, 1.86982	HTA
2702 m
46.18289, 1.89020	46.16947, 1.86988	 
192	140	N/A	BT
114 m
46.16199, 1.87483	HTA
2954 m
46.18289, 1.89020	46.16099, 1.87507	 
193	113	
000AO0106
BT
57 m
46.17997, 1.86506	HTA
2776 m
46.18289, 1.89020	46.18041, 1.86531	 
194	273	N/A	BT
161 m
46.17531, 1.88196	HTA
1157 m
46.18289, 1.89020	46.17676, 1.88177	 
195	161	N/A	BT
79 m
46.16970, 1.88149	HTA
1675 m
46.18289, 1.89020	46.17028, 1.88190	 
196	122	N/A	BT
50 m
46.17531, 1.88196	HTA
1219 m
46.18289, 1.89020	46.17575, 1.88185	 
197	178	N/A	BT
143 m
46.16503, 1.85993	HTA
4044 m
46.18289, 1.89020	46.16439, 1.85880	 
198	189	N/A	BT
152 m
46.19426, 1.86738	HTA
2843 m
46.18289, 1.89020	46.19552, 1.86792	 
199	101	N/A	BT
43 m
46.19532, 1.87453	HTA
2248 m
46.18289, 1.89020	46.19570, 1.87452	 
200	218	N/A	BT
216 m
46.17372, 1.87927	HTA
1773 m
46.18289, 1.89020	46.17340, 1.87735	 
 Analyse Environnementale
Biodiversité:
Zones Natura 2000: 0
ZNIEFF Type I: 0
ZNIEFF Type II: 0

Espaces protégés:
Parcs Nationaux: 0
Parcs Naturels Régionaux: 0
Réserves: 0

 Synthèse et Recommandations
Scores de potentiel:
Score Potentiel Energetique:
100/100
Score Potentiel Economique:
100/100
 Informations Techniques
Version du rapport: 2.1_integre
Date de génération: 2025-08-11 07:27:19
Optimisation géométrique: Oui
Durée de génération: sec
Sources de données:
IGN, OSM, Cadastre, RPG, GeoRisques, SIRENEmmune_name=nom,
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

CORRUPTED BLOCK END """

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

    # Sauvegarde et URL de la carte
    carte_path = save_map_html(m, f"carte_{commune}.html")
    carte_url = "/" + carte_path if carte_path.startswith("static/") else carte_path

    # Passage au template (n'oublie pas carte_url dans rapport_commune.html)
    return render_template("rapport_commune.html", report=report, carte_url=carte_url)



@app.route("/toitures")
def recherche_toitures():
    """Interface de recherche de toitures par commune"""
    return render_template("recherche_toitures.html")

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

    # 10. Carte Folium complète avec tous les calques métiers
    carte_url = None
    try:
        print(f"[DEBUG] Génération carte pour {address} - Lat: {lat}, Lon: {lon}")
        
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
        try:
            carte_url = save_map_html(map_obj, carte_filename)
        except Exception as save_error:
            logging.error(f"[search_by_address] Erreur save_map_html: {save_error}")
            carte_url = None
        save_map_to_cache(map_obj)
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
    # Protection contre l'ouverture multiple de navigateurs
    if hasattr(open_browser, '_opened'):
        return
    open_browser._opened = True
    webbrowser.open_new("http://127.0.0.1:5000")

def main():
    try:
        print("Routes disponibles:")
        pprint.pprint(list(app.url_map.iter_rules()))
        Timer(1, open_browser).start()
        app.run(host="127.0.0.1", port=5000, debug=False)  # Debug False pour éviter les reloads multiples
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
        parkings_data = get_parkings_info_by_polygon(contour) if filters.get("filter_parkings", True) else []
        friches_data = get_friches_info_by_polygon(contour) if filters.get("filter_friches", True) else []
        
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
                    "nom": nom,
                    "prenom": prenom,
                    "denomination": denomination,
                    "activite": activite,
                    "adresse": adresse,
                    "siret": siret,
                    "lien_annuaire": f"https://www.pagesjaunes.fr/annuaire/chercherlespros?quoiqui={nom_url}&ou={ville_url}&univers=pagesjaunes&idOu=" if nom or prenom or denomination else "",
                    "lien_entreprise": f"https://www.societe.com/societe/{denomination.lower().replace(' ', '-')}-{siret}.html" if siret and denomination else "",
                    "lien_pages_blanches": f"https://www.pagesjaunes.fr/pagesblanches/recherche?quoiqui={nom}+{prenom}&ou={props.get('libelleCom','')}" if nom or prenom else ""
                }
                
                eleveurs_data.append({
                    "type": "Feature",
                    "geometry": geom,
                    "properties": eleveur_props
                })
        except Exception as e:
            print(f"⚠️ [RAPPORT_INTÉGRÉ] Erreur collecte éleveurs: {e}")
            eleveurs_data = []
        
        sirene_data = get_sirene_info_by_polygon(contour)
        
        # Toitures: utiliser OSM bâtiments + filtres surface/distance au lieu du WFS "POTENTIEL_SOLAIRE"
        toitures_data = []
        if filters.get("filter_toitures", True):
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
            except Exception as e:
                print(f"⚠️ [RAPPORT_INTÉGRÉ] Erreur génération toitures: {e}")
                toitures_data = []

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

        sirene_data = get_sirene_info_by_polygon(contour)

        # Calcul rapide d'une valeur d'irradiation (kWh/kWc/an) via PVGIS au centre de la commune
        pvgis_kwh_per_kwc = None
        try:
            pvgis_kwh_per_kwc = get_pvgis_production(lat, lon, 30, 180, peakpower=1.0)
        except Exception:
            pvgis_kwh_per_kwc = None
        
        # APIs enrichies
        api_cadastre = get_api_cadastre_data(contour_optimise)
        api_nature = get_all_api_nature_data(contour_optimise)
        api_urbanisme = get_all_gpu_data(contour_optimise)

        # Collecte et analyse des zones d'urbanisme (PLU/GPU)
        # Utiliser la logique d'optimisation des zones directement
        plu_info = []
        
        zones_data = []
        if filters.get("filter_zones", True):
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
                        
                        # Enrichissement des propriétés
                        props_enrichies = props.copy()
                        props_enrichies.update({
                            "surface_m2": round(surface_m2, 2),
                            "surface_ha": round(surface_m2 / 10000.0, 4),
                            "coords": [lat_c, lon_c],
                            "distance_bt": round(d_bt, 2) if d_bt is not None else None,
                            "distance_hta": round(d_hta, 2) if d_hta is not None else None,
                            "nom_commune": commune_name
                        })
                        
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
                    'nom': pr.get('nom') or pr.get('libelle') or ''
                }
            except Exception:
                return {}

        # Préparer un index simple des parcelles de la commune si disponible, pour associer par centroïde
        cadastre_features = []
        if isinstance(api_cadastre, dict):
            cadastre_features = (api_cadastre or {}).get('features', []) or []

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
                    'parcelles': (
                        feat.get('properties', {}).get('parcelles_cadastrales')
                        or _parcelles_for_geom(geom)
                        or _parcelles_for_point(lon_c, lat_c)
                        or _parcelles_from_api_near(lon_c, lat_c)
                    ),
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
                    'parcelles': (
                        feat.get('properties', {}).get('parcelles_cadastrales')
                        or _parcelles_for_geom(geom)
                        or _parcelles_for_point(lon_c, lat_c)
                        or _parcelles_from_api_near(lon_c, lat_c)
                    ),
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
                    'parcelles': (
                        props.get('parcelles_cadastrales')
                        or _parcelles_for_geom(geom)
                        or _parcelles_for_point(lon_c, lat_c)
                        or _parcelles_from_api_near(lon_c, lat_c)
                    ),
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
                    
                    # Références cadastrales
                    parcelles_refs = _parcelles_for_geom(parcelle["geometry"]) or _parcelles_for_point(lon_c, lat_c) or _parcelles_from_api_near(lon_c, lat_c)
                    
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
            "zones": {
                "type": "FeatureCollection",
                "features": zones_data
            },
            "parkings_analysis": parkings_analysis,
            "friches_analysis": friches_analysis,
            "toitures_analysis": toitures_analysis,
            
            "infrastructures_analysis": {
                "energie": {
                    "postes_electriques": {
                        "postes_bt": {"count": len(postes_bt_data)},
                        "postes_hta": {"count": len(postes_hta_data)}
                    }
                }
            },
            
            "environnement_analysis": {
                "zones_protegees": api_nature.get("summary", {}),
                "biodiversite": {
                    "zones_natura2000": api_nature.get("details", {}).get("natura2000_directive_habitat", {}).get("count", 0) + 
                                       api_nature.get("details", {}).get("natura2000_directive_oiseaux", {}).get("count", 0),
                    "znieff": api_nature.get("details", {}).get("znieff_type1", {}).get("count", 0) + 
                             api_nature.get("details", {}).get("znieff_type2", {}).get("count", 0)
                }
            },
            
            "socioeconomique_analysis": {
                "economie": {
                    "entreprises": {"total": len(sirene_data)}
                }
            },
            
            "synthese_recommandations": {
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
            },
            
            "api_data": {
                "cadastre": api_cadastre,
                "nature": api_nature,
                "urbanisme": api_urbanisme
            }
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

            m = folium.Map(location=[lat, lon], zoom_start=13, tiles=None)
            folium.TileLayer(
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri World Imagery",
                name="Satellite",
                overlay=False, control=True, show=True
            ).add_to(m)
            folium.TileLayer("OpenStreetMap", name="Fond OSM", overlay=False, control=True, show=False).add_to(m)

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
        # Récupération des paramètres
        commune = flask_request.values.get("commune", "").strip()
        
        if not commune:
            return jsonify({"error": "Veuillez fournir une commune."}), 400
        
        print(f"📊 [RAPPORT_COMPLET] Génération du rapport exhaustif pour {commune}")
        
        # Récupération des filtres optionnels
        filters = {
            # Filtres RPG
            "filter_rpg": flask_request.values.get("filter_rpg", "true").lower() == "true",
            "rpg_min_area": float(flask_request.values.get("rpg_min_area", 1.0)),
            "rpg_max_area": float(flask_request.values.get("rpg_max_area", 1000.0)),
            
            # Filtres parkings
            "filter_parkings": flask_request.values.get("filter_parkings", "true").lower() == "true",
            "parking_min_area": float(flask_request.values.get("parking_min_area", 1500.0)),

            # Filtres friches
            "filter_friches": flask_request.values.get("filter_friches", "true").lower() == "true",
            "friches_min_area": float(flask_request.values.get("friches_min_area", 1000.0)),

            # Filtres toitures
            "filter_toitures": flask_request.values.get("filter_toitures", "true").lower() == "true",
            "toitures_min_surface": float(flask_request.values.get("toitures_min_surface", 100.0)),
            
            # Filtres zones
            "filter_zones": flask_request.values.get("filter_zones", "true").lower() == "true",
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
                # Utiliser la carte interactive standard si aucune carte dédiée n'a été générée
                rapport["carte_url"] = "/static/map.html"
        except Exception:
            pass

        if export_format == "html" or is_browser_request:
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

if __name__ == "__main__":
    main()  # Ceci inclut Timer + app.run()


app.config["TEMPLATES_AUTO_RELOAD"] = True
