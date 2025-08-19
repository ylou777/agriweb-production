#!/usr/bin/env python3
"""
Test rapide du système de paiement AgriWeb 2.0
"""

print("🧪 Test du système de paiement...")

try:
    # Test 1: Import Stripe
    import stripe
    print("✅ Stripe importé")
    
    # Test 2: Import gestionnaire de paiements
    from stripe_integration import stripe_payment_manager
    print("✅ StripePaymentManager importé")
    
    # Test 3: Vérifier plans configurés
    plans = list(stripe_payment_manager.pricing_plans.keys())
    print(f"✅ Plans configurés: {plans}")
    
    # Test 4: Vérifier limits
    for plan in plans:
        limits = stripe_payment_manager.get_plan_limits(plan)
        if limits:
            print(f"   📋 {plan}: {limits['searches_limit']} recherches, {limits['amount']}€/mois")
    
    # Test 5: Configuration clés
    secret_key = stripe_payment_manager.stripe_secret_key
    if secret_key.startswith('sk_test_'):
        print("✅ Mode test configuré")
    elif secret_key.startswith('sk_live_'):
        print("✅ Mode production configuré")
    else:
        print("⚠️  Clés par défaut (à remplacer)")
    
    print("\n🎯 Système de paiement prêt !")
    print("💡 Prochaine étape: Configurer vraies clés Stripe")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
