# 💳 Système de Paiement AgriWeb 2.0 - Solution Complète

## 🎯 Enjeux du Paiement pour AgriWeb 2.0

### Besoins Identifiés
- **Abonnements récurrents** (mensuel/annuel)
- **Essais gratuits** avec conversion automatique
- **Niveaux de service** (Starter, Pro, Enterprise)
- **Paiements sécurisés** (conformité PCI DSS)
- **Facturation automatique** avec relances
- **Gestion des impayés** et suspensions

## 🏗️ Architecture Paiement Recommandée

### Option 1 : Stripe (Recommandé)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AgriWeb 2.0   │    │     Stripe      │    │   Comptes       │
│   (Interface)   │────│   (Paiements)   │────│   Bancaires     │
│   + Webhooks    │    │   + Facturation │    │   + Factures    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Avantages Stripe :**
- ✅ Abonnements natifs
- ✅ Essais gratuits intégrés
- ✅ Webhooks fiables
- ✅ Conformité PCI DSS
- ✅ Support multi-devises
- ✅ Facturation automatique

### Option 2 : PayPal Business (Alternative)
```
┌─────────────────┐    ┌─────────────────┐
│   AgriWeb 2.0   │    │     PayPal      │
│   (Interface)   │────│   Subscriptions │
│   + IPN         │    │   + Billing     │
└─────────────────┘    └─────────────────┘
```

**Avantages PayPal :**
- ✅ Reconnaissance client
- ✅ Pas de carte obligatoire
- ✅ Protection vendeur
- ❌ Interface moins moderne

## 💰 Modèles Tarifaires Suggérés

### Grille Tarifaire Competitive
```
🆓 ESSAI GRATUIT
• 15 jours
• 50 recherches max
• Toutes fonctionnalités
• Support email

💼 STARTER - 99€/mois
• 500 recherches/mois
• Données de base
• Support email
• Rapports PDF

🚀 PROFESSIONAL - 299€/mois
• 2000 recherches/mois
• Toutes les couches
• Support prioritaire
• API access
• Rapports avancés

🏢 ENTERPRISE - 599€/mois
• Recherches illimitées
• Support 24/7
• White label
• Intégration personnalisée
• Account manager
```

### Calculs de Rentabilité
```
Coûts fixes mensuels:
- Infrastructure GeoServer: 500€
- Stripe fees (3%): Variable
- Support/Dev: 1000€
Total fixe: 1500€/mois

Seuil rentabilité:
- 2 clients Enterprise: 1198€
- OU 5 clients Pro: 1495€  
- OU 15 clients Starter: 1485€

Objectif réaliste: 50 clients mixtes = 8000€/mois
```

## 🔧 Implémentation Technique Stripe

### 1. Configuration Stripe
```python
# stripe_config.py
import stripe
import os
from datetime import datetime, timedelta

class StripeManager:
    def __init__(self):
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        # IDs des produits Stripe (à créer dans le dashboard)
        self.products = {
            'starter': 'price_starter_monthly',    # 99€/mois
            'professional': 'price_pro_monthly',  # 299€/mois  
            'enterprise': 'price_ent_monthly'     # 599€/mois
        }
        
        self.trial_days = 15  # Essai gratuit
    
    def create_customer(self, email: str, name: str, company: str = None) -> str:
        """Crée un client Stripe"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    'company': company or '',
                    'source': 'agriweb_2.0'
                }
            )
            return customer.id
        except Exception as e:
            print(f"Erreur création client Stripe: {e}")
            return None
    
    def create_subscription(self, customer_id: str, plan: str, trial: bool = True) -> dict:
        """Crée un abonnement avec essai gratuit"""
        try:
            price_id = self.products.get(plan)
            if not price_id:
                raise ValueError(f"Plan inconnu: {plan}")
            
            subscription_data = {
                'customer': customer_id,
                'items': [{'price': price_id}],
                'metadata': {
                    'plan': plan,
                    'created_from': 'agriweb_signup'
                }
            }
            
            # Essai gratuit
            if trial:
                subscription_data['trial_period_days'] = self.trial_days
            
            subscription = stripe.Subscription.create(**subscription_data)
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'status': subscription.status,
                'trial_end': subscription.trial_end,
                'current_period_end': subscription.current_period_end
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_checkout_session(self, customer_id: str, plan: str, success_url: str, cancel_url: str) -> str:
        """Crée une session de paiement Stripe Checkout"""
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': self.products[plan],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                subscription_data={
                    'trial_period_days': self.trial_days,
                    'metadata': {
                        'plan': plan,
                        'source': 'agriweb_checkout'
                    }
                }
            )
            return session.url
        except Exception as e:
            print(f"Erreur checkout session: {e}")
            return None
    
    def get_subscription_status(self, subscription_id: str) -> dict:
        """Récupère le statut d'un abonnement"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                'status': subscription.status,
                'current_period_end': subscription.current_period_end,
                'trial_end': subscription.trial_end,
                'plan': subscription.metadata.get('plan'),
                'cancel_at_period_end': subscription.cancel_at_period_end
            }
        except Exception as e:
            return {'error': str(e)}
    
    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> bool:
        """Annule un abonnement"""
        try:
            if at_period_end:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                stripe.Subscription.delete(subscription_id)
            return True
        except Exception as e:
            print(f"Erreur annulation: {e}")
            return False

# Instance globale
stripe_manager = StripeManager()
```

