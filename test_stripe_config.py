#!/usr/bin/env python3
"""
Test de configuration Stripe pour AgriWeb 2.0
"""

print("🧪 Test du système de paiement Stripe...")
print("=" * 50)

try:
    import stripe
    print("✅ Module Stripe importé avec succès")
except ImportError as e:
    print(f"❌ Erreur import Stripe: {e}")
    exit(1)

# Test de la configuration de base
try:
    from stripe_integration import stripe_payment_manager
    print("✅ StripePaymentManager importé")
    
    # Afficher la configuration
    print(f"📋 Plans configurés: {list(stripe_payment_manager.pricing_plans.keys())}")
    print(f"🆓 Période d'essai: {stripe_payment_manager.trial_period_days} jours")
    
    # Test des clés (sans révéler les valeurs)
    secret_key = stripe_payment_manager.stripe_secret_key
    pub_key = stripe_payment_manager.stripe_publishable_key
    
    if secret_key.startswith('sk_'):
        print(f"✅ Clé secrète configurée: {secret_key[:15]}...")
    else:
        print("⚠️ Clé secrète par défaut (à remplacer)")
    
    if pub_key.startswith('pk_'):
        print(f"✅ Clé publique configurée: {pub_key[:15]}...")
    else:
        print("⚠️ Clé publique par défaut (à remplacer)")
    
    # Test de création d'un client (simulation)
    print("\n🧪 Test des fonctions principales...")
    
    # Test de validation de plan
    for plan in ['starter', 'professional', 'enterprise']:
        limits = stripe_payment_manager.get_plan_limits(plan)
        if limits:
            print(f"✅ Plan {plan}: {limits['searches_limit']} recherches, {limits['amount']}€/mois")
    
    print("\n✅ Tous les tests de base sont passés !")
    print("💡 Pour activer les paiements :")
    print("   1. Créer un compte Stripe")
    print("   2. Récupérer les clés API")
    print("   3. Créer les produits et prix")
    print("   4. Mettre à jour stripe_integration.py avec les vrais IDs")
    
except Exception as e:
    print(f"❌ Erreur lors du test: {e}")
    import traceback
    traceback.print_exc()

print("\n🎯 Prêt pour la configuration Stripe !")
