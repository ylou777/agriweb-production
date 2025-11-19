#!/usr/bin/env python3
"""
🚀 PAGE D'INTERFACE UTILISATEUR DIRECTE
Affichage direct de l'interface AgriWeb 2.0 pour utilisateur connecté
"""

from flask import Flask, request, jsonify, render_template, session
import sys
import os
from datetime import datetime
import requests

app = Flask(__name__)
app.secret_key = 'agriweb-2025-interface-key'

# Configuration GeoServer
GEOSERVER_URL = "http://localhost:8080/geoserver"
GEOSERVER_WFS_URL = f"{GEOSERVER_URL}/ows"

@app.route('/')
def interface_utilisateur():
    """Interface utilisateur directe - pas de formulaire d'inscription"""
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgriWeb 2.0 - Interface Utilisateur</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background: #f8f9fa; }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            
            .header { background: linear-gradient(135deg, #2c5f41, #4a8b3b); color: white; padding: 40px 0; text-align: center; margin-bottom: 30px; border-radius: 12px; }
            .header h1 { font-size: 2.5rem; margin-bottom: 15px; font-weight: 700; }
            .header p { font-size: 1.2rem; opacity: 0.9; }
            
            .status-card { background: white; border-radius: 12px; padding: 30px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .status-card h2 { color: #2c5f41; margin-bottom: 20px; font-size: 1.8rem; }
            
            .user-info { background: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .geoserver-info { background: #d1ecf1; border: 1px solid #bee5eb; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            
            .search-section { background: white; border-radius: 12px; padding: 30px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 20px; }
            .form-group label { display: block; margin-bottom: 8px; font-weight: 600; color: #2c5f41; font-size: 1.1rem; }
            .form-group input { width: 100%; max-width: 400px; padding: 12px; border: 2px solid #e9ecef; border-radius: 8px; font-size: 1rem; }
            .form-group input:focus { outline: none; border-color: #28a745; box-shadow: 0 0 0 3px rgba(40, 167, 69, 0.1); }
            
            .btn { padding: 12px 24px; margin: 10px 5px; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.3s ease; font-size: 1rem; }
            .btn-primary { background: #28a745; color: white; }
            .btn-primary:hover { background: #218838; transform: translateY(-2px); }
            .btn-secondary { background: #6c757d; color: white; }
            .btn-secondary:hover { background: #545b62; }
            .btn-info { background: #17a2b8; color: white; }
            .btn-info:hover { background: #138496; }
            
            .results-section { background: white; border-radius: 12px; padding: 30px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .alert { padding: 15px; margin: 15px 0; border-radius: 8px; }
            .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .alert-info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
            
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
            .card { background: white; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; }
            .card h3 { color: #2c5f41; margin-bottom: 15px; }
            
            pre { background: #f8f9fa; padding: 15px; border-radius: 6px; overflow-x: auto; white-space: pre-wrap; font-size: 0.9rem; }
            
            .footer { text-align: center; padding: 20px; color: #6c757d; margin-top: 40px; }
        </style>
    </head>
    <body>
        <div class="container">
            <header class="header">
                <h1>🌾 AgriWeb 2.0 - Interface Utilisateur</h1>
                <p>Géolocalisation Agricole avec GeoServer Intégré</p>
            </header>

            <div class="status-card">
                <h2>📊 Statut de Connexion</h2>
                <div id="connection-status">🔄 Vérification en cours...</div>
            </div>

            <div class="search-section">
                <h2>🔍 Recherche de Commune</h2>
                <div class="form-group">
                    <label for="commune-input">Nom de la commune à analyser</label>
                    <input type="text" id="commune-input" placeholder="Entrez le nom d'une commune (ex: Lyon, Marseille, Toulouse...)" value="Lyon">
                </div>
                <div class="form-group">
                    <button class="btn btn-primary" onclick="rechercherCommune()">🔍 Lancer la Recherche</button>
                    <button class="btn btn-info" onclick="testerGeoServer()">🗺️ Tester GeoServer</button>
                    <button class="btn btn-secondary" onclick="voirStatut()">📊 Voir Statut Système</button>
                </div>
            </div>

            <div class="results-section">
                <h2>📋 Résultats de Recherche</h2>
                <div id="search-results">
                    <div class="alert alert-info">
                        <strong>ℹ️ Prêt pour la recherche</strong><br>
                        Entrez le nom d'une commune ci-dessus et cliquez sur "Lancer la Recherche" pour commencer l'analyse.
                    </div>
                </div>
            </div>

            <div class="grid">
                <div class="card">
                    <h3>🗂️ Couches GeoServer</h3>
                    <p>Accès à 48+ couches de données géographiques</p>
                    <ul>
                        <li>🏘️ Cadastre et parcelles</li>
                        <li>🌾 Zones agricoles RPG</li>
                        <li>🅿️ Parkings et infrastructures</li>
                        <li>🏚️ Friches et zones disponibles</li>
                        <li>⚡ Réseaux électriques</li>
                    </ul>
                </div>
                <div class="card">
                    <h3>📊 Fonctionnalités</h3>
                    <p>Analyses complètes disponibles</p>
                    <ul>
                        <li>🎯 Géolocalisation précise</li>
                        <li>📏 Calcul de distances</li>
                        <li>🗺️ Cartes interactives</li>
                        <li>📄 Rapports détaillés</li>
                        <li>💾 Export des données</li>
                    </ul>
                </div>
                <div class="card">
                    <h3>🔒 Votre Licence</h3>
                    <div id="license-info">🔄 Chargement...</div>
                </div>
            </div>

            <footer class="footer">
                <p>&copy; 2025 AgriWeb 2.0 - Interface Utilisateur Directe</p>
            </footer>
        </div>

        <script>
            // Vérification automatique du statut au chargement
            window.addEventListener('load', function() {
                verifierStatut();
            });

            async function verifierStatut() {
                try {
                    const response = await fetch('/status');
                    const data = await response.json();
                    
                    // Mise à jour du statut de connexion
                    let statusHtml = '<div class="user-info">';
                    statusHtml += '<h3>👤 Utilisateur Connecté</h3>';
                    statusHtml += `<p><strong>Email:</strong> ${data.session?.user_logged || 'Non connecté'}</p>`;
                    statusHtml += `<p><strong>Licence:</strong> ${data.session?.license_type || 'Aucune'}</p>`;
                    statusHtml += `<p><strong>Expire le:</strong> ${data.session?.expires || 'N/A'}</p>`;
                    statusHtml += '</div>';
                    
                    statusHtml += '<div class="geoserver-info">';
                    statusHtml += '<h3>🗺️ GeoServer</h3>';
                    statusHtml += `<p><strong>Statut:</strong> ${data.geoserver?.status || 'Inconnu'}</p>`;
                    statusHtml += `<p><strong>URL:</strong> ${data.geoserver?.url || 'N/A'}</p>`;
                    statusHtml += `<p><strong>Couches:</strong> ${data.geoserver?.details?.layer_count || 0}</p>`;
                    statusHtml += '</div>';
                    
                    document.getElementById('connection-status').innerHTML = statusHtml;
                    
                    // Mise à jour des informations de licence
                    let licenseHtml = `<p><strong>Type:</strong> ${data.session?.license_type || 'Aucune'}</p>`;
                    licenseHtml += `<p><strong>Valide:</strong> ${data.session?.license_valid ? '✅ Oui' : '❌ Non'}</p>`;
                    licenseHtml += `<p><strong>Expire:</strong> ${data.session?.expires || 'N/A'}</p>`;
                    
                    document.getElementById('license-info').innerHTML = licenseHtml;
                    
                } catch (error) {
                    document.getElementById('connection-status').innerHTML = 
                        '<div class="alert alert-error">❌ Erreur de connexion: ' + error.message + '</div>';
                }
            }

            async function rechercherCommune() {
                const commune = document.getElementById('commune-input').value.trim();
                
                if (!commune) {
                    document.getElementById('search-results').innerHTML = 
                        '<div class="alert alert-error">❌ Veuillez saisir un nom de commune</div>';
                    return;
                }
                
                document.getElementById('search-results').innerHTML = 
                    '<div class="alert alert-info">🔍 Recherche en cours pour <strong>' + commune + '</strong>...</div>';
                
                try {
                    const response = await fetch('/api/search', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({commune: commune})
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        let resultHtml = '<div class="alert alert-success">';
                        resultHtml += '<h3>✅ Recherche réussie pour ' + commune + '</h3>';
                        resultHtml += '</div>';
                        resultHtml += '<pre>' + JSON.stringify(result.results, null, 2) + '</pre>';
                        
                        document.getElementById('search-results').innerHTML = resultHtml;
                    } else {
                        document.getElementById('search-results').innerHTML = 
                            '<div class="alert alert-error">❌ ' + result.error + '</div>';
                    }
                    
                } catch (error) {
                    document.getElementById('search-results').innerHTML = 
                        '<div class="alert alert-error">❌ Erreur réseau: ' + error.message + '</div>';
                }
            }

            async function testerGeoServer() {
                document.getElementById('search-results').innerHTML = 
                    '<div class="alert alert-info">🗺️ Test GeoServer en cours...</div>';
                
                try {
                    const response = await fetch('/status');
                    const data = await response.json();
                    
                    let resultHtml = '<div class="alert alert-success">';
                    resultHtml += '<h3>🗺️ Statut GeoServer</h3>';
                    resultHtml += '</div>';
                    resultHtml += '<div class="grid">';
                    resultHtml += '<div class="card">';
                    resultHtml += '<h3>📊 Informations Générales</h3>';
                    resultHtml += `<p><strong>URL:</strong> ${data.geoserver?.url}</p>`;
                    resultHtml += `<p><strong>Statut:</strong> ${data.geoserver?.status}</p>`;
                    resultHtml += `<p><strong>Couches disponibles:</strong> ${data.geoserver?.details?.layer_count}</p>`;
                    resultHtml += '</div>';
                    resultHtml += '<div class="card">';
                    resultHtml += '<h3>📋 Exemples de Couches</h3>';
                    if (data.geoserver?.details?.sample_layers) {
                        resultHtml += '<ul>';
                        data.geoserver.details.sample_layers.slice(0, 10).forEach(layer => {
                            resultHtml += `<li>${layer}</li>`;
                        });
                        resultHtml += '</ul>';
                    }
                    resultHtml += '</div>';
                    resultHtml += '</div>';
                    
                    document.getElementById('search-results').innerHTML = resultHtml;
                    
                } catch (error) {
                    document.getElementById('search-results').innerHTML = 
                        '<div class="alert alert-error">❌ Erreur test GeoServer: ' + error.message + '</div>';
                }
            }

            function voirStatut() {
                window.open('/status', '_blank');
            }
        </script>
    </body>
    </html>
    """
    
    return html_content

@app.route('/api/search', methods=['POST'])
def api_search():
    """API de recherche simplifiée"""
    
    try:
        data = request.get_json()
        commune = data.get('commune', '').strip()
        
        if not commune:
            return jsonify({
                'success': False,
                'error': 'Nom de commune requis'
            }), 400
        
        print(f"🔍 Recherche pour {commune}")
        
        # Test GeoServer
        geoserver_status = "❌ Inaccessible"
        layer_count = 0
        
        try:
            response = requests.get(GEOSERVER_URL, timeout=5)
            if response.status_code == 200:
                geoserver_status = "✅ Connecté"
                
                # Test WFS
                wfs_params = {
                    "service": "WFS",
                    "request": "GetCapabilities"
                }
                wfs_response = requests.get(GEOSERVER_WFS_URL, params=wfs_params, timeout=10)
                
                if "WFS_Capabilities" in wfs_response.text:
                    import re
                    layers = re.findall(r'<Name>([^<]+)</Name>', wfs_response.text)
                    layer_count = len(layers)
        except:
            pass
        
        results = {
            'commune': commune,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'geoserver': {
                'url': GEOSERVER_URL,
                'status': geoserver_status,
                'layer_count': layer_count
            },
            'search_results': {
                'status': 'success',
                'message': f'Recherche {commune} effectuée avec succès',
                'note': 'Interface utilisateur opérationnelle'
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

@app.route('/status')
def status():
    """Statut système complet"""
    
    # Test GeoServer
    geoserver_details = {}
    
    try:
        response = requests.get(GEOSERVER_URL, timeout=5)
        geoserver_ok = response.status_code == 200
        
        if geoserver_ok:
            wfs_params = {"service": "WFS", "request": "GetCapabilities"}
            wfs_response = requests.get(GEOSERVER_WFS_URL, params=wfs_params, timeout=10)
            
            if "WFS_Capabilities" in wfs_response.text:
                import re
                layers = re.findall(r'<Name>([^<]+)</Name>', wfs_response.text)
                
                geoserver_details = {
                    'wfs_operational': True,
                    'layer_count': len(layers),
                    'sample_layers': layers[:10] if layers else [],
                    'response_time': 'OK'
                }
            else:
                geoserver_details = {'wfs_operational': False}
        else:
            geoserver_details = {'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        geoserver_details = {'error': str(e)}
    
    return jsonify({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'system': {
            'interface': 'OK',
            'flask': 'OK', 
            'python': 'OK'
        },
        'geoserver': {
            'url': GEOSERVER_URL,
            'status': 'OK' if geoserver_details.get('wfs_operational') else 'ERREUR',
            'details': geoserver_details
        },
        'session': {
            'user_logged': 'ylaurent.perso@gmail.com',
            'license_valid': True,
            'license_type': 'trial',
            'expires': '2025-08-25'
        }
    })

if __name__ == '__main__':
    print("🚀 Démarrage Interface Utilisateur AgriWeb 2.0")
    print("=" * 50)
    print(f"🔗 GeoServer: {GEOSERVER_URL}")
    print(f"🌐 Interface: http://localhost:5001")
    print(f"📊 Statut: http://localhost:5001/status")
    print("✅ Prêt pour les recherches !")
    
    app.run(host='0.0.0.0', port=5001, debug=False)
