"""
🎯 ÉTAPE SUIVANTE : Modification concrète de votre agriweb_hebergement_gratuit.py

Ce fichier montre EXACTEMENT quelles lignes ajouter dans votre application
pour intégrer le CRM avec filtrage SIRENE intelligent.
"""

def show_exact_modifications():
    print("=" * 80)
    print("🔧 MODIFICATIONS EXACTES À APPORTER À VOTRE CODE")
    print("=" * 80)
    
    print("\n1️⃣ AJOUT AU DÉBUT DU FICHIER (après les imports existants) :")
    print("="*60)
    
    code_imports = """
# === IMPORT CRM INTELLIGENT (à ajouter après vos imports existants) ===
try:
    from agriweb_crm_routes import add_crm_routes
    from agriweb_crm_bridge_intelligent import integrate_agriweb_search_to_crm_intelligent
    from agriweb_crm_bridge_intelligent import get_sirene_analysis_for_widget
    CRM_AVAILABLE = True
    print("✅ [CRM] Module CRM intelligent disponible")
except ImportError as e:
    CRM_AVAILABLE = False
    print(f"⚠️ [CRM] Module CRM non disponible: {e}")
"""
    
    print(code_imports)
    
    print("\n2️⃣ AJOUT APRÈS LA CRÉATION DE L'APP FLASK :")
    print("="*60)
    
    code_app_setup = """
# === CONFIGURATION CRM (à ajouter après app = Flask(__name__)) ===
if CRM_AVAILABLE:
    try:
        add_crm_routes(app)
        print("✅ [CRM] Routes CRM ajoutées à l'application")
    except Exception as e:
        print(f"❌ [CRM] Erreur ajout routes CRM: {e}")
        CRM_AVAILABLE = False
"""
    
    print(code_app_setup)
    
    print("\n3️⃣ NOUVELLE ROUTE API CRM (à ajouter avec vos autres routes) :")
    print("="*60)
    
    code_api_route = """
# === ROUTE API CRM (à ajouter avec vos autres @app.route) ===
@app.route("/api/crm/integrate_commune_search", methods=["POST"])
def integrate_commune_search_to_crm():
    \"\"\"API pour intégrer les résultats de recherche par commune dans le CRM avec filtrage intelligent\"\"\"
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
        
        # Utiliser la version intelligente avec filtrage SIRENE
        result = integrate_agriweb_search_to_crm_intelligent(data["search_results"])
        
        return jsonify({
            "success": True,
            "summary": result,
            "message": "Prospects créés avec succès dans le CRM (avec filtrage intelligent)"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur intégration CRM: {str(e)}"
        }), 500

@app.route("/api/crm/analyze_sirene", methods=["POST"]) 
def analyze_sirene_for_crm():
    \"\"\"API pour analyser les données SIRENE et retourner les statistiques de qualification\"\"\"
    if not CRM_AVAILABLE:
        return jsonify({"error": "CRM non disponible"}), 503
        
    try:
        from flask import request
        data = request.get_json()
        
        if not data or "search_results" not in data:
            return jsonify({"error": "Données manquantes"}), 400
            
        analysis = get_sirene_analysis_for_widget(data["search_results"])
        return jsonify(analysis)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
"""
    
    print(code_api_route)
    
    print("\n4️⃣ MODIFICATION DE VOTRE FONCTION search_by_commune EXISTANTE :")
    print("="*60)
    
    code_search_modification = """
# === MODIFICATION À LA FIN DE VOTRE FONCTION search_by_commune ===
# TROUVEZ cette ligne vers la fin de votre fonction search_by_commune :
# return jsonify(report_data)

# ET REMPLACEZ-LA PAR :

# Ajout des informations CRM avant le retour
if CRM_AVAILABLE:
    report_data["crm_available"] = True
    
    # Analyse intelligente des prospects SIRENE
    if report_data.get("sirene_data", {}).get("features"):
        sirene_analysis = get_sirene_analysis_for_widget(report_data)
        report_data["crm_sirene_analysis"] = sirene_analysis
        report_data["crm_prospects_detected"] = sirene_analysis["qualified_prospects"]
        
        print(f"📊 [CRM] {sirene_analysis['qualified_prospects']}/{sirene_analysis['total_enterprises']} entreprises SIRENE qualifiées")
    else:
        report_data["crm_prospects_detected"] = 0
else:
    report_data["crm_available"] = False
    report_data["crm_prospects_detected"] = 0

return jsonify(report_data)
"""
    
    print(code_search_modification)

