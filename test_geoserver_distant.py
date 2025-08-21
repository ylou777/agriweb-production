#!/usr/bin/env python3
"""
Test complet d'accès distant à GeoServer
Suit la checklist recommandée par ChatGPT
"""
import os
import requests
from requests.auth import HTTPBasicAuth
import json
from urllib.parse import urljoin

def test_geoserver_remote_access():
    """Test de l'accès distant selon la checklist ChatGPT"""
    
    print("🌐 TEST D'ACCÈS DISTANT GEOSERVER")
    print("="*50)
    
    # Configuration à tester
    test_configs = [
        {
            "name": "IP Directe Port 8080", 
            "url": "http://81.220.178.156:8080/geoserver",
            "username": "railway_user",
            "password": "railway_secure_pass_2024"
        },
        {
            "name": "IP Directe Port 443 (HTTPS)",
            "url": "https://81.220.178.156:443/geoserver", 
            "username": "railway_user",
            "password": "railway_secure_pass_2024"
        },
        {
            "name": "Configuration Environnement",
            "url": os.getenv("GEOSERVER_URL", "http://localhost:8080/geoserver"),
            "username": os.getenv("GEOSERVER_USERNAME", "admin"),
            "password": os.getenv("GEOSERVER_PASSWORD", "geoserver")
        }
    ]
    
    results = []
    
    for config in test_configs:
        print(f"\n🔍 Test: {config['name']}")
        print(f"URL: {config['url']}")
        print(f"User: {config['username']}")
        
        result = test_single_config(config)
        results.append({**config, **result})
    
    return results

def test_single_config(config):
    """Test une configuration spécifique"""
    
    url = config["url"] 
    username = config["username"]
    password = config["password"]
    
    tests = []
    
    # Test 1: Connectivité de base
    print("  📡 Test connectivité...")
    connectivity = test_basic_connectivity(url)
    tests.append(("Connectivité", connectivity))
    
    if not connectivity["success"]:
        return {"tests": tests, "overall": "FAILED", "reason": "Connectivité échouée"}
    
    # Test 2: Authentication
    print("  🔐 Test authentification...")
    auth_result = test_authentication(url, username, password)
    tests.append(("Authentification", auth_result))
    
    if not auth_result["success"]:
        return {"tests": tests, "overall": "FAILED", "reason": "Authentification échouée"}
    
    # Test 3: WMS GetCapabilities
    print("  🗺️ Test WMS...")
    wms_result = test_wms_capabilities(url, username, password)
    tests.append(("WMS Capabilities", wms_result))
    
    # Test 4: WFS GetCapabilities  
    print("  📊 Test WFS...")
    wfs_result = test_wfs_capabilities(url, username, password)
    tests.append(("WFS Capabilities", wfs_result))
    
    # Test 5: Service Security
    print("  🛡️ Test permissions...")
    perms_result = test_service_permissions(url, username, password)
    tests.append(("Permissions", perms_result))
    
    # Évaluation globale
    success_count = sum(1 for _, test in tests if test["success"])
    overall = "SUCCESS" if success_count >= 3 else "PARTIAL" if success_count >= 1 else "FAILED"
    
    return {"tests": tests, "overall": overall, "success_count": success_count}

def test_basic_connectivity(url):
    """Test de connectivité de base"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code in [200, 401, 403]:
            return {
                "success": True, 
                "status_code": response.status_code,
                "message": "Serveur accessible"
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code, 
                "message": f"Réponse inattendue: {response.status_code}"
            }
    except requests.exceptions.ConnectTimeout:
        return {"success": False, "message": "Timeout de connexion"}
    except requests.exceptions.ConnectionError as e:
        return {"success": False, "message": f"Erreur de connexion: {str(e)[:100]}"}
    except Exception as e:
        return {"success": False, "message": f"Erreur: {str(e)[:100]}"}

def test_authentication(url, username, password):
    """Test d'authentification"""
    try:
        # Test de l'authentification sur l'endpoint REST
        rest_url = urljoin(url, "/rest/about/version")
        response = requests.get(
            rest_url,
            auth=HTTPBasicAuth(username, password),
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Authentification réussie",
                "endpoint": "/rest/about/version"
            }
        elif response.status_code == 401:
            return {
                "success": False,
                "message": "Identifiants incorrects",
                "status_code": 401
            }
        elif response.status_code == 403:
            return {
                "success": False,
                "message": "Accès refusé (permissions insuffisantes)",
                "status_code": 403
            }
        else:
            return {
                "success": False,
                "message": f"Réponse inattendue: {response.status_code}",
                "status_code": response.status_code
            }
            
    except Exception as e:
        return {"success": False, "message": f"Erreur auth: {str(e)[:100]}"}

def test_wms_capabilities(url, username, password):
    """Test WMS GetCapabilities selon recommandations ChatGPT"""
    try:
        wms_url = urljoin(url, "/wms")
        response = requests.get(
            wms_url,
            auth=HTTPBasicAuth(username, password),
            params={
                "service": "WMS",
                "request": "GetCapabilities", 
                "version": "1.3.0"
            },
            timeout=20
        )
        
        if response.status_code == 200:
            content = response.text
            if "WMS_Capabilities" in content:
                # Compter les couches disponibles
                layer_count = content.count("<Layer")
                return {
                    "success": True,
                    "message": f"WMS OK, {layer_count} couches détectées",
                    "layer_count": layer_count
                }
            else:
                return {
                    "success": False,
                    "message": "Réponse WMS invalide (pas de WMS_Capabilities)"
                }
        else:
            return {
                "success": False,
                "message": f"Erreur WMS: {response.status_code}",
                "status_code": response.status_code
            }
            
    except Exception as e:
        return {"success": False, "message": f"Erreur WMS: {str(e)[:100]}"}

