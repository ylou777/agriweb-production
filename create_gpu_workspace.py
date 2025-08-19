#!/usr/bin/env python3
"""
🗂️ CRÉATION WORKSPACE GPU DANS GEOSERVER
Prépare l'environnement GeoServer pour les couches AgriWeb
"""

import requests
import json
from datetime import datetime

def create_gpu_workspace():
    """Crée le workspace GPU dans GeoServer"""
    
    base_url = "https://geoserver-agriweb-production.up.railway.app"
    auth = ('admin', 'admin')
    
    print("🗂️ CRÉATION WORKSPACE GPU DANS GEOSERVER")
    print("=" * 55)
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Étape 1: Vérifier que GeoServer est accessible
    print("1️⃣ Vérification accès GeoServer...")
    try:
        response = requests.get(f"{base_url}/geoserver/rest/workspaces", 
                              auth=auth, timeout=10)
        if response.status_code == 200:
            print("   ✅ GeoServer accessible")
            workspaces = response.json()
            existing_workspaces = [ws['name'] for ws in workspaces['workspaces']['workspace']]
            print(f"   📋 Workspaces existants: {existing_workspaces}")
        else:
            print(f"   ❌ Erreur accès: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur connexion: {e}")
        return False
    
    print()
    
    # Étape 2: Créer le workspace GPU si nécessaire
    print("2️⃣ Création workspace GPU...")
    
    if 'gpu' in existing_workspaces:
        print("   ✅ Workspace 'gpu' déjà existant")
    else:
        try:
            workspace_data = {
                "workspace": {
                    "name": "gpu",
                    "isolated": False
                }
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{base_url}/geoserver/rest/workspaces",
                auth=auth,
                headers=headers,
                data=json.dumps(workspace_data),
                timeout=10
            )
            
            if response.status_code == 201:
                print("   ✅ Workspace 'gpu' créé avec succès!")
            else:
                print(f"   ⚠️ Création workspace: Status {response.status_code}")
                print(f"   📄 Réponse: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Erreur création workspace: {e}")
    
    print()
    
    # Étape 3: Vérifier le workspace GPU
    print("3️⃣ Vérification workspace GPU...")
    try:
        response = requests.get(f"{base_url}/geoserver/rest/workspaces/gpu", 
                              auth=auth, timeout=10)
        if response.status_code == 200:
            print("   ✅ Workspace 'gpu' confirmé")
            workspace_info = response.json()
            print(f"   📋 Nom: {workspace_info['workspace']['name']}")
            print(f"   🔗 Href: {workspace_info['workspace']['href']}")
        else:
            print(f"   ❌ Workspace non trouvé: Status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur vérification: {e}")
    
    print()
    
    # Étape 4: Lister les datastores dans GPU
    print("4️⃣ Vérification datastores...")
    try:
        response = requests.get(f"{base_url}/geoserver/rest/workspaces/gpu/datastores", 
                              auth=auth, timeout=10)
        if response.status_code == 200:
            datastores = response.json()
            if 'dataStores' in datastores and datastores['dataStores']:
                store_count = len(datastores['dataStores']['dataStore'])
                print(f"   📊 Datastores trouvés: {store_count}")
                for store in datastores['dataStores']['dataStore']:
                    print(f"      - {store['name']}")
            else:
                print("   📭 Aucun datastore (normal pour nouveau workspace)")
        else:
            print(f"   ⚠️ Erreur datastores: Status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur datastores: {e}")
    
    print()
    
    # Étape 5: Afficher les couches prévues
    print("5️⃣ Couches prévues pour le workspace GPU...")
    
    # Configuration des couches depuis AgriWeb
    planned_layers = {
        "Cadastrales": ["prefixes_sections", "PARCELLE2024", "gpu1"],
        "Énergétiques": ["poste_elec_shapefile", "postes-electriques-rte", "CapacitesDAccueil"],
        "Agricoles": ["PARCELLES_GRAPHIQUES", "etablissements_eleveurs"],
        "Commerciales": ["GeolocalisationEtablissement_Sirene france"],
        "Terrain": ["parkings_sup500m2", "friches-standard", "POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93"],
        "Réglementaires": ["ZAER_ARRETE_SHP_FRA", "ppri"]
    }
    
    total_layers = sum(len(layers) for layers in planned_layers.values())
    print(f"   📊 Total couches prévues: {total_layers}")
    
    for category, layers in planned_layers.items():
        print(f"   📂 {category}: {len(layers)} couches")
        for layer in layers:
            print(f"      - gpu:{layer}")
    
    print()
    print("=" * 55)
    print("📋 RÉSUMÉ:")
    
    # Test final
    try:
        response = requests.get(f"{base_url}/geoserver/rest/workspaces/gpu", 
                              auth=auth, timeout=5)
        gpu_ready = response.status_code == 200
        
        if gpu_ready:
            print("🎉 WORKSPACE GPU PRÊT!")
            print("✅ Workspace 'gpu' opérationnel")
            print("✅ Accès API REST fonctionnel")
            print("✅ Prêt pour l'import des couches")
            print()
            print("📝 PROCHAINES ÉTAPES:")
            print("   1. Préparer les données géographiques")
            print("   2. Créer les datastores nécessaires")
            print("   3. Importer les 14 couches planifiées")
            print("   4. Configurer les styles et métadonnées")
            print()
            print("🔗 ACCÈS WORKSPACE:")
            print(f"   🌐 Interface: {base_url}/geoserver/web/")
            print(f"   🔧 API: {base_url}/geoserver/rest/workspaces/gpu")
            
        else:
            print("❌ PROBLÈME WORKSPACE GPU")
            print("⚠️ Vérifiez la configuration GeoServer")
            
    except Exception as e:
        print(f"❌ Erreur test final: {e}")
    
    print("=" * 55)
    return gpu_ready

if __name__ == "__main__":
    create_gpu_workspace()
