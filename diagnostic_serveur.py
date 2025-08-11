#!/usr/bin/env python3
"""
Serveur de diagnostic pour identifier le problème exact
"""

import sys
import traceback
from flask import Flask, request, jsonify

# Créer une app Flask simple pour le diagnostic
app = Flask(__name__)

@app.route("/")
def index():
    return "Serveur de diagnostic OK"

@app.route("/test_search", methods=["GET", "POST"])
def test_search():
    """Test minimal de la logique de recherche"""
    try:
        print("🔍 [DIAGNOSTIC] Début test_search")
        
        # Test récupération paramètres
        commune = request.values.get("commune", "test")
        print(f"📍 [DIAGNOSTIC] Commune: {commune}")
        
        filter_toitures = request.values.get("filter_toitures", "false")
        print(f"🏠 [DIAGNOSTIC] Filter toitures: {filter_toitures}")
        
        # Test réponse JSON simple
        response = {
            "status": "ok",
            "commune": commune,
            "filter_toitures": filter_toitures == "true",
            "message": "Test diagnostic réussi"
        }
        
        print("✅ [DIAGNOSTIC] Réponse créée")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ [DIAGNOSTIC] Erreur: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

if __name__ == "__main__":
    print("🧪 [DIAGNOSTIC] Serveur de test sur port 5002")
    try:
        app.run(host='127.0.0.1', port=5002, debug=True, use_reloader=False)
    except Exception as e:
        print(f"❌ [DIAGNOSTIC] Erreur démarrage: {e}")
        traceback.print_exc()
