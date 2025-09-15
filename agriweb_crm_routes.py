"""
Routes CRM pour intégration dans AgriWeb
À ajouter dans votre application principale agriweb_hebergement_gratuit.py
"""

from flask import request, jsonify, session, render_template_string
from functools import wraps
import json

# Import du bridge CRM
try:
    from agriweb_crm_bridge_intelligent import (
        integrate_agriweb_search_to_crm_intelligent, 
        get_sirene_analysis_for_widget,
        extract_prospects_from_commune_search_intelligent
    )
    CRM_ENABLED = True
except ImportError:
    CRM_ENABLED = False

def add_crm_routes(app):
    """Ajoute les routes CRM à l'application Flask"""
    
    @app.route('/api/crm/integrate_search', methods=['POST'])
    def api_crm_integrate_search():
        """API pour intégrer une recherche AgriWeb au CRM"""
        if not CRM_ENABLED:
            return jsonify({'success': False, 'error': 'CRM non disponible'}), 503
        
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Non authentifié'}), 401
        
        try:
            data = request.get_json()
            search_response = data.get('search_response')
            search_params = data.get('search_params', {})
            
            if not search_response:
                return jsonify({'success': False, 'error': 'Données de recherche manquantes'}), 400
            
            # Intégrer au CRM
            result = integrate_agriweb_search_to_crm_intelligent(search_response)
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'success': False, 'error': f'Erreur serveur: {str(e)}'}), 500
    
    @app.route('/api/crm/dashboard')
    def api_crm_dashboard():
        """API pour récupérer les données du dashboard CRM"""
        if not CRM_ENABLED:
            return jsonify({'error': 'CRM non disponible'}), 503
        
        if 'user_id' not in session:
            return jsonify({'error': 'Non authentifié'}), 401
        
        dashboard_data = get_crm_dashboard_data(session['user_id'])
        
        if dashboard_data:
            return jsonify(dashboard_data)
        else:
            return jsonify({'error': 'Impossible de récupérer les données CRM'}), 500
    
    @app.route('/crm/login', methods=['GET', 'POST'])
    def crm_login():
        """Page de connexion CRM intégrée"""
        if not CRM_ENABLED:
            return "CRM non disponible", 503
        
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            # Import du manager CRM
            from agriweb_crm_standalone import SimpleCRMManager
            crm_manager = SimpleCRMManager()
            
            user = crm_manager.authenticate_user(username, password)
            
            if user:
                # Ajouter les infos CRM à la session
                session['crm_user_id'] = user['id']
                session['crm_username'] = user['username']
                session['crm_role'] = user['role']
                session['crm_full_name'] = f"{user['first_name']} {user['last_name']}"
                
                # Compatibilité avec le système de session principal
                session['user_id'] = user['id']
                session['username'] = user['username']
                
                return jsonify({'success': True, 'redirect': '/'})
            else:
                return jsonify({'success': False, 'error': 'Identifiants incorrects'})
        
        return render_template_string('''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexion CRM - AgriWeb</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container">
        <div class="row justify-content-center mt-5">
            <div class="col-md-6 col-lg-4">
                <div class="card shadow">
                    <div class="card-body">
                        <div class="text-center mb-4">
                            <h2 class="h4">🌾 AgriWeb CRM</h2>
                            <p class="text-muted">Connexion au système commercial</p>
                        </div>
                        
                        <form id="loginForm">
                            <div class="mb-3">
                                <label for="username" class="form-label">Nom d'utilisateur</label>
                                <input type="text" class="form-control" id="username" name="username" required>
                            </div>
                            
                            <div class="mb-3">
                                <label for="password" class="form-label">Mot de passe</label>
                                <input type="password" class="form-control" id="password" name="password" required>
                            </div>
                            
                            <div class="d-grid">
                                <button type="submit" class="btn btn-success">Se connecter</button>
                            </div>
                        </form>
                        
                        <div class="mt-4 p-3 bg-light rounded">
                            <small class="text-muted">
                                <strong>Comptes de test :</strong><br>
                                • admin@agriweb.com / admin123<br>
                                • directeur@agriweb.com / director123<br>
                                • commercial@agriweb.com / commercial123
                            </small>
                        </div>
                        
                        <div class="text-center mt-3">
                            <a href="/" class="btn btn-link">← Retour à AgriWeb</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('loginForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            fetch('/crm/login', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = data.redirect;
                } else {
                    alert('Erreur: ' + data.error);
                }
            })
            .catch(error => {
                alert('Erreur de connexion: ' + error.message);
            });
        });
    </script>
</body>
</html>
        ''')
    
    @app.route('/crm/dashboard')
    def crm_dashboard():
        """Dashboard CRM intégré dans AgriWeb"""
        if not CRM_ENABLED:
            return "CRM non disponible", 503
        
        if 'crm_user_id' not in session:
            return redirect('/crm/login')
        
        # Import du manager CRM
        from agriweb_crm_standalone import SimpleCRMManager
        crm_manager = SimpleCRMManager()
        
        # Récupérer les prospects
        prospects = crm_manager.get_prospects(session['crm_user_id'])
        
        # Statistiques
        total_prospects = len(prospects)
        new_prospects = len([p for p in prospects if p['status'] == 'nouveau'])
        auto_prospects = len([p for p in prospects if p['source'] == 'recherche_automatique'])
        
        return render_template_string('''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard CRM - AgriWeb</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-success">
        <div class="container">
            <a class="navbar-brand" href="/">🌾 AgriWeb</a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text me-3">{{ session.crm_full_name }} ({{ session.crm_role }})</span>
                <a class="nav-link" href="/">Recherche</a>
                <a class="nav-link" href="/crm/logout">Déconnexion</a>
            </div>
        </div>
    </nav>

    <div class="container-fluid py-4">
        <div class="row mb-4">
            <div class="col">
                <h2>📊 Dashboard CRM</h2>
                <p class="text-muted">Prospects générés depuis vos recherches AgriWeb</p>
            </div>
        </div>

        <!-- Statistiques -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card bg-primary text-white">
                    <div class="card-body text-center">
                        <h3>{{ total_prospects }}</h3>
                        <p class="mb-0">Total Prospects</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning text-white">
                    <div class="card-body text-center">
                        <h3>{{ new_prospects }}</h3>
                        <p class="mb-0">Nouveaux</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body text-center">
                        <h3>{{ auto_prospects }}</h3>
                        <p class="mb-0">Auto-générés</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body text-center">
                        <h3>{{ prospects|selectattr("status", "equalto", "qualifié")|list|length }}</h3>
                        <p class="mb-0">Qualifiés</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Prospects récents -->
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">📋 Prospects Récents</h5>
            </div>
            <div class="card-body">
                {% if prospects %}
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Entreprise</th>
                                <th>Ville</th>
                                <th>Source</th>
                                <th>Statut</th>
                                <th>Créé le</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for prospect in prospects[:10] %}
                            <tr>
                                <td><strong>{{ prospect.company_name }}</strong></td>
                                <td>{{ prospect.city or "-" }}</td>
                                <td>
                                    <span class="badge bg-{% if prospect.source == 'recherche_automatique' %}success{% else %}secondary{% endif %}">
                                        {{ prospect.source }}
                                    </span>
                                </td>
                                <td>
                                    <span class="badge bg-{% if prospect.status == 'nouveau' %}warning{% elif prospect.status == 'qualifié' %}info{% else %}secondary{% endif %}">
                                        {{ prospect.status }}
                                    </span>
                                </td>
                                <td>{{ prospect.created_at[:10] if prospect.created_at else "-" }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="text-center p-4">
                    <p class="text-muted">Aucun prospect trouvé. Effectuez une recherche AgriWeb pour commencer !</p>
                    <a href="/" class="btn btn-success">🔍 Nouvelle Recherche</a>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
        ''', prospects=prospects, total_prospects=total_prospects, new_prospects=new_prospects, auto_prospects=auto_prospects)

    @app.route('/crm/logout')
    def crm_logout():
        """Déconnexion CRM"""
        # Nettoyer les données CRM de la session
        session.pop('crm_user_id', None)
        session.pop('crm_username', None)
        session.pop('crm_role', None)
        session.pop('crm_full_name', None)
        session.pop('user_id', None)
        session.pop('username', None)
        
        return redirect('/')

    print(f"✅ Routes CRM ajoutées {'(ACTIVES)' if CRM_ENABLED else '(INACTIVES)'}")

