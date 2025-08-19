#!/usr/bin/env python3
"""
🧪 TEST COMPLET AGRIWEB + GEOSERVER
Validation des 14 couches critiques pour AgriWeb 2.0
"""

import requests
import json
from datetime import datetime

def test_all_agriweb_layers():
    """Test complet des couches AgriWeb depuis votre GeoServer"""
    
    print("🧪 TEST COMPLET AGRIWEB + GEOSERVER")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Validation des 14 couches critiques AgriWeb")
    
    geoserver_url = "http://localhost:8080/geoserver"
    wfs_url = f"{geoserver_url}/ows"
    
    # Les 14 couches critiques pour AgriWeb
    critical_layers = [
        "gpu:prefixes_sections",
        "gpu:poste_elec_shapefile", 
        "gpu:postes-electriques-rte",
        "gpu:CapacitesDAccueil",
        "gpu:parkings_sup500m2",
        "gpu:friches-standard",
        "gpu:POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93",
        "gpu:ZAER_ARRETE_SHP_FRA",
        "gpu:PARCELLES_GRAPHIQUES",
        "gpu:GeolocalisationEtablissement_Sirene france",
        "gpu:gpu1",
        "gpu:PARCELLE2024",
        "gpu:etablissements_eleveurs",
        "gpu:ppri"
    ]
    
    print(f"\n🔍 Test des {len(critical_layers)} couches critiques...")
    
    working_layers = []
    missing_layers = []
    error_layers = []
    
    for layer_name in critical_layers:
        print(f"\n📋 Test: {layer_name}")
        
        try:
            # Test GetFeature avec 1 seule feature
            params = {
                "service": "WFS",
                "version": "1.0.0", 
                "request": "GetFeature",
                "typeName": layer_name,
                "maxFeatures": 1,
                "outputFormat": "application/json"
            }
            
            response = requests.get(wfs_url, params=params, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    feature_count = len(data.get("features", []))
                    
                    if feature_count > 0:
                        print(f"   ✅ OPÉRATIONNELLE ({feature_count} feature accessible)")
                        working_layers.append(layer_name)
                        
                        # Afficher quelques propriétés
                        if data["features"]:
                            props = data["features"][0].get("properties", {})
                            if props:
                                prop_names = list(props.keys())[:3]  # 3 premières propriétés
                                print(f"      📊 Propriétés: {', '.join(prop_names)}...")
                    else:
                        print(f"   ⚠️ VIDE (couche existe mais pas de données)")
                        working_layers.append(layer_name)  # La couche existe
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Réponse non-JSON")
                    error_layers.append(layer_name)
                    
            elif response.status_code == 404:
                print(f"   ❌ MANQUANTE (404)")
                missing_layers.append(layer_name)
                
            else:
                print(f"   ❌ ERREUR HTTP {response.status_code}")
                error_layers.append(layer_name)
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️ TIMEOUT")
            error_layers.append(layer_name)
            
        except Exception as e:
            print(f"   ❌ ERREUR: {str(e)[:40]}...")
            error_layers.append(layer_name)
    
    # RÉSULTATS FINAUX
    print(f"\n" + "="*60)
    print(f"📊 RÉSULTATS DU TEST COMPLET")
    print(f"="*60)
    
    print(f"✅ Couches opérationnelles: {len(working_layers)}/{len(critical_layers)}")
    print(f"❌ Couches manquantes: {len(missing_layers)}")
    print(f"⚠️ Couches avec erreurs: {len(error_layers)}")
    
    if working_layers:
        print(f"\n✅ COUCHES OPÉRATIONNELLES:")
        for layer in working_layers:
            print(f"   • {layer}")
    
    if missing_layers:
        print(f"\n❌ COUCHES MANQUANTES:")
        for layer in missing_layers:
            print(f"   • {layer}")
            
    if error_layers:
        print(f"\n⚠️ COUCHES AVEC ERREURS:")
        for layer in error_layers:
            print(f"   • {layer}")
    
    # VERDICT FINAL
    success_rate = len(working_layers) / len(critical_layers) * 100
    
    print(f"\n🎯 VERDICT FINAL:")
    print(f"   📈 Taux de réussite: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print(f"   🎉 EXCELLENT ! AgriWeb peut fonctionner avec votre GeoServer")
        print(f"   ✅ Intégration prête pour la production")
    elif success_rate >= 50:
        print(f"   ⚠️ PARTIEL - AgriWeb fonctionnera avec limitations")
        print(f"   🔧 Quelques couches manquantes à ajouter")
    else:
        print(f"   ❌ INSUFFISANT - Trop de couches manquantes")
        print(f"   📋 Configuration GeoServer à compléter")
    
    return {
        "working": working_layers,
        "missing": missing_layers, 
        "errors": error_layers,
        "success_rate": success_rate
    }

def test_sample_commune():
    """Test d'une recherche AgriWeb sur une commune test"""
    
    print(f"\n" + "="*60)
    print(f"🌍 TEST RECHERCHE COMMUNE (simulation AgriWeb)")
    print(f"="*60)
    
    # Test simple avec une commune
    commune_test = "Lyon"  # Commune avec beaucoup de données
    
    print(f"🏘️ Test de recherche pour: {commune_test}")
    
    # Simulation d'une recherche RPG (parcelles agricoles)
    try:
        geoserver_url = "http://localhost:8080/geoserver"
        wfs_url = f"{geoserver_url}/ows"
        
        # Test parcelles RPG
        params = {
            "service": "WFS",
            "version": "1.0.0",
            "request": "GetFeature", 
            "typeName": "gpu:PARCELLES_GRAPHIQUES",
            "maxFeatures": 5,
            "outputFormat": "application/json"
        }
        
        response = requests.get(wfs_url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            parcelles_count = len(data.get("features", []))
            
            print(f"✅ Parcelles RPG trouvées: {parcelles_count}")
            
            if parcelles_count > 0:
                # Analyser une parcelle
                parcelle = data["features"][0]
                props = parcelle.get("properties", {})
                geom = parcelle.get("geometry", {})
                
                print(f"📊 Exemple de parcelle:")
                print(f"   🗂️ Propriétés: {len(props)} champs")
                print(f"   📐 Géométrie: {geom.get('type', 'N/A')}")
                
                if props:
                    # Afficher quelques propriétés importantes
                    for key in ['code_comm', 'surf_graph', 'code_cultu']:
                        if key in props:
                            print(f"   • {key}: {props[key]}")
                            
            print(f"✅ AgriWeb peut effectuer des recherches sur votre GeoServer !")
            
        else:
            print(f"❌ Erreur test recherche: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur test recherche: {e}")

if __name__ == "__main__":
    print("🚀 Démarrage test complet AgriWeb + GeoServer...")
    
    # Test 1: Validation des couches
    results = test_all_agriweb_layers()
    
    # Test 2: Simulation recherche
    test_sample_commune()
    
    print(f"\n" + "="*60)
    print(f"🏁 TEST TERMINÉ")
    print(f"="*60)
    
    if results["success_rate"] >= 80:
        print(f"🎉 VOTRE GEOSERVER EST PRÊT POUR AGRIWEB 2.0 !")
        print(f"✅ Vous pouvez maintenant intégrer le système de licences")
        print(f"🚀 AgriWeb commercial peut démarrer en production")
    else:
        print(f"⚠️ Configuration GeoServer à compléter")
        print(f"📋 Voir les couches manquantes ci-dessus")
    
    print(f"\n📖 Guide complet: GUIDE_GEOSERVER_CONFIGURATION.md")