### 2. Intégration dans l'API AgriWeb
```python
# Dans production_commercial.py - Ajouter ces routes

@app.route('/api/payment/create-checkout', methods=['POST'])
def create_checkout_session():
    """Crée une session de paiement Stripe"""
    if not session.get('authenticated'):
        return jsonify({"error": "Non autorisé"}), 401
    
    try:
        data = request.get_json()
        plan = data.get('plan')  # starter, professional, enterprise
        
        if plan not in ['starter', 'professional', 'enterprise']:
            return jsonify({"error": "Plan invalide"}), 400
        
        user_data = session.get('user_data', {})
        email = user_data.get('email')
        name = user_data.get('name')
        company = user_data.get('company')
        
        # Créer client Stripe si nécessaire
        stripe_customer_id = user_data.get('stripe_customer_id')
        if not stripe_customer_id:
            stripe_customer_id = stripe_manager.create_customer(email, name, company)
            if stripe_customer_id:
                # Sauvegarder l'ID client dans la base
                user_manager.update_user_stripe_id(email, stripe_customer_id)
        
        # URLs de retour
        success_url = request.url_root + 'payment/success?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = request.url_root + 'payment/cancel'
        
        # Créer session checkout
        checkout_url = stripe_manager.create_checkout_session(
            stripe_customer_id, 
            plan, 
            success_url, 
            cancel_url
        )
        
        if checkout_url:
            return jsonify({
                "success": True,
                "checkout_url": checkout_url,
                "plan": plan
            })
        else:
            return jsonify({"error": "Erreur création session"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/payment/success')
def payment_success():
    """Page de confirmation après paiement réussi"""
    session_id = request.args.get('session_id')
    
    if session_id:
        try:
            # Récupérer les détails de la session
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            subscription_id = checkout_session.subscription
            customer_id = checkout_session.customer
            
            # Mettre à jour l'utilisateur avec l'abonnement
            user_email = session.get('user_data', {}).get('email')
            if user_email:
                user_manager.activate_subscription(user_email, subscription_id)
            
            return render_template_string(PAYMENT_SUCCESS_TEMPLATE, 
                                        subscription_id=subscription_id)
        except Exception as e:
            return f"Erreur: {e}", 500
    
    return "Session invalide", 400

@app.route('/api/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Webhook Stripe pour événements d'abonnement"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_manager.webhook_secret
        )
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400
    
    # Traitement des événements
    if event['type'] == 'invoice.payment_succeeded':
        # Paiement réussi - activer/renouveler l'abonnement
        subscription_id = event['data']['object']['subscription']
        handle_payment_success(subscription_id)
        
    elif event['type'] == 'invoice.payment_failed':
        # Paiement échoué - avertir utilisateur
        subscription_id = event['data']['object']['subscription']
        handle_payment_failed(subscription_id)
        
    elif event['type'] == 'customer.subscription.deleted':
        # Abonnement annulé - désactiver accès
        subscription_id = event['data']['object']['id']
        handle_subscription_cancelled(subscription_id)
    
    return "Success", 200

def handle_payment_success(subscription_id: str):
    """Traite un paiement réussi"""
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        customer_id = subscription.customer
        customer = stripe.Customer.retrieve(customer_id)
        
        # Trouver l'utilisateur par email
        user_email = customer.email
        if user_email:
            # Activer l'abonnement
            user_manager.activate_subscription(user_email, subscription_id)
            
            # Réinitialiser les compteurs
            user_manager.reset_usage_counters(user_email)
            
            print(f"✅ Paiement réussi pour {user_email}")
            
    except Exception as e:
        print(f"❌ Erreur traitement paiement: {e}")

def handle_payment_failed(subscription_id: str):
    """Traite un paiement échoué"""
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        customer = stripe.Customer.retrieve(subscription.customer)
        
        user_email = customer.email
        if user_email:
            # Marquer comme impayé
            user_manager.mark_payment_failed(user_email)
            
            # Envoyer email de relance
            send_payment_reminder_email(user_email)
            
            print(f"⚠️ Paiement échoué pour {user_email}")
            
    except Exception as e:
        print(f"❌ Erreur traitement échec: {e}")

def handle_subscription_cancelled(subscription_id: str):
    """Traite une annulation d'abonnement"""
    try:
        # Trouver l'utilisateur par subscription_id
        user_email = user_manager.find_user_by_subscription(subscription_id)
        
        if user_email:
            # Désactiver l'accès
            user_manager.deactivate_subscription(user_email)
            
            print(f"❌ Abonnement annulé pour {user_email}")
            
    except Exception as e:
        print(f"❌ Erreur traitement annulation: {e}")
```

