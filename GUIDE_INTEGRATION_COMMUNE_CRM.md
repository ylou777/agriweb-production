# 🔗 GUIDE D'INTÉGRATION CRM POUR RECHERCHE PAR COMMUNE

## 📋 Vue d'ensemble

Ce guide vous montre comment ajouter un bouton "Créer prospects CRM" directement 
dans l'interface de vos résultats de recherche par commune.

## 🎯 Objectif

Permettre aux utilisateurs de transformer automatiquement les données trouvées 
lors d'une recherche par commune en prospects commerciaux dans le CRM.

## 🚀 Étapes d'installation

### 1️⃣ Modifications Python (agriweb_hebergement_gratuit.py)

```python

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

```

### 2️⃣ Modifications HTML/JavaScript (votre template de résultats)

```html

<!-- À ajouter dans votre template HTML qui affiche les résultats de recherche par commune -->
<!-- Placez ce code APRÈS l'affichage de vos résultats (carte, tableaux, etc.) -->

<!-- ===== WIDGET CRM ===== -->
<div class="row mt-4" id="crmWidget" style="display: none;">
    <div class="col-12">
        <div class="card border-primary shadow">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">
                    <i class="fas fa-users"></i> 
                    Système CRM Commercial
                    <small class="float-end">
                        <span class="badge bg-light text-dark" id="crmProspectsCount">-</span> prospects détectés
                    </small>
                </h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <!-- Information prospects -->
                    <div class="col-md-8">
                        <h6 class="text-primary">📊 Prospects commerciaux identifiés :</h6>
                        <div id="crmProspectsList" class="mb-3">
                            <!-- Liste générée dynamiquement -->
                        </div>
                        
                        <div id="crmAnalysis" class="alert alert-info" style="display: none;">
                            <h6 class="alert-heading">🎯 Analyse commerciale :</h6>
                            <div id="crmAnalysisContent"></div>
                        </div>
                    </div>
                    
                    <!-- Actions CRM -->
                    <div class="col-md-4">
                        <div class="d-grid gap-2">
                            <button id="btnCreateProspects" class="btn btn-primary btn-lg" 
                                    onclick="createCRMProspects()" disabled>
                                <i class="fas fa-plus-circle"></i>
                                Créer Prospects CRM
                            </button>
                            
                            <a href="/crm/dashboard" class="btn btn-outline-primary" target="_blank">
                                <i class="fas fa-chart-line"></i>
                                Dashboard CRM
                            </a>
                            
                            <a href="/crm/login" class="btn btn-outline-secondary btn-sm" target="_blank">
                                <i class="fas fa-sign-in-alt"></i>
                                Se connecter au CRM
                            </a>
                        </div>
                        
                        <div class="mt-3">
                            <small class="text-muted">
                                <i class="fas fa-info-circle"></i>
                                Les prospects seront créés automatiquement à partir des données de cette recherche.
                            </small>
                        </div>
                    </div>
                </div>
                
                <!-- Status des opérations CRM -->
                <div id="crmStatus" class="mt-3" style="display: none;"></div>
            </div>
        </div>
    </div>
</div>

<!-- ===== JAVASCRIPT CRM ===== -->
<script>
// Variables globales pour le CRM
let currentSearchResults = null;
let crmConnected = false;

// Vérifier la disponibilité du CRM
function checkCRMAvailability() {
    fetch('/crm/dashboard')
        .then(response => {
            if (response.ok) {
                crmConnected = true;
                console.log('✅ [CRM] Utilisateur connecté au CRM');
            } else {
                console.log('ℹ️ [CRM] Utilisateur non connecté');
            }
        })
        .catch(() => {
            console.log('⚠️ [CRM] CRM non disponible');
        });
}

// Analyser les résultats de recherche pour détecter des prospects
function analyzeCRMProspects(searchResults) {
    const prospects = {
        sirene: [],
        rpg: [],
        batiments: [],
        parkings: [],
        friches: [],
        total: 0
    };
    
    // Analyser SIRENE (entreprises)
    if (searchResults.sirene_data && searchResults.sirene_data.features) {
        searchResults.sirene_data.features.forEach(feature => {
            const props = feature.properties;
            prospects.sirene.push({
                name: props.denominationUniteLegale || 'Entreprise SIRENE',
                activity: props.libelle_activite || 'Activité inconnue',
                address: props.adresseEtablissement || '',
                city: props.libelleCommuneEtablissement || ''
            });
        });
    }
    
    // Analyser RPG (parcelles importantes)
    if (searchResults.rpg_data && searchResults.rpg_data.features) {
        searchResults.rpg_data.features.forEach(feature => {
            const props = feature.properties;
            const surface = props.surf_parc || 0;
            if (surface > 5) {  // Parcelles > 5ha
                prospects.rpg.push({
                    surface: surface,
                    culture: props.lib_cultu || 'Culture inconnue',
                    id: props.id_parcel || 'ID inconnu'
                });
            }
        });
    }
    
    // Analyser bâtiments
    if (searchResults.batiments_data && searchResults.batiments_data.features) {
        searchResults.batiments_data.features.forEach(feature => {
            const props = feature.properties;
            if (['agricole', 'industriel'].includes(props.usage) && props.surface_plancher > 500) {
                prospects.batiments.push({
                    usage: props.usage,
                    surface: props.surface_plancher,
                    nature: props.nature || 'Bâtiment'
                });
            }
        });
    }
    
    // Analyser parkings
    if (searchResults.parkings_data && searchResults.parkings_data.features) {
        searchResults.parkings_data.features.forEach(feature => {
            const props = feature.properties;
            if (props.surface > 3000) {  // Parkings > 3000m²
                prospects.parkings.push({
                    nom: props.nom || 'Parking',
                    surface: props.surface,
                    places: props.nb_places || 0
                });
            }
        });
    }
    
    // Analyser friches
    if (searchResults.friches_data && searchResults.friches_data.features) {
        searchResults.friches_data.features.forEach(feature => {
            const props = feature.properties;
            if (props.surface > 5000) {  // Friches > 5000m²
                prospects.friches.push({
                    nom: props.nom || 'Friche',
                    surface: props.surface,
                    statut: props.statut || 'Statut inconnu'
                });
            }
        });
    }
    
    // Calculer le total
    prospects.total = prospects.sirene.length + prospects.rpg.length + 
                     prospects.batiments.length + prospects.parkings.length + 
                     prospects.friches.length;
    
    return prospects;
}

// Afficher les prospects détectés dans l'interface
function displayCRMProspects(prospects) {
    const countElement = document.getElementById('crmProspectsCount');
    const listElement = document.getElementById('crmProspectsList');
    const analysisElement = document.getElementById('crmAnalysis');
    const analysisContent = document.getElementById('crmAnalysisContent');
    const createButton = document.getElementById('btnCreateProspects');
    
    countElement.textContent = prospects.total;
    
    if (prospects.total > 0) {
        let html = '';
        
        // Afficher les entreprises SIRENE
        if (prospects.sirene.length > 0) {
            html += `<div class="mb-2">
                <strong>🏢 Entreprises SIRENE (${prospects.sirene.length})</strong>
                <ul class="list-unstyled ms-3">`;
            prospects.sirene.slice(0, 3).forEach(entreprise => {
                html += `<li><small>• ${entreprise.name} - ${entreprise.activity}</small></li>`;
            });
            if (prospects.sirene.length > 3) {
                html += `<li><small>... et ${prospects.sirene.length - 3} autres</small></li>`;
            }
            html += '</ul></div>';
        }
        
        // Afficher les parcelles RPG
        if (prospects.rpg.length > 0) {
            html += `<div class="mb-2">
                <strong>🌾 Parcelles agricoles (${prospects.rpg.length})</strong>
                <ul class="list-unstyled ms-3">`;
            prospects.rpg.slice(0, 2).forEach(parcelle => {
                html += `<li><small>• ${parcelle.surface}ha - ${parcelle.culture}</small></li>`;
            });
            if (prospects.rpg.length > 2) {
                html += `<li><small>... et ${prospects.rpg.length - 2} autres</small></li>`;
            }
            html += '</ul></div>';
        }
        
        // Afficher les autres types
        if (prospects.batiments.length > 0) {
            html += `<div class="mb-2"><strong>🏭 Bâtiments (${prospects.batiments.length})</strong></div>`;
        }
        if (prospects.parkings.length > 0) {
            html += `<div class="mb-2"><strong>🅿️ Parkings (${prospects.parkings.length})</strong></div>`;
        }
        if (prospects.friches.length > 0) {
            html += `<div class="mb-2"><strong>🏚️ Friches (${prospects.friches.length})</strong></div>`;
        }
        
        listElement.innerHTML = html;
        
        // Afficher l'analyse
        let analysisHtml = `
            <ul class="mb-0">
                <li><strong>Priorité haute :</strong> ${prospects.sirene.length} entreprises actives</li>
                <li><strong>Priorité moyenne :</strong> ${prospects.rpg.length + prospects.batiments.length + prospects.friches.length} propriétaires fonciers</li>
                <li><strong>Priorité faible :</strong> ${prospects.parkings.length} gestionnaires publics</li>
            </ul>
        `;
        analysisContent.innerHTML = analysisHtml;
        analysisElement.style.display = 'block';
        
        createButton.disabled = false;
        document.getElementById('crmWidget').style.display = 'block';
    } else {
        listElement.innerHTML = '<p class="text-muted">Aucun prospect commercial détecté dans cette recherche.</p>';
        createButton.disabled = true;
    }
}

// Créer les prospects dans le CRM
function createCRMProspects() {
    if (!currentSearchResults) {
        alert('Aucune donnée de recherche disponible');
        return;
    }
    
    const statusDiv = document.getElementById('crmStatus');
    statusDiv.innerHTML = `
        <div class="alert alert-info">
            <div class="d-flex align-items-center">
                <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                <span>⏳ Création des prospects dans le CRM en cours...</span>
            </div>
        </div>
    `;
    statusDiv.style.display = 'block';
    
    // Préparer les données pour l'API CRM
    const payload = {
        search_results: currentSearchResults,
        search_metadata: {
            commune: currentSearchResults.commune || 'Commune inconnue',
            timestamp: new Date().toISOString(),
            user_initiated: true,
            search_type: 'commune_search'
        }
    };
    
    fetch('/api/crm/integrate_commune_search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            const summary = result.summary;
            statusDiv.innerHTML = `
                <div class="alert alert-success">
                    <h6 class="alert-heading">✅ Prospects créés avec succès !</h6>
                    <ul class="mb-2">
                        <li><strong>${summary.prospects_created || 0}</strong> nouveaux prospects créés</li>
                        <li><strong>${summary.prospects_skipped || 0}</strong> prospects existants ignorés</li>
                        <li><strong>${summary.prospects_updated || 0}</strong> prospects mis à jour</li>
                    </ul>
                    <a href="/crm/dashboard" target="_blank" class="btn btn-sm btn-success">
                        <i class="fas fa-external-link-alt"></i> Voir dans le CRM
                    </a>
                </div>
            `;
            
            // Désactiver le bouton pour éviter les doublons
            document.getElementById('btnCreateProspects').disabled = true;
            document.getElementById('btnCreateProspects').innerHTML = 
                '<i class="fas fa-check"></i> Prospects créés';
        } else {
            statusDiv.innerHTML = `
                <div class="alert alert-warning">
                    <h6 class="alert-heading">⚠️ Erreur lors de la création</h6>
                    <p class="mb-2">${result.error}</p>
                    <small class="text-muted">
                        Vérifiez que vous êtes connecté au CRM : 
                        <a href="/crm/login" target="_blank">Se connecter</a>
                    </small>
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

