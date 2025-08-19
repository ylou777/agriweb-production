"""
Configuration GeoServer Production Adaptable pour AgriWeb 2.0
Permet de basculer facilement entre environnement local et production centralisée
"""

import os
import requests
from urllib.parse import quote
from typing import Dict, List, Optional
import time

class AgriWebGeoServerConfig:
    """Configuration GeoServer flexible pour AgriWeb 2.0"""
    
    def __init__(self):
        # Détection automatique de l'environnement
        self.environment = os.getenv('AGRIWEB_ENV', 'development')
        
        # Configuration selon l'environnement
        if self.environment == 'production':
            self.base_url = os.getenv('GEOSERVER_URL', 'https://geoserver.agriweb.com/geoserver')
            self.workspace = os.getenv('GEOSERVER_WORKSPACE', 'agriweb_public')
            self.timeout = 30
            self.max_features = 10000
        else:  # development
            self.base_url = os.getenv('GEOSERVER_URL', 'http://localhost:8080/geoserver')
            self.workspace = os.getenv('GEOSERVER_WORKSPACE', 'gpu')
            self.timeout = 10
            self.max_features = 1000
        
        # URLs construites
        self.wfs_url = f"{self.base_url}/{self.workspace}/ows"
        self.wms_url = f"{self.base_url}/{self.workspace}/wms"
        
        # Configuration cache
        self.cache_ttl = 3600  # 1 heure
        
        # Mapping des couches (flexibilité nom ancien -> nouveau)
        self.layer_mapping = {
            # Couches cadastrales
            "prefixes_sections": "cadastre_sections",
            "PARCELLE2024": "parcelles_agricoles",
            
            # Infrastructure électrique  
            "poste_elec_shapefile": "postes_bt",
            "postes-electriques-rte": "postes_hta", 
            "CapacitesDAccueil": "capacites_accueil",
            
            # Urbanisme et réglementations
            "gpu1": "plu_zones",
            "ppri": "ppri_zones",
            "ZAER_ARRETE_SHP_FRA": "zaer_zones",
            
            # Activités économiques
            "parkings_sup500m2": "parkings",
            "friches-standard": "friches", 
            "POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93": "potentiel_solaire",
            
            # Données agricoles
            "PARCELLES_GRAPHIQUES": "rpg_parcelles",
            "etablissements_eleveurs": "eleveurs",
            
            # Données d'entreprises
            "GeolocalisationEtablissement_Sirene france": "sirene_etablissements"
        }
        
        print(f"🗺️ GeoServer configuré: {self.environment} - {self.base_url}")
    
    def get_layer_name(self, layer_name: str) -> str:
        """Retourne le nom de couche adapté à l'environnement"""
        if self.environment == 'production':
            return self.layer_mapping.get(layer_name, layer_name)
        else:
            # En développement, garde les noms originaux
            return layer_name
    
    def create_optimized_session(self) -> requests.Session:
        """Crée une session HTTP optimisée pour GeoServer"""
        session = requests.Session()
        
        # Headers optimisés
        session.headers.update({
            'User-Agent': f'AgriWeb-2.0-{self.environment}',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # Configuration cache selon environnement
        if self.environment == 'production':
            session.headers['Cache-Control'] = f'max-age={self.cache_ttl}'
        
        return session
    
    def build_wfs_params(self, layer_name: str, bbox: str, max_features: Optional[int] = None, **kwargs) -> Dict:
        """Construit les paramètres WFS optimisés"""
        layer_prod = self.get_layer_name(layer_name)
        
        params = {
            'service': 'WFS',
            'version': '2.0.0',
            'request': 'GetFeature',
            'typeName': f"{self.workspace}:{layer_prod}",
            'outputFormat': 'application/json',
            'bbox': bbox,
            'srsname': kwargs.get('srsname', 'EPSG:4326'),
            'maxFeatures': max_features or self.max_features
        }
        
        # Paramètres additionnels selon environnement
        if self.environment == 'production':
            params.update({
                'startIndex': kwargs.get('startIndex', 0),
                'resultType': 'results'
            })
        
        return params
    
    def fetch_layer_data(self, layer_name: str, bbox: str, max_features: Optional[int] = None, **kwargs) -> List[Dict]:
        """
        Fonction principale pour récupérer les données d'une couche
        
        Args:
            layer_name: Nom de la couche (ancien format accepté)
            bbox: Bounding box "minx,miny,maxx,maxy,EPSG:4326"
            max_features: Limite nombre de features
            **kwargs: Paramètres additionnels (srsname, etc.)
        
        Returns:
            Liste des features GeoJSON
        """
        session = self.create_optimized_session()
        params = self.build_wfs_params(layer_name, bbox, max_features, **kwargs)
        
        start_time = time.time()
        
        try:
            response = session.get(
                self.wfs_url,
                params=params,
                timeout=self.timeout
            )
            
            response_time = round((time.time() - start_time) * 1000, 2)
            response.raise_for_status()
            
            # Parsing JSON
            data = response.json()
            features = data.get('features', [])
            
            # Log performance
            layer_display = self.get_layer_name(layer_name)
            print(f"[{self.environment.upper()}] {layer_display}: {len(features)} features en {response_time}ms")
            
            return features
            
        except requests.exceptions.Timeout:
            print(f"[TIMEOUT] {layer_name} - Timeout après {self.timeout}s")
            return []
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            print(f"[HTTP_{status_code}] {layer_name} - Erreur serveur")
            return []
            
        except requests.exceptions.RequestException as e:
            print(f"[NETWORK_ERROR] {layer_name} - {str(e)[:100]}")
            return []
            
        except Exception as e:
            print(f"[ERROR] {layer_name} - {str(e)[:100]}")
            return []
    
    def test_connectivity(self) -> Dict:
        """Test de connectivité et performance du GeoServer"""
        print(f"🔍 Test de connectivité {self.environment}: {self.base_url}")
        
        test_result = {
            'accessible': False,
            'response_time_ms': None,
            'version': None,
            'workspace_exists': False,
            'error': None
        }
        
        try:
            # Test version GeoServer
            start_time = time.time()
            response = requests.get(
                f"{self.base_url}/rest/about/version.json",
                timeout=10
            )
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                test_result['accessible'] = True
                test_result['response_time_ms'] = response_time
                
                version_data = response.json()
                test_result['version'] = version_data.get('about', {}).get('version', 'Inconnue')
                
                print(f"✅ GeoServer accessible en {response_time}ms - Version: {test_result['version']}")
                
                # Test workspace
                ws_response = requests.get(
                    f"{self.base_url}/rest/workspaces/{self.workspace}.json",
                    timeout=5
                )
                test_result['workspace_exists'] = (ws_response.status_code == 200)
                
                if test_result['workspace_exists']:
                    print(f"✅ Workspace '{self.workspace}' accessible")
                else:
                    print(f"⚠️ Workspace '{self.workspace}' non trouvé (sera créé en production)")
                    
            else:
                test_result['error'] = f"HTTP {response.status_code}"
                print(f"❌ GeoServer non accessible: HTTP {response.status_code}")
                
        except Exception as e:
            test_result['error'] = str(e)
            print(f"❌ Erreur connexion: {e}")
        
        return test_result

# Instance globale de configuration
geoserver = AgriWebGeoServerConfig()

# Fonctions de compatibilité avec le code existant
def fetch_wfs_data(layer_name: str, bbox: str, srsname: str = "EPSG:4326") -> List[Dict]:
    """Fonction de compatibilité avec agriweb_source.py"""
    return geoserver.fetch_layer_data(layer_name, bbox, srsname=srsname)

# Export des variables pour compatibilité
GEOSERVER_URL = geoserver.base_url
GEOSERVER_WFS_URL = geoserver.wfs_url

# Constantes de couches (adaptées automatiquement à l'environnement)
CADASTRE_LAYER = geoserver.get_layer_name("prefixes_sections")
POSTE_LAYER = geoserver.get_layer_name("poste_elec_shapefile")
PLU_LAYER = geoserver.get_layer_name("gpu1")
PARCELLE_LAYER = geoserver.get_layer_name("PARCELLE2024")
HT_POSTE_LAYER = geoserver.get_layer_name("postes-electriques-rte")
CAPACITES_RESEAU_LAYER = geoserver.get_layer_name("CapacitesDAccueil")
PARKINGS_LAYER = geoserver.get_layer_name("parkings_sup500m2")
FRICHES_LAYER = geoserver.get_layer_name("friches-standard")
POTENTIEL_SOLAIRE_LAYER = geoserver.get_layer_name("POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93")
ZAER_LAYER = geoserver.get_layer_name("ZAER_ARRETE_SHP_FRA")
PARCELLES_GRAPHIQUES_LAYER = geoserver.get_layer_name("PARCELLES_GRAPHIQUES")
SIRENE_LAYER = geoserver.get_layer_name("GeolocalisationEtablissement_Sirene france")
ELEVEURS_LAYER = geoserver.get_layer_name("etablissements_eleveurs")
PPRI_LAYER = geoserver.get_layer_name("ppri")

if __name__ == "__main__":
    # Test de connectivité au démarrage
    test_result = geoserver.test_connectivity()
    
    if test_result['accessible']:
        print("\n🎯 Configuration prête pour AgriWeb 2.0!")
        print(f"Environment: {geoserver.environment}")
        print(f"Workspace: {geoserver.workspace}")
        print(f"Timeout: {geoserver.timeout}s")
        print(f"Max features: {geoserver.max_features}")
    else:
        print(f"\n⚠️ GeoServer non accessible: {test_result.get('error', 'Erreur inconnue')}")
        print("Vérifiez que GeoServer est démarré ou configurez GEOSERVER_URL")
