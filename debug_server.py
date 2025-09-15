#!/usr/bin/env python3
"""
Serveur Flask minimal pour debug
"""

import sys
import os
sys.path.append('.')

from flask import Flask, request, jsonify
import traceback

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Serveur debug actif"

@app.route('/health')
def health():
    return jsonify({"status": "ok", "message": "Serveur de debug fonctionnel"})

@app.route('/search_by_commune')
def search_debug():
    try:
        # Log des paramètres reçus
        print(f"🔍 Paramètres reçus: {dict(request.args)}")
        
        commune = request.args.get('commune', '')
        if not commune:
            return jsonify({"error": "Paramètre commune manquant"}), 400
            
        print(f"📍 Recherche pour: {commune}")
        
        # Import du module principal pour test
        try:
            from agriweb_hebergement_gratuit import search_by_commune as original_search
            print("✅ Import de la fonction de recherche OK")
            
            # Appel de la fonction originale
            result = original_search()
            print("✅ Fonction de recherche exécutée")
            return result
            
        except Exception as e:
            print(f"❌ Erreur dans la fonction de recherche: {e}")
            traceback.print_exc()
            return jsonify({
                "error": f"Erreur fonction recherche: {str(e)}",
                "type": type(e).__name__,
                "traceback": traceback.format_exc()
            }), 500
            
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        traceback.print_exc()
        return jsonify({
            "error": f"Erreur serveur: {str(e)}",
            "type": type(e).__name__
        }), 500

if __name__ == '__main__':
    print("🚀 Démarrage serveur de debug sur port 5001")
    app.run(debug=True, host='0.0.0.0', port=5001)