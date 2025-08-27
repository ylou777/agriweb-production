#!/usr/bin/env python3
"""
Proxy simple pour rediriger https://agriweb-prod.ngrok-free.app vers GeoServer
"""
from flask import Flask, redirect, request, Response
import requests

app = Flask(__name__)

GEOSERVER_BASE = "http://localhost:8080/geoserver"

@app.route('/')
def root():
    """Rediriger la racine directement vers l'interface GeoServer"""
    return redirect('/web/', code=302)

@app.route('/<path:path>')
def proxy_to_geoserver(path):
    """Proxy toutes les requêtes vers GeoServer"""
    target_url = f"{GEOSERVER_BASE}/{path}"
    
    # Ajouter les paramètres de requête
    if request.query_string:
        target_url += f"?{request.query_string.decode()}"
    
    try:
        # Transférer la requête
        if request.method == 'GET':
            resp = requests.get(
                target_url,
                headers={k: v for k, v in request.headers.items() if k.lower() != 'host'},
                cookies=request.cookies,
                allow_redirects=False
            )
        elif request.method == 'POST':
            resp = requests.post(
                target_url,
                data=request.get_data(),
                headers={k: v for k, v in request.headers.items() if k.lower() != 'host'},
                cookies=request.cookies,
                allow_redirects=False
            )
        else:
            resp = requests.request(
                request.method,
                target_url,
                data=request.get_data(),
                headers={k: v for k, v in request.headers.items() if k.lower() != 'host'},
                cookies=request.cookies,
                allow_redirects=False
            )
        
        # Créer la réponse
        response = Response(
            resp.content,
            status=resp.status_code,
            headers=[(k, v) for k, v in resp.headers.items() if k.lower() not in ['content-encoding', 'transfer-encoding']]
        )
        
        return response
        
    except Exception as e:
        return f"Erreur de connexion à GeoServer: {e}", 502

if __name__ == "__main__":
    print("Démarrage du proxy GeoServer sur le port 3000")
    print(f"Redirection vers: {GEOSERVER_BASE}")
    app.run(host='0.0.0.0', port=3000, debug=False)
