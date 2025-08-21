#!/usr/bin/env python3
"""
Script de test pour le module proxy GeoServer sécurisé
Configure les variables d'environnement pour le développement local
"""

import os

# Configuration des variables d'environnement pour le développement
os.environ["ENVIRONMENT"] = "development"
os.environ["GEOSERVER_URL"] = "http://localhost:8080/geoserver"
os.environ["GEOSERVER_USERNAME"] = "admin"
os.environ["GEOSERVER_PASSWORD"] = "geoserver"

print("🔧 Variables d'environnement configurées pour le développement")
print(f"   - ENVIRONMENT: {os.environ['ENVIRONMENT']}")
print(f"   - GEOSERVER_URL: {os.environ['GEOSERVER_URL']}")
print(f"   - GEOSERVER_USERNAME: {os.environ['GEOSERVER_USERNAME']}")
print()

# Test du module proxy
try:
    from geoserver_proxy import init_geoserver_proxies, get_geoserver_info, test_geoserver_connection
    print("✅ Module proxy GeoServer importé avec succès")
    
    # Test des fonctions
    print("\n📊 Informations GeoServer :")
    info = get_geoserver_info()
    for key, value in info.items():
        print(f"   - {key}: {value}")
    
    # Test de connexion
    print(f"\n🔌 Test de connexion...")
    connection_ok = test_geoserver_connection()
    status = "✅ OK" if connection_ok else "❌ FAILED"
    print(f"   Résultat: {status}")
    
    if connection_ok:
        print("\n🎉 Proxy GeoServer prêt pour l'intégration!")
    else:
        print("\n⚠️  GeoServer non accessible. Vérifiez que GeoServer est démarré sur localhost:8080")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
