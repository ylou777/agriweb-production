#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serveur AgriWeb utilisant directement les templates existants
Ce fichier utilise tous vos templates déjà créés avec les routes appropriées
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import os
import json
import requests
from datetime import datetime
import folium
from geopy.geocoders import Nominatim
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# === Configuration GeoServer ===
GEOSERVER_URL = os.environ.get('GEOSERVER_URL', "http://localhost:8080/geoserver")
GEOSERVER_USER = os.environ.get('GEOSERVER_USER', "admin")
GEOSERVER_PASSWORD = os.environ.get('GEOSERVER_PASSWORD', "geoserver")

# Configuration des couches
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
    'communes': "gpu:communes-20220101"
}

# === Gestionnaire d'utilisateurs simple ===
class SimpleUserManager:
    def __init__(self):
        self.users = {
            'admin': {'password': 'admin123', 'role': 'admin'},
            'demo': {'password': 'demo123', 'role': 'user'}
        }
    
    def authenticate(self, username, password):
        user = self.users.get(username)
        if user and user['password'] == password:
            return {'username': username, 'role': user['role']}
        return None
    
    def create_user(self, username, password, role='user'):
        if username not in self.users:
            self.users[username] = {'password': password, 'role': role}
            return True
        return False

user_manager = SimpleUserManager()

# === Décorateur d'authentification ===
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
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
                         total_users=len(user_manager.users))

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

# === ROUTES DE RAPPORTS ===
@app.route('/rapport_point')
@login_required
def rapport_point():
    """Route de rapport ponctuel utilisant le template existant"""
    # Récupération des paramètres
    lat = request.args.get('lat', 46.8)
    lon = request.args.get('lon', 2.0)
    
    # Données d'exemple pour le template
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
        'entreprises_sirene': 127
    }
    
    return render_template('rapport_point.html', **rapport_data)

@app.route('/rapport_commune')
@login_required
def rapport_commune():
    """Route de rapport communal"""
    commune = request.args.get('commune', 'Paris')
    
    # Données d'exemple
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
    
    # Données étendues pour le rapport complet
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
        # Données supplémentaires pour le rapport complet
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

# === ROUTES D'API ET DONNÉES ===
@app.route('/api/recherche_commune')
@login_required
def api_recherche_commune():
    """API de recherche de commune"""
    query = request.args.get('q', '')
    
    # Simulation de résultats de recherche
    communes = [
        {'nom': 'Paris', 'code': '75056', 'dept': '75'},
        {'nom': 'Lyon', 'code': '69123', 'dept': '69'},
        {'nom': 'Marseille', 'code': '13055', 'dept': '13'}
    ]
    
    if query:
        communes = [c for c in communes if query.lower() in c['nom'].lower()]
    
    return jsonify(communes)

@app.route('/api/geoserver_proxy')
@login_required
def geoserver_proxy():
    """Proxy vers GeoServer pour éviter les problèmes CORS"""
    try:
        # Récupération des paramètres de la requête
        params = dict(request.args)
        
        # Construction de l'URL GeoServer
        geoserver_url = f"{GEOSERVER_URL}/wfs"
        
        # Requête vers GeoServer avec authentification
        auth = (GEOSERVER_USER, GEOSERVER_PASSWORD)
        response = requests.get(geoserver_url, params=params, auth=auth, timeout=30)
        
        # Retour de la réponse
        return response.content, response.status_code, {'Content-Type': response.headers.get('Content-Type', 'application/json')}
        
    except Exception as e:
        logger.error(f"Erreur proxy GeoServer: {e}")
        return jsonify({'error': 'Erreur de connexion au serveur de données'}), 500

@app.route('/api/layers_config')
@login_required
def api_layers_config():
    """API retournant la configuration des couches"""
    return jsonify(LAYERS_CONFIG)

# === ROUTES DE DÉMONSTRATION ===
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

# === ROUTES D'ADMINISTRATION ===
@app.route('/admin')
@login_required
def admin():
    """Page d'administration (nécessite le rôle admin)"""
    user = session.get('user')
    if user['role'] != 'admin':
        flash('Accès refusé. Droits administrateur requis.', 'error')
        return redirect(url_for('index'))
    
    return f'''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Administration - AgriWeb</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h1>Administration AgriWeb</h1>
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5>Statistiques</h5>
                        </div>
                        <div class="card-body">
                            <p>Utilisateurs enregistrés: {len(user_manager.users)}</p>
                            <p>Templates disponibles: {len([f for f in os.listdir('templates') if f.endswith('.html')])}</p>
                            <p>Couches configurées: {len(LAYERS_CONFIG)}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5>Actions</h5>
                        </div>
                        <div class="card-body">
                            <a href="{url_for('index')}" class="btn btn-primary">Retour à l'accueil</a>
                            <a href="{url_for('logout')}" class="btn btn-secondary">Déconnexion</a>
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

# === POINT D'ENTRÉE ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          🌾 AgriWeb Templates Server 🌾                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  🚀 Serveur démarré avec succès !                                          ║
║                                                                              ║
║  📍 URL locale: http://127.0.0.1:{port}                                  ║
║  🔑 Comptes de test:                                                        ║
║     • admin / admin123 (administrateur)                                     ║
║     • demo / demo123 (utilisateur)                                          ║
║                                                                              ║
║  📋 Templates disponibles: {len([f for f in os.listdir('templates') if f.endswith('.html')])}                                               ║
║  🗂️ Couches configurées: {len(LAYERS_CONFIG)}                                                 ║
║                                                                              ║
║  🎯 Toutes vos pages sont maintenant accessibles !                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='127.0.0.1', port=port, debug=debug)
