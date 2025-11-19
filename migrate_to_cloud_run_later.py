#!/usr/bin/env python3
"""
🔄 Migration Railway → Google Cloud Run
Quand vous serez prêt à économiser ~$30/mois
"""

import os
import subprocess
import json
from datetime import datetime

class MigrationManager:
    def __init__(self):
        self.backup_dir = f"backup_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def check_prerequisites(self):
        """Vérifier que tout est prêt pour la migration"""
        print("🔍 Vérification des prérequis...")
        
        # Vérifier Railway CLI
        try:
            subprocess.run(["railway", "--version"], check=True, capture_output=True)
            print("✅ Railway CLI OK")
        except:
            print("❌ Railway CLI manquant")
            return False
            
        # Vérifier Google Cloud CLI
        try:
            subprocess.run(["gcloud", "--version"], check=True, capture_output=True)
            print("✅ Google Cloud CLI OK")
        except:
            print("❌ Google Cloud CLI manquant - installer avec:")
            print("   curl https://sdk.cloud.google.com | bash")
            return False
            
        return True
    
    def backup_railway_data(self):
        """Sauvegarder les données GeoServer depuis Railway"""
        print("💾 Sauvegarde des données Railway...")
        
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Backup via Railway
        commands = [
            f"railway run --service geoserver -- tar -czf /tmp/geoserver_backup.tar.gz /opt/geoserver_data",
            f"railway run --service geoserver -- cat /tmp/geoserver_backup.tar.gz > {self.backup_dir}/geoserver_data.tar.gz"
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd.split(), check=True)
                print(f"✅ {cmd}")
            except Exception as e:
                print(f"❌ Échec: {cmd} - {e}")
                return False
        
        return True
    
    def setup_cloud_run(self):
        """Configurer Google Cloud Run"""
        print("☁️ Configuration Cloud Run...")
        
        # Créer le projet Cloud Run
        commands = [
            "gcloud config set project agriweb-geoserver",
            "gcloud services enable run.googleapis.com",
            "gcloud services enable storage.googleapis.com"
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd.split(), check=True)
                print(f"✅ {cmd}")
            except Exception as e:
                print(f"⚠️ {cmd} - {e}")
    
    def migrate_data_to_cloud_storage(self):
        """Migrer les données vers Cloud Storage"""
        print("📦 Migration vers Cloud Storage...")
        
        commands = [
            "gsutil mb gs://agriweb-geoserver-data",
            f"gsutil cp {self.backup_dir}/geoserver_data.tar.gz gs://agriweb-geoserver-data/",
            "gsutil iam ch allUsers:objectViewer gs://agriweb-geoserver-data"
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd.split(), check=True)
                print(f"✅ {cmd}")
            except Exception as e:
                print(f"❌ {cmd} - {e}")
                return False
        
        return True
    
    def deploy_to_cloud_run(self):
        """Déployer sur Cloud Run"""
        print("🚀 Déploiement Cloud Run...")
        
        # Créer Dockerfile Cloud Run
        dockerfile_content = '''
FROM kartoza/geoserver:2.24.0

ENV GEOSERVER_DATA_DIR=/geoserver_data
ENV JAVA_OPTS="-Xms512m -Xmx2048m -XX:+UseContainerSupport"

# Script de récupération des données
RUN echo '#!/bin/bash' > /start.sh && \\
    echo 'gsutil cp gs://agriweb-geoserver-data/geoserver_data.tar.gz /tmp/' >> /start.sh && \\
    echo 'tar -xzf /tmp/geoserver_data.tar.gz -C /' >> /start.sh && \\
    echo 'exec /scripts/docker-entrypoint.sh' >> /start.sh && \\
    chmod +x /start.sh

EXPOSE 8080
CMD ["/start.sh"]
'''
        
        with open('Dockerfile.cloudrun', 'w') as f:
            f.write(dockerfile_content)
        
        # Déployer
        deploy_cmd = [
            "gcloud", "run", "deploy", "agriweb-geoserver",
            "--source", ".",
            "--dockerfile", "Dockerfile.cloudrun",
            "--region", "europe-west1",
            "--memory", "4Gi",
            "--cpu", "2",
            "--max-instances", "10",
            "--port", "8080",
            "--allow-unauthenticated"
        ]
        
        try:
            result = subprocess.run(deploy_cmd, check=True, capture_output=True, text=True)
            print("✅ Déploiement Cloud Run réussi!")
            print(f"🌐 URL: {result.stdout}")
            return True
        except Exception as e:
            print(f"❌ Échec déploiement: {e}")
            return False
    
    def update_flask_config(self, cloud_run_url):
        """Mettre à jour la config Flask avec la nouvelle URL"""
        print("🔧 Mise à jour configuration Flask...")
        
        config_updates = f'''
# Nouvelle configuration Cloud Run
GEOSERVER_URL = "{cloud_run_url}"
GEOSERVER_USER = "admin"
GEOSERVER_PASSWORD = "admin123"
'''
        
        with open('config_cloud_run.py', 'w') as f:
            f.write(config_updates)
        
        print("✅ Configuration sauvée dans config_cloud_run.py")
    
    def run_migration(self):
        """Lancer la migration complète"""
        print("🚀 DÉBUT MIGRATION RAILWAY → CLOUD RUN")
        print("=" * 50)
        
        if not self.check_prerequisites():
            return False
        
        if not self.backup_railway_data():
            return False
        
        self.setup_cloud_run()
        
        if not self.migrate_data_to_cloud_storage():
            return False
        
        if not self.deploy_to_cloud_run():
            return False
        
        print("\n🎉 MIGRATION TERMINÉE!")
        print(f"💰 Économie: ~$30/mois")
        print(f"📁 Backup dans: {self.backup_dir}")
        print("\n📋 Prochaines étapes:")
        print("1. Tester le nouveau GeoServer")
        print("2. Mettre à jour votre application Flask")
        print("3. Arrêter Railway quand tout fonctionne")
        
        return True

if __name__ == "__main__":
    print("⚠️  ATTENTION: Ce script est préparé pour PLUS TARD")
    print("⚠️  Utilisez Railway maintenant pour démarrer rapidement")
    print("⚠️  Lancez cette migration dans 3-6 mois pour économiser")
    print("\nVoulez-vous voir les étapes? (y/n)")
    
    if input().lower() == 'y':
        migrator = MigrationManager()
        print("\n📋 ÉTAPES DE MIGRATION (pour plus tard):")
        print("1. railway run -- tar -czf backup.tar.gz /opt/geoserver_data")
        print("2. gsutil mb gs://agriweb-geoserver-data")
        print("3. gcloud run deploy --source .")
        print("4. Tester et valider")
        print("5. Arrêter Railway")
