#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC GEOSERVER AGRIWEB 2.0
Script de vérification et test de toutes vos couches GeoServer
"""

import requests
import json
from datetime import datetime
import sys

def diagnose_geoserver():
    """Diagnostic complet de votre GeoServer"""
    
    print("🔍 DIAGNOSTIC GEOSERVER AGRIWEB 2.0")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    GEOSERVER_URL = "http://localhost:8080/geoserver"
    
    # 1. Test de connexion
    print("\n1️⃣ Test de connexion GeoServer...")
    try:
        response = requests.get(f"{GEOSERVER_URL}/rest/about/version.json", 
                              auth=('admin', 'geoserver'), timeout=10)
        if response.status_code == 200:
            version_info = response.json()
            print(f"  ✅ GeoServer connecté sur {GEOSERVER_URL}")
            resources = version_info.get('about', {}).get('resource', [])
            if resources:
                version = resources[0].get('Version', 'Inconnue')
                print(f"  📊 Version: {version}")
        else:
            print(f"  ❌ Erreur de connexion: HTTP {response.status_code}")
            print("  💡 Vérifiez que GeoServer est démarré et accessible")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  🚨 Impossible de se connecter à {GEOSERVER_URL}")
        print("  💡 GeoServer est-il démarré ? Port correct ?")
        return False
    except Exception as e:
        print(f"  🚨 Erreur: {e}")
        return False
    
    # 2. Test des workspaces
    print("\n2️⃣ Vérification des workspaces...")
    try:
        response = requests.get(f"{GEOSERVER_URL}/rest/workspaces.json",
                              auth=('admin', 'geoserver'))
        if response.status_code == 200:
            workspaces = response.json().get("workspaces", {}).get("workspace", [])
            workspace_names = [ws["name"] for ws in workspaces]
            print(f"  📁 Workspaces trouvés: {', '.join(workspace_names)}")
            
            if "gpu" in workspace_names:
                print("  ✅ Workspace 'gpu' détecté (utilisé par AgriWeb)")
            else:
                print("  ⚠️ Workspace 'gpu' manquant")
                print("  💡 Créez le workspace 'gpu' dans GeoServer")
        else:
            print(f"  ❌ Erreur workspaces: HTTP {response.status_code}")
    except Exception as e:
        print(f"  🚨 Erreur workspaces: {e}")
    
    # 3. Test de toutes vos couches AgriWeb
    print("\n3️⃣ Test des couches AgriWeb...")
    
    # Toutes vos couches d'après agriweb_source.py
    all_layers = {
        "🗺️ Cadastre": "gpu:prefixes_sections",
        "⚡ Postes BT": "gpu:poste_elec_shapefile",
        "🔌 Postes HTA": "gpu:postes-electriques-rte", 
        "📊 Capacités réseau": "gpu:CapacitesDAccueil",
        "🅿️ Parkings": "gpu:parkings_sup500m2",
        "🏚️ Friches": "gpu:friches-standard",
        "☀️ Potentiel solaire": "gpu:POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93",
        "🌿 ZAER": "gpu:ZAER_ARRETE_SHP_FRA",
        "🌾 RPG": "gpu:PARCELLES_GRAPHIQUES",
        "🏢 Sirène": "gpu:GeolocalisationEtablissement_Sirene france",
        "🏘️ PLU": "gpu:gpu1",
        "📍 Parcelles": "gpu:PARCELLE2024",
        "🐄 Éleveurs": "gpu:etablissements_eleveurs",
        "🌊 PPRI": "gpu:ppri"
    }
    
    working_layers = 0
    critical_layers = 0
    
    for nom, layer in all_layers.items():
        # Marquer les couches critiques
        is_critical = layer in [
            "gpu:prefixes_sections",
            "gpu:poste_elec_shapefile", 
            "gpu:PARCELLES_GRAPHIQUES"
        ]
        if is_critical:
            critical_layers += 1
        
        if test_single_layer(GEOSERVER_URL, nom, layer, is_critical):
            working_layers += 1
    
    # 4. Résumé et recommandations
    print(f"\n📊 RÉSUMÉ DU DIAGNOSTIC")
    print("-" * 40)
    print(f"✅ Couches fonctionnelles: {working_layers}/{len(all_layers)}")
    print(f"🔥 Couches critiques OK: {min(critical_layers, working_layers)}/{critical_layers}")
    
    if working_layers == len(all_layers):
        print("\n🎉 EXCELLENT ! Toutes vos couches sont accessibles !")
        print("   AgriWeb 2.0 peut utiliser toutes les fonctionnalités.")
        
    elif working_layers >= critical_layers:
        print("\n✅ BIEN ! Les couches critiques fonctionnent.")
        print("   AgriWeb 2.0 peut fonctionner avec les fonctionnalités de base.")
        print("   Corrigez les autres couches pour les fonctionnalités avancées.")
        
    else:
        print("\n⚠️ ATTENTION ! Des couches critiques sont manquantes.")
        print("   AgriWeb 2.0 aura des fonctionnalités limitées.")
        
    # 5. Recommandations
    print(f"\n💡 RECOMMANDATIONS")
    print("-" * 20)
    
    if working_layers < len(all_layers):
        print("1. Vérifiez que vos données sont bien importées dans GeoServer")
        print("2. Vérifiez les noms des couches (attention à la casse)")
        print("3. Vérifiez les permissions d'accès aux données")
        
    print("4. Optimisez vos couches avec des index spatiaux")
    print("5. Configurez GeoWebCache pour les performances")
    print("6. Testez avec des requêtes réelles sur une commune")
    
    return working_layers >= critical_layers

def test_single_layer(geoserver_url, nom, layer_name, is_critical=False):
    """Test d'une couche spécifique"""
    url = f"{geoserver_url}/ows"
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature", 
        "typeName": layer_name,
        "maxFeatures": 1,
        "outputFormat": "application/json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            feature_count = len(data.get("features", []))
            
            # Vérifier s'il y a des données
            if feature_count > 0:
                critical_mark = " 🔥" if is_critical else ""
                print(f"  ✅ {nom}: {feature_count} feature(s){critical_mark}")
                return True
            else:
                critical_mark = " 🔥" if is_critical else ""
                print(f"  ⚠️ {nom}: 0 features (couche vide){critical_mark}")
                return False
        else:
            critical_mark = " 🔥" if is_critical else ""
            print(f"  ❌ {nom}: HTTP {response.status_code}{critical_mark}")
            if response.status_code == 404:
                print(f"     💡 Couche '{layer_name}' non trouvée")
            return False
    except requests.exceptions.Timeout:
        print(f"  ⏰ {nom}: Timeout (> 15s)")
        return False
    except Exception as e:
        print(f"  🚨 {nom}: {str(e)}")
        return False

