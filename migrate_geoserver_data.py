#!/usr/bin/env python3
"""
Script de migration des couches GeoServer vers Railway
Ce script exporte les données du GeoServer local et les importe vers Railway
"""

import os
import requests
import json
import zipfile
import tempfile
from pathlib import Path
import time
import sys

class GeoServerMigrator:
    def __init__(self):
        # Configuration locale
        self.local_geoserver = "http://localhost:8080/geoserver"
        self.local_admin = ("admin", "geoserver")
        
        # Configuration Railway
        self.railway_geoserver = "https://geoserver-agriweb-production.up.railway.app/geoserver"
        self.railway_admin = ("admin", "admin123")
        
        # Répertoire de sauvegarde
        self.backup_dir = Path("geoserver_backup")
        self.backup_dir.mkdir(exist_ok=True)
        
    def test_connection(self, url, auth):
        """Teste la connexion à un GeoServer"""
        try:
            response = requests.get(f"{url}/rest/about/version", 
                                  auth=auth, timeout=10)
            if response.status_code == 200:
                version_info = response.json()
                return True, version_info
            return False, f"Status: {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    def export_workspaces(self):
        """Exporte tous les workspaces du GeoServer local"""
        print("🔄 Export des workspaces...")
        
        try:
            # Lister les workspaces
            response = requests.get(f"{self.local_geoserver}/rest/workspaces",
                                  auth=self.local_admin,
                                  headers={'Accept': 'application/json'})
            
            if response.status_code != 200:
                print(f"❌ Erreur listing workspaces: {response.status_code}")
                return False
                
            workspaces = response.json().get('workspaces', {}).get('workspace', [])
            
            if not workspaces:
                print("⚠️  Aucun workspace trouvé")
                return True
                
            workspaces_data = []
            
            for ws in workspaces:
                ws_name = ws['name']
                print(f"   📁 Workspace: {ws_name}")
                
                # Détails du workspace
                ws_response = requests.get(f"{self.local_geoserver}/rest/workspaces/{ws_name}",
                                         auth=self.local_admin,
                                         headers={'Accept': 'application/json'})
                
                if ws_response.status_code == 200:
                    ws_data = ws_response.json()
                    workspaces_data.append(ws_data)
                    
                    # Exporter les datastores
                    self.export_datastores(ws_name)
                    
                    # Exporter les couches
                    self.export_layers(ws_name)
            
            # Sauvegarder les workspaces
            with open(self.backup_dir / "workspaces.json", 'w') as f:
                json.dump(workspaces_data, f, indent=2)
                
            print(f"✅ {len(workspaces_data)} workspaces exportés")
            return True
            
        except Exception as e:
            print(f"❌ Erreur export workspaces: {e}")
            return False
    
    def export_datastores(self, workspace):
        """Exporte les datastores d'un workspace"""
        try:
            response = requests.get(f"{self.local_geoserver}/rest/workspaces/{workspace}/datastores",
                                  auth=self.local_admin,
                                  headers={'Accept': 'application/json'})
            
            if response.status_code == 200:
                datastores = response.json().get('dataStores', {}).get('dataStore', [])
                
                if datastores:
                    # Créer le répertoire pour ce workspace
                    ws_dir = self.backup_dir / workspace
                    ws_dir.mkdir(exist_ok=True)
                    
                    datastores_data = []
                    for ds in datastores:
                        ds_name = ds['name']
                        print(f"      🗄️  Datastore: {ds_name}")
                        
                        # Détails du datastore
                        ds_response = requests.get(f"{self.local_geoserver}/rest/workspaces/{workspace}/datastores/{ds_name}",
                                                 auth=self.local_admin,
                                                 headers={'Accept': 'application/json'})
                        
                        if ds_response.status_code == 200:
                            datastores_data.append(ds_response.json())
                    
                    # Sauvegarder
                    with open(ws_dir / "datastores.json", 'w') as f:
                        json.dump(datastores_data, f, indent=2)
                        
        except Exception as e:
            print(f"   ⚠️  Erreur export datastores {workspace}: {e}")
    
    def export_layers(self, workspace):
        """Exporte les couches d'un workspace"""
        try:
            response = requests.get(f"{self.local_geoserver}/rest/workspaces/{workspace}/layers",
                                  auth=self.local_admin,
                                  headers={'Accept': 'application/json'})
            
            if response.status_code == 200:
                layers = response.json().get('layers', {}).get('layer', [])
                
                if layers:
                    ws_dir = self.backup_dir / workspace
                    ws_dir.mkdir(exist_ok=True)
                    
                    layers_data = []
                    for layer in layers:
                        layer_name = layer['name']
                        print(f"      🗺️  Couche: {layer_name}")
                        
                        # Détails de la couche
                        layer_response = requests.get(f"{self.local_geoserver}/rest/workspaces/{workspace}/layers/{layer_name}",
                                                    auth=self.local_admin,
                                                    headers={'Accept': 'application/json'})
                        
                        if layer_response.status_code == 200:
                            layers_data.append(layer_response.json())
                    
                    # Sauvegarder
                    with open(ws_dir / "layers.json", 'w') as f:
                        json.dump(layers_data, f, indent=2)
                        
        except Exception as e:
            print(f"   ⚠️  Erreur export layers {workspace}: {e}")
    
    def import_to_railway(self):
        """Importe les données vers GeoServer Railway"""
        print("🚀 Import vers Railway...")
        
        # Vérifier la connectivité Railway
        connected, info = self.test_connection(self.railway_geoserver, self.railway_admin)
        if not connected:
            print(f"❌ GeoServer Railway non accessible: {info}")
            return False
            
        print(f"✅ GeoServer Railway connecté: {info}")
        
        # Charger les workspaces
        workspaces_file = self.backup_dir / "workspaces.json"
        if not workspaces_file.exists():
            print("❌ Pas de sauvegarde de workspaces trouvée")
            return False
            
        with open(workspaces_file) as f:
            workspaces = json.load(f)
            
        # Créer les workspaces
        for ws_data in workspaces:
            ws_name = ws_data['workspace']['name']
            print(f"   📁 Création workspace: {ws_name}")
            
            # Créer le workspace
            create_data = {
                "workspace": {
                    "name": ws_name,
                    "isolated": ws_data['workspace'].get('isolated', False)
                }
            }
            
            response = requests.post(f"{self.railway_geoserver}/rest/workspaces",
                                   auth=self.railway_admin,
                                   headers={'Content-Type': 'application/json'},
                                   json=create_data)
            
            if response.status_code in [201, 409]:  # 409 = déjà existe
                print(f"   ✅ Workspace {ws_name} créé/existe")
                
                # Importer datastores et layers
                self.import_workspace_content(ws_name)
            else:
                print(f"   ❌ Erreur création workspace {ws_name}: {response.status_code}")
        
        return True
    
    def import_workspace_content(self, workspace):
        """Importe le contenu d'un workspace"""
        ws_dir = self.backup_dir / workspace
        
        # Importer les datastores
        datastores_file = ws_dir / "datastores.json"
        if datastores_file.exists():
            with open(datastores_file) as f:
                datastores = json.load(f)
                
            for ds_data in datastores:
                ds_name = ds_data['dataStore']['name']
                print(f"      🗄️  Import datastore: {ds_name}")
                
                # Adapter les paramètres de connexion
                connection_params = ds_data['dataStore'].get('connectionParameters', {})
                
                # Pour les shapfiles, il faudra uploader les fichiers
                # Pour les bases de données, adapter les paramètres
                # Ici on skip l'import automatique des datastores complexes
                print(f"      ⚠️  Datastore {ds_name} nécessite une configuration manuelle")
        
        # Note: L'import des couches nécessite que les datastores soient configurés
        print(f"      💡 Configurez manuellement les datastores puis relancez l'import")

