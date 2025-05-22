# Imports principaux
# ──────────────────────────────────────────────────────────────
from flask import (
    Flask, request, render_template, jsonify, send_file,
    make_response, Response, stream_with_context
)
import folium
from folium.plugins import Draw, MeasureControl, Search, MarkerCluster
from shapely.geometry import shape, mapping, Point
from shapely.ops import transform as shp_transform
from pyproj import Transformer
from urllib.parse import quote_plus
import unicodedata, re
from threading import Timer
import webbrowser
import os
import json
import io
import csv
import zipfile
from io import BytesIO
import pprint
from functools import lru_cache
# ─── HTTP / réseaux ───────────────────────────────────────────
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import quote, quote_plus

# ─── Cartographie / géo ───────────────────────────────────────
import folium
from folium.plugins import Draw, MeasureControl, MarkerCluster, Search
from shapely.geometry import Point, shape, mapping
from shapely.ops import transform as shp_transform
from shapely.errors import GEOSException
from pyproj import Transformer
from geopy.geocoders import Nominatim
from branca.element import Element
from flask import Flask, redirect
# ─── Bureautique ──────────────────────────────────────────────
from docx import Document

# ─── GUI licence (optionnel, protégé) ─────────────────────────
try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    tk = None  # Environnement headless (pas d’interface X11)
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Session HTTP avec retry exponentiel
session = requests.Session()
session.mount(
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
GEOSERVER_WFS_URL = f"{GEOSERVER_URL}/ows"
ELEVEURS_LAYER = "gpu:etablissements_eleveurs"

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

def main_server():
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000")
    Timer(1, open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=False)

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
    api_nature = get_api_nature_data(geom)
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
    kwh_an = get_pvgis_production(lat, lon, default_tilt, default_azimuth, peakpower=1.0)

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
        "search_radius": search_radius
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
        response = session.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[Sirene] Erreur SIRET {siret} : {e}")
        return None
        
def fetch_wfs_data(layer_name, bbox, srsname="EPSG:4326"):
    # On encode uniquement les espaces (%20) mais on laisse les ":"
    layer_q = quote(layer_name, safe=':')            # « : » n’est plus codé
    try:
        url = (
            f"{GEOSERVER_WFS_URL}"
            f"?service=WFS&version=2.0.0&request=GetFeature"
            f"&typeName={layer_q}"
            f"&outputFormat=application/json"
            f"&bbox={bbox}&srsname={srsname}"
        )
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        if not resp.text.lstrip().startswith("{"):
            print(f"[fetch_wfs_data] Réponse non-JSON pour {layer_name}")
            return []
        return resp.json().get("features", [])
    except Exception as e:
        print(f"[fetch_wfs_data] Erreur WFS {layer_name}: {e}")
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
        return {"features": []}

def get_nearest_postes(lat, lon, radius_deg=0.1):
    bbox    = f"{lon-radius_deg},{lat-radius_deg},{lon+radius_deg},{lat+radius_deg},EPSG:4326"
    features = fetch_wfs_data(POSTE_LAYER, bbox)
    point   = Point(lon, lat)

    postes = []
    for feature in features:
        geom_shp = shape(feature["geometry"])
        dist     = geom_shp.distance(point) * 111000

        postes.append({
          "properties": feature["properties"],
          "distance":   round(dist, 2),
          # ici je ne stocke **jamais** l’objet Point Shapely, 
          # mais son équivalent dict GeoJSON :
          "geometry":  mapping(geom_shp)
        })

    return sorted(postes, key=lambda x: x["distance"])[:3]

def get_nearest_ht_postes(lat, lon, layer=HT_POSTE_LAYER, radius_deg=0.5):
    bbox = f"{lon-radius_deg},{lat-radius_deg},{lon+radius_deg},{lat+radius_deg},EPSG:4326"
    features = fetch_wfs_data(layer, bbox)
    postes = []
    point = Point(lon, lat)
    for feature in features:
        geom = shape(feature["geometry"])
        distance = geom.distance(point) * 111000
        postes.append({
            "properties": feature["properties"],
            "distance": round(distance, 2),
            # on renvoie un dict GeoJSON, pas l’objet Shapely
            "geometry": mapping(geom)
        })
    return sorted(postes, key=lambda x: x["distance"])[:3]

def get_nearest_capacites_reseau(lat, lon, count=3, radius_deg=0.1):
    bbox = f"{lon-radius_deg},{lat-radius_deg},{lon+radius_deg},{lat+radius_deg},EPSG:4326"
    features = fetch_wfs_data(CAPACITES_RESEAU_LAYER, bbox)
    capacites = []
    point = Point(lon, lat)
    for feature in features:
        geom = shape(feature["geometry"])
        distance = geom.distance(point) * 111000
        capacites.append({
            "properties": feature["properties"],
            "distance": round(distance, 2),
            "geometry": mapping(geom)
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

def fetch_wfs_data(layer_name, bbox, srsname="EPSG:4326"):
    layer_q = quote(layer_name, safe=':')
    url = f"{GEOSERVER_WFS_URL}?service=WFS&version=2.0.0&request=GetFeature&typeName={layer_q}&outputFormat=application/json&bbox={bbox}&srsname={srsname}"
    try:
        resp = session.get(url, timeout=10)
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
    geojson = {
        "type": "Point",
        "coordinates": [lon, lat]
    }
    payload = {"points": geojson, "dataSetName": "SRTM_GL3"}
    url = f"{ELEVATION_API_URL}/points"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            values = result.get("data", [])
            if values:
                return round(values[0].get("elevation", None), 2)
    except Exception as e:
        print("Erreur get_elevation_at_point:", e)
    return None

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

def build_map(
    lat, lon, address,
    parcelle_props, parcelles_data,
    postes_data, ht_postes_data, plu_info,
    parkings_data, friches_data, potentiel_solaire_data,
    zaer_data, rpg_data, sirene_data,
    search_radius, ht_radius_deg,
    api_cadastre=None, api_nature=None, api_urbanisme=None,
    eleveurs_data=None
):
    import folium
    from folium.plugins import Draw, MeasureControl, MarkerCluster
    from shapely.geometry import shape, mapping
    from shapely.ops import transform as shp_transform
    from pyproj import Transformer
    from utils import decode_rpg_feature, bbox_to_polygon, get_all_gpu_data, get_nearest_capacites_reseau, get_api_cadastre_data, get_api_nature_data
    
    map_obj = folium.Map(location=[lat, lon], zoom_start=17, tiles=None)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite",
        overlay=False, control=True, show=True
    ).add_to(map_obj)

    folium.TileLayer("OpenStreetMap", name="Fond OSM", overlay=False, control=True, show=False).add_to(map_obj)
    Draw(export=True).add_to(map_obj)
    MeasureControl(position="topright").add_to(map_obj)

    cadastre_group = folium.FeatureGroup(name="Cadastre (WFS)", show=True)
    if parcelle_props and parcelle_props.get("geometry"):
        tooltip = "<br>".join(f"{k}: {v}" for k, v in parcelle_props.items() if k != "geometry")
        folium.GeoJson(parcelle_props["geometry"], style_function=lambda _: {"color": "blue", "weight": 2}, tooltip=tooltip).add_to(cadastre_group)

    if parcelles_data.get("features"):
        to_wgs84 = Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True).transform
        for feat in parcelles_data["features"]:
            geom_wgs = shp_transform(to_wgs84, shape(feat["geometry"]))
            props = feat.get("properties", {})
            tooltip = "<br>".join(f"{k}: {v}" for k, v in props.items())
            folium.GeoJson(mapping(geom_wgs), style_function=lambda _: {"color": "purple", "weight": 2}, tooltip=tooltip).add_to(cadastre_group)
    map_obj.add_child(cadastre_group)

    if api_cadastre and api_cadastre.get("features"):
        cad_api_group = folium.FeatureGroup(name="Cadastre (API IGN)", show=True)
        for feat in api_cadastre["features"]:
            folium.GeoJson(feat["geometry"], style_function=lambda _: {"color": "#FF6600", "weight": 2, "fillColor": "#FFFF00", "fillOpacity": 0.4}, tooltip="<br>".join(f"{k}: {v}" for k, v in feat.get("properties", {}).items())).add_to(cad_api_group)
        map_obj.add_child(cad_api_group)

    bt_group = folium.FeatureGroup(name=f"Postes BT (\u2264 {ht_radius_deg*111:.1f} km)", show=True)
    for poste in postes_data:
        props = poste["properties"]
        dist_m = poste.get("distance")
        lon_p, lat_p = shape(poste["geometry"]).centroid.coords[0]
        popup = "<b>Poste BT</b><br>" + "<br>".join(f"{k}: {v}" for k, v in props.items())
        if dist_m is not None:
            popup += f"<br><b>Distance</b>: {dist_m:.1f} m"
        folium.Marker([lat_p, lon_p], popup=popup, icon=folium.Icon(color="darkgreen", icon="flash", prefix="fa")).add_to(bt_group)
        folium.Circle([lat_p, lon_p], radius=25, color="darkgreen", fill=True, fill_opacity=0.2).add_to(bt_group)
    map_obj.add_child(bt_group)

    hta_group = folium.FeatureGroup(name="Postes HTA (capacit\u00e9)", show=True)
    for poste in ht_postes_data:
        props = poste.get("properties", {})
        dist_m = poste.get("distance")
        try:
            lon_p, lat_p = shape(poste["geometry"]).centroid.coords[0]
        except Exception as e:
            print("❌ Erreur géométrie HTA:", e)
            continue
        capa = props.get("Capacité") or props.get("CapacitÃƒÂ©") or "N/A"
        popup = "<b>Poste HTA</b><br>" + "<br>".join(f"{k}: {v}" for k, v in props.items())
        if dist_m is not None:
            popup += f"<br><b>Distance</b>: {dist_m:.1f} m"
        popup += f"<br><b>Capacité dispo</b>: {capa}"
        folium.Marker([lat_p, lon_p], popup=popup, icon=folium.Icon(color="orange", icon="bolt", prefix="fa")).add_to(hta_group)
    map_obj.add_child(hta_group)

    plu_group = folium.FeatureGroup(name="PLU", show=True)
    for item in plu_info:
        folium.GeoJson(item.get("geometry"), style_function=lambda _: {"color": "red", "weight": 2}, tooltip="<br>".join(f"{k}: {v}" for k, v in item.items())).add_to(plu_group)
    map_obj.add_child(plu_group)

    for name, data, color in [("Parkings", parkings_data, "darkgreen"), ("Friches", friches_data, "brown"), ("Potentiel Solaire", potentiel_solaire_data, "gold"), ("ZAER", zaer_data, "cyan")]:
        group = folium.FeatureGroup(name=name, show=True)
        for f in data:
            folium.GeoJson(f.get("geometry"), style_function=lambda _: {"color": color, "weight": 2}, tooltip="<br>".join(f"{k}: {v}" for k, v in f.get("properties", {}).items())).add_to(group)
        map_obj.add_child(group)

    rpg_group = folium.FeatureGroup(name="RPG", show=True)
    for feat in rpg_data:
        dec = decode_rpg_feature(feat)
        geom, props = dec['geometry'], dec['properties']
        popup = "<br>".join(f"{k}: {v}" for k, v in props.items())
        folium.GeoJson(geom, style_function=lambda _: {"color": "darkblue", "weight": 2, "fillOpacity": 0.3}, popup=popup).add_to(rpg_group)
    map_obj.add_child(rpg_group)

    caps = get_nearest_capacites_reseau(lat, lon, count=3, radius_deg=ht_radius_deg)
    caps_group = folium.FeatureGroup(name="Postes HTA (Capacités)", show=True)
    for item in caps:
        popup = "<br>".join(f"{k}: {v}" for k, v in item['properties'].items())
        lon_c, lat_c = shape(item['geometry']).centroid.coords[0]
        folium.Marker([lat_c, lon_c], popup=popup, icon=folium.Icon(color="purple", icon="flash")).add_to(caps_group)
    map_obj.add_child(caps_group)

    sir_group = folium.FeatureGroup(name="Entreprises Sirene", show=True)
    for feat in sirene_data:
        if feat.get('geometry', {}).get('type') == 'Point':
            lon_s, lat_s = feat['geometry']['coordinates']
            popup = "<br>".join(f"{k}: {v}" for k, v in feat['properties'].items())
            folium.Marker([lat_s, lon_s], popup=popup, icon=folium.Icon(color="darkred", icon="building")).add_to(sir_group)
    map_obj.add_child(sir_group)

    delta = 5.0 / 111.0
    bbox_poly = bbox_to_polygon(lon, lat, delta)
    gpu = api_urbanisme or get_all_gpu_data(bbox_poly)
    for ep, title in [("prescription-surf","PPR Surfaces"),("prescription-lin","PPR Linéaire"),("prescription-pct","PPR Points")]:
        feats = gpu.get(ep,{}).get('features',[])
        group = folium.FeatureGroup(name=title, show=False)
        for f in feats:
            folium.GeoJson(f['geometry'], style_function=lambda _: {"color": "#FFAA00", "weight": 2}, tooltip="<br>".join(f"{k}: {v}" for k,v in f.get('properties',{}).items())).add_to(group)
        map_obj.add_child(group)

    gpu_group = folium.FeatureGroup(name="Urbanisme (GPU 5km)", show=False)
    for ep, data in gpu.items():
        if data and 'features' in data:
            for f in data['features']:
                folium.GeoJson(f['geometry'], style_function=lambda _: {"color": "#0000FF", "weight": 1}, tooltip=f"Type: {ep}").add_to(gpu_group)
    map_obj.add_child(gpu_group)

    if eleveurs_data:
        to_wgs = Transformer.from_crs("EPSG:2154","EPSG:4326",always_xy=True).transform
        el_group = folium.FeatureGroup(name="Éleveurs", show=True)
        cluster = MarkerCluster().add_to(el_group)
        for feat in eleveurs_data:
            x, y = shape(feat['geometry']).coords[0]
            lon_e, lat_e = to_wgs(x, y)
            props = feat['properties']
            popup = "<br>".join(f"{k}: {v}" for k,v in props.items())
            if props.get('siret'):
                popup += f"<br><a href='https://annuaire-entreprises.data.gouv.fr/etablissement/{props['siret']}' target='_blank'>Fiche entreprise</a>"
            folium.Marker([lat_e, lon_e], popup=popup, icon=folium.Icon(color="cadetblue", icon="paw", prefix="fa")).add_to(cluster)
        map_obj.add_child(el_group)

    cad5 = api_cadastre or get_api_cadastre_data(bbox_poly)
    nat5 = api_nature or get_api_nature_data(bbox_poly)
    for name, data, show in [("API Cadastre IGN (5km)", cad5, False), ("API Nature IGN (5km)", nat5, False)]:
        grp = folium.FeatureGroup(name=name, show=show)
        for f in data.get('features', []):
            folium.GeoJson(f['geometry'], style_function=lambda _: {"color": "#FF5500" if 'Cadastre' in name else "#22AA22", "weight":2}, tooltip="<br>".join(f"{k}: {v}" for k,v in f.get('properties',{}).items())).add_to(grp)
        map_obj.add_child(grp)

    folium.LayerControl().add_to(map_obj)
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
    window.fetchAndDisplayGeoJson = function () {/* rien ici */};
    })();
    </script>
    """
    map_obj.get_root().html.add_child(Element(helper_js))
    return map_obj


def save_map_to_cache(map_obj):
    last_map_params["html"] = map_obj._repr_html_()

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
    api_nature = get_api_nature_data(geom)
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
    kwh_an = get_pvgis_production(lat, lon, default_tilt, default_azimuth, peakpower=1.0)

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
        "search_radius": search_radius
    }



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

app = Flask(__name__)


@app.route("/search_by_commune", methods=["GET", "POST"])
def search_by_commune():
    # ───────────────────────── 1) paramètres ──────────────────────────
    commune = request.values.get("commune", "").strip()
    culture = request.values.get("culture", "")
    ht_max_km = float(request.values.get("ht_max_distance", 1.0))
    bt_max_km = float(request.values.get("bt_max_distance", 1.0))
    sir_km    = float(request.values.get("sirene_radius", 0.05))
    min_ha    = float(request.values.get("min_area_ha", 0))
    max_ha    = float(request.values.get("max_area_ha", 1e9))

    if not commune:
        return jsonify({"error": "Veuillez fournir une commune."}), 400

    coords = geocode_address(commune)
    if not coords:
        return jsonify({"error": "Commune non trouvée."}), 404
    lat, lon = coords

    # ───────────────────────── 2) emprise 5 km ────────────────────────
    r_deg = 5.0 / 111.0
    bbox  = f"{lon-r_deg},{lat-r_deg},{lon+r_deg},{lat+r_deg},EPSG:4326"

    # ───────────────────────── 3) couches sources ─────────────────────
    parcelles_data   = get_all_parcelles(lat, lon, radius=r_deg)
    rpg_raw          = get_rpg_info(lat, lon, radius=r_deg)

    # → on récupère **tous** les postes BT / HTA de l’emprise
    postes_bt_data   = fetch_wfs_data(POSTE_LAYER,    bbox)
    postes_hta_data  = fetch_wfs_data(HT_POSTE_LAYER, bbox)

    eleveurs_data = fetch_wfs_data(ELEVEURS_LAYER, bbox, srsname="EPSG:4326")
    plu_info      = get_plu_info(lat, lon, radius=r_deg)
    zaer_data     = get_zaer_info(lat, lon, radius=r_deg)
    parkings_data = get_parkings_info(lat, lon, radius=r_deg)
    friches_data  = get_friches_info(lat, lon, radius=r_deg)
    solaire_data  = get_potentiel_solaire_info(lat, lon, radius=r_deg)
    sirene_data   = get_sirene_info(lat, lon, radius=sir_km / 111.0)

    point          = {"type": "Point", "coordinates": [lon, lat]}
    api_cadastre   = get_api_cadastre_data(point)
    api_nature     = get_api_nature_data(point)
    api_urbanisme  = get_all_gpu_data(point)

    # ───────────────────────── 4) filtrage RPG ────────────────────────
    from shapely.geometry import shape
    from shapely.ops       import transform as shp_transform
    from pyproj            import Transformer
    to_l93 = Transformer.from_crs("EPSG:4326", "EPSG:2154",
                                  always_xy=True).transform

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
        d_bt   = calculate_min_distance(cent, postes_bt_data)    # m ou None
        d_hta  = calculate_min_distance(cent, postes_hta_data)   # m ou None

        # si les deux sont hors seuils : on oublie la parcelle
        if ((d_bt  or 1e12) / 1000.0) > bt_max_km \
        and ((d_hta or 1e12) / 1000.0) > ht_max_km:
            continue

        # enrichissement des propriétés
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

    # ───────────────────────── 5) carte interactive ───────────────────
    map_obj = build_map(
        lat, lon, commune,
        parcelle_props={}, parcelles_data=parcelles_data,
        postes_data=postes_bt_data,          # tous les BT
        ht_postes_data=postes_hta_data,      # tous les HTA
        plu_info=plu_info,
        parkings_data=parkings_data,
        friches_data=friches_data,
        potentiel_solaire_data=solaire_data,
        zaer_data=zaer_data,
        rpg_data=final_rpg,
        sirene_data=sirene_data,
        search_radius=r_deg,
        ht_radius_deg=ht_max_km/111.0,
        api_cadastre=api_cadastre,
        api_nature=api_nature,
        api_urbanisme=api_urbanisme,
        eleveurs_data=eleveurs_data
    )
    save_map_to_cache(map_obj)
   
    

    # ───────────────────────── 6) réponse JSON ────────────────────────
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
@app.route("/generate_report_docx", methods=["POST"])
def generate_report_docx():
    lat = request.form.get("lat")
    lon = request.form.get("lon")
    if not lat or not lon:
        return "Coordonnées manquantes", 400
    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return "Coordonnées invalides", 400

    address = request.form.get("address") or f"{lat}, {lon}"
    ht_radius = float(request.form.get("ht_radius", 1.0))
    sirene_radius = float(request.form.get("sirene_radius", 0.05))

    data = build_report_data(lat, lon, address, ht_radius, sirene_radius)

    doc = Document()
    doc.add_heading("Rapport de la zone", level=1)
    doc.add_paragraph(f"Adresse : {data['address']}")
    doc.add_paragraph(f"Latitude : {data['lat']}")
    doc.add_paragraph(f"Longitude : {data['lon']}")
    doc.add_paragraph(f"Geoportail : {data['geoportail_url']}")

    doc.add_heading("Synthèse", level=2)
    doc.add_paragraph(f"{len(data.get('postes', []))} postes BT à proximité")
    doc.add_paragraph(f"{len(data.get('ht_postes', []))} postes HTA à proximité")
    doc.add_paragraph(f"{len(data.get('rpg', []))} parcelles RPG")
    doc.add_paragraph(f"{len(data.get('eleveurs', []))} éleveurs")

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        download_name="rapport.docx",
        as_attachment=True,
    )

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

    # Récupération des rayons
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

    # Informations de base
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

    # Calcul des distances pour RPG
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

    # Récupération de la couche Éleveurs
    eleveurs_bbox = f"{lon-0.03},{lat-0.03},{lon+0.03},{lat+0.03},EPSG:4326"
    eleveurs_data = fetch_wfs_data(ELEVEURS_LAYER, eleveurs_bbox)

    # Altitude du point
    altitude_m = get_elevation_at_point(lat, lon)

    # Génération des autres couches et carte
    search_radius = 0.03
    geom = {"type": "Point", "coordinates": [lon, lat]}
    api_cadastre = get_api_cadastre_data(geom)
    api_nature = get_api_nature_data(geom)
    api_urbanisme = get_all_gpu_data(geom)

    map_obj = build_map(
        lat, lon, address,
        parcelle or {},
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
        api_urbanisme,
        eleveurs_data=eleveurs_data
    )
    save_map_to_cache(map_obj)
    rapport_map_filename = os.path.join(app.root_path, "templates", "rapport_map.html")
    map_obj.save(rapport_map_filename)

    # URL vers Geoportail
    geoportail_url = (
        f"https://www.geoportail-urbanisme.gouv.fr/map/#tile=1&lon={lon}&lat={lat}"
        f"&zoom=19&mlon={lon}&mlat={lat}"
    )

    # Capacités réseau HTA
    capacites_reseau = get_nearest_capacites_reseau(lat, lon, count=3, radius_deg=ht_radius_deg)
    hta_serializable = []
    for item in capacites_reseau:
        props = item["properties"]
        ht_item = {dk: props.get(sk, "Non défini") for dk, sk in hta_mapping.items()}
        ht_item["distance"] = item["distance"]
        hta_serializable.append(ht_item)

    # Production PV annualisée
    default_tilt = 30
    default_azimuth = 180
    kwh_an = get_pvgis_production(lat, lon, default_tilt, default_azimuth, peakpower=1.0)

    # Assemblage du rapport
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
        # Ajouts : couche Éleveurs et altitude
        "eleveurs": eleveurs_data,
        "altitude_m": altitude_m,
        "kwh_per_kwc": round(kwh_an, 2) if kwh_an is not None else "N/A",
        "ht_radius_km": ht_radius_km,
        "sirene_radius_km": sirene_radius_km,
        "search_radius": search_radius
    }
    return render_template("rapport.html", report=report)


@app.route("/rapport_map.html")
def rapport_map():
    return render_template("rapport_map.html")


###########################
# NOUVELLE PARTIE : FEASIBILITY SIMPLIFIEE
###########################
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

@app.route("/generate_reports", methods=["POST"])
def generate_reports():
    from shapely.geometry import shape
    from shapely.ops import transform
    from pyproj import Transformer
    from shapely.errors import GEOSException

    # 1) Lecture des critères
    criteria = request.get_json() or {}
    commune = criteria.get("commune")
    if not commune:
        return jsonify({"error": "commune manquante"}), 400

    # 2) Géocodage ou coordonnées forcées
    if "force_lat" in criteria and "force_lon" in criteria:
        lat = criteria["force_lat"]
        lon = criteria["force_lon"]
    else:
        coords = geocode_address(commune)
        if not coords:
            return jsonify({"error": f"Commune '{commune}' non trouvée"}), 404
        lat, lon = coords

    # 3) Zone de recherche (5 km)
    delta_deg = 5.0 / 111.0
    bbox_poly = bbox_to_polygon(lon, lat, delta_deg)

    # 4) Charger les données
    rpg_data      = get_rpg_info(lat, lon, radius=delta_deg)
    postes_bt     = get_nearest_postes(lat, lon, radius_deg=criteria.get("max_bt_dist_m",500)/111000)
    postes_hta    = get_nearest_ht_postes(lat, lon, radius_deg=criteria.get("max_ht_dist_m",2000)/111000)
    eleveurs_data = fetch_wfs_data(
        ELEVEURS_LAYER,
        f"{lon-delta_deg},{lat-delta_deg},{lon+delta_deg},{lat+delta_deg},EPSG:4326"
    )

    # 5) Exclusions : nature et historique, nettoyage géométries
    nature_shapes = []
    if criteria.get("exclude_nature"):
        api_nat = get_api_nature_data(bbox_poly) or {}
        for feat in api_nat.get("features", []):
            try:
                ns = shape(feat.get("geometry", {}))
                if not ns.is_valid:
                    ns = ns.buffer(0)
                nature_shapes.append(ns)
            except (GEOSException, ValueError):
                continue

    hist_shapes = []
    if criteria.get("exclude_historic"):
        gpu = fetch_gpu_data("acte-sup", bbox_poly) or {}
        for feat in gpu.get("features", []):
            try:
                hs = shape(feat.get("geometry", {}))
                if not hs.is_valid:
                    hs = hs.buffer(0)
                hist_shapes.append(hs)
            except (GEOSException, ValueError):
                continue

    # 6) Filtrer parcelles
    filtered_parcelles = []
    min_area_m2 = criteria.get("min_parcelle_area_ha", 10.0) * 10000
    proj_metric = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)

    # Ensure bt_max_km and ht_max_km are defined from criteria or set defaults
    bt_max_km = criteria.get("bt_max_km", 5.0)
    ht_max_km = criteria.get("ht_max_km", 5.0)

    for feat in rpg_data:
        feat = decode_rpg_feature(feat)
        props = feat.get("properties", {})
        geom = shape(feat.get("geometry", {}))

        # a) surface minimale
        try:
            poly_m = transform(proj_metric.transform, geom)
        except GEOSException:
            continue
        if poly_m.area < min_area_m2:
            continue

        # b) exclure zones
        skip = False
        for ns in nature_shapes:
            try:
                if geom.intersects(ns): skip = True; break
            except GEOSException:
                continue
        if skip: continue
        for hs in hist_shapes:
            try:
                if geom.intersects(hs): skip = True; break
            except GEOSException:
                continue
        if skip: continue

        # c) distances aux postes
        centroid = geom.centroid.coords[0]
        # distance aux réseaux (m en sortie)
        d_bt  = calculate_min_distance(centroid, postes_bt)   # None ⇢ pas de BT <= 5 km
        d_hta = calculate_min_distance(centroid, postes_hta)  # None ⇢ pas de HTA <= 5 km

        # Remplace None par une très grande valeur, puis convertit en km
        d_bt_km  = (d_bt  or 1e12) / 1000.0
        d_hta_km = (d_hta or 1e12) / 1000.0

        # Écarte la parcelle **seulement** si elle est hors-seuil pour les 2 réseaux
        if d_bt_km > bt_max_km and d_hta_km > ht_max_km:
            continue

        props.update({
            "distance_bt_m": round(d_bt,2),
            "distance_hta_m": round(d_hta,2)
        })
        filtered_parcelles.append(props)

    # 7) Filtrer éleveurs
    filtered_eleveurs = []
    if criteria.get("has_eleveurs"):
        filtered_eleveurs = [e.get("properties", {}) for e in eleveurs_data]

    # 8) Retour JSON
    return jsonify({
        "commune": commune,
        "lat": lat,
        "lon": lon,
        "parcelles": filtered_parcelles,
        "eleveurs": filtered_eleveurs
    })
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
# ──────────────────────────────────────────────────────────────────────────────
# compute_commune_report
# ──────────────────────────────────────────────────────────────────────────────
from shapely.geometry import shape, mapping
from shapely.ops      import transform as shp_transform
from pyproj           import Transformer

def compute_commune_report(
    commune_name: str,
    culture: str,
    min_area_ha: float,
    max_area_ha: float,
    ht_max_km: float  = 5.0,
    bt_max_km: float  = 5.0,
    sirene_km: float  = 5.0,
    want_eleveurs: bool = False
) -> dict:
    # 1) ─── Géocodage
    coords = geocode_address(commune_name)
    if not coords:                       # si la commune est introuvable
        return {k: [] for k in [
            "commune", "rpg", "eleveurs", "postes_bt", "postes_hta",
            "parcelles", "api_cadastre", "api_nature", "api_urbanisme",
            "plu", "parkings", "friches", "solaire", "zaer",
            "ppr_lin", "ppr_surf", "ppr_pct"
        ]}

    lat, lon = coords
    point_geojson = {"type": "Point", "coordinates": [lon, lat]}

    # 2) ─── Emprise de travail : cercle ~5 km
    r_km  = 5.0
    r_deg = r_km / 111.0

    # 3) ─── RPG dans le cercle + proj. métrique pour calcul surface
    raw_rpg     = get_rpg_info(lat, lon, radius=r_deg) or []
    proj_metric = Transformer.from_crs("EPSG:4326", "EPSG:2154",
                                       always_xy=True).transform

    # 4) ─── Postes BT / HTA dans l’emprise
    postes_bt  = get_nearest_postes(lat, lon, radius_deg=r_deg)
    postes_hta = get_nearest_ht_postes(lat, lon, radius_deg=r_deg)

    # 5) ─── Filtrage des RPG
    filtered_rpg = []
    for feat in raw_rpg:
        dec   = decode_rpg_feature(feat)
        poly  = shape(dec["geometry"])
        props = dec["properties"]

        # a) culture
        if culture and culture.lower() not in props.get("Culture", "").lower():
            continue

        # b) surface (ha)
        ha = shp_transform(proj_metric, poly).area / 10_000.0
        if ha < min_area_ha or ha > max_area_ha:
            continue

        # c) distances réseaux
        cent = poly.centroid.coords[0]
        d_bt  = calculate_min_distance(cent, postes_bt)   # => m ou None
        d_hta = calculate_min_distance(cent, postes_hta)  # => m ou None

        # remplacer None par très grand pour les comparaisons
        d_bt_km  = (d_bt  or 1e12) / 1000.0
        d_hta_km = (d_hta or 1e12) / 1000.0

        # on exclut uniquement si les DEUX dépassent leur seuil
        if d_bt_km > bt_max_km and d_hta_km > ht_max_km:
            continue

        # helper d’arrondi qui accepte None
        _r2 = lambda x: round(x, 2) if x is not None else None

        props.update({
            "SURF_HA":           round(ha, 3),
            "min_bt_distance_m": _r2(d_bt),
            "min_ht_distance_m": _r2(d_hta),
        })
        filtered_rpg.append({
            "type":       "Feature",
            "geometry":   dec["geometry"],
            "properties": props
        })

    # 6) ─── Éleveurs éventuels
    eleveurs = []
    if want_eleveurs:
        bbox = f"{lon-r_deg},{lat-r_deg},{lon+r_deg},{lat+r_deg},EPSG:4326"
        for e in fetch_wfs_data(ELEVEURS_LAYER, bbox, srsname="EPSG:4326") or []:
            eleveurs.append({
                "type":       "Feature",
                "geometry":   e["geometry"],
                "properties": e["properties"]
            })

    # 7) ─── Simplification des postes (on garde la distance dans properties)
    bt_simple  = [{"type":"Feature","geometry":p["geometry"],
                   "properties":{**p["properties"],"distance":p["distance"]}}
                  for p in postes_bt]
    hta_simple = [{"type":"Feature","geometry":p["geometry"],
                   "properties":{**p["properties"],"distance":p["distance"]}}
                  for p in postes_hta]

    # 8) ─── Couche « sirène_km » pour API et autres jeux
    sirene_deg = sirene_km / 111.0

    parcelles     = get_all_parcelles(lat, lon, radius=sirene_deg)
    api_cadastre  = get_api_cadastre_data(point_geojson)
    api_nature    = get_api_nature_data(point_geojson)
    api_urbanisme = get_all_gpu_data(point_geojson)
    plu           = get_plu_info(lat, lon, radius=sirene_deg)
    parkings      = get_parkings_info(lat, lon, radius=sirene_deg)
    friches       = get_friches_info(lat, lon, radius=sirene_deg)
    solaire       = get_potentiel_solaire_info(lat, lon, radius=sirene_deg)
    zaer          = get_zaer_info(lat, lon, radius=sirene_deg)

    bbox_poly = {
        "type": "Polygon",
        "coordinates": [[
            [lon - sirene_deg, lat - sirene_deg],
            [lon + sirene_deg, lat - sirene_deg],
            [lon + sirene_deg, lat + sirene_deg],
            [lon - sirene_deg, lat + sirene_deg],
            [lon - sirene_deg, lat - sirene_deg]
        ]]
    }
    ppr_lin  = fetch_gpu_data("prescription-lin",  bbox_poly) or {}
    ppr_surf = fetch_gpu_data("prescription-surf", bbox_poly) or {}
    ppr_pct  = fetch_gpu_data("prescription-pct",  bbox_poly) or {}

    # 9) ─── Retour
    return {
        "commune":    commune_name,
        "rpg":        filtered_rpg,
        "eleveurs":   eleveurs,
        "postes_bt":  bt_simple,
        "postes_hta": hta_simple,

        "parcelles":     parcelles,
        "api_cadastre":  api_cadastre,
        "api_nature":    api_nature,
        "api_urbanisme": api_urbanisme,
        "plu":           plu,
        "parkings":      parkings,
        "friches":       friches,
        "solaire":       solaire,
        "zaer":          zaer,
        "ppr_lin":       ppr_lin.get("features", []),
        "ppr_surf":      ppr_surf.get("features", []),
        "ppr_pct":       ppr_pct.get("features", []),
    }

# 2) Route SSE “Recherche par département”
# ——————————————————————————————————————————————————————————————
from flask import Response, stream_with_context

@app.route("/generate_reports_by_dept_sse")
def generate_reports_by_dept_sse():
    def event_stream():
        department   = request.args.get("department")
        if not department:
            yield "event: error\ndata: " + json.dumps({"error": "Paramètre 'department' manquant"}) + "\n\n"
            return

        # 1) on lit tous les paramètres y compris sirene_radius
        culture     = request.args.get("culture", "")
        min_area    = float(request.args.get("min_area_ha", 0))
        max_area    = float(request.args.get("max_area_ha", 99999))
        ht_max_km   = float(request.args.get("ht_max_distance", 10))
        bt_max_km   = float(request.args.get("bt_max_distance", 10))
        sirene_km   = float(request.args.get("sirene_radius", 5))       # ← bien lu
        want_elev   = request.args.get("want_eleveurs", "false").lower() == "true"

        communes = get_communes_for_dept(department)
        total = len(communes)

        for idx, feat in enumerate(communes, start=1):
            nom = feat["properties"]["nom"]
            # 2) on passe sirene_km en param
            rpt = compute_commune_report(
                commune_name=nom,
                culture=culture,
                min_area_ha=min_area,
                max_area_ha=max_area,
                ht_max_km=ht_max_km,
                bt_max_km=bt_max_km,
                sirene_km=sirene_km,
                want_eleveurs=want_elev
            )
            yield f"event: progress\ndata: [{idx}/{total}] {nom}\n\n"
            yield f"event: result\ndata: {json.dumps(rpt, ensure_ascii=False)}\n\n"

        yield "event: end\ndata: ✅ Terminé\n\n"

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )




# ------------------------------------------------------------------
# CSV generation for departmental reports
# ------------------------------------------------------------------
@app.route("/generate_reports_by_dept_csv")
def generate_reports_by_dept_csv():
    department = request.args.get("department")
    if not department:
        return jsonify({"error": "Paramètre 'department' manquant"}), 400

    culture    = request.args.get("culture", "")
    min_area   = float(request.args.get("min_area_ha", 0))
    max_area   = float(request.args.get("max_area_ha", 99999))
    ht_max_km  = float(request.args.get("ht_max_distance", 10))
    bt_max_km  = float(request.args.get("bt_max_distance", 10))
    sirene_km  = float(request.args.get("sirene_radius", 5))
    want_elev  = request.args.get("want_eleveurs", "false").lower() == "true"

    communes = get_communes_for_dept(department)

    rpg_rows = []
    rpg_keys = set()
    elev_rows = []
    elev_keys = set()

    for feat in communes:
        nom = feat["properties"].get("nom")
        rpt = compute_commune_report(
            commune_name=nom,
            culture=culture,
            min_area_ha=min_area,
            max_area_ha=max_area,
            ht_max_km=ht_max_km,
            bt_max_km=bt_max_km,
            sirene_km=sirene_km,
            want_eleveurs=want_elev
        )

        # RPG parcels
        for parc in rpt.get("rpg", []):
            props = dict(parc.get("properties", {}))
            geom = parc.get("geometry")
            if geom:
                cent = shape(geom).centroid
                caps = get_nearest_capacites_reseau(cent.y, cent.x, count=1,
                                                   radius_deg=sirene_km/111.0)
                cap_props = {}
                if caps:
                    cp = caps[0]["properties"]
                    cap_props = {
                        f"cap_{k}": cp.get(v) for k, v in hta_mapping.items()
                    }
                props.update(cap_props)
            props["Commune"] = nom
            rpg_rows.append(props)
            rpg_keys.update(props.keys())

        # Eleveurs
        if want_elev:
            for el in rpt.get("eleveurs", []):
                eprops = dict(el.get("properties", {}))
                eprops["Commune"] = nom
                elev_rows.append(eprops)
                elev_keys.update(eprops.keys())

    # Build CSV contents
    rpg_headers = sorted(rpg_keys)
    rpg_buf = io.StringIO()
    w = csv.DictWriter(rpg_buf, fieldnames=rpg_headers)
    w.writeheader()
    for row in rpg_rows:
        w.writerow({h: row.get(h, "") for h in rpg_headers})
    rpg_content = rpg_buf.getvalue()

    elev_content = ""
    if elev_rows:
        elev_headers = sorted(elev_keys)
        e_buf = io.StringIO()
        ew = csv.DictWriter(e_buf, fieldnames=elev_headers)
        ew.writeheader()
        for row in elev_rows:
            ew.writerow({h: row.get(h, "") for h in elev_headers})
        elev_content = e_buf.getvalue()

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("rpg.csv", rpg_content)
        if elev_content:
            zf.writestr("eleveurs.csv", elev_content)
    zip_buf.seek(0)

    return Response(
        zip_buf.getvalue(),
        mimetype="application/zip",
        headers={"Content-Disposition": f"attachment; filename=rapport_{department}.zip"}
    )




def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

def main():
    Timer(1, open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=False)

pprint.pprint(list(app.url_map.iter_rules()))

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

    # Pour la recherche par adresse, c'est l'endpoint /search_by_address qui génère la carte
    return render_template(
        "index.html",
        address=address,
        parcelle=parcelle_props,
        postes=postes_data,
        ht_postes=ht_postes_data,
        plu=info_response["plu"],
        parcelles_data={},
        lat=lat,
        lon=lon,
        rpg_data=rpg_data,
        sirene_data=sirene_data,
        info=info_response,
        parkings_data = get_parkings_info(lat, lon, radius=search_radius),
        culture_options=sorted(set(rpg_culture_mapping.values()))
    )

@app.route("/search_by_address", methods=["GET", "POST"])
def search_by_address_route():
    # 1) ────────── lecture des paramètres (GET ou POST) ──────────
    values = request.values                       # raccourci
    address   = values.get("address") or None
    lat_str   = values.get("lat")
    lon_str   = values.get("lon")

    # Rayon par défauts (en km)
    def _to_float(val, default):
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    ht_radius_km     = _to_float(values.get("ht_radius"),     1.0)
    bt_radius_km     = _to_float(values.get("bt_radius"),     1.0)
    sirene_radius_km = _to_float(values.get("sirene_radius"), 0.05)

    # 2) ────────── géocodage / coordonnées ──────────
    if lat_str not in (None, "") and lon_str not in (None, ""):
        try:
            lat = float(lat_str)
            lon = float(lon_str)
        except ValueError:
            return jsonify({"error": "Les coordonnées doivent être des nombres."}), 400
    elif address:
        coords = geocode_address(address)
        if not coords:
            return jsonify({"error": "Adresse non trouvée."}), 404
        lat, lon = coords
    else:
        return jsonify({"error": "Veuillez fournir une adresse ou des coordonnées."}), 400

    # 3) ────────── récupération des couches ──────────
    search_radius    = 0.03                       # ≃ 3 km
    parcelle         = get_parcelle_info(lat, lon)
    if not parcelle:
        all_parcelles = get_all_parcelles(lat, lon, radius=search_radius)
        if all_parcelles.get("features"):
            parcelle = all_parcelles["features"][0]["properties"]
    parcelles_data   = get_all_parcelles(lat, lon, radius=search_radius)

    bt_radius_deg = bt_radius_km / 111
    ht_radius_deg = ht_radius_km / 111

    postes_data      = get_nearest_postes(lat, lon, radius_deg=bt_radius_deg)
    ht_postes_data   = get_nearest_ht_postes(lat, lon, radius_deg=ht_radius_deg)
    plu_info         = get_plu_info(lat, lon, radius=search_radius)
    parkings_data    = get_parkings_info(lat, lon, radius=search_radius)
    friches_data     = get_friches_info(lat, lon, radius=search_radius)
    potentiel_solaire_data = get_potentiel_solaire_info(lat, lon)
    zaer_data        = get_zaer_info(lat, lon, radius=search_radius)
    rpg_data         = get_rpg_info(lat, lon, radius=0.0027)

    sirene_radius_deg = sirene_radius_km / 111
    sirene_data       = get_sirene_info(lat, lon, radius=sirene_radius_deg)

    capacites_reseau  = get_nearest_capacites_reseau(lat, lon, count=3,
                                                     radius_deg=ht_radius_deg)

    # 4) ────────── sérialisations compactes ──────────
    hta_serializable = []
    for item in capacites_reseau:
        props   = item["properties"]
        ht_item = {dk: props.get(sk, "Non défini") for dk, sk in hta_mapping.items()}
        ht_item["distance"] = item["distance"]
        hta_serializable.append(ht_item)

    bt_serializable  = [{"distance": p["distance"], "properties": p["properties"]}
                        for p in postes_data]

    rpg_serializable = [decode_rpg_feature(f)["properties"] for f in rpg_data]

    plu_serializable  = plu_info
    zaer_serializable = [z.get("properties", {}) for z in zaer_data]

    # 5) ────────── appels API ponctuels ──────────
    geom           = {"type": "Point", "coordinates": [lon, lat]}
    api_cadastre   = get_api_cadastre_data(geom)
    api_nature     = get_api_nature_data(geom)
    api_urbanisme  = get_all_gpu_data(geom)

    info_response = {
        "lat": lat, "lon": lon, "address": address,
        "parcelle": parcelle or {},
        "plu": plu_serializable,
        "sirene_radius_km": sirene_radius_km,
        "hta": hta_serializable, "bt": bt_serializable,
        "rpg": rpg_serializable, "zaer": zaer_serializable,
        "ht_radius_km": ht_radius_km, "bt_radius_km": bt_radius_km,
        "api_cadastre": api_cadastre,
        "api_nature":   api_nature,
        "api_urbanisme": api_urbanisme,
    }

    # 6) ────────── génération de la carte ──────────
    map_obj = build_map(
        lat, lon, address,
        parcelle or {}, parcelles_data,
        postes_data, ht_postes_data,
        plu_info, parkings_data, friches_data,
        potentiel_solaire_data, zaer_data,
        rpg_data, sirene_data,
        search_radius, ht_radius_deg,
        api_cadastre, api_nature, api_urbanisme,
        eleveurs_data=None ,  # Pas d'éleveurs ici
    )
    save_map_to_cache(map_obj)
    

    return jsonify(info_response)


@app.route("/map.html")
def map_view():
    html = last_map_params.get("html")

    if not html:
        # Carte de secours
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
            show=True
        ).add_to(map_obj)

        folium.TileLayer("OpenStreetMap", name="OSM", overlay=False, show=False).add_to(map_obj)
        folium.LayerControl().add_to(map_obj)

        # Injecte le JS manquant
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

            window.fetchAndDisplayGeoJson = function () {/* rien ici */};
        })();
        </script>
        """
        map_obj.get_root().html.add_child(Element(helper_js))

        html = map_obj.get_root().render()
        # 🔧 ENREGISTRE la version générée
        last_map_params["html"] = html

    print("🗺️ map_view called, sending map HTML...")
    return Response(html, mimetype='text/html')

if __name__ == "__main__":
    main()  # Ceci inclut Timer + app.run()


app.config["TEMPLATES_AUTO_RELOAD"] = True