### 3. Interface de Paiement Frontend
```html
<!-- Template pour la sélection d'abonnement -->
<div class="pricing-plans">
    <h2>🚀 Choisissez votre abonnement AgriWeb 2.0</h2>
    
    <div class="plans-grid">
        <!-- Plan Starter -->
        <div class="plan-card starter">
            <h3>💼 Starter</h3>
            <div class="price">99€<span>/mois</span></div>
            <ul class="features">
                <li>✅ 500 recherches/mois</li>
                <li>✅ Données de base</li>
                <li>✅ Support email</li>
                <li>✅ Rapports PDF</li>
            </ul>
            <button onclick="selectPlan('starter')" class="btn-subscribe">
                🆓 15 jours gratuits
            </button>
        </div>
        
        <!-- Plan Professional -->
        <div class="plan-card professional popular">
            <div class="popular-badge">⭐ Populaire</div>
            <h3>🚀 Professional</h3>
            <div class="price">299€<span>/mois</span></div>
            <ul class="features">
                <li>✅ 2000 recherches/mois</li>
                <li>✅ Toutes les couches</li>
                <li>✅ Support prioritaire</li>
                <li>✅ API access</li>
                <li>✅ Rapports avancés</li>
            </ul>
            <button onclick="selectPlan('professional')" class="btn-subscribe">
                🆓 15 jours gratuits
            </button>
        </div>
        
        <!-- Plan Enterprise -->
        <div class="plan-card enterprise">
            <h3>🏢 Enterprise</h3>
            <div class="price">599€<span>/mois</span></div>
            <ul class="features">
                <li>✅ Recherches illimitées</li>
                <li>✅ Support 24/7</li>
                <li>✅ White label</li>
                <li>✅ Intégration personnalisée</li>
                <li>✅ Account manager</li>
            </ul>
            <button onclick="selectPlan('enterprise')" class="btn-subscribe">
                🆓 15 jours gratuits
            </button>
        </div>
    </div>
</div>

<script>
async function selectPlan(plan) {
    try {
        // Créer session checkout Stripe
        const response = await fetch('/api/payment/create-checkout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ plan: plan })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Rediriger vers Stripe Checkout
            window.location.href = result.checkout_url;
        } else {
            alert('Erreur: ' + result.error);
        }
    } catch (error) {
        alert('Erreur de connexion: ' + error);
    }
}

// Affichage du statut d'abonnement actuel
function displaySubscriptionStatus() {
    const user = getCurrentUser();
    if (user && user.subscription_status) {
        const statusDiv = document.getElementById('subscription-status');
        statusDiv.innerHTML = `
            <div class="subscription-info">
                📋 Abonnement: ${user.license_type.toUpperCase()}
                📅 Expire: ${user.expires}
                📊 Usage: ${user.searches_used}/${user.searches_limit}
                <button onclick="manageSubscription()">Gérer</button>
            </div>
        `;
    }
}
</script>

<style>
.plans-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin: 2rem 0;
}

.plan-card {
    border: 2px solid #e0e0e0;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    position: relative;
    transition: transform 0.3s ease;
}

.plan-card:hover {
    transform: translateY(-5px);
    border-color: #007bff;
}

.plan-card.popular {
    border-color: #28a745;
    transform: scale(1.05);
}

.popular-badge {
    position: absolute;
    top: -10px;
    left: 50%;
    transform: translateX(-50%);
    background: #28a745;
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
}

.price {
    font-size: 3rem;
    font-weight: bold;
    color: #007bff;
    margin: 1rem 0;
}

.price span {
    font-size: 1.2rem;
    color: #666;
}

.features {
    list-style: none;
    padding: 0;
    margin: 2rem 0;
}

.features li {
    padding: 0.5rem 0;
    border-bottom: 1px solid #f0f0f0;
}

.btn-subscribe {
    background: linear-gradient(45deg, #007bff, #28a745);
    color: white;
    border: none;
    padding: 1rem 2rem;
    border-radius: 8px;
    font-size: 1.1rem;
    cursor: pointer;
    width: 100%;
    transition: all 0.3s ease;
}

.btn-subscribe:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0,123,255,0.3);
}
</style>
```

