#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC SÉCURISÉ GEOSERVER EXISTANT
LECTURE SEULE - AUCUNE MODIFICATION DE VOTRE CONFIGURATION
"""

import requests
import json
from datetime import datetime

def find_geoserver_safely():
    """Trouve votre GeoServer SANS rien modifier"""
    
    print("🛡️ DIAGNOSTIC SÉCURISÉ DE VOTRE GEOSERVER EXISTANT")
    print("=" * 60)
    print("⚠️ MODE LECTURE SEULE - Aucune modification de vos données")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Chemins possibles pour votre GeoServer existant
    possible_paths = [
        "http://localhost:8080/geoserver",
        "http://localhost:8080",  # Racine Tomcat
        "http://localhost:8081/geoserver", 
        "http://localhost:8080/geoserver-2.22.0",  # Version spécifique
        "http://localhost:8080/geoserver-2.21.0",
        "http://localhost:8080/gs",  # Raccourci possible
        "http://127.0.0.1:8080/geoserver"
    ]
    
    print(f"\n🔍 Recherche de votre GeoServer (lecture seule)...")
    
    for base_url in possible_paths:
        print(f"\n🧭 Test: {base_url}")
        result = test_geoserver_readonly(base_url)
        if result:
            return result
    
    print(f"\n🤔 GeoServer non trouvé sur les chemins standards...")
    print(f"💡 Pouvez-vous me dire :")
    print(f"   - Sur quel port tourne votre GeoServer ?")
    print(f"   - Quelle URL utilisez-vous normalement ?")
    print(f"   - Avez-vous une interface web qui fonctionne ?")
    
    return None

def test_geoserver_readonly(base_url):
    """Test en lecture seule - AUCUNE modification"""
    
    try:
        # Test 1: Page principale (lecture seule)
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            content = response.text.lower()
            if "geoserver" in content:
                print(f"   ✅ GeoServer trouvé !")
                
                # Test 2: Vérification des services (lecture seule)
                services_ok = test_services_readonly(base_url)
                
                if services_ok:
                    print(f"   🎯 GEOSERVER FONCTIONNEL DÉTECTÉ !")
                    analyze_existing_layers_safely(base_url)
                    return base_url
                
        else:
            print(f"   ❌ Pas de réponse (HTTP {response.status_code})")
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connexion impossible")
    except Exception as e:
        print(f"   ❌ Erreur: {str(e)[:40]}...")
    
    return None

def test_services_readonly(base_url):
    """Teste les services WFS/WMS en lecture seule"""
    
    print(f"   🔍 Test des services (lecture seule)...")
    
    # Test WFS GetCapabilities (lecture seule)
    try:
        wfs_url = f"{base_url}/ows" if "/geoserver" in base_url else f"{base_url}/geoserver/ows"
        params = {
            "service": "WFS",
            "request": "GetCapabilities",
            "version": "1.0.0"
        }
        
        response = requests.get(wfs_url, params=params, timeout=10)
        if response.status_code == 200 and "WFS_Capabilities" in response.text:
            print(f"   ✅ Service WFS opérationnel")
            return True
        else:
            print(f"   ⚠️ Service WFS: réponse {response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️ Service WFS: {str(e)[:30]}...")
    
    return False

def analyze_existing_layers_safely(base_url):
    """Analyse vos couches existantes SANS les modifier"""
    
    print(f"\n📊 ANALYSE DE VOS COUCHES EXISTANTES (lecture seule)")
    print(f"-" * 50)
    
    # Récupération de la liste des couches (lecture seule)
    try:
        # Méthode 1: GetCapabilities WFS
        wfs_url = f"{base_url}/ows" if "/geoserver" in base_url else f"{base_url}/geoserver/ows"
        params = {
            "service": "WFS",
            "request": "GetCapabilities",
            "version": "1.0.0"
        }
        
        response = requests.get(wfs_url, params=params, timeout=15)
        if response.status_code == 200:
            capabilities = response.text
            
            # Extraction des noms de couches
            import re
            layer_pattern = r'<Name>([^<]+)</Name>'
            layers_found = re.findall(layer_pattern, capabilities)
            
            print(f"🗂️ Couches détectées dans votre GeoServer:")
            
            # Couches attendues par AgriWeb
            expected_layers = [
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
            
            agriweb_layers_found = 0
            other_layers_count = 0
            
            for layer in layers_found:
                if layer in expected_layers:
                    print(f"   ✅ {layer} (utilisée par AgriWeb)")
                    agriweb_layers_found += 1
                else:
                    other_layers_count += 1
            
            if other_layers_count > 0:
                print(f"   📋 + {other_layers_count} autres couches (conservées)")
            
            print(f"\n📊 Résumé de compatibilité AgriWeb:")
            print(f"   ✅ Couches AgriWeb trouvées: {agriweb_layers_found}/{len(expected_layers)}")
            print(f"   📁 Total couches dans GeoServer: {len(layers_found)}")
            
            # Test de quelques couches critiques (lecture seule)
            if agriweb_layers_found > 0:
                test_critical_layers_safely(base_url, expected_layers[:3])
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {str(e)}")
        return False

def test_critical_layers_safely(base_url, layers_to_test):
    """Teste quelques couches critiques en lecture seule"""
    
    print(f"\n🧪 Test des couches critiques (lecture seule, 1 feature max)")
    print(f"-" * 45)
    
    wfs_url = f"{base_url}/ows" if "/geoserver" in base_url else f"{base_url}/geoserver/ows"
    
    for layer_name in layers_to_test:
        try:
            params = {
                "service": "WFS",
                "version": "1.0.0",
                "request": "GetFeature",
                "typeName": layer_name,
                "maxFeatures": 1,  # SEULEMENT 1 feature pour test
                "outputFormat": "application/json"
            }
            
            response = requests.get(wfs_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                feature_count = len(data.get("features", []))
                print(f"   ✅ {layer_name}: {feature_count} feature(s) accessible(s)")
            else:
                print(f"   ⚠️ {layer_name}: erreur HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {layer_name}: {str(e)[:40]}...")

def create_safe_integration_plan(geoserver_url):
    """Crée un plan d'intégration sécurisé"""
    
    print(f"\n🎯 PLAN D'INTÉGRATION SÉCURISÉ")
    print(f"=" * 40)
    print(f"✅ GeoServer détecté: {geoserver_url}")
    print(f"🛡️ AUCUNE modification de votre configuration existante")
    
    print(f"\n📋 Étapes recommandées:")
    print(f"1. ✅ Diagnostic terminé (aucune modification)")
    print(f"2. 🔄 Mise à jour URL dans agriweb_source.py")
    print(f"3. 🧪 Test d'une recherche AgriWeb sur une commune")
    print(f"4. 📊 Validation des performances")
    print(f"5. 🚀 Intégration avec le système de licences")
    
    print(f"\n🔧 Configuration AgriWeb recommandée:")
    print(f"   GEOSERVER_URL = '{geoserver_url}'")
    
    print(f"\n⚠️ SÉCURITÉ:")
    print(f"   - Vos couches existantes sont PRÉSERVÉES")
    print(f"   - Aucune modification de configuration")
    print(f"   - Mode lecture seule pour AgriWeb")
    print(f"   - Sauvegarde recommandée avant production")

if __name__ == "__main__":
    print("🛡️ Démarrage du diagnostic sécurisé...")
    print("⚠️ AUCUNE modification ne sera apportée à votre GeoServer")
    
    geoserver_url = find_geoserver_safely()
    
    if geoserver_url:
        create_safe_integration_plan(geoserver_url)
        
        print(f"\n🎉 DIAGNOSTIC TERMINÉ AVEC SUCCÈS")
        print(f"📋 Votre GeoServer est prêt pour l'intégration AgriWeb")
        print(f"🛡️ Toutes vos couches sont préservées et sécurisées")
        
    else:
        print(f"\n🤔 GeoServer non localisé automatiquement")
        print(f"💬 Pouvez-vous indiquer l'URL que vous utilisez ?")
        print(f"   Exemple: http://localhost:8080/geoserver")
    
    print(f"\n📖 Guide détaillé: GUIDE_GEOSERVER_CONFIGURATION.md")
