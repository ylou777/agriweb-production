# -*- coding: utf-8 -*-
"""
Routes d'authentification améliorées avec confirmation email
AgriWeb 2025
"""

from flask import Blueprint, request, jsonify, render_template_string, redirect, session, make_response
from auth_system_improved import auth_system
import os

# Blueprint pour les routes d'authentification
auth_bp = Blueprint('auth', __name__)

# ── Shared CSS base (dark theme aligned with homepage charte graphique) ──
AUTH_BASE_CSS = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        background: #0a0e27;
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #e8eaed;
        overflow: hidden;
        position: relative;
    }
    /* Animated gradient background */
    body::before {
        content: '';
        position: fixed;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: radial-gradient(ellipse at 20% 50%, rgba(255,183,0,0.06) 0%, transparent 50%),
                    radial-gradient(ellipse at 80% 20%, rgba(102,126,234,0.06) 0%, transparent 50%),
                    radial-gradient(ellipse at 50% 80%, rgba(118,75,162,0.04) 0%, transparent 50%);
        animation: bgDrift 20s ease-in-out infinite;
        z-index: 0;
    }
    @keyframes bgDrift {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        33% { transform: translate(2%, -1%) rotate(1deg); }
        66% { transform: translate(-1%, 1%) rotate(-0.5deg); }
    }
    /* Floating particles */
    .particles { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
    .particle {
        position: absolute;
        width: 3px; height: 3px;
        background: rgba(255,183,0,0.3);
        border-radius: 50%;
        animation: particleFloat 15s infinite linear;
    }
    .particle:nth-child(2) { width: 2px; height: 2px; left: 20%; animation-delay: -3s; animation-duration: 18s; background: rgba(102,126,234,0.25); }
    .particle:nth-child(3) { left: 40%; animation-delay: -7s; animation-duration: 22s; }
    .particle:nth-child(4) { width: 2px; height: 2px; left: 60%; animation-delay: -11s; animation-duration: 16s; background: rgba(118,75,162,0.25); }
    .particle:nth-child(5) { left: 80%; animation-delay: -5s; animation-duration: 20s; }
    .particle:nth-child(6) { left: 10%; animation-delay: -9s; animation-duration: 25s; background: rgba(255,183,0,0.15); }
    @keyframes particleFloat {
        0% { transform: translateY(100vh) scale(0); opacity: 0; }
        10% { opacity: 1; }
        90% { opacity: 1; }
        100% { transform: translateY(-20vh) scale(1.5); opacity: 0; }
    }
    /* Auth card - glassmorphism */
    .auth-card {
        position: relative; z-index: 1;
        background: rgba(26, 31, 58, 0.7);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border: 1px solid rgba(255, 183, 0, 0.12);
        border-radius: 24px;
        padding: 2.8rem 2.4rem;
        max-width: 460px;
        width: 92%;
        box-shadow: 0 24px 64px rgba(0, 0, 0, 0.4),
                    inset 0 1px 0 rgba(255, 255, 255, 0.04);
        animation: cardAppear 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        opacity: 0;
        transform: translateY(20px);
    }
    .auth-card.wide { max-width: 500px; }
    @keyframes cardAppear {
        to { opacity: 1; transform: translateY(0); }
    }
    /* Brand */
    .auth-brand {
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 0.3rem;
    }
    .auth-brand .gold {
        background: linear-gradient(135deg, #FFB700, #FFA000);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .auth-subtitle {
        color: #9ba1b0;
        font-size: 0.88rem;
        font-weight: 400;
    }
    .auth-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 52px; height: 52px;
        border-radius: 16px;
        background: linear-gradient(135deg, rgba(255,183,0,0.15), rgba(255,140,0,0.08));
        border: 1px solid rgba(255,183,0,0.2);
        margin-bottom: 1rem;
        font-size: 1.4rem;
        color: #FFB700;
    }
    /* Form elements */
    .form-label {
        font-size: 0.82rem;
        font-weight: 500;
        color: #9ba1b0;
        margin-bottom: 0.35rem;
        letter-spacing: 0.02em;
    }
    .form-control {
        background: rgba(15, 17, 23, 0.6);
        border: 1px solid rgba(42, 45, 58, 0.8);
        border-radius: 12px;
        color: #e8eaed;
        padding: 0.7rem 1rem;
        font-size: 0.92rem;
        font-family: inherit;
        transition: all 0.25s ease;
    }
    .form-control::placeholder { color: #6b7185; }
    .form-control:focus {
        background: rgba(15, 17, 23, 0.8);
        border-color: #FFB700;
        box-shadow: 0 0 0 3px rgba(255,183,0,0.1);
        color: #e8eaed;
        outline: none;
    }
    .form-text { color: #6b7185; font-size: 0.78rem; }
    /* Primary button */
    .btn-agri {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        width: 100%;
        padding: 0.78rem 1.5rem;
        background: linear-gradient(135deg, #FFB700, #FF8C00);
        color: #0a0e27;
        border: none;
        border-radius: 12px;
        font-size: 0.95rem;
        font-weight: 700;
        font-family: inherit;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
        text-decoration: none;
        box-shadow: 0 4px 16px rgba(255,183,0,0.25);
    }
    .btn-agri:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 28px rgba(255,183,0,0.4);
        color: #0a0e27;
    }
    .btn-agri:active { transform: translateY(0); }
    /* Secondary / outline button */
    .btn-outline-agri {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.4rem;
        padding: 0.6rem 1.2rem;
        background: transparent;
        color: #FFB700;
        border: 1px solid rgba(255,183,0,0.3);
        border-radius: 12px;
        font-size: 0.88rem;
        font-weight: 600;
        font-family: inherit;
        cursor: pointer;
        transition: all 0.25s ease;
        text-decoration: none;
    }
    .btn-outline-agri:hover {
        background: rgba(255,183,0,0.08);
        border-color: rgba(255,183,0,0.5);
        color: #FFB700;
    }
    /* Links */
    .auth-link {
        color: #FFB700;
        text-decoration: none;
        font-weight: 500;
        font-size: 0.85rem;
        transition: color 0.2s;
    }
    .auth-link:hover { color: #FFA000; text-decoration: underline; }
    .auth-link-muted {
        color: #6b7185;
        text-decoration: none;
        font-size: 0.83rem;
        transition: color 0.2s;
    }
    .auth-link-muted:hover { color: #9ba1b0; }
    /* Separator */
    .sep { display: flex; align-items: center; gap: 1rem; margin: 1.4rem 0; }
    .sep::before, .sep::after { content: ''; flex: 1; height: 1px; background: rgba(42,45,58,0.8); }
    .sep span { color: #6b7185; font-size: 0.78rem; font-weight: 500; }
    /* Status icons */
    .status-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 72px; height: 72px;
        border-radius: 20px;
        margin-bottom: 1.2rem;
        font-size: 2rem;
    }
    .status-icon.success {
        background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(16,185,129,0.05));
        border: 1px solid rgba(16,185,129,0.25);
        color: #10b981;
    }
    .status-icon.error {
        background: linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.05));
        border: 1px solid rgba(239,68,68,0.25);
        color: #ef4444;
    }
    .msg-text { color: #9ba1b0; font-size: 0.9rem; line-height: 1.6; }
    .msg-text strong { color: #e8eaed; }
    /* Responsive */
    @media (max-width: 480px) {
        .auth-card { padding: 2rem 1.4rem; border-radius: 20px; }
        .auth-brand { font-size: 1.3rem; }
    }
"""

PARTICLES_HTML = """
<div class="particles">
    <div class="particle"></div><div class="particle"></div><div class="particle"></div>
    <div class="particle"></div><div class="particle"></div><div class="particle"></div>
</div>
"""

@auth_bp.route("/register", methods=["GET"])
def register_form():
    """Affichage du formulaire d'inscription"""
    return render_template_string("""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inscription - AgriWeb Pro</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>""" + AUTH_BASE_CSS + """</style>
</head>
<body>
    """ + PARTICLES_HTML + """
    <div class="auth-card wide">
        <div class="text-center" style="margin-bottom:1.6rem">
            <div class="auth-icon"><i class="bi bi-rocket-takeoff"></i></div>
            <div class="auth-brand"><span class="gold">AgriWeb</span> Pro</div>
            <p class="auth-subtitle">Créez votre compte pour accéder à toutes les fonctionnalités</p>
        </div>
        <form method="POST" action="/auth/register">
            <div style="margin-bottom:0.9rem">
                <label class="form-label">Nom complet</label>
                <input type="text" class="form-control" name="name" placeholder="Jean Dupont" required>
            </div>
            <div style="margin-bottom:0.9rem">
                <label class="form-label">Email professionnel</label>
                <input type="email" class="form-control" name="email" placeholder="vous@entreprise.fr" required>
            </div>
            <div style="margin-bottom:0.9rem">
                <label class="form-label">Entreprise <span style="color:#6b7185">(optionnel)</span></label>
                <input type="text" class="form-control" name="company" placeholder="Nom de votre entreprise">
            </div>
            <div style="margin-bottom:1.2rem">
                <label class="form-label">Mot de passe</label>
                <input type="password" class="form-control" name="password" placeholder="Au moins 8 caractères" required minlength="8">
            </div>
            <button type="submit" class="btn-agri">
                <i class="bi bi-person-plus-fill"></i> Créer mon compte
            </button>
        </form>
        <div class="sep"><span>ou</span></div>
        <div style="text-align:center">
            <span class="auth-link-muted">Déjà un compte ?</span>
            <a href="/auth/login" class="auth-link" style="margin-left:0.3rem">Se connecter</a>
        </div>
    </div>
</body>
</html>
""")

@auth_bp.route("/register", methods=["POST"])
def register():
    """Inscription avec validation stricte et confirmation email"""
    try:
        data = request.get_json() if request.is_json else request.form
        
        email = data.get('email', '').strip().lower()
        name = data.get('name', '').strip()
        company = data.get('company', '').strip()
        password = data.get('password', '').strip()
        
        # Validation côté serveur
        if not email or not name or not password:
            if request.is_json:
                return jsonify({
                    'success': False, 
                    'error': 'Tous les champs obligatoires doivent être remplis'
                }), 400
            else:
                return render_template_string(ERROR_PAGE_TEMPLATE,
                                            title="Erreur d'inscription",
                                            message="Tous les champs obligatoires doivent être remplis")
        
        # Tentative d'inscription
        success, message = auth_system.register_user(email, name, company, password)
        
        if success:
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': message,
                    'next_step': 'check_email'
                }), 201
            else:
                # Retourner une page HTML propre pour l'inscription réussie
                return render_template_string(SUCCESS_PAGE_TEMPLATE,
                                            title="Inscription réussie !",
                                            message=f"Compte créé ! Vérifiez votre email {email} pour l'activer.")
        else:
            if request.is_json:
                return jsonify({
                    'success': False, 
                    'error': message
                }), 400
            else:
                return render_template_string(ERROR_PAGE_TEMPLATE,
                                            title="Erreur d'inscription",
                                            message=message)
            
    except Exception as e:
        print(f"Erreur register: {e}")
        if request.is_json:
            return jsonify({
                'success': False, 
                'error': 'Erreur lors de l\'inscription'
            }), 500
        else:
            return render_template_string(ERROR_PAGE_TEMPLATE,
                                        title="Erreur d'inscription",
                                        message="Erreur lors de l'inscription")

@auth_bp.route("/login", methods=["GET"])
def login_form():
    """Affichage du formulaire de connexion"""
    return render_template_string("""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexion - AgriWeb Pro</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>""" + AUTH_BASE_CSS + """</style>
</head>
<body>
    """ + PARTICLES_HTML + """
    <div class="auth-card">
        <div class="text-center" style="margin-bottom:1.8rem">
            <div class="auth-icon"><i class="bi bi-shield-lock-fill"></i></div>
            <div class="auth-brand"><span class="gold">AgriWeb</span> Pro</div>
            <p class="auth-subtitle">Connectez-vous à votre espace</p>
        </div>
        <form method="POST" action="/auth/login">
            <div style="margin-bottom:1rem">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.35rem">
                    <label class="form-label" style="margin-bottom:0">Email</label>
                </div>
                <input type="email" class="form-control" name="email" placeholder="vous@entreprise.fr" required>
            </div>
            <div style="margin-bottom:1.3rem">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.35rem">
                    <label class="form-label" style="margin-bottom:0">Mot de passe</label>
                    <a href="/auth/reset-password" class="auth-link-muted" style="font-size:0.78rem">
                        <i class="bi bi-key"></i> Oublié ?
                    </a>
                </div>
                <input type="password" class="form-control" name="password" placeholder="Votre mot de passe" required>
            </div>
            <button type="submit" class="btn-agri">
                <i class="bi bi-box-arrow-in-right"></i> Se connecter
            </button>
        </form>
        <div class="sep"><span>ou</span></div>
        <div style="text-align:center">
            <span class="auth-link-muted">Pas encore de compte ?</span>
            <a href="/auth/register" class="auth-link" style="margin-left:0.3rem">S'inscrire</a>
        </div>
    </div>
</body>
</html>
""")

@auth_bp.route("/login", methods=["POST"])
def login():
    """Connexion avec vérification email obligatoire"""
    try:
        data = request.get_json() if request.is_json else request.form
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({
                'success': False, 
                'error': 'Email et mot de passe requis'
            }), 400
        
        # Tentative d'authentification
        success, user_data, message = auth_system.authenticate_user(email, password)
        
        if success:
            # Créer une session
            session_token = auth_system.create_session(
                user_data['id'], 
                request.remote_addr, 
                request.headers.get('User-Agent')
            )
            
            if session_token:
                if request.is_json:
                    resp = jsonify({
                        'success': True, 
                        'message': message,
                        'user': {
                            'name': user_data['name'],
                            'email': user_data['email'],
                            'subscription_status': user_data['subscription_status']
                        },
                        'redirect': '/app'
                    })
                else:
                    resp = make_response(redirect('/app'))
                
                # Stocker le token de session
                session['session_token'] = session_token
                # Cookies sécurisés en prod (Railway)
                cookie_secure = os.getenv('COOKIE_SECURE', 'true').lower() in ('1','true','yes','on')
                cookie_samesite = os.getenv('COOKIE_SAMESITE', 'Lax')
                resp.set_cookie(
                    'session_token', session_token,
                    max_age=604800, httponly=True,
                    secure=cookie_secure,
                    samesite=cookie_samesite
                )
                
                return resp
            else:
                return jsonify({
                    'success': False, 
                    'error': 'Erreur lors de la création de session'
                }), 500
        else:
            return jsonify({
                'success': False, 
                'error': message
            }), 401
            
    except Exception as e:
        print(f"Erreur login: {e}")
        return jsonify({
            'success': False, 
            'error': 'Erreur lors de la connexion'
        }), 500

@auth_bp.route("/verify-email")
def verify_email():
    """Page de vérification d'email"""
    token = request.args.get('token')
    
    if not token:
        return render_template_string(ERROR_PAGE_TEMPLATE, 
                                    title="Lien invalide",
                                    message="Token de vérification manquant")
    
    # Vérifier le token
    success, message = auth_system.verify_email(token)
    
    if success:
        return render_template_string(SUCCESS_PAGE_TEMPLATE,
                                    title="Email vérifié !",
                                    message=message)
    else:
        return render_template_string(ERROR_PAGE_TEMPLATE,
                                    title="Erreur de vérification",
                                    message=message)

@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    """Renvoyer un email de vérification"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({
                'success': False, 
                'error': 'Email requis'
            }), 400
        
        # Logique pour renvoyer l'email de vérification
        # TODO: Implémenter la logique de renvoi
        
        return jsonify({
            'success': True, 
            'message': 'Email de vérification renvoyé'
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': 'Erreur lors du renvoi'
        }), 500

# Templates pour les pages de vérification
SUCCESS_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - AgriWeb Pro</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>""" + AUTH_BASE_CSS + """</style>
</head>
<body>
    """ + PARTICLES_HTML + """
    <div class="auth-card" style="text-align:center">
        <div class="status-icon success"><i class="bi bi-check-circle-fill"></i></div>
        <div class="auth-brand" style="margin-bottom:0.5rem"><span class="gold">{{ title }}</span></div>
        <p class="msg-text" style="margin-bottom:1.5rem">{{ message }}</p>
        <a href="/auth/login" class="btn-agri" style="margin-bottom:0.8rem;display:inline-flex">
            <i class="bi bi-box-arrow-in-right"></i> Se connecter
        </a>
        <div style="margin-top:0.8rem">
            <a href="/" class="auth-link-muted"><i class="bi bi-house"></i> Retour à l'accueil</a>
        </div>
    </div>
</body>
</html>
"""

ERROR_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - AgriWeb Pro</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>""" + AUTH_BASE_CSS + """</style>
</head>
<body>
    """ + PARTICLES_HTML + """
    <div class="auth-card" style="text-align:center">
        <div class="status-icon error"><i class="bi bi-x-circle-fill"></i></div>
        <div class="auth-brand" style="margin-bottom:0.5rem;color:#ef4444">{{ title }}</div>
        <p class="msg-text" style="margin-bottom:1.5rem">{{ message }}</p>
        <a href="/" class="btn-agri" style="margin-bottom:0.8rem;display:inline-flex">
            <i class="bi bi-house"></i> Retour à l'accueil
        </a>
        <div style="margin-top:0.8rem">
            <a href="/auth/login" class="auth-link"><i class="bi bi-box-arrow-in-right"></i> Se connecter</a>
        </div>
    </div>
</body>
</html>
"""

@auth_bp.route("/reset-password", methods=["GET"])
def reset_password_form():
    """Formulaire de demande de réinitialisation de mot de passe"""
    return render_template_string("""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Réinitialiser le mot de passe - AgriWeb Pro</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>""" + AUTH_BASE_CSS + """</style>
</head>
<body>
    """ + PARTICLES_HTML + """
    <div class="auth-card">
        <div class="text-center" style="margin-bottom:1.8rem">
            <div class="auth-icon"><i class="bi bi-key-fill"></i></div>
            <div class="auth-brand"><span class="gold">Mot de passe</span> oublié</div>
            <p class="auth-subtitle">Entrez votre email pour recevoir un lien de réinitialisation</p>
        </div>
        <form method="POST" action="/auth/reset-password">
            <div style="margin-bottom:1.2rem">
                <label class="form-label"><i class="bi bi-envelope"></i> Email</label>
                <input type="email" class="form-control" name="email" placeholder="vous@entreprise.fr" required>
            </div>
            <button type="submit" class="btn-agri">
                <i class="bi bi-send"></i> Envoyer le lien
            </button>
        </form>
        <div class="sep"><span></span></div>
        <div style="text-align:center">
            <a href="/auth/login" class="auth-link-muted"><i class="bi bi-arrow-left"></i> Retour à la connexion</a>
        </div>
    </div>
</body>
</html>
""")

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password_request():
    """Traitement de la demande de réinitialisation"""
    try:
        email = request.form.get('email', '').strip()
        
        if not email:
            return render_template_string(RESET_ERROR_TEMPLATE, 
                                          title="Email requis",
                                          message="Veuillez saisir votre adresse email.",
                                          back_url="/auth/reset-password")
        
        # Demander la réinitialisation via le système d'auth
        success, message = auth_system.request_password_reset(email)
        
        if success:
            return render_template_string("""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email envoyé - AgriWeb Pro</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>""" + AUTH_BASE_CSS + """</style>
</head>
<body>
    """ + PARTICLES_HTML + """
    <div class="auth-card" style="text-align:center">
        <div class="status-icon success"><i class="bi bi-envelope-check-fill"></i></div>
        <div class="auth-brand" style="margin-bottom:0.5rem"><span class="gold">Email envoyé</span></div>
        <p class="msg-text" style="margin-bottom:1.5rem">
            Un lien de réinitialisation a été envoyé à <strong>{{ email }}</strong>.<br>
            Vérifiez votre boîte mail et cliquez sur le lien pour créer un nouveau mot de passe.
        </p>
        <a href="/auth/login" class="btn-agri" style="display:inline-flex">
            <i class="bi bi-arrow-left"></i> Retour à la connexion
        </a>
    </div>
</body>
</html>
""", email=email)
        else:
            return render_template_string(RESET_ERROR_TEMPLATE,
                                          title="Erreur",
                                          message=message,
                                          back_url="/auth/reset-password")
            
    except Exception as e:
        return render_template_string(RESET_ERROR_TEMPLATE,
                                      title="Erreur système",
                                      message="Une erreur s'est produite. Veuillez réessayer.",
                                      back_url="/auth/reset-password")

@auth_bp.route("/new-password", methods=["GET"])
def new_password_form():
    """Formulaire de nouveau mot de passe"""
    token = request.args.get('token')
    
    if not token:
        return render_template_string(RESET_ERROR_TEMPLATE, 
                                      title="Token manquant",
                                      message="Lien de réinitialisation invalide.",
                                      back_url="/auth/login")
    
    return render_template_string("""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nouveau mot de passe - AgriWeb Pro</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>""" + AUTH_BASE_CSS + """</style>
</head>
<body>
    """ + PARTICLES_HTML + """
    <div class="auth-card">
        <div class="text-center" style="margin-bottom:1.8rem">
            <div class="auth-icon"><i class="bi bi-shield-lock-fill"></i></div>
            <div class="auth-brand"><span class="gold">Nouveau</span> mot de passe</div>
            <p class="auth-subtitle">Choisissez un nouveau mot de passe sécurisé</p>
        </div>
        <form method="POST" action="/auth/new-password">
            <input type="hidden" name="token" value="{{ token }}">
            <div style="margin-bottom:0.9rem">
                <label class="form-label"><i class="bi bi-lock"></i> Nouveau mot de passe</label>
                <input type="password" class="form-control" name="password" 
                       placeholder="Au moins 8 caractères" required minlength="8">
                <div class="form-text">Majuscules, minuscules et chiffres recommandés.</div>
            </div>
            <div style="margin-bottom:1.2rem">
                <label class="form-label"><i class="bi bi-lock-fill"></i> Confirmer</label>
                <input type="password" class="form-control" name="confirm_password" 
                       placeholder="Répétez le mot de passe" required>
            </div>
            <button type="submit" class="btn-agri">
                <i class="bi bi-check2"></i> Définir le nouveau mot de passe
            </button>
        </form>
    </div>
</body>
</html>
""", token=token)

@auth_bp.route("/new-password", methods=["POST"])
def new_password_submit():
    """Traitement du nouveau mot de passe"""
    try:
        token = request.form.get('token')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([token, password, confirm_password]):
            return render_template_string(RESET_ERROR_TEMPLATE,
                                          title="Données incomplètes",
                                          message="Tous les champs sont requis.",
                                          back_url="/auth/login")
        
        if password != confirm_password:
            return render_template_string(RESET_ERROR_TEMPLATE,
                                          title="Mots de passe différents",
                                          message="Les deux mots de passe ne correspondent pas.",
                                          back_url="/auth/new-password?token=" + token)
        
        # Réinitialiser le mot de passe via le système d'auth
        success, message = auth_system.reset_password_with_token(token, password)
        
        if success:
            return render_template_string("""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mot de passe modifié - AgriWeb Pro</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>""" + AUTH_BASE_CSS + """</style>
</head>
<body>
    """ + PARTICLES_HTML + """
    <div class="auth-card" style="text-align:center">
        <div class="status-icon success"><i class="bi bi-check-circle-fill"></i></div>
        <div class="auth-brand" style="margin-bottom:0.5rem"><span class="gold">Mot de passe modifié</span></div>
        <p class="msg-text" style="margin-bottom:1.5rem">
            Votre mot de passe a été mis à jour avec succès.<br>
            Vous pouvez maintenant vous connecter avec votre nouveau mot de passe.
        </p>
        <a href="/auth/login" class="btn-agri" style="display:inline-flex">
            <i class="bi bi-box-arrow-in-right"></i> Se connecter
        </a>
    </div>
</body>
</html>
""")
        else:
            return render_template_string(RESET_ERROR_TEMPLATE,
                                          title="Erreur de réinitialisation",
                                          message=message,
                                          back_url="/auth/login")
            
    except Exception as e:
        return render_template_string(RESET_ERROR_TEMPLATE,
                                      title="Erreur système",
                                      message="Une erreur s'est produite. Veuillez réessayer.",
                                      back_url="/auth/login")

RESET_ERROR_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - AgriWeb Pro</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>""" + AUTH_BASE_CSS + """</style>
</head>
<body>
    """ + PARTICLES_HTML + """
    <div class="auth-card" style="text-align:center">
        <div class="status-icon error"><i class="bi bi-x-circle-fill"></i></div>
        <div class="auth-brand" style="margin-bottom:0.5rem;color:#ef4444">{{ title }}</div>
        <p class="msg-text" style="margin-bottom:1.5rem">{{ message }}</p>
        <a href="{{ back_url or '/' }}" class="btn-agri" style="margin-bottom:0.8rem;display:inline-flex">
            <i class="bi bi-arrow-left"></i> Retour
        </a>
        <div style="margin-top:0.8rem">
            <a href="/auth/login" class="auth-link"><i class="bi bi-box-arrow-in-right"></i> Se connecter</a>
        </div>
    </div>
</body>
</html>
"""
