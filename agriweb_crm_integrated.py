"""
Application AgriWeb avec système CRM intégré
Version avec gestionnaire hiérarchique et gestion des prospects
"""

import os
import sys
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import datetime

# Importer les nouveaux modules CRM
from models import db, init_db, User, Prospect, SavedSearch
from crm_manager import CRMUserManager

# Import du code existant (réutiliser les fonctions de recherche existantes)
import requests
import json

# Configuration de l'application
app = Flask(__name__)
app.secret_key = 'agriweb_crm_secret_key_2024'

# Configuration de la base de données
app.config.update({
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///agriweb_crm.db',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False
})

# Initialisation des composants
crm_manager = CRMUserManager(app)
init_db(app)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                           ROUTES D'AUTHENTIFICATION                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion avec gestion des rôles"""
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        user = crm_manager.authenticate_user(email, password)
        if user:
            return jsonify({
                'success': True,
                'user': {
                    'name': user.name,
                    'email': user.email,
                    'role': user.role,
                    'searches_remaining': user.searches_limit - user.searches_used
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Identifiants invalides'}), 401
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    """Déconnexion"""
    crm_manager.logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['POST'])
def register():
    """Inscription - seulement pour admin et directeurs"""
    if not crm_manager.require_login():
        return jsonify({'success': False, 'error': 'Non connecté'}), 401
    
    current_user = crm_manager.get_current_user()
    if not (current_user.is_admin or current_user.is_director):
        return jsonify({'success': False, 'error': 'Permission insuffisante'}), 403
    
    data = request.get_json()
    try:
        user = crm_manager.create_user(
            email=data['email'],
            password=data['password'],
            name=data['name'],
            role=data.get('role', 'commercial'),
            manager_email=data.get('manager_email')
        )
        return jsonify({
            'success': True,
            'user': {
                'name': user.name,
                'email': user.email,
                'role': user.role
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                              ROUTES PRINCIPALES                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@app.route('/')
def index():
    """Page principale avec vérification d'authentification"""
    if not crm_manager.require_login():
        return redirect(url_for('login'))
    
    user = crm_manager.get_current_user()
    user_stats = crm_manager.get_user_stats(user)
    
    # Template existant enrichi avec données CRM
    return render_template_string(MAIN_TEMPLATE, 
                                user=user, 
                                user_stats=user_stats)

@app.route('/api/user/stats')
def get_user_stats():
    """API pour récupérer les statistiques utilisateur"""
    if not crm_manager.require_login():
        return jsonify({'error': 'Non connecté'}), 401
    
    user = crm_manager.get_current_user()
    stats = crm_manager.get_user_stats(user)
    
    # Ajouter stats équipe si directeur/admin
    if user.is_director or user.is_admin:
        stats['team_stats'] = crm_manager.get_team_stats(user)
    
    return jsonify(stats)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                            ROUTES CRM PROSPECTS                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@app.route('/api/prospects')
def get_prospects():
    """Liste des prospects pour l'utilisateur"""
    if not crm_manager.require_login():
        return jsonify({'error': 'Non connecté'}), 401
    
    user = crm_manager.get_current_user()
    status = request.args.get('status')
    prospects = crm_manager.get_user_prospects(user, status)
    
    return jsonify([{
        'id': p.id,
        'company_name': p.company_name,
        'contact_email': p.contact_email,
        'status': p.status,
        'priority': p.priority,
        'created_at': p.created_at.isoformat(),
        'assigned_to': p.assigned_to.name if p.assigned_to else None,
        'tags': p.get_tags()
    } for p in prospects])

@app.route('/api/prospects', methods=['POST'])
def create_prospect():
    """Créer un nouveau prospect"""
    if not crm_manager.require_login():
        return jsonify({'error': 'Non connecté'}), 401
    
    data = request.get_json()
    try:
        prospect = crm_manager.create_prospect(
            company_name=data['company_name'],
            contact_email=data.get('contact_email'),
            contact_name=data.get('contact_name'),
            contact_phone=data.get('contact_phone'),
            address=data.get('address'),
            city=data.get('city'),
            notes=data.get('notes')
        )
        
        return jsonify({
            'success': True,
            'prospect_id': prospect.id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                        ROUTES RECHERCHES SAUVEGARDÉES                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@app.route('/api/searches/save', methods=['POST'])
def save_search():
    """Sauvegarder une recherche"""
    if not crm_manager.require_login():
        return jsonify({'error': 'Non connecté'}), 401
    
    data = request.get_json()
    try:
        search = crm_manager.save_search(
            name=data['name'],
            search_params=data['search_params'],
            description=data.get('description'),
            department=data.get('department'),
            city=data.get('city'),
            category=data.get('category'),
            is_public=data.get('is_public', False)
        )
        
        return jsonify({
            'success': True,
            'search_id': search.id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/searches')
def get_saved_searches():
    """Liste des recherches sauvegardées"""
    if not crm_manager.require_login():
        return jsonify({'error': 'Non connecté'}), 401
    
    user = crm_manager.get_current_user()
    searches = crm_manager.get_user_searches(user)
    
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'description': s.description,
        'department': s.department,
        'city': s.city,
        'category': s.category,
        'is_public': s.is_public,
        'usage_count': s.usage_count,
        'created_at': s.created_at.isoformat(),
        'owner': s.user.name,
        'tags': s.get_tags()
    } for s in searches])

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                            ROUTES D'ADMINISTRATION                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@app.route('/admin')
def admin_dashboard():
    """Tableau de bord administrateur"""
    if not crm_manager.require_role(['admin', 'directeur_commercial']):
        return jsonify({'error': 'Permission insuffisante'}), 403
    
    user = crm_manager.get_current_user()
    team_members = crm_manager.get_team_members(user)
    team_stats = crm_manager.get_team_stats(user)
    
    return render_template_string(ADMIN_TEMPLATE, 
                                user=user,
                                team_members=team_members,
                                team_stats=team_stats)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                               TEMPLATES HTML                              ║
# ╚══════════════════════════════════════════════════════════════════════════╝

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgriWeb CRM - Connexion</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container-fluid vh-100 d-flex align-items-center justify-content-center">
        <div class="row w-100">
            <div class="col-md-6 col-lg-4 mx-auto">
                <div class="card shadow">
                    <div class="card-body p-5">
                        <div class="text-center mb-4">
                            <h2 class="text-success"><i class="fas fa-seedling"></i> AgriWeb CRM</h2>
                            <p class="text-muted">Plateforme commerciale agricole</p>
                        </div>
                        
                        <form id="loginForm">
                            <div class="mb-3">
                                <label class="form-label">Email</label>
                                <div class="input-group">
                                    <span class="input-group-text"><i class="fas fa-envelope"></i></span>
                                    <input type="email" class="form-control" id="email" required>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">Mot de passe</label>
                                <div class="input-group">
                                    <span class="input-group-text"><i class="fas fa-lock"></i></span>
                                    <input type="password" class="form-control" id="password" required>
                                </div>
                            </div>
                            
                            <button type="submit" class="btn btn-success w-100 mb-3">
                                <i class="fas fa-sign-in-alt"></i> Se connecter
                            </button>
                        </form>
                        
                        <div id="errorMessage" class="alert alert-danger d-none"></div>
                        
                        <div class="text-center small text-muted">
                            <p>Comptes de démonstration :</p>
                            <p><strong>Admin:</strong> admin@agriweb.com / admin123</p>
                            <p><strong>Directeur:</strong> directeur@agriweb.com / director123</p>
                            <p><strong>Commercial:</strong> commercial@agriweb.com / commercial123</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('errorMessage');
            
            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    window.location.href = '/';
                } else {
                    errorDiv.textContent = data.error;
                    errorDiv.classList.remove('d-none');
                }
            } catch (error) {
                errorDiv.textContent = 'Erreur de connexion';
                errorDiv.classList.remove('d-none');
            }
        });
    </script>
</body>
</html>
'''

MAIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgriWeb CRM - Tableau de bord</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-success">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">
                <i class="fas fa-seedling"></i> AgriWeb CRM
            </a>
            
            <div class="navbar-nav ms-auto">
                <div class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                        <i class="fas fa-user"></i> {{ user.name }}
                        <span class="badge bg-light text-dark ms-1">{{ user.role }}</span>
                    </a>
                    <ul class="dropdown-menu">
                        {% if user.is_admin or user.is_director %}
                        <li><a class="dropdown-item" href="/admin"><i class="fas fa-users"></i> Administration</a></li>
                        {% endif %}
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item" href="/logout"><i class="fas fa-sign-out-alt"></i> Déconnexion</a></li>
                    </ul>
                </div>
            </div>
        </div>
    </nav>

    <div class="container-fluid py-4">
        <!-- Statistiques utilisateur -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card text-white bg-primary">
                    <div class="card-body">
                        <h5 class="card-title"><i class="fas fa-building"></i> Mes Prospects</h5>
                        <h2>{{ user_stats.total_prospects }}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-white bg-success">
                    <div class="card-body">
                        <h5 class="card-title"><i class="fas fa-chart-line"></i> Taux Conversion</h5>
                        <h2>{{ user_stats.conversion_rate }}%</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-white bg-info">
                    <div class="card-body">
                        <h5 class="card-title"><i class="fas fa-search"></i> Recherches</h5>
                        <h2>{{ user_stats.searches_remaining }}</h2>
                        <small>restantes</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-white bg-warning">
                    <div class="card-body">
                        <h5 class="card-title"><i class="fas fa-calendar"></i> Ce Mois</h5>
                        <h2>{{ user_stats.prospects_this_month }}</h2>
                        <small>nouveaux prospects</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Interface principale -->
        <div class="row">
            <div class="col-md-8">
                <!-- Carte (réutiliser l'existant) -->
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-map"></i> Recherche Géographique</h5>
                    </div>
                    <div class="card-body">
                        <div id="map-container" style="height: 600px;">
                            <!-- Ici sera intégrée la carte existante -->
                            <iframe src="/legacy-map" width="100%" height="100%" frameborder="0"></iframe>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <!-- Prospects récents -->
                <div class="card mb-3">
                    <div class="card-header">
                        <h6><i class="fas fa-building"></i> Prospects Récents</h6>
                    </div>
                    <div class="card-body" id="recent-prospects">
                        <div class="text-center">
                            <div class="spinner-border" role="status"></div>
                        </div>
                    </div>
                </div>

                <!-- Recherches sauvegardées -->
                <div class="card">
                    <div class="card-header">
                        <h6><i class="fas fa-bookmark"></i> Recherches Sauvegardées</h6>
                    </div>
                    <div class="card-body" id="saved-searches">
                        <div class="text-center">
                            <div class="spinner-border" role="status"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Charger les prospects récents
        async function loadRecentProspects() {
            try {
                const response = await fetch('/api/prospects?limit=5');
                const prospects = await response.json();
                
                const container = document.getElementById('recent-prospects');
                if (prospects.length === 0) {
                    container.innerHTML = '<p class="text-muted text-center">Aucun prospect</p>';
                    return;
                }
                
                container.innerHTML = prospects.map(p => `
                    <div class="border-bottom pb-2 mb-2">
                        <h6 class="mb-1">${p.company_name}</h6>
                        <small class="text-muted">${p.status} • ${new Date(p.created_at).toLocaleDateString()}</small>
                    </div>
                `).join('');
            } catch (error) {
                document.getElementById('recent-prospects').innerHTML = 
                    '<p class="text-danger">Erreur de chargement</p>';
            }
        }

        // Charger les recherches sauvegardées
        async function loadSavedSearches() {
            try {
                const response = await fetch('/api/searches?limit=5');
                const searches = await response.json();
                
                const container = document.getElementById('saved-searches');
                if (searches.length === 0) {
                    container.innerHTML = '<p class="text-muted text-center">Aucune recherche</p>';
                    return;
                }
                
                container.innerHTML = searches.map(s => `
                    <div class="border-bottom pb-2 mb-2">
                        <h6 class="mb-1">${s.name}</h6>
                        <small class="text-muted">${s.category || 'Général'} • ${s.usage_count} utilisations</small>
                    </div>
                `).join('');
            } catch (error) {
                document.getElementById('saved-searches').innerHTML = 
                    '<p class="text-danger">Erreur de chargement</p>';
            }
        }

        // Initialisation
        document.addEventListener('DOMContentLoaded', () => {
            loadRecentProspects();
            loadSavedSearches();
        });
    </script>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Administration - AgriWeb CRM</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-success">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">
                <i class="fas fa-seedling"></i> AgriWeb CRM - Administration
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/"><i class="fas fa-home"></i> Accueil</a>
                <a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt"></i> Déconnexion</a>
            </div>
        </div>
    </nav>

    <div class="container-fluid py-4">
        <h2><i class="fas fa-users"></i> Gestion de l'équipe</h2>
        
        <!-- Statistiques équipe -->
        {% if team_stats %}
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card text-white bg-primary">
                    <div class="card-body">
                        <h5>Équipe</h5>
                        <h2>{{ team_stats.team_size }}</h2>
                        <small>membres</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-white bg-success">
                    <div class="card-body">
                        <h5>Prospects Total</h5>
                        <h2>{{ team_stats.total_prospects }}</h2>
                    </div>
                </div>
            </div>
        </div>
        {% endif %}

        <!-- Liste des membres -->
        <div class="card">
            <div class="card-header">
                <h5>Membres de l'équipe</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Nom</th>
                                <th>Email</th>
                                <th>Rôle</th>
                                <th>Prospects</th>
                                <th>Conversion</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for member in team_members %}
                            <tr>
                                <td>{{ member.name }}</td>
                                <td>{{ member.email }}</td>
                                <td><span class="badge bg-info">{{ member.role }}</span></td>
                                <td>{{ member.assigned_prospects.count() }}</td>
                                <td>-</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("🚀 AgriWeb CRM démarré sur http://localhost:5000")
        print("👤 Comptes de test:")
        print("   Admin: admin@agriweb.com / admin123")
        print("   Directeur: directeur@agriweb.com / director123") 
        print("   Commercial: commercial@agriweb.com / commercial123")
    
    app.run(debug=True, host='0.0.0.0', port=5000)