def main():
    print("🔄 MIGRATION GEOSERVER LOCAL → RAILWAY")
    print("=====================================")
    
    migrator = GeoServerMigrator()
    
    # Test connexions
    print("\n🔍 Test des connexions...")
    
    # Test local
    local_ok, local_info = migrator.test_connection(migrator.local_geoserver, migrator.local_admin)
    if local_ok:
        print(f"✅ GeoServer local OK: {local_info}")
    else:
        print(f"❌ GeoServer local inaccessible: {local_info}")
        print("💡 Démarrez votre GeoServer local avant la migration")
        return
    
    # Test Railway
    railway_ok, railway_info = migrator.test_connection(migrator.railway_geoserver, migrator.railway_admin)
    if railway_ok:
        print(f"✅ GeoServer Railway OK: {railway_info}")
    else:
        print(f"❌ GeoServer Railway inaccessible: {railway_info}")
        print("💡 Attendez que le déploiement Railway soit terminé")
        return
    
    # Export des données locales
    print(f"\n📦 Export depuis {migrator.local_geoserver}...")
    if not migrator.export_workspaces():
        print("❌ Échec de l'export")
        return
    
    print(f"✅ Données exportées dans: {migrator.backup_dir}")
    
    # Import vers Railway
    print(f"\n🚀 Import vers {migrator.railway_geoserver}...")
    if migrator.import_to_railway():
        print("✅ Migration terminée !")
        print(f"\n🌐 Votre GeoServer Railway: {migrator.railway_geoserver}")
        print("🔐 Admin: admin / admin123")
    else:
        print("❌ Échec de l'import")

if __name__ == "__main__":
    main()