// Fonction à appeler après chaque recherche par commune réussie
function onCommuneSearchComplete(searchResults) {
    console.log('🔍 [CRM] Analyse des résultats de recherche commune:', searchResults.commune);
    
    currentSearchResults = searchResults;
    
    // Vérifier si le CRM est disponible
    if (searchResults.crm_available) {
        const prospects = analyzeCRMProspects(searchResults);
        displayCRMProspects(prospects);
        checkCRMAvailability();
    } else {
        console.log('ℹ️ [CRM] Module CRM non disponible');
        document.getElementById('crmWidget').style.display = 'none';
    }
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 [CRM] Widget CRM initialisé');
    
    // Si des résultats de recherche sont déjà présents au chargement
    // (cas où la page est rechargée), vous pouvez les analyser ici
});
</script>

<!-- ===== CSS OPTIONNEL POUR AMÉLIORER L'APPARENCE ===== -->
<style>
#crmWidget .card {
    border-left: 4px solid #0d6efd;
}

#crmWidget .btn {
    border-radius: 8px;
}

#crmWidget .badge {
    font-size: 0.9em;
}

#crmProspectsList ul li {
    padding: 2px 0;
}

.spinner-border-sm {
    width: 1rem;
    height: 1rem;
}
</style>

```

### 3️⃣ Modification de votre JavaScript de recherche

Dans votre fonction qui traite les résultats de recherche par commune, ajoutez :

```javascript
// Après avoir affiché vos résultats normaux (carte, tableaux, etc.)
// Ajoutez cette ligne :
onCommuneSearchComplete(searchResults);
```

### 4️⃣ Test de l'intégration

1. Démarrez votre application AgriWeb normale
2. Connectez-vous au CRM via `/crm/login`
3. Effectuez une recherche par commune
4. Le widget CRM doit apparaître avec le nombre de prospects détectés
5. Cliquez sur "Créer prospects CRM"
6. Vérifiez les résultats dans `/crm/dashboard`

## 📊 Types de prospects automatiquement détectés

### 🏢 Entreprises SIRENE (Priorité HAUTE)
- **Source** : Données SIRENE de votre recherche
- **Critères** : Toutes les entreprises trouvées
- **Exemple** : "FERME SOLAIRE ATLANTIQUE - Culture de céréales"

### 🌾 Propriétaires fonciers (Priorité MOYENNE)
- **Source** : Données RPG de votre recherche  
- **Critères** : Parcelles > 5 hectares
- **Exemple** : "Propriétaire parcelle 15.5ha - Blé tendre d'hiver"

### 🏭 Propriétaires de toitures (Priorité MOYENNE)
- **Source** : Données bâtiments de votre recherche
- **Critères** : Bâtiments agricoles/industriels > 500m²
- **Exemple** : "Propriétaire hangar agricole 1200m²"

### 🅿️ Gestionnaires parkings (Priorité FAIBLE)
- **Source** : Données parkings de votre recherche
- **Critères** : Parkings > 3000m²
- **Exemple** : "Gestionnaire parking 450 places"

### 🏚️ Propriétaires friches (Priorité MOYENNE)
- **Source** : Données friches de votre recherche
- **Critères** : Friches > 5000m²
- **Exemple** : "Propriétaire friche industrielle 2.5ha"

## 🔄 Workflow complet

```
1. Utilisateur effectue recherche par commune
     ↓
