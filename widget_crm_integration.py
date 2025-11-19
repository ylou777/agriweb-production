"""
Widget CRM Intelligent - Version intégrée pour AgriWeb

Ce fichier contient le widget CRM qui s'affiche automatiquement
après une recherche par commune lorsque des prospects SIRENE sont détectés.
"""

# Widget CRM JavaScript intégré
WIDGET_CRM_JS = """
<script>
// === WIDGET CRM INTELLIGENT INTÉGRÉ ===
console.log('🎯 [CRM] Widget CRM intelligent chargé');

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

// Créer et afficher le widget CRM
function displayCRMWidget(searchResults) {
    console.log('🧠 [CRM] Analyse des données de recherche pour:', searchResults.commune);
    
    if (!searchResults.crm_available) {
        console.log('⚠️ [CRM] Module CRM non disponible');
        return;
    }
    
    const analysis = analyzeQualifiedProspects(searchResults);
    if (!analysis || analysis.total_qualified === 0) {
        console.log('ℹ️ [CRM] Aucun prospect qualifié détecté');
        return;
    }
    
    // Supprimer le widget existant s'il y en a un
    const existingWidget = document.getElementById('crmWidgetIntelligent');
    if (existingWidget) {
        existingWidget.remove();
    }
    
    // Créer le HTML du widget
    const widgetHTML = `
    <div class="row mt-4" id="crmWidgetIntelligent">
        <div class="col-12">
            <div class="card border-success shadow">
                <div class="card-header bg-success text-white">
                    <h5 class="mb-0">
                        <i class="fas fa-brain"></i> 
                        CRM Commercial Intelligent
                        <small class="float-end">
                            <span class="badge bg-light text-dark">${analysis.total_qualified}</span> prospects qualifiés
                        </small>
                    </h5>
                </div>
                <div class="card-body">
                    <!-- Statistiques SIRENE -->
                    <div class="alert alert-info">
                        <h6 class="alert-heading">🏢 Qualification SIRENE :</h6>
                        <div class="row">
                            <div class="col-md-6">
                                <strong>📊 Total entreprises :</strong> ${analysis.sirene.total_enterprises}<br>
                                <strong>✅ Qualifiées :</strong> ${analysis.sirene.qualified_prospects}<br>
                                <strong>📈 Taux de qualification :</strong> 
                                <span class="badge bg-${analysis.sirene.qualification_rate > 15 ? 'success' : analysis.sirene.qualification_rate > 5 ? 'warning' : 'danger'}">${analysis.sirene.qualification_rate}%</span>
                            </div>
                            <div class="col-md-6">
                                <strong>🔥 Priorité haute :</strong> ${analysis.sirene.by_priority.haute}<br>
                                <strong>⚡ Priorité moyenne :</strong> ${analysis.sirene.by_priority.moyenne}<br>
                                <strong>💡 Priorité faible :</strong> ${analysis.sirene.by_priority.faible}
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-8">
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
                        </div>
                        
                        <div class="col-md-4">
                            <div class="d-grid gap-2">
                                <button id="btnCreateQualifiedProspects" class="btn btn-success btn-lg" 
                                        onclick="createQualifiedCRMProspects()">
                                    <i class="fas fa-magic"></i>
                                    Créer Prospects Qualifiés
                                </button>
                                
                                <button id="btnAnalyzeSirene" class="btn btn-outline-success" 
                                        onclick="analyzeSireneDetailed()">
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
    `;
    
    // Trouver où insérer le widget (après les résultats)
    const resultContainer = document.querySelector('.results-container, .container, #app') || document.body;
    
    // Insérer le widget
    const widgetDiv = document.createElement('div');
    widgetDiv.innerHTML = widgetHTML;
    resultContainer.appendChild(widgetDiv.firstElementChild);
    
    // Stocker les résultats pour les actions
    currentSearchResultsIntelligent = searchResults;
    
    console.log('✅ [CRM] Widget affiché avec', analysis.total_qualified, 'prospects qualifiés');
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
        alert(`Analyse détaillée SIRENE:\n${analysis.message || 'Analyse terminée'}\nNombre de prospects qualifiés: ${analysis.qualified_prospects || 0}`);
    })
    .catch(error => console.error('Erreur analyse SIRENE:', error));
}

// Auto-déclencher l'affichage du widget quand les résultats de recherche sont disponibles
// Cette fonction sera appelée automatiquement par le système
window.checkAndDisplayCRMWidget = function(searchResults) {
    console.log('🔍 [CRM] Vérification automatique du widget pour:', searchResults?.commune);
    if (searchResults && searchResults.crm_available && searchResults.crm_prospects_detected > 0) {
        displayCRMWidget(searchResults);
    }
};

console.log('✅ [CRM] Fonctions du widget CRM prêtes');
</script>
"""

def get_crm_widget_js():
    """Retourne le JavaScript du widget CRM"""
    return WIDGET_CRM_JS

def inject_crm_widget_in_html(html_content, search_results=None):
    """Injecte le widget CRM dans le HTML si des prospects sont détectés"""
    if not search_results or not search_results.get('crm_available'):
        return html_content
    
    # Ajouter le JavaScript du widget avant la fermeture du body
    widget_js = WIDGET_CRM_JS
    
    # Ajouter un script pour déclencher automatiquement l'affichage
    if search_results.get('crm_prospects_detected', 0) > 0:
        auto_trigger = f"""
        <script>
        // Auto-déclenchement du widget CRM
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('🎯 [CRM] Auto-déclenchement du widget');
            const searchResults = {json.dumps(search_results, default=str)};
            if (window.checkAndDisplayCRMWidget) {{
                window.checkAndDisplayCRMWidget(searchResults);
            }}
        }});
        </script>
        """
        widget_js += auto_trigger
    
    # Injecter avant </body>
    if '</body>' in html_content:
        html_content = html_content.replace('</body>', widget_js + '\n</body>')
    else:
        html_content += widget_js
    
    return html_content

if __name__ == "__main__":
    print("🎯 Widget CRM Intelligent - Version intégrée")
    print("Ce module fournit le widget CRM pour AgriWeb")