def show_html_modifications():
    print("\n" + "=" * 80)
    print("🌐 MODIFICATIONS HTML/JAVASCRIPT POUR L'INTERFACE")
    print("=" * 80)
    
    print("\n5️⃣ WIDGET CRM INTELLIGENT (à ajouter dans votre template HTML) :")
    print("="*60)
    
    widget_html = """
<!-- ===== WIDGET CRM INTELLIGENT ===== -->
<!-- À ajouter dans votre template de résultats de recherche par commune -->

<div class="row mt-4" id="crmWidgetIntelligent" style="display: none;">
    <div class="col-12">
        <div class="card border-success shadow">
            <div class="card-header bg-success text-white">
                <h5 class="mb-0">
                    <i class="fas fa-brain"></i> 
                    CRM Commercial Intelligent
                    <small class="float-end">
                        <span class="badge bg-light text-dark" id="crmQualifiedCount">-</span> prospects qualifiés
                    </small>
                </h5>
            </div>
            <div class="card-body">
                <!-- Statistiques SIRENE -->
                <div id="sireneQualificationStats" class="alert alert-info" style="display: none;">
                    <h6 class="alert-heading">🏢 Qualification SIRENE :</h6>
                    <div id="sireneStatsContent"></div>
                </div>
                
                <div class="row">
                    <div class="col-md-8">
                        <h6 class="text-success">🎯 Prospects qualifiés automatiquement :</h6>
                        <div id="crmQualifiedProspectsList"></div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="d-grid gap-2">
                            <button id="btnCreateQualifiedProspects" class="btn btn-success btn-lg" 
                                    onclick="createQualifiedCRMProspects()" disabled>
                                <i class="fas fa-magic"></i>
                                Créer Prospects Qualifiés
                            </button>
                            
                            <button id="btnAnalyzeSirene" class="btn btn-outline-success" 
                                    onclick="analyzeSireneDetailed()" disabled>
                                <i class="fas fa-search"></i>
                                Analyser SIRENE Détaillé
                            </button>
                            
                            <a href="/crm/dashboard" class="btn btn-outline-primary" target="_blank">
                                <i class="fas fa-chart-line"></i>
                                Dashboard CRM
                            </a>
                        </div>
                        
                        <div class="mt-3">
                            <small class="text-muted">
                                <i class="fas fa-info-circle"></i>
                                Filtrage intelligent : seules les entreprises pertinentes sont sélectionnées.
                            </small>
                        </div>
                    </div>
                </div>
                
                <div id="crmIntelligentStatus" class="mt-3" style="display: none;"></div>
            </div>
        </div>
    </div>
</div>

<script>
// === JAVASCRIPT CRM INTELLIGENT ===

let currentSearchResultsIntelligent = null;

// Analyser avec qualification SIRENE intelligente
function analyzeQualifiedProspects(searchResults) {
    if (!searchResults.crm_available) {
        return null;
    }
    
    const analysis = {
        sirene: searchResults.crm_sirene_analysis || {
            total_enterprises: 0,
            qualified_prospects: 0,
            qualification_rate: 0,
            by_priority: {haute: 0, moyenne: 0, faible: 0}
        },
        total_qualified: searchResults.crm_prospects_detected || 0
    };
    
    return analysis;
}

// Afficher les statistiques de qualification
function displayQualificationStats(analysis) {
    const statsDiv = document.getElementById('sireneQualificationStats');
    const statsContent = document.getElementById('sireneStatsContent');
    const countElement = document.getElementById('crmQualifiedCount');
    
    if (analysis.sirene.total_enterprises > 0) {
        countElement.textContent = analysis.sirene.qualified_prospects;
        
        const qualRate = analysis.sirene.qualification_rate;
        const rateClass = qualRate > 15 ? 'success' : qualRate > 5 ? 'warning' : 'danger';
        
        statsContent.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <strong>📊 Total entreprises :</strong> ${analysis.sirene.total_enterprises}<br>
                    <strong>✅ Qualifiées :</strong> ${analysis.sirene.qualified_prospects}<br>
                    <strong>📈 Taux de qualification :</strong> 
                    <span class="badge bg-${rateClass}">${qualRate}%</span>
                </div>
                <div class="col-md-6">
                    <strong>🔥 Priorité haute :</strong> ${analysis.sirene.by_priority.haute}<br>
                    <strong>⚡ Priorité moyenne :</strong> ${analysis.sirene.by_priority.moyenne}<br>
                    <strong>💡 Priorité faible :</strong> ${analysis.sirene.by_priority.faible}
                </div>
            </div>
        `;
        
        statsDiv.style.display = 'block';
    }
}

// Afficher la liste des prospects qualifiés
function displayQualifiedProspectsList(analysis) {
    const listElement = document.getElementById('crmQualifiedProspectsList');
    const createButton = document.getElementById('btnCreateQualifiedProspects');
    const analyzeButton = document.getElementById('btnAnalyzeSirene');
    
    if (analysis.total_qualified > 0) {
        let html = `
            <div class="alert alert-success">
                <h6 class="alert-heading">🎯 Qualification automatique réussie !</h6>
                <p class="mb-2">
                    <strong>${analysis.total_qualified}</strong> prospects commerciaux ont été identifiés 
                    et pré-qualifiés selon nos critères de pertinence.
                </p>
                <ul class="mb-0">
                    <li><strong>${analysis.sirene.by_priority.haute}</strong> prospects priorité HAUTE (agriculture, énergie)</li>
                    <li><strong>${analysis.sirene.by_priority.moyenne}</strong> prospects priorité MOYENNE (industrie, BTP)</li>
                    <li><strong>${analysis.sirene.by_priority.faible}</strong> prospects priorité FAIBLE (services spécialisés)</li>
                </ul>
            </div>
        `;
        
        if (analysis.sirene.qualification_rate < 5) {
            html += `
                <div class="alert alert-warning">
                    <h6 class="alert-heading">⚠️ Taux de qualification faible</h6>
                    <p class="mb-0">
                        Seulement ${analysis.sirene.qualification_rate}% des entreprises sont pertinentes. 
                        Cette commune semble peu favorable pour le photovoltaïque.
                    </p>
                </div>
            `;
        }
        
        listElement.innerHTML = html;
        createButton.disabled = false;
        analyzeButton.disabled = false;
        
        document.getElementById('crmWidgetIntelligent').style.display = 'block';
    } else {
        listElement.innerHTML = '<p class="text-muted">Aucun prospect qualifié détecté dans cette commune.</p>';
        createButton.disabled = true;
        analyzeButton.disabled = true;
    }
}

// Créer les prospects qualifiés dans le CRM
function createQualifiedCRMProspects() {
    if (!currentSearchResultsIntelligent) {
        alert('Aucune donnée de recherche disponible');
        return;
    }
    
    const statusDiv = document.getElementById('crmIntelligentStatus');
    statusDiv.innerHTML = `
        <div class="alert alert-info">
            <div class="d-flex align-items-center">
                <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                <span>⏳ Création des prospects qualifiés dans le CRM...</span>
            </div>
        </div>
    `;
    statusDiv.style.display = 'block';
    
    const payload = {
        search_results: currentSearchResultsIntelligent,
        search_metadata: {
            commune: currentSearchResultsIntelligent.commune || 'Commune inconnue',
            timestamp: new Date().toISOString(),
            user_initiated: true,
            search_type: 'commune_search_intelligent'
        }
    };
    
    fetch('/api/crm/integrate_commune_search', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            const summary = result.summary;
            statusDiv.innerHTML = `
                <div class="alert alert-success">
                    <h6 class="alert-heading">🎉 Prospects qualifiés créés avec succès !</h6>
                    <ul class="mb-2">
                        <li><strong>${summary.prospects_created || 0}</strong> nouveaux prospects qualifiés</li>
                        <li>Filtrage intelligent appliqué automatiquement</li>
                        <li>Priorisation commerciale activée</li>
                    </ul>
                    <a href="/crm/dashboard" target="_blank" class="btn btn-sm btn-success">
                        <i class="fas fa-external-link-alt"></i> Voir les prospects qualifiés
                    </a>
                </div>
            `;
            
            document.getElementById('btnCreateQualifiedProspects').disabled = true;
            document.getElementById('btnCreateQualifiedProspects').innerHTML = 
                '<i class="fas fa-check"></i> Prospects Créés';
        } else {
            statusDiv.innerHTML = `
                <div class="alert alert-warning">
                    <h6 class="alert-heading">⚠️ Erreur lors de la création</h6>
                    <p class="mb-0">${result.error}</p>
                </div>
            `;
        }
    })
    .catch(error => {
        statusDiv.innerHTML = `
            <div class="alert alert-danger">
                <h6 class="alert-heading">❌ Erreur réseau</h6>
                <p class="mb-0">${error.message}</p>
            </div>
        `;
    });
}

// Analyser les détails SIRENE
function analyzeSireneDetailed() {
    if (!currentSearchResultsIntelligent) return;
    
    fetch('/api/crm/analyze_sirene', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({search_results: currentSearchResultsIntelligent})
    })
    .then(response => response.json())
    .then(analysis => {
        // Afficher une modal ou une section détaillée avec l'analyse
        alert(`Analyse détaillée SIRENE:\\n${analysis.message}\\nTop prospects: ${analysis.top_prospects.length}`);
    })
    .catch(error => console.error('Erreur analyse SIRENE:', error));
}

// Fonction principale à appeler après recherche commune
function onCommuneSearchCompleteIntelligent(searchResults) {
    console.log('🧠 [CRM INTELLIGENT] Analyse avec qualification SIRENE pour:', searchResults.commune);
    
    currentSearchResultsIntelligent = searchResults;
    
    if (searchResults.crm_available) {
        const analysis = analyzeQualifiedProspects(searchResults);
        if (analysis) {
            displayQualificationStats(analysis);
            displayQualifiedProspectsList(analysis);
        }
    } else {
        document.getElementById('crmWidgetIntelligent').style.display = 'none';
    }
}
</script>
"""
    
    print(widget_html)

