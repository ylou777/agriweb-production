#!/usr/bin/env python3
"""
Test de configuration sécurisée pour GeoServer distant
Configuration optimale selon les recommandations ChatGPT
"""
import os
import requests
from requests.auth import HTTPBasicAuth
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_configuration_distante():
    """Test de la configuration pour GeoServer distant"""
    
    print("🌐 TEST CONFIGURATION GEOSERVER DISTANT")
    print("="*45)
    
    # Configurations à tester selon vos options
    configs_test = {
        "IP Publique (actuelle)": {
            "url": "http://81.220.178.156:8080/geoserver",
            "username": "railway_user",
            "password": "votre_mot_de_passe",
            "description": "Votre serveur actuel"
        },
        "IP + Port 443 (HTTPS)": {
            "url": "https://81.220.178.156:443/geoserver", 
            "username": "railway_user",
            "password": "votre_mot_de_passe",
            "description": "Même serveur en HTTPS"
        },
        "Avec domaine (recommandé)": {
            "url": "https://geoserver.votredomaine.com/geoserver",
            "username": "railway_user", 
            "password": "votre_mot_de_passe",
            "description": "Configuration professionnelle"
        }
    }
    
    print("\n📋 CONFIGURATIONS À TESTER:")
    for name, config in configs_test.items():
        print(f"\n🔧 {name}:")
        print(f"   URL: {config['url']}")
        print(f"   User: {config['username']}")
        print(f"   Description: {config['description']}")

def test_variables_environnement():
    """Test des variables d'environnement recommandées"""
    
    print(f"\n💡 VARIABLES D'ENVIRONNEMENT RECOMMANDÉES")
    print(f"="*45)
    
    # Variables actuelles
    current_vars = {
        "GEOSERVER_URL": os.getenv("GEOSERVER_URL"),
        "GEOSERVER_USERNAME": os.getenv("GEOSERVER_USERNAME"),
        "GEOSERVER_PASSWORD": os.getenv("GEOSERVER_PASSWORD"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "development")
    }
    
    print(f"\n📋 Variables actuelles:")
    for var, value in current_vars.items():
        if value:
            display_value = "***" if "PASSWORD" in var else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NON DÉFINIE")
    
    # Variables recommandées selon ChatGPT
    print(f"\n📋 Variables recommandées pour Railway:")
    recommendations = {
        "GEOSERVER_URL": "http://81.220.178.156:8080/geoserver",
        "GEOSERVER_USERNAME": "app_user", 
        "GEOSERVER_PASSWORD": "votre_mot_de_passe_securise"
    }
    
    for var, value in recommendations.items():
        display_value = "***" if "PASSWORD" in var else value
        print(f"   railway variables set {var}={display_value}")

