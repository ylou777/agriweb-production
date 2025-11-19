#!/usr/bin/env python3
"""
🚀 INTÉGRATION PRODUCTION - Adaptateur pour votre application existante
Intègre le système de licences avec votre application AgriWeb existante
"""

import os
import sys
from functools import wraps
from flask import request, jsonify, session
from datetime import datetime
import logging

# Import du système de production
from production_system import LicenseManager, GeoServerAdapter, require_license

# Import de votre application existante
try:
    from agriweb_source import app as existing_app
    EXISTING_APP_AVAILABLE = True
except ImportError:
    print("⚠️  Application agriweb_source non trouvée. Mode développement.")
    EXISTING_APP_AVAILABLE = False

class ProductionIntegrator:
    """Intègre le système de production avec votre application existante"""
    
    def __init__(self, app=None):
        self.app = app
        self.license_manager = LicenseManager()
        
    def init_app(self, app):
        """Initialise l'intégration avec l'application Flask"""
        self.app = app
        
        # Ajouter les nouvelles routes de production
        self.register_production_routes()
        
        # Protéger les routes existantes
        self.protect_existing_routes()
        
    def register_production_routes(self):
        """Enregistre les nouvelles routes de production"""
        
        @self.app.route('/production/status')
        def production_status():
            """Status du système de production"""
            return jsonify({
                "status": "active",
                "version": "2.0.0",
                "features": ["trial_system", "license_management", "geoserver_adaptation"]
            })
        
        @self.app.route('/api/trial/start', methods=['POST'])
        def start_trial():
            """Démarre un essai gratuit et redirige vers l'application"""
            data = request.get_json()
            email = data.get('email')
            company = data.get('company', '')
            
            if not email:
                return jsonify({"error": "Email requis"}), 400
            
            # Créer la licence d'essai
            result = self.license_manager.create_trial_license(email, company)
            
            if result["success"]:
                # Stocker la licence en session
                session['license_key'] = result["license_key"]
                session['trial_user'] = True
                
                # Configuration GeoServer pour l'essai
                trial_config = self.get_trial_geoserver_config()
                
                return jsonify({
                    "success": True,
                    "license_key": result["license_key"],
                    "redirect_url": "/",  # Redirection vers votre app existante
                    "geoserver_config": trial_config,
                    "message": "Essai gratuit activé ! Vous pouvez maintenant utiliser AgriWeb."
                })
            else:
                return jsonify({"error": result["message"]}), 400
    
    def get_trial_geoserver_config(self):
        """Configuration GeoServer limitée pour l'essai"""
        return {
            "GEOSERVER_URL": "http://localhost:8080/geoserver",  # Votre GeoServer
            "RATE_LIMIT": 30,  # 30 requêtes/minute pour l'essai
            "ALLOWED_LAYERS": [
                "gpu:prefixes_sections",
                "gpu:poste_elec_shapefile", 
                "gpu:PARCELLE2024",
                "gpu:PARCELLES_GRAPHIQUES"
            ],
            "MAX_COMMUNES_PER_SEARCH": 5,  # Limité pour l'essai
            "TRIAL_MODE": True
        }
    
    def protect_existing_routes(self):
        """Ajoute la protection par licence aux routes existantes importantes"""
        
        # Liste des routes à protéger (adapez selon vos routes)
        protected_endpoints = [
            'rapport_departement',
            'search_commune',
            'generate_report',
            'export_data'
        ]
        
        # Ajouter le middleware de protection
        @self.app.before_request
        def check_license_before_request():
            """Vérifie la licence avant chaque requête protégée"""
            
            # Ignorer certaines routes (statiques, API publique, etc.)
            if request.endpoint in ['static', 'production_status', 'start_trial', None]:
                return
            
            # Routes publiques (page d'accueil, inscription essai)
            public_routes = ['index', 'landing_page', 'api.trial.start']
            if request.endpoint in public_routes:
                return
            
            # Vérifier si l'utilisateur a une licence valide
            license_key = session.get('license_key') or request.headers.get('X-License-Key')
            
            if not license_key:
                # Rediriger vers la page d'inscription essai
                if request.is_json:
                    return jsonify({
                        "error": "Licence requise",
                        "trial_available": True,
                        "trial_url": "/trial/register"
                    }), 401
                else:
                    # Redirection HTML vers landing page
                    from flask import redirect, url_for
                    return redirect(url_for('landing_page'))
            
            # Valider la licence
            validation = self.license_manager.validate_license(license_key)
            
            if not validation["valid"]:
                session.pop('license_key', None)
                if request.is_json:
                    return jsonify({
                        "error": validation["message"],
                        "trial_available": True
                    }), 401
                else:
                    from flask import redirect, url_for
                    return redirect(url_for('landing_page'))
            
            # Stocker les infos de licence pour la requête
            request.license_info = validation
            
            # Adapter la configuration GeoServer selon la licence
            self.adapt_geoserver_config(validation)
    
    def adapt_geoserver_config(self, license_info):
        """Adapte la configuration GeoServer selon le type de licence"""
        
        # Configuration selon le type de licence
        if license_info["license_type"] == "trial":
            config = self.get_trial_geoserver_config()
        elif license_info["license_type"] == "basic":
            config = {
                "GEOSERVER_URL": "http://localhost:8080/geoserver",
                "RATE_LIMIT": 100,
                "ALLOWED_LAYERS": "all_basic",
                "MAX_COMMUNES_PER_SEARCH": 20,
                "TRIAL_MODE": False
            }
        else:  # professional, enterprise
            config = {
                "GEOSERVER_URL": "http://localhost:8080/geoserver",
                "RATE_LIMIT": -1,  # Illimité
                "ALLOWED_LAYERS": "all",
                "MAX_COMMUNES_PER_SEARCH": -1,  # Illimité
                "TRIAL_MODE": False
            }
        
        # Injecter la config dans l'application (vous devrez adapter selon votre code)
        self.app.config.update(config)

