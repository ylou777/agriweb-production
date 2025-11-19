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

@auth_bp.route("/register", methods=["GET"])
def register_form():
    """Affichage du formulaire d'inscription"""
    return render_template_string("""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Inscription - AgriWeb Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>
        body {
            background: linear-gradient(135deg, #28a745, #20c997);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .registration-card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 3rem;
            max-width: 500px;
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="registration-card">
        <div class="text-center mb-4">
            <h2 class="text-success mb-3">🚀 Inscription AgriWeb Pro</h2>
            <p class="text-muted">Créez votre compte pour accéder à toutes les fonctionnalités</p>
        </div>
        <form method="POST" action="/auth/register">
            <div class="mb-3">
                <label for="name" class="form-label">Nom complet</label>
                <input type="text" class="form-control" id="name" name="name" required>
            </div>
            <div class="mb-3">
                <label for="email" class="form-label">Email</label>
                <input type="email" class="form-control" id="email" name="email" required>
            </div>
            <div class="mb-3">
                <label for="company" class="form-label">Entreprise (optionnel)</label>
                <input type="text" class="form-control" id="company" name="company">
            </div>
            <div class="mb-3">
                <label for="password" class="form-label">Mot de passe</label>
                <input type="password" class="form-control" id="password" name="password" required>
            </div>
            <button type="submit" class="btn btn-success w-100 mb-3">
                <i class="bi bi-person-plus"></i> Créer mon compte
            </button>
        </form>
        <div class="text-center">
            <small class="text-muted">
                Déjà un compte ? <a href="/auth/login" class="text-success">Se connecter</a>
            </small>
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
    <title>🔐 Connexion - AgriWeb Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>
        body {
            background: linear-gradient(135deg, #28a745, #20c997);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .login-card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 3rem;
            max-width: 450px;
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="text-center mb-4">
            <h2 class="text-success mb-3">🔐 Connexion AgriWeb Pro</h2>
            <p class="text-muted">Connectez-vous à votre compte</p>
        </div>
        <form method="POST" action="/auth/login">
            <div class="mb-3">
                <label for="email" class="form-label">Email</label>
                <input type="email" class="form-control" id="email" name="email" required>
            </div>
            <div class="mb-3">
                <label for="password" class="form-label">Mot de passe</label>
                <input type="password" class="form-control" id="password" name="password" required>
            </div>
            <button type="submit" class="btn btn-success w-100 mb-3">
                <i class="bi bi-box-arrow-in-right"></i> Se connecter
            </button>
        </form>
        <div class="text-center">
            <div class="mb-2">
                <small class="text-muted">
                    <a href="/auth/reset-password" class="text-warning text-decoration-none">
                        <i class="bi bi-key"></i> Mot de passe oublié ?
                    </a>
                </small>
            </div>
            <small class="text-muted">
                Pas encore de compte ? <a href="/auth/register" class="text-success">S'inscrire</a>
            </small>
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
    <title>{{ title }} - AgriWeb</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>
        body {
            background: linear-gradient(135deg, #28a745, #20c997);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .verification-card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 3rem;
            max-width: 500px;
            text-align: center;
        }
        .success-icon {
            font-size: 4rem;
            color: #28a745;
            margin-bottom: 1rem;
        }
        .btn-primary {
            background: linear-gradient(135deg, #28a745, #20c997);
            border: none;
            border-radius: 10px;
            padding: 0.75rem 2rem;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="verification-card">
        <div class="success-icon">
            <i class="bi bi-check-circle-fill"></i>
        </div>
        <h2 class="text-success mb-3">{{ title }}</h2>
        <p class="text-muted mb-4">{{ message }}</p>
        <a href="/" class="btn btn-primary">
            <i class="bi bi-house"></i> Retour à l'accueil
        </a>
        <div class="mt-4">
            <a href="/app" class="btn btn-outline-success">
                <i class="bi bi-box-arrow-in-right"></i> Se connecter maintenant
            </a>
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
    <title>{{ title }} - AgriWeb</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>
        body {
            background: linear-gradient(135deg, #dc3545, #fd7e14);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .verification-card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 3rem;
            max-width: 500px;
            text-align: center;
        }
        .error-icon {
            font-size: 4rem;
            color: #dc3545;
            margin-bottom: 1rem;
        }
        .btn-primary {
            background: linear-gradient(135deg, #28a745, #20c997);
            border: none;
            border-radius: 10px;
            padding: 0.75rem 2rem;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="verification-card">
        <div class="error-icon">
            <i class="bi bi-x-circle-fill"></i>
        </div>
        <h2 class="text-danger mb-3">{{ title }}</h2>
        <p class="text-muted mb-4">{{ message }}</p>
        <a href="/" class="btn btn-primary">
            <i class="bi bi-house"></i> Retour à l'accueil
        </a>
        <div class="mt-4">
            <small class="text-muted">
                Besoin d'aide ? Contactez notre support technique
            </small>
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
    <title>🔑 Réinitialiser le mot de passe - AgriWeb Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>
        body {
            background: linear-gradient(135deg, #6c757d, #495057);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .reset-card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 3rem;
            max-width: 500px;
            width: 100%;
        }
        .btn-primary {
            background: linear-gradient(135deg, #6c757d, #495057);
            border: none;
            border-radius: 10px;
            padding: 0.75rem 2rem;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="reset-card">
        <div class="text-center mb-4">
            <h2 class="text-secondary mb-3">🔑 Réinitialiser le mot de passe</h2>
            <p class="text-muted">Entrez votre email pour recevoir un lien de réinitialisation</p>
        </div>
        <form method="POST" action="/auth/reset-password">
            <div class="mb-3">
                <label for="email" class="form-label">
                    <i class="bi bi-envelope"></i> Email
                </label>
                <input type="email" class="form-control" id="email" name="email" 
                       placeholder="votre@email.com" required>
            </div>
            <div class="d-grid gap-2">
                <button type="submit" class="btn btn-primary">
                    <i class="bi bi-send"></i> Envoyer le lien de réinitialisation
                </button>
            </div>
        </form>
        <div class="text-center mt-4">
            <a href="/auth/login" class="text-decoration-none">
                <i class="bi bi-arrow-left"></i> Retour à la connexion
            </a>
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
    <title>✅ Email envoyé - AgriWeb Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>
        body {
            background: linear-gradient(135deg, #28a745, #20c997);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .success-card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 3rem;
            max-width: 500px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="success-card">
        <div class="text-success mb-4">
            <i class="bi bi-check-circle-fill" style="font-size: 4rem;"></i>
        </div>
        <h2 class="text-success mb-3">📧 Email envoyé !</h2>
        <p class="text-muted mb-4">
            Un lien de réinitialisation a été envoyé à <strong>{{ email }}</strong>.<br>
            Vérifiez votre boîte mail et cliquez sur le lien pour créer un nouveau mot de passe.
        </p>
        <a href="/auth/login" class="btn btn-success">
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
    <title>🔐 Nouveau mot de passe - AgriWeb Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>
        body {
            background: linear-gradient(135deg, #007bff, #0056b3);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .password-card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 3rem;
            max-width: 500px;
            width: 100%;
        }
        .btn-primary {
            background: linear-gradient(135deg, #007bff, #0056b3);
            border: none;
            border-radius: 10px;
            padding: 0.75rem 2rem;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="password-card">
        <div class="text-center mb-4">
            <h2 class="text-primary mb-3">🔐 Nouveau mot de passe</h2>
            <p class="text-muted">Choisissez un nouveau mot de passe sécurisé</p>
        </div>
        <form method="POST" action="/auth/new-password">
            <input type="hidden" name="token" value="{{ token }}">
            <div class="mb-3">
                <label for="password" class="form-label">
                    <i class="bi bi-lock"></i> Nouveau mot de passe
                </label>
                <input type="password" class="form-control" id="password" name="password" 
                       placeholder="Au moins 8 caractères" required minlength="8">
                <div class="form-text">
                    Le mot de passe doit contenir au moins 8 caractères avec majuscules, minuscules et chiffres.
                </div>
            </div>
            <div class="mb-3">
                <label for="confirm_password" class="form-label">
                    <i class="bi bi-lock-fill"></i> Confirmer le mot de passe
                </label>
                <input type="password" class="form-control" id="confirm_password" name="confirm_password" 
                       placeholder="Répétez le mot de passe" required>
            </div>
            <div class="d-grid gap-2">
                <button type="submit" class="btn btn-primary">
                    <i class="bi bi-check2"></i> Définir le nouveau mot de passe
                </button>
            </div>
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
    <title>✅ Mot de passe modifié - AgriWeb Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>
        body {
            background: linear-gradient(135deg, #28a745, #20c997);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .success-card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 3rem;
            max-width: 500px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="success-card">
        <div class="text-success mb-4">
            <i class="bi bi-check-circle-fill" style="font-size: 4rem;"></i>
        </div>
        <h2 class="text-success mb-3">🎉 Mot de passe modifié !</h2>
        <p class="text-muted mb-4">
            Votre mot de passe a été mis à jour avec succès.<br>
            Vous pouvez maintenant vous connecter avec votre nouveau mot de passe.
        </p>
        <a href="/auth/login" class="btn btn-success">
            <i class="bi bi-arrow-right"></i> Se connecter
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
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>
        body {
            background: linear-gradient(135deg, #dc3545, #c82333);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .error-card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 3rem;
            max-width: 500px;
            text-align: center;
        }
        .error-icon {
            font-size: 4rem;
            color: #dc3545;
            margin-bottom: 1rem;
        }
        .btn-primary {
            background: linear-gradient(135deg, #28a745, #20c997);
            border: none;
            border-radius: 10px;
            padding: 0.75rem 2rem;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="error-card">
        <div class="error-icon">
            <i class="bi bi-x-circle-fill"></i>
        </div>
        <h2 class="text-danger mb-3">{{ title }}</h2>
        <p class="text-muted mb-4">{{ message }}</p>
        <div class="d-grid gap-2">
            <a href="{{ back_url or '/' }}" class="btn btn-primary">
                <i class="bi bi-arrow-left"></i> Retour
            </a>
            <a href="/auth/login" class="btn btn-outline-secondary">
                <i class="bi bi-house"></i> Connexion
            </a>
        </div>
        <div class="mt-4">
            <small class="text-muted">
                Besoin d'aide ? Contactez notre support technique
            </small>
        </div>
    </div>
</body>
</html>
"""
