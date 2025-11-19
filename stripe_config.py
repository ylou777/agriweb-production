"""
Configuration complète Stripe pour AgriWeb Pro
"""
import os
import stripe
from datetime import datetime, timedelta

class StripeConfig:
    """Configuration centralisée pour Stripe"""
    
    # Clés Stripe (en test pour le moment)
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', 'pk_test_51QRwd8P3NsW4P31F90DJhd1FHB8C0H5o62yQGrtPu6x8csTiynXi65gVWQge4fLMnRkNTkYzfL3f1bRKqs3uLS8s00sOsrFAve')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_51QRwd8P3NsW4P31FcUqlpArJbOXtML95f3UQCjFbgLkB5MvmJEKKJECE3Onasv9tNXTQ9SVbIBxQnETiHmIIHVO000QqwxzF7m')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_your_webhook_secret_here')
    
    # Configuration des plans
    PRICING_PLANS = {
        'basic': {
            'name': 'Basic',
            'price': 35,  # euros
            'price_id': 'price_basic_monthly',  # À créer dans Stripe
            'features': [
                'Recherche par coordonnées uniquement',
                'Rapports de base',
                'Export PDF',
                'Support email'
            ],
            'limits': {
                'coordinates_search_only': True,
                'advanced_features': False,
                'users': 1
            }
        },
        'professional': {
            'name': 'Professional',
            'price': 199,  # euros
            'price_id': 'price_professional_monthly',  # À créer dans Stripe
            'features': [
                'Toutes les fonctionnalités',
                'Recherches illimitées',
                'Rapports complets',
                'Exports avancés',
                'Support prioritaire',
                '1 poste utilisateur'
            ],
            'limits': {
                'coordinates_search_only': False,
                'advanced_features': True,
                'users': 1
            }
        },
        'team': {
            'name': 'Team',
            'price': 299,  # euros
            'price_id': 'price_team_monthly',  # À créer dans Stripe
            'features': [
                'Toutes les fonctionnalités Professional',
                'Recherches illimitées',
                'Rapports complets',
                'Exports avancés',
                'Support prioritaire',
                '3 postes utilisateurs',
                'Gestion d\'équipe'
            ],
            'limits': {
                'coordinates_search_only': False,
                'advanced_features': True,
                'users': 3
            }
        },
        'enterprise': {
            'name': 'Enterprise',
            'price': 'Sur devis',  # Prix personnalisé
            'price_id': 'price_enterprise_custom',  # À créer dans Stripe
            'features': [
                'Toutes les fonctionnalités Team',
                'Utilisateurs illimités',
                'Personnalisation complète',
                'Support 24/7',
                'White label',
                'Intégrations sur mesure',
                'Account manager dédié',
                'Formation équipe'
            ],
            'limits': {
                'coordinates_search_only': False,
                'advanced_features': True,
                'users': -1,  # Illimité
                'white_label': True,
                'custom_integration': True
            }
        }
    }
    
    # Période d'essai
    TRIAL_PERIOD_DAYS = 7
    
    @classmethod
    def initialize(cls):
        """Initialise Stripe avec la clé secrète"""
        stripe.api_key = cls.STRIPE_SECRET_KEY
        print(f"✅ Stripe initialisé avec la clé: {cls.STRIPE_SECRET_KEY[:7]}...")
        return True

