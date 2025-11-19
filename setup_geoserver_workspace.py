#!/usr/bin/env python3
"""
🚀 CRÉATION AUTOMATIQUE DU WORKSPACE GPU
Et test d'importation des couches GeoServer
"""

import requests
import json
from datetime import datetime
import base64

class GeoServerManager:
    def __init__(self, base_url="https://geoserver-agriweb-production.up.railway.app/geoserver"):
        self.base_url = base_url
        self.username = "admin"
        self.password = "admin"
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.auth = (self.username, self.password)
    
    def test_connection(self):
        """Test la connexion à GeoServer"""
        try:
            response = requests.get(
                f"{self.base_url}/web/",
                auth=self.auth,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def create_workspace(self, workspace_name="gpu"):
        """Crée le workspace GPU"""
        
        workspace_data = {
            "workspace": {
                "name": workspace_name,
                "metadata": {
                    "entry": [
                        {"@key": "description", "$": "Workspace principal pour AgriWeb GPU"},
                        {"@key": "created", "$": datetime.now().isoformat()},
                        {"@key": "project", "$": "AgriWeb 2.0"}
                    ]
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/rest/workspaces",
                json=workspace_data,
                headers=self.headers,
                auth=self.auth,
                timeout=15
            )
            
            if response.status_code == 201:
                print(f"✅ Workspace '{workspace_name}' créé avec succès")
                return True
            elif response.status_code == 409:
                print(f"ℹ️ Workspace '{workspace_name}' existe déjà")
                return True
            else:
                print(f"❌ Erreur création workspace: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception création workspace: {e}")
            return False
    
    def list_workspaces(self):
        """Liste tous les workspaces"""
        try:
            response = requests.get(
                f"{self.base_url}/rest/workspaces",
                headers={'Accept': 'application/json'},
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                workspaces = data.get('workspaces', {}).get('workspace', [])
                
                print("\n📋 WORKSPACES EXISTANTS:")
                print("-" * 25)
                if workspaces:
                    for ws in workspaces:
                        print(f"🗂️ {ws['name']}")
                else:
                    print("❌ Aucun workspace trouvé")
                return workspaces
            else:
                print(f"❌ Impossible de lister les workspaces: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Erreur listage workspaces: {e}")
            return []
    
    def get_workspace_info(self, workspace_name="gpu"):
        """Récupère les informations du workspace"""
        try:
            response = requests.get(
                f"{self.base_url}/rest/workspaces/{workspace_name}",
                headers={'Accept': 'application/json'},
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n📊 INFORMATIONS WORKSPACE '{workspace_name}':")
                print("-" * 35)
                workspace = data.get('workspace', {})
                print(f"🏷️ Nom: {workspace.get('name', 'N/A')}")
                
                # Métadonnées
                metadata = workspace.get('metadata', {})
                if metadata:
                    entries = metadata.get('entry', [])
                    for entry in entries:
                        key = entry.get('@key', 'Unknown')
                        value = entry.get('$', 'N/A')
                        print(f"📋 {key}: {value}")
                
                return True
            else:
                print(f"❌ Workspace '{workspace_name}' non trouvé: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur récupération workspace: {e}")
            return False
    
    def prepare_sample_datastore(self, workspace_name="gpu"):
        """Prépare un datastore d'exemple (Vector - Directory)"""
        
        # Pour l'instant, on crée juste un datastore de type Directory
        # qui peut contenir des fichiers Shapefile
        datastore_data = {
            "dataStore": {
                "name": "sample_vector_data",
                "type": "Directory of spatial files (shapefiles)",
                "enabled": True,
                "workspace": {
                    "name": workspace_name
                },
                "connectionParameters": {
                    "entry": [
                        {"@key": "url", "$": "file:data/sample/"},
                        {"@key": "charset", "$": "UTF-8"}
                    ]
                },
                "metadata": {
                    "entry": [
                        {"@key": "description", "$": "Datastore d'exemple pour tests AgriWeb"},
                        {"@key": "created", "$": datetime.now().isoformat()}
                    ]
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/rest/workspaces/{workspace_name}/datastores",
                json=datastore_data,
                headers=self.headers,
                auth=self.auth,
                timeout=15
            )
            
            if response.status_code == 201:
                print(f"✅ Datastore 'sample_vector_data' créé dans '{workspace_name}'")
                return True
            elif response.status_code == 409:
                print(f"ℹ️ Datastore 'sample_vector_data' existe déjà")
                return True
            else:
                print(f"❌ Erreur création datastore: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception création datastore: {e}")
            return False

def main():
    """Fonction principale de setup"""
    
    print("🚀 SETUP AUTOMATIQUE GEOSERVER - WORKSPACE GPU")
    print("=" * 55)
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Initialisation du manager
    geoserver = GeoServerManager()
    
    # 1. Test de connexion
    print("1️⃣ Test de connexion GeoServer...")
    if not geoserver.test_connection():
        print("❌ Impossible de se connecter à GeoServer")
        print("💡 Vérifiez que GeoServer est accessible :")
        print("   https://geoserver-agriweb-production.up.railway.app/geoserver/web/")
        return False
    
    print("✅ Connexion GeoServer établie")
    
    # 2. Liste des workspaces existants
    print("\n2️⃣ Vérification des workspaces existants...")
    workspaces = geoserver.list_workspaces()
    
    # 3. Création du workspace GPU
    print("\n3️⃣ Création du workspace GPU...")
    if geoserver.create_workspace("gpu"):
        print("✅ Workspace GPU prêt")
    else:
        print("❌ Échec création workspace GPU")
        return False
    
    # 4. Informations du workspace
    print("\n4️⃣ Vérification du workspace GPU...")
    geoserver.get_workspace_info("gpu")
    
    # 5. Création d'un datastore d'exemple
    print("\n5️⃣ Préparation datastore d'exemple...")
    geoserver.prepare_sample_datastore("gpu")
    
    print("\n" + "=" * 55)
    print("✅ SETUP TERMINÉ AVEC SUCCÈS !")
    print()
    print("📋 ÉTAPES SUIVANTES :")
    print("1. 🌐 Ouvrir GeoServer : https://geoserver-agriweb-production.up.railway.app/geoserver/web/")
    print("2. 🔐 Se connecter avec : admin / admin")
    print("3. 🗂️ Vérifier le workspace 'gpu'")
    print("4. 📥 Commencer l'importation des données réelles")
    print()
    print("💡 Le workspace GPU est maintenant prêt pour l'importation des 14 couches planifiées")
    
    return True

if __name__ == "__main__":
    main()