## 📊 Dashboard de Gestion des Abonnements

### Tableau de Bord Administrateur
```python
@app.route('/admin/subscriptions')
def admin_subscriptions():
    """Dashboard des abonnements pour admin"""
    if not session.get('admin_authenticated'):
        return redirect('/admin/login')
    
    # Statistiques des abonnements
    stats = {
        'total_users': len(user_manager.users),
        'active_subscriptions': len([u for u in user_manager.users.values() if u.get('active')]),
        'trial_users': len([u for u in user_manager.users.values() if u.get('license_type') == 'trial']),
        'revenue_monthly': calculate_monthly_revenue(),
        'churn_rate': calculate_churn_rate()
    }
    
    # Liste des utilisateurs avec détails abonnement
    users_with_subscriptions = []
    for email, user in user_manager.users.items():
        if user.get('stripe_subscription_id'):
            subscription_status = stripe_manager.get_subscription_status(
                user['stripe_subscription_id']
            )
            user['subscription_details'] = subscription_status
        
        users_with_subscriptions.append(user)
    
    return render_template_string(ADMIN_SUBSCRIPTIONS_TEMPLATE, 
                                stats=stats, 
                                users=users_with_subscriptions)

def calculate_monthly_revenue():
    """Calcule le chiffre d'affaires mensuel"""
    revenue = 0
    for user in user_manager.users.values():
        if user.get('active') and user.get('license_type') != 'trial':
            if user['license_type'] == 'starter':
                revenue += 99
            elif user['license_type'] == 'professional':
                revenue += 299
            elif user['license_type'] == 'enterprise':
                revenue += 599
    return revenue

def calculate_churn_rate():
    """Calcule le taux de désabonnement"""
    # Logique de calcul du churn basée sur les annulations
    # À implémenter selon vos besoins
    return 5.2  # Exemple: 5.2%
```

## 🔐 Sécurité et Conformité

### Mesures de Sécurité
```python
# Chiffrement des données sensibles
from cryptography.fernet import Fernet

class PaymentSecurity:
    def __init__(self):
        self.encryption_key = os.getenv('PAYMENT_ENCRYPTION_KEY').encode()
        self.cipher = Fernet(self.encryption_key)
    
    def encrypt_payment_data(self, data: str) -> str:
        """Chiffre les données de paiement"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_payment_data(self, encrypted_data: str) -> str:
        """Déchiffre les données de paiement"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def log_payment_event(self, event_type: str, user_email: str, amount: float = None):
        """Log sécurisé des événements de paiement"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': event_type,
            'user': user_email,
            'amount': amount,
            'ip': request.remote_addr if request else None
        }
        
        # Enregistrement dans un fichier de log sécurisé
        with open('payment_audit.log', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
```

