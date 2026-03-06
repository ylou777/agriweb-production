#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  BLOG / CONTENT MARKETING – HeliaPV                                          ║
║  Stratégie de content marketing technique autour des APIs solaires           ║
║                                                                              ║
║  Routes :                                                                    ║
║    /blog                                → Index des articles                 ║
║    /blog/api-ign-lidar-hd-solaire       → Article 1 – IGN LiDAR HD          ║
║    /blog/api-gpu-plu-zonage-pv          → Article 2 – GPU / PLU              ║
║    /blog/enedis-data-connect-courbes    → Article 3 – Enedis Data Connect    ║
║    /blog/pvgis-api-simulation-8760h     → Article 4 – PVGIS 8760h            ║
║    /bureaux-etudes                      → Landing page bureaux d'études      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from flask import Blueprint, render_template, request
import datetime

blog_bp = Blueprint('blog', __name__, url_prefix='')

# ── Métadonnées des articles ──────────────────────────────────────────────────
ARTICLES = [
    {
        "slug": "api-ign-lidar-hd-solaire",
        "titre": "API IGN LiDAR HD COPC : analyser le potentiel solaire d'un bâtiment en Python",
        "description": (
            "Tutoriel complet pour accéder aux nuages de points LiDAR HD de l'IGN "
            "gratuitement, extraire les plans de toit et calculer l'irradiation "
            "solaire disponible – avec des exemples Python prêts à l'emploi."
        ),
        "categorie": "IGN / Données géographiques",
        "tags": ["IGN", "LiDAR HD", "COPC", "Python", "Photovoltaïque"],
        "date": "2026-02-10",
        "lecture": "8 min",
        "image_emoji": "🛰️",
    },
    {
        "slug": "api-gpu-plu-zonage-pv",
        "titre": "API GPU Géoportail de l'Urbanisme : identifier les zones PLU favorables à vos projets PV",
        "description": (
            "Comment interroger le Géoportail de l'Urbanisme (GPU) en Python pour "
            "récupérer automatiquement les zones PLU/PLUi d'une parcelle et qualifier "
            "sa faisabilité réglementaire en 5 secondes."
        ),
        "categorie": "Réglementation / Urbanisme",
        "tags": ["GPU", "PLU", "PLUi", "WFS", "Python", "Urbanisme"],
        "date": "2026-02-18",
        "lecture": "7 min",
        "image_emoji": "🗺️",
    },
    {
        "slug": "enedis-data-connect-courbes-charge",
        "titre": "Enedis Data Connect : intégrer les courbes de charge Linky dans vos études de rentabilité PV",
        "description": (
            "Guide technique OAuth2 complet pour récupérer les données de consommation "
            "Linky via l'API Enedis Data Connect, les parser en Python et les utiliser "
            "dans vos calculs d'autoconsommation."
        ),
        "categorie": "Enedis / Réseau électrique",
        "tags": ["Enedis", "Data Connect", "OAuth2", "Linky", "Autoconsommation"],
        "date": "2026-02-25",
        "lecture": "9 min",
        "image_emoji": "⚡",
    },
    {
        "slug": "pvgis-api-simulation-8760h",
        "titre": "PVGIS EU Science Hub : simuler 8 760 heures de production solaire via API REST",
        "description": (
            "Exploitez l'API gratuite PVGIS du Joint Research Centre européen pour "
            "obtenir des simulations horaires de production PV précises (P50/P90), "
            "calculer le taux d'autoconsommation et générer des rapports bancables."
        ),
        "categorie": "Simulation PV / Production",
        "tags": ["PVGIS", "Simulation PV", "8760h", "P50/P90", "API REST"],
        "date": "2026-03-03",
        "lecture": "10 min",
        "image_emoji": "☀️",
    },
]


@blog_bp.route('/blog')
def blog_index():
    """Page d'index du blog technique HeliaPV."""
    return render_template('blog/index.html',
                           articles=ARTICLES,
                           page_title="Blog Technique HeliaPV – APIs Solaires",
                           annee=datetime.datetime.now().year)


@blog_bp.route('/blog/api-ign-lidar-hd-solaire')
def article_lidar():
    meta = next(a for a in ARTICLES if a["slug"] == "api-ign-lidar-hd-solaire")
    return render_template('blog/article_lidar_ign.html',
                           meta=meta, annee=datetime.datetime.now().year)


@blog_bp.route('/blog/api-gpu-plu-zonage-pv')
def article_gpu():
    meta = next(a for a in ARTICLES if a["slug"] == "api-gpu-plu-zonage-pv")
    return render_template('blog/article_gpu_plu.html',
                           meta=meta, annee=datetime.datetime.now().year)


@blog_bp.route('/blog/enedis-data-connect-courbes-charge')
def article_enedis():
    meta = next(a for a in ARTICLES if a["slug"] == "enedis-data-connect-courbes-charge")
    return render_template('blog/article_enedis.html',
                           meta=meta, annee=datetime.datetime.now().year)


@blog_bp.route('/blog/pvgis-api-simulation-8760h')
def article_pvgis():
    meta = next(a for a in ARTICLES if a["slug"] == "pvgis-api-simulation-8760h")
    return render_template('blog/article_pvgis.html',
                           meta=meta, annee=datetime.datetime.now().year)


@blog_bp.route('/bureaux-etudes')
def landing_bureaux_etudes():
    """Landing page dédiée aux bureaux d'études PV."""
    return render_template('blog/landing_bureaux_etudes.html',
                           annee=datetime.datetime.now().year)
