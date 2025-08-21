"""
Module de proxy GeoServer sécurisé
Implémente les bonnes pratiques de sécurité recommandées par ChatGPT
"""
import os
import logging
import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urljoin
from flask import request, Response, stream_with_context

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def env_required(name: str) -> str:
    """Récupère une variable d'environnement obligatoire"""
    value = os.getenv(name)
    if not value:
        # En mode développement, on peut être plus permissif
        if os.getenv("ENVIRONMENT") == "development":
            logger.warning(f"Mode développement: Missing required environment variable: {name}")
            # Valeurs par défaut pour le développement local
            defaults = {
                "GEOSERVER_USERNAME": "admin", 
                "GEOSERVER_PASSWORD": "geoserver",
                "GEOSERVER_URL": "http://81.220.178.156:8080/geoserver"
            }
            return defaults.get(name, "")
        else:
            raise RuntimeError(f"Missing required environment variable: {name}")
    return value

# Configuration GeoServer avec variables d'environnement obligatoires
GEOSERVER_URL = env_required("GEOSERVER_URL")
GEOSERVER_USER = env_required("GEOSERVER_USERNAME") 
GEOSERVER_PASS = env_required("GEOSERVER_PASSWORD")
TIMEOUT = (5, 30)  # (connexion, lecture) en secondes

# Log de l'URL sélectionnée au démarrage (recommandation ChatGPT)
logger.info(f"[GeoServer] URL sélectionnée: {GEOSERVER_URL}")
logger.info(f"[GeoServer] Utilisateur: {GEOSERVER_USER}")

# Configuration de la session avec retry
session = requests.Session()
session.auth = HTTPBasicAuth(GEOSERVER_USER, GEOSERVER_PASS)
session.headers.update({"User-Agent": "railway-app/1.0"})

# Configuration des retries (recommandation ChatGPT)
retry_strategy = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

def assert_geoserver_ok(url: str, user: str, pwd: str) -> bool:
    """
    Test de connectivité GeoServer recommandé par ChatGPT
    Évite un "ça marche en local mais pas en prod" silencieux
    """
    try:
        r = requests.get(
            urljoin(url, "/wms"),
            params={"service": "WMS", "request": "GetCapabilities", "version": "1.3.0"},
            auth=HTTPBasicAuth(user, pwd),
            timeout=(5, 20)
        )
        r.raise_for_status()
        assert b"<WMS_Capabilities" in r.content, "Réponse inattendue de GeoServer"
        logger.info(f"[GeoServer] Capabilities OK pour {url}")
        return True
    except Exception as e:
        logger.exception(f"[GeoServer] Échec de connexion à {url}: {e}")
        return False

# Test de connectivité au démarrage (recommandation ChatGPT)
try:
    startup_test = assert_geoserver_ok(GEOSERVER_URL, GEOSERVER_USER, GEOSERVER_PASS)
    if startup_test:
        logger.info(f"[GeoServer] ✅ Connexion validée au démarrage: {GEOSERVER_URL}")
    else:
        logger.error(f"[GeoServer] ❌ ATTENTION: Connexion échouée au démarrage: {GEOSERVER_URL}")
except Exception as e:
    logger.exception(f"[GeoServer] Erreur lors du test de démarrage: {e}")
def check_geoserver(url: str) -> bool:
    """Teste la connexion à GeoServer avec WMS GetCapabilities"""
    try:
        r = session.get(
            urljoin(url, "/wms"),
            params={"service": "WMS", "request": "GetCapabilities", "version": "1.3.0"},
            timeout=TIMEOUT,
        )
        return r.ok and b"<WMS_Capabilities" in r.content
    except Exception as e:
        logger.warning(f"GeoServer check failed for {url}: {e}")
        return False

# URL GeoServer active (utilise directement la variable d'environnement sécurisée)
ACTIVE_GEOSERVER_URL = GEOSERVER_URL

