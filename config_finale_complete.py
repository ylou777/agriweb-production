#!/usr/bin/env python3
"""
🎯 CONFIGURATION FINALE GEOSERVER + FLASK
Intégration complète pour votre application AgriWeb
"""

# ✅ GEOSERVER RAILWAY - PRODUCTION
GEOSERVER_URL = "https://geoserver-agriweb-production.up.railway.app"
GEOSERVER_USER = "admin"
GEOSERVER_PASSWORD = "admin123"

# Services GeoServer
GEOSERVER_WMS = f"{GEOSERVER_URL}/geoserver/ows"
GEOSERVER_WFS = f"{GEOSERVER_URL}/geoserver/ows"
GEOSERVER_REST = f"{GEOSERVER_URL}/geoserver/rest"
GEOSERVER_ADMIN = f"{GEOSERVER_URL}/geoserver/web/"

# Configuration Flask pour GeoServer
class GeoServerConfig:
    """Configuration GeoServer pour Flask"""
    
    BASE_URL = GEOSERVER_URL
    USERNAME = GEOSERVER_USER
    PASSWORD = GEOSERVER_PASSWORD
    
    # Services
    WMS_URL = GEOSERVER_WMS
    WFS_URL = GEOSERVER_WFS
    REST_API = GEOSERVER_REST
    
    # Headers par défaut
    HEADERS = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Timeouts
    REQUEST_TIMEOUT = 30
    UPLOAD_TIMEOUT = 300  # 5 minutes pour upload de données
    
    @classmethod
    def get_auth(cls):
        """Retourne l'authentification pour requests"""
        return (cls.USERNAME, cls.PASSWORD)
    
    @classmethod
    def test_connection(cls):
        """Tester la connexion GeoServer"""
        import requests
        try:
            response = requests.get(
                f"{cls.REST_API}/workspaces",
                auth=cls.get_auth(),
                timeout=cls.REQUEST_TIMEOUT
            )
            return response.status_code == 200
        except:
            return False

# Fonctions utilitaires pour Flask
def get_layer_wms_url(layer_name, workspace="topp"):
    """Générer URL WMS pour une couche"""
    return f"{GEOSERVER_WMS}?service=WMS&version=1.3.0&request=GetMap&layers={workspace}:{layer_name}&styles=&bbox={{bbox}}&width={{width}}&height={{height}}&srs=EPSG:4326&format=image/png"

def get_layer_wfs_url(layer_name, workspace="topp"):
    """Générer URL WFS pour une couche"""
    return f"{GEOSERVER_WFS}?service=WFS&version=2.0.0&request=GetFeature&typeName={workspace}:{layer_name}&outputFormat=application/json"

def create_workspace(workspace_name):
    """Créer un workspace via API REST"""
    import requests
    
    url = f"{GEOSERVER_REST}/workspaces"
    data = {
        "workspace": {
            "name": workspace_name
        }
    }
    
    response = requests.post(
        url,
        json=data,
        auth=GeoServerConfig.get_auth(),
        headers=GeoServerConfig.HEADERS,
        timeout=GeoServerConfig.REQUEST_TIMEOUT
    )
    
    return response.status_code in [200, 201]

# Configuration complète pour agriweb_source.py
AGRIWEB_GEOSERVER_CONFIG = {
    'geoserver_url': GEOSERVER_URL,
    'geoserver_user': GEOSERVER_USER,
    'geoserver_password': GEOSERVER_PASSWORD,
    'wms_url': GEOSERVER_WMS,
    'wfs_url': GEOSERVER_WFS,
    'default_workspace': 'agriweb',
    'default_srs': 'EPSG:4326'
}

# 💰 Informations de coût
COST_INFO = {
    'platform': 'Railway Pro',
    'monthly_cost_usd': 45,  # Estimation avec 100 Go
    'storage_cost_per_gb': 0.15,
    'data_volume_gb': 100,
    'total_storage_cost': 100 * 0.15,  # $15/mois
    'base_plan_cost': 20,  # $20/mois minimum
    'estimated_total': 45,  # $20 + $15 + utilisation
    'migration_savings': 35  # Économie possible avec Cloud Run
}

# 🔄 Préparation migration future
MIGRATION_PLAN = {
    'current_platform': 'Railway',
    'target_platform': 'Google Cloud Run',
    'migration_script': 'migrate_to_cloud_run_later.py',
    'estimated_savings_monthly': COST_INFO['migration_savings'],
    'migration_timeline': '3-6 months after launch'
}

if __name__ == "__main__":
    print("🎯 CONFIGURATION GEOSERVER RAILWAY")
    print("=" * 50)
    print(f"🌐 URL: {GEOSERVER_URL}")
    print(f"👤 Admin: {GEOSERVER_USER} / {GEOSERVER_PASSWORD}")
    print(f"🗺️ WMS: {GEOSERVER_WMS}")
    print(f"📊 WFS: {GEOSERVER_WFS}")
    print(f"🔧 REST: {GEOSERVER_REST}")
    print(f"💰 Coût estimé: ${COST_INFO['estimated_total']}/mois")
    print()
    
    # Test de connexion
    print("🧪 Test de connexion...")
    if GeoServerConfig.test_connection():
        print("✅ GeoServer accessible!")
    else:
        print("⏳ GeoServer en cours de démarrage...")
    
    print("\n📋 Prochaines étapes:")
    print("1. Attendre le démarrage complet de GeoServer")
    print("2. Créer workspace 'agriweb'")
    print("3. Importer vos 100 Go de données")
    print("4. Intégrer dans votre application Flask")
    print("5. Tests et mise en production!")
