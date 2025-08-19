#!/usr/bin/env python3
"""
🚀 AGRIWEB 2.0 - VERSION PRODUCTION COMPLÈTE
Intégration de l'application complète AgriWeb avec authentification
Optimisé pour hébergement gratuit (Railway, Render, Heroku)
"""

from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for, flash
import json
import os
import uuid
from datetime import datetime, timedelta
import hashlib
import secrets
from functools import wraps

# Configuration pour hébergement
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Configuration GeoServer
    GEOSERVER_LOCAL = "http://localhost:8080/geoserver"
    GEOSERVER_RAILWAY = "https://geoserver-agriweb-production.up.railway.app/geoserver"
    GEOSERVER_USERNAME = os.environ.get('GEOSERVER_USERNAME', 'admin')
    GEOSERVER_PASSWORD = os.environ.get('GEOSERVER_PASSWORD', 'geoserver')

# Création de l'application Flask
app = Flask(__name__)
app.config.from_object(Config)

# Gestionnaire d'utilisateurs simple
class SimpleUserManager:
    def __init__(self):
        self.users_file = 'users.json'
        self.users = self.load_users()
    
    def load_users(self):
        """Charge les utilisateurs depuis le fichier JSON"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"❌ Erreur chargement utilisateurs: {e}")
            return {}
    
    def save_users(self):
        """Sauvegarde les utilisateurs dans le fichier JSON"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Erreur sauvegarde utilisateurs: {e}")
            return False
    
    def hash_password(self, password):
        """Hash le mot de passe avec salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password, stored_hash):
        """Vérifie le mot de passe"""
        try:
            salt, password_hash = stored_hash.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except:
            return False
    
    def create_user(self, email, password, subscription_type="trial", **kwargs):
        """Crée un nouvel utilisateur"""
        if email in self.users:
            return False, "Utilisateur existe déjà"
        
        user_data = {
            "id": str(uuid.uuid4()),
            "email": email,
            "password": self.hash_password(password),
            "subscription": subscription_type,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "is_active": True
        }
        user_data.update(kwargs)
        
        self.users[email] = user_data
        if self.save_users():
            return True, "Utilisateur créé avec succès"
        return False, "Erreur lors de la création"
    
    def authenticate_user(self, email, password):
        """Authentifie un utilisateur"""
        if email not in self.users:
            return False, "Utilisateur non trouvé"
        
        user = self.users[email]
        if not user.get('is_active', True):
            return False, "Compte désactivé"
        
        if self.verify_password(password, user['password']):
            # Mise à jour de la dernière connexion
            self.users[email]['last_login'] = datetime.now().isoformat()
            self.save_users()
            return True, user
        
        return False, "Mot de passe incorrect"

# Instance du gestionnaire d'utilisateurs
user_manager = SimpleUserManager()

# Décorateur pour vérifier l'authentification
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# Import de l'application AgriWeb complète
def import_agriweb_source():
    """Import dynamique de l'application AgriWeb source avec gestion d'erreurs"""
    try:
        import sys
        import importlib.util
        
        # Chemin vers agriweb_source.py
        source_path = os.path.join(os.path.dirname(__file__), 'agriweb_source.py')
        
        if not os.path.exists(source_path):
            print(f"❌ Fichier agriweb_source.py non trouvé: {source_path}")
            return None
        
        # Import du module
        spec = importlib.util.spec_from_file_location("agriweb_source", source_path)
        agriweb_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agriweb_module)
        
        print("✅ Module agriweb_source importé avec succès")
        return agriweb_module
        
    except Exception as e:
        print(f"❌ Erreur import agriweb_source: {e}")
        return None

# ===== ROUTES D'AUTHENTIFICATION =====

@app.route('/')
def index():
    """Page d'accueil - Redirection selon l'état d'authentification"""
    if session.get('user_id'):
        # Import de l'application AgriWeb source
        agriweb_module = import_agriweb_source()
        if agriweb_module and hasattr(agriweb_module, 'app'):
            try:
                # Créer une version de la route principale avec authentification
                source_app = agriweb_module.app
                
                # Chercher la route principale dans l'application source
                for rule in source_app.url_map.iter_rules():
                    if rule.rule == '/' and 'GET' in rule.methods:
                        view_func = source_app.view_functions.get(rule.endpoint)
                        if view_func:
                            # Exécuter la fonction avec le contexte approprié
                            with source_app.app_context():
                                return view_func()
                
                # Si pas de route trouvée, rediriger vers l'interface de recherche
                return redirect('/search_interface')
                
            except Exception as e:
                print(f"❌ Erreur exécution AgriWeb source: {e}")
                return redirect('/search_interface')
        else:
            return redirect('/search_interface')
    else:
        return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Veuillez remplir tous les champs', 'error')
            return redirect('/login')
        
        success, result = user_manager.authenticate_user(email, password)
        
        if success:
            session['user_id'] = result['id']
            session['user_email'] = result['email']
            session['subscription'] = result.get('subscription', 'trial')
            session['authenticated'] = True
            flash('Connexion réussie !', 'success')
            return redirect('/')
        else:
            flash(f'Erreur de connexion: {result}', 'error')
            return redirect('/login')
    
    return """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🚀 Connexion AgriWeb 2.0</title>
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
            .login-container { 
                background: white; 
                padding: 2rem; 
                border-radius: 12px; 
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                max-width: 400px; 
                width: 100%; 
            }
            .form-group { margin: 1rem 0; }
            label { display: block; margin-bottom: 0.5rem; font-weight: 600; }
            input { 
                width: 100%; 
                padding: 0.8rem; 
                border: 2px solid #e9ecef; 
                border-radius: 8px; 
                font-size: 1rem; 
            }
            input:focus { outline: none; border-color: #28a745; }
            .btn { 
                background: #28a745; 
                color: white; 
                padding: 0.8rem 1.5rem; 
                border: none; 
                border-radius: 8px; 
                font-size: 1rem; 
                cursor: pointer; 
                width: 100%; 
            }
            .btn:hover { background: #218838; }
            .register-link { text-align: center; margin-top: 1rem; }
            .register-link a { color: #28a745; text-decoration: none; }
            .alert { 
                padding: 0.8rem; 
                border-radius: 6px; 
                margin-bottom: 1rem; 
            }
            .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .alert-success { background: #d1eddb; color: #155724; border: 1px solid #c3e6cb; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h1 style="text-align: center; color: #28a745; margin-bottom: 2rem;">🚀 AgriWeb 2.0</h1>
            
            <form method="POST">
                <div class="form-group">
                    <label for="email">📧 Email :</label>
                    <input type="email" id="email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label for="password">🔑 Mot de passe :</label>
                    <input type="password" id="password" name="password" required>
                </div>
                
                <button type="submit" class="btn">🚀 Se connecter</button>
            </form>
            
            <div class="register-link">
                <p>Pas encore de compte ? <a href="/register">Créer un compte</a></p>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not email or not password:
            flash('Veuillez remplir tous les champs', 'error')
            return redirect('/register')
        
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas', 'error')
            return redirect('/register')
        
        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères', 'error')
            return redirect('/register')
        
        success, message = user_manager.create_user(email, password)
        
        if success:
            flash('Compte créé avec succès ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect('/login')
        else:
            flash(f'Erreur lors de la création du compte: {message}', 'error')
            return redirect('/register')
    
    return """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📝 Inscription AgriWeb 2.0</title>
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
            .register-container { 
                background: white; 
                padding: 2rem; 
                border-radius: 12px; 
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                max-width: 400px; 
                width: 100%; 
            }
            .form-group { margin: 1rem 0; }
            label { display: block; margin-bottom: 0.5rem; font-weight: 600; }
            input { 
                width: 100%; 
                padding: 0.8rem; 
                border: 2px solid #e9ecef; 
                border-radius: 8px; 
                font-size: 1rem; 
            }
            input:focus { outline: none; border-color: #28a745; }
            .btn { 
                background: #28a745; 
                color: white; 
                padding: 0.8rem 1.5rem; 
                border: none; 
                border-radius: 8px; 
                font-size: 1rem; 
                cursor: pointer; 
                width: 100%; 
            }
            .btn:hover { background: #218838; }
            .login-link { text-align: center; margin-top: 1rem; }
            .login-link a { color: #28a745; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="register-container">
            <h1 style="text-align: center; color: #28a745; margin-bottom: 2rem;">📝 Créer un compte</h1>
            
            <form method="POST">
                <div class="form-group">
                    <label for="email">📧 Email :</label>
                    <input type="email" id="email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label for="password">🔑 Mot de passe :</label>
                    <input type="password" id="password" name="password" minlength="6" required>
                </div>
                
                <div class="form-group">
                    <label for="confirm_password">🔑 Confirmer le mot de passe :</label>
                    <input type="password" id="confirm_password" name="confirm_password" minlength="6" required>
                </div>
                
                <button type="submit" class="btn">📝 Créer mon compte</button>
            </form>
            
            <div class="login-link">
                <p>Déjà un compte ? <a href="/login">Se connecter</a></p>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    flash('Vous avez été déconnecté avec succès', 'success')
    return redirect('/login')

# ===== INTÉGRATION AGRIWEB SOURCE =====

@app.route('/search_interface')
@login_required
def search_interface():
    """Interface de recherche de base si AgriWeb source n'est pas disponible"""
    user_email = session.get('user_email', 'Utilisateur')
    user_name = user_email.split('@')[0] if '@' in user_email else user_email
    
    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🌾 AgriWeb 2.0 - Interface Principal</title>
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
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .user-info {{
                display: flex;
                align-items: center;
                gap: 1rem;
            }}
            .container {{ 
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }}
            .main-interface {{
                background: white;
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }}
            .status-card {{
                background: #e3f2fd;
                padding: 1.5rem;
                border-radius: 8px;
                margin: 1rem 0;
                border-left: 4px solid #2196f3;
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
                cursor: pointer;
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
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌾 AgriWeb 2.0</h1>
            <div class="user-info">
                <span>👤 {user_name}</span>
                <a href="/logout" style="color: white; text-decoration: none;">🚪 Déconnexion</a>
            </div>
        </div>
        
        <div class="container">
            <div class="main-interface">
                <h2>🚀 Interface Principal AgriWeb</h2>
                
                <div class="status-card">
                    <h3>📊 Statut du système</h3>
                    <p><strong>Utilisateur :</strong> {user_email}</p>
                    <p><strong>Subscription :</strong> {session.get('subscription', 'trial').upper()}</p>
                    <p><strong>Session active :</strong> ✅ Oui</p>
                </div>
                
                <div style="margin: 2rem 0;">
                    <h3>🛠️ Fonctionnalités disponibles</h3>
                    <div>
                        <a href="/test_agriweb" class="btn">🧪 Tester AgriWeb Source</a>
                        <a href="/carte" class="btn">🗺️ Carte Interactive</a>
                        <a href="/recherche" class="btn">🔍 Recherche Avancée</a>
                        <a href="/rapports" class="btn">📊 Rapports</a>
                    </div>
                </div>
                
                <div class="status-card">
                    <h3>ℹ️ Information</h3>
                    <p>Cette interface utilise l'authentification intégrée. L'application AgriWeb complète est en cours d'intégration.</p>
                    <p>Si vous voyez ce message, cela signifie que le système d'authentification fonctionne correctement.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/test_agriweb')
@login_required
def test_agriweb():
    """Test de l'intégration avec AgriWeb source"""
    agriweb_module = import_agriweb_source()
    
    if agriweb_module:
        return f"""
        <h1>✅ Succès d'intégration AgriWeb</h1>
        <p>Module AgriWeb source importé avec succès !</p>
        <p>Module détecté : {type(agriweb_module)}</p>
        <p>Attributs disponibles : {dir(agriweb_module)[:10]}...</p>
        <a href="/search_interface">← Retour</a>
        """
    else:
        return f"""
        <h1>❌ Erreur d'intégration AgriWeb</h1>
        <p>Impossible d'importer le module AgriWeb source.</p>
        <p>Vérifiez que le fichier agriweb_source.py est présent.</p>
        <a href="/search_interface">← Retour</a>
        """

# ===== ROUTES PROXY POUR AGRIWEB SOURCE =====

def create_agriweb_proxy_route(route_path, methods=['GET', 'POST']):
    """Crée une route proxy vers AgriWeb source avec authentification"""
    def proxy_view():
        if not session.get('user_id'):
            return redirect('/login')
        
        agriweb_module = import_agriweb_source()
        if not agriweb_module or not hasattr(agriweb_module, 'app'):
            return f"❌ AgriWeb source non disponible pour la route {route_path}"
        
        try:
            source_app = agriweb_module.app
            
            # Chercher la route correspondante
            for rule in source_app.url_map.iter_rules():
                if rule.rule == route_path and any(method in rule.methods for method in methods):
                    view_func = source_app.view_functions.get(rule.endpoint)
                    if view_func:
                        with source_app.app_context():
                            return view_func()
            
            return f"❌ Route {route_path} non trouvée dans AgriWeb source"
            
        except Exception as e:
            return f"❌ Erreur exécution route {route_path}: {e}"
    
    proxy_view.__name__ = f"proxy_{route_path.replace('/', '_')}"
    return proxy_view

# Ajouter des routes proxy principales
@app.route('/carte')
@login_required
def carte():
    """Route proxy pour la carte"""
    return create_agriweb_proxy_route('/carte')()

@app.route('/recherche')
@login_required
def recherche():
    """Route proxy pour la recherche"""
    return create_agriweb_proxy_route('/recherche')()

@app.route('/rapports')
@login_required
def rapports():
    """Route proxy pour les rapports"""
    return create_agriweb_proxy_route('/rapports')()

# ===== GESTION D'ERREURS =====

@app.errorhandler(404)
def not_found(error):
    return """
    <h1>🔍 Page non trouvée</h1>
    <p>La page demandée n'existe pas.</p>
    <a href="/">← Retour à l'accueil</a>
    """, 404

@app.errorhandler(500)
def internal_error(error):
    return f"""
    <h1>❌ Erreur interne</h1>
    <p>Une erreur s'est produite: {error}</p>
    <a href="/">← Retour à l'accueil</a>
    """, 500

# ===== POINT D'ENTRÉE =====

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Démarrage AgriWeb 2.0 Production Complète")
    print(f"📍 Port: {port}")
    print(f"🐛 Debug: {debug}")
    print(f"🔧 Plateforme: {get_platform_name()}")
    
    # Test d'import au démarrage
    agriweb_module = import_agriweb_source()
    if agriweb_module:
        print("✅ Module AgriWeb source importé avec succès")
    else:
        print("⚠️ Module AgriWeb source non disponible - mode dégradé")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
