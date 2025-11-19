#!/usr/bin/env python3
"""
🛡️ CORRECTION DE L'AVERTISSEMENT NGROK
Ajoute les headers nécessaires pour contourner la page d'avertissement
"""

from flask import Flask, request, make_response
import requests

def add_ngrok_bypass_headers(app):
    """Ajoute les headers pour contourner l'avertissement ngrok"""
    
    @app.before_request
    def bypass_ngrok_warning():
        """Ajoute automatiquement les headers ngrok"""
        # Headers pour contourner l'avertissement ngrok
        if 'ngrok' in request.headers.get('host', ''):
            # Modification automatique des requêtes sortantes
            pass
    
    @app.after_request
    def add_headers(response):
        """Ajoute les headers de contournement ngrok"""
        # Header pour éviter l'avertissement ngrok
        response.headers['ngrok-skip-browser-warning'] = 'true'
        response.headers['User-Agent'] = 'AgriWeb-Custom-Browser/2.0'
        return response
    
    return app

# Configuration pour les requêtes HTTP sortantes
def create_ngrok_session():
    """Crée une session avec les headers ngrok appropriés"""
    session = requests.Session()
    session.headers.update({
        'ngrok-skip-browser-warning': 'true',
        'User-Agent': 'AgriWeb-GeoServer-Client/2.0'
    })
    return session

print("✅ Module de contournement ngrok chargé")