# Fonction pour enrichir l'interface principale avec le CRM
def get_crm_widget_html(user_session):
    """Génère le HTML du widget CRM pour l'interface principale"""
    if not CRM_ENABLED or 'crm_user_id' not in user_session:
        return '''
        <div class="crm-widget">
            <div class="card bg-light">
                <div class="card-body text-center">
                    <h6>🎯 CRM Commercial</h6>
                    <p class="small text-muted">Connectez-vous pour générer des prospects</p>
                    <a href="/crm/login" class="btn btn-sm btn-success">Se connecter</a>
                </div>
            </div>
        </div>
        '''
    
    # Récupérer les données CRM
    dashboard_data = get_crm_dashboard_data(user_session['crm_user_id'])
    
    if not dashboard_data:
        return '''
        <div class="crm-widget">
            <div class="card bg-warning">
                <div class="card-body text-center">
                    <h6>⚠️ CRM</h6>
                    <p class="small">Erreur de connexion</p>
                </div>
            </div>
        </div>
        '''
    
    return f'''
    <div class="crm-widget">
        <div class="card bg-success text-white">
            <div class="card-body">
                <h6>🎯 CRM - {user_session.get('crm_full_name', 'Utilisateur')}</h6>
                <div class="row text-center">
                    <div class="col-4">
                        <div class="h5">{dashboard_data['total_prospects']}</div>
                        <small>Total</small>
                    </div>
                    <div class="col-4">
                        <div class="h5">{dashboard_data['new_prospects']}</div>
                        <small>Nouveaux</small>
                    </div>
                    <div class="col-4">
                        <div class="h5">{dashboard_data['auto_prospects']}</div>
                        <small>Auto</small>
                    </div>
                </div>
                <div class="d-grid mt-2">
                    <a href="/crm/dashboard" class="btn btn-light btn-sm">Dashboard</a>
                </div>
            </div>
        </div>
    </div>
    '''