### Conformité RGPD
```python
@app.route('/api/user/data-export', methods=['POST'])
def export_user_data():
    """Export des données utilisateur (RGPD)"""
    if not session.get('authenticated'):
        return jsonify({"error": "Non autorisé"}), 401
    
    user_email = session.get('user_data', {}).get('email')
    user_data = user_manager.get_user_complete_data(user_email)
    
    # Inclure les données de paiement (anonymisées)
    payment_history = get_user_payment_history(user_email, anonymized=True)
    
    export_data = {
        'user_profile': user_data,
        'payment_history': payment_history,
        'usage_statistics': get_user_usage_stats(user_email),
        'export_date': datetime.now().isoformat()
    }
    
    return jsonify(export_data)

@app.route('/api/user/delete-account', methods=['POST'])
def delete_user_account():
    """Suppression de compte (RGPD)"""
    if not session.get('authenticated'):
        return jsonify({"error": "Non autorisé"}), 401
    
    user_email = session.get('user_data', {}).get('email')
    user = user_manager.users.get(user_email)
    
    if user and user.get('stripe_subscription_id'):
        # Annuler l'abonnement Stripe
        stripe_manager.cancel_subscription(user['stripe_subscription_id'], at_period_end=False)
    
    # Supprimer les données utilisateur
    user_manager.delete_user(user_email)
    
    # Log de la suppression
    log_entry = {
        'action': 'account_deleted',
        'email': user_email,
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify({"success": True, "message": "Compte supprimé"})
```

## 📈 Analytics et KPIs

### Métriques Importantes
```python
class PaymentAnalytics:
    def __init__(self):
        self.metrics = {}
    
    def calculate_key_metrics(self):
        """Calcule les KPIs principaux"""
        return {
            'mrr': self.calculate_mrr(),  # Monthly Recurring Revenue
            'arr': self.calculate_arr(),  # Annual Recurring Revenue
            'ltv': self.calculate_ltv(),  # Lifetime Value
            'cac': self.calculate_cac(),  # Customer Acquisition Cost
            'churn_rate': self.calculate_churn(),
            'conversion_rate': self.calculate_conversion_rate()
        }
    
    def calculate_mrr(self):
        """Revenus récurrents mensuels"""
        mrr = 0
        for user in user_manager.users.values():
            if user.get('active') and user.get('stripe_subscription_id'):
                plan = user.get('license_type')
                if plan == 'starter':
                    mrr += 99
                elif plan == 'professional':
                    mrr += 299
                elif plan == 'enterprise':
                    mrr += 599
        return mrr
    
    def calculate_conversion_rate(self):
        """Taux de conversion essai → payant"""
        total_trials = len([u for u in user_manager.users.values() 
                          if u.get('license_type') == 'trial'])
        total_paid = len([u for u in user_manager.users.values() 
                        if u.get('active') and u.get('license_type') != 'trial'])
        
        if total_trials > 0:
            return (total_paid / (total_trials + total_paid)) * 100
        return 0

# Dashboard analytics
@app.route('/admin/analytics')
def admin_analytics():
    """Dashboard analytique des paiements"""
    analytics = PaymentAnalytics()
    metrics = analytics.calculate_key_metrics()
    
    return render_template_string(ANALYTICS_TEMPLATE, metrics=metrics)
```

## 🎯 Plan d'Implémentation

### Phase 1 : Configuration (Semaine 1)
- [ ] **Compte Stripe** professionnel
- [ ] **Produits et prix** configurés
- [ ] **Webhooks** configurés
- [ ] **Tests paiement** en mode sandbox

### Phase 2 : Intégration (Semaine 2)
- [ ] **API paiement** dans AgriWeb
- [ ] **Interface abonnement** client
- [ ] **Dashboard admin** gestion
- [ ] **Tests fonctionnels** complets

### Phase 3 : Production (Semaine 3)
- [ ] **Migration Stripe Live**
- [ ] **Monitoring paiements**
- [ ] **Support client** paiements
- [ ] **Documentation utilisateur**

## 💰 Estimation Coûts

### Frais Stripe
```
Transaction fees: 1.4% + 0.25€ (cartes EU)
Abonnements: Pas de frais fixes
Disputes: 15€ par dispute

Exemple avec 50 clients:
- Revenus: ~8000€/mois
- Frais Stripe: ~120€/mois (1.5%)
- Net: ~7880€/mois
```

### Alternatives Considérées
1. **Stripe** (recommandé) - Le plus complet
2. **PayPal Business** - Plus simple mais moins de features
3. **Square** - Bon pour TPE/PME
4. **GoCardless** - Spécialisé prélèvements SEPA

Voulez-vous que je commence par implémenter l'intégration Stripe dans votre système actuel ?
