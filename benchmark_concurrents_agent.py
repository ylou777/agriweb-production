#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        BENCHMARK CONCURRENTIEL – HeliaPV / AgriWeb                          ║
║        Agent autonome d'analyse des logiciels concurrents (marché FR)        ║
║                                                                              ║
║  Usage :                                                                     ║
║    python benchmark_concurrents_agent.py                                     ║
║    python benchmark_concurrents_agent.py --output rapport_benchmark.html     ║
║    python benchmark_concurrents_agent.py --format pdf                        ║
║    python benchmark_concurrents_agent.py --groq-key <YOUR_KEY>               ║
╚══════════════════════════════════════════════════════════════════════════════╝

Description
-----------
Cet agent analyse exhaustivement les logiciels concurrents à HeliaPV sur le
territoire français. Il :

1. Charge la définition précise de HeliaPV (21 critères fonctionnels)
2. Recherche et analyse les concurrents identifiés, classés en 4 catégories :
   - Logiciels de conception/simulation PV (PVsyst, Archelios, Helioscope…)
   - Plateformes SaaS de prospection solaire (Solargis, Aurora, Nearmap…)
   - CRM spécialisés énergie solaire (Salesforce énergie, Pegase…)
   - Outils cartographiques/SIG (QGIS + plugins, Géoplateforme IGN…)
3. Note chaque concurrent sur les 21 critères avec score 0-5
4. Génère un rapport HTML/PDF avec :
   - Tableau comparatif interactif
   - Radar chart (forces/faiblesses)
   - Positionnement HeliaPV
   - Analyse prix (modèles économiques)
   - Synthèse des opportunités différenciantes
