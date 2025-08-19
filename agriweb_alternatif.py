#!/usr/bin/env python3
"""
🚀 AGRIWEB SANS PYPROJ - VERSION ALTERNATIVE
Version d'AgriWeb qui fonctionne sans PyProj en cas de problème
"""

import sys
import os

# Ajouter le chemin du module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Imports de base
from flask import Flask, render_template, request, jsonify
import folium
import requests
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    """Page d'accueil AgriWeb"""
    return render_template('index.html')

@app.route('/search_by_commune')
def search_commune():
    """Page de recherche par commune"""
    return render_template('commune_search.html')

@app.route('/toitures')
def toitures():
    """Page d'analyse des toitures"""
    return render_template('recherche_toitures.html')

@app.route('/rapport_commune')
def rapport_commune():
    """Page de rapport de commune"""
    return render_template('rapport_commune.html')

@app.route('/rapport_point')
def rapport_point():
    """Page de rapport de point"""
    return render_template('rapport_point.html')

@app.route('/generated_map')
def generated_map():
    """Page des cartes générées"""
    # Créer une carte simple avec Folium
    m = folium.Map(location=[46.603354, 1.888334], zoom_start=6)
    folium.Marker([46.603354, 1.888334], popup="France").add_to(m)
    
    map_html = m._repr_html_()
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgriWeb - Cartes</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>Cartes AgriWeb</h1>
        <a href="/">← Retour accueil</a>
        <div style="margin: 20px 0;">
            {map_html}
        </div>
    </body>
    </html>
    """

@app.route('/api/status')
def api_status():
    """API de statut"""
    return jsonify({
        'status': 'OK',
        'timestamp': datetime.now().isoformat(),
        'server': 'AgriWeb Alternative (sans PyProj)',
        'message': 'Serveur fonctionnel'
    })

if __name__ == '__main__':
    print("🚀 AgriWeb Alternative - Démarrage sans PyProj")
    print("🌐 Interface: http://localhost:5000")
    print("📊 Fonctionnalités de base disponibles")
    
    app.run(host='127.0.0.1', port=5000, debug=True)
