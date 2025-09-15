"""
Application AgriWeb CRM - Version Autonome Complète
Système CRM avec hiérarchie commerciale et gestion des prospects
"""

import os
import sqlite3
import hashlib
import uuid
import json
from datetime import datetime
from flask import Flask, request, jsonify, session, redirect, url_for

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION ET INITIALISATION
# ═══════════════════════════════════════════════════════════════════════

app = Flask(__name__)
app.secret_key = 'agriweb_crm_secret_2024'

# Base de données SQLite simple
DB_PATH = 'agriweb_crm.db'

def init_database():
    """Initialise la base de données avec les tables nécessaires"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table des utilisateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'commercial',
            manager_id TEXT,
            license_type TEXT DEFAULT 'trial',
            searches_used INTEGER DEFAULT 0,
            searches_limit INTEGER DEFAULT 50,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            FOREIGN KEY (manager_id) REFERENCES users (id)
        )
    ''')
    
    # Table des prospects
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prospects (
            id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            contact_email TEXT,
            contact_phone TEXT,
            contact_name TEXT,
            address TEXT,
            city TEXT,
            postal_code TEXT,
            department TEXT,
            coordinates TEXT,
            status TEXT DEFAULT 'nouveau',
            priority TEXT DEFAULT 'normale',
            source TEXT DEFAULT 'manuel',
            source_search_id TEXT,
            assigned_to_id TEXT,
            created_by_id TEXT NOT NULL,
            notes TEXT,
            tags TEXT,
            estimated_value REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_contact TIMESTAMP,
            next_action_date TIMESTAMP,
            converted_at TIMESTAMP,
            FOREIGN KEY (assigned_to_id) REFERENCES users (id),
            FOREIGN KEY (created_by_id) REFERENCES users (id)
        )
    ''')
    
    # Table des recherches sauvegardées
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_searches (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            search_params TEXT NOT NULL,
            department TEXT,
            city TEXT,
            coordinates TEXT,
            radius INTEGER,
            tags TEXT,
            category TEXT,
            user_id TEXT NOT NULL,
            is_public BOOLEAN DEFAULT 0,
            auto_prospect BOOLEAN DEFAULT 0,
            usage_count INTEGER DEFAULT 0,
            last_used TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Créer les utilisateurs par défaut s'ils n'existent pas
    admin_id = str(uuid.uuid4())
    director_id = str(uuid.uuid4())
    commercial_id = str(uuid.uuid4())
    
    admin_password = hashlib.sha256("admin123".encode()).hexdigest()
    director_password = hashlib.sha256("director123".encode()).hexdigest()
    commercial_password = hashlib.sha256("commercial123".encode()).hexdigest()
    
    # Vérifier si admin existe déjà
    cursor.execute("SELECT id FROM users WHERE email = ?", ('admin@agriweb.com',))
    if not cursor.fetchone():
        # Créer admin
        cursor.execute('''
            INSERT INTO users (id, email, password_hash, name, role, license_type, searches_limit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (admin_id, 'admin@agriweb.com', admin_password, 'Administrateur Système', 'admin', 'enterprise', 999999))
        
        # Créer directeur
        cursor.execute('''
            INSERT INTO users (id, email, password_hash, name, role, manager_id, license_type, searches_limit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (director_id, 'directeur@agriweb.com', director_password, 'Directeur Commercial', 'directeur_commercial', admin_id, 'professional', 1000))
        
        # Créer commercial
        cursor.execute('''
            INSERT INTO users (id, email, password_hash, name, role, manager_id, license_type, searches_limit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (commercial_id, 'commercial@agriweb.com', commercial_password, 'Commercial Terrain', 'commercial', director_id, 'standard', 100))
    
    conn.commit()
    conn.close()
    print("✅ Base de données initialisée avec succès")

# ═══════════════════════════════════════════════════════════════════════
# GESTIONNAIRE CRM SIMPLIFIÉ
# ═══════════════════════════════════════════════════════════════════════

class SimpleCRMManager:
    """Gestionnaire CRM simplifié avec base de données SQLite"""
    
    def authenticate_user(self, email, password):
        """Authentifie un utilisateur"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("""
            SELECT * FROM users 
            WHERE email = ? AND password_hash = ? AND active = 1
        """, (email, password_hash))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            # Stocker en session
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            session['user_name'] = user['name']
            
            # Mettre à jour last_login
            self.update_last_login(user['id'])
            return dict(user)
        return None
    
    def update_last_login(self, user_id):
        """Met à jour la dernière connexion"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
    
    def get_current_user(self):
        """Retourne l'utilisateur actuellement connecté"""
        user_id = session.get('user_id')
        if not user_id:
            return None
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    def logout_user(self):
        """Déconnecte l'utilisateur"""
        session.clear()
    
    def require_login(self):
        """Vérifie que l'utilisateur est connecté"""
        return self.get_current_user() is not None
    
    def require_role(self, required_roles):
        """Vérifie que l'utilisateur a un des rôles requis"""
        user = self.get_current_user()
        if not user:
            return False
        if isinstance(required_roles, str):
            required_roles = [required_roles]
        return user['role'] in required_roles
    
    def create_prospect(self, company_name, **kwargs):
        """Crée un nouveau prospect"""
        current_user = self.get_current_user()
        if not current_user:
            raise PermissionError("Utilisateur non connecté")
        
        prospect_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO prospects (
                id, company_name, contact_email, contact_name, contact_phone,
                address, city, notes, created_by_id, assigned_to_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prospect_id, company_name,
            kwargs.get('contact_email'), kwargs.get('contact_name'), kwargs.get('contact_phone'),
            kwargs.get('address'), kwargs.get('city'), kwargs.get('notes'),
            current_user['id'], kwargs.get('assigned_to_id', current_user['id'])
        ))
        
        conn.commit()
        conn.close()
        
        return {'id': prospect_id, 'company_name': company_name}
    
    def get_user_prospects(self, user=None, status=None):
        """Retourne les prospects visibles pour l'utilisateur"""
        if not user:
            user = self.get_current_user()
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if user['role'] == 'admin':
            # Admin voit tous les prospects
            query = "SELECT * FROM prospects"
            params = []
        elif user['role'] == 'directeur_commercial':
            # Directeur voit ses prospects + ceux de son équipe
            query = """
                SELECT p.* FROM prospects p
                LEFT JOIN users u ON p.assigned_to_id = u.id
                WHERE p.assigned_to_id = ? OR u.manager_id = ?
            """
            params = [user['id'], user['id']]
        else:
            # Commercial voit ses prospects
            query = "SELECT * FROM prospects WHERE assigned_to_id = ?"
            params = [user['id']]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        prospects = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return prospects
    
    def save_search(self, name, search_params, **kwargs):
        """Sauvegarde une recherche"""
        current_user = self.get_current_user()
        if not current_user:
            raise PermissionError("Utilisateur non connecté")
        
        search_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO saved_searches (
                id, name, description, search_params, department, city,
                category, user_id, is_public
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            search_id, name, kwargs.get('description', ''),
            json.dumps(search_params), kwargs.get('department'),
            kwargs.get('city'), kwargs.get('category', 'general'),
            current_user['id'], kwargs.get('is_public', False)
        ))
        
        conn.commit()
        conn.close()
        
        return {'id': search_id, 'name': name}
    
    def get_user_searches(self, user=None):
        """Retourne les recherches de l'utilisateur"""
        if not user:
            user = self.get_current_user()
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM saved_searches 
            WHERE user_id = ? OR is_public = 1
            ORDER BY created_at DESC
        """, (user['id'],))
        
        searches = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return searches
    
    def get_user_stats(self, user=None):
        """Retourne les statistiques de l'utilisateur"""
        if not user:
            user = self.get_current_user()
        
        prospects = self.get_user_prospects(user)
        
        stats = {
            'total_prospects': len(prospects),
            'prospects_by_status': {},
            'prospects_this_month': 0,
            'conversion_rate': 0,
            'searches_used': user['searches_used'],
            'searches_remaining': user['searches_limit'] - user['searches_used']
        }
        
        # Prospects par statut
        for prospect in prospects:
            status = prospect['status']
            stats['prospects_by_status'][status] = stats['prospects_by_status'].get(status, 0) + 1
        
        # Taux de conversion
        total = len(prospects)
        converted = stats['prospects_by_status'].get('converti', 0)
        if total > 0:
            stats['conversion_rate'] = round((converted / total) * 100, 1)
        
        return stats
    
    def get_team_members(self, user=None):
        """Retourne les membres de l'équipe"""
        if not user:
            user = self.get_current_user()
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if user['role'] == 'admin':
            cursor.execute("SELECT * FROM users WHERE role != 'admin'")
        elif user['role'] == 'directeur_commercial':
            cursor.execute("SELECT * FROM users WHERE manager_id = ?", (user['id'],))
        else:
            return []
        
        members = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return members

