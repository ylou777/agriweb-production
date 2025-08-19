# Configuration des URLs GeoServer pour l'application AgriWeb
# Ce script met à jour automatiquement toutes les références GeoServer

import os
import re
from pathlib import Path

class GeoServerURLUpdater:
    def __init__(self, new_geoserver_url="https://geoserver-agriweb.up.railway.app"):
        self.new_url = new_geoserver_url.rstrip('/')
        self.local_patterns = [
            r'http://localhost:8080/?',
            r'127\.0\.0\.1:8080/?',
            r'http://localhost:8080/geoserver/?'
        ]
        
    def update_file(self, file_path):
        """Met à jour les URLs GeoServer dans un fichier"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Remplacement des patterns
            for pattern in self.local_patterns:
                content = re.sub(pattern, f"{self.new_url}/geoserver/", content, flags=re.IGNORECASE)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Mis à jour: {file_path}")
                return True
            else:
                print(f"⚪ Aucun changement: {file_path}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur avec {file_path}: {e}")
            return False
    
    def scan_and_update(self, directory="."):
        """Scan et mise à jour de tous les fichiers Python et JS"""
        extensions = ['.py', '.js', '.html', '.json']
        updated_files = []
        
        for ext in extensions:
            for file_path in Path(directory).rglob(f"*{ext}"):
                if '__pycache__' in str(file_path) or 'backup_' in str(file_path):
                    continue
                    
                if self.update_file(file_path):
                    updated_files.append(str(file_path))
        
        return updated_files
    
    def create_environment_config(self):
        """Crée un fichier .env pour la configuration"""
        env_content = f"""# Configuration GeoServer
GEOSERVER_URL={self.new_url}/geoserver
GEOSERVER_LOCAL_URL=http://localhost:8080/geoserver
ENVIRONMENT=production

# Configuration application
FLASK_ENV=production
DEBUG=False
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Fichier .env créé")

if __name__ == "__main__":
    print("🔧 Configuration des URLs GeoServer...")
    
    # URL du GeoServer distant (modifiez selon votre déploiement)
    remote_url = input("URL du GeoServer distant (défaut: https://geoserver-agriweb.up.railway.app): ").strip()
    if not remote_url:
        remote_url = "https://geoserver-agriweb.up.railway.app"
    
    updater = GeoServerURLUpdater(remote_url)
    
    # Mise à jour des fichiers
    updated_files = updater.scan_and_update()
    
    print(f"\n📊 Résumé:")
    print(f"   - {len(updated_files)} fichiers mis à jour")
    print(f"   - Nouvelle URL: {remote_url}/geoserver")
    
    # Création du fichier .env
    updater.create_environment_config()
    
    print("\n✅ Configuration terminée !")
    print("💡 Redémarrez l'application pour appliquer les changements")