# JavaScript pour l'intégration automatique
CRM_INTEGRATION_JS = '''
<script>
// Variables globales CRM
let crmIntegrationEnabled = false;
let lastSearchResponse = null;
let lastSearchParams = null;

// Vérifier si l'utilisateur est connecté au CRM
fetch('/api/crm/dashboard')
    .then(response => {
        if (response.ok) {
            crmIntegrationEnabled = true;
            console.log('✅ CRM Integration: ENABLED');
        } else {
            console.log('ℹ️ CRM Integration: DISABLED (pas connecté)');
        }
    })
    .catch(() => {
        console.log('ℹ️ CRM Integration: UNAVAILABLE');
    });

// Fonction pour intégrer automatiquement une recherche au CRM
function integrateToCRM(searchResponse, searchParams) {
    if (!crmIntegrationEnabled) {
        return;
    }
    
    // Stocker pour utilisation manuelle
    lastSearchResponse = searchResponse;
    lastSearchParams = searchParams;
    
    // Afficher le bouton d'intégration
    showCRMIntegrationButton();
    
    // Intégration automatique si activée
    if (document.getElementById('autoIntegrateCRM')?.checked) {
        performCRMIntegration();
    }
}

// Afficher le bouton d'intégration CRM
function showCRMIntegrationButton() {
    let button = document.getElementById('crmIntegrateBtn');
    if (!button) {
        // Créer le bouton s'il n'existe pas
        button = document.createElement('button');
        button.id = 'crmIntegrateBtn';
        button.className = 'btn btn-success btn-sm me-2';
        button.innerHTML = '🎯 Créer Prospects CRM';
        button.onclick = performCRMIntegration;
        
        // Ajouter à côté du bouton de recherche
        const searchButton = document.querySelector('button[type="submit"]');
        if (searchButton && searchButton.parentNode) {
            searchButton.parentNode.appendChild(button);
        }
    }
    
    button.disabled = false;
    button.style.display = 'inline-block';
}

// Effectuer l'intégration CRM
function performCRMIntegration() {
    if (!lastSearchResponse || !lastSearchParams) {
        alert('Aucune recherche à intégrer');
        return;
    }
    
    const button = document.getElementById('crmIntegrateBtn');
    if (button) {
        button.disabled = true;
        button.innerHTML = '⏳ Intégration...';
    }
    
    fetch('/api/crm/integrate_search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            search_response: lastSearchResponse,
            search_params: lastSearchParams
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`✅ Intégration réussie: ${data.summary.prospects_created} prospects créés`);
            
            // Recharger le widget CRM
            location.reload();
        } else {
            alert(`❌ Erreur: ${data.error}`);
        }
    })
    .catch(error => {
        alert(`❌ Erreur réseau: ${error.message}`);
    })
    .finally(() => {
        if (button) {
            button.disabled = false;
            button.innerHTML = '🎯 Créer Prospects CRM';
        }
    });
}

// Ajouter une case à cocher pour l'intégration automatique
document.addEventListener('DOMContentLoaded', function() {
    if (crmIntegrationEnabled) {
        const searchForm = document.querySelector('form');
        if (searchForm) {
            const autoCheckbox = document.createElement('div');
            autoCheckbox.className = 'form-check mt-2';
            autoCheckbox.innerHTML = `
                <input class="form-check-input" type="checkbox" id="autoIntegrateCRM" checked>
                <label class="form-check-label" for="autoIntegrateCRM">
                    Créer automatiquement des prospects CRM
                </label>
            `;
            searchForm.appendChild(autoCheckbox);
        }
    }
});
</script>
'''