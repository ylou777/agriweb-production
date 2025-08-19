#!/usr/bin/env python3
"""
🚀 AGRIWEB 2.0 - VERSION PRODUCTION AVEC PAIEMENTS
Optimisé pour hébergement gratuit (Railway, Render, Heroku)
"""

from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for, flash
import json
import os
import uuid
from datetime import datetime, timedelta
import hashlib
import secrets
# import stripe  # Commented out for Railway deployment

# Import du module de correction ngrok
try:
    from fix_ngrok_warning import add_ngrok_bypass_headers, create_ngrok_session
    NGROK_FIX_AVAILABLE = True
    print("✅ Correction ngrok chargée")
except ImportError:
    NGROK_FIX_AVAILABLE = False
    print("⚠️ Correction ngrok non disponible")

# Fonction utilitaire pour détecter la plateforme
def get_platform_name():
    """Détecte la plateforme d'hébergement"""
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        return 'Railway'
    elif os.environ.get('RENDER'):
        return 'Render'
    elif os.environ.get('DYNO'):
        return 'Heroku'
    elif os.environ.get('VERCEL'):
        return 'Vercel'
    else:
        return 'Hébergement local'

# Configuration pour hébergement
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY') or 'sk_test_YOUR_KEY'
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY') or 'pk_test_YOUR_KEY'
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET') or 'whsec_YOUR_SECRET'
    DATABASE_URL = os.environ.get('DATABASE_URL')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Configuration GeoServer flexible ✅
    GEOSERVER_LOCAL = "http://localhost:8080/geoserver"
    GEOSERVER_RAILWAY = "https://geoserver-agriweb-production.up.railway.app/geoserver"
    GEOSERVER_TUNNEL = os.environ.get('GEOSERVER_TUNNEL_URL')  # URL ngrok ou autre tunnel
    GEOSERVER_PRODUCTION = os.environ.get('GEOSERVER_URL', GEOSERVER_RAILWAY)
    
    # Authentification GeoServer ✅
    GEOSERVER_USERNAME = os.environ.get('GEOSERVER_USERNAME', 'admin')
    GEOSERVER_PASSWORD = os.environ.get('GEOSERVER_PASSWORD', 'geoserver')
    
    @staticmethod
    def get_geoserver_url():
        # Priorité: TUNNEL > PRODUCTION > LOCAL
        if Config.GEOSERVER_TUNNEL:
            print(f"🌐 Utilisation GeoServer via tunnel: {Config.GEOSERVER_TUNNEL}")
            return Config.GEOSERVER_TUNNEL
        
        environment = os.environ.get('ENVIRONMENT', 'development')
        platform = get_platform_name()
        
        if environment == 'production' or platform != 'Hébergement local':
            print(f"☁️ Utilisation GeoServer Railway: {Config.GEOSERVER_PRODUCTION}")
            return Config.GEOSERVER_PRODUCTION
        else:
            print(f"🏠 Utilisation GeoServer local: {Config.GEOSERVER_LOCAL}")
            return Config.GEOSERVER_LOCAL

    @staticmethod
    def get_geoserver_auth():
        """Retourne l'authentification GeoServer (username, password)"""
        return (Config.GEOSERVER_USERNAME, Config.GEOSERVER_PASSWORD)

    @staticmethod
    def make_geoserver_request(url, method='GET', **kwargs):
        """Fait une requête GeoServer avec authentification automatique"""
        import requests
        from requests.auth import HTTPBasicAuth
        
        auth = HTTPBasicAuth(Config.GEOSERVER_USERNAME, Config.GEOSERVER_PASSWORD)
        
        if method.upper() == 'GET':
            return requests.get(url, auth=auth, **kwargs)
        elif method.upper() == 'POST':
            return requests.post(url, auth=auth, **kwargs)
        elif method.upper() == 'PUT':
            return requests.put(url, auth=auth, **kwargs)
        elif method.upper() == 'DELETE':
            return requests.delete(url, auth=auth, **kwargs)
        else:
            raise ValueError(f"Méthode HTTP non supportée: {method}")

# Configuration GeoServer
GEOSERVER_URL = Config.get_geoserver_url()

# Configuration
app = Flask(__name__)
app.config.from_object(Config)

