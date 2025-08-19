#!/usr/bin/env python3
"""
Script de Migration vers GeoServer Centralisé Puissant
AgriWeb 2.0 - Configuration Production

Ce script adapte votre configuration locale vers un GeoServer centralisé haute performance.
"""

import os
import json
import requests
from urllib.parse import urljoin
from typing import Dict, List, Optional

class GeoServerMigrator:
    """Gestionnaire de migration vers GeoServer centralisé"""
    
    def __init__(self):
        # Configuration actuelle (localhost)
        self.current_config = {
            'url': 'http://localhost:8080/geoserver',
            'workspace': 'gpu',
            'layers': [
                'prefixes_sections',
                'poste_elec_shapefile', 
                'gpu1',
                'PARCELLE2024',
                'postes-electriques-rte',
                'CapacitesDAccueil',
                'parkings_sup500m2',
                'friches-standard',
                'POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93',
                'ZAER_ARRETE_SHP_FRA',
                'PARCELLES_GRAPHIQUES',
                'GeolocalisationEtablissement_Sirene france',
                'etablissements_eleveurs',
                'ppri'
            ]
        }
        
        # Configuration cible (production)
        self.target_config = {
            'url': os.getenv('GEOSERVER_PROD_URL', 'https://geoserver.agriweb.com/geoserver'),
            'workspace': 'agriweb_public',
            'timeout': 30,
            'max_features': 10000,
            'cache_ttl': 3600
        }
        
        self.migration_report = {
            'layers_tested': [],
            'layers_ok': [],
            'layers_failed': [],
            'performance_metrics': {}
        }
    
    def test_current_geoserver(self) -> Dict:
        """Test de l'installation GeoServer actuelle"""
        print("🔍 Test du GeoServer actuel (localhost:8080)...")
        
        test_results = {
            'accessible': False,
            'layers_count': 0,
            'layers_details': [],
            'performance': {}
        }
        
        try:
            # Test connectivité de base
            response = requests.get(
                f"{self.current_config['url']}/rest/about/version.json",
                timeout=10
            )
            
            if response.status_code == 200:
                test_results['accessible'] = True
                version_info = response.json()
                print(f"✅ GeoServer accessible - Version: {version_info.get('about', {}).get('version', 'Inconnue')}")
                
                # Test de chaque couche
                for layer in self.current_config['layers']:
                    layer_test = self.test_layer_current(layer)
                    test_results['layers_details'].append(layer_test)
                    if layer_test['accessible']:
                        test_results['layers_count'] += 1
                
                print(f"📊 {test_results['layers_count']}/{len(self.current_config['layers'])} couches accessibles")
                
        except Exception as e:
            print(f"❌ Erreur connexion GeoServer local: {e}")
        
        return test_results
    
    def test_layer_current(self, layer_name: str) -> Dict:
        """Test d'une couche spécifique sur GeoServer actuel"""
        layer_result = {
            'name': layer_name,
            'accessible': False,
            'feature_count': 0,
            'response_time_ms': None,
            'error': None
        }
        
        try:
            import time
            start_time = time.time()
            
            # Test WFS GetFeature avec bbox France
            wfs_url = f"{self.current_config['url']}/{self.current_config['workspace']}/ows"
            params = {
                'service': 'WFS',
                'version': '2.0.0',
                'request': 'GetFeature',
                'typeName': f"{self.current_config['workspace']}:{layer_name}",
                'outputFormat': 'application/json',
                'maxFeatures': 10,
                'bbox': '-5,42,9,51,EPSG:4326'  # Bbox France approximatif
            }
            
            response = requests.get(wfs_url, params=params, timeout=15)
            end_time = time.time()
            
            layer_result['response_time_ms'] = round((end_time - start_time) * 1000, 2)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    features = data.get('features', [])
                    layer_result['feature_count'] = len(features)
                    layer_result['accessible'] = True
                    print(f"  ✅ {layer_name}: {len(features)} features en {layer_result['response_time_ms']}ms")
                except:
                    layer_result['error'] = "Réponse non-JSON"
                    print(f"  ⚠️ {layer_name}: Réponse non-JSON")
            else:
                layer_result['error'] = f"HTTP {response.status_code}"
                print(f"  ❌ {layer_name}: HTTP {response.status_code}")
                
        except Exception as e:
            layer_result['error'] = str(e)
            print(f"  ❌ {layer_name}: {e}")
        
        return layer_result
    
    def generate_production_config(self) -> str:
        """Génère la configuration Python pour la production"""
        
        config_code = f'''"""
Configuration GeoServer Production pour AgriWeb 2.0
Générée automatiquement par le script de migration
"""

import os
import requests
from urllib.parse import quote
from typing import Dict, List, Optional

class ProductionGeoServerConfig:
    """Configuration GeoServer centralisé haute performance"""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        
        # URLs selon l'environnement
        if environment == "development":
            self.base_url = "http://localhost:8080/geoserver"
            self.workspace = "gpu"
        else:  # production
            self.base_url = os.getenv('GEOSERVER_URL', '{self.target_config["url"]}')
            self.workspace = os.getenv('GEOSERVER_WORKSPACE', '{self.target_config["workspace"]}')
        
        # Paramètres de performance
        self.timeout = {self.target_config["timeout"]}
        self.max_features = {self.target_config["max_features"]}
        self.cache_ttl = {self.target_config["cache_ttl"]}
        
        # URLs construites
        self.wfs_url = f"{{self.base_url}}/{{self.workspace}}/ows"
        self.wms_url = f"{{self.base_url}}/{{self.workspace}}/wms"
        
        # Mapping des couches (ancien nom -> nouveau nom si différent)
        self.layer_mapping = {{
            # Couches cadastrales
            "prefixes_sections": "cadastre_sections",
            "PARCELLE2024": "parcelles_agricoles",
            
            # Infrastructure électrique  
            "poste_elec_shapefile": "postes_bt",
            "postes-electriques-rte": "postes_hta", 
            "CapacitesDAccueil": "capacites_accueil",
            
            # Urbanisme
            "gpu1": "plu_zones",
            
            # Autres couches (nom inchangé)
            "parkings_sup500m2": "parkings_sup500m2",
            "friches-standard": "friches_standard", 
            "POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93": "potentiel_solaire",
            "ZAER_ARRETE_SHP_FRA": "zaer_zones",
            "PARCELLES_GRAPHIQUES": "rpg_parcelles",
            "GeolocalisationEtablissement_Sirene france": "sirene_etablissements",
            "etablissements_eleveurs": "eleveurs",
            "ppri": "ppri_zones"
        }}
    
    def get_layer_name(self, old_layer_name: str) -> str:
        """Retourne le nom de couche pour la production"""
        return self.layer_mapping.get(old_layer_name, old_layer_name)
    
    def get_wfs_params(self, layer_name: str, bbox: str, max_features: Optional[int] = None) -> Dict:
        """Paramètres WFS optimisés pour production"""
        production_layer = self.get_layer_name(layer_name)
        
        return {{
            'service': 'WFS',
            'version': '2.0.0',
            'request': 'GetFeature',
            'typeName': f"{{self.workspace}}:{{production_layer}}",
            'outputFormat': 'application/json',
            'bbox': bbox,
            'srsname': 'EPSG:4326',
            'maxFeatures': max_features or self.max_features,
            'startIndex': 0,
            'resultType': 'results'
        }}
    
    def create_session(self) -> requests.Session:
        """Session HTTP optimisée"""
        session = requests.Session()
        session.headers.update({{
            'User-Agent': 'AgriWeb-2.0-Production',
            'Accept': 'application/json',
            'Cache-Control': f'max-age={{self.cache_ttl}}'
        }})
        return session

# Instance globale de configuration
geoserver_config = ProductionGeoServerConfig()

def fetch_wfs_data_production(layer_name: str, bbox: str, max_features: Optional[int] = None) -> List[Dict]:
    """
    Fonction de remplacement pour fetch_wfs_data optimisée production
    
    Args:
        layer_name: Nom de la couche (ancien format accepté)
        bbox: Bounding box au format "minx,miny,maxx,maxy,EPSG:4326" 
        max_features: Limite du nombre de features
    
    Returns:
        Liste des features GeoJSON
    """
    session = geoserver_config.create_session()
    params = geoserver_config.get_wfs_params(layer_name, bbox, max_features)
    
    try:
        response = session.get(
            geoserver_config.wfs_url,
            params=params,
            timeout=geoserver_config.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        features = data.get('features', [])
        
        print(f"[GEOSERVER] {{layer_name}} -> {{len(features)}} features en {{response.elapsed.total_seconds():.2f}}s")
        return features
        
    except requests.exceptions.Timeout:
        print(f"[TIMEOUT] GeoServer timeout pour {{layer_name}} ({{geoserver_config.timeout}}s)")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"[HTTP_ERROR] {{e.response.status_code}} pour {{layer_name}}")
        return []
    except Exception as e:
        print(f"[ERROR] Erreur GeoServer {{layer_name}}: {{e}}")
        return []

# Aliases pour compatibilité avec le code existant
def fetch_wfs_data(layer_name: str, bbox: str, srsname: str = "EPSG:4326") -> List[Dict]:
    """Fonction de compatibilité avec l'ancien code"""
    return fetch_wfs_data_production(layer_name, bbox)

# Variables de compatibilité
GEOSERVER_URL = geoserver_config.base_url
GEOSERVER_WFS_URL = geoserver_config.wfs_url

# Constantes couches mises à jour
CADASTRE_LAYER = geoserver_config.get_layer_name("prefixes_sections")
POSTE_LAYER = geoserver_config.get_layer_name("poste_elec_shapefile")
PLU_LAYER = geoserver_config.get_layer_name("gpu1")
PARCELLE_LAYER = geoserver_config.get_layer_name("PARCELLE2024")
HT_POSTE_LAYER = geoserver_config.get_layer_name("postes-electriques-rte")
CAPACITES_RESEAU_LAYER = geoserver_config.get_layer_name("CapacitesDAccueil")
PARKINGS_LAYER = geoserver_config.get_layer_name("parkings_sup500m2")
FRICHES_LAYER = geoserver_config.get_layer_name("friches-standard")
POTENTIEL_SOLAIRE_LAYER = geoserver_config.get_layer_name("POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93")
ZAER_LAYER = geoserver_config.get_layer_name("ZAER_ARRETE_SHP_FRA")
PARCELLES_GRAPHIQUES_LAYER = geoserver_config.get_layer_name("PARCELLES_GRAPHIQUES")
SIRENE_LAYER = geoserver_config.get_layer_name("GeolocalisationEtablissement_Sirene france")
ELEVEURS_LAYER = geoserver_config.get_layer_name("etablissements_eleveurs")
PPRI_LAYER = geoserver_config.get_layer_name("ppri")
'''
        return config_code
    
    def create_migration_patch(self) -> str:
        """Crée un patch pour agriweb_source.py"""
        
        patch_code = '''"""
Patch de Migration GeoServer Production
À appliquer sur agriweb_source.py

Instructions:
1. Sauvegarder agriweb_source.py original
2. Remplacer la section de configuration GeoServer
3. Tester avec la variable d'environnement GEOSERVER_URL
"""

# === DÉBUT REMPLACEMENT ===
# Remplacer les lignes 359-377 dans agriweb_source.py par:

# Configuration GeoServer (Production Ready)
from config_geoserver_production import (
    geoserver_config,
    fetch_wfs_data_production as fetch_wfs_data,
    GEOSERVER_URL,
    GEOSERVER_WFS_URL,
    CADASTRE_LAYER,
    POSTE_LAYER,
    PLU_LAYER,
    PARCELLE_LAYER,
    HT_POSTE_LAYER,
    CAPACITES_RESEAU_LAYER,
    PARKINGS_LAYER,
    FRICHES_LAYER,
    POTENTIEL_SOLAIRE_LAYER,
    ZAER_LAYER,
    PARCELLES_GRAPHIQUES_LAYER,
    SIRENE_LAYER,
    ELEVEURS_LAYER,
    PPRI_LAYER
)

# === FIN REMPLACEMENT ===

# Pour tester localement (développement):
# export GEOSERVER_URL="http://localhost:8080/geoserver"

# Pour production:
# export GEOSERVER_URL="https://geoserver.agriweb.com/geoserver"
# export GEOSERVER_WORKSPACE="agriweb_public"
'''
        return patch_code
    
    def run_migration_report(self) -> Dict:
        """Exécute le rapport complet de migration"""
        print("🚀 RAPPORT DE MIGRATION GEOSERVER AGRIWEB 2.0")
        print("=" * 60)
        
        # Test de l'existant
        current_test = self.test_current_geoserver()
        
        # Génération des fichiers
        print("\\n📝 Génération des fichiers de configuration...")
        
        # Sauvegarde config production
        production_config = self.generate_production_config()
        with open('config_geoserver_production.py', 'w', encoding='utf-8') as f:
            f.write(production_config)
        print("✅ config_geoserver_production.py créé")
        
        # Sauvegarde patch
        patch_content = self.create_migration_patch()
        with open('migration_geoserver_patch.txt', 'w', encoding='utf-8') as f:
            f.write(patch_content)
        print("✅ migration_geoserver_patch.txt créé")
        
        # Rapport final
        report = {
            'current_geoserver': current_test,
            'target_config': self.target_config,
            'migration_files': [
                'config_geoserver_production.py',
                'migration_geoserver_patch.txt'
            ],
            'next_steps': [
                "1. Déployer GeoServer production sur " + self.target_config['url'],
                "2. Importer toutes les couches testées",
                "3. Appliquer le patch sur agriweb_source.py", 
                "4. Tester avec GEOSERVER_URL en variable d'environnement",
                "5. Déployer en production"
            ]
        }
        
        print("\\n📊 RÉSUMÉ:")
        print(f"  • GeoServer local: {'✅ Accessible' if current_test['accessible'] else '❌ Non accessible'}")
        print(f"  • Couches OK: {current_test['layers_count']}/{len(self.current_config['layers'])}")
        print(f"  • Configuration cible: {self.target_config['url']}")
        
        print("\\n🎯 PROCHAINES ÉTAPES:")
        for i, step in enumerate(report['next_steps'], 1):
            print(f"  {i}. {step}")
        
        return report

if __name__ == "__main__":
    migrator = GeoServerMigrator()
    report = migrator.run_migration_report()
    
    # Sauvegarde rapport JSON
    with open('migration_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("\\n💾 Rapport complet sauvé dans migration_report.json")