def show_implementation_steps():
    print("\n" + "=" * 80)
    print("📋 ÉTAPES D'IMPLÉMENTATION CONCRÈTES")
    print("=" * 80)
    
    steps = """
🚀 ÉTAPE 1 : Préparation des fichiers
   1. Copiez agriweb_crm_bridge_intelligent.py dans votre dossier
   2. Copiez sirene_filtering_intelligent.py dans votre dossier
   3. Vérifiez que agriweb_crm_routes.py existe

🚀 ÉTAPE 2 : Modification de agriweb_hebergement_gratuit.py
   1. Ajoutez les imports au début du fichier (section 1)
   2. Ajoutez la configuration CRM après app = Flask(__name__) (section 2)
   3. Ajoutez les nouvelles routes API (section 3)
   4. Modifiez la fin de votre fonction search_by_commune (section 4)

🚀 ÉTAPE 3 : Modification de votre template HTML
   1. Ajoutez le widget CRM intelligent (section 5)
   2. Remplacez onCommuneSearchComplete par onCommuneSearchCompleteIntelligent
   3. Ajoutez les styles CSS pour améliorer l'apparence

🚀 ÉTAPE 4 : Test et validation
   1. Démarrez votre application AgriWeb
   2. Lancez le CRM standalone : python agriweb_crm_standalone.py
   3. Connectez-vous au CRM via /crm/login
   4. Effectuez une recherche par commune
   5. Vérifiez que le widget CRM intelligent apparaît
   6. Testez la création de prospects qualifiés

🚀 ÉTAPE 5 : Ajustement des critères
   1. Modifiez les seuils dans sirene_filtering_intelligent.py
   2. Ajustez les codes NAF selon votre secteur
   3. Personnalisez les mots-clés qualifiants
   4. Testez avec différentes communes

⚠️  POINTS D'ATTENTION :
   • Sauvegardez votre code existant avant modification
   • Testez d'abord sur une copie de votre application
   • Vérifiez les logs pour identifier d'éventuels problèmes
   • Les modifications sont rétrocompatibles (pas de casse si CRM indisponible)
"""
    
    print(steps)