# Initialiser le gestionnaire CRM
crm_manager = SimpleCRMManager()

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
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-success">
            <div class="container">
                <span class="navbar-brand"><i class="fas fa-seedling"></i> AgriWeb CRM</span>
                <span class="text-white">
                    <i class="fas fa-user"></i> {user['name']} 
                    <span class="badge bg-light text-dark">{user['role']}</span>
                </span>
                <a href="/logout" class="btn btn-outline-light">
                    <i class="fas fa-sign-out-alt"></i> Déconnexion
                </a>
            </div>
        </nav>
        
        <div class="container mt-4">
            <div class="row mb-4">
                <div class="col-md-12">
                    <h2><i class="fas fa-tachometer-alt"></i> Tableau de bord CRM</h2>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card text-white bg-primary">
                        <div class="card-body text-center">
                            <h5><i class="fas fa-building"></i> Mes Prospects</h5>
                            <h2 id="prospects-count">-</h2>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-3">
                    <div class="card text-white bg-info">
                        <div class="card-body text-center">
                            <h5><i class="fas fa-search"></i> Recherches</h5>
                            <h2>{user['searches_limit'] - user['searches_used']}</h2>
                            <small>restantes</small>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-3">
                    <div class="card text-white bg-success">
                        <div class="card-body text-center">
                            <h5><i class="fas fa-chart-line"></i> Taux Conversion</h5>
                            <h2 id="conversion-rate">-%</h2>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-3">
                    <div class="card text-white bg-warning">
                        <div class="card-body text-center">
                            <h5><i class="fas fa-user-tie"></i> Mon Rôle</h5>
                            <h2>{user['role'].replace('_', ' ').title()}</h2>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-bolt"></i> Actions Rapides</h5>
                        </div>
                        <div class="card-body">
                            <button class="btn btn-primary mb-2 w-100" onclick="createProspect()">
                                <i class="fas fa-plus"></i> Créer un Prospect
                            </button>
                            <button class="btn btn-success mb-2 w-100" onclick="saveSearch()">
                                <i class="fas fa-save"></i> Sauvegarder une Recherche
                            </button>
                            {'<a href="/admin" class="btn btn-warning w-100"><i class="fas fa-users"></i> Administration</a>' if user['role'] in ['admin', 'directeur_commercial'] else ''}
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-building"></i> Prospects Récents</h5>
                        </div>
                        <div class="card-body" id="prospects-list">
                            <div class="text-center">
                                <div class="spinner-border" role="status"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-bookmark"></i> Recherches Sauvegardées</h5>
                        </div>
                        <div class="card-body" id="searches-list">
                            <div class="text-center">
                                <div class="spinner-border" role="status"></div>
                            </div>
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
                    document.getElementById('conversion-rate').textContent = (data.conversion_rate || 0) + '%';
                }});
            
            // Charger les prospects
            fetch('/api/prospects')
                .then(r => r.json())
                .then(prospects => {{
                    const list = document.getElementById('prospects-list');
                    if (prospects.length === 0) {{
                        list.innerHTML = '<div class="text-muted text-center">Aucun prospect</div>';
                    }} else {{
                        list.innerHTML = prospects.slice(0, 5).map(p => 
                            `<div class="border-bottom pb-2 mb-2">
                                <strong>${{p.company_name}}</strong><br>
                                <small class="text-muted">
                                    <span class="badge bg-secondary">${{p.status}}</span>
                                    ${{new Date(p.created_at).toLocaleDateString()}}
                                </small>
                            </div>`
                        ).join('');
                    }}
                }});
            
            // Charger les recherches
            fetch('/api/searches')
                .then(r => r.json())
                .then(searches => {{
                    const list = document.getElementById('searches-list');
                    if (searches.length === 0) {{
                        list.innerHTML = '<div class="text-muted text-center">Aucune recherche</div>';
                    }} else {{
                        list.innerHTML = searches.slice(0, 5).map(s => 
                            `<div class="border-bottom pb-2 mb-2">
                                <strong>${{s.name}}</strong><br>
                                <small class="text-muted">${{s.category || 'Général'}}</small>
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
                            alert('✅ Prospect créé avec succès!');
                            location.reload();
                        }} else {{
                            alert('❌ Erreur: ' + data.error);
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
                            alert('✅ Recherche sauvegardée!');
                            location.reload();
                        }} else {{
                            alert('❌ Erreur: ' + data.error);
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
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container vh-100 d-flex align-items-center justify-content-center">
            <div class="card shadow" style="width: 400px;">
                <div class="card-body p-4">
                    <div class="text-center mb-4">
                        <h3 class="text-success">
                            <i class="fas fa-seedling"></i> AgriWeb CRM
                        </h3>
                        <p class="text-muted">Plateforme commerciale agricole</p>
                    </div>
                    
                    <form id="loginForm">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-envelope"></i> Email
                            </label>
                            <input type="email" class="form-control" id="email" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-lock"></i> Mot de passe
                            </label>
                            <input type="password" class="form-control" id="password" required>
                        </div>
                        <button type="submit" class="btn btn-success w-100">
                            <i class="fas fa-sign-in-alt"></i> Se connecter
                        </button>
                    </form>
                    
                    <div id="error" class="alert alert-danger mt-3 d-none"></div>
                    
                    <div class="mt-4 p-3 bg-light rounded">
                        <h6 class="text-center mb-3">Comptes de démonstration</h6>
                        <div class="small">
                            <div class="mb-2">
                                <strong>👑 Admin:</strong><br>
                                <code>admin@agriweb.com</code> / <code>admin123</code>
                            </div>
                            <div class="mb-2">
                                <strong>👔 Directeur:</strong><br>
                                <code>directeur@agriweb.com</code> / <code>director123</code>
                            </div>
                            <div>
                                <strong>💼 Commercial:</strong><br>
                                <code>commercial@agriweb.com</code> / <code>commercial123</code>
                            </div>
                        </div>
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
    return jsonify(prospects)

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
        return jsonify({'success': True, 'prospect_id': prospect['id']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/searches')
def api_searches():
    """API pour lister les recherches"""
    if not crm_manager.require_login():
        return jsonify({'error': 'Non connecté'}), 401
    
    user = crm_manager.get_current_user()
    searches = crm_manager.get_user_searches(user)
    return jsonify(searches)

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
        return jsonify({'success': True, 'search_id': search['id']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/admin')
def admin():
    """Page d'administration"""
    if not crm_manager.require_role(['admin', 'directeur_commercial']):
        return """
        <div style="text-align: center; padding: 50px;">
            <h2>❌ Accès refusé</h2>
            <p>Vous n'avez pas les permissions nécessaires.</p>
            <a href="/">Retour à l'accueil</a>
        </div>
        """, 403
    
    user = crm_manager.get_current_user()
    team_members = crm_manager.get_team_members(user)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Administration - AgriWeb CRM</title>
        <meta charset="utf-8">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-success">
            <div class="container">
                <span class="navbar-brand">
                    <i class="fas fa-users"></i> Administration CRM
                </span>
                <div>
                    <a href="/" class="btn btn-outline-light me-2">
                        <i class="fas fa-home"></i> Accueil
                    </a>
                    <a href="/logout" class="btn btn-outline-light">
                        <i class="fas fa-sign-out-alt"></i> Déconnexion
                    </a>
                </div>
            </div>
        </nav>
        
        <div class="container mt-4">
            <h2><i class="fas fa-users-cog"></i> Gestion de l'équipe</h2>
            
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="card text-white bg-info">
                        <div class="card-body text-center">
                            <h5>Membres d'équipe</h5>
                            <h2>{len(team_members)}</h2>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-list"></i> Liste des membres</h5>
                </div>
                <div class="card-body">
                    {'<div class="text-muted">Aucun membre dans votre équipe.</div>' if not team_members else ''}
                    {'''
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Nom</th>
                                    <th>Email</th>
                                    <th>Rôle</th>
                                    <th>Statut</th>
                                    <th>Dernière connexion</th>
                                </tr>
                            </thead>
                            <tbody>
                    ''' + ''.join([f'''
                                <tr>
                                    <td><i class="fas fa-user"></i> {member['name']}</td>
                                    <td>{member['email']}</td>
                                    <td><span class="badge bg-info">{member['role'].replace('_', ' ').title()}</span></td>
                                    <td><span class="badge bg-success">Actif</span></td>
                                    <td>{member.get('last_login', 'Jamais') or 'Jamais'}</td>
                                </tr>
                    ''' for member in team_members]) + '''
                            </tbody>
                        </table>
                    </div>
                    ''' if team_members else ''}
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# ═══════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ═══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("🔧 Initialisation de l'application AgriWeb CRM...")
    init_database()
    
    print("\n" + "="*70)
    print("🚀 AGRIWEB CRM - SYSTÈME COMMERCIAL HIÉRARCHIQUE")
    print("="*70)
    print("🌐 URL: http://localhost:5000")
    print("📱 Interface: Responsive Bootstrap 5")
    print("🗄️  Base de données: SQLite (agriweb_crm.db)")
    print("\n👤 COMPTES DE DÉMONSTRATION:")
    print("   👑 Admin: admin@agriweb.com / admin123")
    print("   👔 Directeur: directeur@agriweb.com / director123")  
    print("   💼 Commercial: commercial@agriweb.com / commercial123")
    print("\n🌟 FONCTIONNALITÉS CRM:")
    print("   ✅ Authentification par rôles")
    print("   ✅ Hiérarchie commerciale (Admin > Directeur > Commercial)")
    print("   ✅ Gestion des prospects avec assignation automatique")
    print("   ✅ Sauvegarde et partage de recherches")
    print("   ✅ Tableau de bord personnalisé par rôle")
    print("   ✅ Administration d'équipe")
    print("   ✅ Statistiques et reporting")
    print("="*70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)