2. AgriWeb collecte données (SIRENE, RPG, bâtiments, etc.)
     ↓
3. Widget CRM analyse automatiquement les données
     ↓
4. Affichage du nombre de prospects détectés
     ↓
5. Utilisateur clique "Créer prospects CRM"
     ↓
6. Création automatique dans la base CRM
     ↓
7. Redirection vers dashboard commercial
```

## 💡 Avantages de cette approche

✅ **Aucune modification majeure** de votre code existant
✅ **Widget optionnel** qui n'apparaît que si connecté au CRM
✅ **Intégration progressive** possible
✅ **Fonctionne en parallèle** de votre système actuel
✅ **Qualification automatique** des prospects
✅ **Traçabilité** de la source de chaque prospect

## 🛠️ URLs importantes

- `/crm/login` - Connexion au CRM
- `/crm/dashboard` - Dashboard des prospects  
- `/api/crm/integrate_commune_search` - API d'intégration
- `/crm/prospects` - Gestion des prospects

## 👥 Comptes de test CRM

- **Admin** : admin@agriweb.com / admin123
- **Directeur** : directeur@agriweb.com / director123  
- **Commercial** : commercial@agriweb.com / commercial123

## 🎬 Test immédiat

```bash
# 1. Démarrer le CRM
python agriweb_crm_standalone.py

# 2. Aller sur http://localhost:5000
# 3. Se connecter avec admin@agriweb.com / admin123
# 4. Tester l'interface CRM

# 5. Intégrer dans votre AgriWeb selon ce guide
```

## 🔧 Personnalisation

Vous pouvez facilement :
- Modifier les critères de détection des prospects
- Ajouter d'autres sources de données
- Personnaliser l'interface du widget
- Ajouter des champs spécifiques à votre métier

## 📞 Support

En cas de problème, vérifiez :
1. Que les modules CRM sont bien importés
2. Que l'utilisateur est connecté au CRM
3. Que les données de recherche contiennent les champs attendus
4. Les logs dans la console du navigateur et de Python

---

**🎯 RÉSULTAT FINAL :** Chaque recherche par commune devient automatiquement une source de prospects commerciaux qualifiés !
