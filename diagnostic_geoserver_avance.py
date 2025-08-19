#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC AVANCÉ GEOSERVER
Script pour identifier précisément votre configuration GeoServer
"""

import requests
import re
from urllib.parse import urljoin

def deep_geoserver_analysis():
    """Analyse approfondie pour trouver GeoServer"""
    
    print("🔍 DIAGNOSTIC AVANCÉ GEOSERVER")
    print("=" * 50)
    
    # Étape 1: Analyser ce qui tourne sur le port 8080
    print("\n1️⃣ ANALYSE DU PORT 8080")
    analyze_port_8080()
    
    # Étape 2: Chercher GeoServer dans d'autres emplacements
    print("\n2️⃣ RECHERCHE D'EMPLACEMENTS ALTERNATIFS")
    find_alternative_paths()
    
    # Étape 3: Vérifier si GeoServer est installé
    print("\n3️⃣ VÉRIFICATION INSTALLATION GEOSERVER")
    check_geoserver_installation()

def analyze_port_8080():
    """Analyse ce qui répond sur le port 8080"""
    
    base_url = "http://localhost:8080"
    
    try:
        response = requests.get(base_url, timeout=10)
        print(f"   ✅ Port 8080 répond (HTTP {response.status_code})")
        
        # Analyser le contenu de la page
        content = response.text.lower()
        
        if "tomcat" in content:
            print("   🐱 Serveur détecté: Apache Tomcat")
            
            # Chercher la version Tomcat
            version_match = re.search(r'tomcat[/\s]*([\d\.]+)', content)
            if version_match:
                print(f"   📊 Version: Tomcat {version_match.group(1)}")
        
        if "geoserver" in content:
            print("   🌐 GeoServer détecté dans la page")
        else:
            print("   ⚠️ GeoServer non mentionné sur la page principale")
        
        # Extraire les liens disponibles
        links = re.findall(r'href=["\']([^"\']+)["\']', content)
        geoserver_links = [link for link in links if 'geoserver' in link.lower()]
        
        if geoserver_links:
            print(f"   🔗 Liens GeoServer trouvés: {geoserver_links}")
        
        # Tester les applications déployées communes
        test_common_apps(base_url)
        
    except Exception as e:
        print(f"   ❌ Erreur analyse port 8080: {e}")

def test_common_apps(base_url):
    """Teste les applications web communes sur Tomcat"""
    
    print("   🔍 Applications déployées:")
    
    common_apps = [
        ("manager", "Tomcat Manager"),
        ("geoserver", "GeoServer"),
        ("geonetwork", "GeoNetwork"),
        ("geowebcache", "GeoWebCache"),
        ("ROOT", "Application racine")
    ]
    
    for app_path, app_name in common_apps:
        test_url = f"{base_url}/{app_path}"
        try:
            response = requests.get(test_url, timeout=5)
            if response.status_code == 200:
                print(f"      ✅ {app_name}: {test_url}")
            elif response.status_code == 404:
                print(f"      ❌ {app_name}: Non installé")
            else:
                print(f"      ⚠️ {app_name}: HTTP {response.status_code}")
        except:
            print(f"      ❌ {app_name}: Inaccessible")

def find_alternative_paths():
    """Cherche GeoServer dans des emplacements alternatifs"""
    
    base_urls = [
        "http://localhost:8080",
        "http://localhost:8081"
    ]
    
    alternative_paths = [
        "/geoserver",
        "/geoserver/web",
        "/GeoServer",
        "/geo",
        "/maps",
        "/wfs",
        "/wms",
        "/", # Racine
    ]
    
    for base_url in base_urls:
        print(f"\n   🔍 Test des chemins sur {base_url}:")
        
        for path in alternative_paths:
            test_url = urljoin(base_url, path)
            
            try:
                response = requests.get(test_url, timeout=3)
                content = response.text.lower()
                
                if response.status_code == 200:
                    if "geoserver" in content or "wfs" in content or "capabilities" in content:
                        print(f"      🎯 TROUVÉ: {test_url}")
                        test_geoserver_services(test_url)
                    else:
                        print(f"      ✅ {path}: Accessible mais pas GeoServer")
                else:
                    print(f"      ❌ {path}: HTTP {response.status_code}")
                    
            except:
                print(f"      ❌ {path}: Inaccessible")

def test_geoserver_services(base_url):
    """Teste les services GeoServer sur une URL donnée"""
    
    print(f"      🧪 Test des services GeoServer:")
    
    # Test WFS
    wfs_url = urljoin(base_url, "/ows")
    wfs_params = {"service": "WFS", "request": "GetCapabilities"}
    
    try:
        response = requests.get(wfs_url, params=wfs_params, timeout=10)
        if response.status_code == 200 and "WFS_Capabilities" in response.text:
            print(f"         ✅ Service WFS: {wfs_url}")
            extract_layer_info(response.text)
        else:
            print(f"         ❌ Service WFS: Non fonctionnel")
    except:
        print(f"         ❌ Service WFS: Erreur de connexion")
    
    # Test WMS
    wms_url = urljoin(base_url, "/ows")
    wms_params = {"service": "WMS", "request": "GetCapabilities"}
    
    try:
        response = requests.get(wms_url, params=wms_params, timeout=10)
        if response.status_code == 200 and "WMS_Capabilities" in response.text:
            print(f"         ✅ Service WMS: {wms_url}")
        else:
            print(f"         ❌ Service WMS: Non fonctionnel")
    except:
        print(f"         ❌ Service WMS: Erreur de connexion")

def extract_layer_info(capabilities_xml):
    """Extrait les informations des couches depuis GetCapabilities"""
    
    # Recherche des noms de couches
    layer_pattern = r'<Name>([^<]+)</Name>'
    layers = re.findall(layer_pattern, capabilities_xml)
    
    if layers:
        print(f"         📊 {len(layers)} couches trouvées:")
        
        # Chercher les couches AgriWeb
        agriweb_layers = []
        for layer in layers:
            if any(keyword in layer.lower() for keyword in ['gpu', 'prefecture', 'poste', 'cadastre', 'parcelle']):
                agriweb_layers.append(layer)
        
        if agriweb_layers:
            print(f"         🎯 Couches AgriWeb détectées:")
            for layer in agriweb_layers[:5]:  # Afficher les 5 premières
                print(f"            - {layer}")
            if len(agriweb_layers) > 5:
                print(f"            ... et {len(agriweb_layers) - 5} autres")
        else:
            print(f"         ⚠️ Aucune couche AgriWeb détectée")
            print(f"         📋 Exemples de couches: {layers[:3]}")

def check_geoserver_installation():
    """Vérifie si GeoServer est correctement installé"""
    
    print("   🔍 Vérification de l'installation:")
    
    # Vérifier les fichiers WAR Tomcat communs
    potential_locations = [
        "C:/Program Files/Apache Software Foundation/Tomcat*/webapps/",
        "C:/apache-tomcat*/webapps/",
        "C:/tomcat*/webapps/",
        "/opt/tomcat/webapps/",
        "/var/lib/tomcat*/webapps/"
    ]
    
    print("   📁 Emplacements WAR potentiels:")
    for location in potential_locations:
        print(f"      - {location}")
    
    print("\n   💡 SOLUTIONS DE DÉPANNAGE:")
    print("      1. Vérifiez si geoserver.war est dans webapps/")
    print("      2. Redémarrez Tomcat après déploiement")
    print("      3. Vérifiez les logs Tomcat: logs/catalina.out")
    print("      4. Testez l'URL complète avec /geoserver/web/")

def generate_config_recommendations():
    """Génère des recommandations de configuration"""
    
    print("\n4️⃣ RECOMMANDATIONS DE CONFIGURATION")
    print("-" * 40)
    
    print("📋 Pour installer GeoServer sur Tomcat:")
    print("   1. Téléchargez geoserver.war depuis geoserver.org")
    print("   2. Copiez dans webapps/ de Tomcat")
    print("   3. Redémarrez Tomcat")
    print("   4. Accédez à http://localhost:8080/geoserver")
    
    print("\n🔧 Configuration AgriWeb recommandée:")
    print("   URL de base: http://localhost:8080/geoserver")
    print("   Services WFS: http://localhost:8080/geoserver/ows")
    print("   Admin interface: http://localhost:8080/geoserver/web/")
    print("   Credentials par défaut: admin/geoserver")
    
    print("\n📊 Après installation, importez vos couches:")
    print("   - Créez le workspace 'gpu'")
    print("   - Importez vos shapefiles/PostGIS")
    print("   - Configurez les couches selon GUIDE_GEOSERVER_CONFIGURATION.md")

if __name__ == "__main__":
    print("🚀 Diagnostic avancé GeoServer pour AgriWeb 2.0\n")
    
    deep_geoserver_analysis()
    generate_config_recommendations()
    
    print("\n" + "="*60)
    print("🎯 CONCLUSION:")
    print("   Votre Tomcat fonctionne, mais GeoServer n'est pas déployé")
    print("   ou n'est pas accessible à l'emplacement standard.")
    print("\n📖 Consultez GUIDE_GEOSERVER_CONFIGURATION.md pour la suite!")
