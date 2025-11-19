#!/usr/bin/env python3
"""
🗂️ CRÉATION WORKSPACE GPU DANS GEOSERVER FONCTIONNEL
Maintenant que GeoServer est opérationnel
"""

import requests
import json
from datetime import datetime

def create_gpu_workspace():
    """Crée le workspace GPU dans GeoServer fonctionnel"""
    
    print("🗂️ CRÉATION WORKSPACE GPU - GEOSERVER FONCTIONNEL")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    print("✅ GeoServer déployé avec succès (41,502 ms selon logs)")
    print()
    
    base_url = "https://geoserver-agriweb-production.up.railway.app/geoserver"
    auth = ('admin', 'admin')
    
    # Test initial de connexion
    print("1️⃣ Vérification connexion GeoServer...")
    try:
        response = requests.get(f"{base_url}/rest/workspaces", auth=auth, timeout=10)
        if response.status_code == 200:
            print("   ✅ Connexion API REST établie")
            workspaces = response.json()
            print(f"   📁 Workspaces existants: {len(workspaces.get('workspaces', {}).get('workspace', []))}")
        else:
            print(f"   ⚠️ Status: {response.status_code}")
            print("   💡 GeoServer potentiellement en cours de finalisation")
            return False
    except Exception as e:
        print(f"   ❌ Erreur connexion: {e}")
        return False
    
    print()
    
    # Vérification si workspace GPU existe déjà
    print("2️⃣ Vérification workspace GPU...")
    try:
        response = requests.get(f"{base_url}/rest/workspaces/gpu", auth=auth, timeout=10)
        if response.status_code == 200:
            print("   ✅ Workspace GPU existe déjà")
            return True
        elif response.status_code == 404:
            print("   📝 Workspace GPU à créer")
        else:
            print(f"   ⚠️ Status inattendu: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur vérification: {e}")
    
    print()
    
    # Création du workspace GPU
    print("3️⃣ Création workspace GPU...")
    workspace_data = {
        "workspace": {
            "name": "gpu",
            "isolated": False
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/rest/workspaces",
            auth=auth,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(workspace_data),
            timeout=10
        )
        
        if response.status_code == 201:
            print("   ✅ Workspace GPU créé avec succès!")
        elif response.status_code == 409:
            print("   ✅ Workspace GPU existe déjà")
        else:
            print(f"   ⚠️ Status création: {response.status_code}")
            print(f"   📄 Réponse: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Erreur création: {e}")
    
    print()
    
    # Vérification finale
    print("4️⃣ Vérification finale...")
    try:
        response = requests.get(f"{base_url}/rest/workspaces/gpu", auth=auth, timeout=10)
        if response.status_code == 200:
            print("   ✅ Workspace GPU confirmé")
            workspace_info = response.json()
            print(f"   📋 Nom: {workspace_info.get('workspace', {}).get('name', 'N/A')}")
            
            # Préparation pour les couches
            print()
            print("🚀 WORKSPACE GPU PRÊT POUR LES COUCHES")
            print("=" * 40)
            
            layers_config = {
                "Cadastrales": ["prefixes_sections", "PARCELLE2024", "gpu1"],
                "Énergétiques": ["poste_elec_shapefile", "postes-electriques-rte", "CapacitesDAccueil"],
                "Agricoles": ["PARCELLES_GRAPHIQUES", "etablissements_eleveurs"],
                "Commerciales": ["GeolocalisationEtablissement_Sirene"],
                "Terrain": ["parkings_sup500m2", "friches-standard", "POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93"],
                "Réglementaires": ["ZAER_ARRETE_SHP_FRA", "ppri"]
            }
            
            total_layers = sum(len(layers) for layers in layers_config.values())
            print(f"📊 {total_layers} couches planifiées:")
            
            for category, layers in layers_config.items():
                print(f"   📁 {category}: {len(layers)} couches")
                for layer in layers:
                    print(f"      - gpu:{layer}")
            
            print()
            print("💡 PROCHAINES ÉTAPES:")
            print("   1. ✅ Workspace GPU créé")
            print("   2. 📥 Importer les données sources")
            print("   3. 🗺️ Configurer les datastores")
            print("   4. 🎨 Définir les styles")
            print("   5. 🔗 Publier les couches")
            print("   6. 🧪 Tester l'intégration AgriWeb")
            
            return True
        else:
            print(f"   ❌ Échec vérification: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur vérification finale: {e}")
        return False

if __name__ == "__main__":
    success = create_gpu_workspace()
    if success:
        print("\n🎉 SUCCÈS ! Workspace GPU créé dans GeoServer fonctionnel")
    else:
        print("\n⚠️ Problème lors de la création. Vérifiez que GeoServer est complètement démarré.")
