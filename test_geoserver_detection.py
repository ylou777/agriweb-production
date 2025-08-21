import os
import requests

def detect_working_geoserver():
    """Détecte automatiquement une URL GeoServer fonctionnelle"""
    
    # Priorité 1: Variable d'environnement (faire confiance directement sur Railway)
    env_url = os.getenv("GEOSERVER_URL")
    if env_url:
        # En production (Railway/Heroku), faire confiance à la variable d'environnement
        # sans test localhost car le serveur distant ne peut pas se connecter à localhost
        environment = os.getenv("ENVIRONMENT", "").lower()
        if environment in ["production", "railway"] or "railway" in os.environ.get("RAILWAY_ENVIRONMENT", ""):
            print(f"🚀 [PRODUCTION] Utilisation de GEOSERVER_URL: {env_url}")
            return env_url
        
        # En développement local, tester la connectivité
        try:
            response = requests.head(env_url, timeout=5, allow_redirects=True)
            if response.status_code in [200, 302]:
                print(f"✅ [LOCAL] GeoServer accessible via variable d'environnement: {env_url}")
                return env_url
        except Exception as e:
            print(f"⚠️ [LOCAL] Test de la variable d'environnement échoué: {e}")
    
    # Priorité 2: Détection automatique ngrok (développement local uniquement)
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=3)
        if response.status_code == 200:
            data = response.json()
            for tunnel in data.get('tunnels', []):
                if tunnel.get('proto') == 'https':
                    current_url = f"{tunnel.get('public_url')}/geoserver"
                    print(f"🔍 URL ngrok détectée automatiquement: {current_url}")
                    # Tester la connectivité
                    try:
                        test_response = requests.head(current_url, timeout=5, allow_redirects=True)
                        if test_response.status_code in [200, 302]:
                            print(f"✅ GeoServer accessible: {current_url}")
                            return current_url
                    except Exception as e:
                        print(f"❌ Test échoué pour {current_url}: {e}")
                    break
    except Exception as e:
        print(f"⚠️ Détection ngrok échouée: {e}")
    
    print("❌ Aucune URL GeoServer fonctionnelle trouvée")
    return None

if __name__ == "__main__":
    # Test avec variable d'environnement
    os.environ['GEOSERVER_URL'] = 'https://complete-simple-ghost.ngrok-free.app/geoserver'
    
    print("🧪 Test de détection GeoServer:")
    url = detect_working_geoserver()
    print(f"📍 URL finale détectée: {url}")