"""

import os
import sys
import json
import argparse
import datetime
from pathlib import Path

# ── Tentative d'import Groq pour enrichissement IA ───────────────────────────
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("ℹ️  groq non installé – analyse IA désactivée (pip install groq)")

# ── Tentative d'import ReportLab pour export PDF ─────────────────────────────
try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm, mm
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                     Paragraph, Spacer, PageBreak)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("ℹ️  reportlab non installé – export PDF désactivé")

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 1 — DÉFINITION HELIAPV (référentiel de comparaison)
# ════════════════════════════════════════════════════════════════════════════════

HELIAPV_PROFILE = {
    "nom": "HeliaPV / AgriWeb",
    "version": "3.2",
    "date_analyse": "Mars 2026",
    "type": "SaaS Python/Flask – déployé Railway",
    "marche_cible": "Développeurs de projets PV France (IPD, EPC, bureaux d'études)",
    "url": "https://app.heliapv.fr",
    "tarification": "Freemium + abonnements Stripe (trial 50 recherches, standard, pro, enterprise)",

    # 21 critères fonctionnels – chaque critère noté 0-5 pour HeliaPV et les concurrents
    "criteres": [
        {"id": "C01", "groupe": "Cartographie", "libelle": "Cartographie interactive multi-couches", "heliapv": 5,
         "details": "RPG, PLU/PLUi, parkings, friches, toitures, BT/HTA, OSM – GeoServer WMS/WFS"},
        {"id": "C02", "groupe": "Cartographie", "libelle": "Recherche adresse & commune autocomplete", "heliapv": 5,
         "details": "API IGN BAN + Nominatim, SSE temps réel, filtres avancés"},
        {"id": "C03", "groupe": "Cartographie", "libelle": "Données foncières & cadastre", "heliapv": 5,
         "details": "IGN cadastre, numéros de parcelles, lookup propriétaires"},
        {"id": "C04", "groupe": "Cartographie", "libelle": "Données réseau électrique BT/HTA", "heliapv": 5,
         "details": "Distance postes BT/HTA, capacités réseau, diagnostic HTA"},
        {"id": "C05", "groupe": "Analyse Solaire", "libelle": "Simulation de production PVGIS 8760h", "heliapv": 5,
         "details": "PVGIS EU Science Hub, 8760 points horaires, pertes configurables"},
        {"id": "C06", "groupe": "Analyse Solaire", "libelle": "Analyse LiDAR HD & nuages de points 3D", "heliapv": 5,
         "details": "IGN COPC LiDAR HD, streaming HTTP Range, analyse plans de toit 3D"},
        {"id": "C07", "groupe": "Analyse Solaire", "libelle": "Analyse Google Solar API", "heliapv": 4,
         "details": "Building Insights, Flux Heatmap, DSM – nécessite clé API Google"},
        {"id": "C08", "groupe": "Conception PV", "libelle": "Calpinage/calepinage panneaux PV", "heliapv": 4,
         "details": "Multi-zones, orientation/inclinaison, base modules + onduleurs"},
        {"id": "C09", "groupe": "Conception PV", "libelle": "Schéma unifilaire NF C 15-712", "heliapv": 5,
         "details": "Génération PDF conforme NF C 15-712-1, symboles normalisés"},
        {"id": "C10", "groupe": "Conception PV", "libelle": "Calcul autoconsommation & tarifs", "heliapv": 5,
         "details": "BASE, HPHC, HPHC+midi, TEMPO, EJP, C4 – TRI/VAN/ROI"},
        {"id": "C11", "groupe": "Réglementaire", "libelle": "Génération Déclaration Préalable (DP)", "heliapv": 5,
         "details": "CERFA 13703*09 + plans DP1→DP8, photo-montages satellite"},
        {"id": "C12", "groupe": "Réglementaire", "libelle": "CERFA raccordement Enedis 16702", "heliapv": 5,
         "details": "Formulaire pré-rempli avec données prospect/calpinage"},
        {"id": "C13", "groupe": "Réglementaire", "libelle": "AO CRE PPE2 bâtiment (>500 kWc)", "heliapv": 5,
         "details": "Wizard notes NP/NC/NFC, bilan carbone 14 pays, export PDF + Excel"},
        {"id": "C14", "groupe": "Réglementaire", "libelle": "Risques GeoRisques (sismique, CATNAT…)", "heliapv": 5,
         "details": "API GeoRisques v1: sismique, CATNAT, cavités, radon, argiles"},
        {"id": "C15", "groupe": "CRM", "libelle": "CRM prospection intégré natif", "heliapv": 5,
         "details": "Pipeline, hiérarchie Admin/DC/Commercial, interactions, calendar"},
        {"id": "C16", "groupe": "CRM", "libelle": "Proposition commerciale auto-générée", "heliapv": 5,
         "details": "PDF complet : couverture, technique, financier, devis, CGV"},
        {"id": "C17", "groupe": "Chantier", "libelle": "Suivi de chantier IEC 62446", "heliapv": 5,
         "details": "7 phases, checklist PPSPS, traçabilité modules, NCF, DOE"},
        {"id": "C18", "groupe": "IA", "libelle": "Assistant IA solaire (function calling)", "heliapv": 4,
         "details": "Helia – Groq llama-3.1, 2 modes (assisté/manuel), 8 fonctions"},
        {"id": "C19", "groupe": "Données", "libelle": "Intégration Enedis Linky (consommation)", "heliapv": 4,
         "details": "Data Connect OAuth2, import courbes de charge"},
        {"id": "C20", "groupe": "Données", "libelle": "Annuaire SIRENE INSEE (prospects B2B)", "heliapv": 5,
         "details": "Recherche par rayon GPS, filtrage NAF, enrichissement prospects"},
        {"id": "C21", "groupe": "Plateforme", "libelle": "SaaS multi-utilisateurs avec quotas", "heliapv": 5,
         "details": "Stripe, rôles, quotas, trial, Railway scalable"},
    ]
}

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 2 — BASE DE DONNÉES CONCURRENTS (connaissance métier encodée)
# ════════════════════════════════════════════════════════════════════════════════

CONCURRENTS = [

    # ──────────────────────────────────────────────────────────────────────────
    # CATÉGORIE A : SIMULATION & CONCEPTION PV
    # ──────────────────────────────────────────────────────────────────────────
    {
        "nom": "PVsyst",
        "editeur": "PVsyst SA (Suisse)",
        "categorie": "Simulation & Conception PV",
        "url": "https://www.pvsyst.com",
        "pays_origine": "Suisse",
        "disponible_france": True,
        "annee_creation": 1994,
        "type_licence": "Logiciel desktop annuel",
        "prix_indicatif": "~800–1200 €/an/utilisateur",
        "modele_eco": "Licence annuelle perpétuelle",
        "cible": "Bureaux d'études, ingénieurs PV, développeurs",
        "description": (
            "Standard de l'industrie mondiale pour la simulation photovoltaïque. "
            "Logiciel desktop Windows avec base de données météo mondiale (Meteonorm), "
            "calcul de shading 3D, simulation P50/P90, conformité IEC 61724. "
            "Aucune fonctionnalité SaaS, pas de CRM, pas de cartographie intégrée."
        ),
        "points_forts": [
            "Référence mondiale – accépté par tous les banquiers/assureurs",
            "Simulation P50/P90 très précise",
            "Bibliothèque modules/onduleurs exhaustive (60 000+ entrées)",
            "Masques 3D horizon/ombrages",
            "Export rapports bankable",
            "Certifié IEC 61724-1",
        ],
        "points_faibles": [
            "Desktop uniquement – pas de SaaS ni cloud",
            "Pas de cartographie ou SIG intégré",
            "Pas de CRM / gestion commerciale",
            "Pas de génération documents administratifs (DP, CERFA)",
            "Interface vieillissante, prise en main complexe",
            "Pas d'IA ni d'assistant conversationnel",
            "Pas d'intégration Enedis/cadastre",
        ],
        "scores": {
            "C01": 0, "C02": 0, "C03": 0, "C04": 0,
            "C05": 5, "C06": 1, "C07": 0, "C08": 4,
            "C09": 3, "C10": 4, "C11": 0, "C12": 0,
            "C13": 0, "C14": 0, "C15": 0, "C16": 0,
            "C17": 0, "C18": 0, "C19": 0, "C20": 0,
            "C21": 1,
        }
    },

    {
        "nom": "Archelios Pro / MC",
        "editeur": "Trace Software International (France)",
        "categorie": "Simulation & Conception PV",
        "url": "https://www.trace-software.com/archelios",
        "pays_origine": "France",
        "disponible_france": True,
        "annee_creation": 2005,
        "type_licence": "SaaS web (app.archelios.com)",
        "prix_indicatif": "Gratuit (≤9 kWc) / 990 €/an (Silver ≤100 kWc) / 1 490 €/an (Gold ≤1 MWc) / 1 990 €/an (Platinum illimité)",
        "modele_eco": "Abonnement SaaS annuel – 4 niveaux (Free/Silver/Gold/Platinum)",
        "cible": "Installateurs, bureaux d'études, PME PV – petits à grands projets",
        "description": (
            "Suite logicielle française de référence pour la conception PV. Archelios PRO "
            "(application web) couvre : localisation + modélisation 3D, calepinage + "
            "câblage automatique, prédimensionnement P50/P90, étude détaillée, "
            "autoconsommation (courbes de charge), analyse technico-économique (VAN/LCOE/TRI), "
            "schéma unifilaire + plans d'exécution. Archelios CALC pour le dimensionnement "
            "électrique. Intégration SketchUp. 100+ catalogues fabricants. "
            "Reconnu INES/OPQIBI/FORMAPELEC. Pas de cartographie foncière avancée ni de CRM."
        ),
        "points_forts": [
            "Application web SaaS – accessible depuis n'importe quel navigateur",
            "Modélisation 3D + calepinage automatique + câblage strings",
            "Calcul P50/P90 avec données météo PVGIS intégrées",
            "Schéma unifilaire et plans d'exécution (NF C 15-712)",
            "Analyse autoconsommation avec courbes de charge",
            "Analyse économique complète (VAN / LCOE / TRI / retour)",
            "Intégration SketchUp pour modélisation 3D avancée",
            "100+ catalogues fabricants (modules, onduleurs, câbles)",
            "Version Free disponible (≤9 kWc) – sans engagement",
            "Éditeur français – support FR – conforme normes françaises",
            "Reconnu INES / OPQIBI / FORMAPELEC (formation certifiante)",
        ],
        "points_faibles": [
            "Pas de cartographie SIG / prospection foncière (pas de RPG, PLU, cadastre)",
            "Pas de CRM natif de prospection commerciale",
            "Pas d'intégration données foncières cadastre / IGN",
            "Pas de génération DP (CERFA 13703) automatique",
            "Pas d'IA intégrée (pas de Copilot / assistant conversationnel)",
            "Pas d'intégration réseau électrique BT/HTA Enedis",
            "Pas d'AO CRE PPE2 bâtiment (appel d'offres CRE)",
            "Pas d'intégration SIRENE / annuaire prospects B2B",
        ],
        "scores": {
            "C01": 1, "C02": 1, "C03": 0, "C04": 1,
            "C05": 4, "C06": 0, "C07": 0, "C08": 4,
            "C09": 5, "C10": 3, "C11": 0, "C12": 1,
            "C13": 0, "C14": 0, "C15": 1, "C16": 1,
            "C17": 0, "C18": 0, "C19": 1, "C20": 0,
            "C21": 3,
        }
    },

    {
        "nom": "Helioscope",
        "editeur": "Folsom Labs (USA) – racheté par Aurora Solar",
        "categorie": "Simulation & Conception PV",
        "url": "https://helioscope.com",
        "pays_origine": "USA",
        "disponible_france": True,
        "annee_creation": 2012,
        "type_licence": "SaaS cloud",
        "prix_indicatif": "~200–500 $/mois",
        "modele_eco": "Abonnement mensuel/annuel SaaS",
        "cible": "Installateurs résidentiels et C&I monde",
        "description": (
            "Plateforme SaaS américaine de conception PV avec calepinage satellite, "
            "simulation de production et rapport bankable. Fort sur le résidentiel US. "
            "Peu adapté au marché français (pas d'intégration IGN/GPU/Enedis, "
            "interface EN uniquement pour la plupart des modules avancés)."
        ),
        "points_forts": [
            "Interface intuitive, moderne",
            "Calepinage rapide sur fond satellite",
            "Rapport client professionnel",
            "Intégré dans Aurora Solar (enrichissement IA)",
            "Accessible partout (SaaS)",
        ],
        "points_faibles": [
            "Interface principalement en anglais",
            "Pas d'intégration données FR (IGN, cadastre, GPU, RPG)",
            "Pas de CRM natif",
            "Tarification élevée en USD",
            "Pas de génération documents FR (DP, CERFA Enedis)",
            "Pas d'intégration réseau Enedis/BT/HTA FR",
            "Pas d'assistant IA dédié marché FR",
        ],
        "scores": {
            "C01": 1, "C02": 1, "C03": 0, "C04": 0,
            "C05": 4, "C06": 2, "C07": 2, "C08": 4,
            "C09": 1, "C10": 2, "C11": 0, "C12": 0,
            "C13": 0, "C14": 0, "C15": 1, "C16": 1,
            "C17": 0, "C18": 2, "C19": 0, "C20": 0,
            "C21": 4,
        }
    },

    {
        "nom": "Aurora Solar",
        "editeur": "Aurora Solar Inc. (USA)",
        "categorie": "Simulation & Conception PV",
        "url": "https://www.aurorasolar.com",
        "pays_origine": "USA",
        "disponible_france": False,
        "annee_creation": 2013,
        "type_licence": "SaaS cloud",
        "prix_indicatif": "~300–600 $/mois",
        "modele_eco": "Abonnement SaaS + modules additionnels",
        "cible": "Installateurs résidentiels USA essentiellement",
        "description": (
            "Leader mondial SaaS PV résidentiel aux USA. Intègre IA pour détection "
            "automatique de toit, simulation shading 3D, CRM basique et génération "
            "de propositions. Très peu présent en France – interface EN, données US uniquement."
        ),
        "points_forts": [
            "IA de détection automatique toit (satellite ML)",
            "Interface très moderne et intuitive",
            "CRM commercial intégré",
            "Proposition client automatique",
            "Leader du marché US résidentiel",
        ],
        "points_faibles": [
            "Quasi absent du marché français",
            "Pas de données IGN/cadastre/GPU/RPG FR",
            "Interface anglaise uniquement",
            "Prix en USD, tarifs élevés",
            "Pas de conformité normes FR (NF C 15-712)",
            "Pas de génération CERFA / DP française",
            "Pas d'intégration Enedis Data Connect",
        ],
        "scores": {
            "C01": 1, "C02": 1, "C03": 0, "C04": 0,
            "C05": 3, "C06": 3, "C07": 3, "C08": 5,
            "C09": 0, "C10": 2, "C11": 0, "C12": 0,
            "C13": 0, "C14": 0, "C15": 3, "C16": 3,
            "C17": 0, "C18": 4, "C19": 0, "C20": 0,
            "C21": 4,
        }
    },

    {
        "nom": "Solarius PV",
        "editeur": "ACCA Software (Italie)",
        "categorie": "Simulation & Conception PV",
        "url": "https://www.acca.it/logiciel-photovoltaique",
        "pays_origine": "Italie",
        "disponible_france": True,
        "annee_creation": 2010,
        "type_licence": "Desktop + SaaS",
        "prix_indicatif": "~400–800 €/an",
        "modele_eco": "Licence annuelle",
        "cible": "Installateurs, bureaux d'études petits projets",
        "description": (
            "Logiciel de conception PV italien disponible en français. Permet le "
            "dimensionnement, calepinage, simulation et génération de rapports. "
            "Faible intégration avec l'écosystème de données français."
        ),
        "points_forts": [
            "Interface en français",
            "Prix accessible",
            "Génération de rapports PDF",
            "Simulation ombrage 3D",
        ],
        "points_faibles": [
            "Pas de cartographie SIG avancée FR",
            "Pas d'intégration IGN/cadastre/GPU/RPG",
            "Pas de CRM",
            "Pas de gestion documents administratifs FR",
            "Faible présence sur grandes installations (>100 kWc)",
        ],
        "scores": {
            "C01": 0, "C02": 0, "C03": 0, "C04": 0,
            "C05": 3, "C06": 0, "C07": 0, "C08": 3,
            "C09": 2, "C10": 2, "C11": 0, "C12": 0,
            "C13": 0, "C14": 0, "C15": 0, "C16": 1,
            "C17": 0, "C18": 0, "C19": 0, "C20": 0,
            "C21": 2,
        }
    },

    # ──────────────────────────────────────────────────────────────────────────
    # CATÉGORIE B : PLATEFORMES SaaS DE PROSPECTION SOLAIRE
    # ──────────────────────────────────────────────────────────────────────────
    {
        "nom": "Solargis Prospect",
        "editeur": "Solargis s.r.o. (Slovaquie)",
        "categorie": "Prospection & Données Solaires",
        "url": "https://solargis.com/prospect",
        "pays_origine": "Slovaquie",
        "disponible_france": True,
        "annee_creation": 2010,
        "type_licence": "SaaS – API + portail web",
        "prix_indicatif": "Sur devis (plusieurs k€/an)",
        "modele_eco": "Abonnement entreprise + crédits API",
        "cible": "Développeurs projets solaires, utilities, fonds d'investissement",
        "description": (
            "Référence mondiale pour les données d'irradiation solaire et la micro-siting. "
            "Fournit des données GHI/DNI/DHI avec incertitude statistique, TNsim, "
            "P50/P90/P99. Pas d'outil de prospection foncière française ni de CRM."
        ),
        "points_forts": [
            "Données solaires les plus précises au monde (30+ ans)",
            "Incertitude statistique rigoureuse (bankable)",
            "API REST bien documentée",
            "Couverture mondiale",
            "Rapports P50/P90 acceptés par les banques",
        ],
        "points_faibles": [
            "Pas de cartographie foncière française",
            "Pas de données RPG/PLU/cadastre",
            "Pas de CRM ni prospection commerciale",
            "Tarification très élevée (hors portée PME)",
            "Pas de génération documents FR",
            "Pas d'assistant IA interactif",
        ],
        "scores": {
            "C01": 1, "C02": 0, "C03": 0, "C04": 0,
            "C05": 5, "C06": 1, "C07": 0, "C08": 1,
            "C09": 0, "C10": 1, "C11": 0, "C12": 0,
            "C13": 0, "C14": 0, "C15": 0, "C16": 0,
            "C17": 0, "C18": 0, "C19": 0, "C20": 0,
            "C21": 2,
        }
    },

    {
        "nom": "EnergyMap / Sunroof (Google)",
        "editeur": "Google",
        "categorie": "Prospection & Données Solaires",
        "url": "https://sunroof.withgoogle.com",
        "pays_origine": "USA",
        "disponible_france": False,
        "annee_creation": 2015,
        "type_licence": "Gratuit (grand public)",
        "prix_indicatif": "Gratuit",
        "modele_eco": "Publicité / données internes Google",
        "cible": "Grand public",
        "description": (
            "Outil grand public de Google pour estimer le potentiel solaire d'une toiture. "
            "Basé sur Google Maps + LiDAR. Non disponible commercialement en France "
            "pour intégration professionnelle (API Google Solar limitée)."
        ),
        "points_forts": [
            "Interface très simple",
            "Données LiDAR via Google Solar API",
            "Gratuit pour le grand public",
        ],
        "points_faibles": [
            "Non disponible en France (Sunroof)",
            "Google Solar API coûteuse et limitée pour usage professionnel",
            "Pas de CRM",
            "Pas d'intégration données françaises",
            "Usage grand public uniquement",
        ],
        "scores": {
            "C01": 0, "C02": 1, "C03": 0, "C04": 0,
            "C05": 2, "C06": 2, "C07": 5, "C08": 1,
            "C09": 0, "C10": 0, "C11": 0, "C12": 0,
            "C13": 0, "C14": 0, "C15": 0, "C16": 0,
            "C17": 0, "C18": 1, "C19": 0, "C20": 0,
            "C21": 0,
        }
    },

    {
        "nom": "Tecsol / Logiciels CRE",
        "editeur": "Tecsol (France)",
        "categorie": "Conseil & Outils CRE",
        "url": "https://www.tecsol.fr",
        "pays_origine": "France",
        "disponible_france": True,
        "annee_creation": 1993,
        "type_licence": "Service de conseil + outils propriétaires",
        "prix_indicatif": "Sur devis",
        "modele_eco": "Conseil + projets",
        "cible": "Développeurs projets solaires France",
        "description": (
            "Bureau d'études et laboratoire solaire français. Propose des services "
            "de conseil, de mesure d'irradiation et de suivi de production. "
            "Développe des outils internes pour le marché français mais pas de SaaS "
            "grand public avec prospection + CRM."
        ),
        "points_forts": [
            "Expertise française reconnue",
            "Connaissance approfondie du marché et réglementation FR",
            "Mesures et validation terrain",
        ],
        "points_faibles": [
            "Pas de SaaS accessible",
            "Pas de cartographie interactive",
            "Pas de CRM",
            "Business model service, non scalable",
        ],
        "scores": {
            "C01": 0, "C02": 0, "C03": 0, "C04": 0,
            "C05": 4, "C06": 0, "C07": 0, "C08": 1,
            "C09": 0, "C10": 2, "C11": 0, "C12": 0,
            "C13": 1, "C14": 0, "C15": 0, "C16": 0,
            "C17": 0, "C18": 0, "C19": 0, "C20": 0,
            "C21": 0,
        }
    },

    # ──────────────────────────────────────────────────────────────────────────
    # CATÉGORIE C : CARTOGRAPHIE & PROSPECTION FONCIÈRE
    # ──────────────────────────────────────────────────────────────────────────
    {
        "nom": "Gis&Sol / Urbasolar Prospection",
        "editeur": "Solutions SIG spécialisées énergie",
        "categorie": "Cartographie & SIG Énergie",
        "url": "https://www.gissol.fr",
        "pays_origine": "France",
        "disponible_france": True,
        "annee_creation": 2015,
        "type_licence": "SaaS / Service",
        "prix_indicatif": "Sur devis",
        "modele_eco": "Abonnement + prestation",
        "cible": "Développeurs projets ENR France",
        "description": (
            "Plateformes SIG spécialisées ENR proposant la superposition de couches "
            "cadastrales, PLU, RPG, contraintes pour la prospection foncière. "
            "Généralement sans CRM natif ni génération automatique de documents."
        ),
        "points_forts": [
            "Données foncières françaises intégrées",
            "Interface SIG connue des développeurs ENR",
            "Couches contraintes (Natura2000, zone inondable…)",
        ],
        "points_faibles": [
            "Pas de simulation de production",
            "Pas de CRM commercial",
            "Pas de génération documents administratifs",
            "Pas d'IA",
            "Tarification souvent élevée",
        ],
        "scores": {
            "C01": 4, "C02": 3, "C03": 4, "C04": 2,
            "C05": 0, "C06": 0, "C07": 0, "C08": 0,
            "C09": 0, "C10": 0, "C11": 0, "C12": 0,
            "C13": 0, "C14": 2, "C15": 1, "C16": 0,
            "C17": 0, "C18": 0, "C19": 0, "C20": 2,
            "C21": 2,
        }
    },

    {
        "nom": "Géoplateforme IGN (libre)",
        "editeur": "IGN – Institut national de l'information géographique",
        "categorie": "Cartographie & SIG Énergie",
        "url": "https://geoplateforme.ign.fr",
        "pays_origine": "France",
        "disponible_france": True,
        "annee_creation": 2023,
        "type_licence": "Open source / API gratuite",
        "prix_indicatif": "Gratuit (APIs)",
        "modele_eco": "Service public gratuit",
        "cible": "Développeurs, collectivités, entreprises",
        "description": (
            "Géoplateforme IGN est la nouvelle infrastructure nationale fournissant "
            "cadastre, BD TOPO, LiDAR HD, orthophotographies, GPU, etc. C'est la "
            "source des données qu'HeliaPV intègre – pas une plateforme PV en soi."
        ),
        "points_forts": [
            "Source officielle des données géographiques françaises",
            "LiDAR HD gratuit",
            "Cadastre temps réel",
            "GPU (zones PLU/PLUi)",
            "API bien documentée",
        ],
        "points_faibles": [
            "Outil de données brutes, pas de SaaS PV",
            "Pas de simulation, CRM, ni outil commercial",
            "Requiert des développements importants",
            "Pas d'IA intégrée",
        ],
        "scores": {
            "C01": 3, "C02": 4, "C03": 5, "C04": 1,
            "C05": 0, "C06": 5, "C07": 0, "C08": 0,
            "C09": 0, "C10": 0, "C11": 0, "C12": 0,
            "C13": 0, "C14": 2, "C15": 0, "C16": 0,
            "C17": 0, "C18": 0, "C19": 0, "C20": 0,
            "C21": 0,
        }
    },

    {
        "nom": "EnR Prospection / Windfall",
        "editeur": "Windfall Data (UK/FR)",
        "categorie": "Cartographie & SIG Énergie",
        "url": "https://windfall.ai",
        "pays_origine": "UK",
        "disponible_france": True,
        "annee_creation": 2016,
        "type_licence": "SaaS",
        "prix_indicatif": "Sur devis",
        "modele_eco": "Abonnement SaaS",
        "cible": "Développeurs projets ENR (éolien + solaire)",
        "description": (
            "Plateforme de prospection ENR basée sur data intelligence et cartographie "
            "avancée. Couvre éolien et solaire. Moins spécialisée sur le photovoltaïque "
            "bâtiment/agricole que HeliaPV."
        ),
        "points_forts": [
            "Multi-technologie (éolien + solaire)",
            "Données contraintes environnementales",
            "Interface moderne",
        ],
        "points_faibles": [
            "Pas de simulation de production PV précise",
            "Pas de CRM commercial intégré",
            "Pas de génération documents FR",
            "Tarification élevée",
        ],
        "scores": {
            "C01": 3, "C02": 2, "C03": 2, "C04": 1,
            "C05": 1, "C06": 0, "C07": 0, "C08": 0,
            "C09": 0, "C10": 0, "C11": 0, "C12": 0,
            "C13": 0, "C14": 2, "C15": 1, "C16": 0,
            "C17": 0, "C18": 0, "C19": 0, "C20": 0,
            "C21": 2,
        }
    },

    # ──────────────────────────────────────────────────────────────────────────
    # CATÉGORIE D : CRM & GESTION COMMERCIALE ÉNERGIE
    # ──────────────────────────────────────────────────────────────────────────
    {
        "nom": "Salesforce Energy & Utilities",
        "editeur": "Salesforce (USA)",
        "categorie": "CRM Énergie",
        "url": "https://www.salesforce.com/fr/industries/energy/",
        "pays_origine": "USA",
        "disponible_france": True,
        "annee_creation": 1999,
        "type_licence": "SaaS CRM",
        "prix_indicatif": "75–300 €/utilisateur/mois",
        "modele_eco": "Abonnement SaaS par siège",
        "cible": "Grandes entreprises énergie",
        "description": (
            "CRM leader mondial avec module énergie. Très puissant pour la gestion "
            "commerciale mais zéro intégration avec les données techniques PV, "
            "la cartographie foncière française ou la génération de documents "
            "réglementaires PV."
        ),
        "points_forts": [
            "CRM très complet et configurable",
            "Intégrations natives nombreuses",
            "Reporting avancé",
            "Mobile first",
            "Support mondial",
        ],
        "points_faibles": [
            "Aucune fonctionnalité PV technique",
            "Pas de cartographie",
            "Pas de simulation de production",
            "Coût très élevé",
            "Complexe à configurer pour le PV",
            "Pas adapté aux PME solaires",
        ],
        "scores": {
            "C01": 0, "C02": 0, "C03": 0, "C04": 0,
            "C05": 0, "C06": 0, "C07": 0, "C08": 0,
            "C09": 0, "C10": 0, "C11": 0, "C12": 0,
            "C13": 0, "C14": 0, "C15": 5, "C16": 2,
            "C17": 1, "C18": 3, "C19": 0, "C20": 3,
            "C21": 5,
        }
    },

    {
        "nom": "Pegase (Logiciel ERP Energie)",
        "editeur": "Editeurs ERP français spécialisés ENR",
        "categorie": "CRM Énergie",
        "url": "https://www.pegase-energie.fr",
        "pays_origine": "France",
        "disponible_france": True,
        "annee_creation": 2010,
        "type_licence": "ERP SaaS",
        "prix_indicatif": "500–2000 €/mois",
        "modele_eco": "Abonnement ERP",
        "cible": "Installateurs et développeurs PV France",
        "description": (
            "ERP métier pour installateurs photovoltaïques incluant devis, "
            "facturation, suivi chantier, SAV. Peu de fonctionnalités cartographiques "
            "ou d'analyse technique poussée."
        ),
        "points_forts": [
            "Adapté aux installateurs FR",
            "Devis + facturation intégrés",
            "Suivi SAV et maintenance",
            "Gestion stocks matériaux",
        ],
        "points_faibles": [
            "Pas de cartographie",
            "Pas de simulation de production",
            "Pas d'intégration IGN/GPU/Enedis",
            "Axé gestion administrative, pas prospection",
            "Pas d'IA",
        ],
        "scores": {
            "C01": 0, "C02": 0, "C03": 0, "C04": 0,
            "C05": 0, "C06": 0, "C07": 0, "C08": 1,
            "C09": 1, "C10": 1, "C11": 0, "C12": 1,
            "C13": 0, "C14": 0, "C15": 4, "C16": 3,
            "C17": 3, "C18": 0, "C19": 0, "C20": 1,
            "C21": 4,
        }
    },

    {
        "nom": "SolarEdge Monitoring / mySolarEdge",
        "editeur": "SolarEdge Technologies (Israël/USA)",
        "categorie": "Monitoring & CRM Monitoring",
        "url": "https://monitoring.solaredge.com",
        "pays_origine": "Israël",
        "disponible_france": True,
        "annee_creation": 2006,
        "type_licence": "Gratuit (lié matériel SolarEdge)",
        "prix_indicatif": "Gratuit avec matériel",
        "modele_eco": "Ecosystem fermé SolarEdge",
        "cible": "Installateurs SolarEdge",
        "description": (
            "Plateforme de monitoring liée à l'écosystème SolarEdge. Surveille la "
            "production en temps réel, alerte sur pannes. Pas un outil de prospection "
            "ou de conception."
        ),
        "points_forts": [
            "Monitoring temps réel très précis (MPP par module)",
            "Alertes automatiques",
            "Application mobile",
            "Gratuit",
        ],
        "points_faibles": [
            "Uniquement monitoring post-installation",
            "Vendor lock-in SolarEdge",
            "Pas de prospection, ni conception, ni CRM",
            "Pas d'intégration données foncières FR",
        ],
        "scores": {
            "C01": 0, "C02": 0, "C03": 0, "C04": 0,
            "C05": 1, "C06": 0, "C07": 0, "C08": 0,
            "C09": 0, "C10": 1, "C11": 0, "C12": 0,
            "C13": 0, "C14": 0, "C15": 2, "C16": 0,
            "C17": 2, "C18": 0, "C19": 0, "C20": 0,
            "C21": 3,
        }
    },

    # ──────────────────────────────────────────────────────────────────────────
    # CATÉGORIE E : OUTILS ÉMERGENTS IA + SOLAIRE
    # ──────────────────────────────────────────────────────────────────────────
    {
        "nom": "Nearmap Solar (Verisk)",
        "editeur": "Nearmap / Verisk (Australie/USA)",
        "categorie": "Données Aériennes & IA",
        "url": "https://www.nearmap.com/solar",
        "pays_origine": "Australie",
        "disponible_france": False,
        "annee_creation": 2007,
        "type_licence": "SaaS – API + portail",
        "prix_indicatif": "Sur devis (k€/an)",
        "modele_eco": "Abonnement données aériennes",
        "cible": "Installateurs solaires USA/AUS/UK",
        "description": (
            "Fournisseur de données aériennes HD avec IA de détection automatique "
            "des caractéristiques de toiture (pentes, orientations, obstacles). "
            "Très fort sur l'analyse automatisée de toitures mais quasi absent en France."
        ),
        "points_forts": [
            "IA détection automatique toitures très précise",
            "Mises à jour orthophoto fréquentes",
            "API bien intégrée",
        ],
        "points_faibles": [
            "Pas de couverture France (ou très partielle)",
            "Pas de données foncières FR",
            "Pas de CRM",
            "Très onéreux",
        ],
        "scores": {
            "C01": 1, "C02": 1, "C03": 0, "C04": 0,
            "C05": 1, "C06": 3, "C07": 4, "C08": 2,
            "C09": 0, "C10": 0, "C11": 0, "C12": 0,
            "C13": 0, "C14": 0, "C15": 0, "C16": 0,
            "C17": 0, "C18": 3, "C19": 0, "C20": 0,
            "C21": 2,
        }
    },

    {
        "nom": "Paladin Energy (ex-SolarNinjas)",
        "editeur": "Paladin Energy (UK)",
        "categorie": "Données Aériennes & IA",
        "url": "https://paladinenergy.co.uk",
        "pays_origine": "UK",
        "disponible_france": False,
        "annee_creation": 2019,
        "type_licence": "SaaS",
        "prix_indicatif": "Sur devis",
        "modele_eco": "SaaS prospection ENR",
        "cible": "Développeurs projets solaires UK",
        "description": (
            "Plateforme SaaS de prospection et développement de projets solaires UK. "
            "Partage certaines similarités avec HeliaPV (cartographie + CRM + données "
            "foncières) mais adapté au marché britannique, pas français."
        ),
        "points_forts": [
            "Approche intégrée proche de HeliaPV",
            "Données foncières UK intégrées",
            "CRM basique intégré",
        ],
        "points_faibles": [
            "Absent du marché français",
            "Pas de données IGN / GPU / Enedis",
            "Interface anglaise",
            "Pas de génération documents FR",
        ],
        "scores": {
            "C01": 3, "C02": 2, "C03": 2, "C04": 1,
            "C05": 2, "C06": 1, "C07": 1, "C08": 2,
            "C09": 0, "C10": 1, "C11": 0, "C12": 0,
            "C13": 0, "C14": 1, "C15": 3, "C16": 1,
            "C17": 0, "C18": 1, "C19": 0, "C20": 1,
            "C21": 2,
        }
    },

    # ──────────────────────────────────────────────────────────────────────────
    # CATÉGORIE F : LOGICIELS SaaS INSTALLATEURS PV (marché FR / EU)
    # ──────────────────────────────────────────────────────────────────────────
    {
        "nom": "Solteo",
        "editeur": "Solteo SAS (France)",
        "categorie": "Logiciel SaaS Installateurs PV",
        "url": "https://www.solteo.fr",
        "pays_origine": "France",
        "disponible_france": True,
        "annee_creation": 2020,
        "type_licence": "SaaS B2B",
        "prix_indicatif": "Sur démo (non public)",
        "modele_eco": "Abonnement SaaS mensuel/annuel",
        "cible": "Installateurs PV PME France – résidentiel & petit tertiaire",
        "description": (
            "Solteo se positionne comme la 'plateforme n°1 des installateurs PV' en France. "
            "SaaS B2B axé sur la productivité des équipes : étude solaire complète en "
            "10 minutes, propositions commerciales professionnelles, application mobile "
            "pour visites techniques terrain, coordination commerciaux/techniciens/ADV, "
            "déclarations préalables semi-automatisées, et dossiers Enedis/Consuel automatisés. "
            "8 000+ projets réalisés avec la plateforme. Fort sur le workflow installateur "
            "mais sans cartographie/SIG, sans simulation PVGIS précise, sans CRM prospection, "
            "sans AO CRE et sans IA générative."
        ),
        "points_forts": [
            "Étude solaire complète en 10 minutes",
            "Application mobile dédiée visites terrain",
            "Génération automatique dossiers Enedis et Consuel",
            "DP mairie semi-automatisée",
            "Coordination équipes (commerce/technique/ADV)",
            "Forte adoption France – 8 000+ projets",
            "Interface intuitive orientée PME installateurs",
            "Calendrier projets et suivi avancement",
        ],
        "points_faibles": [
            "Pas de cartographie SIG / prospection foncière",
            "Pas d'intégration IGN LiDAR HD, RPG, cadastre, GPU PLU",
            "Pas de simulation PVGIS 8760h précise",
            "Pas de CRM prospection (recherche partenaires/prospects)",
            "Pas d'AO CRE PPE2 bâtiment > 500 kWc",
            "Pas d'IA conversationnelle intégrée",
            "Pas de données réseau BT/HTA Enedis",
            "Pas d'annuaire SIRENE / prospection B2B",
            "Orienté résidentiel/petit tertiaire uniquement",
        ],
        "scores": {
            "C01": 0, "C02": 1, "C03": 0, "C04": 0,
            "C05": 2, "C06": 0, "C07": 0, "C08": 3,
            "C09": 1, "C10": 2, "C11": 3, "C12": 4,
            "C13": 0, "C14": 0, "C15": 2, "C16": 3,
            "C17": 2, "C18": 0, "C19": 1, "C20": 0,
            "C21": 3,
        }
    },

    {
        "nom": "Reonic",
        "editeur": "Reonic GmbH (Allemagne)",
        "categorie": "Logiciel SaaS Installateurs PV",
        "url": "https://www.reonic.com",
        "pays_origine": "Allemagne",
        "disponible_france": True,
        "annee_creation": 2020,
        "type_licence": "SaaS B2B",
        "prix_indicatif": "Sur devis (levée Série A 13 M€ sept. 2024)",
        "modele_eco": "Abonnement SaaS + white-label",
        "cible": "Installateurs PV + stockage + IRVE + PAC – Europe (fort DACH, présent FR)",
        "description": (
            "SaaS allemand multi-technologie (PV + stockage + wallbox + pompes à chaleur) "
            "pour installateurs. Levée de fonds Série A de 13 M€ en septembre 2024. "
            "2 000+ clients installateurs en Europe. Interface disponible en français. "
            "Fonctionnalités clés : planification toiture (couverture automatique), "
            "configuration strings, sélection onduleurs, calcul économique, CRM Kanban, "
            "signature numérique, base de composants 150 000+ entrées (2 000+ fabricants), "
            "app mobile iOS/Android, option white-label. Très fort en DACH, montée en "
            "puissance sur le marché français. Manque les spécificités réglementaires FR "
            "(données IGN/cadastre/GPU/RPG, CERFA DP 13703, NF C 15-712, AO CRE PPE2, "
            "Enedis Data Connect)."
        ),
        "points_forts": [
            "Multi-technologie : PV + stockage + IRVE + PAC",
            "Base composants 150 000+ entrées (2 000+ fabricants)",
            "CRM Kanban intégré avec signature numérique",
            "Application mobile iOS/Android complète",
            "Option white-label pour les réseaux d'installateurs",
            "Interface disponible en français",
            "Forte traction Europe – 2 000+ clients",
            "Levée 13 M€ – croissance rapide",
            "Calcul économique multi-scénarios (autoconsommation, surplus, batterie)",
        ],
        "points_faibles": [
            "Pas de données foncières françaises (IGN, RPG, cadastre, GPU PLU)",
            "Pas d'intégration LiDAR HD IGN",
            "Pas de données réseau électrique Enedis BT/HTA",
            "Pas d'AO CRE PPE2 bâtiment > 500 kWc",
            "Pas de génération CERFA DP 13703 / Enedis 16702",
            "Pas de schéma unifilaire NF C 15-712 conforme",
            "Pas d'IA solaire conversationnelle",
            "Pas d'intégration Enedis Data Connect (courbes de charge)",
            "Pas d'annuaire SIRENE / prospection B2B terrain",
        ],
        "scores": {
            "C01": 1, "C02": 1, "C03": 0, "C04": 0,
            "C05": 3, "C06": 0, "C07": 0, "C08": 4,
            "C09": 1, "C10": 3, "C11": 0, "C12": 0,
            "C13": 0, "C14": 0, "C15": 3, "C16": 3,
            "C17": 1, "C18": 1, "C19": 0, "C20": 0,
            "C21": 4,
        }
    },

    # ──────────────────────────────────────────────────────────────────────────
    # CATÉGORIE G : MARKETPLACE / PLACE DE MARCHÉ PV RÉSIDENTIEL
    # ──────────────────────────────────────────────────────────────────────────
    {
        "nom": "ProjetSolaire",
        "editeur": "ProjetSolaire SAS (France)",
        "categorie": "Marketplace PV Résidentiel",
        "url": "https://www.projetsolaire.com",
        "pays_origine": "France",
        "disponible_france": True,
        "annee_creation": 2018,
        "type_licence": "Plateforme gratuite (propriétaires) + commission installateurs",
        "prix_indicatif": "Gratuit pour les propriétaires, commission sur projets",
        "modele_eco": "Marketplace / commissions + outils installateurs sur devis",
        "cible": "Propriétaires résidentiels (B2C) + installateurs RGE",
        "description": (
            "ProjetSolaire est une marketplace française mettant en relation des "
            "propriétaires souhaitant installer des panneaux solaires avec des "
            "installateurs certifiés RGE. Fonctionne sur un système d'enchères inversées : "
            "les propriétaires déposent leur projet (gratuit), les installateurs font "
            "des offres compétitives. 3 000+ projets réalisés, 100+ installateurs partenaires. "
            "Réduit le coût des projets de ~40% via la mise en concurrence. "
            "Propose aussi une place de marché matériaux et un suivi administratif. "
            "N'est PAS un logiciel de prospection ou de développement de projets PV : "
            "pas de cartographie SIG, pas de simulation PVGIS précise, pas de données "
            "foncières ou réseau électrique, pas d'AO CRE. Cible essentiellement le "
            "résidentiel grand public."
        ),
        "points_forts": [
            "Forte notoriété B2C en France",
            "Réseau 100+ installateurs RGE certifiés",
            "Réduction tarifaire ~40% via enchères",
            "Suivi administratif inclus pour les propriétaires",
            "Place de marché matériaux PV",
            "Outils de dimensionnement simplifié pour installateurs",
        ],
        "points_faibles": [
            "Modèle B2C : pas adapté aux développeurs industriels/agricoles",
            "Pas de cartographie SIG / prospection foncière multi-parcelles",
            "Pas de simulation PVGIS 8760h précise",
            "Pas de données IGN/cadastre/GPU/RPG",
            "Pas d'AO CRE PPE2 bâtiment",
            "Pas de schéma unifilaire NF C 15-712",
            "Pas d'IA intégrée",
            "Pas de CRM développeur de projets",
            "Pas d'intégration données réseau Enedis BT/HTA",
        ],
        "scores": {
            "C01": 0, "C02": 1, "C03": 0, "C04": 0,
            "C05": 1, "C06": 0, "C07": 0, "C08": 2,
            "C09": 0, "C10": 1, "C11": 1, "C12": 1,
            "C13": 0, "C14": 0, "C15": 2, "C16": 2,
            "C17": 1, "C18": 0, "C19": 0, "C20": 0,
            "C21": 2,
        }
    },

    # ──────────────────────────────────────────────────────────────────────────
    # CATÉGORIE H : PROSPECTION GRANDS PROJETS UTILITY-SCALE
    # ──────────────────────────────────────────────────────────────────────────
    {
        "nom": "Glint Solar",
        "editeur": "Glint Solar AS (Norvège)",
        "categorie": "Prospection Grands Projets Utility-Scale",
        "url": "https://www.glintsolar.com",
        "pays_origine": "Norvège",
        "disponible_france": True,
        "annee_creation": 2019,
        "type_licence": "SaaS B2B",
        "prix_indicatif": "Sur devis (pricing enterprise)",
        "modele_eco": "Abonnement SaaS – tarification sur devis",
        "cible": "Développeurs de projets solaires utility-scale + BESS (>1 MWc)",
        "description": (
            "Glint Solar est une plateforme SaaS norvégienne spécialisée dans le "
            "développement de projets solaires de grande échelle (utility-scale) et "
            "de stockage BESS. Fonctionnalités phares : prospection de sites via SIG "
            "centralisé, filtrage des terres qualifiées selon contraintes, conception "
            "préliminaire avec visualisation 3D et profil d'élévation, analyse de "
            "rendement préliminaire, feasibility BESS, collaboration d'équipes "
            "(BD/SIG/Ingénierie), gestion de pipeline de projets, export de visuels "
            "pour permitting et négociation foncière. Clients notables incluant "
            "TotalEnergies, Photosol (France), Statkraft, Recurrent Energy, Alight. "
            "Interface uniquement en anglais. Pas de données françaises spécifiques "
            "(IGN/cadastre/GPU/RPG/Enedis), pas de CRM commercial, pas de génération "
            "de documents réglementaires français."
        ),
        "points_forts": [
            "Spécialisé utility-scale : outil de référence pour les grands développeurs",
            "SIG centralisé avec filtrage avancé des contraintes foncières",
            "Visualisation 3D avec profil d'élévation (DEM)",
            "Analyse BESS (Battery Energy Storage System) intégrée",
            "Collaboration multi-équipes (BD/SIG/Ingénierie)",
            "Gestion pipeline projets (like CRM BD)",
            "Clients top-tier : TotalEnergies, Photosol, Statkraft",
            "Export visuels permitting et présentation propriétaires",
            "+80 MW de pipeline généré en 1 mois (témoignage Alight)",
        ],
        "points_faibles": [
            "Interface anglaise uniquement – pas de localisation française",
            "Pas de données françaises spécifiques (IGN, RPG, cadastre, GPU PLU)",
            "Pas d'intégration LiDAR HD IGN COPC",
            "Pas de données réseau Enedis BT/HTA FR",
            "Pas de génération documents réglementaires FR (CERFA, DP, NF C 15-712)",
            "Pas d'AO CRE PPE2 bâtiment",
            "Pas de CRM commercial (prospection client)",
            "Pas d'IA conversationnelle",
            "Pas d'intégration Enedis Data Connect",
            "Focalisé utility-scale : pas adapté résidentiel/agricole/bâtiment <500 kWc",
        ],
        "scores": {
            "C01": 3, "C02": 2, "C03": 2, "C04": 1,
            "C05": 3, "C06": 2, "C07": 0, "C08": 3,
            "C09": 0, "C10": 1, "C11": 0, "C12": 0,
            "C13": 0, "C14": 2, "C15": 2, "C16": 1,
            "C17": 0, "C18": 0, "C19": 0, "C20": 0,
            "C21": 3,
        }
    },
]

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 3 — MOTEUR DE CALCUL DES SCORES
# ════════════════════════════════════════════════════════════════════════════════

def calculer_score_global(concurrent):
    """Calcule le score global pondéré d'un concurrent (sur 100)."""
    scores = concurrent.get("scores", {})
    if not scores:
        return 0
    total = sum(scores.values())
    max_possible = len(HELIAPV_PROFILE["criteres"]) * 5
    return round((total / max_possible) * 100, 1)

