#!/usr/bin/env python3
"""
Test simple pour isoler le problème de boucle infinie
"""

from flask import Flask, jsonify
import time

app = Flask(__name__)

@app.route("/")
def index():
    return "<h1>Test simple</h1><p>Test de base OK</p>"

@app.route("/search_by_commune")
def search_by_commune_simple():
    print(f"🔍 [TEST] Appel à search_by_commune_simple - {time.time()}")
    return jsonify({"message": "Test OK", "timestamp": time.time()})

if __name__ == "__main__":
    print("🚀 Démarrage serveur test simple...")
    app.run(debug=True, host="127.0.0.1", port=5000)