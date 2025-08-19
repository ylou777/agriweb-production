#!/usr/bin/env python3
"""
🚀 DÉPLOIEMENT COMPLET AGRIWEB 2.0
Script tout-en-un pour le passage en production avec essai gratuit
"""

import os
import sys
import subprocess
import sqlite3
from datetime import datetime
from flask import Flask
import yaml

# Imports des modules de production
from production_system import create_production_app, LicenseManager
from production_integration import integrate_production_system
from payment_system import create_payment_routes
from geoserver_production_setup import GeoServerDeploymentHelper

class AgriWebProductionDeployer:
    """Gestionnaire de déploiement complet pour AgriWeb 2.0"""
    
    def __init__(self):
        self.deployment_config = {
            "app_name": "AgriWeb 2.0",
            "version": "2.0.0",
            "deployment_date": datetime.now().isoformat(),
            "features": [
                "trial_system",
                "license_management", 
                "stripe_payments",
                "geoserver_adaptation",
                "department_reports",
                "interactive_maps"
            ]
        }
        
    def check_requirements(self):
        """Vérifie les prérequis pour le déploiement"""
        
        print("🔍 Vérification des prérequis...")
        
        requirements = {
            "Python >= 3.8": self.check_python_version(),
            "Flask installé": self.check_package("flask"),
            "Stripe installé": self.check_package("stripe"),
            "Psycopg2 installé": self.check_package("psycopg2-binary"),
            "Application existante": self.check_existing_app(),
            "Base de données SQLite": True  # SQLite est inclus avec Python
        }
        
        all_ok = True
        for req, status in requirements.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {req}")
            if not status:
                all_ok = False
        
        if not all_ok:
            print("\n❌ Certains prérequis ne sont pas satisfaits.")
            print("Installez les dépendances manquantes avec :")
            print("pip install flask stripe psycopg2-binary requests pyyaml")
            return False
        
        print("✅ Tous les prérequis sont satisfaits !")
        return True
    
    def check_python_version(self):
        """Vérifie la version de Python"""
        return sys.version_info >= (3, 8)
    
    def check_package(self, package_name):
        """Vérifie qu'un package Python est installé"""
        try:
            __import__(package_name.replace('-', '_'))
            return True
        except ImportError:
            return False
    
    def check_existing_app(self):
        """Vérifie si l'application AgriWeb existante est disponible"""
        try:
            from agriweb_source import app
            return True
        except ImportError:
            return False
    
    def setup_production_database(self):
        """Configure la base de données de production"""
        
        print("🗄️ Configuration de la base de données...")
        
        # Initialiser le gestionnaire de licences
        license_manager = LicenseManager()
        
        # Ajouter des colonnes manquantes pour Stripe
        conn = sqlite3.connect(license_manager.db_path)
        cursor = conn.cursor()
        
        # Vérifier et ajouter les colonnes Stripe si nécessaires
        cursor.execute("PRAGMA table_info(licenses)")
        columns = [column[1] for column in cursor.fetchall()]
        
        stripe_columns = [
            ("stripe_customer_id", "TEXT"),
            ("stripe_subscription_id", "TEXT"),
            ("is_paid", "BOOLEAN DEFAULT 0"),
            ("subscription_cancelled", "BOOLEAN DEFAULT 0"),
            ("cancelled_at", "TIMESTAMP"),
            ("deactivated_at", "TIMESTAMP")
        ]
        
        for col_name, col_type in stripe_columns:
            if col_name not in columns:
                cursor.execute(f"ALTER TABLE licenses ADD COLUMN {col_name} {col_type}")
                print(f"  ✅ Colonne {col_name} ajoutée")
        
        conn.commit()
        conn.close()
        
        print("✅ Base de données configurée !")
    
    def create_production_app(self):
        """Crée l'application Flask de production complète"""
        
        print("🏗️ Création de l'application de production...")
        
        # Intégrer avec l'application existante si possible
        try:
            app = integrate_production_system()
            print("  ✅ Intégration avec l'application existante")
        except Exception as e:
            print(f"  ⚠️ Erreur d'intégration : {e}")
            print("  📝 Création d'une application de démonstration")
            app = self.create_demo_app()
        
        # Ajouter les routes de paiement
        create_payment_routes(app)
        print("  ✅ Routes de paiement ajoutées")
        
        # Configuration de production
        app.config.update({
            'ENV': 'production',
            'DEBUG': False,
            'TESTING': False,
            'SECRET_KEY': os.environ.get('SECRET_KEY', 'change-this-in-production'),
            'SQLALCHEMY_TRACK_MODIFICATIONS': False
        })
        
        return app
    
    def create_demo_app(self):
        """Crée une application de démonstration si l'app principale n'est pas disponible"""
        
        app = Flask(__name__)
        app.secret_key = "demo-secret-change-in-production"
        
        from production_integration import ProductionIntegrator, create_landing_page_route
        
        integrator = ProductionIntegrator()
        integrator.init_app(app)
        create_landing_page_route(app)
        
        @app.route('/')
        def demo_home():
            from flask import request
            license_info = getattr(request, 'license_info', None)
            
            if license_info:
                return f'''
                <div style="font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px;">
                    <h1>🎉 AgriWeb 2.0 - Mode Production</h1>
                    <div style="background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3>✅ Licence Active</h3>
                        <p><strong>Type :</strong> {license_info["license_type"].title()}</p>
                        <p><strong>Email :</strong> {license_info["email"]}</p>
                        <p><strong>Expire le :</strong> {license_info["expires_at"].strftime("%d/%m/%Y")}</p>
                    </div>
                    
                    <h3>🔧 Fonctionnalités disponibles :</h3>
                    <ul>
                        <li>✅ Système de licences opérationnel</li>
                        <li>✅ Essai gratuit 7 jours</li>
                        <li>✅ Paiements Stripe intégrés</li>
                        <li>✅ Protection par licence</li>
                        <li>⚠️ Application principale à connecter</li>
                    </ul>
                    
                    <div style="margin: 30px 0;">
                        <a href="/pricing" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                            📋 Voir les tarifs
                        </a>
                        <a href="/production/status" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">
                            📊 Status système
                        </a>
                    </div>
                    
                    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <strong>💡 Pour activer votre application AgriWeb complète :</strong><br>
                        1. Assurez-vous que agriweb_source.py est accessible<br>
                        2. Relancez le déploiement<br>
                        3. Votre application sera automatiquement protégée par licences
                    </div>
                </div>
                '''
            else:
                return '<script>window.location="/landing"</script>'
        
        return app
    
    def generate_deployment_files(self):
        """Génère les fichiers de configuration pour le déploiement"""
        
        print("📄 Génération des fichiers de déploiement...")
        
        # 1. Fichier requirements.txt
        requirements_content = '''Flask==2.3.3
stripe==6.0.0
psycopg2-binary==2.9.7
requests==2.31.0
PyYAML==6.0.1
python-dotenv==1.0.0
gunicorn==21.2.0
folium==0.14.0
geopandas==0.13.2
shapely==2.0.1
pyproj==3.6.0
'''
        
        with open("requirements_production.txt", "w") as f:
            f.write(requirements_content)
        
        # 2. Fichier de configuration environnement
        env_content = '''# Configuration de production AgriWeb 2.0
# IMPORTANT: Modifiez ces valeurs pour votre environnement

# Application
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this
DEBUG=False

# Base de données
DATABASE_URL=postgresql://user:password@localhost/agriweb_prod

# GeoServer
GEOSERVER_URL=http://localhost:8080/geoserver
GEOSERVER_USER=admin
GEOSERVER_PASSWORD=your-geoserver-password

# Stripe (mode production)
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email (pour notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@domain.com
SMTP_PASSWORD=your-email-password

# Domaine de production
DOMAIN=https://your-domain.com
'''
        
        with open(".env.production", "w") as f:
            f.write(env_content)
        
        # 3. Script de démarrage
        startup_script = '''#!/bin/bash
# Script de démarrage pour AgriWeb 2.0 en production

echo "🚀 Démarrage d'AgriWeb 2.0..."

# Chargement des variables d'environnement
source .env.production

# Démarrage avec Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --log-level info complete_production_deployment:app

echo "✅ AgriWeb 2.0 démarré sur le port 5000"
'''
        
        with open("start_production.sh", "w") as f:
            f.write(startup_script)
        
        # Rendre le script exécutable
        os.chmod("start_production.sh", 0o755)
        
        # 4. Configuration Docker (optionnel)
        dockerfile_content = '''FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers
COPY requirements_production.txt .
COPY . .

# Installation des dépendances Python
RUN pip install -r requirements_production.txt

# Port d'exposition
EXPOSE 5000

# Commande de démarrage
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "complete_production_deployment:app"]
'''
        
        with open("Dockerfile", "w") as f:
            f.write(dockerfile_content)
        
        print("  ✅ requirements_production.txt")
        print("  ✅ .env.production")
        print("  ✅ start_production.sh")
        print("  ✅ Dockerfile")
    
    def create_complete_app_file(self):
        """Crée le fichier principal d'application pour la production"""
        
        app_content = '''#!/usr/bin/env python3
"""
🚀 AGRIWEB 2.0 - APPLICATION DE PRODUCTION COMPLÈTE
Point d'entrée principal avec toutes les fonctionnalités
"""

import os
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv('.env.production')

# Import et configuration de l'application
from complete_production_deployment import AgriWebProductionDeployer

def create_app():
    """Factory pour créer l'application de production"""
    deployer = AgriWebProductionDeployer()
    
    # Vérifications et setup
    if not deployer.check_requirements():
        raise Exception("Prérequis non satisfaits")
    
    deployer.setup_production_database()
    app = deployer.create_production_app()
    
    return app

# Application principale
app = create_app()

if __name__ == "__main__":
    print("🚀 AgriWeb 2.0 - Mode Production")
    print("   Port: 5000")
    print("   URL: http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
'''
        
        with open("app_production.py", "w") as f:
            f.write(app_content)
        
        print("  ✅ app_production.py créé")
    
    def run_deployment(self):
        """Lance le déploiement complet"""
        
        print("🚀 DÉPLOIEMENT AGRIWEB 2.0 EN PRODUCTION")
        print("=" * 60)
        
        # 1. Vérifications
        if not self.check_requirements():
            return False
        
        # 2. Configuration base de données
        self.setup_production_database()
        
        # 3. Génération des fichiers
        self.generate_deployment_files()
        self.create_complete_app_file()
        
        # 4. Configuration GeoServer
        print("🌐 Configuration GeoServer...")
        geoserver_helper = GeoServerDeploymentHelper()
        geoserver_helper.setup_production_environment()
        
        # 5. Création de l'application
        app = self.create_production_app()
        
        # 6. Sauvegarde de la configuration
        self.save_deployment_config()
        
        print("\n🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !")
        print("=" * 60)
        
        self.display_deployment_summary()
        
        return app
    
    def save_deployment_config(self):
        """Sauvegarde la configuration de déploiement"""
        
        config_file = "deployment_config.yaml"
        
        with open(config_file, "w") as f:
            yaml.dump(self.deployment_config, f, default_flow_style=False)
        
        print(f"  ✅ Configuration sauvegardée : {config_file}")
    
    def display_deployment_summary(self):
        """Affiche le résumé du déploiement"""
        
        print("""
📋 RÉSUMÉ DU DÉPLOIEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 FONCTIONNALITÉS ACTIVES :
   ✅ Essai gratuit 7 jours automatique
   ✅ Gestion complète des licences (Basic, Pro, Enterprise)
   ✅ Paiements sécurisés avec Stripe
   ✅ Protection par licence de toutes les fonctionnalités
   ✅ Adaptation GeoServer selon le type de licence
   ✅ Interface de tarification professionnelle
   ✅ Système de renouvellement automatique

🔧 FICHIERS GÉNÉRÉS :
   📄 requirements_production.txt - Dépendances Python
   📄 .env.production - Variables d'environnement
   📄 app_production.py - Application principale
   📄 start_production.sh - Script de démarrage
   📄 Dockerfile - Configuration Docker
   📄 production_geoserver_config.yaml - Config GeoServer
   📄 DEPLOYMENT_GUIDE.md - Guide de déploiement complet

🌐 URLS IMPORTANTES :
   🏠 Page d'accueil : http://localhost:5000/
   🆓 Essai gratuit : http://localhost:5000/landing
   💳 Tarification : http://localhost:5000/pricing
   📊 Status système : http://localhost:5000/production/status
   🔧 API licences : http://localhost:5000/api/license/validate

💡 PROCHAINES ÉTAPES :

1. CONFIGURATION STRIPE :
   - Créez un compte Stripe (https://stripe.com)
   - Récupérez vos clés API (test puis production)
   - Configurez les webhooks pour les renouvellements
   - Modifiez .env.production avec vos vraies clés

2. GEOSERVER PRODUCTION :
   - Déployez GeoServer sur votre serveur
   - Importez vos données géographiques
   - Configurez les couches selon le guide
   - Adaptez l'URL dans production_geoserver_config.yaml

3. HÉBERGEMENT :
   - Choisissez un hébergeur (AWS, OVH, DigitalOcean...)
   - Configurez votre nom de domaine
   - Déployez avec Docker ou directement
   - Configurez HTTPS avec Let's Encrypt

4. TESTS :
   - Testez l'inscription essai gratuit
   - Vérifiez les paiements en mode test
   - Validez toutes les fonctionnalités avec licences
   - Effectuez des tests de charge

🚀 DÉMARRAGE RAPIDE :
   
   Mode développement :
   python complete_production_deployment.py
   
   Mode production :
   ./start_production.sh
   
   Avec Docker :
   docker build -t agriweb2.0 .
   docker run -p 5000:5000 agriweb2.0

💰 MODÈLE ÉCONOMIQUE ACTIVÉ :
   🆓 Essai : 7 jours gratuits, 10 communes max
   💼 Basic : 299€/an, 100 communes, 500 rapports/jour
   🚀 Pro : 999€/an, 1000 communes, API complète
   🏢 Enterprise : 2999€/an, illimité, GeoServer dédié

🎉 Votre système AgriWeb 2.0 est prêt pour la commercialisation !
   Consultez DEPLOYMENT_GUIDE.md pour les détails techniques.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

def main():
    """Point d'entrée principal du déploiement"""
    
    print("🚀 Initialisation du déploiement AgriWeb 2.0...")
    
    deployer = AgriWebProductionDeployer()
    app = deployer.run_deployment()
    
    if app:
        print("\n🎮 Lancement du serveur de production...")
        app.run(host="127.0.0.1", port=5000, debug=False)
    else:
        print("❌ Échec du déploiement")
        sys.exit(1)

# Point d'entrée pour Gunicorn
app = None

def get_app():
    """Fonction pour obtenir l'app (utilisée par Gunicorn)"""
    global app
    if app is None:
        deployer = AgriWebProductionDeployer()
        app = deployer.run_deployment()
    return app

# Pour l'import direct
app = get_app()

if __name__ == "__main__":
    main()
