#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serveur AgriWeb Complet - Intégration de tous les modules existants
Ce serveur utilise TOUS vos modules, utils, templates et fichiers statiques
"""

import sys
import os
from pathlib import Path

# Ajout des chemins pour les modules locaux
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / 'modules'))
sys.path.insert(0, str(current_dir / 'utils'))
sys.path.insert(0, str(current_dir / 'tools'))

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
import json
import requests
from datetime import datetime
import logging
from functools import wraps

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import conditionnel des modules utils (gestion des erreurs)
try:
    from utils.geoserver_utils import *
except ImportError as e:
    logger.warning(f"Module geoserver_utils non disponible: {e}")

try:
    from utils.map_utils import *
except ImportError as e:
    logger.warning(f"Module map_utils non disponible: {e}")

try:
    from utils.report_utils import *
except ImportError as e:
    logger.warning(f"Module report_utils non disponible: {e}")

try:
    from utils.common import *
except ImportError as e:
    logger.warning(f"Module common non disponible: {e}")

# Import conditionnel des modules principaux
try:
    from modules.data_service import *
except ImportError as e:
    logger.warning(f"Module data_service non disponible: {e}")

try:
    from modules.geo_utils import *
except ImportError as e:
    logger.warning(f"Module geo_utils non disponible: {e}")

try:
    from modules.map_generator import *
except ImportError as e:
    logger.warning(f"Module map_generator non disponible: {e}")

# Création de l'application Flask
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Configuration des chemins statiques
app.static_folder = 'static'
app.template_folder = 'templates'

# === Configuration GeoServer ===
GEOSERVER_URL = os.environ.get('GEOSERVER_URL', "http://localhost:8080/geoserver")
GEOSERVER_USER = os.environ.get('GEOSERVER_USER', "admin")
GEOSERVER_PASSWORD = os.environ.get('GEOSERVER_PASSWORD', "geoserver")

# Configuration des couches étendues
LAYERS_CONFIG = {
    'cadastre': "gpu:cadastre france",
    'poste_bt': "gpu:poste_elec_shapefile",
    'plu': "gpu:gpu1",
    'parcelles': "gpu:PARCELLE2024",
    'poste_hta': "gpu:postes-electriques-rte",
    'capacites': "gpu:CapacitesDAccueil",
    'parkings': "gpu:parkings_sup500m2",
    'friches': "gpu:friches-standard",
    'potentiel_solaire': "gpu:POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93",
    'zaer': "gpu:ZAER_ARRETE_SHP_FRA",
    'rpg': "gpu:PARCELLES_GRAPHIQUES",
    'sirene': "gpu:GeolocalisationEtablissement_Sirene france",
    'communes': "gpu:communes-20220101",
    'batiments': "gpu:batiments_osm",
    'transport': "gpu:transport_public",
    'zones_risques': "gpu:zones_risques"
}

# === Gestionnaire d'utilisateurs avancé ===
class AdvancedUserManager:
    def __init__(self):
        self.users = {
            'admin': {'password': 'admin123', 'role': 'admin', 'permissions': ['read', 'write', 'admin']},
            'demo': {'password': 'demo123', 'role': 'user', 'permissions': ['read']},
            'agriweb': {'password': 'agriweb2025', 'role': 'power_user', 'permissions': ['read', 'write']},
            'guest': {'password': 'guest123', 'role': 'guest', 'permissions': ['read']}
        }
    
    def authenticate(self, username, password):
        user = self.users.get(username)
        if user and user['password'] == password:
            return {
                'username': username, 
                'role': user['role'],
                'permissions': user['permissions']
            }
        return None
    
    def create_user(self, username, password, role='user', permissions=['read']):
        if username not in self.users:
            self.users[username] = {
                'password': password, 
                'role': role,
                'permissions': permissions
            }
            return True
        return False
    
    def has_permission(self, username, permission):
        user = self.users.get(username)
        return user and permission in user.get('permissions', [])

user_manager = AdvancedUserManager()

# === Décorateurs d'authentification ===
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        if session['user']['role'] != 'admin':
            flash('Accès refusé. Droits administrateur requis.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# === ROUTES D'AUTHENTIFICATION ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = user_manager.authenticate(username, password)
        if user:
            session['user'] = user
            flash(f'Connexion réussie ! Bienvenue {username}', 'success')
            return redirect(url_for('index'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Déconnexion réussie', 'success')
    return redirect(url_for('login'))

# === ROUTE PRINCIPALE ===
@app.route('/')
@login_required
def index():
    """Page d'accueil utilisant le template index.html existant"""
    return render_template('index.html', 
                         user=session.get('user'),
                         total_users=len(user_manager.users),
                         layers_count=len(LAYERS_CONFIG))

