#!/usr/bin/env python3
"""
🚀 AGRIWEB 2.0 - SYSTÈME DE PRODUCTION COMMERCIAL
Version complète avec authentification, essais gratuits et licences payantes
"""

from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for, flash
import json
import os
import uuid
from datetime import datetime, timedelta
import hashlib
import secrets

# Configuration
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Base de données des utilisateurs
USERS_FILE = "production_users.json"
LICENSES_FILE = "production_licenses.json"

class UserManager:
    """Gestionnaire des utilisateurs et licences"""
    
    def __init__(self):
        self.users = self.load_users()
        self.licenses = self.load_licenses()
    
    def load_users(self):
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_users(self):
        try:
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            print(f"Erreur sauvegarde utilisateurs: {e}")
            return False
    
    def load_licenses(self):
        if os.path.exists(LICENSES_FILE):
            try:
                with open(LICENSES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_licenses(self):
        try:
            with open(LICENSES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.licenses, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            print(f"Erreur sauvegarde licences: {e}")
            return False
    
    def create_trial_user(self, email, name, company=""):
        """Créer un utilisateur avec essai gratuit - VERSION VALIDÉE ET TESTÉE"""
        
        print(f"📝 Tentative d'inscription: {email}")
        
        if email in self.users:
            # Utilisateur existe déjà - logique validée lors des tests
            existing_user = self.users[email]
            print(f"👤 Utilisateur existant trouvé: {email}")
            
            try:
                expires = datetime.fromisoformat(existing_user['expires'])
                print(f"📅 Expiration: {expires}")
                
                if datetime.now() < expires:
                    # Essai encore valide
                    print("✅ Essai encore actif")
                    return {
                        "success": False, 
                        "error": "Cet email est déjà utilisé", 
                        "action": "login",
                        "message": f"Vous avez déjà un essai actif jusqu'au {expires.strftime('%d/%m/%Y')}. Connectez-vous.",
                        "debug": "Essai actif détecté"
                    }
                else:
                    # Essai expiré
                    print("⚠️ Essai expiré")
                    return {
                        "success": False, 
                        "error": "Cet email est déjà utilisé", 
                        "action": "expired",
                        "message": "Votre essai gratuit a expiré. Contactez-nous pour une licence payante.",
                        "debug": "Essai expiré détecté"
                    }
            except Exception as e:
                print(f"❌ Erreur lors de la vérification: {e}")
                return {
                    "success": False, 
                    "error": "Erreur de données utilisateur",
                    "debug": str(e)
                }
        
        # Nouvel utilisateur - créer l'essai
        print(f"✅ Nouveau utilisateur: {email}")
        user_id = str(uuid.uuid4())
        license_key = self.generate_license_key()
        expires = datetime.now() + timedelta(days=7)
        
        user_data = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "company": company,
            "license_type": "trial",
            "license_key": license_key,
            "created": datetime.now().isoformat(),
            "expires": expires.isoformat(),
            "active": True,
            "searches_used": 0,
            "searches_limit": 100,  # Limite pour l'essai
            "last_login": None
        }
        
        # Ajouter aux bases de données
        self.users[email] = user_data
        self.licenses[license_key] = {
            "user_email": email,
            "type": "trial",
            "expires": expires.isoformat(),
            "active": True
        }
        
        # Sauvegarder
        if self.save_users() and self.save_licenses():
            return {
                "success": True,
                "message": f"Essai gratuit activé pour {name}",
                "user": user_data,
                "license_key": license_key
            }
        else:
            return {"success": False, "error": "Erreur de sauvegarde"}
    
    def authenticate_user(self, email):
        """Authentifier un utilisateur existant - VERSION VALIDÉE ET TESTÉE"""
        
        print(f"🔑 Tentative de connexion: {email}")
        
        if email not in self.users:
            print(f"❌ Email non trouvé: {email}")
            return {
                "success": False, 
                "error": "Email non trouvé",
                "debug": f"Email {email} pas dans la base de données"
            }
        
        user = self.users[email]
        
        # Vérifier si non expiré
        try:
            expires = datetime.fromisoformat(user['expires'])
            if datetime.now() > expires:
                print(f"⚠️ Compte expiré: {expires}")
                return {
                    "success": False, 
                    "error": f"Votre accès a expiré le {expires.strftime('%d/%m/%Y')}. Contactez-nous pour renouveler.",
                    "debug": "Compte expiré"
                }
        except Exception as e:
            print(f"❌ Erreur lors de la vérification de date: {e}")
            return {
                "success": False, 
                "error": "Erreur de données utilisateur",
                "debug": str(e)
            }
        
        # Mettre à jour la dernière connexion
        user['last_login'] = datetime.now().isoformat()
        self.users[email] = user
        self.save_users()
        
        print(f"✅ Connexion réussie: {email}")
        return {
            "success": True,
            "message": f"Connexion réussie ! Bienvenue {user['name']}",
            "user": user,
            "debug": "Connexion validée avec succès"
        }
    
    def generate_license_key(self):
        """Générer une clé de licence unique"""
        return f"AW2-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
    
    def validate_license(self, license_key):
        """Valider une clé de licence"""
        
        if license_key not in self.licenses:
            return {"valid": False, "error": "Clé de licence invalide"}
        
        license_data = self.licenses[license_key]
        
        if not license_data['active']:
            return {"valid": False, "error": "Licence désactivée"}
        
        expires = datetime.fromisoformat(license_data['expires'])
        if datetime.now() > expires:
            return {"valid": False, "error": "Licence expirée"}
        
        return {
            "valid": True,
            "license": license_data,
            "user": self.users.get(license_data['user_email'])
        }

# Initialiser le gestionnaire
user_manager = UserManager()
print(f"🚀 Gestionnaire d'utilisateurs initialisé")
print(f"👥 {len(user_manager.users)} utilisateurs chargés")
for email in user_manager.users.keys():
    user = user_manager.users[email]
    expires = user.get('expires', 'N/A')
    print(f"  📧 {email} - Expire: {expires}")
print("=" * 60)

# ROUTES DE PRODUCTION

@app.route('/')
def landing_page():
    """Page d'accueil commerciale"""
    return render_template_string(LANDING_PAGE_TEMPLATE)

@app.route('/login')
def login_page():
    """Page de connexion"""
    return render_template_string(LOGIN_PAGE_TEMPLATE)

@app.route('/api/trial/register', methods=['POST'])
def register_trial():
    """Inscription pour essai gratuit"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        name = data.get('name', '').strip()
        company = data.get('company', '').strip()
        
        if not email or not name:
            return jsonify({"success": False, "error": "Email et nom requis"}), 400
        
        result = user_manager.create_trial_user(email, name, company)
        
        if result["success"]:
            # Connecter automatiquement l'utilisateur
            session['authenticated'] = True
            session['user_email'] = email
            session['user_data'] = result["user"]
            session['license_key'] = result["license_key"]
            
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Erreur inscription: {e}")
        return jsonify({"success": False, "error": "Erreur serveur"}), 500

@app.route('/api/user/login', methods=['POST'])
def login_existing_user():
    """Connexion d'un utilisateur existant"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({"success": False, "error": "Email requis"}), 400
        
        result = user_manager.authenticate_user(email)
        
        if result["success"]:
            # Connecter l'utilisateur
            session['authenticated'] = True
            session['user_email'] = email
            session['user_data'] = result["user"]
            session['license_key'] = result["user"]["license_key"]
            
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Erreur connexion: {e}")
        return jsonify({"success": False, "error": "Erreur serveur"}), 500

@app.route('/api/auth/login', methods=['POST'])
def login_user():
    """Connexion utilisateur existant"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({"success": False, "error": "Email requis"}), 400
        
        result = user_manager.authenticate_user(email)
        
        if result["success"]:
            # Connecter l'utilisateur
            session['authenticated'] = True
            session['user_email'] = email
            session['user_data'] = result["user"]
            session['license_key'] = result["user"]["license_key"]
            
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout_user():
    """Déconnexion"""
    session.clear()
    return jsonify({"success": True, "message": "Déconnexion réussie"})

@app.route('/api/auth/status')
def auth_status():
    """Vérifier le statut d'authentification"""
    if session.get('authenticated'):
        user_data = session.get('user_data', {})
        return jsonify({
            "authenticated": True,
            "user": {
                "name": user_data.get('name'),
                "email": user_data.get('email'),
                "company": user_data.get('company'),
                "license_type": user_data.get('license_type'),
                "expires": user_data.get('expires'),
                "searches_used": user_data.get('searches_used', 0),
                "searches_limit": user_data.get('searches_limit', 0)
            }
        })
    else:
        return jsonify({"authenticated": False})

@app.route('/app')
def app_interface():
    """Interface principale de l'application (protégée)"""
    if not session.get('authenticated'):
        return redirect('/login')
    
    # Importer et intégrer l'application AgriWeb
    try:
        from agriweb_source import app as agriweb_app
        
        # Créer une interface intégrée
        user_data = session.get('user_data', {})
        
        return render_template_string(APP_INTERFACE_TEMPLATE, user=user_data)
    except Exception as e:
        return f"Erreur de chargement de l'application: {e}"

@app.route('/admin')
def admin_panel():
    """Panneau d'administration"""
    return render_template_string(ADMIN_TEMPLATE, 
                                users=user_manager.users, 
                                licenses=user_manager.licenses)

# TEMPLATES HTML

LANDING_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgriWeb 2.0 - Géolocalisation Agricole Professionnelle</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        .hero { background: linear-gradient(135deg, #2c5f41 0%, #4a8b3b 100%); color: white; padding: 100px 0; }
        .feature-card { transition: transform 0.3s; }
        .feature-card:hover { transform: translateY(-5px); }
        .price-card { border: 2px solid #e9ecef; transition: all 0.3s; }
        .price-card.featured { border-color: #28a745; transform: scale(1.05); }
        .price-card:hover { box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark" style="background: #2c5f41;">
        <div class="container">
            <a class="navbar-brand fw-bold" href="#">🌾 AgriWeb 2.0</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/login">Connexion</a>
                <a class="nav-link" href="#pricing">Tarifs</a>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero text-center">
        <div class="container">
            <h1 class="display-4 fw-bold mb-4">AgriWeb 2.0</h1>
            <p class="lead mb-5">La solution professionnelle de géolocalisation agricole et foncière</p>
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card bg-light text-dark">
                        <div class="card-body">
                            <h4><i class="bi bi-gift"></i> Essai Gratuit 7 Jours</h4>
                            <p>Testez toutes les fonctionnalités sans engagement</p>
                            <button class="btn btn-success btn-lg" onclick="showTrialForm()">
                                Démarrer l'Essai Gratuit
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Features Section -->
    <section class="py-5">
        <div class="container">
            <h2 class="text-center mb-5">Fonctionnalités Avancées</h2>
            <div class="row">
                <div class="col-md-4 mb-4">
                    <div class="card feature-card h-100">
                        <div class="card-body text-center">
                            <i class="bi bi-geo-alt-fill text-success" style="font-size: 3rem;"></i>
                            <h5 class="mt-3">Géolocalisation Précise</h5>
                            <p>Analyses foncières et agricoles avec précision GPS</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="card feature-card h-100">
                        <div class="card-body text-center">
                            <i class="bi bi-bar-chart-fill text-success" style="font-size: 3rem;"></i>
                            <h5 class="mt-3">Rapports Détaillés</h5>
                            <p>Génération automatique de rapports professionnels</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="card feature-card h-100">
                        <div class="card-body text-center">
                            <i class="bi bi-map-fill text-success" style="font-size: 3rem;"></i>
                            <h5 class="mt-3">Cartes Interactives</h5>
                            <p>Visualisation avancée avec données en temps réel</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Pricing Section -->
    <section id="pricing" class="py-5 bg-light">
        <div class="container">
            <h2 class="text-center mb-5">Nos Formules</h2>
            <div class="row">
                <div class="col-md-4 mb-4">
                    <div class="card price-card h-100">
                        <div class="card-body text-center">
                            <h5>Essai Gratuit</h5>
                            <div class="h2 text-success">0€</div>
                            <p class="text-muted">7 jours</p>
                            <ul class="list-unstyled">
                                <li>✅ Toutes les fonctionnalités</li>
                                <li>✅ 100 recherches</li>
                                <li>✅ Support email</li>
                            </ul>
                            <button class="btn btn-outline-success" onclick="showTrialForm()">
                                Commencer
                            </button>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="card price-card featured h-100">
                        <div class="card-body text-center">
                            <h5>Professionnel</h5>
                            <div class="h2 text-success">299€</div>
                            <p class="text-muted">par mois</p>
                            <ul class="list-unstyled">
                                <li>✅ Fonctionnalités complètes</li>
                                <li>✅ Recherches illimitées</li>
                                <li>✅ Support prioritaire</li>
                                <li>✅ API access</li>
                            </ul>
                            <button class="btn btn-success">Choisir</button>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="card price-card h-100">
                        <div class="card-body text-center">
                            <h5>Entreprise</h5>
                            <div class="h2 text-success">999€</div>
                            <p class="text-muted">par mois</p>
                            <ul class="list-unstyled">
                                <li>✅ Tout inclus</li>
                                <li>✅ Utilisateurs multiples</li>
                                <li>✅ Support dédié</li>
                                <li>✅ Personnalisation</li>
                            </ul>
                            <button class="btn btn-success">Contacter</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Modal d'inscription -->
    <div class="modal fade" id="trialModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">🎉 Essai Gratuit 7 Jours</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div id="trial-alert"></div>
                    <form id="trialForm">
                        <div class="mb-3">
                            <label class="form-label">Nom complet</label>
                            <input type="text" class="form-control" id="trial-name" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Email professionnel</label>
                            <input type="email" class="form-control" id="trial-email" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Entreprise</label>
                            <input type="text" class="form-control" id="trial-company">
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                    <button type="button" class="btn btn-success" onclick="submitTrial()">
                        Activer l'Essai Gratuit
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function showTrialForm() {
            new bootstrap.Modal(document.getElementById('trialModal')).show();
        }
        
        async function submitTrial() {
            const name = document.getElementById('trial-name').value.trim();
            const email = document.getElementById('trial-email').value.trim();
            const company = document.getElementById('trial-company').value.trim();
            
            if (!name || !email) {
                showAlert('Nom et email requis', 'danger');
                return;
            }
            
            try {
                const response = await fetch('/api/trial/register', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name: name, email: email, company: company})
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert(result.message, 'success');
                    setTimeout(() => {
                        window.location.href = '/app';
                    }, 2000);
                } else {
                    // Gestion spéciale pour les utilisateurs existants
                    if (result.action === 'login') {
                        showAlert(result.message, 'warning');
                        // Montrer le bouton de connexion
                        document.getElementById('trial-alert').innerHTML += 
                            `<div class="mt-3">
                                <button class="btn btn-primary" onclick="loginExistingUser('${email}')">
                                    🔑 Se connecter avec cet email
                                </button>
                            </div>`;
                    } else if (result.action === 'expired') {
                        showAlert(result.message, 'info');
                        document.getElementById('trial-alert').innerHTML += 
                            `<div class="mt-3">
                                <button class="btn btn-success" onclick="contactUs()">
                                    💰 Obtenir une licence payante
                                </button>
                            </div>`;
                    } else {
                        showAlert(result.error, 'danger');
                    }
                }
            } catch (error) {
                showAlert('Erreur: ' + error.message, 'danger');
            }
        }
        
        async function loginExistingUser(email) {
            try {
                const response = await fetch('/api/user/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: email})
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert(result.message, 'success');
                    setTimeout(() => {
                        window.location.href = '/app';
                    }, 2000);
                } else {
                    showAlert(result.error, 'danger');
                }
            } catch (error) {
                showAlert('Erreur de connexion: ' + error.message, 'danger');
            }
        }
        
        function contactUs() {
            showAlert('📧 Contactez-nous: contact@agriweb.fr ou 📞 01.23.45.67.89', 'info');
        }
        
        function showAlert(message, type) {
            document.getElementById('trial-alert').innerHTML = 
                `<div class="alert alert-${type}">${message}</div>`;
        }
    </script>
</body>
</html>
'''

LOGIN_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgriWeb 2.0 - Connexion</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .login-container { max-width: 400px; margin: 100px auto; }
        .card { box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="card">
            <div class="card-body p-5">
                <div class="text-center mb-4">
                    <h2>🌾 AgriWeb 2.0</h2>
                    <p class="text-muted">Connexion à votre compte</p>
                </div>
                
                <div id="alert-zone"></div>
                
                <form id="loginForm">
                    <div class="mb-3">
                        <label class="form-label">Adresse email</label>
                        <input type="email" class="form-control" id="login-email" required>
                    </div>
                    <button type="submit" class="btn btn-success w-100 mb-3">Se Connecter</button>
                </form>
                
                <div class="text-center">
                    <p>Pas encore de compte ?</p>
                    <a href="/" class="btn btn-outline-success">Essai Gratuit 7 Jours</a>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const email = document.getElementById('login-email').value.trim();
            
            if (!email) {
                showAlert('Email requis', 'danger');
                return;
            }
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: email})
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert(result.message, 'success');
                    setTimeout(() => {
                        window.location.href = '/app';
                    }, 1500);
                } else {
                    showAlert(result.error, 'danger');
                }
            } catch (error) {
                showAlert('Erreur de connexion: ' + error.message, 'danger');
            }
        });
        
        function showAlert(message, type) {
            document.getElementById('alert-zone').innerHTML = 
                `<div class="alert alert-${type}">${message}</div>`;
        }
    </script>
</body>
</html>
'''

APP_INTERFACE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgriWeb 2.0 - Interface Principale</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .user-info { background: #d4edda; }
        .app-frame { height: 80vh; border: none; width: 100%; }
    </style>
</head>
<body>
    <!-- Barre utilisateur -->
    <div class="user-info p-3">
        <div class="container d-flex justify-content-between align-items-center">
            <div>
                <strong>✅ {{ user.name }}</strong> ({{ user.email }})
                <span class="badge bg-success">{{ user.license_type }}</span>
                <small>Expire le: {{ user.expires[:10] }}</small>
            </div>
            <div>
                <span class="me-3">{{ user.searches_used }}/{{ user.searches_limit }} recherches</span>
                <button class="btn btn-sm btn-outline-secondary" onclick="logout()">Déconnexion</button>
            </div>
        </div>
    </div>
    
    <!-- Interface AgriWeb intégrée -->
    <div class="container-fluid">
        <div class="alert alert-info">
            <h4>🚀 Bienvenue dans AgriWeb 2.0 !</h4>
            <p>Votre essai gratuit est actif. Accédez à toutes les fonctionnalités de géolocalisation agricole.</p>
            <a href="http://localhost:5001" target="_blank" class="btn btn-primary">
                Ouvrir l'Application AgriWeb
            </a>
        </div>
        
        <!-- Iframe vers l'application AgriWeb -->
        <iframe src="http://localhost:5001" class="app-frame"></iframe>
    </div>

    <script>
        async function logout() {
            try {
                await fetch('/api/auth/logout', {method: 'POST'});
                window.location.href = '/';
            } catch (error) {
                console.error('Erreur déconnexion:', error);
            }
        }
    </script>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgriWeb 2.0 - Administration</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h1>📊 Administration AgriWeb 2.0</h1>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>👥 Utilisateurs ({{ users|length }})</h5>
                    </div>
                    <div class="card-body">
                        {% for email, user in users.items() %}
                        <div class="mb-2 p-2 border rounded">
                            <strong>{{ user.name }}</strong> ({{ email }})<br>
                            <small>{{ user.company }} - {{ user.license_type }} - Expire: {{ user.expires[:10] }}</small>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>🔑 Licences ({{ licenses|length }})</h5>
                    </div>
                    <div class="card-body">
                        {% for key, license in licenses.items() %}
                        <div class="mb-2 p-2 border rounded">
                            <code>{{ key }}</code><br>
                            <small>{{ license.user_email }} - {{ license.type }} - {{ license.expires[:10] }}</small>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

if __name__ == '__main__':
    print("🚀 AgriWeb 2.0 - Système de Production Commercial")
    print("=" * 60)
    print("🌐 Site commercial: http://localhost:5000")
    print("🔐 Connexion: http://localhost:5000/login")
    print("🎯 Interface app: http://localhost:5000/app")
    print("👥 Administration: http://localhost:5000/admin")
    print("=" * 60)
    print("✅ Système de production opérationnel")
    
    app.run(host='127.0.0.1', port=5000, debug=False)
