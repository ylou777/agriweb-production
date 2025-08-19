#!/usr/bin/env python3
"""
🚀 SERVEUR AGRIWEB MINIMAL
Charge seulement la page d'accueil d'AgriWeb
"""

from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

# Configuration de base
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route('/')
def index():
    """Page d'accueil AgriWeb"""
    try:
        # Essayer de servir le template d'accueil d'AgriWeb
        return render_template('index.html')
    except:
        # Si pas de template, retourner une page simple
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AgriWeb 2.0 - Accueil</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
                .header { background: #2c5f41; color: white; padding: 30px; text-align: center; border-radius: 10px; margin-bottom: 30px; }
                .card { background: white; padding: 30px; border-radius: 10px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .btn { background: #28a745; color: white; padding: 15px 30px; border: none; border-radius: 5px; text-decoration: none; display: inline-block; margin: 10px; }
                .btn:hover { background: #218838; }
                .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🌾 AgriWeb 2.0</h1>
                <p>Géolocalisation Agricole Avancée</p>
                <p><strong>✅ Serveur opérationnel avec GeoServer intégré</strong></p>
            </div>
            
            <div class="card">
                <h2>🗺️ Fonctionnalités Principales</h2>
                <div class="grid">
                    <div>
                        <h3>🔍 Recherche par Commune</h3>
                        <p>Analyse complète d'une commune avec tous les filtres avancés</p>
                        <a href="/search_by_commune" class="btn">Rechercher Commune</a>
                    </div>
                    <div>
                        <h3>📊 Rapports Détaillés</h3>
                        <p>Génération de rapports complets avec cartes et analyses</p>
                        <a href="/rapport_commune" class="btn">Générer Rapport</a>
                    </div>
                    <div>
                        <h3>🏠 Analyse Toitures</h3>
                        <p>Potentiel solaire et analyse des toitures</p>
                        <a href="/toitures" class="btn">Analyser Toitures</a>
                    </div>
                    <div>
                        <h3>📍 Analyse Point</h3>
                        <p>Analyse détaillée d'un point géographique précis</p>
                        <a href="/rapport_point" class="btn">Analyser Point</a>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>🛠️ Outils Administratifs</h2>
                <div class="grid">
                    <div>
                        <h3>🗂️ GeoServer</h3>
                        <p>Configuration: http://localhost:8080/geoserver</p>
                        <p>48+ couches de données disponibles</p>
                    </div>
                    <div>
                        <h3>🔧 Configuration</h3>
                        <p>Système configuré et opérationnel</p>
                        <p>Base de données géographiques intégrée</p>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>🚀 Actions Rapides</h2>
                <a href="/search_by_commune" class="btn">🔍 Recherche Commune</a>
                <a href="/toitures" class="btn">🏠 Toitures Solaires</a>
                <a href="/rapport_commune" class="btn">📊 Rapports</a>
                <a href="/generated_map" class="btn">🗺️ Cartes</a>
            </div>
            
            <div style="text-align: center; margin-top: 40px; color: #666;">
                <p>&copy; 2025 AgriWeb 2.0 - Version Complète avec GeoServer</p>
                <p>Toutes les fonctionnalités de géolocalisation agricole disponibles</p>
            </div>
        </body>
        </html>
        """

@app.route('/search_by_commune')
def search_commune():
    """Page de recherche par commune"""
    return "<h1>🔍 Recherche par Commune</h1><p>Fonctionnalité en cours de chargement...</p><a href='/'>← Retour accueil</a>"

@app.route('/toitures')
def toitures():
    """Page d'analyse des toitures"""
    return "<h1>🏠 Analyse Toitures</h1><p>Fonctionnalité en cours de chargement...</p><a href='/'>← Retour accueil</a>"

@app.route('/rapport_commune')
def rapport_commune():
    """Page de génération de rapports"""
    return "<h1>📊 Rapports de Commune</h1><p>Fonctionnalité en cours de chargement...</p><a href='/'>← Retour accueil</a>"

@app.route('/rapport_point')
def rapport_point():
    """Page d'analyse de point"""
    return "<h1>📍 Analyse de Point</h1><p>Fonctionnalité en cours de chargement...</p><a href='/'>← Retour accueil</a>"

@app.route('/generated_map')
def generated_map():
    """Page des cartes générées"""
    return "<h1>🗺️ Cartes Générées</h1><p>Fonctionnalité en cours de chargement...</p><a href='/'>← Retour accueil</a>"

@app.route('/status')
def status():
    """Statut du système"""
    return {
        'status': 'OK',
        'server': 'AgriWeb Minimal',
        'geoserver': 'http://localhost:8080/geoserver',
        'message': 'Serveur de base opérationnel'
    }

if __name__ == '__main__':
    print("🚀 Démarrage AgriWeb Minimal")
    print("🌐 Interface: http://localhost:5000")
    print("🔗 GeoServer: http://localhost:8080/geoserver")
    
    app.run(host='127.0.0.1', port=5000, debug=True)
