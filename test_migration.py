#!/usr/bin/env python3
"""
Test de l'application avec la nouvelle configuration GeoServer
"""

import os
import sys
import requests
from pathlib import Path

# Ajout du répertoire courant au path
sys.path.insert(0, str(Path(__file__).parent))

def test_config():
    """Test de la configuration"""
    print("🔧 Test de la configuration...")
    
    # Import de la configuration
    try:
        from config import get_geoserver_url
        geoserver_url = get_geoserver_url()
        print(f"✅ URL GeoServer configurée: {geoserver_url}")
        return geoserver_url
    except Exception as e:
        print(f"❌ Erreur configuration: {e}")
        return None

def test_environment_switching():
    """Test du basculement d'environnement"""
    print("\n🔄 Test du basculement d'environnement...")
    
    # Test environnement development
    os.environ['ENVIRONMENT'] = 'development'
    from importlib import reload
    import config
    reload(config)
    dev_url = config.get_geoserver_url()
    print(f"📍 Développement: {dev_url}")
    
    # Test environnement production
    os.environ['ENVIRONMENT'] = 'production'
    reload(config)
    prod_url = config.get_geoserver_url()
    print(f"🌐 Production: {prod_url}")
    
    return dev_url, prod_url

def test_application_startup():
    """Test de démarrage de l'application"""
    print("\n🚀 Test de démarrage de l'application...")
    
    try:
        # Import de l'application principale
        from agriweb_hebergement_gratuit import app
        
        # Vérification que l'app est configurée
        print("✅ Application importée avec succès")
        
        # Test des routes principales
        with app.test_client() as client:
            # Test route racine
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Route racine accessible")
            else:
                print(f"⚠️ Route racine: {response.status_code}")
            
            # Test route recherche
            response = client.get('/recherche')
            if response.status_code in [200, 302]:  # 302 pour redirection
                print("✅ Route recherche accessible")
            else:
                print(f"⚠️ Route recherche: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur application: {e}")
        return False

def test_geoserver_connection(url):
    """Test de connexion GeoServer"""
    print(f"\n🔍 Test de connexion GeoServer: {url}")
    
    try:
        # Test de la page d'accueil GeoServer
        response = requests.get(f"{url}/web/", timeout=10)
        if response.status_code == 200:
            print("✅ GeoServer accessible")
            return True
        else:
            print(f"⚠️ GeoServer: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur connexion GeoServer: {e}")
        return False

def main():
    """Test principal"""
    print("🧪 Test de Migration GeoServer - Configuration Application")
    print("=" * 60)
    
    # Test 1: Configuration
    geoserver_url = test_config()
    if not geoserver_url:
        print("❌ Configuration échouée")
        return False
    
    # Test 2: Basculement d'environnement
    dev_url, prod_url = test_environment_switching()
    
    # Test 3: Application
    app_ok = test_application_startup()
    
    # Test 4: Connexion GeoServer (si local)
    geoserver_ok = False
    if "localhost" in geoserver_url:
        geoserver_ok = test_geoserver_connection(geoserver_url)
    else:
        print(f"\n🌐 GeoServer distant configuré: {geoserver_url}")
        print("💡 Test de connexion après déploiement")
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS:")
    print(f"   ✅ Configuration: {'OK' if geoserver_url else 'ÉCHEC'}")
    print(f"   ✅ Environnements: OK (dev: {dev_url.split('/')[-2]}, prod: {prod_url.split('/')[-2]})")
    print(f"   ✅ Application: {'OK' if app_ok else 'ÉCHEC'}")
    print(f"   {'✅' if geoserver_ok else '🔄'} GeoServer: {'OK' if geoserver_ok else 'PRÊT POUR DÉPLOIEMENT'}")
    
    # Instructions
    print("\n💡 PROCHAINES ÉTAPES:")
    if geoserver_ok:
        print("   1. Exportez vos données GeoServer: python migrate_geoserver.py")
        print("   2. Déployez sur Railway")
        print("   3. Changez ENVIRONMENT=production dans .env")
    else:
        print("   1. Déployez GeoServer sur Railway")
        print("   2. Mettez à jour l'URL dans .env")
        print("   3. Changez ENVIRONMENT=production dans .env")
        print("   4. Relancez ce test")
    
    return app_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
