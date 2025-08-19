#!/usr/bin/env python3
"""
🚀 SERVEUR SIMPLE AGRIWEB 2.0 - INSCRIPTION FONCTIONNELLE
Test direct du système d'inscription
"""

from flask import Flask, request, jsonify, session, render_template_string
from production_system import LicenseManager
import os

app = Flask(__name__)
app.secret_key = "test-secret-for-agriweb-2025"

# Template HTML complet avec JavaScript fonctionnel
LANDING_PAGE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgriWeb 2.0 - Essai Gratuit</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .hero { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            min-height: 100vh; 
            display: flex; 
            align-items: center; 
        }
        .trial-card { 
            background: rgba(255,255,255,0.95); 
            border-radius: 15px; 
            padding: 2rem; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .btn-trial {
            background: linear-gradient(45deg, #28a745, #20c997);
            border: none;
            font-weight: bold;
            transition: all 0.3s;
        }
        .btn-trial:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
    </style>
</head>
<body>
    <div class="hero">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="trial-card text-dark">
                        <div class="text-center mb-4">
                            <h1 class="mb-3">🚀 AgriWeb 2.0</h1>
                            <h3 class="text-primary">Essai gratuit 7 jours</h3>
                            <p class="text-muted">Solution professionnelle d'analyse agricole et foncière</p>
                        </div>
                        
                        <form id="trialForm" class="mt-4">
                            <div class="mb-3">
                                <label for="email" class="form-label fw-bold">📧 Email professionnel</label>
                                <input type="email" class="form-control form-control-lg" id="email" required
                                       placeholder="votre.email@entreprise.com">
                            </div>
                            <div class="mb-3">
                                <label for="company" class="form-label fw-bold">🏢 Entreprise</label>
                                <input type="text" class="form-control form-control-lg" id="company"
                                       placeholder="Nom de votre entreprise">
                            </div>
                            <button type="submit" class="btn btn-trial btn-lg w-100 text-white" id="submitBtn">
                                ✨ Démarrer l'essai gratuit
                            </button>
                        </form>
                        
                        <div class="mt-4 text-center">
                            <div class="row">
                                <div class="col-4">
                                    <small class="text-success">✅<br>Aucune carte<br>bancaire</small>
                                </div>
                                <div class="col-4">
                                    <small class="text-success">✅<br>Accès<br>immédiat</small>
                                </div>
                                <div class="col-4">
                                    <small class="text-success">✅<br>Support<br>inclus</small>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Zone de résultat -->
                        <div id="result" class="mt-3"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('trialForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = document.getElementById('submitBtn');
            const resultDiv = document.getElementById('result');
            const email = document.getElementById('email').value.trim();
            const company = document.getElementById('company').value.trim();
            
            // Validation
            if (!email) {
                resultDiv.innerHTML = `
                    <div class="alert alert-warning">
                        ⚠️ Veuillez saisir votre email professionnel
                    </div>
                `;
                return;
            }
            
            // UI feedback
            submitBtn.disabled = true;
            submitBtn.innerHTML = '⏳ Activation en cours...';
            resultDiv.innerHTML = '';
            
            try {
                console.log('Envoi de la requête:', { email, company });
                
                const response = await fetch('/api/trial/start', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        email: email, 
                        company: company || 'Non spécifiée'
                    })
                });
                
                console.log('Statut de la réponse:', response.status);
                
                if (!response.ok) {
                    throw new Error(`Erreur HTTP ${response.status}: ${response.statusText}`);
                }
                
                const result = await response.json();
                console.log('Résultat:', result);
                
                if (result.success) {
                    resultDiv.innerHTML = `
                        <div class="alert alert-success">
                            <h5>🎉 Félicitations !</h5>
                            <p><strong>Votre essai gratuit de 7 jours est activé !</strong></p>
                            <p>📄 Licence: <code>${result.license_key}</code></p>
                            <div class="d-grid mt-3">
                                <button class="btn btn-success btn-lg" onclick="window.location.href='/'">
                                    🚀 Accéder à AgriWeb 2.0
                                </button>
                            </div>
                        </div>
                    `;
                    
                    // Auto-redirection après 3 secondes
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 3000);
                    
                } else {
                    throw new Error(result.error || 'Erreur inconnue');
                }
                
            } catch (error) {
                console.error('Erreur:', error);
                resultDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <h5>❌ Erreur</h5>
                        <p><strong>Impossible d'activer l'essai:</strong> ${error.message}</p>
                        <small>Vérifiez votre connexion et réessayez.</small>
                        <div class="mt-2">
                            <button class="btn btn-outline-danger btn-sm" onclick="location.reload()">
                                🔄 Réessayer
                            </button>
                        </div>
                    </div>
                `;
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '✨ Démarrer l\\'essai gratuit';
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    """Page d'accueil avec statut de licence"""
    license_key = session.get('license_key')
    trial_user = session.get('trial_user', False)
    
    if license_key and trial_user:
        return f'''
        <div style="font-family: Arial; max-width: 800px; margin: 50px auto; padding: 30px; background: #f8f9fa; border-radius: 15px;">
            <h1>🎉 Bienvenue dans AgriWeb 2.0 !</h1>
            
            <div style="background: #d4edda; padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid #c3e6cb;">
                <h3>✅ Essai gratuit actif</h3>
                <p><strong>📄 Licence:</strong> <code>{license_key}</code></p>
                <p><strong>📧 Email:</strong> {session.get('email', 'Non spécifié')}</p>
                <p><strong>⏰ Statut:</strong> 7 jours d'essai gratuit</p>
            </div>
            
            <h3>🛠️ Fonctionnalités disponibles :</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0;">
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">
                    <h5>📊 Rapports</h5>
                    <p>Génération de rapports départementaux</p>
                    <small class="text-success">✅ Disponible</small>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">
                    <h5>🗺️ Cartes</h5>
                    <p>Cartes interactives et analyses</p>
                    <small class="text-success">✅ Disponible</small>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">
                    <h5>📋 Export</h5>
                    <p>Export de données en PDF</p>
                    <small class="text-warning">⚠️ Limité (essai)</small>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">
                    <h5>🔧 API</h5>
                    <p>Accès API pour intégrations</p>
                    <small class="text-danger">❌ Non disponible (essai)</small>
                </div>
            </div>
            
            <div style="margin: 30px 0; text-align: center;">
                <a href="/pricing" style="background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                    💳 Voir les tarifs complets
                </a>
                <a href="/landing" style="background: #6c757d; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; margin-left: 10px;">
                    👤 Nouvel essai
                </a>
            </div>
            
            <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border: 1px solid #ffeaa7;">
                <strong>🚀 Prêt pour la production ?</strong><br>
                Votre système AgriWeb 2.0 est maintenant opérationnel !<br>
                L'inscription fonctionne parfaitement et vous pouvez commencer la commercialisation.
            </div>
        </div>
        '''
    else:
        return '<script>window.location="/landing"</script>'

@app.route('/landing')
def landing():
    """Page d'inscription à l'essai gratuit"""
    return LANDING_PAGE

@app.route('/api/trial/start', methods=['POST'])
def start_trial():
    """API d'activation d'essai gratuit"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "Données manquantes"}), 400
        
        email = data.get('email', '').strip()
        company = data.get('company', '').strip()
        
        if not email:
            return jsonify({"success": False, "error": "Email requis"}), 400
        
        # Créer la licence d'essai
        license_manager = LicenseManager()
        license_info = license_manager.create_trial_license(email, company)
        
        # Stocker en session
        session['license_key'] = license_info['license_key']
        session['trial_user'] = True
        session['email'] = email
        session['company'] = company
        
        print(f"✅ Licence créée: {license_info['license_key']} pour {email}")
        
        return jsonify({
            "success": True,
            "license_key": license_info['license_key'],
            "message": f"Essai gratuit activé pour {email} !",
            "redirect_url": "/"
        })
        
    except Exception as e:
        print(f"❌ Erreur API: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/pricing')
def pricing():
    """Page de tarification"""
    return '''
    <div style="font-family: Arial; max-width: 1000px; margin: 50px auto; padding: 20px;">
        <h1>💳 Tarification AgriWeb 2.0</h1>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin: 30px 0;">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #dee2e6;">
                <h3>💼 Basic</h3>
                <div style="font-size: 2em; font-weight: bold; color: #28a745;">299€</div>
                <div style="color: #6c757d;">par an</div>
                <ul style="text-align: left; margin: 20px 0;">
                    <li>100 communes max</li>
                    <li>500 rapports/jour</li>
                    <li>Cartes interactives</li>
                    <li>Export PDF</li>
                    <li>Support email</li>
                </ul>
                <button style="background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; width: 100%;">
                    Choisir Basic
                </button>
            </div>
            
            <div style="background: #007bff; color: white; padding: 20px; border-radius: 10px; text-align: center; transform: scale(1.05);">
                <h3>🚀 Pro</h3>
                <div style="font-size: 2em; font-weight: bold;">999€</div>
                <div style="opacity: 0.8;">par an</div>
                <ul style="text-align: left; margin: 20px 0;">
                    <li>1000 communes max</li>
                    <li>Rapports illimités</li>
                    <li>API complète</li>
                    <li>Export tous formats</li>
                    <li>Support prioritaire</li>
                </ul>
                <button style="background: white; color: #007bff; border: none; padding: 10px 20px; border-radius: 5px; width: 100%; font-weight: bold;">
                    Choisir Pro ⭐
                </button>
            </div>
            
            <div style="background: #6f42c1; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                <h3>🏢 Enterprise</h3>
                <div style="font-size: 2em; font-weight: bold;">2999€</div>
                <div style="opacity: 0.8;">par an</div>
                <ul style="text-align: left; margin: 20px 0;">
                    <li>Communes illimitées</li>
                    <li>GeoServer dédié</li>
                    <li>Personnalisation</li>
                    <li>Formation incluse</li>
                    <li>Support 24/7</li>
                </ul>
                <button style="background: white; color: #6f42c1; border: none; padding: 10px 20px; border-radius: 5px; width: 100%; font-weight: bold;">
                    Nous contacter
                </button>
            </div>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="/landing" style="background: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">
                🆓 Commencer par l'essai gratuit
            </a>
        </div>
    </div>
    '''

if __name__ == "__main__":
    print("🚀 AgriWeb 2.0 - Serveur d'inscription")
    print("📱 URLs disponibles:")
    print("   🏠 Accueil: http://localhost:5000/")
    print("   🆓 Essai gratuit: http://localhost:5000/landing")
    print("   💳 Tarifs: http://localhost:5000/pricing")
    print("   🔧 API: http://localhost:5000/api/trial/start")
    print("\n✨ Testez l'inscription sur /landing")
    
    app.run(host="127.0.0.1", port=5000, debug=True)
