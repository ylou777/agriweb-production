"""
DÉMONSTRATION PRATIQUE - Lien entre vos recherches AgriWeb et le CRM

Ce fichier montre exactement comment connecter votre système de recherche existant au CRM
"""

# Exemple de fonction de votre système actuel
def example_agriweb_search_function():
    """
    Simulation de votre fonction de recherche AgriWeb actuelle
    (similaire à ce qui se passe dans agriweb_hebergement_gratuit.py)
    """
    
    # Vos recherches actuelles retournent probablement quelque chose comme ça:
    search_response = {
        "success": True,
        "commune": "Nantes",
        "coordinates": [47.2184, -1.5536],
        
        # Données SIRENE (entreprises)
        "sirene": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [-1.5536, 47.2184]},
                    "properties": {
                        "denominationUniteLegale": "FERME BIO NANTES",
                        "activitePrincipaleUniteLegale": "01.13Z",
                        "adresseEtablissement": "123 RUE DE LA FERME",
                        "codePostalEtablissement": "44000",
                        "libelleCommuneEtablissement": "NANTES",
                        "siret": "12345678901234"
                    }
                },
                {
                    "type": "Feature", 
                    "geometry": {"type": "Point", "coordinates": [-1.5600, 47.2200]},
                    "properties": {
                        "denominationUniteLegale": "MARAICHAGE ATLANTIQUE",
                        "activitePrincipaleUniteLegale": "01.12Z",
                        "adresseEtablissement": "456 AVENUE AGRICOLE",
                        "codePostalEtablissement": "44100",
                        "libelleCommuneEtablissement": "NANTES"
                    }
                }
            ]
        },
        
        # Données de bâtiments
        "batiments": {
            "type": "FeatureCollection", 
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [-1.5500, 47.2150]},
                    "properties": {
                        "usage": "agricole",
                        "nature": "hangar",
                        "hauteur": 8,
                        "surface": 500
                    }
                }
            ]
        },
        
        # Données RPG (parcelles agricoles)
        "rpg": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-1.5600, 47.2100], [-1.5500, 47.2100], [-1.5500, 47.2200], [-1.5600, 47.2200], [-1.5600, 47.2100]]]
                    },
                    "properties": {
                        "code_cultu": "BTH",
                        "surf_parc": 12.5,  # 12.5 hectares
                        "code_group": "17"
                    }
                }
            ]
        },
        
        # Et d'autres données...
        "parkings": {"type": "FeatureCollection", "features": []},
        "friches": {"type": "FeatureCollection", "features": []},
        "zones_urbanisme": {"type": "FeatureCollection", "features": []}
    }
    
    search_params = {
        "commune": "Nantes",
        "timestamp": "2024-09-14 15:30:00",
        "user_filters": {
            "filter_rpg": True,
            "filter_sirene": True,
            "rpg_min_area": 5,
            "sir_km": 0.05
        }
    }
    
    return search_response, search_params

# DÉMONSTRATION : Comment intégrer vos recherches au CRM
def demo_integration():
    """Démonstration complète de l'intégration"""
    
    print("🚀 DÉMONSTRATION : AgriWeb → CRM")
    print("=" * 50)
    
    # 1. Simuler une recherche AgriWeb (votre fonction actuelle)
    print("1️⃣ Exécution d'une recherche AgriWeb...")
    search_response, search_params = example_agriweb_search_function()
    
    print(f"   ✅ Recherche terminée pour: {search_params['commune']}")
    print(f"   📊 Entreprises trouvées: {len(search_response['sirene']['features'])}")
    print(f"   🏠 Bâtiments trouvés: {len(search_response['batiments']['features'])}")
    print(f"   🌾 Parcelles RPG: {len(search_response['rpg']['features'])}")
    
    # 2. Extraire les prospects avec le module CRM
    print("\n2️⃣ Extraction des prospects pour le CRM...")
    
    try:
        from agriweb_crm_bridge import extract_prospects_from_search_response
        
        prospects_data = extract_prospects_from_search_response(search_response, search_params)
        
        if prospects_data:
            print(f"   ✅ {len(prospects_data['features'])} prospects extraits:")
            
            for i, feature in enumerate(prospects_data['features'], 1):
                props = feature['properties']
                print(f"      {i}. {props.get('name', 'Sans nom')} - {props.get('search_commune', '')}")
                print(f"         Source: {props.get('source_search', 'N/A')}")
                
        else:
            print("   ⚠️ Aucun prospect extrait")
            
    except ImportError:
        print("   ❌ Module CRM non disponible")
        return
    
    # 3. Intégrer au CRM (simulation)
    print("\n3️⃣ Intégration au CRM...")
    
    # Session utilisateur simulée
    user_session = {
        'user_id': 'admin-001',  # ID utilisateur CRM
        'username': 'admin',
        'role': 'admin'
    }
    
    try:
        from agriweb_crm_bridge import integrate_agriweb_search_to_crm
        
        crm_result = integrate_agriweb_search_to_crm(search_response, search_params, user_session)
        
        if crm_result['success']:
            summary = crm_result['summary']
            print(f"   ✅ Intégration réussie!")
            print(f"      • Prospects créés: {summary['prospects_created']}")
            print(f"      • Prospects ignorés: {summary['prospects_skipped']}")
            print(f"      • Erreurs: {len(summary['errors'])}")
            
            if summary['created_prospect_ids']:
                print(f"      • IDs créés: {summary['created_prospect_ids'][:3]}...")
                
        else:
            print(f"   ❌ Erreur: {crm_result['error']}")
            
    except Exception as e:
        print(f"   ❌ Erreur d'intégration: {e}")
    
    print("\n🎯 RÉSULTAT:")
    print("   Vos recherches AgriWeb peuvent maintenant automatiquement")
    print("   créer des prospects dans le CRM commercial !")