def test_wfs_capabilities(url, username, password):
    """Test WFS GetCapabilities"""
    try:
        wfs_url = urljoin(url, "/wfs")
        response = requests.get(
            wfs_url,
            auth=HTTPBasicAuth(username, password),
            params={
                "service": "WFS",
                "request": "GetCapabilities",
                "version": "2.0.0"
            },
            timeout=20
        )
        
        if response.status_code == 200:
            content = response.text
            if "WFS_Capabilities" in content:
                feature_count = content.count("FeatureType")
                return {
                    "success": True,
                    "message": f"WFS OK, {feature_count} types de features",
                    "feature_count": feature_count
                }
            else:
                return {
                    "success": False,
                    "message": "Réponse WFS invalide"
                }
        else:
            return {
                "success": False, 
                "message": f"Erreur WFS: {response.status_code}",
                "status_code": response.status_code
            }
            
    except Exception as e:
        return {"success": False, "message": f"Erreur WFS: {str(e)[:100]}"}

def test_service_permissions(url, username, password):
    """Test des permissions de service"""
    try:
        # Test d'accès aux workspaces (nécessite ROLE_READER minimum)
        rest_url = urljoin(url, "/rest/workspaces")
        response = requests.get(
            rest_url,
            auth=HTTPBasicAuth(username, password),
            headers={"Accept": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                workspaces = data.get("workspaces", {}).get("workspace", [])
                return {
                    "success": True,
                    "message": f"Accès workspaces OK, {len(workspaces)} workspaces",
                    "workspace_count": len(workspaces)
                }
            except:
                return {
                    "success": True,
                    "message": "Accès workspaces OK (format non-JSON)"
                }
        elif response.status_code == 403:
            return {
                "success": False,
                "message": "Permissions insuffisantes pour les workspaces"
            }
        else:
            return {
                "success": False,
                "message": f"Erreur permissions: {response.status_code}"
            }
            
    except Exception as e:
        return {"success": False, "message": f"Erreur permissions: {str(e)[:100]}"}

def show_configuration_checklist(results):
    """Affiche la checklist de configuration"""
    
    print(f"\n📋 CHECKLIST CONFIGURATION GEOSERVER DISTANT")
    print(f"="*55)
    
    # Analyser les résultats
    working_config = None
    for result in results:
        if result.get("overall") == "SUCCESS":
            working_config = result
            break
    
    if working_config:
        print(f"✅ Configuration fonctionnelle trouvée!")
        print(f"   URL: {working_config['url']}")
        print(f"   Utilisateur: {working_config['username']}")
        print(f"   Tests réussis: {working_config['success_count']}/5")
        
        print(f"\n🔧 Variables Railway à définir:")
        print(f"   railway variables set GEOSERVER_URL={working_config['url']}")
        print(f"   railway variables set GEOSERVER_USERNAME={working_config['username']}")
        print(f"   railway variables set GEOSERVER_PASSWORD={working_config['password']}")
        
    else:
        print(f"❌ Aucune configuration pleinement fonctionnelle")
        
        print(f"\n🛠️ Actions recommandées:")
        print(f"1️⃣ URL Publique:")
        print(f"   - Vérifiez que GeoServer est accessible depuis Internet")
        print(f"   - Port 8080 ou 443 ouvert dans le firewall")
        print(f"   - Redirection de port configurée sur votre routeur")
        
        print(f"\n2️⃣ Utilisateur GeoServer:")
        print(f"   - Créer utilisateur 'railway_user' avec ROLE_READER")
        print(f"   - Service Security: autoriser ROLE_READER sur WMS/WFS")
        print(f"   - Data Security: autoriser lecture sur workspaces")
        
        print(f"\n3️⃣ Configuration GeoServer:")
        print(f"   - Global Settings → Proxy Base URL: votre URL publique")
        print(f"   - Tester depuis: curl -u user:pass URL/geoserver/wms?service=WMS&request=GetCapabilities")

def main():
    """Test principal"""
    
    results = test_geoserver_remote_access()
    
    print(f"\n📊 RÉSUMÉ DES TESTS")
    print(f"="*30)
    
    for result in results:
        status_icon = "✅" if result.get("overall") == "SUCCESS" else "⚠️" if result.get("overall") == "PARTIAL" else "❌"
        success_count = result.get("success_count", 0)
        print(f"{status_icon} {result['name']}: {success_count}/5 tests")
        
        if result.get("reason"):
            print(f"    └─ {result['reason']}")
    
    show_configuration_checklist(results)
    
    print(f"\n💡 PROCHAINES ÉTAPES:")
    print(f"1. Configurer l'utilisateur GeoServer avec ROLE_READER")
    print(f"2. Ouvrir les ports réseau nécessaires") 
    print(f"3. Définir les variables Railway")
    print(f"4. Tester depuis Railway avec les routes proxy")

if __name__ == "__main__":
    main()
