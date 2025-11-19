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