# GUIDE D'IMPLÉMENTATION dans votre code existant
def implementation_guide():
    """Guide pour implémenter dans votre code existant"""
    
    implementation_code = '''
# DANS VOTRE FICHIER agriweb_hebergement_gratuit.py
# Ajoutez ces lignes au début du fichier :

try:
    from agriweb_crm_bridge import integrate_agriweb_search_to_crm, is_crm_available
    CRM_AVAILABLE = True
except ImportError:
    CRM_AVAILABLE = False

# DANS VOTRE FONCTION DE RECHERCHE EXISTANTE
# (probablement dans une route comme /search_by_address)

@app.route("/search_by_address", methods=["GET", "POST"])
def search_by_address():
    # ... votre code existant ...
    
    # Après avoir récupéré tous vos résultats :
    search_response = {
        "sirene": sirene_data,
        "batiments": batiments_data, 
        "rpg": rpg_data,
        # ... autres données
    }
    
    search_params = {
        "commune": commune,
        "timestamp": datetime.now().isoformat(),
        # ... autres paramètres
    }
    
    # NOUVELLE PARTIE : Intégration CRM
    if CRM_AVAILABLE and 'user_id' in session:
        try:
            crm_result = integrate_agriweb_search_to_crm(
                search_response, 
                search_params, 
                session
            )
            
            # Ajouter le résultat CRM à votre réponse
            search_response['crm_integration'] = crm_result
            
        except Exception as e:
            print(f"Erreur CRM: {e}")
    
    # ... retourner votre réponse normale avec en plus les données CRM
    return jsonify(search_response)

# DANS VOTRE TEMPLATE HTML
# Ajoutez un bouton pour afficher les prospects créés :

<div class="crm-section" id="crmResults" style="display: none;">
    <h4>🎯 Prospects CRM Créés</h4>
    <div id="crmProspectsList"></div>
    <a href="/crm/dashboard" class="btn btn-success">Voir Dashboard CRM</a>
</div>

<script>
// JavaScript pour afficher les résultats CRM
function displayCRMResults(response) {
    if (response.crm_integration && response.crm_integration.success) {
        const crmSection = document.getElementById('crmResults');
        const prospectsList = document.getElementById('crmProspectsList');
        
        const summary = response.crm_integration.summary;
        prospectsList.innerHTML = `
            <p>✅ ${summary.prospects_created} prospects créés automatiquement</p>
            <p>⏭️ ${summary.prospects_skipped} prospects déjà existants</p>
        `;
        
        crmSection.style.display = 'block';
    }
}
</script>
'''
    
    print("💻 GUIDE D'IMPLÉMENTATION")
    print("=" * 50)
    print(implementation_code)
    
    # Sauvegarder dans un fichier
    with open('IMPLEMENTATION_GUIDE.txt', 'w', encoding='utf-8') as f:
        f.write(implementation_code)
    
    print("\n📁 Guide sauvegardé dans: IMPLEMENTATION_GUIDE.txt")

if __name__ == "__main__":
    print("🔗 CONNEXION AgriWeb ↔ CRM")
    print("Démonstration du lien entre vos recherches et le système commercial")
    print("=" * 70)
    
    # Choisir le mode
    print("\nQue voulez-vous faire ?")
    print("1. Voir la démonstration")
    print("2. Voir le guide d'implémentation")
    print("3. Les deux")
    
    choice = input("\nChoix (1/2/3): ").strip()
    
    if choice in ['1', '3']:
        demo_integration()
    
    if choice in ['2', '3']:
        print("\n" + "=" * 70)
        implementation_guide()
    
    print("\n🎯 CONCLUSION:")
    print("Vos recherches AgriWeb peuvent maintenant alimenter automatiquement")
    print("un système CRM commercial pour convertir les données en prospects !")
    print("\n🚀 Testez avec: python agriweb_crm_standalone.py")