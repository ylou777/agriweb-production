
# À ajouter au DÉBUT de votre fichier agriweb_hebergement_gratuit.py (après les imports)

# ===== IMPORT CRM (OPTIONNEL) =====
try:
    from agriweb_crm_routes import add_crm_routes
    from agriweb_crm_bridge import integrate_agriweb_search_to_crm
    CRM_AVAILABLE = True
    print("✅ [CRM] Module CRM disponible")
except ImportError as e:
    CRM_AVAILABLE = False
    print(f"⚠️ [CRM] Module CRM non disponible: {e}")

# À ajouter APRÈS la création de votre app Flask (après app = Flask(__name__))
if CRM_AVAILABLE:
    try:
        add_crm_routes(app)
        print("✅ [CRM] Routes CRM ajoutées à l'application")
    except Exception as e:
        print(f"❌ [CRM] Erreur ajout routes CRM: {e}")
        CRM_AVAILABLE = False

# ===== NOUVELLE ROUTE API POUR L'INTÉGRATION CRM =====
@app.route("/api/crm/integrate_commune_search", methods=["POST"])
def integrate_commune_search_to_crm():
    """API pour intégrer les résultats de recherche par commune dans le CRM"""
    if not CRM_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "Module CRM non disponible"
        }), 503
    
    try:
        from flask import request
        data = request.get_json()
        
        if not data or "search_results" not in data:
            return jsonify({
                "success": False,
                "error": "Données de recherche manquantes"
            }), 400
        
        # Utiliser le module d'intégration existant
        result = integrate_agriweb_search_to_crm(data["search_results"])
        
        return jsonify({
            "success": True,
            "summary": result,
            "message": "Prospects créés avec succès dans le CRM"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur intégration CRM: {str(e)}"
        }), 500

# ===== MODIFICATION DE VOTRE ROUTE SEARCH_BY_COMMUNE EXISTANTE =====
# À ajouter à la FIN de votre fonction search_by_commune(), juste avant le return jsonify()

# Recherchez cette ligne dans votre code (probablement vers la fin de search_by_commune):
# return jsonify(report_data)

# Et remplacez-la par :
# AVANT le return, ajouter :
if CRM_AVAILABLE:
    report_data["crm_available"] = True
    report_data["crm_prospects_detected"] = analyze_crm_prospects_count(report_data)
else:
    report_data["crm_available"] = False

return jsonify(report_data)

# ===== FONCTION HELPER POUR ANALYSER LES PROSPECTS =====
def analyze_crm_prospects_count(report_data):
    """Analyse rapide du nombre de prospects potentiels dans les résultats"""
    count = 0
    
    # Compter les entreprises SIRENE
    sirene_data = report_data.get("sirene_data", {})
    if sirene_data.get("features"):
        count += len(sirene_data["features"])
    
    # Compter les parcelles RPG importantes (>5ha)
    rpg_data = report_data.get("rpg_data", {})
    if rpg_data.get("features"):
        large_parcels = [f for f in rpg_data["features"] 
                        if f.get("properties", {}).get("surf_parc", 0) > 5]
        count += len(large_parcels)
    
    # Compter les bâtiments agricoles/industriels
    batiments_data = report_data.get("batiments_data", {})
    if batiments_data.get("features"):
        suitable_buildings = [f for f in batiments_data["features"]
                             if f.get("properties", {}).get("usage") in ["agricole", "industriel"]]
        count += len(suitable_buildings)
    
    # Compter les parkings importants
    parkings_data = report_data.get("parkings_data", {})
    if parkings_data.get("features"):
        large_parkings = [f for f in parkings_data["features"]
                         if f.get("properties", {}).get("surface", 0) > 3000]
        count += len(large_parkings)
    
    # Compter les friches importantes
    friches_data = report_data.get("friches_data", {})
    if friches_data.get("features"):
        large_friches = [f for f in friches_data["features"]
                        if f.get("properties", {}).get("surface", 0) > 5000]
        count += len(large_friches)
    
    return count
