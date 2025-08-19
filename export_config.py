import requests
import json
import os

def export_geoserver_config():
    base_url = 'http://localhost:8080/geoserver'
    
    try:
        # Test de connexion
        response = requests.get(f'{base_url}/rest/workspaces', 
                              auth=('admin', 'admin'), timeout=10)
        
        if response.status_code == 200:
            workspaces = response.json()
            print(f'✅ Trouvé {len(workspaces.get("workspaces", {}).get("workspace", []))} workspaces')
            
            # Sauvegarde de la configuration
            with open('geoserver_config_backup.json', 'w') as f:
                json.dump(workspaces, f, indent=2)
            
            print('✅ Configuration sauvegardée dans geoserver_config_backup.json')
            return True
        else:
            print(f'❌ Erreur: {response.status_code}')
            return False
            
    except Exception as e:
        print(f'❌ Erreur de connexion: {e}')
        return False

if __name__ == '__main__':
    export_geoserver_config()