# Application de la correction ngrok si disponible
if NGROK_FIX_AVAILABLE and Config.GEOSERVER_TUNNEL:
    app = add_ngrok_bypass_headers(app)
    print("🛡️ Headers de contournement ngrok activés")

# Import conditionnel des modules existants
try:
    # from stripe_integration import stripe_payment_manager  # Disabled for Railway
    # stripe_payment_manager.stripe_secret_key = Config.STRIPE_SECRET_KEY
    # stripe_payment_manager.stripe_publishable_key = Config.STRIPE_PUBLISHABLE_KEY
    # stripe_payment_manager.webhook_secret = Config.STRIPE_WEBHOOK_SECRET
    # stripe.api_key = Config.STRIPE_SECRET_KEY
    STRIPE_AVAILABLE = False  # Disabled for Railway deployment
    print("⚠️ Stripe désactivé pour déploiement Railway")
except ImportError:
    STRIPE_AVAILABLE = False
    print("⚠️ Stripe non disponible")

try:
    from production_commercial import UserManager
    USER_MANAGER_AVAILABLE = True
    print("✅ UserManager chargé")
except ImportError:
    # Gestionnaire d'utilisateurs simplifié pour hébergement gratuit
    class SimpleUserManager:
        def __init__(self):
            self.users = {}
            print("🔧 SimpleUserManager initialisé pour hébergement gratuit")
        
        def create_user(self, email, password, name=""):
            """Créer un nouvel utilisateur"""
            if email in self.users:
                raise ValueError(f"L'utilisateur {email} existe déjà")
            
            user_id = str(uuid.uuid4())
            self.users[email] = {
                'id': user_id,
                'email': email,
                'password': hashlib.sha256(password.encode()).hexdigest(),
                'name': name,
                'created_at': datetime.now().isoformat(),
                'active': True,
                'license_type': 'trial',
                'searches_used': 0,
                'searches_limit': 50
            }
            print(f"👤 Utilisateur créé: {email} (ID: {user_id})")
            return user_id
        
        def authenticate_user(self, email, password):
            """Authentifier un utilisateur"""
            user = self.users.get(email)
            if user and user['password'] == hashlib.sha256(password.encode()).hexdigest():
                print(f"✅ Authentification réussie: {email}")
                return user
            print(f"❌ Authentification échouée: {email}")
            return None
        
        def get_user(self, email):
            """Récupérer un utilisateur par email (compatibilité)"""
            return self.users.get(email)
        
        def add_user(self, email, password, name=""):
            """Alias pour create_user (compatibilité)"""
            return self.create_user(email, password, name)
    
    USER_MANAGER_AVAILABLE = False
    print("⚠️ UserManager simplifié activé")

# Instance du gestionnaire d'utilisateurs
if USER_MANAGER_AVAILABLE:
    user_manager = UserManager()
else:
    user_manager = SimpleUserManager()