class StripeManager:
    """Gestionnaire principal pour les opérations Stripe"""
    
    def __init__(self, database_callback=None):
        """
        Initialise le gestionnaire Stripe
        database_callback: fonction pour mettre à jour la base de données
        Signature: callback(email, subscription_type, status='active')
        """
        self.config = StripeConfig()
        self.database_callback = database_callback
        StripeConfig.initialize()
    
    def create_customer(self, email, name=None, company=None):
        """Crée un client Stripe"""
        try:
            customer_data = {'email': email}
            if name:
                customer_data['name'] = name
            if company:
                customer_data['metadata'] = {'company': company}
            
            customer = stripe.Customer.create(**customer_data)
            print(f"✅ Client Stripe créé: {customer.id} pour {email}")
            return customer.id
        except Exception as e:
            print(f"❌ Erreur création client: {e}")
            return None
    
    def create_checkout_session(self, customer_email, plan, success_url=None, cancel_url=None):
        """Crée une session de checkout Stripe"""
        try:
            if plan not in self.config.PRICING_PLANS:
                raise ValueError(f"Plan invalide: {plan}")
            
            plan_config = self.config.PRICING_PLANS[plan]
            
            # Le plan Enterprise nécessite un contact commercial
            if plan == 'enterprise':
                return {
                    'success': False,
                    'error': 'Le plan Enterprise nécessite un devis personnalisé. Veuillez nous contacter.'
                }
            
            # URLs par défaut
            base_url = "http://127.0.0.1:5000"  # À adapter selon l'environnement
            if not success_url:
                success_url = f"{base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
            if not cancel_url:
                cancel_url = f"{base_url}/payment/cancel"
            
            # Création de la session
            session = stripe.checkout.Session.create(
                customer_email=customer_email,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': f'AgriWeb Pro - {plan_config["name"]}',
                            'description': ', '.join(plan_config['features'][:3])  # Limiter la description
                        },
                        'unit_amount': plan_config['price'] * 100,  # En centimes
                        'recurring': {
                            'interval': 'month'
                        }
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                subscription_data={
                    'trial_period_days': self.config.TRIAL_PERIOD_DAYS,
                    'metadata': {
                        'plan': plan,
                        'customer_email': customer_email,
                        'created_at': datetime.now().isoformat(),
                        'max_users': plan_config['limits']['users']
                    }
                },
                metadata={
                    'plan': plan,
                    'customer_email': customer_email,
                    'max_users': plan_config['limits']['users']
                }
            )
            
            print(f"✅ Session checkout créée: {session.id} pour plan {plan}")
            return {
                'success': True,
                'session_id': session.id,
                'checkout_url': session.url,
                'plan': plan
            }
            
        except Exception as e:
            print(f"❌ Erreur checkout: {e}")
            return {'success': False, 'error': str(e)}
    
    def handle_webhook(self, payload, signature):
        """Traite les webhooks Stripe"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.config.STRIPE_WEBHOOK_SECRET
            )
            
            print(f"📡 Webhook reçu: {event['type']}")
            
            if event['type'] == 'checkout.session.completed':
                return self._handle_checkout_completed(event['data']['object'])
            
            elif event['type'] == 'invoice.payment_succeeded':
                return self._handle_payment_succeeded(event['data']['object'])
            
            elif event['type'] == 'invoice.payment_failed':
                return self._handle_payment_failed(event['data']['object'])
            
            elif event['type'] == 'customer.subscription.deleted':
                return self._handle_subscription_cancelled(event['data']['object'])
            
            return {'success': True, 'processed': False}
            
        except stripe.error.SignatureVerificationError:
            print("❌ Signature webhook invalide")
            return {'success': False, 'error': 'Invalid signature'}
        except Exception as e:
            print(f"❌ Erreur webhook: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_checkout_completed(self, session):
        """Traite un checkout complété"""
        customer_email = session.get('customer_details', {}).get('email')
        subscription_id = session.get('subscription')
        plan = session.get('metadata', {}).get('plan')
        
        print(f"✅ Checkout complété: {customer_email} - Plan {plan} - Abonnement {subscription_id}")
        
        # Activer l'abonnement dans la base de données
        if self.database_callback and customer_email and plan:
            try:
                self.database_callback(customer_email, status='active', subscription_type=plan)
                print(f"✅ Abonnement {plan} activé en base pour {customer_email}")
            except Exception as e:
                print(f"❌ Erreur activation base de données: {e}")
        
        return {'success': True, 'action': 'checkout_completed'}
    
    def _handle_payment_succeeded(self, invoice):
        """Traite un paiement réussi"""
        subscription_id = invoice.get('subscription')
        customer_id = invoice.get('customer')
        
        if subscription_id:
            print(f"✅ Paiement réussi pour abonnement: {subscription_id}")
            # Réactiver l'accès si suspendu
        
        return {'success': True, 'action': 'payment_succeeded'}
    
    def _handle_payment_failed(self, invoice):
        """Traite un paiement échoué"""
        subscription_id = invoice.get('subscription')
        customer_id = invoice.get('customer')
        
        print(f"❌ Paiement échoué pour abonnement: {subscription_id}")
        # Envoyer une notification, suspendre l'accès après X échecs
        
        return {'success': True, 'action': 'payment_failed'}
    
    def _handle_subscription_cancelled(self, subscription):
        """Traite une annulation d'abonnement"""
        subscription_id = subscription.get('id')
        customer_id = subscription.get('customer')
        
        print(f"❌ Abonnement annulé: {subscription_id}")
        # Désactiver l'accès utilisateur
        
        return {'success': True, 'action': 'subscription_cancelled'}
    
    def get_subscription_info(self, subscription_id):
        """Récupère les informations d'un abonnement"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                'id': subscription.id,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end,
                'trial_end': subscription.trial_end,
                'plan': subscription.metadata.get('plan'),
                'customer': subscription.customer
            }
        except Exception as e:
            print(f"❌ Erreur récupération abonnement: {e}")
            return None
    
    def cancel_subscription(self, subscription_id):
        """Annule un abonnement"""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            print(f"✅ Abonnement {subscription_id} sera annulé à la fin de la période")
            return True
        except Exception as e:
            print(f"❌ Erreur annulation abonnement: {e}")
            return False
    
    def create_portal_session(self, customer_id, return_url=None):
        """Crée une session du portail client"""
        try:
            if not return_url:
                return_url = "http://127.0.0.1:5000/profile"
            
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
