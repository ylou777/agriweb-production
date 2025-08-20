#!/usr/bin/env python3
"""
Script pour récupérer l'URL ngrok actuelle et la configurer pour Railway
"""
import requests
import json

def get_current_ngrok_url():
    """Récupère l'URL ngrok actuelle"""
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            
            for tunnel in tunnels:
                if tunnel.get('proto') == 'https':
                    public_url = tunnel.get('public_url')
                    if public_url:
                        geoserver_url = f"{public_url}/geoserver"
                        return geoserver_url, public_url
            
            print("❌ Aucun tunnel HTTPS trouvé")
            return None, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion à ngrok: {e}")
        return None, None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None, None

def test_geoserver_connectivity(geoserver_url):
    """Teste la connectivité vers GeoServer"""
    try:
        response = requests.head(geoserver_url, timeout=10, allow_redirects=True)
        return response.status_code in [200, 302]
    except:
        return False

def main():
    print("🔍 Récupération de l'URL ngrok actuelle...")
    
    geoserver_url, ngrok_url = get_current_ngrok_url()
    
    if not geoserver_url:
        print("❌ Impossible de récupérer l'URL ngrok")
        print("Assurez-vous que ngrok est démarré avec: ngrok http 8080")
        return
    
    print(f"✅ URL ngrok trouvée: {ngrok_url}")
    print(f"✅ URL GeoServer: {geoserver_url}")
    
    # Test de connectivité
    print("\n🧪 Test de connectivité...")
    if test_geoserver_connectivity(geoserver_url):
        print("✅ GeoServer accessible via ngrok")
    else:
        print("❌ GeoServer non accessible via ngrok")
        print("Vérifiez que GeoServer est démarré sur le port 8080")
        return
    
    print(f"\n📋 Configuration pour Railway:")
    print(f"Variable d'environnement à configurer:")
    print(f"GEOSERVER_URL = {geoserver_url}")
    
    print(f"\n🚀 Instructions:")
    print(f"1. Allez sur railway.app")
    print(f"2. Ouvrez votre projet 'aware-surprise-production'")
    print(f"3. Allez dans l'onglet 'Variables'")
    print(f"4. Modifiez ou ajoutez: GEOSERVER_URL = {geoserver_url}")
    print(f"5. Railway redémarrera automatiquement avec la nouvelle URL")
    
    print(f"\n💡 Alternative:")
    print(f"Pour un tunnel ngrok permanent, considérez:")
    print(f"- ngrok avec un domaine personnalisé")
    print(f"- Un compte ngrok payant pour des URLs fixes")
    print(f"- Un GeoServer hébergé dans le cloud")

if __name__ == "__main__":
    main()
