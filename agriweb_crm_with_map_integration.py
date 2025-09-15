"""
Extension du système CRM avec intégration automatique des recherches
Version mise à jour de agriweb_crm_standalone.py avec fonctionnalités d'intégration
"""

import os
import json
import sqlite3
import hashlib
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from crm_integration import AgriWebCRMIntegrator, integrate_search_results_to_crm

app = Flask(__name__)
app.secret_key = 'agriweb_crm_secret_key_2024'

class SimpleCRMManager:
    def __init__(self, db_path='agriweb_crm.db'):
        self.db_path = db_path
        self.init_database()
        self.integrator = AgriWebCRMIntegrator(db_path)
    
    def init_database(self):
        """Initialise la base de données avec les tables nécessaires"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table des utilisateurs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                role TEXT NOT NULL DEFAULT 'commercial',
                manager_id TEXT,
                is_active BOOLEAN DEFAULT 1,
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
                contact_person TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                postal_code TEXT,
                coordinates TEXT,
                industry TEXT,
                website TEXT,
                source TEXT,
                source_search_id TEXT,
                status TEXT DEFAULT 'nouveau',
                priority TEXT DEFAULT 'normale',
                estimated_value REAL,
                notes TEXT,
                tags TEXT,
                created_by_id TEXT NOT NULL,
                assigned_to_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by_id) REFERENCES users (id),
                FOREIGN KEY (assigned_to_id) REFERENCES users (id),
                FOREIGN KEY (source_search_id) REFERENCES saved_searches (id)
            )
        ''')
        
        # Table des recherches sauvegardées
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_searches (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                search_params TEXT,
                user_id TEXT NOT NULL,
                category TEXT DEFAULT 'général',
                auto_prospect BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Table des interactions avec les prospects
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prospect_interactions (
                id TEXT PRIMARY KEY,
                prospect_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                description TEXT,
                interaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                follow_up_date DATE,
                FOREIGN KEY (prospect_id) REFERENCES prospects (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        
        # Créer des utilisateurs de démonstration
        self._create_demo_users(cursor)
        
        conn.close()
        print("✅ Base de données initialisée avec succès")
    
    def _create_demo_users(self, cursor):
        """Crée des utilisateurs de démonstration"""
        demo_users = [
            {
                'id': 'admin-001',
                'username': 'admin',
                'email': 'admin@agriweb.com',
                'password': 'admin123',
                'first_name': 'Administrateur',
                'last_name': 'Système',
                'role': 'admin',
                'manager_id': None
            },
            {
                'id': 'dir-001',
                'username': 'directeur',
                'email': 'directeur@agriweb.com',
                'password': 'dir123',
                'first_name': 'Jean',
                'last_name': 'Dupont',
                'role': 'directeur_commercial',
                'manager_id': 'admin-001'
            },
            {
                'id': 'com-001',
                'username': 'commercial',
                'email': 'commercial@agriweb.com',
                'password': 'com123',
                'first_name': 'Marie',
                'last_name': 'Martin',
                'role': 'commercial',
                'manager_id': 'dir-001'
            }
        ]
        
        for user_data in demo_users:
            cursor.execute("SELECT id FROM users WHERE username = ?", (user_data['username'],))
            if not cursor.fetchone():
                password_hash = hashlib.sha256(user_data['password'].encode()).hexdigest()
                cursor.execute('''
                    INSERT INTO users (id, username, email, password_hash, first_name, last_name, role, manager_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_data['id'], user_data['username'], user_data['email'], 
                    password_hash, user_data['first_name'], user_data['last_name'],
                    user_data['role'], user_data['manager_id']
                ))
    
    def authenticate_user(self, username, password):
        """Authentifie un utilisateur"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("""
            SELECT * FROM users 
            WHERE username = ? AND password_hash = ? AND is_active = 1
        """, (username, password_hash))
        
        user = cursor.fetchone()
        
        if user:
            # Mettre à jour la dernière connexion
            cursor.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            """, (user['id'],))
            conn.commit()
        
        conn.close()
        return dict(user) if user else None
    
    def get_prospects(self, user_id, filters=None):
        """Récupère les prospects selon les filtres et permissions"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Base query avec jointures
        query = """
            SELECT p.*, 
                   creator.first_name || ' ' || creator.last_name as created_by_name,
                   assigned.first_name || ' ' || assigned.last_name as assigned_to_name,
                   ss.name as search_name
            FROM prospects p
            LEFT JOIN users creator ON p.created_by_id = creator.id
            LEFT JOIN users assigned ON p.assigned_to_id = assigned.id
            LEFT JOIN saved_searches ss ON p.source_search_id = ss.id
            WHERE 1=1
        """
        
        params = []
        
        # Permissions selon le rôle
        cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        user_role = cursor.fetchone()
        
        if user_role and user_role['role'] == 'commercial':
            query += " AND p.assigned_to_id = ?"
            params.append(user_id)
        elif user_role and user_role['role'] == 'directeur_commercial':
            # Voir ses prospects + ceux de son équipe
            query += """ AND (p.assigned_to_id = ? OR 
                            p.assigned_to_id IN (SELECT id FROM users WHERE manager_id = ?))"""
            params.extend([user_id, user_id])
        
        # Filtres additionnels
        if filters:
            if filters.get('status'):
                query += " AND p.status = ?"
                params.append(filters['status'])
            
            if filters.get('priority'):
                query += " AND p.priority = ?"
                params.append(filters['priority'])
            
            if filters.get('source'):
                query += " AND p.source = ?"
                params.append(filters['source'])
        
        query += " ORDER BY p.created_at DESC"
        
        cursor.execute(query, params)
        prospects = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return prospects
    
    def create_prospect(self, prospect_data, user_id):
        """Crée un nouveau prospect"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        prospect_id = str(uuid.uuid4())
        
        try:
            cursor.execute('''
                INSERT INTO prospects (
                    id, company_name, contact_person, email, phone, address, city, postal_code,
                    coordinates, industry, website, source, status, priority, estimated_value,
                    notes, tags, created_by_id, assigned_to_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prospect_id, prospect_data.get('company_name'),
                prospect_data.get('contact_person'), prospect_data.get('email'),
                prospect_data.get('phone'), prospect_data.get('address'),
                prospect_data.get('city'), prospect_data.get('postal_code'),
                prospect_data.get('coordinates'), prospect_data.get('industry'),
                prospect_data.get('website'), prospect_data.get('source', 'manuel'),
                prospect_data.get('status', 'nouveau'), prospect_data.get('priority', 'normale'),
                prospect_data.get('estimated_value'), prospect_data.get('notes'),
                prospect_data.get('tags'), user_id, prospect_data.get('assigned_to_id', user_id)
            ))
            
            conn.commit()
            conn.close()
            return prospect_id
            
        except Exception as e:
            conn.close()
            raise e
    
    def get_user_team(self, user_id):
        """Récupère l'équipe d'un utilisateur"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, first_name, last_name, role
            FROM users
            WHERE manager_id = ? AND is_active = 1
            ORDER BY first_name, last_name
        """, (user_id,))
        
        team = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return team
    
    def get_integration_dashboard_data(self, user_id):
        """Récupère les données pour le dashboard d'intégration"""
        stats = self.integrator.get_integration_stats(user_id)
        
        # Ajouter les recherches récentes avec auto-création
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ss.*, COUNT(p.id) as prospects_generated
            FROM saved_searches ss
            LEFT JOIN prospects p ON ss.id = p.source_search_id
            WHERE ss.user_id = ? AND ss.auto_prospect = 1
            GROUP BY ss.id
            ORDER BY ss.created_at DESC
            LIMIT 10
        """, (user_id,))
        
        recent_auto_searches = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            'stats': stats,
            'recent_auto_searches': recent_auto_searches
        }

# Instance du gestionnaire CRM
crm_manager = SimpleCRMManager()

# ========================= ROUTES =========================

@app.route('/')
def index():
    """Page d'accueil avec carte intégrée"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgriWeb CRM - Système Intégré</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        .map-container { height: 500px; border: 1px solid #dee2e6; border-radius: 0.375rem; }
        .crm-panel { background: #f8f9fa; border-radius: 0.375rem; padding: 1rem; }
        .integration-controls { margin: 1rem 0; }
        .search-integration-btn { background: linear-gradient(45deg, #28a745, #20c997); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-success">
        <div class="container">
            <a class="navbar-brand" href="#">🌾 AgriWeb CRM</a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text me-3">
                    Bonjour, ''' + session.get('full_name', 'Utilisateur') + ''' (''' + session.get('role', '') + ''')
                </span>
                <a class="nav-link" href="/crm">CRM Dashboard</a>
                <a class="nav-link" href="/logout">Déconnexion</a>
            </div>
        </div>
    </nav>

    <div class="container-fluid py-4">
        <div class="row">
            <!-- Carte principale -->
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">🗺️ Carte de Recherche</h5>
                        <div class="integration-controls">
                            <button id="integrateSearchBtn" class="btn btn-sm search-integration-btn text-white" disabled>
                                ⚡ Créer Prospects
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div id="map" class="map-container"></div>
                        <div class="mt-3">
                            <div class="row">
                                <div class="col-md-6">
                                    <input type="text" id="searchInput" class="form-control" 
                                           placeholder="Nom de la recherche pour CRM..." />
                                </div>
                                <div class="col-md-6">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="autoIntegration" checked>
                                        <label class="form-check-label" for="autoIntegration">
                                            Intégration automatique au CRM
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Panneau CRM -->
            <div class="col-lg-4">
                <div class="crm-panel">
                    <h5>📊 Tableau de Bord CRM</h5>
                    
                    <div class="row text-center mb-3">
                        <div class="col-4">
                            <div class="card bg-primary text-white">
                                <div class="card-body p-2">
                                    <div class="h4" id="totalProspects">-</div>
                                    <small>Total</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="card bg-warning text-white">
                                <div class="card-body p-2">
                                    <div class="h4" id="newProspects">-</div>
                                    <small>Nouveaux</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="card bg-success text-white">
                                <div class="card-body p-2">
                                    <div class="h4" id="autoProspects">-</div>
                                    <small>Auto</small>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">Derniers Prospects</label>
                        <div id="recentProspects" class="list-group" style="max-height: 200px; overflow-y: auto;">
                            <div class="text-center p-3">
                                <div class="spinner-border spinner-border-sm" role="status"></div>
                                <div>Chargement...</div>
                            </div>
                        </div>
                    </div>

                    <div class="d-grid">
                        <a href="/crm" class="btn btn-success">
                            🚀 Dashboard Complet
                        </a>
                    </div>
                </div>

                <!-- Status intégration -->
                <div class="mt-3">
                    <div id="integrationStatus" class="alert" style="display: none;"></div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Variables globales
        let map;
        let currentSearchResults = null;
        let markersLayer = L.layerGroup();

        // Initialisation de la carte
        function initializeMap() {
            map = L.map('map').setView([46.2276, 2.2137], 6);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            
            markersLayer.addTo(map);
            
            // Simulation de recherche au clic
            map.on('click', function(e) {
                simulateSearch(e.latlng);
            });
        }

        // Simulation d'une recherche (remplacer par vraie recherche)
        function simulateSearch(latlng) {
            const searchResults = {
                type: "FeatureCollection",
                features: [
                    {
                        type: "Feature",
                        geometry: {
                            type: "Point",
                            coordinates: [latlng.lng, latlng.lat]
                        },
                        properties: {
                            name: "Entreprise Agricole Test",
                            amenity: "farm",
                            landuse: "farmland",
                            "addr:city": "Test City",
                            "addr:postcode": "12345"
                        }
                    }
                ]
            };
            
            displaySearchResults(searchResults);
        }

        // Affichage des résultats de recherche
        function displaySearchResults(results) {
            currentSearchResults = results;
            markersLayer.clearLayers();
            
            results.features.forEach(feature => {
                if (feature.geometry.type === 'Point') {
                    const coords = feature.geometry.coordinates;
                    const marker = L.marker([coords[1], coords[0]])
                        .bindPopup(`
                            <strong>${feature.properties.name || 'Sans nom'}</strong><br>
                            ${feature.properties['addr:city'] || ''}<br>
                            Type: ${feature.properties.amenity || feature.properties.landuse || 'N/A'}
                        `);
                    markersLayer.addLayer(marker);
                }
            });
            
            // Activer le bouton d'intégration
            document.getElementById('integrateSearchBtn').disabled = false;
            
            // Auto-intégration si activée
            if (document.getElementById('autoIntegration').checked) {
                setTimeout(integrateSearchToCRM, 1000);
            }
        }

        // Intégration des résultats au CRM
        function integrateSearchToCRM() {
            if (!currentSearchResults) {
                showIntegrationStatus('Aucun résultat à intégrer', 'warning');
                return;
            }
            
            const searchName = document.getElementById('searchInput').value || 
                              `Recherche ${new Date().toLocaleString()}`;
            
            showIntegrationStatus('Intégration en cours...', 'info');
            
            fetch('/api/integrate_search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    search_results: currentSearchResults,
                    search_name: searchName
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showIntegrationStatus(data.message, 'success');
                    loadCRMStats(); // Recharger les stats
                } else {
                    showIntegrationStatus(`Erreur: ${data.error}`, 'danger');
                }
            })
            .catch(error => {
                showIntegrationStatus(`Erreur réseau: ${error.message}`, 'danger');
            });
        }

        // Affichage du statut d'intégration
        function showIntegrationStatus(message, type) {
            const statusDiv = document.getElementById('integrationStatus');
            statusDiv.className = `alert alert-${type}`;
            statusDiv.textContent = message;
            statusDiv.style.display = 'block';
            
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        }

        // Chargement des statistiques CRM
        function loadCRMStats() {
            fetch('/api/prospects')
                .then(response => response.json())
                .then(prospects => {
                    const total = prospects.length;
                    const newCount = prospects.filter(p => p.status === 'nouveau').length;
                    const autoCount = prospects.filter(p => p.source === 'recherche_automatique').length;
                    
                    document.getElementById('totalProspects').textContent = total;
                    document.getElementById('newProspects').textContent = newCount;
                    document.getElementById('autoProspects').textContent = autoCount;
                    
                    // Afficher les derniers prospects
                    const recentContainer = document.getElementById('recentProspects');
                    recentContainer.innerHTML = '';
                    
                    prospects.slice(0, 5).forEach(prospect => {
                        const item = document.createElement('div');
                        item.className = 'list-group-item list-group-item-action py-2';
                        item.innerHTML = `
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>${prospect.company_name}</strong>
                                    <small class="text-muted d-block">${prospect.city || ''}</small>
                                </div>
                                <span class="badge bg-${getStatusColor(prospect.status)}">${prospect.status}</span>
                            </div>
                        `;
                        recentContainer.appendChild(item);
                    });
                    
                    if (prospects.length === 0) {
                        recentContainer.innerHTML = '<div class="text-center p-3 text-muted">Aucun prospect</div>';
                    }
                })
                .catch(error => {
                    console.error('Erreur chargement prospects:', error);
                });
        }

        // Couleur selon le statut
        function getStatusColor(status) {
            switch (status) {
                case 'nouveau': return 'warning';
                case 'qualifié': return 'info';
                case 'négociation': return 'primary';
                case 'gagné': return 'success';
                case 'perdu': return 'danger';
                default: return 'secondary';
            }
        }

        // Event listeners
        document.getElementById('integrateSearchBtn').addEventListener('click', integrateSearchToCRM);

        // Initialisation
        document.addEventListener('DOMContentLoaded', function() {
            initializeMap();
            loadCRMStats();
        });
    </script>
</body>
</html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = crm_manager.authenticate_user(username, password)
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = f"{user['first_name']} {user['last_name']}"
            
            flash(f'Bienvenue {user["first_name"]} !', 'success')
            return redirect(url_for('index'))
        else:
            flash('Identifiants incorrects', 'error')
    
    return '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexion - AgriWeb CRM</title>
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
                            <p class="text-muted">Système de gestion commerciale</p>
                        </div>
                        
                        <form method="POST">
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
                                • admin / admin123<br>
                                • directeur / dir123<br>
                                • commercial / com123
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    '''

@app.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    flash('Vous êtes déconnecté', 'info')
    return redirect(url_for('login'))

@app.route('/crm')
def crm_dashboard():
    """Dashboard CRM principal"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Récupérer les prospects
    filters = {
        'status': request.args.get('status'),
        'priority': request.args.get('priority'),
        'source': request.args.get('source')
    }
    filters = {k: v for k, v in filters.items() if v}
    
    prospects = crm_manager.get_prospects(session['user_id'], filters)
    
    # Statistiques
    total_prospects = len(prospects)
    new_prospects = len([p for p in prospects if p['status'] == 'nouveau'])
    qualified_prospects = len([p for p in prospects if p['status'] == 'qualifié'])
    
    # Données d'intégration
    integration_data = crm_manager.get_integration_dashboard_data(session['user_id'])
    
    return f'''
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
            <a class="navbar-brand" href="/">🌾 AgriWeb CRM</a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text me-3">{session.get('full_name', 'Utilisateur')} ({session.get('role', '')})</span>
                <a class="nav-link" href="/">Carte</a>
                <a class="nav-link" href="/logout">Déconnexion</a>
            </div>
        </div>
    </nav>

    <div class="container-fluid py-4">
        <div class="row mb-4">
            <div class="col">
                <h2>📊 Dashboard CRM</h2>
            </div>
        </div>

        <!-- Statistiques -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card bg-primary text-white">
                    <div class="card-body text-center">
                        <h3>{total_prospects}</h3>
                        <p class="mb-0">Total Prospects</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning text-white">
                    <div class="card-body text-center">
                        <h3>{new_prospects}</h3>
                        <p class="mb-0">Nouveaux</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body text-center">
                        <h3>{qualified_prospects}</h3>
                        <p class="mb-0">Qualifiés</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body text-center">
                        <h3>{integration_data["stats"]["auto_prospects_created"]}</h3>
                        <p class="mb-0">Auto-générés</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Liste des prospects -->
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">📋 Liste des Prospects</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Entreprise</th>
                                <th>Ville</th>
                                <th>Source</th>
                                <th>Statut</th>
                                <th>Assigné à</th>
                                <th>Créé le</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f'''
                            <tr>
                                <td><strong>{p["company_name"]}</strong></td>
                                <td>{p["city"] or "-"}</td>
                                <td>
                                    <span class="badge bg-{"success" if p["source"] == "recherche_automatique" else "secondary"}">
                                        {p["source"]}
                                    </span>
                                </td>
                                <td>
                                    <span class="badge bg-{"warning" if p["status"] == "nouveau" else "info" if p["status"] == "qualifié" else "secondary"}">
                                        {p["status"]}
                                    </span>
                                </td>
                                <td>{p["assigned_to_name"] or "-"}</td>
                                <td>{p["created_at"][:10] if p["created_at"] else "-"}</td>
                            </tr>
                            ''' for p in prospects[:20]])}
                        </tbody>
                    </table>
                </div>
                
                {f'<p class="text-muted mt-3">Affichage de 20 prospects sur {total_prospects} total(s)</p>' if total_prospects > 20 else ''}
            </div>
        </div>
    </div>
</body>
</html>
    '''

@app.route('/api/integrate_search', methods=['POST'])
def api_integrate_search():
    """API pour intégrer les résultats de recherche au CRM"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Non authentifié'}), 401
    
    try:
        data = request.get_json()
        search_results = data.get('search_results')
        search_name = data.get('search_name', f'Recherche {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        
        if not search_results:
            return jsonify({'success': False, 'error': 'Aucun résultat fourni'}), 400
        
        # Utiliser la fonction d'intégration
        result = integrate_search_results_to_crm(
            search_results, search_name, session
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Erreur serveur: {str(e)}'
        }), 500

@app.route('/api/prospects', methods=['GET', 'POST'])
def api_prospects():
    """API pour gérer les prospects"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    if request.method == 'GET':
        filters = {
            'status': request.args.get('status'),
            'priority': request.args.get('priority'),
            'source': request.args.get('source')
        }
        filters = {k: v for k, v in filters.items() if v}
        
        prospects = crm_manager.get_prospects(session['user_id'], filters)
        return jsonify(prospects)
    
    elif request.method == 'POST':
        try:
            prospect_data = request.get_json()
            prospect_id = crm_manager.create_prospect(prospect_data, session['user_id'])
            return jsonify({'success': True, 'prospect_id': prospect_id})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/team')
def api_team():
    """API pour récupérer l'équipe"""
    if 'user_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    team = crm_manager.get_user_team(session['user_id'])
    return jsonify(team)

if __name__ == '__main__':
    print("🚀 Démarrage du serveur AgriWeb CRM Intégré...")
    print("📍 URL: http://localhost:5000")
    print("👥 Comptes de test:")
    print("   - Admin: admin / admin123")
    print("   - Directeur: directeur / dir123") 
    print("   - Commercial: commercial / com123")
    print("✨ Fonctionnalités:")
    print("   • Carte interactive avec recherche")
    print("   • Intégration automatique au CRM")
    print("   • Gestion hiérarchique des prospects")
    print("   • Dashboard temps réel")
    print("   • Assignation automatique selon les rôles")
    
    app.run(debug=True, host='0.0.0.0', port=5001)