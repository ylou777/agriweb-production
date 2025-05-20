from flask import Flask, request, render_template, jsonify
import folium
import requests
from folium.plugins import Draw, MeasureControl, Search
from geopy.geocoders import Nominatim
from shapely.geometry import Point, shape
from pyproj import Transformer
import os
import uuid
import sys
import json
import tkinter as tk
from tkinter import filedialog
from threading import Timer
import webbrowser
from flask import make_response

app = Flask(__name__)
app.url_map.strict_slashes = False



# === Configuration GeoServer ===
GEOSERVER_URL = "http://localhost:8080/geoserver"
CADASTRE_LAYER = "gpu:cadastre france"
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
    "Capacité": "CapacitÃƒÂ©",  # Vérifiez l'encodage
    "Capacité suppl.": "CapacitÃƒ_1",
    "Attention": "Attention_",
    "Quote-Part unitaire": "Quote-Part",
    "Convention signée": "dont la co",
    "Capacité RT": "CapacitÃƒ_2",
    "Travaux RT": "Travaux RT",
    "RTE Capacité": "RTE - Capa",
    "RTE Capacité 1": "RTE - Ca_1",
    "Capacité suppl. 2": "CapacitÃƒ_3",
    "Puissance 2": "Puissanc_4",
    "Nombre": "Nombre de",
    "Nombre suppl.": "Nombre d_1",
    "Consommation": "Consommati",
    "Tension Avant": "Tension av",
    "Tension Après": "Tension am",
    "Travaux GR": "Travaux GR",
    "Puissance 3": "Puissanc_5",
    "Puissance EnR projets": "Puissanc_6",
    "Capacité suppl. 3": "CapacitÃƒ_4",
    "Capacité suppl. 4": "CapacitÃƒ_5",
    "Puissance 4": "Puissanc_7",
    "Nombre suppl. 2": "Nombre d_2",
    "Nombre suppl. 3": "Nombre d_3",
    "Consommation suppl.": "Consomma_1",
    "Tension 1": "Tension _1",
    "Tension 2": "Tension _2",
    "Travaux suppl.": "Travaux _1",
    "Puissance 5": "Puissanc_8",
    "Puissance 6": "Puissanc_9",
    "Capacité suppl. 5": "CapacitÃƒ_6",
    "Travaux in": "Travaux in",
    "Capacité suppl. 6": "CapacitÃƒ_7",
    "GRDHTB - C": "GRDHTB - C",
    "GRDHTB - 1": "GRDHTB -_1"
}


def main_server():
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000")
    Timer(1, open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=False)

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


# ----------------------------------------------------------
# 3) Fonctions utilitaires (WFS, geocode, etc.)
# ----------------------------------------------------------

def geocode_address(address):
    geolocator = Nominatim(user_agent="geoapp", timeout=10)
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None

def fetch_wfs_data(layer, bbox, srsname="EPSG:4326"):
    wfs_url = f"{GEOSERVER_URL}/wfs"
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": layer,
        "outputFormat": "application/json",
        "srsname": srsname,
        "bbox": bbox
    }
    response = requests.get(wfs_url, params=params)
    if response.status_code == 200:
        return response.json().get("features", [])
    print(f"Erreur WFS ({layer}): {response.status_code} - {response.text}")
    return []

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
    bbox = f"{x - radius*111000},{y - radius*111000},{x + radius*111000},{y + radius*111000},EPSG:2154"
    url = f"{GEOSERVER_URL}/wfs"
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": PARCELLE_LAYER,
        "outputFormat": "application/json",
        "bbox": bbox
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    print(f"Erreur parcelles: {response.status_code}, {response.text}")
    return {"features": []}

def get_nearest_postes(lat, lon, radius_deg=0.1):
    bbox = f"{lon - radius_deg},{lat - radius_deg},{lon + radius_deg},{lat + radius_deg},EPSG:4326"
    features = fetch_wfs_data(POSTE_LAYER, bbox)
    postes = []
    point = Point(lon, lat)
    for feature in features:
        geom = shape(feature["geometry"])
        distance = geom.distance(point) * 111000
        postes.append({
            "properties": feature["properties"],
            "distance": round(distance, 2),
            "geometry": geom
        })
    return sorted(postes, key=lambda x: x["distance"])[:3]

def get_nearest_ht_postes(lat, lon, layer=HT_POSTE_LAYER, radius_deg=0.5):
    bbox = f"{lon - radius_deg},{lat - radius_deg},{lon + radius_deg},{lat + radius_deg},EPSG:4326"
    features = fetch_wfs_data(layer, bbox)
    postes = []
    point = Point(lon, lat)
    for feature in features:
        geom = shape(feature["geometry"])
        distance = geom.distance(point) * 111000
        postes.append({
            "properties": feature["properties"],
            "distance": round(distance, 2),
            "geometry": geom
        })
    return sorted(postes, key=lambda x: x["distance"])[:3]

