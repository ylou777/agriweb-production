#!/usr/bin/env python3
"""
Script de migration GeoServer local vers hébergement distant
"""

import os
import zipfile
import requests
import shutil
from pathlib import Path

class GeoServerMigration:
    def __init__(self, local_url="http://localhost:8080/geoserver", 
                 remote_url="https://geoserver-agriweb.up.railway.app/geoserver"):
        self.local_url = local_url
        self.remote_url = remote_url
        self.admin_user = "admin"
        self.admin_password = "admin123"
        
    def export_workspace(self, workspace_name="gpu"):
        """Exporte un workspace GeoServer"""
        print(f"📦 Export du workspace '{workspace_name}'...")
        
        export_url = f"{self.local_url}/rest/workspaces/{workspace_name}.zip"
        
        try:
            response = requests.get(
                export_url,
                auth=(self.admin_user, self.admin_password),
                timeout=30
            )
            
            if response.status_code == 200:
                export_file = f"{workspace_name}_export.zip"
                with open(export_file, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Workspace exporté : {export_file}")
                return export_file
            else:
                print(f"❌ Erreur export: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return None
    
    def import_workspace(self, zip_file):
        """Importe un workspace sur le GeoServer distant"""
        print(f"📤 Import du workspace vers {self.remote_url}...")
        
        import_url = f"{self.remote_url}/rest/workspaces"
        
        try:
            with open(zip_file, 'rb') as f:
                files = {'file': (zip_file, f, 'application/zip')}
                
                response = requests.post(
                    import_url,
                    files=files,
                    auth=(self.admin_user, self.admin_password),
                    timeout=60
                )
            
            if response.status_code in [200, 201]:
                print("✅ Workspace importé avec succès")
                return True
            else:
                print(f"❌ Erreur import: {response.status_code}")
                print(f"Réponse: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def migrate_data_dir(self, data_dir_path=None):
        """Migration complète du répertoire de données"""
        if not data_dir_path:
            # Détection automatique du répertoire GeoServer
            possible_paths = [
                r"C:\Program Files\GeoServer\data_dir",
                r"C:\geoserver\data_dir",
                os.path.expanduser("~/geoserver/data_dir"),
                "/opt/geoserver/data_dir"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    data_dir_path = path
                    break
        
        if not data_dir_path or not os.path.exists(data_dir_path):
            print("❌ Répertoire GeoServer non trouvé")
            return False
        
        print(f"📁 Migration depuis: {data_dir_path}")
        
        # Création de l'archive
        archive_name = "geoserver_data_migration.zip"
        
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(data_dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, data_dir_path)
                    zf.write(file_path, arc_name)
        
        print(f"✅ Archive créée: {archive_name}")
        return archive_name
    
    def test_connection(self, url):
        """Test de connexion à GeoServer"""
        try:
            response = requests.get(
                f"{url}/rest/about/version",
                auth=(self.admin_user, self.admin_password),
                timeout=10
            )
            
            if response.status_code == 200:
                version_info = response.json()
                print(f"✅ Connexion OK - Version: {version_info.get('about', {}).get('resource', [{}])[0].get('Version', 'Inconnue')}")
                return True
            else:
                print(f"❌ Erreur connexion: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def run_migration(self):
        """Lance la migration complète"""
        print("🚀 Début de la migration GeoServer...")
        
        # Test connexion locale
        print("\n1. Test connexion locale...")
        if not self.test_connection(self.local_url):
            print("❌ GeoServer local non accessible")
            return False
        
        # Test connexion distante
        print("\n2. Test connexion distante...")
        if not self.test_connection(self.remote_url):
            print("❌ GeoServer distant non accessible")
            print("💡 Assurez-vous que le GeoServer distant est déployé")
            return False
        
        # Export des workspaces
        print("\n3. Export des workspaces...")
        workspaces = ["gpu", "topp"]  # Ajustez selon vos workspaces
        
        for workspace in workspaces:
            export_file = self.export_workspace(workspace)
            if export_file:
                print(f"\n4. Import du workspace {workspace}...")
                self.import_workspace(export_file)
        
        print("\n✅ Migration terminée !")
        print(f"🌐 Votre GeoServer distant: {self.remote_url}")
        
        return True

if __name__ == "__main__":
    migration = GeoServerMigration()
    migration.run_migration()
