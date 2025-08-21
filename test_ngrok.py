import requests
import json

try:
    response = requests.get('http://localhost:4040/api/tunnels', timeout=3)
    print(f'Status API ngrok: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        tunnels = data.get('tunnels', [])
        print(f'Nombre de tunnels: {len(tunnels)}')
        
        for tunnel in tunnels:
            public_url = tunnel.get('public_url', 'N/A')
            config = tunnel.get('config', {})
            addr = config.get('addr', 'N/A')
            print(f'Tunnel: {public_url} -> {addr}')
            
except Exception as e:
    print(f'Erreur: {e}')
