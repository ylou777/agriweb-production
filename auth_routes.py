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
