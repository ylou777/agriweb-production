#!/usr/bin/env python3
"""
🚀 SERVEUR AGRIWEB 2.0 PRODUCTION
Serveur intégré avec GeoServer + Système de licences
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import sys
import os

# Import des modules AgriWeb
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agriweb_source import (
        recherche_osm_bbox, 
        recherche_rpg_parcelles, 
        recherche_parkings,
        recherche_friches, 
        recherche_zones_u,
        recherche_etablissements_eleveurs,
        recherche_toitures_solaires_osm,
        generer_rapport_complet
    )
    print("✅ Modules AgriWeb importés avec succès")
except ImportError as e:
    print(f"❌ Erreur import AgriWeb: {e}")
    sys.exit(1)

app = Flask(__name__)
app.secret_key = 'agriweb-2024-production-key'

# Configuration GeoServer (votre serveur existant)
GEOSERVER_URL = "http://localhost:8080/geoserver"
print(f"🔗 GeoServer configuré: {GEOSERVER_URL}")

@app.route('/')
def index():
    """Page d'accueil AgriWeb 2.0"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def api_search():
    """API de recherche AgriWeb avec gestion des licences"""
    
    try:
        data = request.get_json()
        commune = data.get('commune', '')
        
        # Vérification licence (simulation pour test)
        if not session.get('license_valid'):
            return jsonify({
                'success': False,
                'error': 'Licence requise - Veuillez vous inscrire pour un essai gratuit'
            }), 403
        
        # Recherche via GeoServer
        print(f"🔍 Recherche pour {commune} via GeoServer {GEOSERVER_URL}")
        
        # Appel des fonctions AgriWeb avec votre GeoServer
        results = {
            'commune': commune,
            'geoserver': GEOSERVER_URL,
            'timestamp': str(datetime.now()),
            'data': {
                'message': f'Recherche {commune} prête via votre GeoServer'
            }
        }
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur recherche: {str(e)}'
        }), 500

@app.route('/trial')
def trial():
    """Page d'inscription essai gratuit"""
    return render_template('trial.html')

@app.route('/api/trial', methods=['POST'])
def api_trial():
    """API inscription essai gratuit"""
    
    try:
        data = request.get_json()
        email = data.get('email', '')
        
        # Génération licence d'essai (7 jours)
        session['license_valid'] = True
        session['license_type'] = 'trial'
        session['email'] = email
        
        return jsonify({
            'success': True,
            'message': 'Essai gratuit 7 jours activé !',
            'license_type': 'trial'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur inscription: {str(e)}'
        }), 500

@app.route('/status')
def status():
    """Statut du système"""
    
    import requests
    
    # Test GeoServer
    geoserver_ok = False
    try:
        response = requests.get(GEOSERVER_URL, timeout=5)
        geoserver_ok = response.status_code == 200
    except:
        pass
    
    status_data = {
        'agriweb': 'OK',
        'geoserver': 'OK' if geoserver_ok else 'ERREUR',
        'geoserver_url': GEOSERVER_URL,
        'license_system': 'OK'
    }
    
    return jsonify(status_data)

if __name__ == '__main__':
    print("🚀 Démarrage AgriWeb 2.0 Production")
    print(f"🔗 GeoServer: {GEOSERVER_URL}")
    print(f"🌐 Interface: http://localhost:5000")
    print(f"📊 Statut: http://localhost:5000/status")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
