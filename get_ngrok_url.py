#!/usr/bin/env python3
"""Script pour récupérer l'URL du tunnel ngrok"""

import requests
import json
import time

def get_ngrok_url():
    """Récupère l'URL publique du tunnel ngrok"""
    try:
        # Attendre que ngrok soit prêt
        time.sleep(2)
        
        # Récupérer les tunnels via l'API locale ngrok
        response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('tunnels'):
                for tunnel in data['tunnels']:
                    if tunnel.get('config', {}).get('addr') == 'http://localhost:8080':
                        public_url = tunnel.get('public_url', '')
                        if public_url.startswith('https://'):
                            print(f"✅ Tunnel ngrok trouvé : {public_url}")
                            return public_url
                
                # Si on a des tunnels mais pas pour le port 8080
                print("📋 Tunnels disponibles :")
                for tunnel in data['tunnels']:
                    addr = tunnel.get('config', {}).get('addr', 'N/A')
                    url = tunnel.get('public_url', 'N/A')
                    print(f"  - {addr} -> {url}")
            else:
                print("❌ Aucun tunnel ngrok trouvé")
        else:
            print(f"❌ Erreur API ngrok : {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter à l'API ngrok (port 4040)")
        print("   Vérifiez que ngrok est démarré")
    except Exception as e:
        print(f"❌ Erreur : {e}")
    
    return None

def test_geoserver(ngrok_url):
    """Teste la connectivité avec GeoServer via ngrok"""
    if not ngrok_url:
        return False
        
    try:
        geoserver_url = f"{ngrok_url}/geoserver"
        print(f"🧪 Test de connectivité : {geoserver_url}")
        
        response = requests.get(geoserver_url, timeout=10, allow_redirects=True)
        
        if response.status_code in [200, 302]:
            print(f"✅ GeoServer accessible via ngrok (HTTP {response.status_code})")
            
            # Test d'une couche spécifique
            wfs_url = f"{geoserver_url}/wfs"
            params = {
                'service': 'WFS',
                'version': '2.0.0',
                'request': 'GetCapabilities'
            }
            
            wfs_response = requests.get(wfs_url, params=params, timeout=10)
            if wfs_response.status_code == 200:
                print("✅ Service WFS fonctionnel")
                return True
            else:
                print(f"⚠️ Service WFS non accessible (HTTP {wfs_response.status_code})")
                
        else:
            print(f"❌ GeoServer non accessible (HTTP {response.status_code})")
            
    except Exception as e:
        print(f"❌ Erreur lors du test GeoServer : {e}")
    
    return False

if __name__ == "__main__":
    print("🔄 Recherche du tunnel ngrok...")
    
    # Essayer plusieurs fois car ngrok peut mettre du temps à démarrer
    for attempt in range(5):
        ngrok_url = get_ngrok_url()
        
        if ngrok_url:
            # Tester GeoServer
            if test_geoserver(ngrok_url):
                print(f"\n🎉 Configuration réussie !")
                print(f"📋 URL ngrok : {ngrok_url}")
                print(f"📋 GeoServer : {ngrok_url}/geoserver")
                print(f"\n💡 Mettez à jour votre application avec cette URL :")
                print(f"   GEOSERVER_URL = '{ngrok_url}/geoserver'")
                break
            else:
                print("⚠️ GeoServer non accessible via cette URL")
        else:
            print(f"⏳ Tentative {attempt + 1}/5 - Attente du tunnel ngrok...")
            time.sleep(3)
    else:
        print("❌ Impossible de récupérer l'URL du tunnel ngrok")
        print("💡 Vérifiez que ngrok est démarré avec : ngrok http 8080")