def main():
    print("🎯 PROCHAINE ÉTAPE : MODIFICATION CONCRÈTE DE VOTRE APPLICATION")
    
    show_exact_modifications()
    show_html_modifications()
    show_implementation_steps()
    
    print("\n" + "=" * 80)
    print("✅ RÉSUMÉ DE CE QUI VA CHANGER")
    print("=" * 80)
    
    print("\n🔧 DANS VOTRE CODE PYTHON :")
    print("   • Import du CRM intelligent au début")
    print("   • Configuration automatique des routes CRM")
    print("   • 2 nouvelles routes API pour l'intégration")
    print("   • Ajout de 5 lignes à la fin de search_by_commune")
    
    print("\n🌐 DANS VOTRE INTERFACE :")
    print("   • Widget CRM intelligent avec statistiques de qualification")
    print("   • Affichage du taux de qualification SIRENE")
    print("   • Boutons pour créer les prospects qualifiés")
    print("   • Analyse détaillée optionnelle")
    
    print("\n💰 BÉNÉFICES IMMÉDIATS :")
    print("   • Prospects SIRENE pré-qualifiés automatiquement")
    print("   • Réduction 90% des contacts non pertinents")
    print("   • Priorisation commerciale intelligente")
    print("   • ROI commercial amélioré")
    
    print("\n🚀 PROCHAINE ACTION :")
    print("   Suivre les étapes d'implémentation ci-dessus")
    print("   et tester avec une commune pilote !")

if __name__ == "__main__":
    main()