def get_nearest_capacites_reseau(lat, lon, count=3, radius_deg=0.1):
    bbox = f"{lon - radius_deg},{lat - radius_deg},{lon + radius_deg},{lat + radius_deg},EPSG:4326"
    features = fetch_wfs_data(CAPACITES_RESEAU_LAYER, bbox)
    capacites = []
    point = Point(lon, lat)
    for feature in features:
        geom = shape(feature["geometry"])
        distance = geom.distance(point) * 111000
        capacites.append({
            "properties": feature["properties"],
            "distance": round(distance, 2),
            "geometry": geom
        })
    return sorted(capacites, key=lambda x: x["distance"])[:count]

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
    return fetch_wfs_data(PARCELLES_GRAPHIQUES_LAYER, bbox)

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


# ----------------------------------------------------------
# 4) APIs IGN / GPU
# ----------------------------------------------------------
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


# ----------------------------------------------------------
# 5) Production PV & Élévation
# ----------------------------------------------------------
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

def get_elevation_profile(points):
    geojson = {
        "type": "MultiPoint",
        "coordinates": [[lon, lat] for lat, lon in points]
    }
    payload = {"points": geojson, "dataSetName": "SRTM_GL3"}
    url = f"{ELEVATION_API_URL}/points"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Erreur Elevation API:", response.status_code, response.text)
        return None

