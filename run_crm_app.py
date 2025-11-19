"""
Script de démarrage pour l'application AgriWeb CRM
Lance le serveur avec les nouvelles fonctionnalités CRM
"""

import os
import sys
from datetime import datetime

# Configuration d'environnement pour éviter les erreurs Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
    from models import db, init_db, User, Prospect, SavedSearch
    from crm_manager import CRMUserManager
    
    print("🔧 Initialisation de l'application AgriWeb CRM...")
    
    # Configuration de l'application
    app = Flask(__name__)
    app.secret_key = 'agriweb_crm_secret_key_2024'
    
    # Configuration de la base de données
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///agriweb_crm.db',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })
    
    # Initialisation des composants CRM
    with app.app_context():
        print("📦 Initialisation de la base de données...")
        init_db(app)
        
        crm_manager = CRMUserManager()
        crm_manager.init_app(app)
        
        print("✅ Système CRM initialisé avec succès")
        
        # Vérifier que les utilisateurs de test existent
        admin = User.query.filter_by(email='admin@agriweb.com').first()
        if admin:
            print(f"👤 Admin trouvé: {admin.name} ({admin.role})")
        
        director = User.query.filter_by(email='directeur@agriweb.com').first()
        if director:
            print(f"👤 Directeur trouvé: {director.name} ({director.role})")
        
        commercial = User.query.filter_by(email='commercial@agriweb.com').first()
        if commercial:
            print(f"👤 Commercial trouvé: {commercial.name} ({commercial.role})")
    
    # ═══════════════════════════════════════════════════════════════════════
    # ROUTES PRINCIPALES
    # ═══════════════════════════════════════════════════════════════════════
    
    @app.route('/')
    def index():
        """Page d'accueil avec redirection vers login si nécessaire"""
        if not crm_manager.require_login():
            return redirect(url_for('login'))
        
        user = crm_manager.get_current_user()
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AgriWeb CRM</title>
            <meta charset="utf-8">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-dark bg-success">
                <div class="container">
                    <span class="navbar-brand">🌾 AgriWeb CRM</span>
                    <span class="text-white">Connecté: {user.name} ({user.role})</span>
                    <a href="/logout" class="btn btn-outline-light">Déconnexion</a>
                </div>
            </nav>
            
            <div class="container mt-4">
                <h2>Tableau de bord CRM</h2>
                
                <div class="row">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body text-center">
                                <h5>🏢 Mes Prospects</h5>
                                <h2 id="prospects-count">-</h2>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body text-center">
                                <h5>🔍 Recherches</h5>
                                <h2>{user.searches_limit - user.searches_used}</h2>
                                <small>restantes</small>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body text-center">
                                <h5>📊 Mon Rôle</h5>
                                <h2>{user.role.title()}</h2>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Actions Rapides</h5>
                            </div>
                            <div class="card-body">
                                <button class="btn btn-primary mb-2" onclick="createProspect()">
                                    ➕ Créer un Prospect
                                </button><br>
                                <button class="btn btn-success mb-2" onclick="saveSearch()">
                                    💾 Sauvegarder une Recherche
                                </button><br>
                                {'<button class="btn btn-warning" onclick="location.href=\'/admin\'">👥 Administration</button>' if user.is_admin or user.is_director else ''}
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Prospects Récents</h5>
                            </div>
                            <div class="card-body" id="prospects-list">
                                <div class="text-muted">Chargement...</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                // Charger les statistiques
                fetch('/api/user/stats')
                    .then(r => r.json())
                    .then(data => {{
                        document.getElementById('prospects-count').textContent = data.total_prospects || 0;
                    }});
                
                // Charger les prospects
                fetch('/api/prospects')
                    .then(r => r.json())
                    .then(prospects => {{
                        const list = document.getElementById('prospects-list');
                        if (prospects.length === 0) {{
                            list.innerHTML = '<div class="text-muted">Aucun prospect</div>';
                        }} else {{
                            list.innerHTML = prospects.slice(0, 3).map(p => 
                                `<div class="border-bottom pb-2 mb-2">
                                    <strong>${{p.company_name}}</strong><br>
                                    <small class="text-muted">${{p.status}} • ${{new Date(p.created_at).toLocaleDateString()}}</small>
                                </div>`
                            ).join('');
                        }}
                    }});
                
                function createProspect() {{
                    const name = prompt('Nom de la société:');
                    if (name) {{
                        fetch('/api/prospects', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{company_name: name}})
                        }})
                        .then(r => r.json())
                        .then(data => {{
                            if (data.success) {{
                                alert('Prospect créé avec succès!');
                                location.reload();
                            }} else {{
                                alert('Erreur: ' + data.error);
                            }}
                        }});
                    }}
                }}
                
                function saveSearch() {{
                    const name = prompt('Nom de la recherche:');
                    if (name) {{
                        fetch('/api/searches/save', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{
                                name: name,
                                search_params: {{'demo': true}},
                                description: 'Recherche de démonstration'
                            }})
                        }})
                        .then(r => r.json())
                        .then(data => {{
                            if (data.success) {{
                                alert('Recherche sauvegardée!');
                            }} else {{
                                alert('Erreur: ' + data.error);
                            }}
                        }});
                    }}
                }}
            </script>
        </body>
        </html>
        """
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Page de connexion"""
        if request.method == 'POST':
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            
            user = crm_manager.authenticate_user(email, password)
            if user:
                return jsonify({'success': True, 'message': 'Connexion réussie'})
            else:
                return jsonify({'success': False, 'error': 'Identifiants invalides'}), 401
        
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Connexion - AgriWeb CRM</title>
            <meta charset="utf-8">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">
            <div class="container vh-100 d-flex align-items-center justify-content-center">
                <div class="card" style="width: 400px;">
                    <div class="card-body">
                        <h3 class="text-center mb-4">🌾 AgriWeb CRM</h3>
                        
                        <form id="loginForm">
                            <div class="mb-3">
                                <label class="form-label">Email</label>
                                <input type="email" class="form-control" id="email" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Mot de passe</label>
                                <input type="password" class="form-control" id="password" required>
                            </div>
                            <button type="submit" class="btn btn-success w-100">Se connecter</button>
                        </form>
                        
                        <div id="error" class="alert alert-danger mt-3 d-none"></div>
                        
                        <div class="mt-4 small text-muted">
                            <strong>Comptes de test:</strong><br>
                            Admin: admin@agriweb.com / admin123<br>
                            Directeur: directeur@agriweb.com / director123<br>
                            Commercial: commercial@agriweb.com / commercial123
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                document.getElementById('loginForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    const errorDiv = document.getElementById('error');
                    
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
        """
    
    @app.route('/logout')
    def logout():
        """Déconnexion"""
        crm_manager.logout_user()
        return redirect(url_for('login'))
    
    # ═══════════════════════════════════════════════════════════════════════
    # API ROUTES
    # ═══════════════════════════════════════════════════════════════════════
    
    @app.route('/api/user/stats')
    def api_user_stats():
        """API pour les statistiques utilisateur"""
        if not crm_manager.require_login():
            return jsonify({'error': 'Non connecté'}), 401
        
        user = crm_manager.get_current_user()
        stats = crm_manager.get_user_stats(user)
        return jsonify(stats)
    
    @app.route('/api/prospects')
    def api_prospects():
        """API pour lister les prospects"""
        if not crm_manager.require_login():
            return jsonify({'error': 'Non connecté'}), 401
        
        user = crm_manager.get_current_user()
        prospects = crm_manager.get_user_prospects(user)
        
        return jsonify([{
            'id': p.id,
            'company_name': p.company_name,
            'status': p.status,
            'created_at': p.created_at.isoformat()
        } for p in prospects])
    
    @app.route('/api/prospects', methods=['POST'])
    def api_create_prospect():
        """API pour créer un prospect"""
        if not crm_manager.require_login():
            return jsonify({'error': 'Non connecté'}), 401
        
        data = request.get_json()
        try:
            prospect = crm_manager.create_prospect(
                company_name=data['company_name'],
                contact_email=data.get('contact_email'),
                notes='Prospect créé via interface CRM'
            )
            return jsonify({'success': True, 'prospect_id': prospect.id})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    @app.route('/api/searches/save', methods=['POST'])
    def api_save_search():
        """API pour sauvegarder une recherche"""
        if not crm_manager.require_login():
            return jsonify({'error': 'Non connecté'}), 401
        
        data = request.get_json()
        try:
            search = crm_manager.save_search(
                name=data['name'],
                search_params=data['search_params'],
                description=data.get('description', '')
            )
            return jsonify({'success': True, 'search_id': search.id})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    @app.route('/admin')
    def admin():
        """Page d'administration"""
        if not crm_manager.require_role(['admin', 'directeur_commercial']):
            return jsonify({'error': 'Accès refusé'}), 403
        
        user = crm_manager.get_current_user()
        team_members = crm_manager.get_team_members(user)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Administration - AgriWeb CRM</title>
            <meta charset="utf-8">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-dark bg-success">
                <div class="container">
                    <span class="navbar-brand">👥 Administration CRM</span>
                    <div>
                        <a href="/" class="btn btn-outline-light me-2">Accueil</a>
                        <a href="/logout" class="btn btn-outline-light">Déconnexion</a>
                    </div>
                </div>
            </nav>
            
            <div class="container mt-4">
                <h2>Gestion de l'équipe</h2>
                
                <div class="card">
                    <div class="card-header">
                        <h5>Membres de l'équipe ({len(team_members)})</h5>
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
                                        <th>Statut</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {''.join([f'''
                                    <tr>
                                        <td>{member.name}</td>
                                        <td>{member.email}</td>
                                        <td><span class="badge bg-info">{member.role}</span></td>
                                        <td>{len(member.assigned_prospects.all())}</td>
                                        <td><span class="badge bg-success">Actif</span></td>
                                    </tr>
                                    ''' for member in team_members])}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    if __name__ == '__main__':
        print("\n" + "="*60)
        print("🚀 AGRIWEB CRM - SERVEUR DE DÉMONSTRATION")
        print("="*60)
        print("📍 URL: http://localhost:5000")
        print("👤 Comptes de test:")
        print("   📧 Admin: admin@agriweb.com / admin123")
        print("   📧 Directeur: directeur@agriweb.com / director123")
        print("   📧 Commercial: commercial@agriweb.com / commercial123")
        print("="*60)
        print("🌟 Fonctionnalités CRM disponibles:")
        print("   • Authentification par rôles")
        print("   • Gestion hiérarchique des prospects")
        print("   • Sauvegarde de recherches")
        print("   • Tableau de bord par rôle")
        print("   • Administration d'équipe")
        print("="*60)
        
        app.run(debug=True, host='0.0.0.0', port=5000)

except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("📦 Assurez-vous que Flask et SQLAlchemy sont installés:")
    print("   pip install flask flask-sqlalchemy werkzeug")
    sys.exit(1)

except Exception as e:
    print(f"❌ Erreur lors du démarrage: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)