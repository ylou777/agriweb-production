# -*- coding: utf-8 -*-
"""
Serveur AgriWeb Production avec Authentification Email Réelle
Configuration: ylaurent.perso@gmail.com
"""

from flask import Flask, render_template, request, jsonify, redirect, session, make_response
from auth_system_improved import auth_system, setup_email_config
from auth_routes import auth_bp
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'agriweb-production-secret-2025')

# URL publique de l'app principale (Railway/Prod)
APP_URL = os.getenv('APP_URL', 'https://agriweb-production.up.railway.app')

# MODE PRODUCTION - Envoi réel d'emails
PRODUCTION_MODE = True

# Configuration email production
EMAIL_CONFIG_PROD = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'ylaurent.perso@gmail.com',
    'password': os.getenv('SMTP_PASSWORD', ''),  # À configurer
    'from_name': 'AgriWeb Pro'
}

# Enregistrer le blueprint d'authentification
app.register_blueprint(auth_bp)

@app.route('/')
def index():
    """Page d'accueil production avec authentification email"""
    
    # Vérifier si l'utilisateur est connecté
    session_token = session.get('session_token')
    current_user = None
    is_admin = False
    
    if session_token:
        # TODO: Implémenter get_user_by_session
        pass
    
    return render_template('homepage_new_auth.html', 
                         current_user=current_user,
                         is_admin=is_admin,
                         production_mode=True)

@app.route('/app')
def app_interface():
    """Interface application protégée - Page de succès"""
    session_token = session.get('session_token')
    
    if not session_token:
        return redirect('/?login_required=1')
    
    # Page de succès avec lien vers AgriWeb
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgriWeb Pro - Authentification Réussie</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
        <script>
            // Redirection automatique après 3 secondes
            setTimeout(function() {
                window.location.href = 'http://localhost:5000';
            }, 3000);
        </script>
    </head>
    <body>
        <div class="container-fluid vh-100 d-flex align-items-center justify-content-center" 
             style="background: linear-gradient(135deg, #28a745, #20c997);">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card shadow-lg">
                        <div class="card-body text-center p-5">
                            <h1 class="text-success mb-4">🎉 Authentification Réussie !</h1>
                            <p class="lead">Vous êtes maintenant connecté à <strong>AgriWeb Pro</strong></p>
                            
                            <div class="alert alert-success">
                                <i class="bi bi-check-circle"></i> 
                                <strong>Redirection automatique vers AgriWeb dans 3 secondes...</strong>
                            </div>
                            
                            <div class="mt-4">
                                <a href="{APP_URL}" class="btn btn-success btn-lg me-3">
                                    <i class="bi bi-box-arrow-up-right"></i> Accéder à AgriWeb Maintenant
                                </a>
                                <a href="/logout" class="btn btn-outline-secondary">
                                    <i class="bi bi-box-arrow-right"></i> Déconnexion
                                </a>
                            </div>
                            
                            <div class="mt-4">
                                <small class="text-muted">
                                    Si la redirection ne fonctionne pas, cliquez sur "Accéder à AgriWeb Maintenant"
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/config-status')
def config_status():
    """Vérification de la configuration production"""
    
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    email_configured = bool(smtp_password)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Configuration Production - AgriWeb</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    </head>
    <body class="bg-light">
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h4><i class="bi bi-gear"></i> Configuration Production AgriWeb</h4>
                        </div>
                        <div class="card-body">
                            <h5>📧 Configuration Email</h5>
                            <table class="table">
                                <tr>
                                    <td><strong>Serveur SMTP :</strong></td>
                                    <td>smtp.gmail.com:587</td>
                                    <td><span class="badge bg-success">✅ OK</span></td>
                                </tr>
                                <tr>
                                    <td><strong>Email expéditeur :</strong></td>
                                    <td>ylaurent.perso@gmail.com</td>
                                    <td><span class="badge bg-success">✅ OK</span></td>
                                </tr>
                                <tr>
                                    <td><strong>Mot de passe d'application :</strong></td>
                                    <td>{"Configuré" if email_configured else "⚠️ MANQUANT"}</td>
                                    <td>
                                        <span class="badge bg-{'success' if email_configured else 'warning'}">
                                            {'✅ OK' if email_configured else '⚠️ À configurer'}
                                        </span>
                                    </td>
                                </tr>
                            </table>
                            
                            {'''
                            <div class="alert alert-success">
                                <h6><i class="bi bi-check-circle"></i> Configuration complète !</h6>
                                <p class="mb-0">Le système est prêt à envoyer des emails de confirmation.</p>
                            </div>
                            ''' if email_configured else '''
                            <div class="alert alert-warning">
                                <h6><i class="bi bi-exclamation-triangle"></i> Configuration requise</h6>
                                <p>Pour activer l'envoi d'emails, configurez le mot de passe d'application Gmail :</p>
                                <ol>
                                    <li>Allez sur <a href="https://myaccount.google.com" target="_blank">myaccount.google.com</a></li>
                                    <li>Sécurité → Validation en deux étapes</li>
                                    <li>Mots de passe des applications → Générer</li>
                                    <li>Dans PowerShell : <code>$env:SMTP_PASSWORD="votre_mot_de_passe"</code></li>
                                </ol>
                            </div>
                            '''}
                            
                            <h5 class="mt-4">🔐 Sécurité</h5>
                            <div class="alert alert-info">
                                <ul class="mb-0">
                                    <li><strong>Hachage :</strong> PBKDF2-SHA256 avec 100,000 itérations</li>
                                    <li><strong>Sessions :</strong> Tokens cryptographiques 256-bit</li>
                                    <li><strong>Validation :</strong> Mots de passe forts obligatoires</li>
                                    <li><strong>Emails :</strong> Confirmation obligatoire avant activation</li>
                                </ul>
                            </div>
                            
                            <div class="text-center mt-4">
                                <a href="/" class="btn btn-primary">
                                    <i class="bi bi-house"></i> Retour à l'accueil
                                </a>
                                {"" if not email_configured else '''
                                <a href="/test-email-send" class="btn btn-success ms-2">
                                    <i class="bi bi-envelope"></i> Tester l'envoi d'email
                                </a>
                                '''}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/test-email-send')
