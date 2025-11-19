# Configuration Stripe pour AgriWeb 2.0
import stripe
import os
import json
from datetime import datetime, timedelta
from flask import jsonify, request, session

class StripePaymentManager:
    """Gestionnaire de paiements Stripe pour AgriWeb 2.0"""
    
    def __init__(self):
        # Configuration Stripe
        self.setup_stripe()
        
        # Plans tarifaires (IDs à créer dans le dashboard Stripe)
        self.pricing_plans = {
            'starter': {
                'price_id': 'price_agriweb_starter_monthly',  # À remplacer par l'ID réel
                'amount': 9900,  # 99.00€ en centimes
                'currency': 'eur',
                'interval': 'month',
                'searches_limit': 500,
                'features': ['basic_data', 'pdf_reports', 'email_support']
            },
            'professional': {
                'price_id': 'price_agriweb_pro_monthly',  # À remplacer par l'ID réel
                'amount': 29900,  # 299.00€ en centimes
                'currency': 'eur',
                'interval': 'month',
                'searches_limit': 2000,
                'features': ['all_layers', 'api_access', 'priority_support', 'advanced_reports']
            },
            'enterprise': {
                'price_id': 'price_agriweb_enterprise_monthly',  # À remplacer par l'ID réel
                'amount': 59900,  # 599.00€ en centimes
                'currency': 'eur',
                'interval': 'month',
                'searches_limit': -1,  # Illimité
                'features': ['unlimited_searches', '24_7_support', 'white_label', 'custom_integration']
            }
        }
        
        self.trial_period_days = 15
    
    def setup_stripe(self):
        """Configuration initiale de Stripe"""
        # Clés Stripe (à définir dans les variables d'environnement)
        self.stripe_secret_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_...')  # Remplacer par votre clé
        self.stripe_publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY', 'pk_test_...')  # Remplacer par votre clé
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_...')  # Remplacer par votre secret
        
        stripe.api_key = self.stripe_secret_key
        
        print(f"🔧 Stripe configuré - Mode: {'Test' if 'test' in self.stripe_secret_key else 'Production'}")
    
    def create_or_get_customer(self, email: str, name: str = None, company: str = None):
        """Crée ou récupère un client Stripe"""
        try:
            # Rechercher client existant
            customers = stripe.Customer.list(email=email, limit=1)
            
            if customers.data:
                customer = customers.data[0]
                print(f"✅ Client Stripe existant trouvé: {customer.id}")
                return customer
            
            # Créer nouveau client
            customer_data = {
                'email': email,
                'metadata': {
                    'source': 'agriweb_2.0',
                    'signup_date': datetime.now().isoformat()
                }
            }
            
            if name:
                customer_data['name'] = name
            if company:
                customer_data['description'] = f"Entreprise: {company}"
                customer_data['metadata']['company'] = company
            
            customer = stripe.Customer.create(**customer_data)
            print(f"✅ Nouveau client Stripe créé: {customer.id}")
            
            return customer
            
        except stripe.error.StripeError as e:
            print(f"❌ Erreur Stripe create_customer: {e}")
            return None
    
    def create_checkout_session(self, customer_email: str, plan: str, 
                              success_url: str = None, cancel_url: str = None):
        """Crée une session de paiement Stripe Checkout"""
        try:
            if plan not in self.pricing_plans:
                raise ValueError(f"Plan invalide: {plan}")
            
            plan_config = self.pricing_plans[plan]
            
            # URLs par défaut
            if not success_url:
                success_url = f"{request.url_root}payment/success?session_id={{CHECKOUT_SESSION_ID}}"
            if not cancel_url:
                cancel_url = f"{request.url_root}payment/cancel"
            
            # Configuration de la session
            session_config = {
                'customer_email': customer_email,
                'payment_method_types': ['card'],
                'line_items': [{
                    'price': plan_config['price_id'],
                    'quantity': 1,
                }],
                'mode': 'subscription',
                'success_url': success_url,
                'cancel_url': cancel_url,
                'subscription_data': {
                    'trial_period_days': self.trial_period_days,
                    'metadata': {
                        'plan': plan,
                        'source': 'agriweb_checkout',
                        'created_at': datetime.now().isoformat()
                    }
                },
                'metadata': {
                    'plan': plan,
                    'customer_email': customer_email
                }
            }
            
            checkout_session = stripe.checkout.Session.create(**session_config)
            
            print(f"✅ Session checkout créée: {checkout_session.id} pour plan {plan}")
            
            return {
                'success': True,
                'session_id': checkout_session.id,
                'checkout_url': checkout_session.url,
                'plan': plan
            }
            
        except Exception as e:
            print(f"❌ Erreur create_checkout_session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_successful_checkout(self, session_id: str):
        """Traite un checkout réussi"""
        try:
            # Récupérer la session
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            
            if not checkout_session.subscription:
                return {'success': False, 'error': 'Pas d\'abonnement trouvé'}
            
            # Récupérer l'abonnement
            subscription = stripe.Subscription.retrieve(checkout_session.subscription)
            
            # Récupérer le client
            customer = stripe.Customer.retrieve(checkout_session.customer)
            
            result = {
                'success': True,
                'customer_email': customer.email,
                'subscription_id': subscription.id,
                'plan': subscription.metadata.get('plan'),
                'status': subscription.status,
                'trial_end': subscription.trial_end,
                'current_period_end': subscription.current_period_end,
                'amount': subscription.items.data[0].price.unit_amount / 100  # Conversion centimes -> euros
            }
            
            print(f"✅ Checkout traité: {customer.email} - Plan {result['plan']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Erreur handle_checkout: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_subscription_info(self, subscription_id: str):
        """Récupère les informations d'un abonnement"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            customer = stripe.Customer.retrieve(subscription.customer)
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'customer_email': customer.email,
                'plan': subscription.metadata.get('plan'),
                'status': subscription.status,
                'trial_end': subscription.trial_end,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'amount': subscription.items.data[0].price.unit_amount / 100
            }
            
        except Exception as e:
            print(f"❌ Erreur get_subscription_info: {e}")
            return {'success': False, 'error': str(e)}
    
    def cancel_subscription(self, subscription_id: str, immediate: bool = False):
        """Annule un abonnement"""
        try:
            if immediate:
                # Annulation immédiate
                subscription = stripe.Subscription.delete(subscription_id)
                print(f"✅ Abonnement annulé immédiatement: {subscription_id}")
            else:
                # Annulation en fin de période
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
                print(f"✅ Abonnement marqué pour annulation: {subscription_id}")
            
            return {'success': True, 'subscription': subscription}
            
        except Exception as e:
            print(f"❌ Erreur cancel_subscription: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_webhook(self, payload: str, signature: str):
        """Traite un webhook Stripe"""
        try:
            # Vérifier la signature
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            print(f"📡 Webhook reçu: {event['type']}")
            
            # Traitement selon le type d'événement
            if event['type'] == 'checkout.session.completed':
                return self._handle_checkout_completed(event['data']['object'])
                
            elif event['type'] == 'invoice.payment_succeeded':
                return self._handle_payment_succeeded(event['data']['object'])
                
            elif event['type'] == 'invoice.payment_failed':
                return self._handle_payment_failed(event['data']['object'])
                
            elif event['type'] == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(event['data']['object'])
                
            elif event['type'] == 'customer.subscription.updated':
                return self._handle_subscription_updated(event['data']['object'])
            
            return {'success': True, 'processed': False}
            
        except stripe.error.SignatureVerificationError:
            print("❌ Signature webhook invalide")
            return {'success': False, 'error': 'Invalid signature'}
            
        except Exception as e:
            print(f"❌ Erreur webhook: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_checkout_completed(self, session):
        """Traite un checkout complété"""
        print(f"✅ Checkout complété: {session['id']}")
        return {'success': True, 'action': 'checkout_completed'}
    
    def _handle_payment_succeeded(self, invoice):
        """Traite un paiement réussi"""
        subscription_id = invoice.get('subscription')
        if subscription_id:
            print(f"✅ Paiement réussi pour abonnement: {subscription_id}")
            # Ici, vous pouvez réactiver l'accès utilisateur si suspendu
        return {'success': True, 'action': 'payment_succeeded'}
    
    def _handle_payment_failed(self, invoice):
        """Traite un paiement échoué"""
        subscription_id = invoice.get('subscription')
        if subscription_id:
            print(f"⚠️ Paiement échoué pour abonnement: {subscription_id}")
            # Ici, vous pouvez envoyer une notification ou suspendre l'accès
        return {'success': True, 'action': 'payment_failed'}
    
    def _handle_subscription_deleted(self, subscription):
        """Traite une suppression d'abonnement"""
        print(f"❌ Abonnement supprimé: {subscription['id']}")
        # Ici, vous pouvez désactiver l'accès utilisateur
        return {'success': True, 'action': 'subscription_deleted'}
    
    def _handle_subscription_updated(self, subscription):
        """Traite une mise à jour d'abonnement"""
        print(f"🔄 Abonnement mis à jour: {subscription['id']}")
        return {'success': True, 'action': 'subscription_updated'}
    
    def get_plan_limits(self, plan: str):
        """Retourne les limites d'un plan"""
        if plan in self.pricing_plans:
            return {
                'searches_limit': self.pricing_plans[plan]['searches_limit'],
                'features': self.pricing_plans[plan]['features'],
                'amount': self.pricing_plans[plan]['amount'] / 100
            }
        return None
    
    def validate_plan_access(self, plan: str, feature: str):
        """Vérifie si un plan donne accès à une fonctionnalité"""
        if plan in self.pricing_plans:
            return feature in self.pricing_plans[plan]['features']
        return False
    
    def create_customer_portal_session(self, customer_id: str, return_url: str = None):
        """Crée une session du portail client Stripe"""
        try:
            if not return_url:
                return_url = f"{request.url_root}dashboard"
            
            portal_session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            
            return {
                'success': True,
                'portal_url': portal_session.url
            }
            
        except Exception as e:
            print(f"❌ Erreur portail client: {e}")
            return {'success': False, 'error': str(e)}

# Instance globale
stripe_payment_manager = StripePaymentManager()

# Test de la configuration
if __name__ == "__main__":
    print("🧪 Test de configuration Stripe...")
    
    # Test basique
    try:
        # Test de connexion à l'API Stripe
        stripe.Account.retrieve()
        print("✅ Connexion Stripe OK")
        
        # Affichage de la configuration
        print(f"📋 Plans configurés: {list(stripe_payment_manager.pricing_plans.keys())}")
        print(f"🆓 Période d'essai: {stripe_payment_manager.trial_period_days} jours")
        
    except Exception as e:
        print(f"❌ Erreur de configuration Stripe: {e}")
        print("💡 Vérifiez vos clés API dans les variables d'environnement")
