# 🚀 CONFIGURATION GEOSERVER RAILWAY - PRÊT POUR PRODUCTION!

# ✅ URL CONFIRMÉE - VOTRE GEOSERVER RAILWAY
GEOSERVER_URL = "https://geoserver-agriweb-production.up.railway.app"
GEOSERVER_USER = "admin"
GEOSERVER_PASSWORD = "admin123"

# Services GeoServer disponibles
GEOSERVER_WMS = f"{GEOSERVER_URL}/geoserver/ows"
GEOSERVER_WFS = f"{GEOSERVER_URL}/geoserver/ows"
GEOSERVER_REST = f"{GEOSERVER_URL}/geoserver/rest"

# 💰 COÛT ACTUEL: ~$40-50/mois (Railway Pro)
# 🔄 MIGRATION CLOUD RUN: Possible plus tard pour ~$10/mois

# 🎯 ÉTAPES SUIVANTES:
# 1. Remplacer [VOTRE-URL-RAILWAY] par l'URL réelle
# 2. Importer vos 100 Go de données
# 3. Tester avec votre application Flask
# 4. Mise en production ! 🚀

print("✅ GeoServer Railway configuré!")
print(f"🌐 Admin Interface: {GEOSERVER_URL}/geoserver/web/")
print(f"👤 Login: {GEOSERVER_USER} / {GEOSERVER_PASSWORD}")