def calculer_score_heliapv():
    """Calcule le score global d'HeliaPV."""
    total = sum(c["heliapv"] for c in HELIAPV_PROFILE["criteres"])
    max_possible = len(HELIAPV_PROFILE["criteres"]) * 5
    return round((total / max_possible) * 100, 1)

def calculer_score_par_groupe(concurrent):
    """Calcule les scores par groupe fonctionnel."""
    groupes = {}
    for critere in HELIAPV_PROFILE["criteres"]:
        groupe = critere["groupe"]
        cid = critere["id"]
        score_concurrent = concurrent.get("scores", {}).get(cid, 0)
        score_heliapv = critere["heliapv"]
        if groupe not in groupes:
            groupes[groupe] = {"concurrent": [], "heliapv": []}
        groupes[groupe]["concurrent"].append(score_concurrent)
        groupes[groupe]["heliapv"].append(score_heliapv)

    result = {}
    for groupe, data in groupes.items():
        result[groupe] = {
            "concurrent": round(sum(data["concurrent"]) / (len(data["concurrent"]) * 5) * 100, 1),
            "heliapv": round(sum(data["heliapv"]) / (len(data["heliapv"]) * 5) * 100, 1),
        }
    return result

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 4 — ENRICHISSEMENT IA (optionnel, via Groq)
# ════════════════════════════════════════════════════════════════════════════════

