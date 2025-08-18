#!/usr/bin/env python3
"""
Serveur Flask minimal pour tester l'endpoint rapport_departement
"""
from flask import Flask, request, render_template
import json

app = Flask(__name__)

# Import des fonctions nécessaires
try:
    from agriweb_source import synthese_departement, fetch_sirene_info
    print("✅ Import des fonctions: OK")
except Exception as e:
    print(f"❌ Erreur import: {e}")

@app.route("/test")
def test_route():
    return "Serveur de test fonctionne !"

@app.route("/rapport_departement", methods=["POST"])
def rapport_departement_test():
    """Version test simplifiée de l'endpoint"""
    try:
        data = request.get_json()
        reports = data.get("data", [])
        
        print(f"📥 [TEST_ENDPOINT] Reçu {len(reports)} rapports")
        
        # Test de la synthèse
        synthese = synthese_departement(reports)
        print(f"📊 [TEST_ENDPOINT] Synthèse: {synthese['nb_agriculteurs']} éleveurs, {synthese['nb_parcelles']} parcelles")
        
        # Réponse simple en JSON au lieu du template pour déboguer
        return {
            "status": "success",
            "synthese": synthese,
            "message": f"Traitement de {len(reports)} rapports réussi"
        }
        
    except Exception as e:
        print(f"❌ [TEST_ENDPOINT] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    print("🚀 [TEST] Démarrage serveur de test...")
    app.run(host="127.0.0.1", port=5001, debug=False)
