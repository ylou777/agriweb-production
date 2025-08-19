#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serveur AgriWeb Simple - Sans casser les imports existants
Utilise directement vos templates sans modification
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import os
import json
from datetime import datetime
import logging
from functools import wraps

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Création de l'application Flask
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# === Gestionnaire d'utilisateurs simple ===
class SimpleUserManager:
    def __init__(self):
        self.users = {
            'admin': {'password': 'admin123', 'role': 'admin'},
            'demo': {'password': 'demo123', 'role': 'user'},
            'agriweb': {'password': 'agriweb2025', 'role': 'power_user'},
            'guest': {'password': 'guest123', 'role': 'guest'}
        }
    
    def authenticate(self, username, password):
        user = self.users.get(username)
        if user and user['password'] == password:
            return {'username': username, 'role': user['role']}
        return None

user_manager = SimpleUserManager()

# === Décorateur d'authentification ===
def login_required(f):
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
    """Page d'accueil - utilise votre template index.html existant"""
    return render_template('index.html', user=session.get('user'))

# === ROUTES CARTOGRAPHIQUES (utilisent vos templates existants) ===
@app.route('/carte')
@app.route('/map')
@login_required
def carte():
    """Route carte - utilise votre template map.html existant"""
    return render_template('map.html')

@app.route('/display_map')
@login_required
def display_map():
    """Route d'affichage de carte"""
    return render_template('display_map.html')

# === ROUTES DE RECHERCHE (utilisent vos templates existants) ===
@app.route('/recherche')
@login_required
def recherche():
    """Route de recherche - utilise votre template index.html avec recherche"""
    return render_template('index.html', page='recherche', user=session.get('user'))

@app.route('/commune_search')
@login_required
def commune_search():
    """Route de recherche de commune - redirige vers une page simple"""
    return '''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Recherche Commune - AgriWeb</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h2>Recherche de Commune</h2>
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h5>Rechercher une commune</h5>
                            <input type="text" class="form-control mb-3" placeholder="Nom de la commune">
                            <button class="btn btn-primary">Rechercher</button>
                        </div>
                    </div>
                </div>
            </div>
            <hr>
            <a href="/" class="btn btn-secondary">Retour à l'accueil</a>
        </div>
    </body>
    </html>
    '''

@app.route('/recherche_toitures')
@login_required
def recherche_toitures():
    """Route de recherche de toitures"""
    try:
        return render_template('recherche_toitures.html')
    except:
        return '''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Recherche Toitures - AgriWeb</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-4">
                <h2>Recherche de Toitures</h2>
                <div class="alert alert-info">Module de recherche de toitures en cours de chargement...</div>
                <a href="/" class="btn btn-secondary">Retour à l'accueil</a>
            </div>
        </body>
        </html>
        '''

@app.route('/search_panel')
@login_required
def search_panel():
    """Route du panneau de recherche"""
    try:
        return render_template('search_panel.html')
    except:
        return redirect(url_for('recherche'))

# === ROUTES DE RAPPORTS ===
@app.route('/rapport_point')
@login_required
def rapport_point():
    """Route de rapport ponctuel"""
    try:
        # Utilise votre template existant
        return render_template('rapport_point.html', 
                             latitude=46.8, longitude=2.0, 
                             timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        logger.error(f"Erreur template rapport_point: {e}")
        return '''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Rapport Point - AgriWeb</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-4">
                <h2>Rapport Géospatial</h2>
                <div class="alert alert-success">Rapport en cours de génération...</div>
                <a href="/" class="btn btn-secondary">Retour à l'accueil</a>
            </div>
        </body>
        </html>
        '''

@app.route('/rapport_commune')
@login_required
def rapport_commune():
    """Route de rapport communal"""
    try:
        return render_template('rapport_commune.html')
    except:
        return redirect(url_for('rapport_point'))

# === ROUTES D'API SIMPLES ===
@app.route('/api/recherche_commune')
@login_required
def api_recherche_commune():
    """API de recherche de commune - données d'exemple"""
    query = request.args.get('q', '')
    
    communes = [
        {'nom': 'Paris', 'code': '75056', 'dept': '75'},
        {'nom': 'Lyon', 'code': '69123', 'dept': '69'},
        {'nom': 'Marseille', 'code': '13055', 'dept': '13'},
        {'nom': 'Toulouse', 'code': '31555', 'dept': '31'}
    ]
    
    if query:
        communes = [c for c in communes if query.lower() in c['nom'].lower()]
    
    return jsonify(communes)

@app.route('/api/status')
def api_status():
    """API de statut - pour vérifier que le serveur fonctionne"""
    return jsonify({
        'status': 'OK',
        'timestamp': datetime.now().isoformat(),
        'templates_disponibles': len([f for f in os.listdir('templates') if f.endswith('.html')]) if os.path.exists('templates') else 0
    })

# === ROUTES DE DEBUG SIMPLES ===
@app.route('/debug')
@login_required
def debug():
    """Route de debug simple"""
    user = session.get('user')
    if user['role'] != 'admin':
        return redirect(url_for('index'))
    
    templates = []
    if os.path.exists('templates'):
        templates = [f for f in os.listdir('templates') if f.endswith('.html')]
    
    return f'''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Debug - AgriWeb</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h2>Debug AgriWeb</h2>
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Templates disponibles ({len(templates)})</div>
                        <div class="card-body">
                            <ul class="list-group">
                                {''.join([f'<li class="list-group-item">{t}</li>' for t in templates])}
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Utilisateur connecté</div>
                        <div class="card-body">
                            <p>Nom: {user['username']}</p>
                            <p>Rôle: {user['role']}</p>
                        </div>
                    </div>
                </div>
            </div>
            <hr>
            <a href="/" class="btn btn-primary">Retour à l'accueil</a>
        </div>
    </body>
    </html>
    '''

# === GESTION D'ERREURS ===
@app.errorhandler(404)
def not_found(error):
    logger.warning(f"Page non trouvée: {request.url}")
    return f'''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Page non trouvée - AgriWeb</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <div class="alert alert-warning">
                <h4>Page non trouvée (404)</h4>
                <p>La page <code>{request.url}</code> n'existe pas.</p>
            </div>
            <a href="/" class="btn btn-primary">Retour à l'accueil</a>
        </div>
    </body>
    </html>
    ''', 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Erreur interne: {error}")
    return f'''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Erreur - AgriWeb</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <div class="alert alert-danger">
                <h4>Erreur interne du serveur (500)</h4>
                <p>Une erreur s'est produite. Veuillez réessayer.</p>
            </div>
            <a href="/" class="btn btn-primary">Retour à l'accueil</a>
        </div>
    </body>
    </html>
    ''', 500

# === POINT D'ENTRÉE ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                       🌾 AgriWeb Serveur Simple 🌾                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  🚀 Serveur démarré SANS casser vos imports !                              ║
║                                                                              ║
║  📍 URL locale: http://127.0.0.1:{port}                                  ║
║  🔑 Comptes de test:                                                        ║
║     • admin / admin123 (administrateur)                                     ║
║     • demo / demo123 (utilisateur)                                          ║
║     • agriweb / agriweb2025 (utilisateur avancé)                           ║
║     • guest / guest123 (invité)                                            ║
║                                                                              ║
║  ✅ Routes disponibles:                                                     ║
║     • / - Accueil                                                           ║
║     • /carte - Cartes                                                       ║
║     • /recherche - Recherche                                               ║
║     • /rapport_point - Rapports                                            ║
║     • /debug - Debug (admin)                                               ║
║                                                                              ║
║  🎯 AUCUN import problématique !                                           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='127.0.0.1', port=port, debug=debug)