def bbox_to_polygon(lon, lat, delta):
    """
    Construit un polygone (GeoJSON) autour d'un centre (lon, lat)
    avec un rayon en degrés = delta.
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

# ----------------------------------------------------------
# 6) build_map (Principale) - MODIFIÉE pour JS dynamique
# ----------------------------------------------------------
def build_map(
    lat, lon, address,
    parcelle_props, parcelles_data,
    postes_data, ht_postes_data, plu_info,
    parkings_data, friches_data, potentiel_solaire_data,
    zaer_data, rpg_data, sirene_data,
    search_radius, ht_radius_deg,
    api_cadastre=None, api_nature=None, api_urbanisme=None
):
    """
    Crée un folium.Map et y ajoute toutes tes couches habituelles,
    plus un script JS qui permet de toggler dynamiquement les FeatureGroups.
    """
    map_obj = folium.Map(location=[lat, lon], zoom_start=17)
    folium.TileLayer("OpenStreetMap", name="Carte OSM").add_to(map_obj)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Satellite",
        overlay=False,
        control=True
    ).add_to(map_obj)

    Draw(export=True).add_to(map_obj)
    MeasureControl(
        position='topright',
        primary_length_unit='meters',
        primary_area_unit='sqmeters',
        secondary_area_unit='hectares'
    ).add_to(map_obj)

    # Liens Street View et Geoportail
    address_street_view = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}&heading=0&pitch=0&fov=80"
    geoportail_url = f"https://www.geoportail-urbanisme.gouv.fr/map/#tile=1&lon={lon}&lat={lat}&zoom=19&mlon={lon}&mlat={lat}"

    # Marqueur principal
    folium.Marker(
        [lat, lon],
        popup=(
            f"<b>Adresse :</b> {address}<br>"
            f"<a href='{address_street_view}' target='_blank'>Street View</a><br>"
            f"<a href='{geoportail_url}' target='_blank'>Geoportail</a>"
        ),
        icon=folium.Icon(color="blue")
    ).add_to(map_obj)

    # Ajout de tes couches existantes (cadastre, PLU, etc.)
    # ... (inchangé, on recopie ton code)...

    # Extrait ton code existant pour chaque FeatureGroup
    # ===================================================

    # 1) Cadastre (WFS)
    cadastre_group = folium.FeatureGroup(name="Cadastre (WFS)", show=True)
    if parcelle_props:
        tooltip_text = "<br>".join([f"{k}: {v}" for k, v in parcelle_props.items() if k != "geometry"])
        folium.GeoJson(
            parcelle_props.get("geometry", {}),
            style_function=lambda x: {"color": "blue", "weight": 2, "opacity": 0.8},
            tooltip=tooltip_text
        ).add_to(cadastre_group)
    if parcelles_data.get("features"):
        for parcelle in parcelles_data["features"]:
            geom = parcelle.get("geometry")
            props = parcelle.get("properties", {})
            tooltip_text = "<br>".join([f"{k}: {v}" for k, v in props.items()])
            if geom:
                folium.GeoJson(
                    geom,
                    style_function=lambda x: {"color": "purple", "weight": 2, "opacity": 0.5},
                    tooltip=tooltip_text
                ).add_to(cadastre_group)
    map_obj.add_child(cadastre_group)

    # 2) Cadastre (API IGN)
    if api_cadastre and "features" in api_cadastre:
        cad_api_group = folium.FeatureGroup(name="Cadastre (API)", show=True)
        for feat in api_cadastre["features"]:
            geom = feat.get("geometry")
            props = feat.get("properties", {})
            if geom:
                folium.GeoJson(
                    geom,
                    style_function=lambda x: {"color": "#FF6600", "weight": 2, "opacity": 0.8, "fillColor": "#FFFF00", "fillOpacity": 0.4},
                    tooltip="<br>".join([f"{k}: {v}" for k, v in props.items()])
                ).add_to(cad_api_group)
        map_obj.add_child(cad_api_group)

    # 3) Postes BT
    for poste in postes_data:
        coords_poste = poste["geometry"].centroid.coords[0]
        poste_info = poste["properties"]
        st_view = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={coords_poste[1]},{coords_poste[0]}&heading=0&pitch=0&fov=80"
        pop = (
            f"<b>Poste BT</b><br>"
            f"Distance : {poste['distance']} m<br>"
            f"{'<br>'.join([f'{k}: {v}' for k, v in poste_info.items()])}"
            f"<br><a href='{st_view}' target='_blank'>Street View</a>"
        )
        folium.Marker(
            [coords_poste[1], coords_poste[0]],
            popup=pop,
            icon=folium.Icon(color="green")
        ).add_to(map_obj)

    # 4) Postes HTA
    for poste in ht_postes_data:
        coords_poste = poste["geometry"].centroid.coords[0]
        poste_info = poste["properties"]
        pop = (
            f"<b>Poste HTA</b><br>"
            f"Distance : {poste['distance']} m<br>"
            f"{'<br>'.join([f'{k}: {v}' for k, v in poste_info.items()])}"
        )
        folium.Marker(
            [coords_poste[1], coords_poste[0]],
            popup=pop,
            icon=folium.Icon(color="orange", icon="bolt")
        ).add_to(map_obj)

# – PLU
    plu_bbox = f"{lon - search_radius},{lat - search_radius},{lon + search_radius},{lat + search_radius},EPSG:4326"
    plu_features = fetch_wfs_data(PLU_LAYER, plu_bbox)
    if plu_features and len(plu_features) > 0:
        fc = {"type": "FeatureCollection", "features": []}
        for feature in plu_features:
            geom = feature.get("geometry") or feature.get("the_geom") or feature.get("geom")
            if geom:
                feature["geometry"] = geom
                fc["features"].append(feature)
        if fc["features"]:
            tooltip_plu = folium.GeoJsonTooltip(
                fields=["insee", "typeref", "archiveUrl", "files"],
                aliases=["INSEE", "Type", "Archive URL", "Files"],
                localize=True
            )
            plu_group = folium.FeatureGroup(name="PLU", show=True)
            folium.GeoJson(
                fc,
                style_function=lambda f: {"color": "red", "weight": 2, "opacity": 0.7},
                tooltip=tooltip_plu
            ).add_to(plu_group)
            map_obj.add_child(plu_group)

    # – ZAER
    if zaer_data:
        zaer_group = folium.FeatureGroup(name="ZAER (Vectoriel)", show=True)
        for feat in zaer_data:
            geom = feat.get("geometry")
            props = feat.get("properties", {})
            if geom:
                tip = "<br>".join([f"{k}: {v}" for k, v in props.items()])
                folium.GeoJson(
                    geom,
                    style_function=lambda x: {"color": "cyan", "weight": 2, "opacity": 0.7},
                    tooltip=tip
                ).add_to(zaer_group)
        map_obj.add_child(zaer_group)

    # – Parkings
    if parkings_data:
        park_group = folium.FeatureGroup(name="Parkings", show=True)
        for feat in parkings_data:
            geom = feat.get("geometry")
            props = feat.get("properties", {})
            if geom:
                shp = shape(geom)
                ctd = shp.centroid.coords[0]
                pop = "<br>".join([f"{k}: {v}" for k, v in props.items()])
                folium.GeoJson(
                    geom,
                    style_function=lambda x: {"color": "darkgreen", "weight": 2, "opacity": 0.7},
                    tooltip=pop
                ).add_to(park_group)
                folium.Marker(
                    [ctd[1], ctd[0]],
                    popup=pop,
                    icon=folium.Icon(color="red", icon="info-sign")
                ).add_to(park_group)
        map_obj.add_child(park_group)

    # – Friches
    if friches_data:
        friches_group = folium.FeatureGroup(name="Friches", show=True)
        for feat in friches_data:
            geom = feat.get("geometry")
            props = feat.get("properties", {})
            if geom:
                shp = shape(geom)
                pop = "<br>".join([f"{k}: {v}" for k, v in props.items()])
                folium.GeoJson(
                    geom,
                    style_function=lambda x: {"color": "brown", "weight": 2, "opacity": 0.7},
                    tooltip=pop
                ).add_to(friches_group)
        map_obj.add_child(friches_group)

    # – Potentiel solaire
    if potentiel_solaire_data:
        sol_group = folium.FeatureGroup(name="Potentiel Solaire", show=True)
        for feat in potentiel_solaire_data:
            geom = feat.get("geometry")
            props = feat.get("properties", {})
            if geom:
                tip = "<br>".join([f"{k}: {v}" for k, v in props.items()])
                folium.GeoJson(
                    geom,
                    style_function=lambda x: {"color": "gold", "weight": 2, "opacity": 0.7},
                    tooltip=tip
                ).add_to(sol_group)
        map_obj.add_child(sol_group)

# 10) RPG
    if rpg_data:
        # (MODIFICATION) On affiche le polygone pour chaque parcelle,
        #   avec un popup listant toutes ses propriétés
        rpg_group = folium.FeatureGroup(name="RPG", show=True)
        for feat in rpg_data:
            feat = decode_rpg_feature(feat)
            geom = feat.get("geometry")
            props = feat.get("properties", {})

            # On construit un HTML listant toutes les props (dont dist. min)
            prop_lines = []
            for k, v in props.items():
                prop_lines.append(f"<b>{k}</b>: {v}")
            popup_html = "<br>".join(prop_lines)

            if geom:
                folium.GeoJson(
                    data=geom,
                    style_function=lambda x: {
                        "color": "darkblue",
                        "weight": 2,
                        "fillColor": "#8aa",
                        "fillOpacity": 0.3,
                    },
                    highlight_function=lambda x: {
                        "weight": 3,
                        "fillOpacity": 0.6
                    },
                    popup=folium.Popup(popup_html, max_width=300),
                ).add_to(rpg_group)
        map_obj.add_child(rpg_group)

    # – Capacités HTA
    capacites_reseau = get_nearest_capacites_reseau(lat, lon, count=3, radius_deg=ht_radius_deg)
    hta_group = folium.FeatureGroup(name="Postes HTA (Capacités d'accueil)", show=True)
    if capacites_reseau:
        for item in capacites_reseau:
            props = item["properties"]
            ht_item = {}
            for dk, sk in hta_mapping.items():
                ht_item[dk] = props.get(sk, "Non défini")
            ht_item["distance"] = item["distance"]
            lines = [f"<strong>{k}:</strong> {ht_item[k]}" for k in hta_mapping]
            lines.append(f"<strong>Distance:</strong> {ht_item['distance']} m")
            pop_txt = "<br>".join(lines)
            ctd = item["geometry"].centroid.coords[0]
            folium.Marker(
                [ctd[1], ctd[0]],
                popup=f"<b>Poste HTA</b><br>{pop_txt}",
                icon=folium.Icon(color="purple", icon="flash")
            ).add_to(hta_group)
    map_obj.add_child(hta_group)

    # 12) Entreprises (Sirene)
    sirene_group = folium.FeatureGroup(name="Entreprises (Sirene)", show=True)
    if sirene_data:
        for feature in sirene_data:
            geom = feature.get("geometry")
            props = feature.get("properties", {})

            if geom and geom.get("type") == "Point":
                coords = geom.get("coordinates", [])
                if len(coords) == 2:
                    lon_sir, lat_sir = coords
                    siret = props.get("siret", "N/A")

                    annuaire_link = (
                        f"https://annuaire-entreprises.data.gouv.fr/etablissement/"
                        f"{siret}?redirected=1"
                    )
                    popup_content = (
                        f"<b>SIRET:</b> {siret}<br>"
                        f"<a href='{annuaire_link}' target='_blank'>"
                        f"Voir la fiche entreprise</a><br>"
                    )
                    for k, v in props.items():
                        popup_content += f"{k}: {v}<br>"

                    folium.Marker(
                        [lat_sir, lon_sir],
                        popup=popup_content,
                        icon=folium.Icon(color="darkred", icon="building"),
                    ).add_to(sirene_group)
    map_obj.add_child(sirene_group)

    # NOUVELLES COUCHES : rayon 5 km => GPU, Cadastre IGN, Nature
    delta = 5.0 / 111.0  
    bbox_polygon = bbox_to_polygon(lon, lat, delta)

    # -- API GPU (Urbanisme) 5 km
    api_gpu_5km = get_all_gpu_data(bbox_polygon)
    gpu_group = folium.FeatureGroup(name="API GPU Urbanisme (5 km)", show=False)
    for endpoint, data in api_gpu_5km.items():
        if data and "features" in data:
            for feat in data["features"]:
                geom = feat.get("geometry")
                props = feat.get("properties", {})
                if geom:
                    tip = f"<strong>Type:</strong> {endpoint}<br>"
                    tip += "<br>".join([f"<strong>{k}:</strong> {v}" for k, v in props.items()])
                    folium.GeoJson(
                        geom,
                        style_function=lambda x: {"color": "#0000FF", "weight": 2, "opacity": 0.5},
                        tooltip=tip,
                    ).add_to(gpu_group)
    map_obj.add_child(gpu_group)

    # -- API Cadastre IGN (5 km)
    api_cadastre_5km = get_api_cadastre_data(bbox_polygon)
    cadastre_group_5km = folium.FeatureGroup(name="API Cadastre IGN (5 km)", show=False)
    if api_cadastre_5km and "features" in api_cadastre_5km:
        for feat in api_cadastre_5km["features"]:
            geom = feat.get("geometry")
            props = feat.get("properties", {})
            if geom:
                tip = "<br>".join([f"<strong>{k}:</strong> {v}" for k, v in props.items()])
                folium.GeoJson(
                    geom,
                    style_function=lambda x: {"color": "#FF5500", "weight": 2, "opacity": 0.5},
                    tooltip=tip,
                ).add_to(cadastre_group_5km)
    map_obj.add_child(cadastre_group_5km)

    # -- API Nature IGN (5 km)
    api_nature_5km = get_api_nature_data(bbox_polygon)
    nature_group_5km = folium.FeatureGroup(name="API Nature IGN (5 km)", show=False)
    if api_nature_5km and "features" in api_nature_5km:
        for feat in api_nature_5km["features"]:
            geom = feat.get("geometry")
            props = feat.get("properties", {})
            if geom:
                tip = "<br>".join([f"<strong>{k}:</strong> {v}" for k, v in props.items()])
                folium.GeoJson(
                    geom,
                    style_function=lambda x: {"color": "#22AA22", "weight": 2, "opacity": 0.5},
                    tooltip=tip,
                ).add_to(nature_group_5km)
    map_obj.add_child(nature_group_5km)

    # Contrôle des couches
    folium.LayerControl().add_to(map_obj)

    # Injection d'un script JS pour toggler les couches dynamiquement
    dynamic_js = f"""
    <script>
    console.log("Carte Folium chargée. Centre: {lat},{lon}");
    
    window.layerRefs = {{}};
    map.eachLayer(function(layer){{
        if(layer._name){{
            window.layerRefs[layer._name] = layer;
        }}
    }});

    // toggleLayer("Nom de la FeatureGroup", true/false)
    window.toggleLayer = function(layerName, enable){{
        var layer = window.layerRefs[layerName];
        if(!layer){{
            console.warn("Couche non trouvée:", layerName);
            return;
        }}
        if(enable){{
            map.addLayer(layer);
        }} else {{
            map.removeLayer(layer);
        }}
    }};

    map.on('click', function(e){{
        console.log("Clique sur la carte:", e.latlng);
    }});
    </script>
    """
    map_obj.get_root().html.add_child(folium.Element(dynamic_js))

    return map_obj


# ----------------------------------------------------------
# 7) ROUTES Flask
# ----------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
@app.route("/", methods=["GET", "POST"])
def index():
    # Valeurs par défaut pour la carte d'accueil
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

    # Pour un GET, on n'actualise pas la carte (on utilise celle générée lors d'une recherche)
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

            geom = {"type": "Point", "coordinates": [lon, lat]}
            api_cadastre = get_api_cadastre_data(geom)
            api_nature = get_api_nature_data(geom)
            api_urbanisme = get_all_gpu_data(geom)
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
        "api_cadastre": locals().get("api_cadastre", None),
        "api_nature": locals().get("api_nature", None),
        "api_urbanisme": locals().get("api_urbanisme", None)
    }

@app.route("/search_by_address", methods=["GET", "POST"])
def search_by_address_route():
    """
    Recherche par adresse ou lat/lon,
    Génère la carte via build_map,
    Stocke le HTML dans last_map_params, 
    Retourne un JSON d'info.
    """
    address = request.args.get("address") or request.form.get("address")
    lat_str = request.args.get("lat") or request.form.get("lat")
    lon_str = request.args.get("lon") or request.form.get("lon")
    lat, lon = 46.603354, 1.888334

    sirene_radius_km = 0.05
    sr = request.args.get("sirene_radius") or request.form.get("sirene_radius")
    if sr:
        try:
            sirene_radius_km = float(sr)
        except ValueError:
            sirene_radius_km = 0.05

    ht_radius_km = float(request.args.get("ht_radius", 1.0))
    bt_radius_km = float(request.args.get("bt_radius", 1.0))

    # On check si lat/lon
    if lat_str and lon_str:
        try:
            lat = float(lat_str)
            lon = float(lon_str)
        except ValueError:
            return jsonify({"error": "Les coordonnées doivent être des nombres."})
    elif address:
        coords = geocode_address(address)
        if coords:
            lat, lon = coords
        else:
            return jsonify({"error": "Adresse non trouvée."})
    else:
        return jsonify({"error": "Veuillez fournir une adresse ou des coordonnées."})

    search_radius = 0.03
    parcelle = get_parcelle_info(lat, lon)
    if not parcelle:
        all_parcelles = get_all_parcelles(lat, lon, radius=search_radius)
        if all_parcelles.get("features"):
            parcelle = all_parcelles["features"][0]["properties"]
    parcelles_data = get_all_parcelles(lat, lon, radius=search_radius)

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
    capacites_reseau = get_nearest_capacites_reseau(lat, lon, count=3, radius_deg=ht_radius_deg)

    # Sérialisation HTA
    hta_serializable = []
    for item in capacites_reseau:
        props = item["properties"]
        ht_item = {}
        for desired_key, source_key in hta_mapping.items():
            ht_item[desired_key] = props.get(source_key, "Non défini")
        ht_item["distance"] = item["distance"]
        hta_serializable.append(ht_item)

    # Sérialisation BT
    bt_serializable = []
    for item in postes_data:
        bt_serializable.append({
            "distance": item["distance"],
            "properties": item["properties"]
        })

    # Sérialisation RPG
    rpg_serializable = []
    for feature in rpg_data:
        decoded_feature = decode_rpg_feature(feature)
        rpg_serializable.append(decoded_feature["properties"])

    plu_serializable = get_plu_info(lat, lon, radius=search_radius)
    zaer_serializable = []
    for feature in zaer_data:
        zaer_serializable.append(feature.get("properties", {}))

    geom = {"type": "Point", "coordinates": [lon, lat]}
    api_cadastre = get_api_cadastre_data(geom)
    api_nature = get_api_nature_data(geom)
    api_urbanisme = get_all_gpu_data(geom)

    info_response = {
        "lat": lat,
        "lon": lon,
        "address": address,
        "parcelle": parcelle if parcelle else {},
        "plu": plu_serializable,
        "sirene_radius_km": sirene_radius_km,
        "hta": hta_serializable,
        "bt": bt_serializable,
        "rpg": rpg_serializable,
        "zaer": zaer_serializable,
        "ht_radius_km": ht_radius_km,
        "bt_radius_km": bt_radius_km,
        "api_cadastre": api_cadastre,
        "api_nature": api_nature,
        "api_urbanisme": api_urbanisme
    }

    # Générer la carte
    map_obj = build_map(
        lat, lon, address,
        (parcelle if parcelle else {}),
        parcelles_data,
        postes_data,
        ht_postes_data,
        plu_info,
        parkings_data,
        friches_data,
        potentiel_solaire_data,
        zaer_data,
        rpg_data,
        sirene_data,
        search_radius,
        ht_radius_deg,
        api_cadastre,
        api_nature,
        api_urbanisme
    )

    # Stocker la carte dans last_map_params
    last_map_params['html'] = map_obj._repr_html_()

    return jsonify(info_response)


@app.route("/generated_map")
def generated_map():
    # Renvoie le HTML de la carte ou une carte par défaut
    html = last_map_params.get('html')
    if not html:
        map_obj = folium.Map(location=[46.603354, 1.888334], zoom_start=6)
        html = map_obj._repr_html_()
    response = make_response(html)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/map.html")
def serve_map():
    # Iframe pour afficher la carte générée
    return generated_map()

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

@app.route("/search_by_commune", methods=["GET", "POST"])
def search_by_commune():
    # identique à ton code : geocode, get parcelles, get rpg, etc.
    # => build_map => last_map_params => return jsonify
    commune = request.args.get("commune") or request.form.get("commune")
    culture = request.args.get("culture") or request.form.get("culture")

    ht_radius_km = float(request.args.get("ht_radius", 1.0))
    bt_radius_km = float(request.args.get("bt_radius", 1.0))
    bt_max_distance_km = float(request.args.get("bt_max_distance", 1.0))
    ht_max_distance_km = float(request.args.get("ht_max_distance", 1.0))
    sirene_radius_km = float(request.args.get("sirene_radius", 0.05))

    if not commune:
        return jsonify({"error": "Veuillez fournir une commune."})
    coords = geocode_address(commune)
    if not coords:
        return jsonify({"error": "Commune non trouvée."})
    lat, lon = coords

    search_radius = 5.0 / 111.0
    parcelles_data = get_all_parcelles(lat, lon, radius=search_radius)
    rpg_data = get_rpg_info(lat, lon, radius=search_radius)
    if culture:
        filtered = []
        for feat in rpg_data:
            feat = decode_rpg_feature(feat)
            cult = feat["properties"].get("Culture", "").lower()
            if culture.lower() in cult:
                filtered.append(feat)
        rpg_data = filtered

    bt_radius_deg = bt_radius_km / 111.0
    postes_data = get_nearest_postes(lat, lon, radius_deg=bt_radius_deg)
    ht_radius_deg = ht_radius_km / 111.0
    ht_postes_data = get_nearest_ht_postes(lat, lon, radius_deg=ht_radius_deg)

    from shapely.geometry import shape
    for feat in rpg_data:
        feat = decode_rpg_feature(feat)
        centroid = shape(feat["geometry"]).centroid.coords[0]
        min_bt = calculate_min_distance((centroid[0], centroid[1]), postes_data)
        feat["properties"]["min_bt_distance_m"] = round(min_bt, 2) if min_bt is not None else "N/A"
        min_ht = calculate_min_distance((centroid[0], centroid[1]), ht_postes_data)
        feat["properties"]["min_ht_distance_m"] = round(min_ht, 2) if min_ht is not None else "N/A"

    final_rpg = []
    for feat in rpg_data:
        mbt = feat["properties"].get("min_bt_distance_m")
        mht = feat["properties"].get("min_ht_distance_m")
        condition_bt = (mbt != "N/A" and mbt <= bt_max_distance_km * 1000.0)
        condition_ht = (mht != "N/A" and mht <= ht_max_distance_km * 1000.0)
        if condition_bt or condition_ht:
            final_rpg.append(feat)

    plu_info = get_plu_info(lat, lon, radius=search_radius)
    zaer_data = get_zaer_info(lat, lon, radius=search_radius)
    sirene_radius_deg = sirene_radius_km / 111.0
    sirene_data = get_sirene_info(lat, lon, radius=sirene_radius_deg)

    geom = {"type": "Point", "coordinates": [lon, lat]}
    api_cadastre = get_api_cadastre_data(geom)
    api_nature = get_api_nature_data(geom)
    api_urbanisme = get_all_gpu_data(geom)

    info_response = {
        "lat": lat,
        "lon": lon,
        "commune": commune,
        "culture": culture,
        "parcelles": parcelles_data,
        "rpg": [f["properties"] for f in final_rpg],
        "bt": [{"distance": p["distance"], "properties": p["properties"]} for p in postes_data],
        "hta": [{"distance": p["distance"], "properties": p["properties"]} for p in ht_postes_data],
        "zaer": [feature.get("properties", {}) for feature in zaer_data],
        "ht_radius_km": ht_radius_km,
        "bt_radius_km": bt_radius_km,
        "bt_max_distance_km": bt_max_distance_km,
        "ht_max_distance_km": ht_max_distance_km,
        "sirene_radius_km": sirene_radius_km,
        "api_cadastre": api_cadastre,
        "api_nature": api_nature,
        "api_urbanisme": api_urbanisme
    }

    map_obj = build_map(
        lat, lon, commune,
        {},
        parcelles_data,
        postes_data,
        ht_postes_data,
        plu_info,
        parkings_data=[],
        friches_data=[],
        potentiel_solaire_data=[],
        zaer_data=zaer_data,
        rpg_data=final_rpg,
        sirene_data=sirene_data,
        search_radius=search_radius,
        ht_radius_deg=ht_radius_deg,
        api_cadastre=api_cadastre,
        api_nature=api_nature,
        api_urbanisme=api_urbanisme
    )

    if parcelles_data.get("features") and len(parcelles_data["features"]) > 0:
        parcelles_group = folium.FeatureGroup(name="Parcelles de la Commune", show=True)
        geojson_layer = folium.GeoJson(parcelles_data, name="Parcelles").add_to(parcelles_group)
        Search(
            layer=geojson_layer,
            search_label="id",
            placeholder="Rechercher une parcelle",
            collapsed=False
        ).addTo(map_obj)
        map_obj.add_child(parcelles_group)

    set_map_js = "<script>window.map = map;</script>"
    map_obj.get_root().html.add_child(folium.Element(set_map_js))
    map_obj.save(os.path.join(app.root_path, "templates", "map.html"))

    return jsonify(info_response)

@app.route("/rapport", methods=["POST"])
def rapport():
    lat = request.form.get("lat")
    lon = request.form.get("lon")
    if not lat or not lon:
        return "Coordonnées manquantes", 400
    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return "Coordonnées invalides", 400

    address = request.form.get("address")
    if not address:
        address = f"{lat}, {lon}"

    ht_radius_km = request.form.get("ht_radius", 1.0)
    try:
        ht_radius_km = float(ht_radius_km)
    except ValueError:
        ht_radius_km = 1.0
    ht_radius_deg = ht_radius_km / 111

    sirene_radius_km = request.form.get("sirene_radius", 0.05)
    try:
        sirene_radius_km = float(sirene_radius_km)
    except ValueError:
        sirene_radius_km = 0.05
    sirene_radius_deg = sirene_radius_km / 111

    parcelle = get_parcelle_info(lat, lon)
    if not parcelle:
        all_parcelles = get_all_parcelles(lat, lon, radius=0.03)
        if all_parcelles.get("features"):
            parcelle = all_parcelles["features"][0]["properties"]

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
    search_radius = 0.03
    geom = {"type": "Point", "coordinates": [lon, lat]}
    api_cadastre = get_api_cadastre_data(geom)
    api_nature = get_api_nature_data(geom)
    api_urbanisme = get_all_gpu_data(geom)
    map_obj = build_map(
        lat, lon, address,
        parcelle if parcelle else {},
        get_all_parcelles(lat, lon, radius=search_radius),
        postes,
        ht_postes,
        plu_info,
        parkings_data,
        friches_data,
        potentiel_solaire_data,
        zaer_data,
        rpg_data,
        get_sirene_info(lat, lon, radius=0.00045),
        search_radius,
        ht_radius_deg,
        api_cadastre,
        api_nature,
        api_urbanisme
    )
    rapport_map_filename = os.path.join(app.root_path, "templates", "rapport_map.html")
    map_obj.save(rapport_map_filename)

    geoportail_url = (
        f"https://www.geoportail-urbanisme.gouv.fr/map/#tile=1&lon={lon}&lat={lat}"
        f"&zoom=19&mlon={lon}&mlat={lat}"
    )

    capacites_reseau = get_nearest_capacites_reseau(lat, lon, count=3, radius_deg=ht_radius_deg)
    hta_serializable = []
    for item in capacites_reseau:
        props = item["properties"]
        ht_item = {}
        for desired_key, source_key in hta_mapping.items():
            ht_item[desired_key] = props.get(source_key, "Non défini")
        ht_item["distance"] = item["distance"]
        hta_serializable.append(ht_item)

    default_tilt = 30
    default_azimuth = 180
    kwh_an = get_pvgis_production(lat, lon, default_tilt, default_azimuth, peakpower=1.0)

    report = {
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
        "kwh_per_kwc": round(kwh_an, 2) if kwh_an else "N/A",
        "ht_radius_km": ht_radius_km,
        "sirene_radius_km": sirene_radius_km,
        "search_radius": search_radius
    }
    return render_template("rapport.html", report=report)

@app.route("/rapport_map.html")
def rapport_map():
    return render_template("rapport_map.html")


# ----------------------------------------------------------
# 8) Nouvelle Partie: Feasibility_simplified
# ----------------------------------------------------------
@app.route("/feasibility_simplified", methods=["GET"])
def feasibility_simplified():
    lat_str = request.args.get("lat")
    lon_str = request.args.get("lon")
    tilt_str = request.args.get("tilt")
    azim_str = request.args.get("azimuth")

    if not lat_str or not lon_str or not tilt_str or not azim_str:
        return jsonify({"error": "Paramètres manquants (lat, lon, tilt, azimuth)."}), 400

    try:
        lat = float(lat_str)
        lon = float(lon_str)
        tilt = float(tilt_str)
        azimuth = float(azim_str)
    except ValueError:
        return jsonify({"error": "Paramètres invalides (floats attendus)."}), 400

    kwh_an = get_pvgis_production(lat, lon, tilt, azimuth, peakpower=1.0)
    if kwh_an is None:
        return jsonify({"error": "Erreur PVGIS."}), 500
    return jsonify({"kwh_per_kwc": round(kwh_an, 2)})


# ----------------------------------------------------------
# 9) Lancement du serveur
# ----------------------------------------------------------



def main_server():
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000")
    Timer(1, open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=False)

if __name__ == "__main__":
    main_server()   # Lance le serveur Flask

app.config["TEMPLATES_AUTO_RELOAD"] = True
