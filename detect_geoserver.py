#!/usr/bin/env python3
"""
🔍 DÉTECTION AUTOMATIQUE GEOSERVER
Script pour détecter votre configuration GeoServer
"""

import requests
import socket
from urllib.parse import urljoin

def test_geoserver_connection():
    """Teste différentes configurations GeoServer possibles"""
    
    print("🔍 DÉTECTION DE VOTRE GEOSERVER")
    print("=" * 50)
    
    # Configurations possibles
    possible_configs = [
        {"url": "http://localhost:8080/geoserver", "desc": "GeoServer standard (Tomcat)"},
        {"url": "http://localhost:8081/geoserver", "desc": "GeoServer port alternatif"},
        {"url": "http://localhost:9090/geoserver", "desc": "GeoServer Jetty"},
        {"url": "http://127.0.0.1:8080/geoserver", "desc": "GeoServer localhost explicite"},
        {"url": "http://localhost/geoserver", "desc": "GeoServer via Apache (port 80)"},
        {"url": "https://localhost:8443/geoserver", "desc": "GeoServer HTTPS"}
    ]
    
    working_config = None
    
    for config in possible_configs:
        print(f"\n🔍 Test: {config['desc']}")
        print(f"   URL: {config['url']}")
        
        if test_single_config(config['url']):
            working_config = config
            break
    
    if working_config:
        print(f"\n✅ GEOSERVER TROUVÉ !")
        print(f"   URL: {working_config['url']}")
        print(f"   Description: {working_config['desc']}")
        
        # Test des couches avec la config trouvée
        test_agriweb_layers(working_config['url'])
        
        return working_config['url']
    else:
        print(f"\n❌ GEOSERVER NON TROUVÉ")
        print(f"💡 Solutions possibles :")
        print(f"   1. Démarrez GeoServer (vérifiez les services Windows)")
        print(f"   2. Vérifiez le port dans server.xml (Tomcat)")
        print(f"   3. Testez manuellement : http://localhost:8080/geoserver")
        
        return None

def test_single_config(base_url):
    """Teste une configuration GeoServer spécifique"""
    
    # Test 1: Page d'accueil
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200 and "geoserver" in response.text.lower():
            print(f"   ✅ Page d'accueil accessible")
        else:
            print(f"   ❌ Page d'accueil: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connexion impossible")
        return False
    except Exception as e:
        print(f"   ❌ Erreur: {str(e)[:50]}...")
        return False
    
    # Test 2: API REST
    try:
        rest_url = urljoin(base_url, "/rest/about/version.json")
        response = requests.get(rest_url, timeout=5)
        if response.status_code == 200:
            print(f"   ✅ API REST accessible")
        else:
            print(f"   ⚠️ API REST: HTTP {response.status_code}")
    except:
        print(f"   ⚠️ API REST non accessible")
    
    # Test 3: Service WFS
    try:
        wfs_url = urljoin(base_url, "/ows")
        params = {"service": "WFS", "request": "GetCapabilities"}
        response = requests.get(wfs_url, params=params, timeout=10)
        if response.status_code == 200 and "WFS_Capabilities" in response.text:
            print(f"   ✅ Service WFS opérationnel")
            return True
        else:
            print(f"   ❌ Service WFS: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Service WFS: {str(e)[:50]}...")
        return False

def test_agriweb_layers(geoserver_url):
    """Teste les couches critiques d'AgriWeb"""
    
    print(f"\n🎯 TEST DES COUCHES AGRIWEB")
    print("-" * 30)
    
    # Couches les plus importantes pour AgriWeb
    critical_layers = [
        ("🗺️ Cadastre", "gpu:prefixes_sections"),
        ("⚡ Postes BT", "gpu:poste_elec_shapefile"),
        ("🌾 RPG", "gpu:PARCELLES_GRAPHIQUES")
    ]
    
    working_count = 0
    
    for nom, layer_name in critical_layers:
        if test_layer_quick(geoserver_url, nom, layer_name):
            working_count += 1
    
    print(f"\n📊 Résumé: {working_count}/{len(critical_layers)} couches critiques OK")
    
    if working_count == len(critical_layers):
        print("🎉 Excellent ! AgriWeb peut fonctionner avec toutes les fonctionnalités.")
    elif working_count > 0:
        print("✅ Bien ! AgriWeb peut fonctionner avec des fonctionnalités limitées.")
    else:
        print("⚠️ Aucune couche trouvée - vérifiez la configuration des données.")

def test_layer_quick(geoserver_url, nom, layer_name):
    """Test rapide d'une couche"""
    
    url = urljoin(geoserver_url, "/ows")
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": layer_name,
        "maxFeatures": 1,
        "outputFormat": "application/json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            feature_count = len(data.get("features", []))
            print(f"   ✅ {nom}: {feature_count} feature(s)")
            return True
        else:
            print(f"   ❌ {nom}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   🚨 {nom}: {str(e)[:40]}...")
        return False

def check_network_ports():
    """Vérifie quels ports sont ouverts localement"""
    
    print(f"\n🔍 VÉRIFICATION DES PORTS RÉSEAU")
    print("-" * 35)
    
    common_ports = [8080, 8081, 9090, 80, 443, 8443]
    
    for port in common_ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"   ✅ Port {port}: OUVERT")
        else:
            print(f"   ❌ Port {port}: FERMÉ")

if __name__ == "__main__":
    print("🚀 Détection automatique de GeoServer pour AgriWeb 2.0\n")
    
    # Vérification des ports
    check_network_ports()
    
    # Détection GeoServer
    geoserver_url = test_geoserver_connection()
    
    if geoserver_url:
        print(f"\n🎯 CONFIGURATION POUR AGRIWEB 2.0")
        print(f"   Modifiez dans agriweb_source.py :")
        print(f"   GEOSERVER_URL = \"{geoserver_url}\"")
        
        print(f"\n📋 PROCHAINES ÉTAPES :")
        print(f"   1. Mettez à jour l'URL dans votre code")
        print(f"   2. Testez une recherche complète sur une commune")
        print(f"   3. Vérifiez toutes les couches avec diagnostic_geoserver.py")
        
    else:
        print(f"\n🔧 SOLUTIONS DE DÉPANNAGE :")
        print(f"   1. Démarrez GeoServer (services Windows/Linux)")
        print(f"   2. Vérifiez les logs GeoServer pour les erreurs")
        print(f"   3. Testez manuellement dans un navigateur")
        print(f"   4. Vérifiez la configuration Tomcat/Jetty")
    
    print(f"\n📖 Guide complet : GUIDE_GEOSERVER_CONFIGURATION.md")
