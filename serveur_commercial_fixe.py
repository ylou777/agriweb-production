#!/usr/bin/env python3
"""
AgriWeb 2.0 - Serveur Commercial Fixé
Version avec gestion correcte des emails existants
"""

from flask import Flask, request, jsonify, session, render_template_string
import json
import os
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
app.secret_key = "agriweb_production_key_2025_secure"

class UserManager:
    def __init__(self):
        self.users_file = 'production_users.json'
        self.licenses_file = 'production_licenses.json'
        self.users = self.load_users()
        self.licenses = self.load_licenses()
    
    def load_users(self):
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erreur chargement utilisateurs: {e}")
        return {}
    
    def load_licenses(self):
        try:
            if os.path.exists(self.licenses_file):
                with open(self.licenses_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erreur chargement licences: {e}")
        return {}
    
    def save_users(self):
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            print(f"Erreur sauvegarde utilisateurs: {e}")
            return False
    
    def save_licenses(self):
        try:
            with open(self.licenses_file, 'w', encoding='utf-8') as f:
                json.dump(self.licenses, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            print(f"Erreur sauvegarde licences: {e}")
            return False
    
    def generate_license_key(self):
        return f"TRIAL-{str(uuid.uuid4())[:8]}"
    
    def create_trial_user(self, email, name, company=""):
        """Créer un utilisateur avec essai gratuit - VERSION CORRIGÉE"""
        
        print(f"📝 Tentative d'inscription: {email}")
        
        if email in self.users:
            # Utilisateur existe déjà
            existing_user = self.users[email]
            print(f"👤 Utilisateur existant trouvé: {email}")
            
            try:
                expires = datetime.fromisoformat(existing_user['expires'])
                print(f"📅 Expiration: {expires}")
                
                if datetime.now() < expires:
                    # Essai encore valide
                    print("✅ Essai encore actif")
                    return {
                        "success": False, 
                        "error": "Cet email est déjà utilisé", 
                        "action": "login",
                        "message": f"Vous avez déjà un essai actif jusqu'au {expires.strftime('%d/%m/%Y')}. Connectez-vous.",
                        "debug": "Essai actif"
                    }
                else:
                    # Essai expiré
                    print("⚠️ Essai expiré")
                    return {
                        "success": False, 
                        "error": "Cet email est déjà utilisé", 
                        "action": "expired",
                        "message": "Votre essai gratuit a expiré. Contactez-nous pour une licence payante.",
                        "debug": "Essai expiré"
                    }
            except Exception as e:
                print(f"❌ Erreur lors de la vérification: {e}")
                return {
                    "success": False, 
                    "error": "Erreur de données utilisateur",
                    "debug": str(e)
                }
        
        # Nouvel utilisateur
        print(f"✅ Nouveau utilisateur: {email}")
        user_id = str(uuid.uuid4())
        license_key = self.generate_license_key()
        expires = datetime.now() + timedelta(days=7)
        
        user_data = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "company": company,
            "license_type": "trial",
            "license_key": license_key,
            "created": datetime.now().isoformat(),
            "expires": expires.isoformat(),
            "active": True,
            "searches_used": 0,
            "searches_limit": 100,
            "last_login": None
        }
        
        # Ajouter aux bases de données
        self.users[email] = user_data
        self.licenses[license_key] = {
            "user_email": email,
            "type": "trial",
            "expires": expires.isoformat(),
            "active": True
        }
        
        # Sauvegarder
        if self.save_users() and self.save_licenses():
            print(f"💾 Utilisateur sauvegardé: {email}")
            return {
                "success": True,
                "message": f"Essai gratuit activé pour {name}",
                "user": user_data,
                "license_key": license_key,
                "debug": "Nouveau compte créé"
            }
        else:
            return {"success": False, "error": "Erreur de sauvegarde"}
    
    def authenticate_user(self, email):
        """Authentifier un utilisateur existant"""
        
        print(f"🔑 Tentative de connexion: {email}")
        
        if email not in self.users:
            return {
                "success": False, 
                "error": "Email non trouvé",
                "debug": f"Email {email} pas dans la base"
            }
        
        user = self.users[email]
        
        # Vérifier si non expiré
        try:
            expires = datetime.fromisoformat(user['expires'])
            if datetime.now() > expires:
                return {
                    "success": False, 
                    "error": f"Votre accès a expiré le {expires.strftime('%d/%m/%Y')}. Contactez-nous pour renouveler.",
                    "debug": "Compte expiré"
                }
        except Exception as e:
            return {
                "success": False, 
                "error": "Erreur de données utilisateur",
                "debug": str(e)
            }
        
        # Mettre à jour la dernière connexion
        user['last_login'] = datetime.now().isoformat()
        self.users[email] = user
        self.save_users()
        
        print(f"✅ Connexion réussie: {email}")
        return {
            "success": True,
            "message": f"Connexion réussie ! Bienvenue {user['name']}",
            "user": user,
            "debug": "Connexion OK"
        }

# Initialiser le gestionnaire
user_manager = UserManager()
print(f"👥 Gestionnaire initialisé avec {len(user_manager.users)} utilisateurs")

# Template de la page d'accueil avec JavaScript corrigé
LANDING_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgriWeb 2.0 - Géolocalisation Agricole Professionnelle</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .hero-section { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 80px 0; }
        .feature-card { border: none; box-shadow: 0 4px 15px rgba(0,0,0,0.1); transition: transform 0.3s; }
        .feature-card:hover { transform: translateY(-5px); }
        .pricing-card { border: none; box-shadow: 0 8px 25px rgba(0,0,0,0.1); transition: transform 0.3s; }
        .pricing-card:hover { transform: translateY(-10px); }
        .btn-custom { background: linear-gradient(45deg, #667eea, #764ba2); border: none; color: white; }
        .btn-custom:hover { background: linear-gradient(45deg, #764ba2, #667eea); color: white; }
        .status-badge { background: #28a745; color: white; padding: 5px 15px; border-radius: 20px; font-size: 0.9em; }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
        <div class="container">
            <a class="navbar-brand" href="#"><i class="fas fa-globe"></i> AgriWeb 2.0</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/login">Connexion</a>
                <a class="nav-link" href="/admin">Administration</a>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero-section" style="margin-top: 56px;">
        <div class="container text-center">
            <h1 class="display-4 fw-bold mb-4">AgriWeb 2.0</h1>
            <p class="lead mb-4">Géolocalisation Agricole Professionnelle avec GeoServer Intégré</p>
            <div class="status-badge mb-4">
                <i class="fas fa-check-circle"></i> ✅ Système Opérationnel - GeoServer connecté avec 48+ couches de données
            </div>
        </div>
    </section>

    <!-- Features -->
    <section class="py-5">
        <div class="container">
            <h2 class="text-center mb-5">Fonctionnalités Avancées</h2>
            <div class="row g-4">
                <div class="col-md-3">
                    <div class="card feature-card h-100 text-center p-4">
                        <div class="card-body">
                            <i class="fas fa-map fa-3x text-primary mb-3"></i>
                            <h5>🗺️ GeoServer Intégré</h5>
                            <p>Accès à 48+ couches géographiques : cadastre, RPG, zones urbaines, parkings, friches...</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card feature-card h-100 text-center p-4">
                        <div class="card-body">
                            <i class="fas fa-search fa-3x text-success mb-3"></i>
                            <h5>🎯 Recherche Précise</h5>
                            <p>Localisation par commune, coordonnées GPS, filtrage par distance aux réseaux électriques</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card feature-card h-100 text-center p-4">
                        <div class="card-body">
                            <i class="fas fa-chart-bar fa-3x text-warning mb-3"></i>
                            <h5>📊 Rapports Détaillés</h5>
                            <p>Analyses complètes avec cartes interactives, données cadastrales et risques géologiques</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card feature-card h-100 text-center p-4">
                        <div class="card-body">
                            <i class="fas fa-shield-alt fa-3x text-danger mb-3"></i>
                            <h5>🔒 Sécurisé & Fiable</h5>
                            <p>Système de licences professionnel, sauvegarde automatique, haute disponibilité</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Pricing -->
    <section class="py-5 bg-light">
        <div class="container">
            <h2 class="text-center mb-5">Tarifs Professionnels</h2>
            <div class="row g-4">
                <div class="col-lg-3">
                    <div class="card pricing-card h-100">
                        <div class="card-header bg-success text-white text-center">
                            <h4>🆓 Essai Gratuit</h4>
                            <h2>0€</h2>
                            <p>7 jours d'accès complet</p>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled">
                                <li>✅ 10 communes</li>
                                <li>✅ Toutes les fonctionnalités</li>
                                <li>✅ Support technique</li>
                                <li>✅ GeoServer inclus</li>
                            </ul>
                            <button class="btn btn-success w-100" onclick="startTrial('trial')">Commencer l'Essai</button>
                        </div>
                    </div>
                </div>
                <div class="col-lg-3">
                    <div class="card pricing-card h-100">
                        <div class="card-header bg-primary text-white text-center">
                            <h4>💼 Basic</h4>
                            <h2>299€/an</h2>
                            <p>Pour petites exploitations</p>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled">
                                <li>✅ 100 communes/mois</li>
                                <li>✅ 500 rapports/jour</li>
                                <li>✅ API basique</li>
                                <li>✅ Support email</li>
                            </ul>
                            <button class="btn btn-primary w-100" onclick="startTrial('basic')">Choisir Basic</button>
                        </div>
                    </div>
                </div>
                <div class="col-lg-3">
                    <div class="card pricing-card h-100">
                        <div class="card-header bg-warning text-white text-center">
                            <h4>🚀 Pro</h4>
                            <h2>999€/an</h2>
                            <p>Pour professionnels</p>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled">
                                <li>✅ 1000 communes/mois</li>
                                <li>✅ API complète</li>
                                <li>✅ Exports automatisés</li>
                                <li>✅ Support prioritaire</li>
                            </ul>
                            <button class="btn btn-warning w-100" onclick="startTrial('pro')">Choisir Pro</button>
                        </div>
                    </div>
                </div>
                <div class="col-lg-3">
                    <div class="card pricing-card h-100">
                        <div class="card-header bg-dark text-white text-center">
                            <h4>🏢 Enterprise</h4>
                            <h2>2999€/an</h2>
                            <p>Pour grandes organisations</p>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled">
                                <li>✅ Accès illimité</li>
                                <li>✅ GeoServer dédié</li>
                                <li>✅ API sur mesure</li>
                                <li>✅ Support 24/7</li>
                            </ul>
                            <button class="btn btn-dark w-100" onclick="startTrial('enterprise')">Choisir Enterprise</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- CTA Section -->
    <section class="py-5">
        <div class="container text-center">
            <h2 class="mb-4">🆓 Démarrer votre essai gratuit (7 jours)</h2>
            <div id="trial-alert"></div>
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="mb-3">
                        <input type="email" class="form-control" id="trial-email" placeholder="Adresse email professionnelle" value="ylaurent.perso@gmail.com">
                    </div>
                    <div class="mb-3">
                        <input type="text" class="form-control" id="trial-company" placeholder="Nom de l'entreprise" value="lumicasol">
                    </div>
                    <div class="mb-3">
                        <input type="text" class="form-control" id="trial-name" placeholder="Nom complet" value="laurent">
                    </div>
                    <button class="btn btn-custom btn-lg me-3" onclick="submitTrialForm()">
                        <i class="fas fa-rocket"></i> Activer l'Essai Gratuit
                    </button>
                    <button class="btn btn-secondary btn-lg" onclick="clearForm()">Annuler</button>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-dark text-white py-5">
        <div class="container text-center">
            <h3 class="mb-3">Prêt à optimiser votre géolocalisation agricole ?</h3>
            <p class="mb-4">Démarrez votre essai gratuit de 7 jours dès maintenant</p>
            <button class="btn btn-custom btn-lg" onclick="submitTrialForm()">
                <i class="fas fa-play"></i> Essai Gratuit
            </button>
            <hr class="my-4">
            <p>&copy; 2025 AgriWeb 2.0 - Géolocalisation Agricole Professionnelle</p>
            <p><small>Système intégré avec GeoServer - Support technique disponible</small></p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let selectedPlan = 'trial';
        
        function startTrial(plan) {
            selectedPlan = plan;
            document.getElementById('trial-alert').innerHTML = 
                `<div class="alert alert-info">Plan sélectionné: ${plan.toUpperCase()}</div>`;
            document.getElementById('trial-email').focus();
        }
        
        function clearForm() {
            document.getElementById('trial-email').value = '';
            document.getElementById('trial-name').value = '';
            document.getElementById('trial-company').value = '';
            document.getElementById('trial-alert').innerHTML = '';
        }
        
        async function submitTrialForm() {
            const name = document.getElementById('trial-name').value.trim();
            const email = document.getElementById('trial-email').value.trim();
            const company = document.getElementById('trial-company').value.trim();
            
            if (!name || !email) {
                showAlert('Nom et email requis', 'danger');
                return;
            }
            
            try {
                console.log('Envoi de la requête d\\'inscription...');
                const response = await fetch('/api/trial/register', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name: name, email: email, company: company})
                });
                
                const result = await response.json();
                console.log('Réponse reçue:', result);
                
                if (result.success) {
                    showAlert(result.message, 'success');
                    setTimeout(() => {
                        window.location.href = '/app';
                    }, 2000);
                } else {
                    // Gestion spéciale pour les utilisateurs existants - VERSION CORRIGÉE
                    if (result.action === 'login') {
                        showAlert(result.message, 'warning');
                        // Montrer le bouton de connexion
                        document.getElementById('trial-alert').innerHTML += 
                            `<div class="mt-3">
                                <button class="btn btn-primary btn-lg" onclick="loginExistingUser('${email}')">
                                    🔑 Se connecter avec cet email
                                </button>
                            </div>`;
                    } else if (result.action === 'expired') {
                        showAlert(result.message, 'info');
                        document.getElementById('trial-alert').innerHTML += 
                            `<div class="mt-3">
                                <button class="btn btn-success btn-lg" onclick="contactUs()">
                                    💰 Obtenir une licence payante
                                </button>
                            </div>`;
                    } else {
                        showAlert(result.error || 'Erreur inconnue', 'danger');
                    }
                }
            } catch (error) {
                console.error('Erreur:', error);
                showAlert('Erreur de connexion: ' + error.message, 'danger');
            }
        }
        
        async function loginExistingUser(email) {
            console.log('Tentative de connexion pour:', email);
            try {
                const response = await fetch('/api/user/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: email})
                });
                
                const result = await response.json();
                console.log('Résultat connexion:', result);
                
                if (result.success) {
                    showAlert(result.message, 'success');
                    setTimeout(() => {
                        window.location.href = '/app';
                    }, 2000);
                } else {
                    showAlert(result.error, 'danger');
                }
            } catch (error) {
                console.error('Erreur connexion:', error);
                showAlert('Erreur de connexion: ' + error.message, 'danger');
            }
        }
        
        function contactUs() {
            showAlert('📧 Contactez-nous: contact@agriweb.fr ou 📞 01.23.45.67.89', 'info');
        }
        
        function showAlert(message, type) {
            document.getElementById('trial-alert').innerHTML = 
                `<div class="alert alert-${type}">${message}</div>`;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def landing_page():
    """Page d'accueil commerciale"""
    return render_template_string(LANDING_PAGE_TEMPLATE)

@app.route('/api/trial/register', methods=['POST'])
def register_trial():
    """Inscription pour essai gratuit - VERSION CORRIGÉE"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        name = data.get('name', '').strip()
        company = data.get('company', '').strip()
        
        if not email or not name:
            return jsonify({"success": False, "error": "Email et nom requis"}), 400
        
        result = user_manager.create_trial_user(email, name, company)
        
        if result["success"]:
            # Connecter automatiquement l'utilisateur
            session['authenticated'] = True
            session['user_email'] = email
            session['user_data'] = result["user"]
            session['license_key'] = result["license_key"]
            
            return jsonify(result)
        else:
            # Retourner l'erreur avec les actions spécifiques
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Erreur inscription: {e}")
        return jsonify({"success": False, "error": "Erreur serveur", "debug": str(e)}), 500

@app.route('/api/user/login', methods=['POST'])
def login_existing_user():
    """Connexion d'un utilisateur existant - VERSION CORRIGÉE"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({"success": False, "error": "Email requis"}), 400
        
        result = user_manager.authenticate_user(email)
        
        if result["success"]:
            # Connecter l'utilisateur
            session['authenticated'] = True
            session['user_email'] = email
            session['user_data'] = result["user"]
            session['license_key'] = result["user"]["license_key"]
            
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Erreur connexion: {e}")
        return jsonify({"success": False, "error": "Erreur serveur", "debug": str(e)}), 500

@app.route('/app')
def app_page():
    """Page d'application (après connexion)"""
    if not session.get('authenticated'):
        return redirect('/login')
    
    return f"""
    <h1>🎉 Bienvenue dans AgriWeb 2.0!</h1>
    <p>Utilisateur connecté: {session.get('user_email')}</p>
    <p>Licence: {session.get('license_key')}</p>
    <a href="/logout">Déconnexion</a>
    """

@app.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    print("🚀 AgriWeb 2.0 - Serveur Commercial Fixé")
    print("=" * 50)
    print("🌐 http://localhost:5000")
    print(f"👥 {len(user_manager.users)} utilisateurs chargés")
    for email in user_manager.users.keys():
        print(f"  📧 {email}")
    print("=" * 50)
    
    app.run(host='127.0.0.1', port=5000, debug=True)