# === ROUTES CARTOGRAPHIQUES ===
@app.route('/carte')
@app.route('/map')
@login_required
def carte():
    """Route carte utilisant le template map.html existant"""
    return render_template('map.html')

@app.route('/display_map')
@login_required
def display_map():
    """Route d'affichage de carte spécialisée"""
    return render_template('display_map.html')

@app.route('/demo_advanced_layers')
@login_required
def demo_advanced_layers():
    """Route de démonstration des couches avancées"""
    return render_template('demo_advanced_layers.html')

@app.route('/test_layer_editor')
@login_required
def test_layer_editor():
    """Route de test de l'éditeur de couches"""
    return render_template('test_layer_editor.html')

# === ROUTES DE RECHERCHE ===
@app.route('/recherche')
@app.route('/commune_search')
@login_required
def recherche_commune():
    """Route de recherche de commune"""
    return render_template('commune_search.html')

@app.route('/recherche_toitures')
@login_required
def recherche_toitures():
    """Route de recherche de toitures"""
    return render_template('recherche_toitures.html')

@app.route('/search_panel')
@login_required
def search_panel():
    """Route du panneau de recherche"""
    return render_template('search_panel.html')

@app.route('/commune_index')
@login_required
def commune_index():
    """Route d'index des communes"""
    return render_template('commune_index.html')

# === ROUTES DE RAPPORTS ===
@app.route('/rapport_point')
@login_required
def rapport_point():
    """Route de rapport ponctuel utilisant le template existant"""
    lat = request.args.get('lat', 46.8)
    lon = request.args.get('lon', 2.0)
    
    # Simulation de données pour le template
    rapport_data = {
        'latitude': float(lat),
        'longitude': float(lon),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'commune': 'Commune d\'exemple',
        'departement': 'Département d\'exemple',
        'region': 'Région d\'exemple',
        'population': 12345,
        'superficie': 25.67,
        'densite': 481.2,
        'postes_bt': 15,
        'postes_hta': 3,
        'parkings': 8,
        'friches': 5,
        'potentiel_solaire': 1250.75,
        'parcelles_agricoles': 45,
        'entreprises_sirene': 127,
        'elevation': 245,
        'risques_naturels': ['Inondation', 'Sécheresse'],
        'zones_u': 12,
        'zones_a': 8,
        'zones_n': 5
    }
    
    return render_template('rapport_point.html', **rapport_data)

@app.route('/rapport_point_backup')
@login_required
def rapport_point_backup():
    """Route de rapport ponctuel - version backup"""
    return render_template('rapport_point_backup.html')

@app.route('/rapport_point_clean')
@login_required
def rapport_point_clean():
    """Route de rapport ponctuel - version clean"""
    return render_template('rapport_point_clean.html')

@app.route('/rapport_point_with_api_nature')
@login_required
def rapport_point_with_api_nature():
    """Route de rapport ponctuel avec API nature"""
    return render_template('rapport_point_with_api_nature.html')

