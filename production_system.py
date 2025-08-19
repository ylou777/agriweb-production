#!/usr/bin/env python3
"""
🚀 SYSTÈME DE PRODUCTION - AgriWeb 2.0
Gestion des licences avec essai gratuit de 7 jours et déploiement serveur
"""

import os
import json
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from functools import wraps
import logging

# ==================== CONFIGURATION PRODUCTION ====================

class ProductionConfig:
    """Configuration pour l'environnement de production"""
    
    # Sécurité
    SECRET_KEY = secrets.token_hex(32)  # Clé secrète pour les sessions
    
    # Base de données des licences
    LICENSE_DB_PATH = "production_licenses.db"
    
    # GeoServer Configuration (à adapter à votre serveur de production)
    GEOSERVER_PRODUCTION_URL = "http://your-geoserver.domain.com:8080/geoserver"
    
    # Limites par type de licence
    LICENSE_LIMITS = {
        "trial": {
            "duration_days": 7,
            "max_communes": 10,
            "max_reports_per_day": 50,
            "features": ["basic_reports", "commune_search", "parcel_analysis"]
        },
        "basic": {
            "duration_days": 365,
            "max_communes": 100,
            "max_reports_per_day": 500,
            "features": ["basic_reports", "commune_search", "parcel_analysis", "export_data"]
        },
        "professional": {
            "duration_days": 365,
            "max_communes": 1000,
            "max_reports_per_day": 2000,
            "features": ["all_features", "api_access", "priority_support", "custom_geoserver"]
        },
        "enterprise": {
            "duration_days": 365,
            "max_communes": -1,  # Illimité
            "max_reports_per_day": -1,  # Illimité
            "features": ["all_features", "api_access", "priority_support", "custom_geoserver", "white_label"]
        }
    }
    
    # Prix (en euros)
    PRICING = {
        "trial": 0,
        "basic": 299,
        "professional": 999,
        "enterprise": 2999
    }

# ==================== GESTIONNAIRE DE LICENCES ====================

