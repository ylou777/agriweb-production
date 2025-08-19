# 🚀 Guide de Configuration Stripe pour AgriWeb 2.0

## 📋 Checklist de Déploiement Paiements

### Phase 1 : Configuration Stripe (30 minutes)

#### ✅ Étape 1 : Création du compte Stripe
1. **Aller sur** https://stripe.com
2. **Créer un compte** business
3. **Vérifier l'identité** (nécessaire pour recevoir les paiements)
4. **Configurer les informations bancaires** françaises

#### ✅ Étape 2 : Récupération des clés API
```bash
# Aller dans : Dashboard Stripe > Développeurs > Clés API
# Copier ces 3 clés :

# Mode Test (pour développement)
sk_test_... # Clé secrète de test
pk_test_... # Clé publique de test

# Mode Live (pour production)
sk_live_... # Clé secrète live
pk_live_... # Clé publique live
```

#### ✅ Étape 3 : Création des produits et prix
**Dans Dashboard Stripe > Produits :**

**1. Produit "AgriWeb Starter"**
```
Nom: AgriWeb 2.0 - Starter
Description: Plan de base avec 500 recherches/mois
Prix: 99.00 EUR
Facturation: Récurrente - Mensuelle
ID généré: price_XXXXX (noter cet ID)
```

**2. Produit "AgriWeb Professional"**
```
Nom: AgriWeb 2.0 - Professional  
Description: Plan professionnel avec 2000 recherches/mois
Prix: 299.00 EUR
Facturation: Récurrente - Mensuelle
ID généré: price_YYYYY (noter cet ID)
```

**3. Produit "AgriWeb Enterprise"**
```
Nom: AgriWeb 2.0 - Enterprise
Description: Plan entreprise avec recherches illimitées
Prix: 599.00 EUR
Facturation: Récurrente - Mensuelle  
ID généré: price_ZZZZZ (noter cet ID)
```

#### ✅ Étape 4 : Configuration des webhooks
**Dans Dashboard Stripe > Développeurs > Webhooks :**

1. **Cliquer** "Ajouter un endpoint"
2. **URL webhook** : `https://votre-domaine.com/api/webhooks/stripe`
3. **Événements à écouter** :
   - `checkout.session.completed`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.deleted`
   - `customer.subscription.updated`
4. **Récupérer** le secret webhook : `whsec_...`

### Phase 2 : Configuration AgriWeb 2.0 (15 minutes)

#### ✅ Étape 5 : Configuration des variables d'environnement

**Créer le fichier `.env` :**
```bash
# Copier le template
cp stripe_config_template.env .env

# Éditer avec vos vraies clés
nano .env
```

**Contenu du fichier `.env` :**
```bash
# Clés Stripe (remplacer par vos vraies clés)
STRIPE_SECRET_KEY=sk_test_VOTRE_CLE_SECRETE
STRIPE_PUBLISHABLE_KEY=pk_test_VOTRE_CLE_PUBLIQUE  
STRIPE_WEBHOOK_SECRET=whsec_VOTRE_SECRET_WEBHOOK

# IDs des prix Stripe
STRIPE_PRICE_STARTER=price_VOTRE_ID_STARTER
STRIPE_PRICE_PROFESSIONAL=price_VOTRE_ID_PRO
STRIPE_PRICE_ENTERPRISE=price_VOTRE_ID_ENTERPRISE

# Configuration
TRIAL_PERIOD_DAYS=15
BASE_URL=https://votre-domaine.com
```

#### ✅ Étape 6 : Installation des dépendances
```bash
# Installer Stripe Python
pip install stripe

# Vérifier l'installation
python -c "import stripe; print('Stripe OK:', stripe.__version__)"
```

#### ✅ Étape 7 : Mise à jour des IDs de prix
**Éditer `stripe_integration.py` :**
```python
# Ligne ~25-45, remplacer par vos vrais IDs
self.pricing_plans = {
    'starter': {
        'price_id': 'price_VOTRE_VRAI_ID_STARTER',  # ⚠️ Remplacer
        'amount': 9900,
        ...
    },
    'professional': {
        'price_id': 'price_VOTRE_VRAI_ID_PRO',     # ⚠️ Remplacer
        'amount': 29900,
        ...
    },
    'enterprise': {
        'price_id': 'price_VOTRE_VRAI_ID_ENTERPRISE', # ⚠️ Remplacer
        'amount': 59900,
        ...
    }
}
```

### Phase 3 : Tests et Validation (20 minutes)

#### ✅ Étape 8 : Test en mode développement
```bash
# Démarrer l'application
python agriweb_avec_paiements.py

# Aller sur http://localhost:5000
# Se connecter avec un compte test
# Aller sur /pricing
# Tester un abonnement avec les cartes de test Stripe
```

**Cartes de test Stripe :**
```
Carte réussie: 4242 4242 4242 4242
Carte échouée: 4000 0000 0000 0002
3D Secure: 4000 0027 6000 3184
Expiration: N'importe quelle date future
CVV: N'importe quel nombre 3 chiffres
```

#### ✅ Étape 9 : Test des webhooks
```bash
# Installer Stripe CLI pour tester les webhooks
# https://stripe.com/docs/stripe-cli

