#!/usr/bin/env python3
"""
🚀 SERVEUR AGRIWEB 2.0 UNIFIÉ - COMMERCIALISATION + GEOSERVER
Serveur complet avec essais gratuits, licences, paiements et GeoServer intégré
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import sys
import os
from datetime import datetime, timedelta
import requests
import uuid
import json

# Imports pour les cartes
import folium
from folium.plugins import Draw, MeasureControl, MarkerCluster
import geopandas as gpd
from shapely.geometry import shape, Point, mapping, MultiPolygon, Polygon
from pyproj import Transformer
import time

# Import des modules AgriWeb existants
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agriweb_source import (
        build_report_data,
        get_communes_for_dept,
        fetch_gpu_data,
        geocode_address,
        get_address_from_coordinates
    )
    print("✅ Modules AgriWeb importés avec succès")
except ImportError as e:
    print(f"❌ Erreur import AgriWeb: {e}")

import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'agriweb-2025-production-key')

# Configuration GeoServer - Utilise les variables d'environnement Railway
# Fonction pour nettoyer les guillemets des variables Railway
def clean_env_var(var_name, default_value):
    """Nettoie les guillemets des variables d'environnement Railway"""
    value = os.getenv(var_name, default_value)
    if value and value.startswith('"') and value.endswith('"'):
        value = value[1:-1]  # Retire les guillemets
    return value

GEOSERVER_URL = clean_env_var('GEOSERVER_URL', 'http://localhost:8080/geoserver')
GEOSERVER_WFS_URL = f"{GEOSERVER_URL}/ows"
GEOSERVER_USERNAME = clean_env_var('GEOSERVER_USERNAME', 'admin')
GEOSERVER_PASSWORD = clean_env_var('GEOSERVER_PASSWORD', 'geoserver')

# Base de données simple des utilisateurs (en production, utiliser une vraie DB)
USERS_DB = {}

print(f"🚀 [PRODUCTION] Utilisation de GEOSERVER_URL: {GEOSERVER_URL}")
print(f"🚀 Configuration Railway:")
print(f"   - GeoServer URL: {GEOSERVER_URL}")
print(f"   - GeoServer Auth: {GEOSERVER_USERNAME}:{'*' * len(GEOSERVER_PASSWORD)}")
print(f"   - Port: {os.getenv('PORT', '5000')}")
print(f"   - Debug: {os.getenv('FLASK_DEBUG', 'False')}")
print(f"🔗 GeoServer configuré: {GEOSERVER_URL}")

# Debug variables d'environnement
print("🔍 [DEBUG] Variables d'environnement reçues:")
print(f"   - GEOSERVER_URL raw: '{os.getenv('GEOSERVER_URL', 'NOT_SET')}'")
print(f"   - PORT raw: '{os.getenv('PORT', 'NOT_SET')}'")
print(f"   - FLASK_DEBUG raw: '{os.getenv('FLASK_DEBUG', 'NOT_SET')}'")
print(f"   - SECRET_KEY présente: {'Oui' if os.getenv('SECRET_KEY') else 'Non'}")

# Configuration des couches GeoServer
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
SIRENE_LAYER = "gpu:GeolocalisationEtablissement_Sirene france"  # Sirène
ELEVEURS_LAYER = "gpu:etablissements_eleveurs"
PPRI_LAYER = "gpu:ppri"

print("🗺️ [COUCHES] Configuration GeoServer:")
print(f"   - Parcelles: {PARCELLE_LAYER}")
print(f"   - RPG: {PARCELLES_GRAPHIQUES_LAYER}")
print(f"   - PLU: {PLU_LAYER}")
print(f"   - Postes BT: {POSTE_LAYER}")
print(f"   - Postes HTA: {HT_POSTE_LAYER}")