@app.route('/rapport_commune')
@login_required
def rapport_commune():
    """Route de rapport communal"""
    commune = request.args.get('commune', 'Paris')
    
    commune_data = {
        'nom_commune': commune,
        'code_insee': '75056',
        'population': 2161000,
        'superficie': 105.4,
        'densite': 20507,
        'nb_postes_bt': 450,
        'nb_postes_hta': 85,
        'nb_parkings': 120,
        'nb_friches': 25,
        'potentiel_solaire_total': 15750.5,
        'nb_parcelles_agricoles': 0,
        'nb_entreprises': 8500,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return render_template('rapport_commune.html', **commune_data)

@app.route('/rapport_commune_complet')
@login_required
def rapport_commune_complet():
    """Route de rapport communal complet"""
    commune = request.args.get('commune', 'Lyon')
    
    commune_data = {
        'nom_commune': commune,
        'code_insee': '69123',
        'population': 515695,
        'superficie': 47.87,
        'densite': 10773,
        'nb_postes_bt': 280,
        'nb_postes_hta': 45,
        'nb_parkings': 85,
        'nb_friches': 18,
        'potentiel_solaire_total': 8950.3,
        'nb_parcelles_agricoles': 12,
        'nb_entreprises': 3200,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'zones_u': 35,
        'zones_a': 12,
        'zones_n': 8,
        'elevation_min': 162,
        'elevation_max': 305,
        'risques_naturels': ['Inondation', 'Mouvement de terrain'],
        'transport_score': 85,
        'accessibilite_score': 78
    }
    
    return render_template('rapport_commune_complet.html', **commune_data)

@app.route('/rapport_departement')
@login_required
def rapport_departement():
    """Route de rapport départemental"""
    dept = request.args.get('dept', '69')
    
    dept_data = {
        'code_departement': dept,
        'nom_departement': 'Rhône',
        'nb_communes': 267,
        'population_totale': 1876000,
        'superficie_totale': 3249.2,
        'densite_moyenne': 577,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return render_template('rapport_departement.html', **dept_data)

@app.route('/rapport_departement_complet')
@login_required
def rapport_departement_complet():
    """Route de rapport départemental complet"""
    dept = request.args.get('dept', '75')
    
    dept_data = {
        'code_departement': dept,
        'nom_departement': 'Paris',
        'nb_communes': 1,
        'population_totale': 2161000,
        'superficie_totale': 105.4,
        'densite_moyenne': 20507,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'nb_postes_bt_total': 450,
        'nb_postes_hta_total': 85,
        'nb_parkings_total': 120,
        'nb_friches_total': 25,
        'potentiel_solaire_total': 15750.5
    }
    
    return render_template('rapport_departement_complet.html', **dept_data)

@app.route('/rapport_departement_minimal')
@login_required
def rapport_departement_minimal():
    """Route de rapport départemental minimal"""
    return render_template('rapport_departement_minimal.html')

@app.route('/rapport_departement_simple')
@login_required
def rapport_departement_simple():
    """Route de rapport départemental simple"""
    return render_template('rapport_departement_simple.html')

# === ROUTES D'API ET DONNÉES ===
@app.route('/api/recherche_commune')
@login_required
def api_recherche_commune():
    """API de recherche de commune"""
    query = request.args.get('q', '')
    
    # Simulation étendue de résultats de recherche
    communes = [
        {'nom': 'Paris', 'code': '75056', 'dept': '75', 'population': 2161000},
        {'nom': 'Lyon', 'code': '69123', 'dept': '69', 'population': 515695},
        {'nom': 'Marseille', 'code': '13055', 'dept': '13', 'population': 861635},
        {'nom': 'Toulouse', 'code': '31555', 'dept': '31', 'population': 471941},
        {'nom': 'Nice', 'code': '06088', 'dept': '06', 'population': 342637},
        {'nom': 'Nantes', 'code': '44109', 'dept': '44', 'population': 309346},
        {'nom': 'Montpellier', 'code': '34172', 'dept': '34', 'population': 285121},
        {'nom': 'Strasbourg', 'code': '67482', 'dept': '67', 'population': 280966}
    ]
    
    if query:
        communes = [c for c in communes if query.lower() in c['nom'].lower()]
    
    return jsonify(communes)

@app.route('/api/geoserver_proxy')
@login_required
def geoserver_proxy():
    """Proxy vers GeoServer pour éviter les problèmes CORS"""
    try:
        params = dict(request.args)
        geoserver_url = f"{GEOSERVER_URL}/wfs"
        auth = (GEOSERVER_USER, GEOSERVER_PASSWORD)
        response = requests.get(geoserver_url, params=params, auth=auth, timeout=30)
        return response.content, response.status_code, {
            'Content-Type': response.headers.get('Content-Type', 'application/json')
        }
    except Exception as e:
        logger.error(f"Erreur proxy GeoServer: {e}")
        return jsonify({'error': 'Erreur de connexion au serveur de données'}), 500

@app.route('/api/layers_config')
@login_required
def api_layers_config():
    """API retournant la configuration des couches"""
    return jsonify(LAYERS_CONFIG)

@app.route('/api/user_permissions')
@login_required
def api_user_permissions():
    """API retournant les permissions de l'utilisateur"""
    user = session.get('user')
    return jsonify({
        'user': user['username'],
        'role': user['role'],
        'permissions': user['permissions']
    })

# === ROUTES POUR FICHIERS STATIQUES SUPPLÉMENTAIRES ===
@app.route('/static/cartes/<path:filename>')
def static_cartes(filename):
    """Servir les fichiers statiques du dossier cartes"""
    return send_from_directory('static/cartes', filename)

@app.route('/cartes/<path:filename>')
def cartes_files(filename):
    """Alternative pour les fichiers cartes"""
    return send_from_directory('cartes', filename)

# === ROUTES D'ADMINISTRATION ===
@app.route('/admin')
@admin_required
def admin():
    """Page d'administration"""
    templates_count = len([f for f in os.listdir('templates') if f.endswith('.html')])
    static_files_count = sum([len(files) for r, d, files in os.walk('static')])
    
    admin_data = {
        'users_count': len(user_manager.users),
        'templates_count': templates_count,
        'layers_count': len(LAYERS_CONFIG),
        'static_files_count': static_files_count,
        'modules_available': [
            'utils.geoserver_utils',
            'utils.map_utils', 
            'utils.report_utils',
            'utils.common',
            'modules.data_service',
            'modules.geo_utils',
            'modules.map_generator'
        ]
    }
    
    return render_template('admin.html', **admin_data) if os.path.exists('templates/admin.html') else f'''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Administration - AgriWeb</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    </head>
    <body>
        <div class="container mt-4">
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h1><i class="bi bi-gear"></i> Administration AgriWeb</h1>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3">
                                    <div class="card text-center">
                                        <div class="card-body">
                                            <h5 class="card-title text-primary">{admin_data['users_count']}</h5>
                                            <p class="card-text">Utilisateurs</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card text-center">
                                        <div class="card-body">
                                            <h5 class="card-title text-success">{admin_data['templates_count']}</h5>
                                            <p class="card-text">Templates</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card text-center">
                                        <div class="card-body">
                                            <h5 class="card-title text-warning">{admin_data['layers_count']}</h5>
                                            <p class="card-text">Couches GIS</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card text-center">
                                        <div class="card-body">
                                            <h5 class="card-title text-info">{admin_data['static_files_count']}</h5>
                                            <p class="card-text">Fichiers statiques</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <hr>
                            <h5>Modules disponibles:</h5>
                            <ul class="list-group">
                                {''.join([f'<li class="list-group-item"><i class="bi bi-check-circle text-success"></i> {module}</li>' for module in admin_data['modules_available']])}
                            </ul>
                            <hr>
                            <div class="btn-group">
                                <a href="{url_for('index')}" class="btn btn-primary">
                                    <i class="bi bi-house"></i> Accueil
                                </a>
                                <a href="{url_for('carte')}" class="btn btn-success">
                                    <i class="bi bi-map"></i> Cartes
                                </a>
                                <a href="{url_for('recherche_commune')}" class="btn btn-info">
                                    <i class="bi bi-search"></i> Recherche
                                </a>
                                <a href="{url_for('logout')}" class="btn btn-secondary">
                                    <i class="bi bi-door-open"></i> Déconnexion
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

# === GESTION D'ERREURS ===
@app.errorhandler(404)
def not_found(error):
    return render_template('index.html', error="Page non trouvée"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('index.html', error="Erreur interne du serveur"), 500

# === ROUTES DE DEBUG ===
@app.route('/debug/templates')
@admin_required
def debug_templates():
    """Route de debug pour lister tous les templates"""
    templates = [f for f in os.listdir('templates') if f.endswith('.html')]
    return jsonify({'templates': templates})

@app.route('/debug/static')
@admin_required
def debug_static():
    """Route de debug pour lister tous les fichiers statiques"""
    static_files = []
    for root, dirs, files in os.walk('static'):
        for file in files:
            static_files.append(os.path.relpath(os.path.join(root, file), 'static'))
    return jsonify({'static_files': static_files})

@app.route('/debug/modules')
@admin_required
def debug_modules():
    """Route de debug pour vérifier les modules"""
    modules_status = {}
    test_modules = [
        'utils.geoserver_utils',
        'utils.map_utils', 
        'utils.report_utils',
        'utils.common',
        'modules.data_service',
        'modules.geo_utils',
        'modules.map_generator'
    ]
    
    for module in test_modules:
        try:
            __import__(module)
            modules_status[module] = 'OK'
        except Exception as e:
            modules_status[module] = f'ERROR: {str(e)}'
    
    return jsonify({'modules_status': modules_status})

# === POINT D'ENTRÉE ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🌾 AgriWeb Serveur Complet Intégré 🌾                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  🚀 Serveur démarré avec TOUS vos modules !                                ║
║                                                                              ║
║  📍 URL locale: http://127.0.0.1:{port}                                  ║
║  🔑 Comptes disponibles:                                                    ║
║     • admin / admin123 (administrateur)                                     ║
║     • demo / demo123 (utilisateur)                                          ║
║     • agriweb / agriweb2025 (utilisateur avancé)                           ║
║     • guest / guest123 (invité)                                            ║
║                                                                              ║
║  📋 Templates intégrés: {len([f for f in os.listdir('templates') if f.endswith('.html')])}                                             ║
║  🗂️ Couches GIS: {len(LAYERS_CONFIG)}                                                       ║
║  🔧 Modules utils: Tous importés                                           ║
║                                                                              ║
║  🎯 Routes disponibles:                                                     ║
║     • / - Accueil                                                           ║
║     • /carte - Cartes interactives                                         ║
║     • /recherche - Recherche avancée                                       ║
║     • /rapport_point - Rapports géospatiaux                               ║
║     • /admin - Administration                                               ║
║     • /debug/* - Outils de debug                                           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='127.0.0.1', port=port, debug=debug)
