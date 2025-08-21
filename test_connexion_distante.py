#!/usr/bin/env python3
"""
Test de connexion distante à GeoServer
Vérifie si les identifiants configurés fonctionnent
"""
import os
import requests
from requests.auth import HTTPBasicAuth

def test_geoserver_connection():
    """Test de connexion avec la configuration actuelle"""
    
    print("=== Configuration actuelle ===")
    print(f"GEOSERVER_URL: {os.getenv('GEOSERVER_URL', 'http://localhost:8080/geoserver')}")
    print(f"GEOSERVER_USERNAME: {os.getenv('GEOSERVER_USERNAME', 'non défini')}")
    print(f"GEOSERVER_PASSWORD: {'***' if os.getenv('GEOSERVER_PASSWORD') else 'non défini'}")
    print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'development')}")
    print()

    # URL de base
    base_url = os.getenv('GEOSERVER_URL', 'http://localhost:8080/geoserver')
    username = os.getenv('GEOSERVER_USERNAME', 'admin')  
    password = os.getenv('GEOSERVER_PASSWORD', 'geoserver')
    
    print(f"Test de connexion à: {base_url}")
    print(f"Avec utilisateur: {username}")
    print()
    
    try:
        # Test 1: Version GeoServer
        print("🔍 Test 1: Récupération de la version...")
        auth = HTTPBasicAuth(username, password)
        response = requests.get(f'{base_url}/rest/about/version', 
                              auth=auth, 
                              timeout=10)
        
        print(f"Statut de réponse: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ CONNEXION RÉUSSIE!")
            try:
                data = response.json()
                print(f"Version GeoServer: {data}")
            except:
                print("Réponse reçue mais pas au format JSON attendu")
                print(f"Contenu: {response.text[:200]}...")
        elif response.status_code == 401:
            print("❌ ERREUR D'AUTHENTIFICATION - Vérifiez vos identifiants")
            return False
        elif response.status_code == 404:
            print("❌ GEOSERVER NON TROUVÉ - Vérifiez l'URL")
            return False
        else:
            print(f"❌ ERREUR {response.status_code}: {response.text[:200]}")
            return False
            
        print()
        
        # Test 2: Liste des workspaces
        print("🔍 Test 2: Liste des workspaces...")
        response = requests.get(f'{base_url}/rest/workspaces', 
                              auth=auth, 
                              timeout=10,
                              headers={'Accept': 'application/json'})
        
        if response.status_code == 200:
            print("✅ Accès aux workspaces réussi!")
            try:
                data = response.json()
                workspaces = data.get('workspaces', {}).get('workspace', [])
                print(f"Workspaces trouvés: {len(workspaces)}")
                for ws in workspaces[:3]:  # Afficher les 3 premiers
                    print(f"  - {ws.get('name', 'N/A')}")
            except:
                print("Réponse reçue mais format inattendu")
        else:
            print(f"❌ Erreur accès workspaces: {response.status_code}")
            
        print()
        
        # Test 3: Capacités WMS
        print("🔍 Test 3: Capacités WMS...")
        response = requests.get(f'{base_url}/wms', 
                              auth=auth, 
                              timeout=10,
                              params={'request': 'GetCapabilities', 'service': 'WMS'})
        
        if response.status_code == 200:
            print("✅ Service WMS accessible!")
            if 'WMS_Capabilities' in response.text:
                print("✅ Réponse WMS valide")
            else:
                print("⚠️ Réponse inattendue du WMS")
        else:
            print(f"❌ Erreur WMS: {response.status_code}")
            
        return True
        
    except requests.exceptions.ConnectTimeout:
        print("❌ TIMEOUT DE CONNEXION - GeoServer non accessible")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ ERREUR DE CONNEXION: {e}")
        return False
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False

if __name__ == "__main__":
    success = test_geoserver_connection()
    
    print("\n" + "="*50)
    if success:
        print("🎉 VOTRE CONFIGURATION FONCTIONNE!")
        print("Vous pouvez accéder à GeoServer à distance avec vos identifiants.")
    else:
        print("❌ PROBLÈME DE CONFIGURATION")
        print("Vérifiez vos variables d'environnement ou vos identifiants GeoServer.")
    print("="*50)
