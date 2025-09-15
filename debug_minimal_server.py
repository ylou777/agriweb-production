#!/usr/bin/env python3
"""
Serveur Flask minimal pour debug des étapes de search_by_commune
"""

from flask import Flask, request, jsonify
import sys
import os
sys.path.append('.')

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Serveur debug minimal actif"

@app.route('/test_step1')
def test_step1():
    """Test étape 1: Paramètres et vérification de base"""
    try:
        print("🔍 ÉTAPE 1: Récupération paramètres")
        commune = request.args.get('commune', '')
        sirene_radius = request.args.get('sirene_radius', '0.05')
        
        print(f"📍 Commune: {commune}")
        print(f"📐 Rayon SIRENE: {sirene_radius}")
        
        if not commune:
            return jsonify({"error": "Paramètre commune manquant"}), 400
            
        return jsonify({
            "status": "OK",
            "etape": "1 - Paramètres",
            "commune": commune,
            "sirene_radius": sirene_radius,
            "message": "Paramètres récupérés avec succès"
        })
    except Exception as e:
        return jsonify({"error": f"Étape 1 échouée: {str(e)}"}), 500

@app.route('/test_step2')
def test_step2():
    """Test étape 2: Import des modules CRM"""
    try:
        print("🔍 ÉTAPE 2: Test imports CRM")
        
        # Test import CRM
        global CRM_AVAILABLE
        try:
            from agriweb_crm_bridge_intelligent import get_sirene_analysis_for_widget
            CRM_AVAILABLE = True
            crm_status = "CRM disponible"
        except Exception as e:
            CRM_AVAILABLE = False
            crm_status = f"CRM indisponible: {e}"
            
        print(f"🎯 {crm_status}")
        
        return jsonify({
            "status": "OK",
            "etape": "2 - Imports CRM",
            "crm_available": CRM_AVAILABLE,
            "crm_status": crm_status
        })
    except Exception as e:
        return jsonify({"error": f"Étape 2 échouée: {str(e)}"}), 500

@app.route('/test_step3')
def test_step3():
    """Test étape 3: Géocodage de la commune"""
    try:
        print("🔍 ÉTAPE 3: Test géocodage")
        import requests
        
        commune = request.args.get('commune', 'Lyon')
        
        # Test géocodage simple
        geocode_url = f"https://api-adresse.data.gouv.fr/search/?q={commune}&type=municipality&limit=1"
        print(f"🌐 URL géocodage: {geocode_url}")
        
        response = requests.get(geocode_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('features'):
                coords = data['features'][0]['geometry']['coordinates']
                lon, lat = coords[0], coords[1]
                
                return jsonify({
                    "status": "OK",
                    "etape": "3 - Géocodage",
                    "commune": commune,
                    "coordinates": [lon, lat],
                    "message": "Géocodage réussi"
                })
            else:
                return jsonify({"error": "Commune non trouvée"}), 404
        else:
            return jsonify({"error": f"Erreur géocodage: {response.status_code}"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Étape 3 échouée: {str(e)}"}), 500

@app.route('/test_complete')
def test_complete():
    """Test complet mais simplifié"""
    try:
        print("🔍 TEST COMPLET SIMPLIFIÉ")
        
        # Étape 1: Paramètres
        commune = request.args.get('commune', 'Lyon')
        print(f"✅ Paramètres: {commune}")
        
        # Étape 2: CRM
        try:
            from agriweb_crm_bridge_intelligent import get_sirene_analysis_for_widget
            crm_available = True
        except:
            crm_available = False
        print(f"✅ CRM: {crm_available}")
        
        # Retour simplifié
        return jsonify({
            "status": "OK",
            "commune": commune,
            "crm_available": crm_available,
            "crm_prospects_detected": 0,
            "message": "Test complet simplifié réussi",
            "sirene_data": {"features": []},
            "rpg_data": {"features": []},
            "parkings_data": {"features": []},
            "friches_data": {"features": []},
            "zones_data": {"features": []},
            "toitures_data": {"features": []},
            "carte_url": "/static/map.html"
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": f"Test complet échoué: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

if __name__ == '__main__':
    print("🚀 Démarrage serveur debug sur port 5001")
    app.run(debug=True, host='0.0.0.0', port=5001)