"""
SOLUTION SIMPLE : Ajouter un bouton CRM à votre interface AgriWeb existante

Ce fichier montre la façon la plus simple d'ajouter le CRM à votre application 
sans modifier le code complexe existant.
"""

# Code à ajouter dans votre template HTML principal (probablement dans templates/)
SIMPLE_CRM_INTEGRATION_HTML = '''
<!-- À ajouter dans votre template de résultats de recherche -->

<!-- Widget CRM simple -->
<div class="row mt-3" id="crmWidget" style="display: none;">
    <div class="col-12">
        <div class="card border-success">
            <div class="card-header bg-success text-white">
                <h5 class="mb-0">🎯 Système CRM Commercial</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-8">
                        <p class="mb-2">
                            <strong>Prospects détectés dans cette recherche :</strong>
                            <span id="crmProspectsCount">-</span>
                        </p>
                        <div id="crmProspectsList"></div>
                    </div>
                    <div class="col-md-4 text-end">
                        <button id="btnCreateProspects" class="btn btn-success btn-lg mb-2" 
                                onclick="createCRMProspects()" disabled>
                            📝 Créer Prospects CRM
                        </button>
                        <br>
                        <a href="/crm/dashboard" class="btn btn-outline-success" target="_blank">
                            📊 Dashboard CRM
                        </a>
                        <br>
                        <small class="text-muted">
                            <a href="/crm/login" target="_blank">Se connecter au CRM</a>
                        </small>
                    </div>
                </div>
                
                <div id="crmStatus" class="mt-3" style="display: none;"></div>
            </div>
        </div>
    </div>
</div>

<!-- JavaScript pour le CRM -->
<script>
// Variables globales pour le CRM
let currentSearchData = null;
let crmConnected = false;

// Vérifier si l'utilisateur est connecté au CRM
function checkCRMConnection() {
    fetch('/api/crm/dashboard')
        .then(response => {
            if (response.ok) {
                crmConnected = true;
                document.getElementById('crmWidget').style.display = 'block';
                console.log('✅ CRM connecté');
            } else {
                console.log('ℹ️ CRM non connecté');
            }
        })
        .catch(() => {
            console.log('ℹ️ CRM non disponible');
        });
}

// Analyser les données de recherche pour détecter des prospects
function analyzeCRMProspects(searchData) {
    let prospects = [];
    
    // Analyser les données SIRENE (entreprises)
    if (searchData.sirene && searchData.sirene.features) {
        searchData.sirene.features.forEach(feature => {
            const props = feature.properties;
            prospects.push({
                name: props.denominationUniteLegale || 'Entreprise SIRENE',
                address: props.adresseEtablissement || '',
                city: props.libelleCommuneEtablissement || '',
                source: 'SIRENE',
                type: 'entreprise'
            });
        });
    }
    
    // Analyser les bâtiments agricoles/commerciaux
    if (searchData.batiments && searchData.batiments.features) {
        searchData.batiments.features.forEach(feature => {
            const props = feature.properties;
            if (props.usage === 'agricole' || props.usage === 'commercial' || props.nature === 'hangar') {
                prospects.push({
                    name: `Bâtiment ${props.usage || props.nature}`,
                    address: 'Adresse à déterminer',
                    city: searchData.commune || '',
                    source: 'Bâtiments',
                    type: 'infrastructure'
                });
            }
        });
    }
    
    // Analyser les parcelles RPG importantes
    if (searchData.rpg && searchData.rpg.features) {
        searchData.rpg.features.forEach(feature => {
            const props = feature.properties;
            if (props.surf_parc && props.surf_parc > 5) { // Plus de 5 hectares
                prospects.push({
                    name: `Exploitation agricole (${props.surf_parc} ha)`,
                    address: 'Parcelle agricole',
                    city: searchData.commune || '',
                    source: 'RPG',
                    type: 'agriculture'
                });
            }
        });
    }
    
    return prospects;
}

// Afficher les prospects détectés
function displayCRMProspects(prospects) {
    const countElement = document.getElementById('crmProspectsCount');
    const listElement = document.getElementById('crmProspectsList');
    const createButton = document.getElementById('btnCreateProspects');
    
    countElement.textContent = prospects.length;
    
    if (prospects.length > 0) {
        let html = '<div class="list-group list-group-flush">';
        prospects.slice(0, 5).forEach((prospect, index) => {
            html += `
                <div class="list-group-item py-1">
                    <strong>${prospect.name}</strong> 
                    <span class="badge bg-secondary">${prospect.source}</span>
                    <br><small class="text-muted">${prospect.city}</small>
                </div>
            `;
        });
        
        if (prospects.length > 5) {
            html += `<div class="list-group-item py-1 text-center">
                <small class="text-muted">... et ${prospects.length - 5} autres</small>
            </div>`;
        }
        
        html += '</div>';
        listElement.innerHTML = html;
        createButton.disabled = false;
    } else {
        listElement.innerHTML = '<p class="text-muted">Aucun prospect détecté dans cette recherche.</p>';
        createButton.disabled = true;
    }
}

// Créer les prospects dans le CRM
function createCRMProspects() {
    if (!currentSearchData) {
        alert('Aucune donnée de recherche disponible');
        return;
    }
    
    const statusDiv = document.getElementById('crmStatus');
    statusDiv.innerHTML = '<div class="alert alert-info">⏳ Création des prospects en cours...</div>';
    statusDiv.style.display = 'block';
    
    // Préparer les données pour l'API CRM
    const crmData = {
        search_response: currentSearchData,
        search_params: {
            commune: currentSearchData.commune || 'Commune inconnue',
            timestamp: new Date().toISOString(),
            user_search: true
        }
    };
    
    fetch('/api/crm/integrate_search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(crmData)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            const summary = result.summary;
            statusDiv.innerHTML = `
                <div class="alert alert-success">
                    ✅ <strong>Prospects créés avec succès !</strong><br>
                    • ${summary.prospects_created} nouveaux prospects<br>
                    • ${summary.prospects_skipped} prospects existants ignorés<br>
                    <a href="/crm/dashboard" target="_blank" class="btn btn-sm btn-success mt-2">
                        Voir dans le CRM →
                    </a>
                </div>
            `;
        } else {
            statusDiv.innerHTML = `
                <div class="alert alert-warning">
                    ⚠️ <strong>Erreur :</strong> ${result.error}<br>
                    <small>Vérifiez que vous êtes connecté au CRM</small>
                </div>
            `;
        }
    })
    .catch(error => {
        statusDiv.innerHTML = `
            <div class="alert alert-danger">
                ❌ <strong>Erreur réseau :</strong> ${error.message}
            </div>
        `;
    });
}

// Fonction à appeler après chaque recherche AgriWeb
function onSearchComplete(searchResults) {
    currentSearchData = searchResults;
    
    if (crmConnected) {
        const prospects = analyzeCRMProspects(searchResults);
        displayCRMProspects(prospects);
        document.getElementById('crmWidget').style.display = 'block';
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    checkCRMConnection();
    
    // Si vous avez déjà des résultats de recherche au chargement de la page
    // appelez onSearchComplete(vosResultats) ici
});
</script>
'''

