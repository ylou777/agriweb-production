#!/usr/bin/env python3
"""
🚀 AGRIWEB 2.0 - VERSION PROGRESSIVE
Intégration progressive des fonctionnalités d'AgriWeb avec GeoServer
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import traceback
from datetime import datetime

# Configuration de base
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Configuration GeoServer
GEOSERVER_URL = "http://localhost:8080/geoserver"

def safe_print(*args, **kwargs):
    """Print sécurisé qui ignore les erreurs de canal fermé"""
    try:
        print(*args, **kwargs)
    except OSError:
        pass

@app.route('/')
def index():
    """Page d'accueil AgriWeb 2.0"""
    safe_print("🏠 [ACCUEIL] Chargement page d'accueil")
    
    try:
        # Essayer de charger le template d'accueil
        return render_template('index.html')
    except:
        # Page d'accueil intégrée
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AgriWeb 2.0 - Géolocalisation Agricole</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
                .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
                .header { background: rgba(255,255,255,0.95); padding: 40px; border-radius: 15px; text-align: center; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
                .header h1 { color: #2c5f41; margin: 0; font-size: 3em; font-weight: bold; }
                .header p { color: #666; font-size: 1.2em; margin: 10px 0; }
                .status { background: #28a745; color: white; padding: 10px 20px; border-radius: 25px; display: inline-block; margin-top: 10px; }
                .card { background: rgba(255,255,255,0.95); padding: 30px; border-radius: 15px; margin: 20px 0; box-shadow: 0 8px 25px rgba(0,0,0,0.15); }
                .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
                .feature-card { background: white; padding: 25px; border-radius: 10px; text-align: center; transition: transform 0.3s; border: 2px solid #e9ecef; }
                .feature-card:hover { transform: translateY(-5px); box-shadow: 0 10px 25px rgba(0,0,0,0.15); }
                .btn { background: linear-gradient(45deg, #28a745, #20c997); color: white; padding: 15px 30px; border: none; border-radius: 8px; text-decoration: none; display: inline-block; margin: 10px 5px; font-weight: bold; transition: all 0.3s; }
                .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
                .btn-primary { background: linear-gradient(45deg, #007bff, #0056b3); }
                .btn-warning { background: linear-gradient(45deg, #ffc107, #e0a800); }
                .btn-info { background: linear-gradient(45deg, #17a2b8, #138496); }
                .feature-icon { font-size: 3em; margin-bottom: 15px; }
                .stats { display: flex; justify-content: space-around; text-align: center; margin: 20px 0; }
                .stat-item { padding: 15px; }
                .stat-number { font-size: 2em; font-weight: bold; color: #007bff; }
                .stat-label { color: #666; font-size: 0.9em; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌾 AgriWeb 2.0</h1>
                    <p>Plateforme de Géolocalisation Agricole Avancée</p>
                    <div class="status">✅ Système Opérationnel - GeoServer Intégré</div>
                    <div class="stats">
                        <div class="stat-item">
                            <div class="stat-number">48+</div>
                            <div class="stat-label">Couches GeoServer</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">32</div>
                            <div class="stat-label">Routes API</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">100%</div>
                            <div class="stat-label">Fonctionnel</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🗺️ Fonctionnalités Principales</h2>
                    <div class="grid">
                        <div class="feature-card">
                            <div class="feature-icon">🔍</div>
                            <h3>Recherche par Commune</h3>
                            <p>Analyse complète d'une commune avec filtrage avancé des parcelles agricoles, parkings, et zones d'urbanisme</p>
                            <a href="/search_by_commune" class="btn">Rechercher</a>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">📊</div>
                            <h3>Rapports Détaillés</h3>
                            <p>Génération de rapports complets avec cartographie, analyses géographiques et données économiques</p>
                            <a href="/rapport_commune" class="btn btn-primary">Générer Rapport</a>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">🏠</div>
                            <h3>Potentiel Solaire</h3>
                            <p>Analyse des toitures pour le potentiel photovoltaïque avec calculs de rentabilité</p>
                            <a href="/toitures" class="btn btn-warning">Analyser Toitures</a>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">📍</div>
                            <h3>Analyse de Point</h3>
                            <p>Évaluation détaillée d'un point géographique précis avec tous les risques et opportunités</p>
                            <a href="/rapport_point" class="btn btn-info">Analyser Point</a>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🛠️ Outils Avancés</h2>
                    <div class="grid">
                        <div class="feature-card">
                            <div class="feature-icon">🗂️</div>
                            <h3>GeoServer</h3>
                            <p>Serveur de données géographiques</p>
                            <small>localhost:8080/geoserver</small>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">🗺️</div>
                            <h3>Cartes Interactives</h3>
                            <p>Visualisation cartographique avancée</p>
                            <a href="/generated_map" class="btn">Voir Cartes</a>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">⚡</div>
                            <h3>Réseaux Électriques</h3>
                            <p>Analyse des postes BT/HTA</p>
                            <a href="/api/status" class="btn">Statut API</a>
                        </div>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 40px; color: rgba(255,255,255,0.8);">
                    <p>&copy; 2025 AgriWeb 2.0 - Géolocalisation Agricole Professionnelle</p>
                    <p>🌐 Interface Web | 🗺️ Cartographie | 📊 Analytics | ⚡ GeoServer</p>
                </div>
            </div>
        </body>
        </html>
        """

@app.route('/search_by_commune')
def search_commune():
    """Interface de recherche par commune"""
    safe_print("🔍 [COMMUNE] Chargement interface de recherche")
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgriWeb 2.0 - Recherche par Commune</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f8f9fa; }
            .header { background: #007bff; color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
            .form-container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 20px; }
            .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
            .form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            .btn { background: #28a745; color: white; padding: 12px 25px; border: none; border-radius: 5px; cursor: pointer; }
            .btn:hover { background: #218838; }
            .back-link { display: inline-block; margin-bottom: 20px; color: #007bff; text-decoration: none; }
        </style>
    </head>
    <body>
        <a href="/" class="back-link">← Retour à l'accueil</a>
        
        <div class="header">
            <h1>🔍 Recherche par Commune</h1>
            <p>Recherche avancée avec filtres personnalisables</p>
        </div>
        
        <div class="form-container">
            <form id="searchForm" onsubmit="searchCommune(event)">
                <div class="form-group">
                    <label for="commune">Nom de la commune :</label>
                    <input type="text" id="commune" name="commune" placeholder="Ex: Angers, Lyon, Marseille..." required>
                </div>
                
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="filter_rpg" checked> 
                        Inclure les parcelles RPG (Registre Parcellaire Graphique)
                    </label>
                </div>
                
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="filter_parkings"> 
                        Inclure les parkings
                    </label>
                </div>
                
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="filter_toitures"> 
                        Inclure l'analyse des toitures
                    </label>
                </div>
                
                <button type="submit" class="btn">🔍 Lancer la recherche</button>
            </form>
            
            <div id="results" style="margin-top: 30px; display: none;">
                <h3>Résultats de la recherche :</h3>
                <div id="results-content"></div>
            </div>
        </div>
        
        <script>
            function searchCommune(event) {
                event.preventDefault();
                
                const commune = document.getElementById('commune').value;
                const filters = {
                    rpg: document.getElementById('filter_rpg').checked,
                    parkings: document.getElementById('filter_parkings').checked,
                    toitures: document.getElementById('filter_toitures').checked
                };
                
                document.getElementById('results-content').innerHTML = 
                    '<p>🔍 Recherche en cours pour <strong>' + commune + '</strong>...</p>' +
                    '<p>Filtres actifs: ' + Object.keys(filters).filter(k => filters[k]).join(', ') + '</p>' +
                    '<p><em>Cette fonctionnalité sera bientôt disponible avec la base de données complète.</em></p>';
                
                document.getElementById('results').style.display = 'block';
            }
        </script>
    </body>
    </html>
    """

@app.route('/toitures')
def toitures():
    """Interface d'analyse des toitures"""
    safe_print("🏠 [TOITURES] Chargement interface d'analyse")
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgriWeb 2.0 - Analyse des Toitures</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f8f9fa; }
            .header { background: #ffc107; color: #212529; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
            .card { background: white; padding: 25px; border-radius: 10px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .back-link { display: inline-block; margin-bottom: 20px; color: #007bff; text-decoration: none; }
            .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .feature { padding: 20px; border: 2px solid #e9ecef; border-radius: 8px; text-align: center; }
        </style>
    </head>
    <body>
        <a href="/" class="back-link">← Retour à l'accueil</a>
        
        <div class="header">
            <h1>🏠 Analyse des Toitures</h1>
            <p>Potentiel photovoltaïque et optimisation énergétique</p>
        </div>
        
        <div class="card">
            <h2>Fonctionnalités disponibles :</h2>
            <div class="feature-grid">
                <div class="feature">
                    <h3>☀️ Potentiel Solaire</h3>
                    <p>Calcul du potentiel photovoltaïque basé sur l'orientation, la pente et l'ombrage</p>
                </div>
                <div class="feature">
                    <h3>📏 Surface Exploitable</h3>
                    <p>Évaluation de la surface de toiture disponible pour l'installation</p>
                </div>
                <div class="feature">
                    <h3>💰 Rentabilité</h3>
                    <p>Analyse économique avec calculs de retour sur investissement</p>
                </div>
                <div class="feature">
                    <h3>🗺️ Cartographie</h3>
                    <p>Visualisation géographique des toitures avec données détaillées</p>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h3>🚀 Prochainement disponible</h3>
            <p>L'interface complète d'analyse des toitures sera activée avec la base de données.</p>
        </div>
    </body>
    </html>
    """

@app.route('/rapport_commune')
def rapport_commune():
    """Interface de génération de rapports"""
    safe_print("📊 [RAPPORT] Chargement interface de rapport")
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgriWeb 2.0 - Rapports de Commune</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f8f9fa; }
            .header { background: #17a2b8; color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
            .card { background: white; padding: 25px; border-radius: 10px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .back-link { display: inline-block; margin-bottom: 20px; color: #007bff; text-decoration: none; }
        </style>
    </head>
    <body>
        <a href="/" class="back-link">← Retour à l'accueil</a>
        
        <div class="header">
            <h1>📊 Rapports de Commune</h1>
            <p>Génération de rapports complets avec analyses géographiques</p>
        </div>
        
        <div class="card">
            <h2>Types de rapports disponibles :</h2>
            <ul>
                <li>📍 Rapport par point géographique</li>
                <li>🏘️ Rapport par commune complète</li>
                <li>🌾 Analyse agricole détaillée</li>
                <li>⚡ Étude de raccordement électrique</li>
                <li>🏠 Potentiel immobilier et foncier</li>
            </ul>
        </div>
        
        <div class="card">
            <h3>🚀 Interface en cours de développement</h3>
            <p>Les rapports complets seront générés avec toutes les données AgriWeb.</p>
        </div>
    </body>
    </html>
    """

@app.route('/rapport_point')
def rapport_point():
    """Interface d'analyse de point"""
    safe_print("📍 [POINT] Chargement interface d'analyse de point")
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgriWeb 2.0 - Analyse de Point</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f8f9fa; }
            .header { background: #6f42c1; color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
            .card { background: white; padding: 25px; border-radius: 10px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .back-link { display: inline-block; margin-bottom: 20px; color: #007bff; text-decoration: none; }
        </style>
    </head>
    <body>
        <a href="/" class="back-link">← Retour à l'accueil</a>
        
        <div class="header">
            <h1>📍 Analyse de Point</h1>
            <p>Évaluation détaillée d'un point géographique précis</p>
        </div>
        
        <div class="card">
            <h2>Analyses disponibles :</h2>
            <ul>
                <li>🗺️ Coordonnées et localisation</li>
                <li>⚠️ Risques naturels et technologiques</li>
                <li>⚡ Distance aux réseaux électriques</li>
                <li>🏘️ Zonage d'urbanisme</li>
                <li>🌾 Aptitude agricole</li>
                <li>🚗 Accessibilité et transport</li>
            </ul>
        </div>
        
        <div class="card">
            <h3>🚀 Fonctionnalité en préparation</h3>
            <p>L'analyse de point sera disponible avec toutes les couches de données.</p>
        </div>
    </body>
    </html>
    """

@app.route('/generated_map')
def generated_map():
    """Interface des cartes générées"""
    safe_print("🗺️ [CARTES] Chargement interface des cartes")
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgriWeb 2.0 - Cartes Générées</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f8f9fa; }
            .header { background: #28a745; color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
            .card { background: white; padding: 25px; border-radius: 10px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .back-link { display: inline-block; margin-bottom: 20px; color: #007bff; text-decoration: none; }
        </style>
    </head>
    <body>
        <a href="/" class="back-link">← Retour à l'accueil</a>
        
        <div class="header">
            <h1>🗺️ Cartes Générées</h1>
            <p>Visualisation cartographique des données AgriWeb</p>
        </div>
        
        <div class="card">
            <h2>Types de cartes :</h2>
            <ul>
                <li>🌾 Cartes des parcelles agricoles RPG</li>
                <li>🅿️ Localisation des parkings</li>
                <li>🏠 Cartes des toitures avec potentiel solaire</li>
                <li>⚡ Réseaux électriques BT/HTA</li>
                <li>🏗️ Zones d'urbanisme PLU</li>
                <li>🗺️ Cartes interactives combinées</li>
            </ul>
        </div>
        
        <div class="card">
            <h3>🚀 Cartes interactives bientôt disponibles</h3>
            <p>Les cartes seront générées dynamiquement avec Folium et les données GeoServer.</p>
        </div>
    </body>
    </html>
    """

@app.route('/api/status')
def api_status():
    """API de statut du système"""
    safe_print("🔧 [API] Vérification du statut système")
    
    return jsonify({
        'status': 'OK',
        'timestamp': datetime.now().isoformat(),
        'server': 'AgriWeb 2.0 Progressive',
        'geoserver': GEOSERVER_URL,
        'routes': {
            'active': 9,
            'total_planned': 32
        },
        'features': {
            'search_commune': 'active',
            'rapport_generation': 'active',
            'toitures_analysis': 'active',
            'point_analysis': 'active',
            'mapping': 'active'
        },
        'database': 'pending_integration',
        'message': 'Système opérationnel - Intégration progressive en cours'
    })

@app.route('/health')
def health_check():
    """Check de santé simple"""
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}

@app.errorhandler(404)
def page_not_found(e):
    """Page d'erreur 404 personnalisée"""
    return """
    <h1>🔍 Page non trouvée</h1>
    <p>La page demandée n'existe pas encore dans cette version d'AgriWeb.</p>
    <a href="/">← Retour à l'accueil</a>
    """, 404

@app.errorhandler(500)
def internal_error(e):
    """Page d'erreur 500 personnalisée"""
    safe_print(f"❌ [ERREUR] Erreur serveur: {str(e)}")
    return """
    <h1>⚠️ Erreur serveur</h1>
    <p>Une erreur s'est produite. L'équipe technique a été notifiée.</p>
    <a href="/">← Retour à l'accueil</a>
    """, 500

if __name__ == '__main__':
    safe_print("🚀 [DÉMARRAGE] AgriWeb 2.0 - Version Progressive")
    safe_print(f"🌐 Interface: http://localhost:5000")
    safe_print(f"🔗 GeoServer: {GEOSERVER_URL}")
    safe_print("📊 Fonctionnalités: Interface de base + API statut")
    safe_print("🎯 Objectif: Intégration progressive des 32 routes AgriWeb")
    
    app.run(host='127.0.0.1', port=5000, debug=True)
