#!/usr/bin/env python3
"""
🔐 SYSTÈME D'AUTHENTIFICATION SIMPLE pour AgriWeb 2.0
Ajoute une page de connexion basique à votre application existante
"""

from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import datetime, timedelta
import json
import os

# Base de données simple des utilisateurs (fichier JSON)
USERS_FILE = "users_agriweb.json"

def load_users():
    """Charger les utilisateurs depuis le fichier"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users_db):
    """Sauvegarder les utilisateurs dans le fichier"""
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_db, f, indent=2, ensure_ascii=False, default=str)
        return True
    except Exception as e:
        print(f"Erreur sauvegarde: {e}")
        return False

def add_auth_to_app(app):
    """Ajoute l'authentification à une application Flask existante"""
    
    app.secret_key = 'agriweb-auth-2025'
    
    @app.route('/auth')
    def auth_page():
        """Page d'authentification simple"""
        return render_template_string(AUTH_TEMPLATE)
    
    @app.route('/api/auth/login', methods=['POST'])
    def auth_login():
        """Connexion utilisateur"""
        try:
            data = request.get_json()
            email = data.get('email', '').strip().lower()
            
            if not email:
                return jsonify({"success": False, "error": "Email requis"}), 400
            
            users_db = load_users()
            
            if email in users_db:
                user = users_db[email]
                # Vérifier si non expiré
                expires = datetime.fromisoformat(user['expires'])
                if datetime.now() > expires:
                    return jsonify({
                        "success": False, 
                        "error": f"Accès expiré le {expires.strftime('%d/%m/%Y')}"
                    }), 403
                
                # Connecter
                session['authenticated'] = True
                session['user_email'] = email
                session['user_name'] = user['name']
                session['expires'] = user['expires']
                
                return jsonify({
                    "success": True,
                    "message": f"Connexion réussie ! Bienvenue {user['name']}",
                    "user": {
                        "name": user['name'],
                        "email": email,
                        "expires": expires.strftime('%d/%m/%Y')
                    }
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Email non trouvé. Contactez-nous pour créer un compte."
                }), 404
                
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/api/auth/register', methods=['POST'])
    def auth_register():
        """Inscription d'un nouvel utilisateur"""
        try:
            data = request.get_json()
            email = data.get('email', '').strip().lower()
            name = data.get('name', '').strip()
            company = data.get('company', '').strip()
            
            if not email or not name:
                return jsonify({"success": False, "error": "Email et nom requis"}), 400
            
            users_db = load_users()
            
            if email in users_db:
                return jsonify({
                    "success": False,
                    "error": "Cet email est déjà enregistré. Utilisez la connexion."
                }), 400
            
            # Créer nouvel utilisateur avec 7 jours d'accès
            expires = datetime.now() + timedelta(days=7)
            user_data = {
                "name": name,
                "email": email,
                "company": company,
                "created": datetime.now().isoformat(),
                "expires": expires.isoformat(),
                "searches": 0
            }
            
            users_db[email] = user_data
            
            if save_users(users_db):
                # Connecter automatiquement
                session['authenticated'] = True
                session['user_email'] = email
                session['user_name'] = name
                session['expires'] = expires.isoformat()
                
                return jsonify({
                    "success": True,
                    "message": f"Compte créé avec succès ! Accès valable jusqu'au {expires.strftime('%d/%m/%Y')}",
                    "user": {
                        "name": name,
                        "email": email,
                        "company": company,
                        "expires": expires.strftime('%d/%m/%Y')
                    }
                })
            else:
                return jsonify({"success": False, "error": "Erreur de sauvegarde"}), 500
                
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/api/auth/logout', methods=['POST'])
    def auth_logout():
        """Déconnexion"""
        session.clear()
        return jsonify({"success": True, "message": "Déconnexion réussie"})
    
    @app.route('/api/auth/status')
    def auth_status():
        """Statut de connexion"""
        if session.get('authenticated'):
            return jsonify({
                "authenticated": True,
                "user": {
                    "name": session.get('user_name'),
                    "email": session.get('user_email'),
                    "expires": session.get('expires')
                }
            })
        else:
            return jsonify({"authenticated": False})
    
    # Intercepter la page d'accueil pour vérifier l'authentification
    original_index = app.view_functions.get('index')
    
    @app.route('/')
    def protected_index():
        """Page d'accueil avec vérification d'authentification"""
        if not session.get('authenticated'):
            return redirect('/auth')
        
        # Si authentifié, afficher l'interface avec informations utilisateur
        if original_index:
            # Modifier la réponse pour inclure les infos utilisateur
            response = original_index()
            if isinstance(response, str):
                # Injecter les infos utilisateur dans le HTML
                user_info = f"""
                <div style="position: fixed; top: 10px; right: 10px; background: #28a745; color: white; padding: 10px; border-radius: 5px; z-index: 1000;">
                    ✅ Connecté: {session.get('user_name')} | 
                    <a href="/auth" style="color: white;">Gérer le compte</a>
                </div>
                """
                if "<body>" in response:
                    response = response.replace("<body>", f"<body>{user_info}")
            return response
        else:
            return "Application AgriWeb chargée !"

