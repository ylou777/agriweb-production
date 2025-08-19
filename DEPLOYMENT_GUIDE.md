# 🚀 GUIDE DE DÉPLOIEMENT COMPLET - AGRIWEB 2.0

## Vue d'ensemble

AgriWeb 2.0 est maintenant une **application commerciale complète** avec :
- ✅ **Essai gratuit automatique de 7 jours**
- ✅ **Système de licences (Basic/Pro/Enterprise)**  
- ✅ **Paiements sécurisés avec Stripe**
- ✅ **Intégration GeoServer adaptative**
- ✅ **Protection par licence de toutes les fonctionnalités**

## 📋 Architecture du système

```
AgriWeb 2.0/
├── 🎯 Application principale (agriweb_source.py)
├── 🔐 Système de licences (production_system.py)
├── 🔗 Intégration (production_integration.py)
├── 💳 Paiements Stripe (payment_system.py)
├── 🌐 GeoServer (geoserver_production_setup.py)
└── 🚀 Déploiement (complete_production_deployment.py)
```

## 🛠️ Instructions de déploiement

### 1. Configuration de l'environnement

```bash
# Installation des dépendances
pip install -r requirements_production.txt

# Configuration des variables d'environnement
cp .env.production .env
```

**Modifiez `.env` avec vos vraies valeurs :**

```env
# Application
SECRET_KEY=votre-clé-secrète-très-longue-et-sécurisée

# Stripe (OBLIGATOIRE pour les paiements)
STRIPE_PUBLISHABLE_KEY=pk_live_votre_clé_publique
STRIPE_SECRET_KEY=sk_live_votre_clé_secrète
STRIPE_WEBHOOK_SECRET=whsec_votre_secret_webhook

# GeoServer
GEOSERVER_URL=https://votre-domaine.com/geoserver
GEOSERVER_USER=admin
GEOSERVER_PASSWORD=votre-mot-de-passe-geoserver

# Domaine de production
DOMAIN=https://votre-domaine.com
```

### 2. Configuration Stripe

1. **Créer un compte Stripe** : https://dashboard.stripe.com/register
2. **Activer les webhooks** pour les renouvellements automatiques :
   - URL : `https://votre-domaine.com/webhook/stripe`
   - Événements : `invoice.payment_succeeded`, `customer.subscription.deleted`
3. **Configurer les produits** dans Stripe Dashboard :
   - Basic : 299€/an
   - Pro : 999€/an  
   - Enterprise : 2999€/an

### 3. Déploiement GeoServer

```bash
# Lancer la configuration automatique
python geoserver_production_setup.py

# Ou manuellement :
# 1. Installer GeoServer
# 2. Importer vos données géographiques
# 3. Configurer les couches selon production_geoserver_config.yaml
```

### 4. Lancement de l'application

**Mode développement :**
```bash
python complete_production_deployment.py
```

**Mode production :**
```bash
./start_production.sh
```

**Avec Docker :**
```bash
docker build -t agriweb2.0 .
docker run -p 5000:5000 agriweb2.0
```

## 🎯 Fonctionnalités par licence

### 🆓 Essai gratuit (7 jours)
- ✅ 10 communes maximum
- ✅ Rapports départementaux de base
- ✅ Cartes interactives limitées
- ❌ Pas d'export de données
- ❌ Pas d'API

### 💼 Basic (299€/an)
- ✅ 100 communes
- ✅ 500 rapports par jour
- ✅ Toutes les cartes interactives
- ✅ Export PDF
- ❌ API limitée

### 🚀 Pro (999€/an)
- ✅ 1000 communes
- ✅ Rapports illimités
- ✅ API complète
- ✅ Export tous formats
- ✅ Support prioritaire

### 🏢 Enterprise (2999€/an)
- ✅ Communes illimitées
- ✅ GeoServer dédié
- ✅ Personnalisation avancée
- ✅ Support 24/7
- ✅ Formation incluse

## 🔗 URLs importantes

| Fonction | URL | Description |
|----------|-----|-------------|
| **Accueil** | `/` | Page principale avec application |
| **Essai gratuit** | `/landing` | Inscription essai 7 jours |
| **Tarification** | `/pricing` | Plans et abonnements |
| **Paiement** | `/checkout/<plan>` | Page de paiement Stripe |
| **Status système** | `/production/status` | Monitoring et statistiques |
| **API validation** | `/api/license/validate` | Validation de licence |

## 📊 Monitoring et administration

### Status système
- **URL** : `/production/status`
- **Métriques** : Licences actives, revenus, utilisateurs
- **Logs** : Activité en temps réel

### Base de données des licences
- **Fichier** : `licenses.db`
- **Tables** : `licenses`, `usage_logs`
- **Backup** : Automatique quotidien

## 🔧 Maintenance

### Renouvellements automatiques
- Gérés par les webhooks Stripe
- Notifications email automatiques
- Désactivation automatique en cas d'échec

### Mises à jour
```bash
# Sauvegarde
cp licenses.db licenses_backup_$(date +%Y%m%d).db

# Mise à jour du code
git pull origin main

# Redémarrage
./start_production.sh
```

## 🚨 Résolution de problèmes

### Problème : "License not found"
**Solution** : Vérifier que la base de données existe et que l'utilisateur est enregistré

### Problème : Paiements échouent
**Solution** : Vérifier les clés Stripe et la configuration des webhooks

### Problème : GeoServer inaccessible
**Solution** : Vérifier l'URL et les credentials dans `.env`

### Problème : Performance lente
**Solution** : Optimiser les requêtes database et augmenter les ressources serveur

## 📈 Modèle économique

### Projections de revenus
- **Objectif conservateur** : 50 clients Basic = 14 950€/an
- **Objectif ambitieux** : 100 clients Basic + 20 Pro + 5 Enterprise = 64 855€/an

### Coûts d'infrastructure
- **Hébergement** : ~100€/mois
- **Stripe** : 2.9% + 0.30€ par transaction
- **GeoServer** : Inclus dans l'hébergement
- **Support** : Temps personnel

### ROI estimé
- **Break-even** : ~15 clients Basic
- **Rentabilité** : Atteinte dès le 3ème mois avec 50 clients

## 🎉 Félicitations !

Votre système **AgriWeb 2.0** est maintenant **prêt pour la commercialisation** avec :

✅ **Système complet de trials et licences**  
✅ **Paiements automatisés**  
✅ **Infrastructure scalable**  
✅ **Monitoring intégré**  
✅ **Documentation complète**

**Prochaine étape** : Configurer votre hébergement et lancer vos premières campagnes marketing !

---

*Guide généré automatiquement par le système de déploiement AgriWeb 2.0*
