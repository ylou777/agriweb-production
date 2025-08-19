#!/usr/bin/env python3
"""
🚀 AGRIWEB 2.0 - VERSION PRODUCTION COMPLÈTE AVEC AUTHENTIFICATION
Intégration de l'application AgriWeb complète avec authentification et paiements
Optimisé pour hébergement gratuit (Railway, Render, Heroku)
"""

from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for, flash
import json
import os
import uuid
from datetime import datetime, timedelta
import hashlib
import secrets

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

# Configuration
app = Flask(__name__)
app.config.from_object(Config)

# Désactiver Stripe pour déploiement Railway (simplifié)
STRIPE_AVAILABLE = False
print("⚠️ Stripe désactivé pour déploiement Railway")

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

# Instance du gestionnaire d'utilisateurs
user_manager = SimpleUserManager()

# Templates d'authentification
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
        
        <div class="demo-banner">
            <strong>🧪 Mode Démo</strong><br>
            Hébergement gratuit - Fonctionnalités limitées
        </div>
        
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

# Décorateur pour vérifier l'authentification
def login_required(f):
    """Décorateur pour protéger les routes nécessitant une connexion"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# Routes d'authentification
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
            return redirect('/')
        else:
            return render_template_string(
                LOGIN_TEMPLATE, 
                error="Email ou mot de passe incorrect",
                platform=get_platform_name()
            )
    
    return render_template_string(
        LOGIN_TEMPLATE, 
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
            return redirect('/')
        except Exception as e:
            print(f"❌ Erreur création compte: {e}")
            return render_template_string(
                REGISTER_TEMPLATE, 
                error=f"Erreur lors de la création du compte: {e}"
            )
    
    return render_template_string(REGISTER_TEMPLATE)

@app.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    flash('Déconnexion réussie !', 'info')
    return redirect('/login')

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
        <li>⚠️ Paiements désactivés (mode démo)</li>
    </ul>
    <a href="/register">📝 Créer un compte gratuit</a>
    """

# IMPORTANT: Maintenant on importe TOUTES les fonctionnalités AgriWeb
# 🚀 Importation de l'application AgriWeb complète
print("🔄 Chargement de l'application AgriWeb complète...")

# Imports nécessaires pour AgriWeb
try:
    from agriweb_source import *
    print("✅ Application AgriWeb complète chargée avec succès!")
    AGRIWEB_LOADED = True
except ImportError as e:
    print(f"❌ Erreur chargement AgriWeb: {e}")
    AGRIWEB_LOADED = False

# Configuration pour production
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = Config.DEBUG
    
    print(f"🚀 Démarrage AgriWeb 2.0 COMPLET avec authentification")
    print(f"📍 Plateforme: {get_platform_name()}")
    print(f"🔌 Port: {port}")
    print(f"👥 UserManager: ✅ (simplifié)")
    print(f"🌾 AgriWeb complet: {'✅' if AGRIWEB_LOADED else '❌'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