# Code Python à ajouter dans votre application Flask
SIMPLE_CRM_INTEGRATION_PYTHON = '''
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
'''

def create_simple_integration_files():
    """Crée les fichiers pour une intégration simple"""
    
    # Créer le template HTML
    with open('crm_widget_template.html', 'w', encoding='utf-8') as f:
        f.write(SIMPLE_CRM_INTEGRATION_HTML)
    
    # Créer le code Python
    with open('crm_integration_snippet.py', 'w', encoding='utf-8') as f:
        f.write(SIMPLE_CRM_INTEGRATION_PYTHON)
    
    # Créer un guide d'installation
    guide = '''
# 🚀 GUIDE D'INTÉGRATION CRM SIMPLE

## Étapes pour ajouter le CRM à votre AgriWeb existant :

### 1. Ajouter les routes CRM
Dans votre fichier `agriweb_hebergement_gratuit.py`, ajoutez au début :
```python
# Import CRM
try:
    from agriweb_crm_routes import add_crm_routes
    CRM_AVAILABLE = True
except ImportError:
    CRM_AVAILABLE = False

# Après app = Flask(__name__)
if CRM_AVAILABLE:
    add_crm_routes(app)
```

### 2. Ajouter le widget dans votre template HTML
- Copiez le contenu de `crm_widget_template.html`
- Collez-le dans votre template de résultats de recherche
- Placez-le après vos résultats de carte/tableaux

### 3. Connecter les résultats de recherche
Dans votre fonction JavaScript qui traite les résultats de recherche, ajoutez :
```javascript
// Après avoir reçu et affiché vos résultats normaux
onSearchComplete(searchResults);
```

### 4. Tester
1. Démarrez votre application AgriWeb normale
2. Connectez-vous au CRM via `/crm/login`
3. Effectuez une recherche
4. Le widget CRM apparaîtra avec un bouton pour créer des prospects

## URLs importantes :
- `/crm/login` - Connexion CRM
- `/crm/dashboard` - Dashboard des prospects
- `/api/crm/integrate_search` - API d'intégration

## Comptes de test :
- admin@agriweb.com / admin123
- directeur@agriweb.com / director123
- commercial@agriweb.com / commercial123

## Avantages de cette approche :
✅ Aucune modification majeure de votre code existant
✅ Widget optionnel qui n'apparaît que si connecté au CRM
✅ Intégration progressive possible
✅ Fonctionne en parallèle de votre système actuel
'''
    
    with open('GUIDE_INTEGRATION_SIMPLE.md', 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("📁 Fichiers créés :")
    print("   • crm_widget_template.html - Widget à ajouter dans votre template")
    print("   • crm_integration_snippet.py - Code Python à ajouter")
    print("   • GUIDE_INTEGRATION_SIMPLE.md - Guide étape par étape")

if __name__ == "__main__":
    print("🔗 SOLUTION SIMPLE : Intégration CRM dans AgriWeb")
    print("=" * 60)
    
    create_simple_integration_files()
    
    print("\n🎯 RÉSUMÉ :")
    print("Cette solution vous permet d'ajouter un simple widget CRM")
    print("à votre interface AgriWeb existante sans tout refaire.")
    
    print("\n🚀 PROCHAINES ÉTAPES :")
    print("1. Lisez le GUIDE_INTEGRATION_SIMPLE.md")
    print("2. Ajoutez le widget HTML à votre template")
    print("3. Ajoutez les quelques lignes Python")
    print("4. Testez avec votre application actuelle")
    
    print("\n💡 Le widget CRM apparaîtra automatiquement quand :")
    print("   • L'utilisateur est connecté au CRM")
    print("   • Une recherche AgriWeb trouve des prospects")
    print("   • L'utilisateur clique sur 'Créer Prospects CRM'")
    
    print(f"\n🔗 Lien avec vos recherches :")
    print(f"Vos recherches AgriWeb → Détection automatique de prospects")
    print(f"→ Widget CRM → Création en un clic → Dashboard commercial")
    
    print(f"\n📱 Test immédiat :")
    print(f"python agriweb_crm_standalone.py")
    print(f"→ http://localhost:5000")