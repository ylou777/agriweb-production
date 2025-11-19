"""
Utilitaire pour obtenir automatiquement l'URL ngrok actuelle
et mettre à jour l'application
"""
import requests
import json
import re

def get_current_ngrok_url():
    """Récupère l'URL ngrok actuelle via l'API locale"""
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=3)
        if response.status_code == 200:
            data = response.json()
            for tunnel in data.get('tunnels', []):
                if tunnel.get('proto') == 'https':
                    return tunnel.get('public_url')
    except Exception as e:
        print(f"Erreur récupération URL ngrok: {e}")
    return None

def update_app_with_ngrok_url():
    """Met à jour automatiquement l'app avec la nouvelle URL ngrok"""
    current_url = get_current_ngrok_url()
    if current_url:
        geoserver_url = f"{current_url}/geoserver"
        print(f"🔄 Nouvelle URL GeoServer: {geoserver_url}")
        
        # Mettre à jour le fichier Python
        try:
            with open('agriweb_hebergement_gratuit.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remplacer la première URL dans la liste
            pattern = r'("https://[a-f0-9]+\.ngrok-free\.app/geoserver",\s*# URL ngrok actuelle)'
            replacement = f'"{geoserver_url}",  # URL ngrok actuelle (auto-update)'
            
            updated_content = re.sub(pattern, replacement, content)
            
            with open('agriweb_hebergement_gratuit.py', 'w', encoding='utf-8') as f:
                f.write(updated_content)
                
            print("✅ Application mise à jour avec la nouvelle URL ngrok")
            return True
            
        except Exception as e:
            print(f"❌ Erreur mise à jour: {e}")
    
    return False

if __name__ == "__main__":
    update_app_with_ngrok_url()
