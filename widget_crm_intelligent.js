
// === WIDGET CRM MODIFIÉ AVEC QUALIFICATION SIRENE ===

// Analyser les résultats avec qualification SIRENE intelligente
function analyzeCRMProspectsIntelligent(searchResults) {
    const analysis = {
        sirene: {
            total: 0,
            qualified: 0,
            by_priority: {haute: 0, moyenne: 0, faible: 0},
            qualification_rate: 0,
            prospects: []
        },
        rpg: [],
        batiments: [],
        parkings: [],
        friches: [],
        total_prospects: 0
    };
    
    // Analyser SIRENE avec qualification
    if (searchResults.sirene_data && searchResults.sirene_data.features) {
        analysis.sirene.total = searchResults.sirene_data.features.length;
        
        // Simuler la qualification côté client (version simplifiée)
        const qualifiedSirene = qualifySireneProspectsClient(searchResults.sirene_data.features);
        analysis.sirene.qualified = qualifiedSirene.length;
        analysis.sirene.qualification_rate = Math.round(qualifiedSirene.length / analysis.sirene.total * 100 * 10) / 10;
        analysis.sirene.prospects = qualifiedSirene.slice(0, 5); // Top 5
        
        // Compter par priorité
        qualifiedSirene.forEach(prospect => {
            analysis.sirene.by_priority[prospect.priority]++;
        });
    }
    
    // Analyser RPG (logique existante simplifiée)
    if (searchResults.rpg_data && searchResults.rpg_data.features) {
        analysis.rpg = searchResults.rpg_data.features.filter(f => 
            f.properties && f.properties.surf_parc > 5
        );
    }
    
    // [Autres analyses...]
    
    analysis.total_prospects = analysis.sirene.qualified + analysis.rpg.length;
    
    return analysis;
}

// Qualification SIRENE côté client (version simplifiée)
function qualifySireneProspectsClient(sireneFeatures) {
    const qualifyingKeywords = [
        'AGRICOLE', 'ELEVAGE', 'CULTURE', 'FERME', 'COOPERATIVE',
        'SOLAIRE', 'PHOTOVOLTAIQUE', 'ENERGIE', 'ELECTRIQUE',
        'HANGAR', 'ENTREPOT', 'BTP', 'CONSTRUCTION', 'INDUSTRIE'
    ];
    
    const priorityNafCodes = {
        '01': 'haute',    // Agriculture
        '35': 'haute',    // Énergie
        '41': 'moyenne',  // Construction
        '42': 'moyenne',  // Génie civil
        '43': 'moyenne',  // Travaux spécialisés
        '24': 'moyenne',  // Métallurgie
        '25': 'moyenne'   // Produits métalliques
    };
    
    const qualified = [];
    
    sireneFeatures.forEach(feature => {
        const props = feature.properties;
        const denomination = (props.denominationUniteLegale || '').toUpperCase();
        const nafCode = props.activitePrincipaleEtablissement || '';
        const naf2Digits = nafCode.substring(0, 2);
        
        let score = 0;
        let priority = 'faible';
        let reasons = [];
        
        // Score par code NAF
        if (priorityNafCodes[naf2Digits]) {
            score += naf2Digits === '01' ? 50 : 30;
            priority = priorityNafCodes[naf2Digits];
            reasons.push('Secteur pertinent');
        }
        
        // Score par mots-clés
        const foundKeywords = qualifyingKeywords.filter(kw => denomination.includes(kw));
        if (foundKeywords.length > 0) {
            score += foundKeywords.length * 15;
            reasons.push('Mots-clés: ' + foundKeywords.slice(0, 2).join(', '));
        }
        
        // Seuil de qualification
        if (score >= 15) {
            qualified.push({
                name: props.denominationUniteLegale || 'Entreprise SIRENE',
                activity: props.libelle_activite || 'Activité inconnue',
                city: props.libelleCommuneEtablissement || '',
                score: score,
                priority: priority,
                reasons: reasons
            });
        }
    });
    
    return qualified.sort((a, b) => b.score - a.score);
}

// Affichage amélioré avec qualification SIRENE
function displayCRMProspectsIntelligent(analysis) {
    const countElement = document.getElementById('crmProspectsCount');
    const listElement = document.getElementById('crmProspectsList');
    const createButton = document.getElementById('btnCreateProspects');
    
    countElement.textContent = analysis.total_prospects;
    
    if (analysis.total_prospects > 0) {
        let html = '';
        
        // Section SIRENE avec qualification
        if (analysis.sirene.qualified > 0) {
            html += `
                <div class="mb-3">
                    <h6 class="text-primary">🏢 Entreprises SIRENE qualifiées</h6>
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="badge bg-success">${analysis.sirene.qualified}/${analysis.sirene.total} qualifiées (${analysis.sirene.qualification_rate}%)</span>
                        <small class="text-muted">
                            <span class="badge bg-danger">${analysis.sirene.by_priority.haute}</span> haute •
                            <span class="badge bg-warning">${analysis.sirene.by_priority.moyenne}</span> moyenne •
                            <span class="badge bg-secondary">${analysis.sirene.by_priority.faible}</span> faible
                        </small>
                    </div>
                    <div class="list-group list-group-flush">
            `;
            
            analysis.sirene.prospects.slice(0, 3).forEach(prospect => {
                const priorityClass = {
                    'haute': 'danger',
                    'moyenne': 'warning', 
                    'faible': 'secondary'
                }[prospect.priority] || 'secondary';
                
                html += `
                    <div class="list-group-item py-1 px-0">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <strong class="text-truncate">${prospect.name}</strong>
                                <br><small class="text-muted">${prospect.activity}</small>
                                <br><small class="text-info">${prospect.reasons.join('; ')}</small>
                            </div>
                            <span class="badge bg-${priorityClass} ms-2">
                                ${prospect.score} pts
                            </span>
                        </div>
                    </div>
                `;
            });
            
            if (analysis.sirene.prospects.length > 3) {
                html += `
                    <div class="list-group-item py-1 px-0 text-center">
                        <small class="text-muted">... et ${analysis.sirene.qualified - 3} autres prospects</small>
                    </div>
                `;
            }
            
            html += '</div></div>';
        }
        
        // Section RPG (logique existante)
        if (analysis.rpg.length > 0) {
            html += `
                <div class="mb-2">
                    <h6 class="text-primary">🌾 Parcelles agricoles (${analysis.rpg.length})</h6>
                    <small class="text-muted">Parcelles > 5ha pour agrivoltaïsme</small>
                </div>
            `;
        }
        
        listElement.innerHTML = html;
        createButton.disabled = false;
    } else {
        listElement.innerHTML = '<p class="text-muted">Aucun prospect qualifié détecté dans cette recherche.</p>';
        createButton.disabled = true;
    }
}

// Fonction mise à jour pour l'appel après recherche commune
function onCommuneSearchCompleteIntelligent(searchResults) {
    console.log('🔍 [CRM INTELLIGENT] Analyse avec qualification SIRENE:', searchResults.commune);
    
    currentSearchResults = searchResults;
    
    if (searchResults.crm_available) {
        const analysis = analyzeCRMProspectsIntelligent(searchResults);
        displayCRMProspectsIntelligent(analysis);
        checkCRMAvailability();
        
        // Afficher statistiques de qualification
        if (analysis.sirene.total > 0) {
            console.log(`📊 [QUALIFICATION] ${analysis.sirene.qualified}/${analysis.sirene.total} entreprises qualifiées (${analysis.sirene.qualification_rate}%)`);
        }
    }
}