def test_email_send():
    """Test d'envoi d'email réel"""
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    
    if not smtp_password:
        return redirect('/config-status')
    
    try:
        # Test d'envoi d'email à vous-même
        from auth_system_improved import auth_system
        
        # Générer un token de test
        import secrets
        test_token = secrets.token_urlsafe(32)
        
        success = auth_system.send_verification_email(
            'ylaurent.perso@gmail.com',
            test_token,
            'Test AgriWeb'
        )
        
        if success:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test Email - AgriWeb</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body class="bg-light">
                <div class="container mt-5">
                    <div class="row justify-content-center">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-body text-center">
                                    <h2 class="text-success mb-4">✅ Email Envoyé !</h2>
                                    <p class="lead">Un email de test a été envoyé à :</p>
                                    <p><strong>ylaurent.perso@gmail.com</strong></p>
                                    <p>Vérifiez votre boîte mail pour confirmer que l'envoi fonctionne.</p>
                                    <a href="/config-status" class="btn btn-primary">
                                        ← Retour à la configuration
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            raise Exception("Échec de l'envoi")
            
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Erreur Email - AgriWeb</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body text-center">
                                <h2 class="text-danger mb-4">❌ Erreur d'envoi</h2>
                                <p class="lead">Impossible d'envoyer l'email de test.</p>
                                <p><strong>Erreur :</strong> {str(e)}</p>
                                <div class="alert alert-warning text-start">
                                    <h6>Vérifications :</h6>
                                    <ul class="mb-0">
                                        <li>Mot de passe d'application Gmail configuré ?</li>
                                        <li>Authentification à 2 facteurs activée ?</li>
                                        <li>Connexion internet stable ?</li>
                                    </ul>
                                </div>
                                <a href="/config-status" class="btn btn-primary">
                                    ← Retour à la configuration
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

@app.route('/logout')
def logout():
    """Déconnexion"""
    session.pop('session_token', None)
    return redirect('/')

if __name__ == '__main__':
    print("🚀 AGRIWEB PRODUCTION - Authentification Email Réelle")
    print("=" * 60)
    print(f"📧 Email configuré : ylaurent.perso@gmail.com")
    
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    if smtp_password:
        print("✅ Mot de passe d'application : Configuré")
        print("✅ Mode production : Emails réels activés")
    else:
        print("⚠️  Mot de passe d'application : MANQUANT")
        print("📋 Configuration requise pour l'envoi d'emails")
    
    print("=" * 60)
    print("🌐 URL principal : http://localhost:5003")
    print("⚙️  Configuration : http://localhost:5003/config-status")
    print("🧪 Test email : http://localhost:5003/test-email-send")
    print("=" * 60)
    
    # Démarrer en mode production
    app.run(host='127.0.0.1', port=5003, debug=False)