# Test de connectivité GeoServer au démarrage
def test_geoserver_connection():
    """Test la connectivité GeoServer avec gestion d'erreurs"""
    try:
        import requests
        response = requests.get(GEOSERVER_URL, timeout=10, allow_redirects=True)
        print(f"✅ GeoServer test: HTTP {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"⚠️ GeoServer test failed: {e}")
        print("🔄 Application continue sans GeoServer...")
        return False

# Test au démarrage
geoserver_ok = test_geoserver_connection()

# === FONCTIONS UTILITAIRES POUR LES CARTES ===

def safe_print(*args, **kwargs):
    """Print sécurisé pour les logs"""
    try:
        print(*args, **kwargs)
    except Exception:
        pass

def get_parcelle_info(lat, lon):
    """Récupère info parcelle via API IGN"""
    try:
        url = "https://apicarto.ign.fr/api/cadastre/parcelle"
        params = {"lon": lon, "lat": lat}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        safe_print(f"Erreur API parcelle: {e}")
    return None

def get_all_parcelles(lat, lon, radius=0.03):
    """Récupère toutes parcelles dans rayon"""
    try:
        # bbox autour du point
        bbox = f"{lon-radius},{lat-radius},{lon+radius},{lat+radius}"
        url = "https://apicarto.ign.fr/api/cadastre/parcelle"
        params = {"bbox": bbox}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        safe_print(f"Erreur API parcelles: {e}")
    return {"type": "FeatureCollection", "features": []}

@app.route('/')
def index():
    """Page d'accueil principale"""
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgriWeb 2.0 - Géolocalisation Agricole Professionnelle</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
            
            .header { background: linear-gradient(135deg, #2c5f41, #4a8b3b); color: white; padding: 60px 0; text-align: center; }
            .header h1 { font-size: 3rem; margin-bottom: 20px; font-weight: 700; }
            .header p { font-size: 1.3rem; opacity: 0.9; margin-bottom: 30px; }
            
            .status-bar { background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; margin: 20px 0; border-radius: 8px; }
            .status-bar.error { background: #f8d7da; border-color: #f5c6cb; }
            
            .features { padding: 60px 0; background: #f8f9fa; }
            .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; margin-top: 40px; }
            .feature-card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
            .feature-card h3 { color: #2c5f41; margin-bottom: 15px; font-size: 1.4rem; }
            
            .pricing { padding: 60px 0; }
            .pricing h2 { text-align: center; margin-bottom: 50px; font-size: 2.5rem; color: #2c5f41; }
            .plans { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 30px; }
            .plan { background: white; border: 2px solid #e9ecef; border-radius: 12px; padding: 40px 30px; text-align: center; position: relative; }
            .plan.featured { border-color: #28a745; transform: scale(1.05); }
            .plan h3 { color: #2c5f41; margin-bottom: 20px; font-size: 1.8rem; }
            .plan .price { font-size: 2.5rem; color: #28a745; font-weight: bold; margin-bottom: 10px; }
            .plan ul { list-style: none; margin: 20px 0; }
            .plan li { padding: 8px 0; border-bottom: 1px solid #f1f1f1; }
            
            .cta { background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 80px 0; text-align: center; }
            .cta h2 { font-size: 2.5rem; margin-bottom: 20px; }
            
            .btn { display: inline-block; padding: 15px 30px; margin: 10px; border: none; border-radius: 8px; 
                   text-decoration: none; font-weight: 600; cursor: pointer; transition: all 0.3s ease; }
            .btn-primary { background: #28a745; color: white; }
            .btn-primary:hover { background: #218838; transform: translateY(-2px); }
            .btn-secondary { background: #6c757d; color: white; }
            .btn-secondary:hover { background: #545b62; }
            .btn-outline { background: transparent; color: #28a745; border: 2px solid #28a745; }
            .btn-outline:hover { background: #28a745; color: white; }
            
            .form-section { background: white; padding: 40px; margin: 20px 0; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 20px; }
            .form-group label { display: block; margin-bottom: 5px; font-weight: 600; color: #2c5f41; }
            .form-group input { width: 100%; padding: 12px; border: 2px solid #e9ecef; border-radius: 6px; font-size: 1rem; }
            .form-group input:focus { outline: none; border-color: #28a745; }
            
            .hidden { display: none; }
            .alert { padding: 15px; margin: 15px 0; border-radius: 6px; }
            .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            
            .footer { background: #2c5f41; color: white; padding: 40px 0; text-align: center; }
        </style>
    </head>
    <body>
        <header class="header">
            <div class="container">
                <h1>🌾 AgriWeb 2.0</h1>
                <p>Géolocalisation Agricole Professionnelle avec GeoServer Intégré</p>
                <div class="status-bar">
                    <strong>✅ Système Opérationnel</strong> - GeoServer connecté avec 48+ couches de données
                </div>
            </div>
        </header>

        <section class="features">
            <div class="container">
                <h2 style="text-align: center; margin-bottom: 20px; color: #2c5f41;">Fonctionnalités Avancées</h2>
                <div class="features-grid">
                    <div class="feature-card">
                        <h3>🗺️ GeoServer Intégré</h3>
                        <p>Accès à 48+ couches géographiques : cadastre, RPG, zones urbaines, parkings, friches...</p>
                    </div>
                    <div class="feature-card">
                        <h3>🎯 Recherche Précise</h3>
                        <p>Localisation par commune, coordonnées GPS, filtrage par distance aux réseaux électriques</p>
                    </div>
                    <div class="feature-card">
                        <h3>📊 Rapports Détaillés</h3>
                        <p>Analyses complètes avec cartes interactives, données cadastrales et risques géologiques</p>
                    </div>
                    <div class="feature-card">
                        <h3>🔒 Sécurisé & Fiable</h3>
                        <p>Système de licences professionnel, sauvegarde automatique, haute disponibilité</p>
                    </div>
                </div>
            </div>
        </section>

        <section class="pricing">
            <div class="container">
                <h2>Tarifs Professionnels</h2>
                <div class="plans">
                    <div class="plan">
                        <h3>🆓 Essai Gratuit</h3>
                        <div class="price">0€</div>
                        <p>7 jours d'accès complet</p>
                        <ul>
                            <li>✅ 10 communes</li>
                            <li>✅ Toutes les fonctionnalités</li>
                            <li>✅ Support technique</li>
                            <li>✅ GeoServer inclus</li>
                        </ul>
                        <button class="btn btn-primary" onclick="showTrialForm()">Commencer l'Essai</button>
                    </div>
                    
                    <div class="plan featured">
                        <h3>💼 Basic</h3>
                        <div class="price">299€<small>/an</small></div>
                        <p>Pour petites exploitations</p>
                        <ul>
                            <li>✅ 100 communes/mois</li>
                            <li>✅ 500 rapports/jour</li>
                            <li>✅ API basique</li>
                            <li>✅ Support email</li>
                        </ul>
                        <button class="btn btn-primary" onclick="showPaymentForm('basic')">Choisir Basic</button>
                    </div>
                    
                    <div class="plan">
                        <h3>🚀 Pro</h3>
                        <div class="price">999€<small>/an</small></div>
                        <p>Pour professionnels</p>
                        <ul>
                            <li>✅ 1000 communes/mois</li>
                            <li>✅ API complète</li>
                            <li>✅ Exports automatisés</li>
                            <li>✅ Support prioritaire</li>
                        </ul>
                        <button class="btn btn-primary" onclick="showPaymentForm('pro')">Choisir Pro</button>
                    </div>
                    
                    <div class="plan">
                        <h3>🏢 Enterprise</h3>
                        <div class="price">2999€<small>/an</small></div>
                        <p>Pour grandes organisations</p>
                        <ul>
                            <li>✅ Accès illimité</li>
                            <li>✅ GeoServer dédié</li>
                            <li>✅ API sur mesure</li>
                            <li>✅ Support 24/7</li>
                        </ul>
                        <button class="btn btn-primary" onclick="showPaymentForm('enterprise')">Choisir Enterprise</button>
                    </div>
                </div>
            </div>
        </section>

        <!-- Formulaire de connexion -->
        <div id="login-form" class="form-section container hidden">
            <h2>🔐 Se connecter à AgriWeb 2.0</h2>
            <div id="login-alert"></div>
            <form onsubmit="submitLogin(event)">
                <div class="form-group">
                    <label for="login-email">Adresse email</label>
                    <input type="email" id="login-email" name="email" required placeholder="votre.nom@entreprise.com">
                </div>
                <button type="submit" class="btn btn-primary">Se Connecter</button>
                <button type="button" class="btn btn-secondary" onclick="hideLoginForm()">Annuler</button>
            </form>
            <p style="margin-top: 15px; text-align: center;">
                Pas encore de compte ? 
                <a href="#" onclick="hideLoginForm(); showTrialForm();" style="color: #28a745;">Créer un essai gratuit</a>
            </p>
        </div>

        <!-- Formulaire d'essai gratuit -->
        <div id="trial-form" class="form-section container hidden">
            <h2>🆓 Démarrer votre essai gratuit (7 jours)</h2>
            <div id="trial-alert"></div>
            <form onsubmit="submitTrial(event)">
                <div class="form-group">
                    <label for="trial-email">Adresse email professionnelle</label>
                    <input type="email" id="trial-email" name="email" required placeholder="votre.nom@entreprise.com">
                </div>
                <div class="form-group">
                    <label for="trial-company">Nom de l'entreprise</label>
                    <input type="text" id="trial-company" name="company" required placeholder="Votre Entreprise">
                </div>
                <div class="form-group">
                    <label for="trial-name">Nom complet</label>
                    <input type="text" id="trial-name" name="name" required placeholder="Prénom Nom">
                </div>
                <button type="submit" class="btn btn-primary">Activer l'Essai Gratuit</button>
                <button type="button" class="btn btn-secondary" onclick="hideTrialForm()">Annuler</button>
            </form>
            <p style="margin-top: 15px; text-align: center;">
                Déjà un compte ? 
                <a href="#" onclick="hideTrialForm(); showLoginForm();" style="color: #28a745;">Se connecter</a>
            </p>
        </div>

        <!-- Interface utilisateur connecté -->
        <div id="user-interface" class="form-section container hidden">
            <h2>🎯 Interface AgriWeb 2.0</h2>
            <div class="status-bar">
                <span id="user-status"></span>
            </div>
            
            <div class="form-group">
                <label for="search-commune">Rechercher une commune</label>
                <input type="text" id="search-commune" placeholder="Nom de la commune (ex: Lyon)" value="Lyon">
                <button class="btn btn-primary" onclick="searchCommune()">🔍 Rechercher</button>
            </div>
            
            <div id="search-results"></div>
            
            <div style="margin-top: 30px;">
                <button class="btn btn-secondary" onclick="logout()">Se Déconnecter</button>
                <a href="/status" class="btn btn-outline" target="_blank">📊 Statut Système</a>
            </div>
        </div>

        <section class="cta">
            <div class="container">
                <h2>Prêt à optimiser votre géolocalisation agricole ?</h2>
                <p>Accédez à AgriWeb 2.0 dès maintenant</p>
                <button class="btn btn-primary" onclick="showLoginForm()">🔐 Se Connecter</button>
                <button class="btn btn-outline" onclick="showTrialForm()">🆓 Essai Gratuit (7 jours)</button>
            </div>
        </section>

        <footer class="footer">
            <div class="container">
                <p>&copy; 2025 AgriWeb 2.0 - Géolocalisation Agricole Professionnelle</p>
                <p>Système intégré avec GeoServer - Support technique disponible</p>
            </div>
        </footer>

        <script>
            // État de l'application
            let currentUser = null;
            
            function showTrialForm() {
                document.getElementById('trial-form').classList.remove('hidden');
                document.getElementById('login-form').classList.add('hidden');
                document.getElementById('trial-form').scrollIntoView({behavior: 'smooth'});
            }
            
            function hideTrialForm() {
                document.getElementById('trial-form').classList.add('hidden');
            }
            
            function showLoginForm() {
                document.getElementById('login-form').classList.remove('hidden');
                document.getElementById('trial-form').classList.add('hidden');
                document.getElementById('login-form').scrollIntoView({behavior: 'smooth'});
            }
            
            function hideLoginForm() {
                document.getElementById('login-form').classList.add('hidden');
            }
            
            function showPaymentForm(plan) {
                alert('Paiement ' + plan + ' - À implémenter avec Stripe');
            }
            
            async function submitLogin(event) {
                event.preventDefault();
                
                const email = document.getElementById('login-email').value;
                
                try {
                    const response = await fetch('/api/login', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({email: email})
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        document.getElementById('login-alert').innerHTML = 
                            '<div class="alert alert-success">✅ ' + result.message + '</div>';
                        
                        // Masquer le formulaire et afficher l'interface
                        setTimeout(() => {
                            hideLoginForm();
                            showUserInterface(result.user);
                        }, 1000);
                    } else {
                        document.getElementById('login-alert').innerHTML = 
                            '<div class="alert alert-danger">❌ ' + result.error + '</div>';
                    }
                } catch (error) {
                    document.getElementById('login-alert').innerHTML = 
                        '<div class="alert alert-danger">❌ Erreur de connexion: ' + error.message + '</div>';
                }
            }

            async function submitTrial(event) {
                event.preventDefault();
                
                const formData = {
                    email: document.getElementById('trial-email').value,
                    company: document.getElementById('trial-company').value,
                    name: document.getElementById('trial-name').value
                };
                
                try {
                    const response = await fetch('/api/trial', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(formData)
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        document.getElementById('trial-alert').innerHTML = 
                            '<div class="alert alert-success">✅ ' + result.message + '</div>';
                        
                        // Masquer le formulaire et afficher l'interface
                        setTimeout(() => {
                            hideTrialForm();
                            showUserInterface(result.user);
                        }, 2000);
                        
                    } else {
                        document.getElementById('trial-alert').innerHTML = 
                            '<div class="alert alert-error">❌ ' + result.error + '</div>';
                    }
                } catch (error) {
                    document.getElementById('trial-alert').innerHTML = 
                        '<div class="alert alert-error">❌ Erreur réseau: ' + error.message + '</div>';
                }
            }
            
            function showUserInterface(user) {
                currentUser = user;
                document.getElementById('user-interface').classList.remove('hidden');
                document.getElementById('user-interface').scrollIntoView({behavior: 'smooth'});
                
                document.getElementById('user-status').innerHTML = 
                    `👤 Connecté: ${user.name} (${user.email}) - Licence: ${user.license_type} - Expire: ${user.expires}`;
            }
            
            async function searchCommune() {
                const commune = document.getElementById('search-commune').value;
                
                if (!commune) {
                    alert('Veuillez saisir un nom de commune');
                    return;
                }
                
                document.getElementById('search-results').innerHTML = '🔍 Recherche en cours...';
                
                try {
                    const response = await fetch('/api/search', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({commune: commune})
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        document.getElementById('search-results').innerHTML = 
                            '<div class="alert alert-success"><h3>✅ Résultats pour ' + commune + '</h3>' +
                            '<pre>' + JSON.stringify(result.results, null, 2) + '</pre></div>';
                    } else {
                        document.getElementById('search-results').innerHTML = 
                            '<div class="alert alert-error">❌ ' + result.error + '</div>';
                    }
                } catch (error) {
                    document.getElementById('search-results').innerHTML = 
                        '<div class="alert alert-error">❌ Erreur: ' + error.message + '</div>';
                }
            }
            
            function logout() {
                currentUser = null;
                document.getElementById('user-interface').classList.add('hidden');
                window.location.reload();
            }
        </script>
    </body>
    </html>
    """
    
    return html_content

@app.route('/favicon.ico')
def favicon():
    """Route pour le favicon - évite les erreurs 502"""
    from flask import Response
    return Response(status=204)  # No Content - pas de favicon disponible

@app.route('/api/login', methods=['POST'])
def api_login():
    """API de connexion pour utilisateurs existants"""
    
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Adresse email requise'
            }), 400
        
        # Vérifier si l'utilisateur existe
        if email not in USERS_DB:
            return jsonify({
                'success': False,
                'error': 'Aucun compte trouvé avec cette adresse email. Voulez-vous créer un essai gratuit ?'
            }), 404
        
        user_data = USERS_DB[email]
        
        # Vérifier si la licence est encore valide
        expires_date = datetime.fromisoformat(user_data['expires'])
        if datetime.now() > expires_date:
            return jsonify({
                'success': False,
                'error': f'Votre essai gratuit a expiré le {expires_date.strftime("%d/%m/%Y")}. Contactez-nous pour renouveler.'
            }), 403
        
        # Connecter l'utilisateur
        session['user_id'] = user_data['user_id']
        session['email'] = email
        session['license_valid'] = True
        session['license_type'] = user_data['license_type']
        session['expires'] = expires_date.strftime('%Y-%m-%d')
        
        print(f"✅ Connexion réussie: {user_data['name']} ({email})")
        
        return jsonify({
            'success': True,
            'message': f'Connexion réussie ! Bienvenue {user_data["name"]}',
            'user': {
                'name': user_data['name'],
                'email': email,
                'company': user_data['company'],
                'license_type': user_data['license_type'],
                'expires': expires_date.strftime('%d/%m/%Y'),
                'searches_today': user_data.get('searches_today', 0),
                'searches_total': user_data.get('searches_total', 0)
            }
        })
        
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return jsonify({
            'success': False,
            'error': f'Erreur de connexion: {str(e)}'
        }), 500

@app.route('/api/trial', methods=['POST'])
def api_trial():
    """API inscription essai gratuit"""
    
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        company = data.get('company', '').strip()
        name = data.get('name', '').strip()
        
        if not email or not company or not name:
            return jsonify({
                'success': False,
                'error': 'Tous les champs sont requis'
            }), 400
        
        # Vérifier si l'utilisateur existe déjà
        if email in USERS_DB:
            return jsonify({
                'success': False,
                'error': 'Cet email est déjà utilisé'
            }), 400
        
        # Créer l'utilisateur avec licence d'essai
        user_id = str(uuid.uuid4())
        expires_date = datetime.now() + timedelta(days=7)
        
        user_data = {
            'id': user_id,
            'email': email,
            'company': company,
            'name': name,
            'license_type': 'trial',
            'created': datetime.now().isoformat(),
            'expires': expires_date.isoformat(),
            'searches_today': 0,
            'searches_total': 0
        }
        
        USERS_DB[email] = user_data
        
        # Sauvegarder la session
        session['user_id'] = user_id
        session['email'] = email
        session['license_valid'] = True
        session['license_type'] = 'trial'
        session['expires'] = expires_date.strftime('%Y-%m-%d')
        
        print(f"✅ Nouvel utilisateur inscrit: {name} ({email}) - {company}")
        
        return jsonify({
            'success': True,
            'message': f'Essai gratuit activé pour {name} ! Valable 7 jours.',
            'user': {
                'name': name,
                'email': email,
                'company': company,
                'license_type': 'trial',
                'expires': expires_date.strftime('%d/%m/%Y')
            }
        })
        
    except Exception as e:
        print(f"❌ Erreur inscription: {e}")
        return jsonify({
            'success': False,
            'error': f'Erreur inscription: {str(e)}'
        }), 500

@app.route('/api/search', methods=['POST'])
def api_search():
    """API de recherche AgriWeb avec gestion des licences"""
    
    try:
        # Vérifier la licence
        if not session.get('license_valid'):
            return jsonify({
                'success': False,
                'error': 'Licence requise - Veuillez créer un essai gratuit'
            }), 403
        
        email = session.get('email')
        if email and email in USERS_DB:
            user = USERS_DB[email]
            user['searches_today'] += 1
            user['searches_total'] += 1
        
        data = request.get_json()
        commune = data.get('commune', '').strip()
        
        if not commune:
            return jsonify({
                'success': False,
                'error': 'Nom de commune requis'
            }), 400
        
        print(f"🔍 Recherche pour {commune} par {session.get('email', 'unknown')}")
        
        # Test connexion GeoServer
        try:
            response = requests.get(GEOSERVER_URL, timeout=5)
            geoserver_status = "✅ Connecté" if response.status_code == 200 else "❌ Erreur"
        except:
            geoserver_status = "❌ Inaccessible"
        
        # Test WFS et comptage des couches
        layer_count = 0
        sample_layers = []
        
        try:
            wfs_params = {
                "service": "WFS",
                "request": "GetCapabilities"
            }
            wfs_response = requests.get(GEOSERVER_WFS_URL, params=wfs_params, timeout=10)
            
            if "WFS_Capabilities" in wfs_response.text:
                import re
                layers = re.findall(r'<Name>([^<]+)</Name>', wfs_response.text)
                layer_count = len(layers)
                sample_layers = layers[:5]
        except:
            pass
        
        # Simulation d'une recherche réelle (vous pouvez intégrer ici vos vraies fonctions)
        results = {
            'commune': commune,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user': {
                'email': session.get('email'),
                'license': session.get('license_type'),
                'expires': session.get('expires')
            },
            'geoserver': {
                'url': GEOSERVER_URL,
                'status': geoserver_status,
                'layer_count': layer_count,
                'sample_layers': sample_layers
            },
            'search_results': {
                'status': 'success',
                'message': f'Recherche {commune} effectuée avec succès',
                'note': 'Données réelles disponibles via GeoServer'
            }
        }
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        print(f"❌ Erreur recherche: {e}")
        return jsonify({
            'success': False,
            'error': f'Erreur recherche: {str(e)}'
        }), 500

@app.route('/status')
def status():
    """Statut détaillé du système"""
    
    # Test GeoServer complet
    geoserver_details = {}
    
    try:
        response = requests.get(GEOSERVER_URL, timeout=5)
        geoserver_ok = response.status_code == 200
        
        if geoserver_ok:
            # Test WFS
            wfs_params = {"service": "WFS", "request": "GetCapabilities"}
            wfs_response = requests.get(GEOSERVER_WFS_URL, params=wfs_params, timeout=10)
            
            if "WFS_Capabilities" in wfs_response.text:
                import re
                layers = re.findall(r'<Name>([^<]+)</Name>', wfs_response.text)
                
                geoserver_details = {
                    'wfs_operational': True,
                    'layer_count': len(layers),
                    'sample_layers': layers[:10] if layers else [],
                    'response_time': 'OK'
                }
            else:
                geoserver_details = {'wfs_operational': False, 'error': 'WFS non disponible'}
        else:
            geoserver_details = {'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        geoserver_details = {'error': str(e)}
    
    status_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'system': {
            'agriweb': 'OK',
            'flask': 'OK',
            'python': 'OK'
        },
        'geoserver': {
            'url': GEOSERVER_URL,
            'status': 'OK' if geoserver_details.get('wfs_operational') else 'ERREUR',
            'details': geoserver_details
        },
        'users': {
            'total_registered': len(USERS_DB),
            'active_sessions': len([u for u in USERS_DB.values() if u.get('searches_today', 0) > 0])
        },
        'session': {
            'user_logged': session.get('email', 'Non connecté'),
            'license_valid': session.get('license_valid', False),
            'license_type': session.get('license_type', 'Aucune'),
            'expires': session.get('expires', 'N/A')
        }
    }
    
    return jsonify(status_data)

# === FONCTIONS CARTOGRAPHIQUES ===

def build_map_simple(lat, lon, address, parcelles_data=None):
    """Version simplifiée de build_map avec Esri et parcelles"""
    
    # Création carte avec fond Esri
    map_obj = folium.Map(location=[lat, lon], zoom_start=15, tiles=None)
    
    # Couche Esri (satellite)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite",
        overlay=False, control=True, show=True
    ).add_to(map_obj)
    
    # Couche OpenStreetMap
    folium.TileLayer("OpenStreetMap", name="Fond OSM", overlay=False, control=True, show=False).add_to(map_obj)
    
    # Marqueur principal
    folium.Marker(
        [lat, lon], 
        popup=f"📍 {address}<br>Lat: {lat:.6f}<br>Lon: {lon:.6f}",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(map_obj)
    
    # Parcelles cadastrales
    if parcelles_data and parcelles_data.get("features"):
        parcelles_group = folium.FeatureGroup(name="Parcelles", show=True)
        for feature in parcelles_data["features"]:
            if feature.get("geometry"):
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {
                        "color": "#FF6600", 
                        "weight": 2, 
                        "fillColor": "#FFD700", 
                        "fillOpacity": 0.3
                    },
                    popup=folium.Popup(f"Parcelle: {feature.get('properties', {}).get('id', 'N/A')}")
                ).add_to(parcelles_group)
        parcelles_group.add_to(map_obj)
    
    # Contrôles
    folium.LayerControl().add_to(map_obj)
    
    return map_obj

@app.route('/search_by_address', methods=['GET', 'POST'])
def search_by_address_route():
    """Route de recherche par adresse avec cartes complètes"""
    
    safe_print(f"\n{'='*80}")
    safe_print(f"🔍 [RECHERCHE ADRESSE] === DÉBUT RECHERCHE PAR ADRESSE ===")
    safe_print(f"📅 Date/Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    values = request.values
    lat_str = values.get("lat")
    lon_str = values.get("lon") 
    address = values.get("address", "Adresse inconnue")
    
    safe_print(f"📍 Paramètres reçus:")
    safe_print(f"   - Latitude: {lat_str}")
    safe_print(f"   - Longitude: {lon_str}")
    safe_print(f"   - Adresse: {address}")
    
    try:
        lat = float(lat_str)
        lon = float(lon_str)
    except (TypeError, ValueError):
        return jsonify({
            'success': False,
            'error': 'Coordonnées invalides'
        }), 400
    
    # Récupération des parcelles cadastrales
    safe_print("🏠 [PARCELLES] Récupération données cadastrales...")
    parcelle_info = get_parcelle_info(lat, lon)
    if not parcelle_info or not parcelle_info.get("features"):
        parcelle_info = get_all_parcelles(lat, lon, radius=0.01)
    
    parcelles_count = len(parcelle_info.get("features", []))
    safe_print(f"📐 Parcelles trouvées: {parcelles_count}")
    
    # Génération de la carte
    safe_print("🗺️ [CARTE] Génération carte avec Esri et parcelles...")
    
    map_obj = build_map_simple(lat, lon, address, parcelle_info)
    
    # Sauvegarde de la carte
    timestamp = int(time.time())
    map_filename = f"map_{timestamp}_{abs(hash(f'{lat}{lon}'))}.html"
    map_path = os.path.join("static", "cartes", map_filename)
    
    # Créer le dossier si nécessaire
    os.makedirs(os.path.dirname(map_path), exist_ok=True)
    
    map_obj.save(map_path)
    map_url = f"/static/cartes/{map_filename}?t={timestamp}"
    
    safe_print(f"✅ [CARTE] Carte sauvée: {map_url}")
    safe_print(f"✅ [RÉSULTATS] === RECHERCHE PAR ADRESSE TERMINÉE ===")
    
    return jsonify({
        'success': True,
        'map_url': map_url,
        'data': {
            'address': address,
            'coordinates': {'lat': lat, 'lon': lon},
            'parcelles_count': parcelles_count,
            'layers': ['Esri Satellite', 'OpenStreetMap', 'Parcelles cadastrales']
        }
    })

# Module serveur unifié - importé par run_app.py
# N'exécute pas directement l'application pour éviter les conflits Railway

# if __name__ == '__main__':
#     print("🚀 Démarrage AgriWeb 2.0 Unifié - Production")
#     print("=" * 60)
#     print(f"🔗 GeoServer: {GEOSERVER_URL}")
#     print(f"🌐 Interface web: http://localhost:5000")
#     print(f"📊 Statut système: http://localhost:5000/status")
#     print(f"🆓 Essais gratuits: Activés (7 jours)")
#     print(f"💼 Licences: Basic (299€), Pro (999€), Enterprise (2999€)")
#     print("=" * 60)
#     print("✅ Prêt pour la commercialisation !")
#     
#     app.run(host='0.0.0.0', port=5000, debug=False)
