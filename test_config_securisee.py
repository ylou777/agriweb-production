#!/usr/bin/env python3
"""
Test de la configuration sécurisée recommandée par ChatGPT
Vérifie les variables d'environnement et la connectivité GeoServer
"""
import os
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment_config():
    """Test des variables d'environnement requises"""
    
    print("🔧 TEST DE CONFIGURATION SÉCURISÉE")
    print("="*50)
    
    # Variables requises selon ChatGPT
    required_vars = ["GEOSERVER_URL", "GEOSERVER_USERNAME", "GEOSERVER_PASSWORD"]
    missing_vars = []
    
    print("\n📋 Variables d'environnement requises:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == "GEOSERVER_PASSWORD":
                print(f"✅ {var}: ***")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NON DÉFINIE")
            missing_vars.append(var)
    
    # Variables optionnelles
    optional_vars = ["ENVIRONMENT", "RAILWAY_ENVIRONMENT"]
    print(f"\n📋 Variables optionnelles:")
    for var in optional_vars:
        value = os.getenv(var, "non définie")
        print(f"ℹ️  {var}: {value}")
    
    if missing_vars:
        print(f"\n❌ CONFIGURATION INCOMPLÈTE")
        print(f"Variables manquantes: {', '.join(missing_vars)}")
        print(f"\n💡 Pour corriger, définissez ces variables:")
        print(f"Railway: railway variables set VARIABLE=valeur")
        print(f"Local: $env:VARIABLE=\"valeur\" (PowerShell)")
        return False
    else:
        print(f"\n✅ CONFIGURATION COMPLÈTE")
        return True

def test_geoserver_secure_connection():
    """Test de la connexion sécurisée selon les recommandations ChatGPT"""
    
    try:
        # Import du module sécurisé
        from geoserver_proxy import assert_geoserver_ok, GEOSERVER_URL, GEOSERVER_USER, GEOSERVER_PASS
        
        print(f"\n🔗 TEST DE CONNECTIVITÉ SÉCURISÉE")
        print(f"="*40)
        print(f"URL testée: {GEOSERVER_URL}")
        print(f"Utilisateur: {GEOSERVER_USER}")
        
        # Test selon la méthode ChatGPT
        success = assert_geoserver_ok(GEOSERVER_URL, GEOSERVER_USER, GEOSERVER_PASS)
        
        if success:
            print(f"✅ CONNEXION SÉCURISÉE RÉUSSIE!")
            print(f"🎯 GeoServer accessible avec authentification")
            print(f"🎯 Capabilities WMS valides")
            return True
        else:
            print(f"❌ CONNEXION ÉCHOUÉE")
            print(f"⚠️ Vérifiez vos identifiants et l'accessibilité du serveur")
            return False
            
    except ImportError as e:
        print(f"❌ Erreur d'import du module proxy: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def show_recommendations():
    """Affiche les recommandations pour la configuration Production"""
    
    print(f"\n💡 RECOMMANDATIONS CHATGPT POUR LA PRODUCTION")
    print(f"="*60)
    
    print(f"\n1️⃣ Variables Railway à définir:")
    print(f"   railway variables set GEOSERVER_URL=http://81.220.178.156:8080/geoserver")
    print(f"   railway variables set GEOSERVER_USERNAME=app_user")
    print(f"   railway variables set GEOSERVER_PASSWORD=votre_mot_de_passe")
    
    print(f"\n2️⃣ Configuration GeoServer (Admin Panel):")
    print(f"   - Global → Settings → Proxy Base URL:")
    print(f"     http://81.220.178.156:8080/geoserver")
    print(f"   - Service Security → WMS/WFS: autoriser ROLE_READER")
    print(f"   - Créer utilisateur 'app_user' avec ROLE_READER")
    
    print(f"\n3️⃣ Firewall/Réseau:")
    print(f"   - Port 8080 ouvert en entrée sur votre serveur")
    print(f"   - IP sortante Railway autorisée (Static Egress IP recommandé)")
    
    print(f"\n4️⃣ Monitoring:")
    print(f"   - Test de connectivité automatique au démarrage")
    print(f"   - Logs détaillés des erreurs de connexion")
    print(f"   - Timeout et retry configurés")

def main():
    """Test principal"""
    
    print(f"🚀 VALIDATION CONFIGURATION SÉCURISÉE CHATGPT")
    print(f"{"="*55}")
    
    # Test 1: Variables d'environnement
    config_ok = test_environment_config()
    
    if config_ok:
        # Test 2: Connectivité sécurisée
        connection_ok = test_geoserver_secure_connection()
        
        print(f"\n📊 RÉSUMÉ DES TESTS")
        print(f"="*25)
        print(f"Configuration: {'✅ OK' if config_ok else '❌ KO'}")
        print(f"Connectivité:  {'✅ OK' if connection_ok else '❌ KO'}")
        
        if config_ok and connection_ok:
            print(f"\n🎉 CONFIGURATION SÉCURISÉE OPÉRATIONNELLE!")
            print(f"Votre application peut être déployée en production.")
        else:
            print(f"\n⚠️ CONFIGURATION À CORRIGER")
            show_recommendations()
    else:
        show_recommendations()

if __name__ == "__main__":
    main()