# Template HTML pour la page d'authentification
AUTH_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgriWeb 2.0 - Connexion</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .auth-container { 
            background: white; 
            padding: 40px; 
            border-radius: 10px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 400px;
        }
        
        .auth-header { text-align: center; margin-bottom: 30px; }
        .auth-header h1 { color: #2c5f41; margin-bottom: 10px; }
        .auth-header p { color: #666; }
        
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 600; color: #2c5f41; }
        .form-group input { 
            width: 100%; 
            padding: 12px; 
            border: 2px solid #e9ecef; 
            border-radius: 6px; 
            font-size: 16px;
        }
        .form-group input:focus { outline: none; border-color: #28a745; }
        
        .btn { 
            width: 100%; 
            padding: 12px; 
            border: none; 
            border-radius: 6px; 
            font-size: 16px; 
            font-weight: 600; 
            cursor: pointer; 
            margin-bottom: 10px;
            transition: all 0.3s ease;
        }
        .btn-primary { background: #28a745; color: white; }
        .btn-primary:hover { background: #218838; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn-secondary:hover { background: #545b62; }
        
        .alert { 
            padding: 12px; 
            margin-bottom: 20px; 
            border-radius: 6px; 
            text-align: center;
        }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        
        .toggle-link { 
            text-align: center; 
            margin-top: 20px; 
        }
        .toggle-link a { 
            color: #28a745; 
            text-decoration: none; 
            font-weight: 600;
        }
        .toggle-link a:hover { text-decoration: underline; }
        
        .user-info {
            background: #d4edda;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="auth-container">
        <div class="auth-header">
            <h1>🌾 AgriWeb 2.0</h1>
            <p>Géolocalisation Agricole Professionnelle</p>
        </div>
        
        <!-- Zone d'information utilisateur connecté -->
        <div id="user-info" class="user-info hidden">
            <h3>✅ Connecté</h3>
            <p><strong>Nom:</strong> <span id="user-name"></span></p>
            <p><strong>Email:</strong> <span id="user-email"></span></p>
            <p><strong>Accès jusqu'au:</strong> <span id="user-expires"></span></p>
            <button class="btn btn-primary" onclick="goToApp()">🚀 Accéder à AgriWeb</button>
            <button class="btn btn-secondary" onclick="logout()">Se Déconnecter</button>
        </div>
        
        <!-- Formulaire de connexion -->
        <div id="login-form">
            <div id="alert-zone"></div>
            
            <div id="login-section">
                <h3>🔐 Se Connecter</h3>
                <div class="form-group">
                    <label for="login-email">Email</label>
                    <input type="email" id="login-email" placeholder="votre.email@entreprise.com" required>
                </div>
                <button class="btn btn-primary" onclick="login()">Se Connecter</button>
                <div class="toggle-link">
                    <a href="#" onclick="showRegister()">Créer un compte (essai 7 jours gratuit)</a>
                </div>
            </div>
            
            <div id="register-section" class="hidden">
                <h3>🆓 Créer un Compte</h3>
                <div class="form-group">
                    <label for="register-name">Nom complet</label>
                    <input type="text" id="register-name" placeholder="Prénom Nom" required>
                </div>
                <div class="form-group">
                    <label for="register-email">Email</label>
                    <input type="email" id="register-email" placeholder="votre.email@entreprise.com" required>
                </div>
                <div class="form-group">
                    <label for="register-company">Entreprise</label>
                    <input type="text" id="register-company" placeholder="Nom de votre entreprise">
                </div>
                <button class="btn btn-primary" onclick="register()">Créer le Compte (7 jours gratuit)</button>
                <div class="toggle-link">
                    <a href="#" onclick="showLogin()">J'ai déjà un compte</a>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Vérifier si déjà connecté au chargement
        window.onload = function() {
            checkAuthStatus();
        }
        
        async function checkAuthStatus() {
            try {
                const response = await fetch('/api/auth/status');
                const result = await response.json();
                
                if (result.authenticated) {
                    showUserInfo(result.user);
                }
            } catch (error) {
                console.error('Erreur vérification auth:', error);
            }
        }
        
        function showUserInfo(user) {
            document.getElementById('user-name').textContent = user.name;
            document.getElementById('user-email').textContent = user.email;
            
            // Formater la date d'expiration
            const expires = new Date(user.expires);
            document.getElementById('user-expires').textContent = expires.toLocaleDateString('fr-FR');
            
            document.getElementById('user-info').classList.remove('hidden');
            document.getElementById('login-form').classList.add('hidden');
        }
        
        function showAlert(message, type = 'error') {
            const alertZone = document.getElementById('alert-zone');
            alertZone.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
        }
        
        function showLogin() {
            document.getElementById('login-section').classList.remove('hidden');
            document.getElementById('register-section').classList.add('hidden');
            document.getElementById('alert-zone').innerHTML = '';
        }
        
        function showRegister() {
            document.getElementById('login-section').classList.add('hidden');
            document.getElementById('register-section').classList.remove('hidden');
            document.getElementById('alert-zone').innerHTML = '';
        }
        
        async function login() {
            const email = document.getElementById('login-email').value.trim();
            
            if (!email) {
                showAlert('Veuillez saisir votre email');
                return;
            }
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: email})
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert(result.message, 'success');
                    setTimeout(() => {
                        showUserInfo(result.user);
                    }, 1000);
                } else {
                    showAlert(result.error);
                }
            } catch (error) {
                showAlert('Erreur de connexion: ' + error.message);
            }
        }
        
        async function register() {
            const name = document.getElementById('register-name').value.trim();
            const email = document.getElementById('register-email').value.trim();
            const company = document.getElementById('register-company').value.trim();
            
            if (!name || !email) {
                showAlert('Nom et email requis');
                return;
            }
            
            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        name: name,
                        email: email,
                        company: company
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert(result.message, 'success');
                    setTimeout(() => {
                        showUserInfo(result.user);
                    }, 1000);
                } else {
                    showAlert(result.error);
                }
            } catch (error) {
                showAlert('Erreur d\\'inscription: ' + error.message);
            }
        }
        
        async function logout() {
            try {
                const response = await fetch('/api/auth/logout', {
                    method: 'POST'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('user-info').classList.add('hidden');
                    document.getElementById('login-form').classList.remove('hidden');
                    showLogin();
                    showAlert(result.message, 'success');
                }
            } catch (error) {
                showAlert('Erreur de déconnexion: ' + error.message);
            }
        }
        
        function goToApp() {
            window.location.href = '/';
        }
    </script>
</body>
</html>
'''
