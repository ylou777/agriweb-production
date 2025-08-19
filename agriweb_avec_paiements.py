#!/usr/bin/env python3
"""
🚀 AGRIWEB 2.0 - PRODUCTION AVEC PAIEMENTS STRIPE
Version commerciale complète avec authentification et paiements Stripe
"""

from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for, flash
import json
import os
import uuid
from datetime import datetime, timedelta
import hashlib
import secrets
import stripe
from stripe_integration import stripe_payment_manager

# Configuration
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Import des modules existants
from agriweb_source import AgriWebService
from production_commercial import UserManager

# Instance du service AgriWeb
agriweb_service = AgriWebService()

# Instance du gestionnaire d'utilisateurs
user_manager = UserManager()

# Configuration Stripe
STRIPE_PUBLISHABLE_KEY = stripe_payment_manager.stripe_publishable_key

# Templates avec intégration paiement
PAYMENT_SELECTION_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Abonnements AgriWeb 2.0</title>
    <script src="https://js.stripe.com/v3/"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 1rem 0;
            text-align: center;
            color: white;
        }
        
        .container {
            flex: 1;
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 2rem;
        }
        
        .pricing-hero {
            text-align: center;
            color: white;
            margin-bottom: 3rem;
        }
        
        .pricing-hero h1 {
            font-size: 3rem;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .pricing-hero p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .plans-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }
        
        .plan-card {
            background: white;
            border-radius: 20px;
            padding: 2.5rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            position: relative;
            transition: all 0.3s ease;
            overflow: hidden;
        }
        
        .plan-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 30px 60px rgba(0,0,0,0.2);
        }
        
        .plan-card.popular {
            border: 3px solid #28a745;
            transform: scale(1.05);
        }
        
        .plan-card.popular::before {
            content: "⭐ POPULAIRE";
            position: absolute;
            top: -10px;
            left: 50%;
            transform: translateX(-50%);
            background: #28a745;
            color: white;
            padding: 0.5rem 1.5rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .plan-icon {
            font-size: 3rem;
            text-align: center;
            margin-bottom: 1rem;
        }
        
        .plan-name {
            font-size: 1.8rem;
            font-weight: bold;
            text-align: center;
            margin-bottom: 1rem;
            color: #333;
        }
        
        .plan-price {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .plan-price .amount {
            font-size: 3rem;
            font-weight: bold;
            color: #007bff;
        }
        
        .plan-price .period {
            font-size: 1.2rem;
            color: #666;
        }
        
        .plan-features {
            list-style: none;
            padding: 0;
            margin: 2rem 0;
        }
        
        .plan-features li {
            padding: 0.8rem 0;
            border-bottom: 1px solid #f0f0f0;
            display: flex;
            align-items: center;
        }
        
        .plan-features li:last-child {
            border-bottom: none;
        }
        
        .plan-features li::before {
            content: "✅";
            margin-right: 0.8rem;
            font-size: 1.2rem;
        }
        
        .btn-subscribe {
            width: 100%;
            background: linear-gradient(45deg, #007bff, #28a745);
            color: white;
            border: none;
            padding: 1.2rem;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .btn-subscribe:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,123,255,0.3);
        }
        
        .btn-subscribe:active {
            transform: translateY(0);
        }
        
        .trial-badge {
            background: #17a2b8;
            color: white;
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            font-size: 0.9rem;
            margin-top: 1rem;
            display: inline-block;
        }
        
        .features-comparison {
            background: white;
            border-radius: 20px;
            padding: 2rem;
            margin: 3rem 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .loading {
            display: none;
            text-align: center;
            color: white;
            font-size: 1.2rem;
        }
        
        .security-badges {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin: 2rem 0;
            flex-wrap: wrap;
        }
        
        .security-badge {
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 0.8rem 1.5rem;
            border-radius: 25px;
            font-size: 0.9rem;
            backdrop-filter: blur(10px);
        }
        
        @media (max-width: 768px) {
            .plans-grid {
                grid-template-columns: 1fr;
                gap: 1rem;
            }
            
            .plan-card.popular {
                transform: none;
            }
            
            .pricing-hero h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>🌾 AgriWeb 2.0 - Solution Professionnelle</h2>
        <p>Bonjour {{ user_email }} | <a href="/logout" style="color: white;">Déconnexion</a></p>
    </div>
    
    <div class="container">
        <div class="pricing-hero">
            <h1>🚀 Choisissez votre abonnement</h1>
            <p>Commencez votre analyse agricole dès maintenant</p>
            
            <div class="security-badges">
                <div class="security-badge">🔒 Paiement sécurisé Stripe</div>
                <div class="security-badge">🆓 15 jours d'essai gratuit</div>
                <div class="security-badge">❌ Annulation à tout moment</div>
            </div>
        </div>
        
        <div class="plans-grid">
            <!-- Plan Starter -->
            <div class="plan-card">
                <div class="plan-icon">💼</div>
                <div class="plan-name">Starter</div>
                <div class="plan-price">
                    <span class="amount">99€</span>
                    <span class="period">/mois</span>
                </div>
                
                <ul class="plan-features">
                    <li>500 recherches par mois</li>
                    <li>Données cadastrales de base</li>
                    <li>Rapports PDF standard</li>
                    <li>Support par email</li>
                    <li>Accès interface web</li>
                </ul>
                
                <button class="btn-subscribe" onclick="selectPlan('starter')">
                    🆓 Commencer l'essai gratuit
                </button>
                <div class="trial-badge">✨ 15 jours gratuits puis 99€/mois</div>
            </div>
            
            <!-- Plan Professional -->
            <div class="plan-card popular">
                <div class="plan-icon">🚀</div>
                <div class="plan-name">Professional</div>
                <div class="plan-price">
                    <span class="amount">299€</span>
                    <span class="period">/mois</span>
                </div>
                
                <ul class="plan-features">
                    <li>2000 recherches par mois</li>
                    <li>Toutes les couches de données</li>
                    <li>Accès API complet</li>
                    <li>Rapports avancés et exports</li>
                    <li>Support prioritaire</li>
                    <li>Analyse multi-parcelles</li>
                </ul>
                
                <button class="btn-subscribe" onclick="selectPlan('professional')">
                    🆓 Commencer l'essai gratuit
                </button>
                <div class="trial-badge">✨ 15 jours gratuits puis 299€/mois</div>
            </div>
            
            <!-- Plan Enterprise -->
            <div class="plan-card">
                <div class="plan-icon">🏢</div>
                <div class="plan-name">Enterprise</div>
                <div class="plan-price">
                    <span class="amount">599€</span>
                    <span class="period">/mois</span>
                </div>
                
                <ul class="plan-features">
                    <li>Recherches illimitées</li>
                    <li>Support 24/7 dédié</li>
                    <li>Interface personnalisée</li>
                    <li>Intégrations sur mesure</li>
                    <li>Account manager dédié</li>
                    <li>SLA garanti 99.9%</li>
                    <li>Formation équipe incluse</li>
                </ul>
                
                <button class="btn-subscribe" onclick="selectPlan('enterprise')">
                    🆓 Commencer l'essai gratuit
                </button>
                <div class="trial-badge">✨ 15 jours gratuits puis 599€/mois</div>
            </div>
        </div>
        
        <div class="features-comparison">
            <h2 style="text-align: center; margin-bottom: 2rem;">📊 Comparaison détaillée</h2>
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="padding: 1rem; text-align: left;">Fonctionnalité</th>
                            <th style="padding: 1rem; text-align: center;">Starter</th>
                            <th style="padding: 1rem; text-align: center;">Professional</th>
                            <th style="padding: 1rem; text-align: center;">Enterprise</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 1rem;">Recherches mensuelles</td>
                            <td style="padding: 1rem; text-align: center;">500</td>
                            <td style="padding: 1rem; text-align: center;">2000</td>
                            <td style="padding: 1rem; text-align: center;">Illimitées</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 1rem;">Données cadastrales</td>
                            <td style="padding: 1rem; text-align: center;">✅</td>
                            <td style="padding: 1rem; text-align: center;">✅</td>
                            <td style="padding: 1rem; text-align: center;">✅</td>
                        </tr>
                        <tr>
                            <td style="padding: 1rem;">PLU/Zonage</td>
                            <td style="padding: 1rem; text-align: center;">❌</td>
                            <td style="padding: 1rem; text-align: center;">✅</td>
                            <td style="padding: 1rem; text-align: center;">✅</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 1rem;">API Access</td>
                            <td style="padding: 1rem; text-align: center;">❌</td>
                            <td style="padding: 1rem; text-align: center;">✅</td>
                            <td style="padding: 1rem; text-align: center;">✅</td>
                        </tr>
                        <tr>
                            <td style="padding: 1rem;">Support</td>
                            <td style="padding: 1rem; text-align: center;">Email</td>
                            <td style="padding: 1rem; text-align: center;">Prioritaire</td>
                            <td style="padding: 1rem; text-align: center;">24/7 Dédié</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <div class="loading" id="loading">
        <h2>🔄 Redirection vers le paiement sécurisé...</h2>
        <p>Veuillez patienter</p>
    </div>

    <script>
        const stripe = Stripe('{{ stripe_publishable_key }}');
        
        async function selectPlan(plan) {
            const button = event.target;
            button.disabled = true;
            button.innerHTML = '🔄 Chargement...';
            
            document.getElementById('loading').style.display = 'block';
            
            try {
                const response = await fetch('/api/payment/create-checkout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ plan: plan })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Redirection vers Stripe Checkout
                    window.location.href = result.checkout_url;
                } else {
                    alert('❌ Erreur: ' + result.error);
                    button.disabled = false;
                    button.innerHTML = '🆓 Commencer l\'essai gratuit';
                    document.getElementById('loading').style.display = 'none';
                }
            } catch (error) {
                alert('❌ Erreur de connexion: ' + error);
                button.disabled = false;
                button.innerHTML = '🆓 Commencer l\'essai gratuit';
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        // Animation d'entrée
        document.addEventListener('DOMContentLoaded', function() {
            const cards = document.querySelectorAll('.plan-card');
            cards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(50px)';
                setTimeout(() => {
                    card.style.transition = 'all 0.6s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 200);
            });
        });
    </script>
</body>
</html>
"""

PAYMENT_SUCCESS_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>✅ Abonnement Activé - AgriWeb 2.0</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .success-container {
            background: white;
            border-radius: 20px;
            padding: 3rem;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 600px;
            margin: 2rem;
        }
        
        .success-icon {
            font-size: 5rem;
            margin-bottom: 1rem;
            animation: bounce 1s infinite;
        }
        
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-10px); }
            60% { transform: translateY(-5px); }
        }
        
        .success-title {
            font-size: 2.5rem;
            color: #28a745;
            margin-bottom: 1rem;
        }
        
        .success-message {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 2rem;
            line-height: 1.6;
        }
        
        .subscription-details {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 2rem 0;
            text-align: left;
        }
        
        .btn-continue {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 10px;
            font-size: 1.1rem;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: transform 0.3s ease;
        }
        
        .btn-continue:hover {
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="success-container">
        <div class="success-icon">🎉</div>
        <h1 class="success-title">Félicitations !</h1>
        <p class="success-message">
            Votre abonnement AgriWeb 2.0 a été activé avec succès.<br>
            Vous disposez maintenant de 15 jours d'essai gratuit pour découvrir toutes les fonctionnalités.
        </p>
        
        <div class="subscription-details">
            <h3>📋 Détails de votre abonnement</h3>
            <p><strong>Plan:</strong> {{ plan|title }}</p>
            <p><strong>Période d'essai:</strong> 15 jours gratuits</p>
            <p><strong>Facturation:</strong> {{ trial_end }}</p>
            <p><strong>ID Abonnement:</strong> {{ subscription_id }}</p>
        </div>
        
        <a href="/dashboard" class="btn-continue">
            🚀 Commencer l'analyse
        </a>
        
        <p style="margin-top: 2rem; font-size: 0.9rem; color: #666;">
            📧 Un email de confirmation a été envoyé.<br>
            💳 Vous pouvez gérer votre abonnement dans votre dashboard.
        </p>
    </div>
</body>
</html>
"""

# Routes principales
@app.route('/')
def home():
    """Page d'accueil"""
    if session.get('authenticated'):
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/pricing')
def pricing():
    """Page de sélection d'abonnement"""
    if not session.get('authenticated'):
        return redirect('/login')
    
    user_data = session.get('user_data', {})
    user_email = user_data.get('email', '')
    
    return render_template_string(
        PAYMENT_SELECTION_TEMPLATE,
        user_email=user_email,
        stripe_publishable_key=STRIPE_PUBLISHABLE_KEY
    )

@app.route('/api/payment/create-checkout', methods=['POST'])
def create_checkout_session():
    """Crée une session de paiement Stripe"""
    if not session.get('authenticated'):
        return jsonify({"error": "Non autorisé"}), 401
    
    try:
        data = request.get_json()
        plan = data.get('plan')
        
        if plan not in ['starter', 'professional', 'enterprise']:
            return jsonify({"error": "Plan invalide"}), 400
        
        user_data = session.get('user_data', {})
        user_email = user_data.get('email')
        
        if not user_email:
            return jsonify({"error": "Email utilisateur non trouvé"}), 400
        
        # Créer la session checkout
        result = stripe_payment_manager.create_checkout_session(
            customer_email=user_email,
            plan=plan,
            success_url=f"{request.url_root}payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{request.url_root}payment/cancel"
        )
        
        if result['success']:
            # Sauvegarder le plan sélectionné dans la session
            session['selected_plan'] = plan
            
            return jsonify({
                "success": True,
                "checkout_url": result['checkout_url'],
                "plan": plan
            })
        else:
            return jsonify({"error": result['error']}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/payment/success')
def payment_success():
    """Page de confirmation après paiement réussi"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        return "Session ID manquant", 400
    
    try:
        # Traiter le checkout réussi
        result = stripe_payment_manager.handle_successful_checkout(session_id)
        
        if result['success']:
            user_email = result['customer_email']
            subscription_id = result['subscription_id']
            plan = result['plan']
            
            # Mettre à jour l'utilisateur dans la base
            if user_email in user_manager.users:
                user_manager.users[user_email].update({
                    'stripe_subscription_id': subscription_id,
                    'license_type': plan,
                    'active': True,
                    'trial_end': datetime.fromtimestamp(result['trial_end']).isoformat() if result['trial_end'] else None,
                    'subscription_updated': datetime.now().isoformat()
                })
                user_manager.save_users()
                
                # Mettre à jour la session
                session['user_data']['license_type'] = plan
                session['user_data']['active'] = True
            
            return render_template_string(
                PAYMENT_SUCCESS_TEMPLATE,
                plan=plan,
                subscription_id=subscription_id,
                trial_end=datetime.fromtimestamp(result['trial_end']).strftime('%d/%m/%Y') if result['trial_end'] else 'Immédiatement'
            )
        else:
            return f"Erreur lors du traitement: {result['error']}", 500
            
    except Exception as e:
        return f"Erreur: {e}", 500

@app.route('/payment/cancel')
def payment_cancel():
    """Page d'annulation de paiement"""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>❌ Paiement Annulé</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 2rem; }
            .container { max-width: 600px; margin: 0 auto; }
            .btn { background: #007bff; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 8px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>❌ Paiement Annulé</h1>
            <p>Votre paiement a été annulé. Vous pouvez réessayer à tout moment.</p>
            <a href="/pricing" class="btn">🔄 Réessayer</a>
            <a href="/dashboard" class="btn">📊 Retour au Dashboard</a>
        </div>
    </body>
    </html>
    """)

@app.route('/api/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Webhook Stripe pour événements d'abonnement"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    if not sig_header:
        return "Signature manquante", 400
    
    try:
        result = stripe_payment_manager.process_webhook(payload, sig_header)
        
        if result['success']:
            return "Webhook traité", 200
        else:
            return f"Erreur webhook: {result['error']}", 400
            
    except Exception as e:
        return f"Erreur: {e}", 500

@app.route('/dashboard')
def dashboard():
    """Dashboard principal avec informations d'abonnement"""
    if not session.get('authenticated'):
        return redirect('/login')
    
    user_data = session.get('user_data', {})
    user_email = user_data.get('email')
    user = user_manager.users.get(user_email, {})
    
    # Vérifier le statut de l'abonnement si disponible
    subscription_info = None
    if user.get('stripe_subscription_id'):
        subscription_info = stripe_payment_manager.get_subscription_info(
            user['stripe_subscription_id']
        )
    
    # Template de dashboard avec informations d'abonnement
    dashboard_template = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>📊 Dashboard AgriWeb 2.0</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; background: #f5f5f5; }
            .header { background: #007bff; color: white; padding: 1rem; }
            .container { max-width: 1200px; margin: 2rem auto; padding: 0 2rem; }
            .subscription-card { background: white; border-radius: 12px; padding: 2rem; margin: 1rem 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .status-active { border-left: 5px solid #28a745; }
            .status-trial { border-left: 5px solid #17a2b8; }
            .btn { background: #007bff; color: white; padding: 0.8rem 1.5rem; text-decoration: none; border-radius: 6px; display: inline-block; margin: 0.5rem; }
            .btn-danger { background: #dc3545; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; }
            .stat-card { background: white; border-radius: 8px; padding: 1.5rem; text-align: center; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌾 AgriWeb 2.0 - Dashboard</h1>
            <p>Bienvenue {{ user_email }} | <a href="/logout" style="color: white;">Déconnexion</a></p>
        </div>
        
        <div class="container">
            <!-- Statut abonnement -->
            <div class="subscription-card {% if user.active %}status-active{% else %}status-trial{% endif %}">
                <h2>📋 Votre Abonnement</h2>
                
                {% if subscription_info %}
                    <p><strong>Plan:</strong> {{ subscription_info.plan|title }}</p>
                    <p><strong>Statut:</strong> 
                        {% if subscription_info.status == 'active' %}
                            ✅ Actif
                        {% elif subscription_info.status == 'trialing' %}
                            🆓 Période d'essai
                        {% else %}
                            ⚠️ {{ subscription_info.status }}
                        {% endif %}
                    </p>
                    
                    {% if subscription_info.trial_end %}
                        <p><strong>Fin d'essai:</strong> {{ subscription_info.trial_end|timestamp_to_date }}</p>
                    {% endif %}
                    
                    <p><strong>Prochaine facturation:</strong> {{ subscription_info.current_period_end|timestamp_to_date }}</p>
                    <p><strong>Montant:</strong> {{ subscription_info.amount }}€/mois</p>
                    
                    <a href="/manage-subscription" class="btn">⚙️ Gérer l'abonnement</a>
                {% else %}
                    <p><strong>Statut:</strong> 🆓 Pas d'abonnement actif</p>
                    <p>Souscrivez à un abonnement pour accéder à toutes les fonctionnalités.</p>
                    <a href="/pricing" class="btn">🚀 Choisir un abonnement</a>
                {% endif %}
            </div>
            
            <!-- Statistiques d'usage -->
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>🔍 Recherches</h3>
                    <p style="font-size: 2rem; color: #007bff;">{{ user.searches_used or 0 }}</p>
                    <p>sur {{ user.searches_limit or '∞' }} autorisées</p>
                </div>
                
                <div class="stat-card">
                    <h3>📊 Rapports générés</h3>
                    <p style="font-size: 2rem; color: #28a745;">{{ user.reports_generated or 0 }}</p>
                    <p>ce mois-ci</p>
                </div>
                
                <div class="stat-card">
                    <h3>⏰ Dernière connexion</h3>
                    <p style="font-size: 1.2rem;">{{ user.last_login or 'Première connexion' }}</p>
                </div>
            </div>
            
            <!-- Actions rapides -->
            <div class="subscription-card">
                <h2>🚀 Actions Rapides</h2>
                <a href="/search" class="btn">🔍 Nouvelle recherche</a>
                <a href="/reports" class="btn">📊 Mes rapports</a>
                <a href="/api-docs" class="btn">📖 Documentation API</a>
                
                {% if subscription_info %}
                    <a href="/cancel-subscription" class="btn btn-danger">❌ Annuler l'abonnement</a>
                {% endif %}
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(
        dashboard_template,
        user=user,
        user_email=user_email,
        subscription_info=subscription_info
    )

if __name__ == '__main__':
    print("🚀 Démarrage AgriWeb 2.0 avec Paiements Stripe")
    print(f"💳 Stripe configuré: {'Test' if 'test' in STRIPE_PUBLISHABLE_KEY else 'Production'}")
    app.run(host='127.0.0.1', port=5000, debug=True)