def test_connexion_chatgpt_method():
    """Test selon la méthode recommandée par ChatGPT"""
    
    print(f"\n🎯 TEST MÉTHODE CHATGPT")
    print(f"="*30)
    
    # Configuration de test
    test_url = os.getenv("GEOSERVER_URL", "http://81.220.178.156:8080/geoserver")
    test_user = os.getenv("GEOSERVER_USERNAME", "railway_user")
    test_pass = os.getenv("GEOSERVER_PASSWORD", "railway_secure_pass_2024")
    
    print(f"URL testée: {test_url}")
    print(f"Utilisateur: {test_user}")
    
    try:
        # Test assert_geoserver_ok selon ChatGPT
        from urllib.parse import urljoin
        
        logger.info(f"[GeoServer] Test de connexion vers: {test_url}")
        
        # Test WMS GetCapabilities (méthode ChatGPT)
        response = requests.get(
            urljoin(test_url, "/wms"),
            params={
                "service": "WMS", 
                "request": "GetCapabilities", 
                "version": "1.3.0"
            },
            auth=HTTPBasicAuth(test_user, test_pass),
            timeout=(5, 20)  # ChatGPT recommend timeout
        )
        
        print(f"Statut HTTP: {response.status_code}")
        
        if response.status_code == 200:
            # Vérification du contenu (méthode ChatGPT)
            if b"<WMS_Capabilities" in response.content:
                print("✅ CONNEXION CHATGPT VALIDÉE!")
                print("🎯 WMS Capabilities détectées correctement")
                logger.info("[GeoServer] Capabilities OK")
                
                # Test additionnel: compter les layers
                if b"<Layer" in response.content:
                    layer_count = response.content.count(b"<Layer")
                    print(f"🗺️ Layers détectées: {layer_count}")
                
                return True
            else:
                print("⚠️ Réponse HTTP 200 mais contenu inattendu")
                print(f"Début réponse: {response.text[:200]}...")
                return False
                
        elif response.status_code == 401:
            print("🔐 ERREUR D'AUTHENTIFICATION")
            print("Vérifiez GEOSERVER_USERNAME et GEOSERVER_PASSWORD")
            logger.error("[GeoServer] Échec authentification")
            return False
            
        elif response.status_code == 404:
            print("❌ GEOSERVER NON TROUVÉ")
            print("Vérifiez GEOSERVER_URL")
            return False
            
        else:
            print(f"❌ ERREUR {response.status_code}")
            print(f"Réponse: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectTimeout:
        print("❌ TIMEOUT DE CONNEXION")
        print("Serveur non accessible ou trop lent")
        logger.exception("[GeoServer] Timeout")
        return False
        
    except requests.exceptions.ConnectionError as e:
        print("❌ ERREUR DE CONNEXION")
        print(f"Détails: {e}")
        logger.exception("[GeoServer] Connexion échouée")
        return False
        
    except Exception as e:
        print(f"❌ ERREUR INATTENDUE: {e}")
        logger.exception("[GeoServer] Erreur")
        return False

def test_proxy_base_url():
    """Test et recommandations pour Proxy Base URL"""
    
    print(f"\n🔧 CONFIGURATION PROXY BASE URL GEOSERVER")
    print(f"="*40)
    
    test_url = os.getenv("GEOSERVER_URL", "http://81.220.178.156:8080/geoserver")
    
    print(f"📍 Configuration actuelle:")
    print(f"   URL: {test_url}")
    
    print(f"\n📍 Configuration recommandée dans GeoServer Admin:")
    print(f"   1. Aller dans: Global → Settings")
    print(f"   2. Proxy Base URL: {test_url}")
    print(f"   3. Use headers for Proxy URL: ✅ Coché")
    
    print(f"\n💡 Pourquoi c'est important:")
    print(f"   - Les URLs dans GetCapabilities seront correctes")
    print(f"   - Évite les liens localhost dans les réponses")
    print(f"   - Nécessaire pour que Railway accède correctement")

def show_security_checklist():
    """Checklist sécurité selon ChatGPT"""
    
    print(f"\n🔒 CHECKLIST SÉCURITÉ CHATGPT")
    print(f"="*35)
    
    print(f"\n✅ À vérifier dans GeoServer:")
    print(f"   □ Utilisateur 'app_user' créé avec ROLE_READER")
    print(f"   □ Service Security → WMS: ROLE_READER autorisé")
    print(f"   □ Service Security → WFS: ROLE_READER autorisé") 
    print(f"   □ Data Security: Read access pour vos workspaces")
    print(f"   □ Proxy Base URL configurée")
    
    print(f"\n✅ Variables Railway:")
    print(f"   □ GEOSERVER_URL définie (pas de localhost)")
    print(f"   □ GEOSERVER_USERNAME défini")
    print(f"   □ GEOSERVER_PASSWORD défini")
    print(f"   □ Variables identiques local/production")
    
    print(f"\n✅ Réseau/Firewall:")
    print(f"   □ Port 8080 ouvert sur votre serveur")
    print(f"   □ IP Railway autorisée (ou tous si test)")

def main():
    """Test principal"""
    
    test_configuration_distante()
    test_variables_environnement()
    success = test_connexion_chatgpt_method()
    test_proxy_base_url()
    show_security_checklist()
    
    print(f"\n🎯 RÉSUMÉ DU TEST")
    print(f"="*20)
    print(f"Configuration ChatGPT: {'✅ VALIDÉE' if success else '❌ À CORRIGER'}")
    
    if success:
        print(f"🎉 Votre configuration est prête pour Railway !")
        print(f"Vous pouvez déployer en utilisant les mêmes variables.")
    else:
        print(f"⚠️ Corrigez les points ci-dessus avant déploiement Railway.")

if __name__ == "__main__":
    main()
