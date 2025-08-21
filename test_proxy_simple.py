#!/usr/bin/env python3
"""
Test simple du proxy GeoServer sans dépendances externes
"""

import os

# Configuration des variables d'environnement
os.environ["ENVIRONMENT"] = "development"
os.environ["GEOSERVER_URL"] = "http://localhost:8080/geoserver"
os.environ["GEOSERVER_USERNAME"] = "admin"
os.environ["GEOSERVER_PASSWORD"] = "geoserver"

print("=== TEST PROXY GEOSERVER SÉCURISÉ ===")
print()

try:
    # Test du module proxy
    from geoserver_proxy import get_geoserver_info, test_geoserver_connection, ACTIVE_GEOSERVER_URL
    print("✅ Import du module proxy réussi")
    
    # Informations de configuration
    print(f"\n📊 Configuration GeoServer :")
    print(f"   - URL active: {ACTIVE_GEOSERVER_URL}")
    info = get_geoserver_info()
    for key, value in info.items():
        print(f"   - {key}: {value}")
    
    # Test de connexion
    print(f"\n🔌 Test de connexion à GeoServer...")
    connection_ok = test_geoserver_connection()
    
    if connection_ok:
        print("✅ SUCCÈS : GeoServer accessible !")
        print("🎉 Proxy prêt pour l'intégration dans l'application Flask")
    else:
        print("⚠️  GeoServer non accessible")
        print("💡 Solutions possibles :")
        print("   1. Démarrer GeoServer en local (port 8080)")
        print("   2. Utiliser ngrok pour exposer votre GeoServer")
        print("   3. Configurer un GeoServer distant accessible")
    
    print(f"\n📋 Routes proxy qui seront disponibles :")
    print("   - /proxy/wms (pour les tuiles)")
    print("   - /proxy/wfs (pour les données vectorielles)")
    print("   - /proxy/capabilities (pour les capacités)")
    print("   - /proxy/test (pour tester les proxies)")
    
except Exception as e:
    print(f"❌ Erreur lors du test : {e}")
    import traceback
    traceback.print_exc()

print("\n=== FIN DU TEST ===")