def test_specific_commune():
    """Test avec une commune spécifique"""
    print("\n4️⃣ Test avec une commune réelle...")
    
    # Bbox d'une petite zone (exemple: autour de Paris)
    test_bbox = [2.0, 48.5, 2.5, 49.0]  # Longitude min, Latitude min, Longitude max, Latitude max
    
    GEOSERVER_URL = "http://localhost:8080/geoserver"
    test_layer = "gpu:prefixes_sections"  # Couche cadastre
    
    url = f"{GEOSERVER_URL}/ows"
    bbox_str = f"{test_bbox[0]},{test_bbox[1]},{test_bbox[2]},{test_bbox[3]},EPSG:4326"
    
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": test_layer,
        "bbox": bbox_str,
        "maxFeatures": 10,
        "outputFormat": "application/json"
    }
    
    try:
        print(f"  🎯 Test avec bbox: {test_bbox}")
        response = requests.get(url, params=params, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            print(f"  ✅ Test spatial réussi: {len(features)} features dans la zone")
            
            # Afficher quelques propriétés si disponibles
            if features:
                props = features[0].get("properties", {})
                print(f"  📋 Exemple de propriétés: {list(props.keys())[:5]}")
            
            return True
        else:
            print(f"  ❌ Test spatial échoué: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  🚨 Erreur test spatial: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Lancement du diagnostic GeoServer...")
    
    success = diagnose_geoserver()
    
    # Test spatial bonus
    test_specific_commune()
    
    print("\n" + "="*60)
    if success:
        print("🎉 DIAGNOSTIC TERMINÉ - GeoServer prêt pour AgriWeb 2.0!")
        print("   Vous pouvez démarrer la commercialisation.")
    else:
        print("⚠️ DIAGNOSTIC TERMINÉ - Configuration requise")
        print("   Corrigez les problèmes avant la production.")
    
    print("\n📖 Consultez GUIDE_GEOSERVER_CONFIGURATION.md pour plus de détails.")
    
    sys.exit(0 if success else 1)