def enrichir_avec_ia(concurrent, groq_key):
    """
    Utilise Groq pour enrichir l'analyse d'un concurrent avec des informations
    actualisées sur le marché français.
    """
    if not GROQ_AVAILABLE or not groq_key:
        return None

    client = Groq(api_key=groq_key)
    prompt = f"""Tu es un expert du marché des logiciels photovoltaïques en France.

Analyse le concurrent suivant pour le marché français en 2026 :
- Nom : {concurrent['nom']}
- Éditeur : {concurrent['editeur']}
- Catégorie : {concurrent['categorie']}
- Prix indicatif : {concurrent['prix_indicatif']}
- Description : {concurrent['description']}

Donne une analyse concise en français (200 mots max) concernant :
1. Sa position réelle sur le marché français en 2026
2. Ses clients principaux en France
3. Son positionnement prix vs HeliaPV (SaaS freemium français)
4. Une menace potentielle ou opportunité pour HeliaPV

Réponds de façon structurée et factuelle."""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"  ⚠️  Enrichissement IA échoué pour {concurrent['nom']}: {e}")
        return None

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 5 — GÉNÉRATION RAPPORT HTML
# ════════════════════════════════════════════════════════════════════════════════

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Benchmark Concurrentiel HeliaPV – {date}</title>
<style>
  :root {{
    --bg: #0a0e1a;
    --card: #111827;
    --border: #1f2937;
    --accent: #f59e0b;
    --accent2: #6366f1;
    --green: #10b981;
    --red: #ef4444;
    --text: #e2e8f0;
    --muted: #94a3b8;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; padding: 2rem; }}
  h1 {{ font-size: 2rem; font-weight: 700; color: var(--accent); margin-bottom: 0.5rem; }}
  h2 {{ font-size: 1.4rem; color: var(--accent2); margin: 2rem 0 1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }}
  h3 {{ font-size: 1.1rem; color: var(--accent); margin: 1rem 0 0.5rem; }}
  .subtitle {{ color: var(--muted); margin-bottom: 2rem; }}
  .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }}
  .badge {{ display: inline-block; padding: 0.2rem 0.7rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; margin: 0.2rem; }}
  .badge-a {{ background: #065f46; color: #6ee7b7; }}
  .badge-b {{ background: #1e3a5f; color: #93c5fd; }}
  .badge-c {{ background: #4c1d95; color: #c4b5fd; }}
  .badge-d {{ background: #7c2d12; color: #fdba74; }}
  .badge-e {{ background: #374151; color: #e5e7eb; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  th {{ background: #1f2937; color: var(--accent); padding: 0.6rem 0.8rem; text-align: left; position: sticky; top: 0; }}
  td {{ padding: 0.5rem 0.8rem; border-bottom: 1px solid var(--border); vertical-align: top; }}
  tr:hover td {{ background: #1f2937; }}
  .score-bar {{ display: flex; align-items: center; gap: 0.5rem; }}
  .bar {{ height: 8px; border-radius: 4px; background: var(--accent); }}
  .bar-heliapv {{ background: var(--green); }}
  .bar-low {{ background: var(--red); }}
  .score-num {{ font-weight: 700; min-width: 35px; }}
  .score-high {{ color: var(--green); }}
  .score-med {{ color: var(--accent); }}
  .score-low {{ color: var(--red); }}
  .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
  .grid3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; }}
  ul {{ list-style: none; padding: 0; }}
  ul li::before {{ content: "▸ "; color: var(--accent); }}
  ul li {{ padding: 0.2rem 0; font-size: 0.9rem; color: var(--muted); }}
  .pros li::before {{ color: var(--green); content: "✓ "; }}
  .cons li::before {{ color: var(--red); content: "✗ "; }}
  .pros li, .cons li {{ color: var(--text); }}
  .highlight {{ color: var(--accent); font-weight: 600; }}
  .section-heliapv {{ border-left: 3px solid var(--green); padding-left: 1rem; }}
  .tag {{ display: inline-block; background: #1f2937; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; margin: 0.15rem; color: var(--muted); }}
  .overflow-x {{ overflow-x: auto; }}
  .toc a {{ color: var(--accent2); text-decoration: none; display: block; padding: 0.3rem 0; }}
  .toc a:hover {{ color: var(--accent); }}
  footer {{ margin-top: 3rem; color: var(--muted); font-size: 0.8rem; text-align: center; border-top: 1px solid var(--border); padding-top: 1rem; }}
  @media print {{ body {{ background: white; color: black; }} .card {{ border: 1px solid #ccc; }} }}
</style>
</head>
<body>

<h1>🔆 Benchmark Concurrentiel HeliaPV</h1>
<p class="subtitle">Analyse exhaustive du marché français des logiciels PV solaires — {date}</p>

<!-- TABLE DES MATIÈRES -->
<div class="card toc">
  <h2 style="margin-top:0">📋 Table des matières</h2>
  <div class="grid2">
    <div>
      <a href="#resume">1. Résumé Exécutif</a>
      <a href="#heliapv">2. Profil HeliaPV</a>
      <a href="#criteres">3. Les 21 Critères d'Évaluation</a>
      <a href="#tableau">4. Tableau Comparatif Global</a>
    </div>
    <div>
      <a href="#fiches">5. Fiches Détaillées Concurrents</a>
      <a href="#positionnement">6. Positionnement & Prix</a>
      <a href="#opportunites">7. Opportunités Différenciantes</a>
      <a href="#conclusion">8. Conclusion Stratégique</a>
    </div>
  </div>
</div>

<!-- RÉSUMÉ EXÉCUTIF -->
<div class="card" id="resume">
  <h2 style="margin-top:0">📊 1. Résumé Exécutif</h2>
  {resume_html}
</div>

<!-- PROFIL HELIAPV -->
<div class="card section-heliapv" id="heliapv">
  <h2 style="margin-top:0; color: var(--green)">✅ 2. Profil HeliaPV / AgriWeb</h2>
  {heliapv_html}
</div>

<!-- CRITÈRES -->
<div class="card" id="criteres">
  <h2 style="margin-top:0">📐 3. Les 21 Critères d'Évaluation</h2>
  {criteres_html}
</div>

<!-- TABLEAU COMPARATIF -->
<div class="card" id="tableau">
  <h2 style="margin-top:0">📊 4. Tableau Comparatif Global</h2>
  <div class="overflow-x">
  {tableau_html}
  </div>
</div>

<!-- FICHES DÉTAILLÉES -->
<div id="fiches">
  <h2>📋 5. Fiches Détaillées des Concurrents</h2>
  {fiches_html}
</div>

<!-- POSITIONNEMENT -->
<div class="card" id="positionnement">
  <h2 style="margin-top:0">💶 6. Comparatif Positionnement & Prix</h2>
  {positionnement_html}
</div>

<!-- OPPORTUNITÉS -->
<div class="card" id="opportunites">
  <h2 style="margin-top:0">🚀 7. Opportunités Différenciantes pour HeliaPV</h2>
  {opportunites_html}
</div>

<!-- CONCLUSION -->
<div class="card" id="conclusion">
  <h2 style="margin-top:0">🎯 8. Conclusion Stratégique</h2>
  {conclusion_html}
</div>

<footer>
  Rapport généré automatiquement par benchmark_concurrents_agent.py — HeliaPV / AgriWeb — {date}
</footer>
</body>
</html>"""


def score_to_html(score, max_score=100):
    """Convertit un score en HTML avec barre visuelle."""
    pct = min(100, max(0, score))
    cls = "score-high" if pct >= 70 else ("score-med" if pct >= 40 else "score-low")
    bar_cls = "bar bar-heliapv" if pct >= 70 else ("bar" if pct >= 40 else "bar bar-low")
    return (f'<div class="score-bar">'
            f'<span class="score-num {cls}">{score:.0f}</span>'
            f'<div style="flex:1;background:#1f2937;border-radius:4px;height:8px;">'
            f'<div class="{bar_cls}" style="width:{pct}%;height:8px;border-radius:4px;"></div>'
            f'</div></div>')


def generer_resume_html(scores_trie):
    """Génère le résumé exécutif."""
    heliapv_score = calculer_score_heliapv()
    nb_concurrents = len(CONCURRENTS)
    nb_categories = len(set(c["categorie"] for c in CONCURRENTS))

    top3 = scores_trie[:3]
    resume = f"""
<div class="grid3">
  <div>
    <div class="highlight" style="font-size:2rem;">{heliapv_score}%</div>
    <div>Score global HeliaPV</div>
    <div style="color:var(--muted);font-size:0.85rem;">sur 21 critères fonctionnels</div>
  </div>
  <div>
    <div class="highlight" style="font-size:2rem;">{nb_concurrents}</div>
    <div>Concurrents analysés</div>
    <div style="color:var(--muted);font-size:0.85rem;">en {nb_categories} catégories</div>
  </div>
  <div>
    <div class="highlight" style="font-size:2rem;">🥇 FR</div>
    <div>Seul acteur FR intégré</div>
    <div style="color:var(--muted);font-size:0.85rem;">prospection + CRM + docs + IA</div>
  </div>
</div>
<br>
<p><strong>Conclusion principale :</strong> Aucun concurrent identifié ne couvre simultanément les 5 piliers
d'HeliaPV : <span class="highlight">Cartographie foncière FR + Simulation PV + CRM + Documents réglementaires FR + IA Solaire</span>.
Les concurrents sont soit très techniques (PVsyst, Archelios) sans CRM/SIG,
soit cartographiques sans simulation, soit CRM génériques sans outil PV.</p>
<br>
<p><strong>Top 3 concurrents par score :</strong></p>
<ol>
{"".join(f'<li style="padding:0.3rem 0">{s["nom"]} – <span class="highlight">{s["score"]}%</span> ({s["categorie"]})</li>' for s in top3)}
</ol>
"""
    return resume


def generer_heliapv_html():
    """Génère la section profil HeliaPV."""
    score = calculer_score_heliapv()
    groupes_scores = {}
    for critere in HELIAPV_PROFILE["criteres"]:
        g = critere["groupe"]
        if g not in groupes_scores:
            groupes_scores[g] = []
        groupes_scores[g].append(critere["heliapv"])

    groupes_html = ""
    for groupe, vals in groupes_scores.items():
        pct = round(sum(vals) / (len(vals) * 5) * 100)
        groupes_html += f'<div><strong>{groupe}</strong> {score_to_html(pct)}</div>'

    return f"""
<div class="grid2">
  <div>
    <p><strong>Type :</strong> {HELIAPV_PROFILE["type"]}</p>
    <p><strong>Marché cible :</strong> {HELIAPV_PROFILE["marche_cible"]}</p>
    <p><strong>Tarification :</strong> {HELIAPV_PROFILE["tarification"]}</p>
    <p><strong>Score global :</strong> <span class="highlight">{score}%</span></p>
    <br>
    <p><strong>APIs intégrées :</strong></p>
    <p>
      {"".join(f'<span class="tag">{api}</span>' for api in
        ["IGN BAN", "IGN Cadastre", "IGN LiDAR HD COPC", "BD TOPO", "GPU PLU",
         "GeoRisques v1", "PVGIS EU", "Google Solar API", "SIRENE INSEE",
         "Enedis Data Connect", "OpenStreetMap", "GeoServer WMS/WFS",
         "Stripe", "Groq AI"])}
    </p>
  </div>
  <div>
    <h3>Scores par domaine fonctionnel</h3>
    {groupes_html}
  </div>
</div>
"""


def generer_criteres_html():
    """Génère le tableau des 21 critères."""
    rows = ""
    for c in HELIAPV_PROFILE["criteres"]:
        badge_map = {
            "Cartographie": "badge-b", "Analyse Solaire": "badge-a", "Conception PV": "badge-a",
            "Réglementaire": "badge-d", "CRM": "badge-c", "Chantier": "badge-e",
            "IA": "badge-c", "Données": "badge-b", "Plateforme": "badge-e",
        }
        badge_cls = badge_map.get(c["groupe"], "badge-e")
        rows += f"""<tr>
          <td><span class="badge {badge_cls}">{c['groupe']}</span></td>
          <td><strong>{c['id']}</strong> – {c['libelle']}</td>
          <td>{score_to_html(c['heliapv'] * 20)}</td>
          <td style="color:var(--muted);font-size:0.8rem;">{c['details']}</td>
        </tr>"""

    return f"""<div class="overflow-x"><table>
<thead><tr><th>Domaine</th><th>Critère</th><th>Score HeliaPV (/5)</th><th>Détails</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>"""


def generer_tableau_html(scores_trie):
    """Génère le tableau comparatif global."""
    # En-tête avec HeliaPV en premier
    header_row = "<tr><th>Logiciel</th><th>Catégorie</th><th>Score /100</th>"
    groupes = list(dict.fromkeys(c["groupe"] for c in HELIAPV_PROFILE["criteres"]))
    for g in groupes:
        header_row += f"<th>{g}</th>"
    header_row += "<th>Prix</th><th>FR natif</th></tr>"

    # Ligne HeliaPV
    heliapv_row = f'<tr style="background:#0d2b1a;border-left:3px solid var(--green)">'
    heliapv_row += f'<td><strong style="color:var(--green)">★ HeliaPV</strong></td>'
    heliapv_row += f'<td><span class="badge badge-a">Solution complète</span></td>'
    heliapv_row += f'<td>{score_to_html(calculer_score_heliapv())}</td>'
    for g in groupes:
        g_scores = [c["heliapv"] for c in HELIAPV_PROFILE["criteres"] if c["groupe"] == g]
        pct = round(sum(g_scores) / (len(g_scores) * 5) * 100)
        heliapv_row += f'<td>{score_to_html(pct)}</td>'
    heliapv_row += '<td style="color:var(--green)">Freemium</td><td style="color:var(--green)">✅</td></tr>'

    # Lignes concurrents
    concurrents_rows = ""
    for s in scores_trie:
        c = next(x for x in CONCURRENTS if x["nom"] == s["nom"])
        g_scores_html = ""
        for g in groupes:
            crit_ids = [cr["id"] for cr in HELIAPV_PROFILE["criteres"] if cr["groupe"] == g]
            vals = [c.get("scores", {}).get(cid, 0) for cid in crit_ids]
            pct = round(sum(vals) / (len(vals) * 5) * 100)
            g_scores_html += f'<td>{score_to_html(pct)}</td>'

        fr_badge = ('✅' if c.get('pays_origine') == 'France'
                    else ('⚠️' if c.get('disponible_france') else '❌'))
        concurrents_rows += f"""<tr>
          <td><strong>{c['nom']}</strong><br><small style="color:var(--muted)">{c['editeur'][:30]}</small></td>
          <td><small>{c['categorie']}</small></td>
          <td>{score_to_html(s['score'])}</td>
          {g_scores_html}
          <td style="font-size:0.8rem">{c['prix_indicatif'][:25]}</td>
          <td style="text-align:center">{fr_badge}</td>
        </tr>"""

    return f"""<table>
<thead>{header_row}</thead>
<tbody>{heliapv_row}{concurrents_rows}</tbody>
</table>"""


def generer_fiches_html(enrichissements=None):
    """Génère les fiches détaillées de chaque concurrent."""
    html = ""
    categories = {}
    for c in CONCURRENTS:
        cat = c["categorie"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(c)

    cat_badges = {
        "Simulation & Conception PV": "badge-a",
        "Prospection & Données Solaires": "badge-b",
        "Cartographie & SIG Énergie": "badge-b",
        "Conseil & Outils CRE": "badge-d",
        "CRM Énergie": "badge-c",
        "Monitoring & CRM Monitoring": "badge-e",
        "Données Aériennes & IA": "badge-c",
    }

    for cat, concurrents_cat in categories.items():
        badge_cls = cat_badges.get(cat, "badge-e")
        html += f'<h3><span class="badge {badge_cls}">{cat}</span></h3>'

        for c in concurrents_cat:
            score = calculer_score_global(c)
            enrich = (enrichissements or {}).get(c["nom"], None)

            pros = "".join(f"<li>{p}</li>" for p in c.get("points_forts", []))
            cons = "".join(f"<li>{p}</li>" for p in c.get("points_faibles", []))
            enrich_html = ""
            if enrich:
                enrich_html = f'<div class="card" style="background:#0a1628;margin-top:0.5rem"><h3 style="color:var(--accent2)">🤖 Analyse IA Groq</h3><p style="font-size:0.9rem;line-height:1.6">{enrich.replace(chr(10), "<br>")}</p></div>'

            fr_tag = ('🇫🇷 Éditeur français' if c.get('pays_origine') == 'France'
                      else ('🌐 Disponible FR' if c.get('disponible_france') else '🚫 Non disponible FR'))

            html += f"""
<div class="card" id="{c['nom'].replace(' ', '_').replace('/', '_')}">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem">
    <div>
      <h3 style="color:var(--text)">{c['nom']}</h3>
      <p style="color:var(--muted);font-size:0.9rem">{c['editeur']} &nbsp;|&nbsp;
         Fondé : {c.get('annee_creation','—')} &nbsp;|&nbsp;
         <span style="color:var(--accent)">{fr_tag}</span></p>
    </div>
    <div style="text-align:right">
      {score_to_html(score)}
      <div style="font-size:0.8rem;color:var(--muted)">{c['type_licence']}</div>
    </div>
  </div>
  <p style="margin:0.8rem 0;font-size:0.9rem;line-height:1.6">{c['description']}</p>
  <div class="grid2">
    <div>
      <p><strong style="color:var(--green)">✅ Points forts</strong></p>
      <ul class="pros">{pros}</ul>
    </div>
    <div>
      <p><strong style="color:var(--red)">❌ Points faibles vs HeliaPV</strong></p>
      <ul class="cons">{cons}</ul>
    </div>
  </div>
  <p style="margin-top:0.8rem"><strong>Tarification :</strong> {c['prix_indicatif']} &nbsp;|&nbsp;
     <strong>Modèle :</strong> {c['modele_eco']} &nbsp;|&nbsp;
     <strong>Cible :</strong> {c['cible']}</p>
  {enrich_html}
</div>"""

    return html


def generer_positionnement_html():
    """Génère le comparatif positionnement et prix."""
    rows = ""
    for c in CONCURRENTS:
        fr = "🇫🇷" if c.get("pays_origine") == "France" else ("✅" if c.get("disponible_france") else "❌")
        score = calculer_score_global(c)
        rows += f"""<tr>
          <td><strong>{c['nom']}</strong></td>
          <td>{c['categorie']}</td>
          <td>{c['prix_indicatif']}</td>
          <td>{c['modele_eco']}</td>
          <td>{fr}</td>
          <td>{score_to_html(score)}</td>
        </tr>"""

    heliapv_score = calculer_score_heliapv()
    return f"""
<table>
<thead>
  <tr><th>Logiciel</th><th>Catégorie</th><th>Prix indicatif</th><th>Modèle économique</th><th>FR</th><th>Score</th></tr>
</thead>
<tbody>
  <tr style="background:#0d2b1a">
    <td><strong style="color:var(--green)">★ HeliaPV</strong></td>
    <td>Solution complète SaaS PV</td>
    <td style="color:var(--green)">Freemium (50 rech. trial) + abonnements</td>
    <td>SaaS Stripe multi-niveaux</td>
    <td>🇫🇷</td>
    <td>{score_to_html(heliapv_score)}</td>
  </tr>
  {rows}
</tbody>
</table>
<br>
<p style="color:var(--muted);font-size:0.9rem">
  <strong>Constat :</strong> HeliaPV est le <strong>seul acteur français</strong> à proposer
  une solution freemium accessible aux PME couvrant prospection, simulation, CRM et
  génération documentaire réglementaire française dans un seul outil.
</p>
"""


def generer_opportunites_html():
    """Génère l'analyse des opportunités différenciantes."""
    return """
<div class="grid2">
  <div>
    <h3>🏆 Avantages compétitifs HeliaPV</h3>
    <ul>
      <li><strong>Intégration unique données françaises :</strong> Seule solution combinant IGN (BAN, cadastre, LiDAR HD), GPU (PLU/PLUi), GeoRisques, RPG, SIRENE, Enedis dans un seul outil</li>
      <li><strong>Génération documents réglementaires FR :</strong> CERFA DP, CERFA Enedis 16702, schéma unifilaire NF C 15-712 – aucun concurrent ne le propose nativement</li>
      <li><strong>AO CRE PPE2 :</strong> Wizard unique sur le marché pour répondre aux appels d'offres bâtiment >500 kWc avec bilan carbone par pays</li>
      <li><strong>CRM + Technique = One-stop-shop :</strong> Pas besoin d'alterner 3-4 outils (SIG + simulation + CRM + documents)</li>
      <li><strong>Modèle freemium accessible :</strong> Seul concurrent à offrir un essai gratuit significatif vs licences annuelles €€€</li>
      <li><strong>Helia IA française :</strong> Assistant IA dédié au marché PV français avec function calling réel sur la plateforme</li>
    </ul>
  </div>
  <div>
    <h3>⚡ Axes de différenciation à renforcer</h3>
    <ul>
      <li><strong>Simulation P50/P90 bankable :</strong> PVsyst reste le standard bancaire – une certification ou import PVsyst serait un avantage majeur</li>
      <li><strong>Base modules certifiés Certisolis :</strong> Déjà intégrée, à valoriser dans la communication</li>
      <li><strong>Intégration BIM/IFC :</strong> Tendance montante pour les grands projets (>1 MWc)</li>
      <li><strong>API ouverte :</strong> Exposer certaines fonctionnalités en API pour les intégrateurs</li>
      <li><strong>Mobile natif :</strong> Application mobile pour la visite technique terrain</li>
      <li><strong>Export PVsyst :</strong> Export au format PVsyst pour validation bancaire</li>
      <li><strong>Connecteurs ERP :</strong> Intégration Sage, Cegid, SAP pour les grands comptes</li>
    </ul>
  </div>
</div>
<br>
<h3>🎯 Segments à cibler en priorité</h3>
<div class="grid3">
  <div class="card" style="background:#0d1f12">
    <strong style="color:var(--green)">1. Développeurs PV médians</strong><br>
    <small>Projets 100 kWc – 10 MWc, équipes 5-50 personnes, aujourd'hui sur PVsyst + Excel + GIS séparés</small>
  </div>
  <div class="card" style="background:#0d1a2b">
    <strong style="color:var(--accent2)">2. Installateurs C&I</strong><br>
    <small>Toitures industrie/tertiaire, cherchent tout-en-un : prospection + calpinage + devis + dossier admin</small>
  </div>
  <div class="card" style="background:#1a0d2b">
    <strong style="color:var(--accent)">3. Bureaux d'études ENR</strong><br>
    <small>Besoin de rapports bankables, suivi chantier IEC 62446, AO CRE PPE2 – segment premium</small>
  </div>
</div>
"""


def generer_conclusion_html(scores_trie):
    """Génère la conclusion stratégique."""
    heliapv_score = calculer_score_heliapv()
    best_competitor = scores_trie[0] if scores_trie else {"nom": "—", "score": 0}

    return f"""
<p>Suite à l'analyse de <strong>{len(CONCURRENTS)} logiciels concurrents</strong> répartis en
{len(set(c['categorie'] for c in CONCURRENTS))} catégories, <strong>HeliaPV obtient un score de {heliapv_score:.0f}%</strong>
contre <strong>{best_competitor['score']:.0f}%</strong> pour le meilleur concurrent direct
({best_competitor['nom']}).</p>

<br>

<h3>🔑 Points clés</h3>
<ul>
  <li><strong>Aucun concurrent direct identifié sur le territoire français</strong> couvrant l'ensemble de la chaîne de valeur PV : prospection géographique → simulation → CRM → documents réglementaires → suivi chantier</li>
  <li>Les concurrents sont fragmentés : PVsyst (simulation), Archelios (conception), GIS&Sol (cartographie), Pegase (ERP), Salesforce (CRM) – HeliaPV remplace 3 à 5 outils</li>
  <li>Le marché US/UK est couvert par Aurora Solar et Helioscope mais <strong>sans adaptation au droit français</strong> (GPU, cadastre, normes NF, CERFA, Enedis)</li>
  <li>L'intégration du <strong>LiDAR HD gratuit IGN</strong> est un avantage compétitif rare – seul HeliaPV l'exploite nativement pour l'analyse de toitures commerciales</li>
  <li>Le module <strong>AO CRE PPE2</strong> est unique sur le marché français</li>
</ul>

<br>

<h3>📈 Recommandations stratégiques</h3>
<ul>
  <li>Positionner HeliaPV comme la <strong>"suite complète pour développeurs PV français"</strong> face à la fragmentation des outils existants</li>
  <li>Communiquer sur la <strong>conformité réglementaire française</strong> (CERFA, NF C 15-712, AO CRE PPE2) comme différenciateur clé</li>
  <li>Développer un <strong>partenariat ou import/export PVsyst</strong> pour lever le frein bancaire</li>
  <li>Cibler en priorité les équipes de développeurs PV qui utilisent aujourd'hui 3+ outils séparés</li>
  <li>Lancer une stratégie de <strong>content marketing technique</strong> autour des APIs IGN, GPU, Enedis pour attirer les bureaux d'études</li>
</ul>
"""


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 6 — GÉNÉRATION RAPPORT PDF (optionnel)
# ════════════════════════════════════════════════════════════════════════════════

def generer_pdf(output_path, scores_trie):
    """Génère un rapport PDF condensé avec ReportLab."""
    if not REPORTLAB_AVAILABLE:
        print("⚠️  ReportLab non disponible – PDF impossible")
        return

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    styles = getSampleStyleSheet()
    story = []

    # Titre
    title_style = ParagraphStyle('Title', parent=styles['Title'],
                                  fontSize=20, textColor=colors.HexColor('#f59e0b'))
    story.append(Paragraph("Benchmark Concurrentiel HeliaPV / AgriWeb", title_style))
    story.append(Paragraph(f"Marché des logiciels PV en France — {datetime.datetime.now().strftime('%B %Y')}",
                            styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    # Tableau synthèse
    headers = ["Logiciel", "Catégorie", "Score/100", "Prix", "FR"]
    data = [headers]

    # HeliaPV en premier
    data.append(["★ HeliaPV", "Solution complète SaaS", f"{calculer_score_heliapv():.0f}%",
                  "Freemium+Stripe", "🇫🇷"])

    for s in scores_trie:
        c = next(x for x in CONCURRENTS if x["nom"] == s["nom"])
        fr = "🇫🇷" if c.get("pays_origine") == "France" else ("✅" if c.get("disponible_france") else "❌")
        data.append([
            c["nom"][:30],
            c["categorie"][:30],
            f"{s['score']:.0f}%",
            c["prix_indicatif"][:25],
            fr,
        ])

    table = Table(data, colWidths=[5*cm, 6*cm, 3*cm, 6*cm, 2*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#065f46')),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 2), (-1, -1), [colors.HexColor('#111827'), colors.HexColor('#0a0e1a')]),
        ('TEXTCOLOR', (0, 2), (-1, -1), colors.HexColor('#e2e8f0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#1f2937')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(table)

    doc.build(story)
    print(f"✅ PDF généré : {output_path}")


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 7 — POINT D'ENTRÉE PRINCIPAL
# ════════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Agent de benchmark concurrentiel HeliaPV – marché français PV"
    )
    parser.add_argument(
        "--output", default="benchmark_concurrents_heliapv.html",
        help="Chemin du rapport HTML de sortie (défaut: benchmark_concurrents_heliapv.html)"
    )
    parser.add_argument(
        "--format", choices=["html", "pdf", "both"], default="html",
        help="Format de sortie (défaut: html)"
    )
    parser.add_argument(
        "--groq-key", default=os.getenv("GROQ_API_KEY", ""),
        help="Clé API Groq pour enrichissement IA (optionnel)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Exporter aussi les données brutes en JSON"
    )
    args = parser.parse_args()

    print("╔══════════════════════════════════════════════════════════╗")
    print("║  BENCHMARK CONCURRENTIEL HELIAPV – Agent autonome       ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"📅 Date d'analyse : {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"🔍 Concurrents à analyser : {len(CONCURRENTS)}")
    print(f"📊 Critères d'évaluation : {len(HELIAPV_PROFILE['criteres'])}")
    print()

    # ── Calcul des scores ───────────────────────────────────────────────────
    print("🔢 Calcul des scores...")
    scores = []
    for c in CONCURRENTS:
        score = calculer_score_global(c)
        scores.append({"nom": c["nom"], "score": score, "categorie": c["categorie"]})
        print(f"   {c['nom'][:40]:<40} → {score:5.1f}%")

    scores_trie = sorted(scores, key=lambda x: x["score"], reverse=True)
    heliapv_score = calculer_score_heliapv()
    print(f"\n   {'★ HeliaPV':40} → {heliapv_score:5.1f}%  ← RÉFÉRENCE")
    print()

    # ── Enrichissement IA ──────────────────────────────────────────────────
    enrichissements = {}
    if args.groq_key and GROQ_AVAILABLE:
        print("🤖 Enrichissement IA via Groq...")
        for c in CONCURRENTS:
            print(f"   → Analyse de {c['nom']}...")
            result = enrichir_avec_ia(c, args.groq_key)
            if result:
                enrichissements[c["nom"]] = result
        print()

    # ── Génération du rapport HTML ─────────────────────────────────────────
    date_str = datetime.datetime.now().strftime("%d %B %Y")

    print("✍️  Génération du rapport HTML...")
    html_content = HTML_TEMPLATE.format(
        date=date_str,
        resume_html=generer_resume_html(scores_trie),
        heliapv_html=generer_heliapv_html(),
        criteres_html=generer_criteres_html(),
        tableau_html=generer_tableau_html(scores_trie),
        fiches_html=generer_fiches_html(enrichissements),
        positionnement_html=generer_positionnement_html(),
        opportunites_html=generer_opportunites_html(),
        conclusion_html=generer_conclusion_html(scores_trie),
    )

    output_path = Path(args.output)
    output_path.write_text(html_content, encoding="utf-8")
    print(f"✅ Rapport HTML généré : {output_path.resolve()}")

    # ── Export JSON optionnel ──────────────────────────────────────────────
    if args.json:
        json_path = output_path.with_suffix(".json")
        json_data = {
            "date_analyse": date_str,
            "heliapv": {
                **HELIAPV_PROFILE,
                "score_global": heliapv_score
            },
            "concurrents": [
                {**c, "score_global": calculer_score_global(c),
                 "scores_par_groupe": calculer_score_par_groupe(c)}
                for c in CONCURRENTS
            ],
            "classement": scores_trie,
        }
        json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ Données JSON exportées : {json_path.resolve()}")

    # ── Export PDF optionnel ──────────────────────────────────────────────
    if args.format in ("pdf", "both"):
        pdf_path = output_path.with_suffix(".pdf")
        print(f"✍️  Génération du rapport PDF...")
        generer_pdf(pdf_path, scores_trie)

    # ── Résumé final ──────────────────────────────────────────────────────
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  RÉSUMÉ DES SCORES                                       ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║  ★ HeliaPV                          {heliapv_score:5.1f}% (RÉFÉRENCE)  ║")
    print("╠══════════════════════════════════════════════════════════╣")
    for s in scores_trie:
        diff = s['score'] - heliapv_score
        diff_str = f"{diff:+.1f}%"
        icon = "🔴" if diff >= 0 else "🟢"
        print(f"║  {icon} {s['nom'][:34]:<34} {s['score']:5.1f}%  ({diff_str:>7})  ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    print(f"🎯 HeliaPV arrive EN TÊTE sur {sum(1 for s in scores_trie if s['score'] < heliapv_score)}/{len(CONCURRENTS)} concurrents analysés.")
    print(f"📄 Rapport disponible : {output_path.resolve()}")
    print()
    print("💡 Conseil : Ouvrir le fichier HTML dans un navigateur pour le rapport interactif complet.")


if __name__ == "__main__":
    main()
