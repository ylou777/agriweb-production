#!/usr/bin/env python3
"""
Configuration automatique de GeoServer avec fallback
"""
import requests
import os

def get_working_geoserver_url():
    """Trouve une URL GeoServer fonctionnelle"""
    
    # URLs possibles par ordre de priorité
    possible_urls = [
        # URL ngrok permanente (Pay-as-you-go)
        "https://complete-simple-ghost.ngrok-free.app/geoserver",
        # URL locale (pour tests)
        "http://localhost:8080/geoserver"
    ]
    
    # Essayer de récupérer l'URL ngrok actuelle
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
        if response.status_code == 200:
            data = response.json()
            for tunnel in data.get('tunnels', []):
                if tunnel.get('proto') == 'https':
                    current_url = f"{tunnel.get('public_url')}/geoserver"
                    possible_urls.insert(0, current_url)
                    break
    except:
        pass
    
    # Tester chaque URL
    for url in possible_urls:
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            if response.status_code in [200, 302]:
                print(f"✅ GeoServer trouvé : {url}")
                return url
        except:
            continue
    
    print("❌ Aucun GeoServer accessible trouvé")
    return None

def update_app_config():
    """Met à jour la configuration de l'app"""
    working_url = get_working_geoserver_url()
    
    if working_url:
        print(f"\n📝 Configuration recommandée :")
        print(f"GEOSERVER_URL = {working_url}")
        
        # Optionnel : écrire dans un fichier .env
        with open('.env.railway', 'w') as f:
            f.write(f"GEOSERVER_URL={working_url}\n")
            f.write(f"FLASK_DEBUG=False\n")
            f.write(f"SECRET_KEY=agriweb-secret-key-2025-commercial\n")
        
        print(f"✅ Configuration sauvée dans .env.railway")
        return working_url
    
    return None

if __name__ == "__main__":
    print("🔍 Recherche d'un GeoServer accessible...")
    url = update_app_config()
    
    if url:
        print(f"\n🚀 Prêt pour Railway !")
        print(f"\nCopiez cette variable dans Railway :")
        print(f"GEOSERVER_URL = {url}")
    else:
        print(f"\n❌ Problème de configuration GeoServer")
        print(f"Assurez-vous que :")
        print(f"1. GeoServer est démarré (port 8080)")
        print(f"2. ngrok est actif : ngrok http 8080")
        print(f"3. Le pare-feu autorise les connexions")