def get_geoserver_info():
    """Retourne les informations de configuration GeoServer"""
    return {
        "url": ACTIVE_GEOSERVER_URL,
        "username": GEOSERVER_USER,
        "timeout": TIMEOUT,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

def test_geoserver_connection():
    """Teste la connexion au GeoServer actif"""
    return check_geoserver(ACTIVE_GEOSERVER_URL)

def create_wms_proxy(app):
    """Crée le proxy WMS sécurisé"""
    @app.route("/proxy/wms")
    def proxy_wms():
        """Proxy WMS pour tiles/rasters"""
        upstream = urljoin(ACTIVE_GEOSERVER_URL, "/wms")
        
        # Whitelist des paramètres autorisés
        allowed_params = [
            'SERVICE', 'VERSION', 'REQUEST', 'LAYERS', 'STYLES',
            'CRS', 'BBOX', 'WIDTH', 'HEIGHT', 'FORMAT',
            'TRANSPARENT', 'BGCOLOR', 'EXCEPTIONS', 'TIME',
            'ELEVATION', 'SLD', 'SLD_BODY'
        ]
        
        # Filtrer les paramètres
        filtered_params = {
            k.upper(): v for k, v in request.args.items() 
            if k.upper() in allowed_params
        }
        
        try:
            def generate():
                with session.get(upstream, params=filtered_params, timeout=TIMEOUT, stream=True) as r:
                    r.raise_for_status()
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk
            
            return Response(
                stream_with_context(generate()),
                headers={
                    "Cache-Control": "public, max-age=300",
                    "Access-Control-Allow-Origin": "*"
                },
                mimetype="image/png"
            )
        except Exception as e:
            logger.error(f"WMS Proxy error: {e}")
            return {"error": "WMS service unavailable"}, 503

def create_wfs_proxy(app):
    """Crée le proxy WFS sécurisé"""
    @app.route("/proxy/wfs")
    def proxy_wfs():
        """Proxy WFS pour GeoJSON"""
        upstream = urljoin(ACTIVE_GEOSERVER_URL, "/wfs")
        
        # Whitelist des paramètres autorisés
        allowed_params = [
            'SERVICE', 'VERSION', 'REQUEST', 'TYPENAME', 'TYPENAMES',
            'OUTPUTFORMAT', 'MAXFEATURES', 'STARTINDEX', 'COUNT',
            'BBOX', 'CRS', 'SRSNAME', 'FILTER', 'CQL_FILTER',
            'PROPERTYNAME', 'SORTBY', 'FEATUREID'
        ]
        
        # Filtrer les paramètres
        filtered_params = {
            k.upper(): v for k, v in request.args.items() 
            if k.upper() in allowed_params
        }
        
        # Limiter le nombre de features
        if 'MAXFEATURES' not in filtered_params:
            filtered_params['MAXFEATURES'] = '1000'
        
        try:
            r = session.get(upstream, params=filtered_params, timeout=TIMEOUT)
            r.raise_for_status()
            
            return Response(
                r.content,
                mimetype="application/json",
                headers={
                    "Cache-Control": "public, max-age=60",
                    "Access-Control-Allow-Origin": "*"
                }
            )
        except Exception as e:
            logger.error(f"WFS Proxy error: {e}")
            return {"error": "WFS service unavailable"}, 503

def create_capabilities_proxy(app):
    """Crée le proxy pour les capabilities"""
    @app.route("/proxy/capabilities")
    def proxy_capabilities():
        """Proxy pour GetCapabilities (WMS et WFS)"""
        service = request.args.get('service', 'WMS').upper()
        
        if service not in ['WMS', 'WFS']:
            return {"error": "Service must be WMS or WFS"}, 400
        
        upstream = urljoin(ACTIVE_GEOSERVER_URL, f"/{service.lower()}")
        params = {
            'service': service,
            'request': 'GetCapabilities',
            'version': '1.3.0' if service == 'WMS' else '2.0.0'
        }
        
        try:
            r = session.get(upstream, params=params, timeout=TIMEOUT)
            r.raise_for_status()
            
            content_type = "application/xml" if service == 'WMS' else "application/xml"
            
            return Response(
                r.content,
                mimetype=content_type,
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*"
                }
            )
        except Exception as e:
            logger.error(f"Capabilities Proxy error: {e}")
            return {"error": f"{service} capabilities unavailable"}, 503

def init_geoserver_proxies(app):
    """Initialise tous les proxies GeoServer"""
    logger.info(f"🔧 Initialisation des proxies GeoServer")
    logger.info(f"   - URL active: {ACTIVE_GEOSERVER_URL}")
    logger.info(f"   - Utilisateur: {GEOSERVER_USER}")
    logger.info(f"   - Timeout: {TIMEOUT}")
    
    # Créer les proxies
    create_wms_proxy(app)
    create_wfs_proxy(app)
    create_capabilities_proxy(app)
    
    # Route de test
    @app.route("/proxy/test")
    def proxy_test():
        """Test des proxies GeoServer"""
        info = get_geoserver_info()
        connection_ok = test_geoserver_connection()
        
        return {
            "geoserver_info": info,
            "connection_test": "✅ OK" if connection_ok else "❌ FAILED",
            "proxies": {
                "wms": "/proxy/wms",
                "wfs": "/proxy/wfs", 
                "capabilities": "/proxy/capabilities"
            }
        }
    
    logger.info("✅ Proxies GeoServer initialisés")
    return True

# Export des fonctions principales
__all__ = [
    'init_geoserver_proxies',
    'get_geoserver_info', 
    'test_geoserver_connection',
    'ACTIVE_GEOSERVER_URL',
    'check_geoserver'
]

def test_geoserver_connection():
    """Test simple de la connexion GeoServer"""
    return check_geoserver(GEOSERVER_URL)
