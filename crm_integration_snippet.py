
# À ajouter au début de votre fichier agriweb_hebergement_gratuit.py

# Import CRM (optionnel)
try:
    from agriweb_crm_routes import add_crm_routes
    from agriweb_crm_bridge import integrate_agriweb_search_to_crm
    CRM_AVAILABLE = True
    print("✅ CRM disponible")
except ImportError:
    CRM_AVAILABLE = False
    print("⚠️ CRM non disponible")

# Après la création de votre app Flask
if CRM_AVAILABLE:
    add_crm_routes(app)

# Dans votre route de recherche existante, ajoutez ceci :
@app.route("/search_by_address", methods=["GET", "POST"])
def your_existing_search_function():
    # ... votre code existant pour récupérer les données ...
    
    # Votre réponse actuelle (probablement un JSON ou un template)
    search_results = {
        "success": True,
        "commune": commune,
        "sirene": sirene_data,
        "batiments": batiments_data,
        "rpg": rpg_data,
        # ... vos autres données
    }
    
    # NOUVEAU : Ajouter une indication que le CRM est disponible
    if CRM_AVAILABLE:
        search_results["crm_available"] = True
    
    # Retourner votre réponse normale
    return jsonify(search_results)  # ou render_template avec vos données
