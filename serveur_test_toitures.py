#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Serveur Flask minimal pour test de recherche toiture
"""

from flask import Flask, request, jsonify
import traceback

def safe_print(*args, **kwargs):
    """Version sécurisée de print pour éviter WinError 233"""
    try:
        print(*args, **kwargs)
    except OSError:
        pass  # Ignore les erreurs de sortie console

app = Flask(__name__)

@app.route('/')
def home():
    return "Serveur de test toitures fonctionnel"

@app.route('/test_toiture')
def test_toiture():
    """Test simple de recherche toiture sans complexité"""
    try:
        # Récupération sécurisée des paramètres
        commune = request.args.get('commune', 'Test')
        recherche_type = request.args.get('recherche_type', 'toiture')
        
        safe_print(f"[TEST] Recherche {recherche_type} pour {commune}")
        
        return jsonify({
            "status": "success",
            "commune": commune,
            "recherche_type": recherche_type,
            "message": "Test de recherche toiture réussi"
        })
        
    except Exception as e:
        safe_print(f"[ERREUR] {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.errorhandler(500)
def handle_500(e):
    tb = traceback.format_exc()
    safe_print(f"[500 ERROR] {e}")
    safe_print(f"[TRACEBACK] {tb}")
    return jsonify({"error": str(e), "traceback": tb}), 500

if __name__ == '__main__':
    safe_print("🧪 [TEST] Démarrage du serveur de test toitures...")
    try:
        app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)
    except Exception as e:
        safe_print(f"❌ [ERREUR SERVEUR] {e}")
        traceback.print_exc()