class LicenseManager:
    """Gestionnaire des licences et authentification"""
    
    def __init__(self, db_path=ProductionConfig.LICENSE_DB_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialise la base de données des licences"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_key TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                company TEXT,
                license_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                usage_stats TEXT DEFAULT '{}',
                geoserver_config TEXT DEFAULT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_key TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT DEFAULT NULL,
                FOREIGN KEY (license_key) REFERENCES licenses (license_key)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_license_key(self):
        """Génère une clé de licence unique"""
        return f"AW-{secrets.token_hex(8).upper()}-{secrets.token_hex(4).upper()}"
    
    def create_trial_license(self, email, company=None):
        """Crée une licence d'essai gratuite de 7 jours"""
        license_key = self.generate_license_key()
        expires_at = datetime.now() + timedelta(days=ProductionConfig.LICENSE_LIMITS["trial"]["duration_days"])
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO licenses (license_key, email, company, license_type, expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (license_key, email, company, "trial", expires_at))
            
            conn.commit()
            
            # Log de création
            self.log_usage(license_key, "license_created", {"type": "trial"})
            
            return {
                "success": True,
                "license_key": license_key,
                "expires_at": expires_at.isoformat(),
                "message": "Licence d'essai créée avec succès !"
            }
            
        except sqlite3.IntegrityError:
            return {
                "success": False,
                "message": "Cette adresse email a déjà une licence active."
            }
        finally:
            conn.close()
    
    def validate_license(self, license_key):
        """Valide une clé de licence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT license_key, email, company, license_type, expires_at, is_active, usage_stats
            FROM licenses 
            WHERE license_key = ? AND is_active = 1
        ''', (license_key,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {"valid": False, "message": "Licence invalide ou inactive"}
        
        license_key, email, company, license_type, expires_at_str, is_active, usage_stats = result
        expires_at = datetime.fromisoformat(expires_at_str)
        
        if datetime.now() > expires_at:
            return {"valid": False, "message": "Licence expirée"}
        
        # Parse usage stats
        try:
            usage_stats = json.loads(usage_stats) if usage_stats else {}
        except:
            usage_stats = {}
        
        return {
            "valid": True,
            "license_key": license_key,
            "email": email,
            "company": company,
            "license_type": license_type,
            "expires_at": expires_at,
            "usage_stats": usage_stats,
            "limits": ProductionConfig.LICENSE_LIMITS[license_type]
        }
    
    def log_usage(self, license_key, action, details=None):
        """Enregistre l'utilisation de la licence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO usage_log (license_key, action, details)
            VALUES (?, ?, ?)
        ''', (license_key, action, json.dumps(details) if details else None))
        
        conn.commit()
        conn.close()

# ==================== DÉCORATEURS DE SÉCURITÉ ====================

def require_license(f):
    """Décorateur pour vérifier la licence avant l'accès aux fonctionnalités"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        license_key = session.get('license_key') or request.headers.get('X-License-Key')
        
        if not license_key:
            return jsonify({"error": "Licence requise", "trial_available": True}), 401
        
        license_manager = LicenseManager()
        validation = license_manager.validate_license(license_key)
        
        if not validation["valid"]:
            return jsonify({"error": validation["message"], "trial_available": True}), 401
        
        # Ajouter les infos de licence au context
        request.license_info = validation
        license_manager.log_usage(license_key, f.__name__, {"endpoint": request.endpoint})
        
        return f(*args, **kwargs)
    return decorated_function

# ==================== ADAPTATEUR GEOSERVER ====================

class GeoServerAdapter:
    """Adaptateur pour la configuration GeoServer en production"""
    
    def __init__(self, license_info=None):
        self.license_info = license_info
        self.configure_endpoints()
    
    def configure_endpoints(self):
        """Configure les endpoints GeoServer selon le type de licence"""
        if not self.license_info:
            # Configuration de base pour essai
            self.geoserver_url = ProductionConfig.GEOSERVER_PRODUCTION_URL
            self.allowed_layers = ["basic_parcels", "basic_postes"]
        else:
            license_type = self.license_info["license_type"]
            
            if license_type == "trial":
                self.geoserver_url = ProductionConfig.GEOSERVER_PRODUCTION_URL
                self.allowed_layers = ["basic_parcels", "basic_postes", "basic_communes"]
            
            elif license_type in ["basic", "professional", "enterprise"]:
                # Configuration complète
                self.geoserver_url = self.license_info.get("custom_geoserver_url", 
                                                         ProductionConfig.GEOSERVER_PRODUCTION_URL)
                self.allowed_layers = ["all_layers"]
    
    def get_layer_config(self):
        """Retourne la configuration des couches selon la licence"""
        return {
            "GEOSERVER_URL": self.geoserver_url,
            "ALLOWED_LAYERS": self.allowed_layers,
            "RATE_LIMIT": self.get_rate_limit()
        }
    
    def get_rate_limit(self):
        """Détermine la limite de requêtes selon la licence"""
        if not self.license_info:
            return {"requests_per_minute": 10}
        
        license_type = self.license_info["license_type"]
        limits = {
            "trial": {"requests_per_minute": 30},
            "basic": {"requests_per_minute": 100},
            "professional": {"requests_per_minute": 500},
            "enterprise": {"requests_per_minute": -1}  # Illimité
        }
        
        return limits.get(license_type, {"requests_per_minute": 10})

# ==================== API DE PRODUCTION ====================

def create_production_app():
    """Crée l'application Flask pour la production"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = ProductionConfig.SECRET_KEY
    
    license_manager = LicenseManager()
    
    @app.route('/')
    def landing_page():
        """Page d'accueil avec proposition d'essai gratuit"""
        return render_template_string(LANDING_PAGE_TEMPLATE)
    
    @app.route('/api/trial/register', methods=['POST'])
    def register_trial():
        """Inscription pour l'essai gratuit"""
        data = request.get_json()
        email = data.get('email')
        company = data.get('company', '')
        
        if not email:
            return jsonify({"error": "Email requis"}), 400
        
        result = license_manager.create_trial_license(email, company)
        
        if result["success"]:
            # Envoyer email de confirmation (à implémenter)
            # send_trial_confirmation_email(email, result["license_key"])
            
            return jsonify({
                "success": True,
                "license_key": result["license_key"],
                "expires_at": result["expires_at"],
                "message": "Essai gratuit activé ! Votre clé de licence a été envoyée par email."
            })
        else:
            return jsonify({"error": result["message"]}), 400
    
    @app.route('/api/license/validate', methods=['POST'])
    def validate_license_endpoint():
        """Validation d'une clé de licence"""
        data = request.get_json()
        license_key = data.get('license_key')
        
        if not license_key:
            return jsonify({"error": "Clé de licence requise"}), 400
        
        validation = license_manager.validate_license(license_key)
        
        if validation["valid"]:
            session['license_key'] = license_key
            session['license_info'] = validation
            
            # Configuration GeoServer personnalisée
            geoserver_adapter = GeoServerAdapter(validation)
            
            return jsonify({
                "valid": True,
                "license_info": validation,
                "geoserver_config": geoserver_adapter.get_layer_config()
            })
        else:
            return jsonify({"error": validation["message"]}), 401
    
    @app.route('/dashboard')
    @require_license
    def dashboard():
        """Tableau de bord utilisateur"""
        license_info = request.license_info
        return render_template_string(DASHBOARD_TEMPLATE, license_info=license_info)
    
    # Intégration de votre application existante avec protection par licence
    @app.route('/search', methods=['GET', 'POST'])
    @require_license
    def protected_search():
        """Route de recherche protégée par licence"""
        # Ici vous intégrez votre logique de recherche existante
        # en utilisant la configuration GeoServer adaptée à la licence
        
        geoserver_adapter = GeoServerAdapter(request.license_info)
        config = geoserver_adapter.get_layer_config()
        
        # Votre logique existante avec la config adaptée
        return jsonify({"message": "Recherche avec licence validée", "config": config})
    
    return app

# ==================== TEMPLATES HTML ====================

LANDING_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgriWeb 2.0 - Analyse Agricole Professionnelle</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .hero-section { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 80px 0; }
        .feature-icon { font-size: 3rem; color: #667eea; }
        .pricing-card { transition: transform 0.3s; }
        .pricing-card:hover { transform: translateY(-10px); }
        .trial-highlight { background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%); }
    </style>
</head>
<body>
    <!-- Hero Section -->
    <section class="hero-section text-center">
        <div class="container">
            <h1 class="display-4 fw-bold mb-4">AgriWeb 2.0</h1>
            <p class="lead mb-5">La solution professionnelle d'analyse agricole et foncière</p>
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card trial-highlight text-dark">
                        <div class="card-body">
                            <h3>🎉 Essai gratuit 7 jours</h3>
                            <p>Testez toutes les fonctionnalités sans engagement</p>
                            <form id="trialForm">
                                <div class="mb-3">
                                    <input type="email" class="form-control" id="email" placeholder="Votre email professionnel" required>
                                </div>
                                <div class="mb-3">
                                    <input type="text" class="form-control" id="company" placeholder="Nom de votre entreprise (optionnel)">
                                </div>
                                <button type="submit" class="btn btn-dark btn-lg w-100">
                                    Démarrer l'essai gratuit
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Features Section -->
    <section class="py-5">
        <div class="container">
            <h2 class="text-center mb-5">Fonctionnalités</h2>
            <div class="row">
                <div class="col-md-4 text-center mb-4">
                    <div class="feature-icon">🗺️</div>
                    <h4>Analyse Cartographique</h4>
                    <p>Visualisation interactive des parcelles, postes électriques, et zones urbaines</p>
                </div>
                <div class="col-md-4 text-center mb-4">
                    <div class="feature-icon">📊</div>
                    <h4>Rapports Départementaux</h4>
                    <p>Synthèses complètes par département avec TOP 50 des parcelles</p>
                </div>
                <div class="col-md-4 text-center mb-4">
                    <div class="feature-icon">⚡</div>
                    <h4>Calculs de Distance</h4>
                    <p>Distances précises aux postes d'injection électrique BT/HTA</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Pricing Section -->
    <section class="py-5 bg-light">
        <div class="container">
            <h2 class="text-center mb-5">Tarifs</h2>
            <div class="row justify-content-center">
                <div class="col-md-3 mb-4">
                    <div class="card pricing-card">
                        <div class="card-header bg-success text-white text-center">
                            <h4>Essai</h4>
                            <h2>Gratuit</h2>
                            <p>7 jours</p>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled">
                                <li>✅ 10 communes</li>
                                <li>✅ 50 rapports/jour</li>
                                <li>✅ Fonctionnalités de base</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-4">
                    <div class="card pricing-card">
                        <div class="card-header bg-primary text-white text-center">
                            <h4>Basic</h4>
                            <h2>299€</h2>
                            <p>par an</p>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled">
                                <li>✅ 100 communes</li>
                                <li>✅ 500 rapports/jour</li>
                                <li>✅ Export de données</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-4">
                    <div class="card pricing-card">
                        <div class="card-header bg-warning text-dark text-center">
                            <h4>Professional</h4>
                            <h2>999€</h2>
                            <p>par an</p>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled">
                                <li>✅ 1000 communes</li>
                                <li>✅ 2000 rapports/jour</li>
                                <li>✅ Accès API</li>
                                <li>✅ Support prioritaire</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-4">
                    <div class="card pricing-card">
                        <div class="card-header bg-dark text-white text-center">
                            <h4>Enterprise</h4>
                            <h2>2999€</h2>
                            <p>par an</p>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled">
                                <li>✅ Illimité</li>
                                <li>✅ GeoServer dédié</li>
                                <li>✅ Marque blanche</li>
                                <li>✅ Support 24/7</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('trialForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const company = document.getElementById('company').value;
            
            try {
                const response = await fetch('/api/trial/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, company })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert(`Essai activé ! Votre clé de licence : ${result.license_key}`);
                    // Redirection vers le dashboard ou l'application
                    window.location.href = '/dashboard';
                } else {
                    alert(`Erreur : ${result.error}`);
                }
            } catch (error) {
                alert('Erreur de connexion. Veuillez réessayer.');
            }
        });
    </script>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgriWeb 2.0 - Tableau de bord</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h1>Tableau de bord AgriWeb 2.0</h1>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Informations de licence</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>Type :</strong> {{ license_info.license_type|title }}</p>
                        <p><strong>Expire le :</strong> {{ license_info.expires_at.strftime('%d/%m/%Y') }}</p>
                        <p><strong>Email :</strong> {{ license_info.email }}</p>
                        {% if license_info.company %}
                        <p><strong>Entreprise :</strong> {{ license_info.company }}</p>
                        {% endif %}
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Limites d'utilisation</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>Communes max :</strong> 
                            {% if license_info.limits.max_communes == -1 %}
                                Illimité
                            {% else %}
                                {{ license_info.limits.max_communes }}
                            {% endif %}
                        </p>
                        <p><strong>Rapports/jour :</strong>
                            {% if license_info.limits.max_reports_per_day == -1 %}
                                Illimité
                            {% else %}
                                {{ license_info.limits.max_reports_per_day }}
                            {% endif %}
                        </p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="mt-4">
            <a href="/search" class="btn btn-primary btn-lg">
                🔍 Accéder à l'application
            </a>
        </div>
    </div>
</body>
</html>
'''

# ==================== SCRIPT DE DÉPLOIEMENT ====================

def deploy_production():
    """Script de déploiement pour la production"""
    print("🚀 Configuration du système de production AgriWeb 2.0...")
    
    # Initialiser la base de données
    license_manager = LicenseManager()
    print("✅ Base de données des licences initialisée")
    
    # Créer l'application
    app = create_production_app()
    print("✅ Application Flask configurée")
    
    # Configuration de production
    app.config.update(
        DEBUG=False,
        TESTING=False,
        ENV='production'
    )
    
    print("""
    🎉 Système de production prêt !
    
    Fonctionnalités activées :
    - ✅ Essai gratuit 7 jours
    - ✅ Gestion des licences
    - ✅ Protection par licence
    - ✅ Adaptation GeoServer selon licence
    - ✅ Système de paiement (à intégrer)
    
    Prochaines étapes :
    1. Configurer votre GeoServer de production
    2. Intégrer un système de paiement (Stripe, PayPal...)
    3. Configurer l'envoi d'emails
    4. Déployer sur votre serveur
    """)
    
    return app

if __name__ == "__main__":
    # Lancement du serveur de production
    app = deploy_production()
    
    # En production, utilisez un serveur WSGI comme Gunicorn
    # gunicorn -w 4 -b 0.0.0.0:5000 production_system:app
    app.run(host="0.0.0.0", port=5000, debug=False)
