# ── Google Solar API ──────────────────────────────────────────────────────────
import os as _os
GOOGLE_SOLAR_API_KEY = _os.environ.get('GOOGLE_SOLAR_API_KEY', 'AIzaSyCzZGqZYWJe2O-hGDBAbUv68c3URzEkZmw')

# ── Email OVH (Flask-Mail) ────────────────────────────────────────────────────
MAIL_SERVER   = _os.environ.get('MAIL_SERVER',   'smtp.mail.ovh.net')
MAIL_PORT     = int(_os.environ.get('MAIL_PORT', '587'))
MAIL_USE_TLS  = True
MAIL_USE_SSL  = False
MAIL_USERNAME = _os.environ.get('MAIL_USERNAME', '')   # ex: contact@heliapv.fr
MAIL_PASSWORD = _os.environ.get('MAIL_PASSWORD', '')
MAIL_DEFAULT_SENDER = _os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

# ── Enedis Data Connect (OAuth 2.0 – courbes de charge Linky) ─────────────────
# Inscription préalable sur https://datahub-enedis.fr/fournisseurs-de-services/
# Les credentiels sont fournis par Enedis après validation de votre dossier.
# ENEDIS_REDIRECT_URI doit être enregistrée dans votre compte Enedis (ex: https://votre-domaine.fr/api/enedis/dc/callback)
ENEDIS_CLIENT_ID     = _os.environ.get('ENEDIS_CLIENT_ID', '')
ENEDIS_CLIENT_SECRET = _os.environ.get('ENEDIS_CLIENT_SECRET', '')
ENEDIS_REDIRECT_URI  = _os.environ.get('ENEDIS_REDIRECT_URI', '')
ENEDIS_SANDBOX       = _os.environ.get('ENEDIS_SANDBOX', 'true').lower() == 'true'

# ── Configuration GeoServer ───────────────────────────────────────────────────
# Configuration pour le serveur GeoServer
# URL locale pour développement
GEOSERVER_URL_LOCAL = "http://localhost:8080/geoserver"

# URL de production (à configurer selon votre hébergement)
GEOSERVER_URL_PRODUCTION = "https://geoserver-agriweb.up.railway.app/geoserver"

# Détection automatique de l'environnement
import os
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

# Configuration GeoServer selon l'environnement
def get_geoserver_url():
    if ENVIRONMENT == 'production':
        return GEOSERVER_URL_PRODUCTION
    else:
        return GEOSERVER_URL_LOCAL

GEOSERVER_URL = get_geoserver_url()

print(f"🗺️ [GEOSERVER] Environnement: {ENVIRONMENT}")
print(f"🔗 [GEOSERVER] URL: {GEOSERVER_URL}")

# Couches GeoServer (à adapter à votre configuration réelle)
CADASTRE_LAYER = "gpu:prefixes_sections"
POSTE_LAYER = "gpu:poste_elec_shapefile"
PLU_LAYER = "gpu:gpu1"
PARCELLE_LAYER = "gpu:PARCELLE2024"

# URL de l'API Carto (IGN ou autre)
API_CARTO_URL = "https://apicarto.ign.fr/api/gpu"

# Chemin vers le fichier CSV contenant les données des agriculteurs
AGRICULTEURS_CSV_PATH = "C:/Users/Utilisateur/Desktop/AgW3b/static/data/eleveurs_geocoded.csv"