def create_landing_page_route(app):
    """Crée la page d'accueil avec inscription essai"""
    
    @app.route('/trial/register')
    @app.route('/landing')
    def landing_page():
        """Page d'inscription pour l'essai gratuit"""
        return '''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AgriWeb 2.0 - Essai Gratuit</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; min-height: 100vh; display: flex; align-items: center; }
                .trial-card { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 2rem; }
            </style>
        </head>
        <body>
            <div class="hero">
                <div class="container">
                    <div class="row justify-content-center">
                        <div class="col-md-6">
                            <div class="trial-card text-dark">
                                <h1 class="text-center mb-4">🚀 AgriWeb 2.0</h1>
                                <h3 class="text-center mb-4">Essai gratuit 7 jours</h3>
                                <p class="text-center">Découvrez la solution professionnelle d'analyse agricole et foncière</p>
                                
                                <form id="trialForm" class="mt-4">
                                    <div class="mb-3">
                                        <label for="email" class="form-label">Email professionnel</label>
                                        <input type="email" class="form-control" id="email" required>
                                    </div>
                                    <div class="mb-3">
                                        <label for="company" class="form-label">Entreprise (optionnel)</label>
                                        <input type="text" class="form-control" id="company">
                                    </div>
                                    <button type="submit" class="btn btn-primary btn-lg w-100">
                                        Démarrer l'essai gratuit
                                    </button>
                                </form>
                                
                                <div class="mt-4 text-center">
                                    <small>✅ Aucune carte bancaire requise<br>
                                    ✅ Accès immédiat à toutes les fonctionnalités<br>
                                    ✅ Support technique inclus</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                document.getElementById('trialForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    
                    const submitBtn = e.target.querySelector('button[type="submit"]');
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Activation en cours...';
                    
                    const email = document.getElementById('email').value;
                    const company = document.getElementById('company').value;
                    
                    try {
                        const response = await fetch('/api/trial/start', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ email, company })
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            alert('🎉 Essai gratuit activé !\\n\\nVous allez être redirigé vers l\\'application.');
                            window.location.href = result.redirect_url;
                        } else {
                            alert(`Erreur : ${result.error}`);
                            submitBtn.disabled = false;
                            submitBtn.textContent = 'Démarrer l\\'essai gratuit';
                        }
                    } catch (error) {
                        alert('Erreur de connexion. Veuillez réessayer.');
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Démarrer l\\'essai gratuit';
                    }
                });
            </script>
        </body>
        </html>
        '''

def integrate_production_system():
    """Intègre le système de production avec votre application existante"""
    
    if EXISTING_APP_AVAILABLE:
        print("🔗 Intégration avec l'application existante...")
        
        # Initialiser l'intégrateur
        integrator = ProductionIntegrator()
        integrator.init_app(existing_app)
        
        # Ajouter la page d'accueil
        create_landing_page_route(existing_app)
        
        print("✅ Intégration terminée !")
        return existing_app
    
    else:
        print("⚠️  Application existante non trouvée. Création d'une app de démonstration...")
        from flask import Flask
        demo_app = Flask(__name__)
        demo_app.secret_key = "demo-secret-key"
        
        integrator = ProductionIntegrator()
        integrator.init_app(demo_app)
        create_landing_page_route(demo_app)
        
        @demo_app.route('/')
        def demo_home():
            license_info = getattr(request, 'license_info', None)
            if license_info:
                return f'''
                <h1>🎉 AgriWeb 2.0 - Mode Démo</h1>
                <p>Licence active: {license_info["license_type"]}</p>
                <p>Expire le: {license_info["expires_at"]}</p>
                <p>Cette page remplace temporairement votre application principale.</p>
                <a href="/production/status">Status système</a>
                '''
            else:
                return '<h1>Redirection vers essai...</h1><script>window.location="/landing"</script>'
        
        return demo_app

if __name__ == "__main__":
    print("🚀 Lancement du système AgriWeb 2.0 avec licences...")
    
    app = integrate_production_system()
    
    # Configuration pour le développement
    app.config['DEBUG'] = True
    
    print("""
    🎉 Système prêt !
    
    URLs disponibles:
    - http://localhost:5000/landing - Page d'inscription essai
    - http://localhost:5000/ - Application principale (avec licence)
    - http://localhost:5000/production/status - Status du système
    
    Testez l'essai gratuit:
    1. Allez sur /landing
    2. Entrez votre email
    3. Cliquez sur 'Démarrer l'essai gratuit'
    4. Vous serez redirigé vers l'application avec une licence de 7 jours
    """)
    
    app.run(host="127.0.0.1", port=5000, debug=True)
