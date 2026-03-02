#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'authentification intégré pour votre app Railway
Routes d'authentification à ajouter à agriweb_hebergement_gratuit.py
"""

from flask import request, session, jsonify, redirect, render_template_string, url_for
from auth_system_improved import AuthSystem
from production_config import ProductionConfig
import os

# Instance du système d'authentification
auth_system = AuthSystem()

# Template HTML intégré pour l'authentification
AUTH_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% if mode == 'login' %}Connexion{% else %}Inscription{% endif %} - HeliaPV</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>
        body { background: linear-gradient(135deg, #28a745, #20c997); min-height: 100vh; }
        .auth-card { background: white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .brand-logo { color: #28a745; font-size: 2rem; font-weight: bold; }
    </style>
</head>
<body class="d-flex align-items-center">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-5">
                <div class="auth-card p-5">
                    <div class="text-center mb-4">
                        <h1 class="brand-logo">🌱 HeliaPV</h1>
                        <h3>{% if mode == 'login' %}Connexion{% else %}Inscription{% endif %}</h3>
                    </div>
                    
                    {% if error %}
                    <div class="alert alert-danger">{{ error }}</div>
                    {% endif %}
                    
                    {% if success %}
                    <div class="alert alert-success">{{ success }}</div>
                    {% endif %}
                    
                    <form method="POST" id="authForm">
                        {% if mode == 'register' %}
                        <div class="mb-3">
                            <label class="form-label">Nom complet *</label>
                            <input type="text" class="form-control" name="name" required>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Entreprise</label>
                            <input type="text" class="form-control" name="company">
                        </div>
                        {% endif %}
                        
                        <div class="mb-3">
                            <label class="form-label">Email {% if mode == 'register' %}professionnel{% endif %} *</label>
                            <input type="email" class="form-control" name="email" required>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Mot de passe *</label>
                            <input type="password" class="form-control" name="password" required>
                        </div>
                        
                        <button type="submit" class="btn btn-success w-100 py-2">
                            {% if mode == 'login' %}Se connecter{% else %}Créer mon compte{% endif %}
                        </button>
                    </form>
                    
                    <div class="text-center mt-3">
                        {% if mode == 'login' %}
                        <p>Pas encore de compte ? <a href="/auth/register">S'inscrire</a></p>
                        {% else %}
                        <p>Déjà un compte ? <a href="/auth/login">Se connecter</a></p>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

def init_auth_routes(app):
    """Initialise les routes d'authentification dans votre app Flask"""
    
    @app.route('/auth/login', methods=['GET', 'POST'])
    def auth_login():
        """Route de connexion"""
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            if auth_system.authenticate_user(email, password):
                # Créer une session
                session_token = auth_system.create_session(email)
                session['session_token'] = session_token
                session['user_email'] = email
                
                # Redirection vers l'application principale
                return redirect('/')
            else:
                return render_template_string(AUTH_TEMPLATE, 
                                            mode='login', 
                                            error='Email ou mot de passe incorrect')
        
        return render_template_string(AUTH_TEMPLATE, mode='login')
    
    @app.route('/auth/register', methods=['GET', 'POST'])
    def auth_register():
        """Route d'inscription"""
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            name = request.form.get('name')
            company = request.form.get('company', '')
            
            # Tentative d'inscription
            result = auth_system.register_user(email, password, name, company)
            
            if result['success']:
                return render_template_string(AUTH_TEMPLATE, 
                                            mode='register',
                                            success='Inscription réussie ! Vérifiez votre email pour confirmer votre compte.')
            else:
                return render_template_string(AUTH_TEMPLATE, 
                                            mode='register', 
                                            error=result['error'])
        
        return render_template_string(AUTH_TEMPLATE, mode='register')
    
    @app.route('/auth/verify-email')
    def auth_verify_email():
        """Vérification d'email"""
        token = request.args.get('token')
        
        if auth_system.verify_email(token):
            return """
            <div style="text-align:center; margin-top:100px; font-family:Arial;">
                <h2 style="color:green;">✅ Email vérifié avec succès !</h2>
                <p>Votre compte est maintenant activé.</p>
                <a href="/auth/login" style="background:#28a745; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">Se connecter</a>
            </div>
            """
        else:
            return """
            <div style="text-align:center; margin-top:100px; font-family:Arial;">
                <h2 style="color:red;">❌ Erreur de vérification</h2>
                <p>Le lien de vérification est invalide ou expiré.</p>
                <a href="/auth/register" style="background:#28a745; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">Réessayer</a>
            </div>
            """
    
    @app.route('/auth/logout')
    def auth_logout():
        """Déconnexion"""
        session.clear()
        return redirect('/auth/login')
    
    @app.before_request
    def check_auth():
        """Vérification d'authentification avant chaque requête"""
        # Routes publiques (pas besoin d'authentification)
        public_routes = ['/auth/login', '/auth/register', '/auth/verify-email', '/static', '/favicon.ico']
        
        # Si la route est publique, passer
        if any(request.path.startswith(route) for route in public_routes):
            return
        
        # Vérifier si l'utilisateur est connecté
        session_token = session.get('session_token')
        if not session_token:
            return redirect('/auth/login?next=' + request.path)
    
    return app
