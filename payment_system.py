#!/usr/bin/env python3
"""
💳 SYSTÈME DE PAIEMENT - AgriWeb 2.0
Intégration Stripe pour les abonnements et gestion des essais
"""

import stripe
import os
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, session
from production_system import LicenseManager, ProductionConfig

# Configuration Stripe
stripe.api_key = "sk_test_..."  # À remplacer par votre clé Stripe

class PaymentManager:
    """Gestionnaire des paiements avec Stripe"""
    
    def __init__(self):
        self.license_manager = LicenseManager()
        
        # Configuration des produits Stripe
        self.stripe_products = {
            "basic": {
                "price_id": "price_basic_annual",  # À créer dans Stripe
                "amount": 29900,  # 299€ en centimes
                "currency": "eur",
                "interval": "year"
            },
            "professional": {
                "price_id": "price_professional_annual",
                "amount": 99900,  # 999€
                "currency": "eur", 
                "interval": "year"
            },
            "enterprise": {
                "price_id": "price_enterprise_annual",
                "amount": 299900,  # 2999€
                "currency": "eur",
                "interval": "year"
            }
        }
    
    def create_checkout_session(self, license_type, customer_email, trial_license_key=None):
        """Crée une session de paiement Stripe"""
        
        if license_type not in self.stripe_products:
            return {"error": "Type de licence invalide"}
        
        product = self.stripe_products[license_type]
        
        try:
            # Créer ou récupérer le client Stripe
            customers = stripe.Customer.list(email=customer_email, limit=1)
            if customers.data:
                customer = customers.data[0]
            else:
                customer = stripe.Customer.create(email=customer_email)
            
            # Session de checkout
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price': product["price_id"],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url='https://votre-domaine.com/payment/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='https://votre-domaine.com/payment/cancel',
                metadata={
                    'license_type': license_type,
                    'trial_license_key': trial_license_key or '',
                    'customer_email': customer_email
                }
            )
            
            return {
                "checkout_url": session.url,
                "session_id": session.id
            }
            
        except stripe.error.StripeError as e:
            return {"error": str(e)}
    
    def handle_successful_payment(self, session_id):
        """Traite un paiement réussi et active la licence"""
        
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                # Récupérer les métadonnées
                license_type = session.metadata.get('license_type')
                customer_email = session.metadata.get('customer_email')
                trial_license_key = session.metadata.get('trial_license_key')
                
                # Créer la nouvelle licence payée
                new_license = self.create_paid_license(
                    license_type, 
                    customer_email, 
                    session.customer,
                    session.subscription
                )
                
                # Désactiver l'ancienne licence d'essai si applicable
                if trial_license_key:
                    self.deactivate_trial_license(trial_license_key)
                
                return {
                    "success": True,
                    "license_key": new_license["license_key"],
                    "message": f"Abonnement {license_type} activé avec succès !"
                }
            else:
                return {"error": "Paiement non confirmé"}
                
        except stripe.error.StripeError as e:
            return {"error": str(e)}
    
    def create_paid_license(self, license_type, email, stripe_customer_id, stripe_subscription_id):
        """Crée une licence payée avec abonnement Stripe"""
        
        license_key = self.license_manager.generate_license_key()
        expires_at = datetime.now() + timedelta(days=365)  # 1 an
        
        # Enregistrer la licence avec les IDs Stripe
        conn = sqlite3.connect(self.license_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO licenses (
                license_key, email, license_type, expires_at, 
                stripe_customer_id, stripe_subscription_id, is_paid
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (license_key, email, license_type, expires_at, 
              stripe_customer_id, stripe_subscription_id, True))
        
        conn.commit()
        conn.close()
        
        return {"license_key": license_key, "expires_at": expires_at}
    
    def deactivate_trial_license(self, trial_license_key):
        """Désactive une licence d'essai"""
        
        conn = sqlite3.connect(self.license_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE licenses 
            SET is_active = 0, deactivated_at = CURRENT_TIMESTAMP
            WHERE license_key = ? AND license_type = 'trial'
        ''', (trial_license_key,))
        
        conn.commit()
        conn.close()
    
    def handle_webhook(self, payload, sig_header):
        """Traite les webhooks Stripe (renouvellements, annulations...)"""
        
        endpoint_secret = "whsec_..."  # Votre secret webhook Stripe
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            return {"error": "Invalid payload"}
        except stripe.error.SignatureVerificationError:
            return {"error": "Invalid signature"}
        
        # Traiter les événements importants
        if event['type'] == 'invoice.payment_succeeded':
            self.handle_subscription_renewal(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            self.handle_subscription_cancellation(event['data']['object'])
        
        return {"status": "success"}
    
    def handle_subscription_renewal(self, invoice):
        """Gère le renouvellement automatique d'abonnement"""
        
        subscription_id = invoice['subscription']
        
        # Étendre la licence pour 1 an de plus
        conn = sqlite3.connect(self.license_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE licenses 
            SET expires_at = datetime(expires_at, '+1 year')
            WHERE stripe_subscription_id = ? AND is_active = 1
        ''', (subscription_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Licence renouvelée pour l'abonnement {subscription_id}")
    
    def handle_subscription_cancellation(self, subscription):
        """Gère l'annulation d'abonnement"""
        
        subscription_id = subscription['id']
        
        # La licence reste active jusqu'à expiration
        # Mais on note l'annulation
        conn = sqlite3.connect(self.license_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE licenses 
            SET subscription_cancelled = 1, cancelled_at = CURRENT_TIMESTAMP
            WHERE stripe_subscription_id = ? AND is_active = 1
        ''', (subscription_id,))
        
        conn.commit()
        conn.close()
        
        print(f"📋 Abonnement annulé : {subscription_id}")

def create_payment_routes(app):
    """Ajoute les routes de paiement à l'application"""
    
    payment_manager = PaymentManager()
    
    @app.route('/pricing')
    def pricing_page():
        """Page de tarification avec boutons de paiement"""
        return render_template_string(PRICING_PAGE_TEMPLATE)
    
    @app.route('/api/payment/create-checkout', methods=['POST'])
    def create_checkout():
        """Crée une session de paiement Stripe"""
        
        data = request.get_json()
        license_type = data.get('license_type')
        customer_email = data.get('email')
        trial_license_key = session.get('license_key')  # Récupérer la licence d'essai
        
        if not license_type or not customer_email:
            return jsonify({"error": "Données manquantes"}), 400
        
        result = payment_manager.create_checkout_session(
            license_type, customer_email, trial_license_key
        )
        
        if "error" in result:
            return jsonify(result), 400
        
        return jsonify(result)
    
    @app.route('/payment/success')
    def payment_success():
        """Page de succès après paiement"""
        
        session_id = request.args.get('session_id')
        
        if not session_id:
            return "Session ID manquant", 400
        
        result = payment_manager.handle_successful_payment(session_id)
        
        if result.get("success"):
            # Mettre à jour la session avec la nouvelle licence
            session['license_key'] = result["license_key"]
            session['paid_user'] = True
            
            return render_template_string(SUCCESS_PAGE_TEMPLATE, 
                                        license_key=result["license_key"])
        else:
            return f"Erreur : {result.get('error')}", 400
    
    @app.route('/payment/cancel')
    def payment_cancel():
        """Page d'annulation de paiement"""
        return render_template_string(CANCEL_PAGE_TEMPLATE)
    
    @app.route('/api/stripe/webhook', methods=['POST'])
    def stripe_webhook():
        """Endpoint pour les webhooks Stripe"""
        
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        
        result = payment_manager.handle_webhook(payload, sig_header)
        
        if "error" in result:
            return jsonify(result), 400
        
        return jsonify(result)
    
    @app.route('/api/subscription/cancel', methods=['POST'])
    def cancel_subscription():
        """Permet d'annuler un abonnement"""
        
        license_key = session.get('license_key')
        
        if not license_key:
            return jsonify({"error": "Licence requise"}), 401
        
        # Récupérer l'ID d'abonnement Stripe
        conn = sqlite3.connect(payment_manager.license_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT stripe_subscription_id FROM licenses 
            WHERE license_key = ? AND is_active = 1
        ''', (license_key,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({"error": "Abonnement non trouvé"}), 404
        
        subscription_id = result[0]
        
        try:
            # Annuler l'abonnement dans Stripe
            stripe.Subscription.delete(subscription_id)
            
            return jsonify({
                "success": True,
                "message": "Abonnement annulé. Votre licence reste active jusqu'à expiration."
            })
            
        except stripe.error.StripeError as e:
            return jsonify({"error": str(e)}), 400

# Templates HTML pour les pages de paiement

PRICING_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgriWeb 2.0 - Tarifs</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://js.stripe.com/v3/"></script>
    <style>
        .pricing-card { transition: transform 0.3s; border: 2px solid transparent; }
        .pricing-card:hover { transform: translateY(-5px); }
        .pricing-card.popular { border-color: #0d6efd; position: relative; }
        .popular-badge { position: absolute; top: -10px; right: 20px; background: #0d6efd; color: white; padding: 5px 15px; border-radius: 15px; }
    </style>
</head>
<body>
    <div class="container my-5">
        <div class="text-center mb-5">
            <h1>Choisissez votre plan AgriWeb 2.0</h1>
            <p class="lead">Démarrez avec un essai gratuit, passez au plan qui vous convient</p>
        </div>
        
        <div class="row justify-content-center">
            <!-- Plan Basic -->
            <div class="col-md-4 mb-4">
                <div class="card pricing-card h-100">
                    <div class="card-header text-center bg-primary text-white">
                        <h4>Basic</h4>
                        <h2>299€<small>/an</small></h2>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li>✅ 100 communes</li>
                            <li>✅ 500 rapports/jour</li>
                            <li>✅ Export Excel/PDF</li>
                            <li>✅ Support email</li>
                        </ul>
                        <button class="btn btn-primary w-100" onclick="subscribe('basic')">
                            Choisir Basic
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Plan Professional (Populaire) -->
            <div class="col-md-4 mb-4">
                <div class="card pricing-card popular h-100">
                    <div class="popular-badge">⭐ Populaire</div>
                    <div class="card-header text-center bg-warning text-dark">
                        <h4>Professional</h4>
                        <h2>999€<small>/an</small></h2>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li>✅ 1000 communes</li>
                            <li>✅ 2000 rapports/jour</li>
                            <li>✅ Accès API complet</li>
                            <li>✅ Rapports personnalisés</li>
                            <li>✅ Support prioritaire</li>
                        </ul>
                        <button class="btn btn-warning w-100" onclick="subscribe('professional')">
                            Choisir Professional
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Plan Enterprise -->
            <div class="col-md-4 mb-4">
                <div class="card pricing-card h-100">
                    <div class="card-header text-center bg-dark text-white">
                        <h4>Enterprise</h4>
                        <h2>2999€<small>/an</small></h2>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li>✅ Illimité</li>
                            <li>✅ GeoServer dédié</li>
                            <li>✅ Marque blanche</li>
                            <li>✅ Formation incluse</li>
                            <li>✅ Support 24/7</li>
                        </ul>
                        <button class="btn btn-dark w-100" onclick="subscribe('enterprise')">
                            Choisir Enterprise
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="text-center mt-5">
            <p>💳 Paiement sécurisé par Stripe • 🔒 Données protégées • 📞 Support technique inclus</p>
            <p><small>Tous les plans incluent 30 jours de garantie satisfait ou remboursé</small></p>
        </div>
    </div>
    
    <script>
        async function subscribe(planType) {
            // Récupérer l'email depuis la session ou demander à l'utilisateur
            const email = prompt("Votre email professionnel :");
            if (!email) return;
            
            try {
                const response = await fetch('/api/payment/create-checkout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        license_type: planType,
                        email: email
                    })
                });
                
                const result = await response.json();
                
                if (result.checkout_url) {
                    // Rediriger vers Stripe Checkout
                    window.location.href = result.checkout_url;
                } else {
                    alert('Erreur : ' + (result.error || 'Erreur inconnue'));
                }
            } catch (error) {
                alert('Erreur de connexion : ' + error.message);
            }
        }
    </script>
</body>
</html>
'''

SUCCESS_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Paiement réussi - AgriWeb 2.0</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6 text-center">
                <div class="card">
                    <div class="card-body">
                        <h1 class="text-success">🎉 Paiement réussi !</h1>
                        <p class="lead">Votre abonnement AgriWeb 2.0 est maintenant actif.</p>
                        <div class="alert alert-info">
                            <strong>Votre clé de licence :</strong><br>
                            <code>{{ license_key }}</code>
                        </div>
                        <p>Un email de confirmation a été envoyé avec tous les détails.</p>
                        <a href="/" class="btn btn-primary btn-lg">
                            Accéder à l'application
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

CANCEL_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Paiement annulé - AgriWeb 2.0</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6 text-center">
                <div class="card">
                    <div class="card-body">
                        <h1 class="text-warning">⚠️ Paiement annulé</h1>
                        <p>Votre paiement a été annulé. Aucun montant n'a été débité.</p>
                        <p>Vous pouvez continuer à utiliser votre essai gratuit ou choisir un autre plan.</p>
                        <a href="/pricing" class="btn btn-primary">Voir les tarifs</a>
                        <a href="/" class="btn btn-secondary">Retour à l'accueil</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

def setup_stripe_products():
    """Configure les produits dans Stripe (à exécuter une fois)"""
    
    print("💳 Configuration des produits Stripe...")
    
    products = {
        "basic": {
            "name": "AgriWeb 2.0 Basic",
            "description": "Plan Basic - 100 communes, 500 rapports/jour",
            "amount": 29900,
            "currency": "eur"
        },
        "professional": {
            "name": "AgriWeb 2.0 Professional", 
            "description": "Plan Professional - 1000 communes, API complète",
            "amount": 99900,
            "currency": "eur"
        },
        "enterprise": {
            "name": "AgriWeb 2.0 Enterprise",
            "description": "Plan Enterprise - Illimité, GeoServer dédié",
            "amount": 299900,
            "currency": "eur"
        }
    }
    
    for key, product_data in products.items():
        try:
            # Créer le produit
            product = stripe.Product.create(
                name=product_data["name"],
                description=product_data["description"]
            )
            
            # Créer le prix (abonnement annuel)
            price = stripe.Price.create(
                product=product.id,
                unit_amount=product_data["amount"],
                currency=product_data["currency"],
                recurring={"interval": "year"}
            )
            
            print(f"✅ Produit {key} créé : {price.id}")
            
        except stripe.error.StripeError as e:
            print(f"❌ Erreur pour {key} : {e}")

if __name__ == "__main__":
    print("💳 Configuration du système de paiement Stripe")
    
    # Configurer les produits Stripe (à faire une seule fois)
    # setup_stripe_products()
    
    print("""
🎉 Système de paiement prêt !

Fonctionnalités :
- ✅ Intégration Stripe Checkout
- ✅ Gestion des abonnements
- ✅ Webhooks pour renouvellements
- ✅ Passage de l'essai au plan payant
- ✅ Interface de tarification

Pour activer :
1. Configurez vos clés Stripe (API et webhooks)
2. Exécutez setup_stripe_products() une fois
3. Intégrez les routes dans votre application
4. Testez avec les clés de test Stripe

URLs :
- /pricing - Page de tarification
- /api/payment/create-checkout - Création session paiement
- /payment/success - Confirmation paiement
- /api/stripe/webhook - Webhooks Stripe
""")