# Templates simplifiés
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌾 AgriWeb 2.0 - Connexion</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
        }
        .container { 
            background: white; 
            padding: 3rem; 
            border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 400px; 
            width: 100%; 
        }
        .logo { text-align: center; margin-bottom: 2rem; }
        .form-group { margin: 1rem 0; }
        label { display: block; margin-bottom: 0.5rem; font-weight: 600; }
        input { 
            width: 100%; 
            padding: 0.8rem; 
            border: 2px solid #e0e0e0; 
            border-radius: 8px; 
            font-size: 1rem; 
        }
        button { 
            width: 100%; 
            background: linear-gradient(45deg, #667eea, #764ba2); 
            color: white; 
            border: none; 
            padding: 1rem; 
            border-radius: 8px; 
            font-size: 1.1rem; 
            cursor: pointer; 
            margin-top: 1rem;
        }
        button:hover { transform: translateY(-2px); }
        .links { text-align: center; margin-top: 1rem; }
        .links a { color: #667eea; text-decoration: none; }
        .demo-banner { 
            background: #e3f2fd; 
            padding: 1rem; 
            border-radius: 8px; 
            margin-bottom: 1rem; 
            text-align: center; 
            color: #1976d2; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>🌾 AgriWeb 2.0</h1>
            <p>Solution d'analyse agricole professionnelle</p>
        </div>
        
        {% if not STRIPE_AVAILABLE %}
        <div class="demo-banner">
            <strong>🧪 Mode Démo</strong><br>
            Hébergement gratuit - Fonctionnalités limitées
        </div>
        {% endif %}
        
        {% if error %}
        <div style="background: #ffebee; color: #c62828; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            {{ error }}
        </div>
        {% endif %}
        
        <form method="POST">
            <div class="form-group">
                <label for="email">📧 Email</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="password">🔒 Mot de passe</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit">🚀 Se connecter</button>
        </form>
        
        <div class="links">
            <a href="/register">📝 Créer un compte</a> | 
            <a href="/demo">🧪 Démo gratuite</a>
        </div>
        
        <div style="text-align: center; margin-top: 2rem; font-size: 0.9rem; color: #666;">
            <p>🆓 Hébergé gratuitement sur {{ platform }}</p>
            {% if STRIPE_AVAILABLE %}
            <p>💳 Paiements sécurisés par Stripe</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

REGISTER_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📝 Inscription - AgriWeb 2.0</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; 
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            min-height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
        }
        .container { 
            background: white; 
            padding: 3rem; 
            border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 500px; 
            width: 100%; 
        }
        .form-group { margin: 1rem 0; }
        label { display: block; margin-bottom: 0.5rem; font-weight: 600; }
        input { 
            width: 100%; 
            padding: 0.8rem; 
            border: 2px solid #e0e0e0; 
            border-radius: 8px; 
            font-size: 1rem; 
        }
        button { 
            width: 100%; 
            background: linear-gradient(45deg, #28a745, #20c997); 
            color: white; 
            border: none; 
            padding: 1rem; 
            border-radius: 8px; 
            font-size: 1.1rem; 
            cursor: pointer; 
            margin-top: 1rem;
        }
        .trial-info { 
            background: #e8f5e8; 
            padding: 1rem; 
            border-radius: 8px; 
            margin: 1rem 0; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📝 Inscription AgriWeb 2.0</h1>
        
        <div class="trial-info">
            <h3>🆓 Essai Gratuit Inclus</h3>
            <ul>
                <li>✅ 15 jours d'accès complet</li>
                <li>✅ 50 recherches gratuites</li>
                <li>✅ Toutes les fonctionnalités</li>
                {% if STRIPE_AVAILABLE %}
                <li>✅ Upgrade possible vers plans payants</li>
                {% endif %}
            </ul>
        </div>
        
        {% if error %}
        <div style="background: #ffebee; color: #c62828; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            {{ error }}
        </div>
        {% endif %}
        
        <form method="POST">
            <div class="form-group">
                <label for="name">👤 Nom complet</label>
                <input type="text" id="name" name="name" required>
            </div>
            
            <div class="form-group">
                <label for="email">📧 Email</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="password">🔒 Mot de passe</label>
                <input type="password" id="password" name="password" required minlength="6">
            </div>
            
            <button type="submit">🚀 Créer mon compte gratuit</button>
        </form>
        
        <div style="text-align: center; margin-top: 2rem;">
            <a href="/login" style="color: #28a745;">← Retour à la connexion</a>
        </div>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Dashboard - AgriWeb 2.0</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; 
            background: #f5f5f5; 
        }
        .header { 
            background: linear-gradient(45deg, #667eea, #764ba2); 
            color: white; 
            padding: 1rem; 
        }
        .container { 
            max-width: 1200px; 
            margin: 2rem auto; 
            padding: 0 2rem; 
        }
        .card { 
            background: white; 
            border-radius: 12px; 
            padding: 2rem; 
            margin: 1rem 0; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        }
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 1rem; 
        }
        .stat-card { 
            background: white; 
            border-radius: 8px; 
            padding: 1.5rem; 
            text-align: center; 
        }
        .btn { 
            background: #007bff; 
            color: white; 
            padding: 0.8rem 1.5rem; 
            text-decoration: none; 
            border-radius: 6px; 
            display: inline-block; 
            margin: 0.5rem; 
        }
        .btn-success { background: #28a745; }
        .btn-warning { background: #ffc107; color: #212529; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌾 AgriWeb 2.0 - Dashboard</h1>
        <p>Bienvenue {{ user_name }} ({{ user_email }}) | <a href="/logout" style="color: white;">Déconnexion</a></p>
    </div>
    
    <div class="container">
        <!-- Statut compte -->
        <div class="card">
            <h2>📋 Votre Compte</h2>
            <p><strong>Type :</strong> {{ license_type|title }}</p>
            <p><strong>Statut :</strong> 
                {% if active %}
                    <span style="color: #28a745;">✅ Actif</span>
                {% else %}
                    <span style="color: #dc3545;">⚠️ Inactif</span>
                {% endif %}
            </p>
            
            {% if STRIPE_AVAILABLE and license_type == 'trial' %}
                <div style="background: #e3f2fd; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                    <h4>🚀 Upgrade disponible</h4>
                    <p>Passez à un plan payant pour plus de fonctionnalités !</p>
                    <a href="/pricing" class="btn btn-success">Voir les plans</a>
                </div>
            {% endif %}
        </div>
        
        <!-- Statistiques d'usage -->
        <div class="stats-grid">
            <div class="stat-card">
                <h3>🔍 Recherches</h3>
                <p style="font-size: 2rem; color: #007bff;">{{ searches_used }}</p>
                <p>sur {{ searches_limit }} autorisées</p>
            </div>
            
            <div class="stat-card">
                <h3>📊 Rapports</h3>
                <p style="font-size: 2rem; color: #28a745;">{{ reports_generated or 0 }}</p>
                <p>générés ce mois</p>
            </div>
            
            <div class="stat-card">
                <h3>💡 Statut</h3>
                <p style="font-size: 1.5rem;">
                    {% if license_type == 'trial' %}
                        🆓 Essai gratuit
                    {% else %}
                        💳 Abonné {{ license_type }}
                    {% endif %}
                </p>
            </div>
        </div>
        
        <!-- Actions rapides -->
        <div class="card">
            <h2>🚀 Actions Rapides</h2>
            <a href="/search" class="btn">🔍 Nouvelle recherche</a>
            <a href="/reports" class="btn">📊 Mes rapports</a>
            
            {% if STRIPE_AVAILABLE %}
                <a href="/pricing" class="btn btn-warning">💳 Gérer abonnement</a>
            {% endif %}
            
            <div style="margin-top: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                <h4>🌐 Informations de déploiement</h4>
                <p><strong>Plateforme :</strong> {{ platform }}</p>
                <p><strong>Mode :</strong> 
                    {% if STRIPE_AVAILABLE %}
                        💳 Paiements activés
                    {% else %}
                        🧪 Version démo
                    {% endif %}
                </p>
                <p><strong>URL :</strong> {{ request.url_root }}</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

def get_platform_name():
    """Détecte la plateforme d'hébergement"""
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        return "Railway"
    elif os.environ.get('RENDER'):
        return "Render"
    elif os.environ.get('DYNO'):
        return "Heroku"
    elif os.environ.get('VERCEL'):
        return "Vercel"
    else:
        return "Hébergement local"

# Routes principales
@app.route('/')
def home():
    """Page d'accueil"""
    if session.get('authenticated'):
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = user_manager.authenticate_user(email, password)
        if user:
            session['authenticated'] = True
            session['user_data'] = user
            session['user_id'] = user.get('id', str(uuid.uuid4()))
            session['user_email'] = email
            flash('Connexion réussie !', 'success')
            return redirect('/app')
        else:
            return render_template_string(
                LOGIN_TEMPLATE, 
                error="Email ou mot de passe incorrect",
                STRIPE_AVAILABLE=STRIPE_AVAILABLE,
                platform=get_platform_name()
            )
    
    return render_template_string(
        LOGIN_TEMPLATE, 
        STRIPE_AVAILABLE=STRIPE_AVAILABLE,
        platform=get_platform_name()
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Essayer d'abord SimpleUserManager (hébergement gratuit)
            if hasattr(user_manager, 'create_user') and hasattr(user_manager, 'users'):
                # SimpleUserManager - utilise create_user/users
                user_id = user_manager.create_user(email, password, name or "")
                user_data = user_manager.users[email]
                print(f"✅ Compte créé avec SimpleUserManager: {email}")
            elif hasattr(user_manager, 'add_user') and hasattr(user_manager, 'get_user'):
                # UserManager de production - utilise add_user/get_user
                user_id = user_manager.add_user(email, password, name)
                user_data = user_manager.get_user(email)
                print(f"✅ Compte créé avec UserManager: {email}")
            else:
                # Fallback - créer un utilisateur manuel
                user_id = str(uuid.uuid4())
                user_data = {
                    'id': user_id,
                    'email': email,
                    'name': name or "",
                    'created_at': datetime.now().isoformat(),
                    'active': True,
                    'license_type': 'trial',
                    'searches_used': 0,
                    'searches_limit': 50
                }
                print(f"✅ Compte créé en mode fallback: {email}")
            
            session['authenticated'] = True
            session['user_data'] = user_data
            session['user_id'] = user_id
            session['user_email'] = email
            flash('Compte créé avec succès !', 'success')
            return redirect('/dashboard')
        except Exception as e:
            print(f"❌ Erreur création compte: {e}")
            return render_template_string(
                REGISTER_TEMPLATE, 
                error=f"Erreur lors de la création du compte: {e}",
                STRIPE_AVAILABLE=STRIPE_AVAILABLE
            )
    
    return render_template_string(
        REGISTER_TEMPLATE,
        STRIPE_AVAILABLE=STRIPE_AVAILABLE
    )

@app.route('/dashboard')
def dashboard():
    """Dashboard principal"""
    if not session.get('authenticated'):
        return redirect('/login')
    
    user_data = session.get('user_data', {})
    
    return render_template_string(
        DASHBOARD_TEMPLATE,
        user_name=user_data.get('name', 'Utilisateur'),
        user_email=user_data.get('email', ''),
        license_type=user_data.get('license_type', 'trial'),
        active=user_data.get('active', True),
        searches_used=user_data.get('searches_used', 0),
        searches_limit=user_data.get('searches_limit', 50),
        reports_generated=user_data.get('reports_generated', 0),
        STRIPE_AVAILABLE=STRIPE_AVAILABLE,
        platform=get_platform_name()
    )

@app.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    flash('Déconnexion réussie !', 'info')
    return redirect('/login')

# Routes conditionnelles pour Stripe
if STRIPE_AVAILABLE:
    @app.route('/pricing')
    def pricing():
        """Page de sélection d'abonnement"""
        if not session.get('authenticated'):
            return redirect('/login')
        
        # Utiliser le template de pricing depuis agriweb_avec_paiements.py
        from agriweb_avec_paiements import PAYMENT_SELECTION_TEMPLATE
        
        user_data = session.get('user_data', {})
        return render_template_string(
            PAYMENT_SELECTION_TEMPLATE,
            user_email=user_data.get('email', ''),
            stripe_publishable_key=Config.STRIPE_PUBLISHABLE_KEY
        )
    
    @app.route('/api/payment/create-checkout', methods=['POST'])
    def create_checkout_session():
        """Crée une session de paiement Stripe"""
        if not session.get('authenticated'):
            return jsonify({"error": "Non autorisé"}), 401
        
        try:
            data = request.get_json()
            plan = data.get('plan')
            
            user_data = session.get('user_data', {})
            user_email = user_data.get('email')
            
            result = stripe_payment_manager.create_checkout_session(
                customer_email=user_email,
                plan=plan,
                success_url=f"{request.url_root}payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{request.url_root}payment/cancel"
            )
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/app')
def app_welcome():
    """Page d'accueil de l'application AgriWeb avec le bouton d'ouverture"""
    if not session.get('user_id'):
        return redirect('/login')
    
    user_email = session.get('user_email', 'Utilisateur')
    user_name = user_email.split('@')[0] if '@' in user_email else user_email
    
    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🚀 AgriWeb 2.0</title>
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0; 
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                min-height: 100vh; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
            }}
            .container {{ 
                background: white; 
                padding: 3rem; 
                border-radius: 20px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                max-width: 600px; 
                width: 100%; 
                text-align: center;
            }}
            .welcome-title {{ 
                font-size: 2.5rem; 
                margin-bottom: 1rem; 
                color: #28a745;
            }}
            .welcome-message {{ 
                font-size: 1.2rem; 
                margin-bottom: 2rem; 
                color: #666;
                line-height: 1.6;
            }}
            .app-button {{ 
                background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
                color: white; 
                padding: 1rem 2rem; 
                text-decoration: none; 
                border-radius: 12px; 
                display: inline-block; 
                font-size: 1.1rem; 
                font-weight: 600;
                transition: transform 0.2s, box-shadow 0.2s;
                margin: 1rem;
            }}
            .app-button:hover {{ 
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(0,123,255,0.3);
            }}
            .secondary-button {{ 
                background: #6c757d;
                color: white; 
                padding: 0.8rem 1.5rem; 
                text-decoration: none; 
                border-radius: 8px; 
                display: inline-block; 
                margin: 0.5rem;
            }}
            .user-info {{
                background: #f8f9fa;
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 2rem;
                color: #666;
            }}
            .features {{
                text-align: left;
                margin: 2rem 0;
                background: #f8f9fa;
                padding: 1.5rem;
                border-radius: 8px;
            }}
            .features h3 {{
                color: #28a745;
                margin-bottom: 1rem;
            }}
            .features ul {{
                list-style: none;
                padding: 0;
            }}
            .features li {{
                padding: 0.5rem 0;
                color: #666;
            }}
            .features li:before {{
                content: "✅ ";
                margin-right: 0.5rem;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="welcome-title">🚀 Bienvenue dans AgriWeb 2.0 !</h1>
            
            <div class="user-info">
                <p><strong>Utilisateur :</strong> {user_name} ({user_email})</p>
                <p><strong>Statut :</strong> Essai gratuit actif ✅</p>
            </div>
            
            <p class="welcome-message">
                Votre essai gratuit est actif. Accédez à toutes les fonctionnalités de géolocalisation agricole.
            </p>
            
            <div class="features">
                <h3>🌾 Fonctionnalités disponibles :</h3>
                <ul>
                    <li>Recherche géographique avancée</li>
                    <li>Analyse des données agricoles</li>
                    <li>Cartographie interactive</li>
                    <li>Rapports détaillés</li>
                    <li>Données en temps réel</li>
                </ul>
            </div>
            
            <div style="margin: 2rem 0;">
                <a href="/search" class="app-button">🔍 Ouvrir l'application</a>
            </div>
            
            <div>
                <a href="/dashboard" class="secondary-button">📊 Tableau de bord</a>
                <a href="/logout" class="secondary-button">🚪 Déconnexion</a>
            </div>
            
            <div style="text-align: center; margin-top: 2rem; font-size: 0.9rem; color: #666;">
                <p>🆓 Hébergé gratuitement sur {get_platform_name()}</p>
                {'<p>💳 Paiements sécurisés par Stripe</p>' if STRIPE_AVAILABLE else '<p>🧪 Version démo</p>'}
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/search')
def search():
    """Interface de recherche AgriWeb"""
    if not session.get('user_id'):
        return redirect('/login')
    
    user_email = session.get('user_email', 'Utilisateur')
    user_name = user_email.split('@')[0] if '@' in user_email else user_email
    
    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🔍 Recherche AgriWeb 2.0</title>
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0; 
                background: #f8f9fa;
                min-height: 100vh; 
            }}
            .header {{
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                color: white;
                padding: 1rem;
                text-align: center;
            }}
            .container {{ 
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }}
            .search-form {{
                background: white;
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }}
            .form-group {{
                margin: 1rem 0;
            }}
            label {{
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 600;
                color: #333;
            }}
            input, select {{
                width: 100%;
                padding: 0.8rem;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                font-size: 1rem;
            }}
            input:focus, select:focus {{
                outline: none;
                border-color: #28a745;
            }}
            .btn {{
                background: #28a745;
                color: white;
                padding: 0.8rem 1.5rem;
                border: none;
                border-radius: 8px;
                font-size: 1rem;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 0.5rem;
            }}
            .btn:hover {{
                background: #218838;
            }}
            .btn-secondary {{
                background: #6c757d;
            }}
            .btn-secondary:hover {{
                background: #5a6268;
            }}
            .results-area {{
                background: white;
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                min-height: 400px;
                text-align: center;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 AgriWeb 2.0 - Recherche</h1>
            <p>Utilisateur: {user_name} ({user_email}) | <a href="/logout" style="color: white;">Déconnexion</a></p>
        </div>
        
        <div class="container">
            <div class="search-form">
                <h2>🌾 Recherche Géographique</h2>
                <form id="searchForm">
                    <div class="form-group">
                        <label for="address">📍 Adresse ou Coordonnées :</label>
                        <input type="text" id="address" name="address" placeholder="Ex: Lyon, France ou 45.764,4.836" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="radius">📏 Rayon de recherche (km) :</label>
                        <select id="radius" name="radius">
                            <option value="1">1 km</option>
                            <option value="5" selected>5 km</option>
                            <option value="10">10 km</option>
                            <option value="25">25 km</option>
                            <option value="50">50 km</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="type">🏷️ Type de recherche :</label>
                        <select id="type" name="type">
                            <option value="parcels">🌾 Parcelles agricoles</option>
                            <option value="buildings">🏠 Bâtiments</option>
                            <option value="roads">🛣️ Routes</option>
                            <option value="all">🗺️ Tout</option>
                        </select>
                    </div>
                    
                    <button type="submit" class="btn">🔍 Lancer la recherche</button>
                    <a href="/app" class="btn btn-secondary">← Retour</a>
                    <a href="/dashboard" class="btn btn-secondary">📊 Dashboard</a>
                </form>
            </div>
            
            <div class="results-area">
                <h3>📊 Résultats de recherche</h3>
                <p id="status">🎯 Entrez une adresse et cliquez sur "Lancer la recherche" pour commencer.</p>
                <div id="results" style="margin-top: 2rem;"></div>
            </div>
        </div>
        
        <script>
        document.getElementById('searchForm').addEventListener('submit', function(e) {{
            e.preventDefault();
            
            const status = document.getElementById('status');
            const results = document.getElementById('results');
            
            status.innerHTML = '🔄 Recherche en cours...';
            results.innerHTML = '';
            
            // Simulation d'une recherche
            setTimeout(() => {{
                status.innerHTML = '✅ Recherche terminée !';
                results.innerHTML = `
                    <div style="text-align: left; background: #e3f2fd; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                        <h4>🌾 Résultats trouvés :</h4>
                        <ul>
                            <li>📍 12 parcelles agricoles identifiées</li>
                            <li>🏠 8 bâtiments agricoles trouvés</li>
                            <li>🛣️ 3 routes d'accès principales</li>
                            <li>📊 Données mises à jour il y a 2 heures</li>
                        </ul>
                        <p><strong>Note :</strong> Ceci est une démonstration. L'intégration complète avec l'application AgriWeb est en cours.</p>
                    </div>
                `;
            }}, 2000);
        }});
        </script>
    </body>
    </html>
    """

@app.route('/reports')
def reports():
    """Page des rapports"""
    if not session.get('user_id'):
        return redirect('/login')
    
    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📊 Rapports AgriWeb 2.0</title>
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0; 
                background: #f8f9fa;
                min-height: 100vh; 
            }}
            .header {{
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                color: white;
                padding: 1rem;
                text-align: center;
            }}
            .container {{ 
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }}
            .card {{
                background: white;
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }}
            .btn {{
                background: #28a745;
                color: white;
                padding: 0.8rem 1.5rem;
                border: none;
                border-radius: 8px;
                text-decoration: none;
                display: inline-block;
                margin: 0.5rem;
            }}
            .btn-secondary {{
                background: #6c757d;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Mes Rapports</h1>
            <p><a href="/logout" style="color: white;">Déconnexion</a></p>
        </div>
        
        <div class="container">
            <div class="card">
                <h2>📈 Rapports d'analyse</h2>
                <p>Vos rapports d'analyse géographique apparaîtront ici.</p>
                <p><em>Fonctionnalité en cours de développement...</em></p>
                
                <a href="/search" class="btn">🔍 Nouvelle recherche</a>
                <a href="/app" class="btn btn-secondary">← Retour</a>
                <a href="/dashboard" class="btn btn-secondary">📊 Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/demo')
def demo():
    """Page de démonstration"""
    return """
    <h1>🧪 Démo AgriWeb 2.0</h1>
    <p>Cette version de démonstration est hébergée gratuitement.</p>
    <p>Fonctionnalités disponibles en mode démo :</p>
    <ul>
        <li>✅ Authentification utilisateurs</li>
        <li>✅ Interface responsive</li>
        <li>✅ Dashboard basique</li>
        {}
    </ul>
    <a href="/register">📝 Créer un compte gratuit</a>
    """.format(
        "<li>✅ Système de paiement Stripe</li>" if STRIPE_AVAILABLE else "<li>⚠️ Paiements désactivés (mode démo)</li>"
    )

@app.route('/health')
def health():
    """Health check pour les plateformes d'hébergement"""
    return jsonify({
        "status": "healthy",
        "platform": get_platform_name(),
        "stripe_available": STRIPE_AVAILABLE,
        "user_manager": USER_MANAGER_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    })

# Configuration pour production
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = Config.DEBUG
    
    print(f"🚀 Démarrage AgriWeb 2.0")
    print(f"📍 Plateforme: {get_platform_name()}")
    print(f"🔌 Port: {port}")
    print(f"💳 Stripe: {'✅' if STRIPE_AVAILABLE else '❌'}")
    print(f"👥 UserManager: {'✅' if USER_MANAGER_AVAILABLE else '❌ (simplifié)'}")
    print(f"🗺️ GeoServer: {GEOSERVER_URL}")
    
    # Test de connexion GeoServer au démarrage
    def test_geoserver_connection():
        """Test initial de GeoServer avec authentification"""
        try:
            import requests
            from requests.auth import HTTPBasicAuth
            
            auth = HTTPBasicAuth(Config.GEOSERVER_USERNAME, Config.GEOSERVER_PASSWORD)
            response = requests.get(f"{GEOSERVER_URL}/web/", auth=auth, timeout=5)
            
            if response.status_code == 200:
                print("✅ GeoServer: Connexion établie avec authentification")
                return True
            elif response.status_code == 401:
                print("⚠️ GeoServer: Erreur d'authentification - vérifiez GEOSERVER_USERNAME et GEOSERVER_PASSWORD")
                return False
            else:
                print("⏳ GeoServer: En cours de démarrage...")
                return False
        except:
            print("⏳ GeoServer: Non accessible (démarrage en cours)")
            return False
    
    # Test optionnel au démarrage (non bloquant)
    try:
        geoserver_status = test_geoserver_connection()
        if not geoserver_status:
            print("💡 GeoServer peut prendre quelques minutes pour démarrer complètement")
            if Config.GEOSERVER_TUNNEL:
                print(f"🌐 Vérifiez manuellement: {Config.GEOSERVER_TUNNEL}/web/")
            else:
                print("🌐 Vérifiez manuellement: https://geoserver-agriweb-production.up.railway.app/geoserver/web/")
    except:
        pass
    
    # Configuration des couches GeoServer selon la documentation officielle
    print("📋 Configuration des couches GeoServer:")
    GEOSERVER_LAYERS_CONFIG = {
        "workspace": "gpu",  # Workspace principal selon documentation
        "layers": {
            # Couches cadastrales - Compatible Servlet API 4 (Tomcat 9)
            "cadastre": "gpu:prefixes_sections",
            "parcelles": "gpu:PARCELLE2024", 
            "plu": "gpu:gpu1",
            
            # Couches énergétiques  
            "postes_bt": "gpu:poste_elec_shapefile",
            "postes_hta": "gpu:postes-electriques-rte", 
            "capacites": "gpu:CapacitesDAccueil",
            
            # Couches agricoles
            "rpg": "gpu:PARCELLES_GRAPHIQUES",
            "eleveurs": "gpu:etablissements_eleveurs",
            
            # Couches commerciales
            "sirene": "gpu:GeolocalisationEtablissement_Sirene france",
            
            # Couches terrain
            "parkings": "gpu:parkings_sup500m2",
            "friches": "gpu:friches-standard", 
            "solaire": "gpu:POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93",
            
            # Couches réglementaires
            "zaer": "gpu:ZAER_ARRETE_SHP_FRA",
            "ppri": "gpu:ppri"
        },
        "endpoints": {
            "wfs": f"{GEOSERVER_URL}/ows",      # Service WFS selon doc
            "wms": f"{GEOSERVER_URL}/wms",      # Service WMS selon doc
            "admin": f"{GEOSERVER_URL}/web/"    # Interface admin selon doc
        }
    }
    
    print(f"🗂️ Workspace: {GEOSERVER_LAYERS_CONFIG['workspace']}")
    print(f"📊 Couches configurées: {len(GEOSERVER_LAYERS_CONFIG['layers'])}")
    print(f"🔗 Endpoints WFS: {GEOSERVER_LAYERS_CONFIG['endpoints']['wfs']}")
    print(f"🌐 Admin: {GEOSERVER_LAYERS_CONFIG['endpoints']['admin']}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
