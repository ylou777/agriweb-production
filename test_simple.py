#!/usr/bin/env python3
"""
Test page simple pour vérifier la gestion des emails existants
"""

from flask import Flask, request, jsonify, render_template_string
import json
import os
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)

# Charger directement la base de données
def load_users():
    try:
        if os.path.exists('production_users.json'):
            with open('production_users.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

users_db = load_users()
print(f"👥 Utilisateurs chargés: {len(users_db)}")
for email in users_db.keys():
    print(f"  📧 {email}")

# Page de test ultra-simple
TEST_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Test Email Existant - CACHE BUST</title>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <style>
        body { font-family: Arial; padding: 20px; background: #f0f0f0; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        input, button { padding: 10px; margin: 5px; font-size: 16px; }
        input { width: 100%; }
        button { background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #0056b3; }
        #result { margin-top: 20px; padding: 15px; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .btn-login { background: #28a745; margin-top: 10px; }
        .btn-contact { background: #ffc107; color: #212529; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Test Email Existant</h1>
        <p><strong>Timestamp:</strong> {{ timestamp }}</p>
        <p><strong>Cache Bust:</strong> {{ cache_bust }}</p>
        
        <div>
            <label>Email:</label>
            <input type="email" id="email" value="ylaurent.perso@gmail.com">
            
            <label>Nom:</label>
            <input type="text" id="name" value="Laurent">
            
            <label>Entreprise:</label>
            <input type="text" id="company" value="lumicasol">
            
            <button onclick="testInscription()">🧪 Tester Inscription</button>
            <button onclick="clearResult()">🗑️ Effacer</button>
        </div>
        
        <div id="result"></div>
    </div>
    
    <script>
        async function testInscription() {
            const email = document.getElementById('email').value;
            const name = document.getElementById('name').value;
            const company = document.getElementById('company').value;
            
            console.log('Test inscription avec:', {email, name, company});
            
            try {
                const response = await fetch('/api/test/register?' + new Date().getTime(), {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: email, name: name, company: company})
                });
                
                console.log('Status:', response.status);
                const result = await response.json();
                console.log('Résultat:', result);
                
                let html = '<h3>Résultat:</h3><pre>' + JSON.stringify(result, null, 2) + '</pre>';
                let cssClass = 'error';
                
                if (result.success) {
                    cssClass = 'success';
                    html += '<p>✅ Inscription réussie!</p>';
                } else {
                    if (result.action === 'login') {
                        cssClass = 'warning';
                        html += '<button class="btn-login" onclick="testConnexion()">🔑 Se connecter</button>';
                    } else if (result.action === 'expired') {
                        cssClass = 'warning';
                        html += '<button class="btn-contact" onclick="contactUs()">💰 Contacter pour licence</button>';
                    }
                }
                
                document.getElementById('result').innerHTML = html;
                document.getElementById('result').className = cssClass;
                
            } catch (error) {
                console.error('Erreur:', error);
                document.getElementById('result').innerHTML = '<h3>Erreur:</h3><p>' + error.message + '</p>';
                document.getElementById('result').className = 'error';
            }
        }
        
        async function testConnexion() {
            const email = document.getElementById('email').value;
            
            try {
                const response = await fetch('/api/test/login?' + new Date().getTime(), {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: email})
                });
                
                const result = await response.json();
                console.log('Connexion:', result);
                
                let html = '<h3>Connexion:</h3><pre>' + JSON.stringify(result, null, 2) + '</pre>';
                document.getElementById('result').innerHTML += html;
                
                if (result.success) {
                    document.getElementById('result').innerHTML += '<p>✅ Connexion réussie! Redirection...</p>';
                    setTimeout(() => window.location.href = '/success', 2000);
                }
                
            } catch (error) {
                console.error('Erreur connexion:', error);
            }
        }
        
        function contactUs() {
            alert('📧 Contact: contact@agriweb.fr\\n📞 Tél: 01.23.45.67.89');
        }
        
        function clearResult() {
            document.getElementById('result').innerHTML = '';
            document.getElementById('result').className = '';
        }
    </script>
</body>
</html>
'''

@app.route('/')
def test_page():
    return render_template_string(TEST_PAGE, 
        timestamp=datetime.now().strftime('%H:%M:%S'),
        cache_bust=str(uuid.uuid4())[:8]
    )

@app.route('/api/test/register', methods=['POST'])
def test_register():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        name = data.get('name', '').strip()
        company = data.get('company', '').strip()
        
        print(f"📝 Test inscription: {email}")
        
        if not email or not name:
            return jsonify({"success": False, "error": "Email et nom requis"}), 400
        
        # Vérifier si l'utilisateur existe
        if email in users_db:
            existing_user = users_db[email]
            print(f"👤 Utilisateur existant: {email}")
            
            try:
                expires = datetime.fromisoformat(existing_user['expires'])
                print(f"📅 Expire le: {expires}")
                
                if datetime.now() < expires:
                    return jsonify({
                        "success": False,
                        "error": "Cet email est déjà utilisé",
                        "action": "login",
                        "message": f"Essai actif jusqu'au {expires.strftime('%d/%m/%Y')}. Connectez-vous.",
                        "debug": "Essai actif détecté"
                    }), 400
                else:
                    return jsonify({
                        "success": False,
                        "error": "Cet email est déjà utilisé",
                        "action": "expired", 
                        "message": "Essai expiré. Contactez-nous pour une licence payante.",
                        "debug": "Essai expiré détecté"
                    }), 400
            except Exception as e:
                print(f"❌ Erreur date: {e}")
                return jsonify({"success": False, "error": "Erreur de données", "debug": str(e)}), 400
        
        # Nouvel utilisateur
        print(f"✅ Nouveau: {email}")
        return jsonify({
            "success": True,
            "message": f"Nouvel utilisateur {name} créé avec succès",
            "debug": "Nouveau compte"
        })
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({"success": False, "error": "Erreur serveur", "debug": str(e)}), 500

@app.route('/api/test/login', methods=['POST'])
def test_login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        print(f"🔑 Test connexion: {email}")
        
        if email not in users_db:
            return jsonify({"success": False, "error": "Email non trouvé"}), 400
        
        user = users_db[email]
        expires = datetime.fromisoformat(user['expires'])
        
        if datetime.now() > expires:
            return jsonify({"success": False, "error": "Compte expiré"}), 400
        
        return jsonify({
            "success": True,
            "message": f"Connexion réussie pour {user['name']}",
            "user": user
        })
        
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/success')
def success():
    return "<h1>✅ Test réussi!</h1><p>La logique fonctionne correctement.</p><a href='/'>Retour</a>"

if __name__ == '__main__':
    print("🧪 Serveur de test simplifié")
    print("🌐 http://localhost:5555")
    app.run(host='127.0.0.1', port=5555, debug=True)
