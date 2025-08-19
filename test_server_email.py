#!/usr/bin/env python3
"""
Serveur de test simple pour tester la gestion des emails existants
"""

from flask import Flask, request, jsonify, session, render_template_string
import json
import os
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
app.secret_key = "agriweb_test_key_2025"

# Base de données simple en mémoire pour les tests
users_db = {}
licenses_db = {}

def load_existing_users():
    """Charger les utilisateurs existants s'ils existent"""
    try:
        if os.path.exists('production_users.json'):
            with open('production_users.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

# Charger les utilisateurs existants
users_db = load_existing_users()
print(f"👥 Utilisateurs chargés: {len(users_db)}")
for email in users_db.keys():
    print(f"  📧 {email}")

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Email Existant</title>
        <script>
        async function testEmail() {
            const email = document.getElementById('email').value;
            const name = document.getElementById('name').value;
            
            try {
                const response = await fetch('/api/trial/register', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: email, name: name, company: 'test'})
                });
                
                const result = await response.json();
                document.getElementById('result').innerHTML = JSON.stringify(result, null, 2);
                
                // Si l'utilisateur existe, montrer le bouton de connexion
                if (result.action === 'login') {
                    document.getElementById('result').innerHTML += 
                        '<br><button onclick="loginUser()" style="margin-top:10px; padding:10px; background:blue; color:white;">Se connecter</button>';
                }
                
            } catch (error) {
                document.getElementById('result').innerHTML = 'Erreur: ' + error.message;
            }
        }
        
        async function loginUser() {
            const email = document.getElementById('email').value;
            
            try {
                const response = await fetch('/api/user/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: email})
                });
                
                const result = await response.json();
                document.getElementById('result').innerHTML += '<br>Connexion: ' + JSON.stringify(result, null, 2);
                
            } catch (error) {
                document.getElementById('result').innerHTML += '<br>Erreur connexion: ' + error.message;
            }
        }
        </script>
    </head>
    <body>
        <h1>Test Gestion Email Existant</h1>
        <div>
            <label>Email:</label><br>
            <input type="email" id="email" value="ylaurent.perso@gmail.com" style="width:300px;"><br><br>
            
            <label>Nom:</label><br>
            <input type="text" id="name" value="Laurent" style="width:300px;"><br><br>
            
            <button onclick="testEmail()" style="padding:10px; background:green; color:white;">Tester Inscription</button>
        </div>
        
        <h3>Résultat:</h3>
        <pre id="result" style="background:#f0f0f0; padding:10px; border:1px solid #ccc;"></pre>
    </body>
    </html>
    """

@app.route('/api/trial/register', methods=['POST'])
def register_trial():
    """Test d'inscription avec gestion des emails existants"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        name = data.get('name', '').strip()
        company = data.get('company', '').strip()
        
        print(f"📝 Tentative d'inscription: {email}")
        
        if not email or not name:
            return jsonify({"success": False, "error": "Email et nom requis"}), 400
        
        # Vérifier si l'utilisateur existe déjà
        if email in users_db:
            existing_user = users_db[email]
            print(f"👤 Utilisateur existant trouvé: {email}")
            
            # Vérifier la date d'expiration
            try:
                expires = datetime.fromisoformat(existing_user['expires'])
                print(f"📅 Expiration: {expires}")
                
                if datetime.now() < expires:
                    # Essai encore valide
                    return jsonify({
                        "success": False, 
                        "error": "Cet email est déjà utilisé", 
                        "action": "login",
                        "message": f"Vous avez déjà un essai actif jusqu'au {expires.strftime('%d/%m/%Y')}. Connectez-vous.",
                        "debug": "Essai actif"
                    }), 400
                else:
                    # Essai expiré
                    return jsonify({
                        "success": False, 
                        "error": "Cet email est déjà utilisé", 
                        "action": "expired",
                        "message": "Votre essai gratuit a expiré. Contactez-nous pour une licence payante.",
                        "debug": "Essai expiré"
                    }), 400
            except Exception as e:
                print(f"❌ Erreur lors de la vérification de la date: {e}")
                return jsonify({
                    "success": False, 
                    "error": "Erreur de données", 
                    "debug": str(e)
                }), 400
        
        # Nouvel utilisateur - créer l'essai
        print(f"✅ Nouveau utilisateur: {email}")
        user_id = str(uuid.uuid4())
        license_key = f"TRIAL-{user_id[:8]}"
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
            "searches_limit": 100
        }
        
        # Ajouter à la base de données
        users_db[email] = user_data
        
        return jsonify({
            "success": True,
            "message": f"Essai gratuit activé pour {name}",
            "user": user_data,
            "license_key": license_key,
            "debug": "Nouveau compte créé"
        })
        
    except Exception as e:
        print(f"❌ Erreur inscription: {e}")
        return jsonify({"success": False, "error": "Erreur serveur", "debug": str(e)}), 500

@app.route('/api/user/login', methods=['POST'])
def login_user():
    """Test de connexion utilisateur existant"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        print(f"🔑 Tentative de connexion: {email}")
        
        if email not in users_db:
            return jsonify({
                "success": False, 
                "error": "Email non trouvé",
                "debug": f"Email {email} pas dans la base"
            }), 400
        
        user = users_db[email]
        
        # Vérifier si non expiré
        expires = datetime.fromisoformat(user['expires'])
        if datetime.now() > expires:
            return jsonify({
                "success": False, 
                "error": f"Votre accès a expiré le {expires.strftime('%d/%m/%Y')}. Contactez-nous pour renouveler.",
                "debug": "Compte expiré"
            }), 400
        
        # Connexion réussie
        session['authenticated'] = True
        session['user_email'] = email
        session['user_data'] = user
        
        return jsonify({
            "success": True,
            "message": f"Connexion réussie ! Bienvenue {user['name']}",
            "user": user,
            "debug": "Connexion OK"
        })
        
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return jsonify({"success": False, "error": "Erreur serveur", "debug": str(e)}), 500

if __name__ == '__main__':
    print("🧪 Serveur de test - Gestion des emails existants")
    print("🌐 http://localhost:5555")
    print("=" * 50)
    app.run(host='127.0.0.1', port=5555, debug=True)