# Écouter les webhooks en local
stripe listen --forward-to localhost:5000/api/webhooks/stripe

# Dans un autre terminal, déclencher un événement test
stripe trigger payment_intent.succeeded
```

#### ✅ Étape 10 : Test complet du tunnel d'abonnement
1. **Connexion utilisateur** → ✅
2. **Sélection plan** → ✅  
3. **Redirection Stripe** → ✅
4. **Paiement test** → ✅
5. **Webhook reçu** → ✅
6. **Retour succès** → ✅
7. **Mise à jour BDD** → ✅

### Phase 4 : Mise en Production (30 minutes)

#### ✅ Étape 11 : Activation du mode Live
**Dans Dashboard Stripe :**
1. **Activer** le compte live (vérification identité requise)
2. **Récupérer** les clés live : `sk_live_...` et `pk_live_...`
3. **Reconfigurer** les webhooks avec l'URL de production

#### ✅ Étape 12 : Déploiement production
```bash
# Mettre à jour les variables d'environnement
export STRIPE_SECRET_KEY=sk_live_VOTRE_CLE_LIVE
export STRIPE_PUBLISHABLE_KEY=pk_live_VOTRE_CLE_LIVE
export BASE_URL=https://votre-domaine-prod.com

# Redémarrer l'application
systemctl restart agriweb
```

#### ✅ Étape 13 : Test de production avec de vrais paiements
⚠️ **ATTENTION** : Tests avec de vraies cartes = vraie facturation !

## 🔧 Dépannage et FAQ

### ❓ Problème : "Invalid API key"
**Solution :**
```bash
# Vérifier que la clé est bien définie
echo $STRIPE_SECRET_KEY

# Vérifier qu'elle commence par sk_test_ ou sk_live_
# Pas d'espaces avant/après
```

### ❓ Problème : "Price not found"
**Solution :**
1. Vérifier que le prix existe dans le dashboard Stripe
2. Copier exactement l'ID (commence par `price_`)
3. Mode test = prix de test, mode live = prix de live

### ❓ Problème : Webhooks non reçus
**Solutions :**
1. **URL correcte** : `https://votre-domaine.com/api/webhooks/stripe`
2. **HTTPS obligatoire** en production
3. **Secret webhook** correct dans les variables d'environnement
4. **Tester** avec Stripe CLI : `stripe listen`

### ❓ Problème : Paiement réussi mais pas d'activation
**Diagnostic :**
```bash
# Vérifier les logs de webhooks
tail -f logs/payment_audit.log

# Vérifier la base utilisateurs
python -c "
from production_commercial import user_manager
import json
print(json.dumps(user_manager.users, indent=2))
"
```

## 📊 Monitoring et Analytics

### 🔍 Métriques importantes à surveiller :
- **Taux de conversion** essai → payant
- **Taux de désabonnement** (churn)
- **Revenus récurrents** mensuels (MRR)
- **Valeur vie client** (LTV)

### 📈 Dashboard Stripe à consulter :
- **Revenus** : Vue d'ensemble des paiements
- **Abonnements** : Statut des abonnements actifs
- **Analyses** : Métriques de performance
- **Disputes** : Litiges et remboursements

## 🚨 Alertes importantes

### ⚠️ Surveillance des paiements échoués :
```python
# Dans votre monitoring (ex: avec un cron job)
def check_failed_payments():
    failed_payments = stripe.PaymentIntent.list(
        limit=10,
        created={'gte': int((datetime.now() - timedelta(days=1)).timestamp())}
    )
    
    for payment in failed_payments:
        if payment.status == 'payment_failed':
            # Alerter l'équipe
            send_alert(f"Paiement échoué: {payment.id}")
```

## 💡 Optimisations recommandées

### 🔄 Retry logic pour webhooks :
```python
@app.route('/api/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    # Ajouter retry en cas d'échec temporaire
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = stripe_payment_manager.process_webhook(payload, signature)
            return "Success", 200
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Backoff exponentiel
```

### 📧 Notifications par email :
```python
def send_payment_notification(user_email, event_type, details):
    """Envoie des notifications pour les événements de paiement"""
    # Intégrer avec votre système d'email
    pass
```

## ✅ Checklist finale avant Go-Live

- [ ] ✅ Compte Stripe activé et vérifié
- [ ] ✅ Produits et prix créés avec bons montants
- [ ] ✅ Webhooks configurés avec HTTPS
- [ ] ✅ Variables d'environnement de production définies
- [ ] ✅ Tests complets effectués en mode test
- [ ] ✅ Sauvegarde de la base de données
- [ ] ✅ Monitoring et alertes en place
- [ ] ✅ Équipe support formée sur Stripe
- [ ] ✅ Documentation utilisateur rédigée
- [ ] ✅ Plan de communication clients

**🎉 Votre système de paiement AgriWeb 2.0 est prêt !**
