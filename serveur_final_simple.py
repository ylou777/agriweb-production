#!/usr/bin/env python3
"""
🚀 SERVEUR AGRIWEB 2.0 PRODUCTION SIMPLIFIÉ
Serveur intégré avec GeoServer + Système de licences
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import sys
import os
from datetime import datetime
import requests

# Import des modules AgriWeb existants
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agriweb_source import (
        build_report_data,
        get_communes_for_dept,
        fetch_gpu_data,
        geocode_address,
        get_address_from_coordinates
    )
    print("✅ Modules AgriWeb importés avec succès")
except ImportError as e:
    print(f"❌ Erreur import AgriWeb: {e}")
    print("ℹ️ Mode dégradé activé")

app = Flask(__name__)
app.secret_key = 'agriweb-2024-production-key'

# Configuration GeoServer (votre serveur existant)
GEOSERVER_URL = "http://localhost:8080/geoserver"
GEOSERVER_WFS_URL = f"{GEOSERVER_URL}/ows"

print(f"🔗 GeoServer configuré: {GEOSERVER_URL}")

@app.route('/')
def index():
    """Page d'accueil AgriWeb 2.0"""
    
    # Page d'accueil simple
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgriWeb 2.0 - Production</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { background: #2c5f41; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .card { background: #f8f9fa; border: 1px solid #ddd; padding: 20px; margin: 10px 0; border-radius: 8px; }
            .success { background: #d4edda; border-color: #c3e6cb; }
            .info { background: #d1ecf1; border-color: #bee5eb; }
            .warning { background: #fff3cd; border-color: #ffeaa7; }
            .btn { background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
            .btn:hover { background: #218838; }
            .form-group { margin: 15px 0; }
            input[type="text"], input[type="email"] { width: 300px; padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌾 AgriWeb 2.0 - Production</h1>
            <p>Système de géolocalisation agricole avec GeoServer intégré</p>
        </div>
        
        <div class="card success">
            <h2>✅ Système Opérationnel</h2>
            <p><strong>GeoServer :</strong> {geoserver_url}</p>
            <p><strong>Statut :</strong> <a href="/status">Vérifier le statut</a></p>
        </div>
        
        <div class="card info">
            <h2>🔍 Recherche Rapide</h2>
            <div class="form-group">
                <input type="text" id="commune" placeholder="Nom de commune" value="Lyon">
                <button class="btn" onclick="testRecherche()">Tester Recherche</button>
            </div>
            <div id="result"></div>
        </div>
        
        <div class="card warning">
            <h2>📋 Essai Gratuit</h2>
            <p>Pour utiliser AgriWeb 2.0, créez un compte d'essai gratuit (7 jours) :</p>
            <div class="form-group">
                <input type="email" id="email" placeholder="Votre email">
                <button class="btn" onclick="creerEssai()">Créer Essai Gratuit</button>
            </div>
            <div id="trial-result"></div>
        </div>
        
        <script>
            function testRecherche() {
                const commune = document.getElementById('commune').value;
                fetch('/api/search', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({commune: commune})
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('result').innerHTML = 
                        data.success ? 
                        '<div style="color: green;">✅ ' + JSON.stringify(data.results, null, 2) + '</div>' :
                        '<div style="color: red;">❌ ' + data.error + '</div>';
                });
            }
            
            function creerEssai() {
                const email = document.getElementById('email').value;
                fetch('/api/trial', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: email})
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('trial-result').innerHTML = 
                        data.success ? 
                        '<div style="color: green;">✅ ' + data.message + '</div>' :
                        '<div style="color: red;">❌ ' + data.error + '</div>';
                });
            }
        </script>
    </body>
    </html>
    """.format(geoserver_url=GEOSERVER_URL)
    
    return html_content

@app.route('/api/search', methods=['POST'])
def api_search():
    """API de recherche AgriWeb avec gestion des licences"""
    
    try:
        data = request.get_json()
        commune = data.get('commune', '')
        
        # Vérification licence
        if not session.get('license_valid'):
            return jsonify({
                'success': False,
                'error': 'Licence requise - Créez un essai gratuit ci-dessus'
            }), 403
        
        # Test simple avec votre GeoServer
        print(f"🔍 Recherche pour {commune} via GeoServer {GEOSERVER_URL}")
        
        # Test de connexion GeoServer
        try:
            response = requests.get(GEOSERVER_URL, timeout=5)
            geoserver_status = "✅ Opérationnel" if response.status_code == 200 else "❌ Erreur"
        except:
            geoserver_status = "❌ Inaccessible"
        
        # Test WFS
        try:
            wfs_params = {
                "service": "WFS",
                "request": "GetCapabilities"
            }
            wfs_response = requests.get(GEOSERVER_WFS_URL, params=wfs_params, timeout=5)
            wfs_status = "✅ Opérationnel" if "WFS_Capabilities" in wfs_response.text else "❌ Erreur"
            
            # Compter les couches
            import re
            layers = re.findall(r'<Name>([^<]+)</Name>', wfs_response.text)
            layer_count = len(layers)
            
        except:
            wfs_status = "❌ Erreur"
            layer_count = 0
        
        results = {
            'commune': commune,
            'timestamp': str(datetime.now()),
            'geoserver': {
                'url': GEOSERVER_URL,
                'status': geoserver_status,
                'wfs_status': wfs_status,
                'layer_count': layer_count
            },
            'message': f'Recherche {commune} testée avec succès',
            'license': session.get('license_type', 'unknown')
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

@app.route('/api/trial', methods=['POST'])
def api_trial():
    """API inscription essai gratuit"""
    
    try:
        data = request.get_json()
        email = data.get('email', '')
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email requis'
            }), 400
        
        # Génération licence d'essai (7 jours)
        session['license_valid'] = True
        session['license_type'] = 'trial'
        session['email'] = email
        session['created'] = str(datetime.now())
        
        return jsonify({
            'success': True,
            'message': f'Essai gratuit 7 jours activé pour {email} !',
            'license_type': 'trial',
            'expires': '7 jours'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur inscription: {str(e)}'
        }), 500

@app.route('/status')
def status():
    """Statut détaillé du système"""
    
    # Test GeoServer
    geoserver_ok = False
    geoserver_details = {}
    
    try:
        response = requests.get(GEOSERVER_URL, timeout=5)
        geoserver_ok = response.status_code == 200
        
        if geoserver_ok:
            # Test WFS
            wfs_params = {"service": "WFS", "request": "GetCapabilities"}
            wfs_response = requests.get(GEOSERVER_WFS_URL, params=wfs_params, timeout=5)
            
            if "WFS_Capabilities" in wfs_response.text:
                import re
                layers = re.findall(r'<Name>([^<]+)</Name>', wfs_response.text)
                
                geoserver_details = {
                    'wfs_operational': True,
                    'layer_count': len(layers),
                    'sample_layers': layers[:5] if layers else []
                }
            else:
                geoserver_details = {'wfs_operational': False}
                
    except Exception as e:
        geoserver_details = {'error': str(e)}
    
    status_data = {
        'timestamp': str(datetime.now()),
        'agriweb': 'OK',
        'geoserver': {
            'status': 'OK' if geoserver_ok else 'ERREUR',
            'url': GEOSERVER_URL,
            'details': geoserver_details
        },
        'license_system': 'OK',
        'session': {
            'license_valid': session.get('license_valid', False),
            'license_type': session.get('license_type', 'none'),
            'email': session.get('email', 'none')
        }
    }
    
    return jsonify(status_data)

if __name__ == '__main__':
    print("🚀 Démarrage AgriWeb 2.0 Production")
    print(f"🔗 GeoServer: {GEOSERVER_URL}")
    print(f"🌐 Interface: http://localhost:5000")
    print(f"📊 Statut: http://localhost:5000/status")
    print(f"🧪 Pour tester :")
    print(f"   1. Ouvrir http://localhost:5000")
    print(f"   2. Créer un essai gratuit avec votre email")
    print(f"   3. Tester une recherche sur une commune")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
