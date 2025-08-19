#!/usr/bin/env python3
"""
Test d'import direct pour diagnostiquer les problèmes
"""

print("🔄 Test d'import de l'application...")

try:
    print("1. Import de Flask...")
    from flask import Flask
    print("✅ Flask OK")
    
    print("2. Test import agriweb_hebergement_gratuit...")
    import agriweb_hebergement_gratuit as app_module
    print("✅ Import du module principal OK")
    
    print("3. Test de l'application Flask...")
    app = app_module.app
    print("✅ Application Flask récupérée")
    
    print("4. Test du gestionnaire d'utilisateurs...")
    user_manager = app_module.user_manager
    print("✅ Gestionnaire d'utilisateurs OK")
    
    print("5. Test d'import agriweb_source...")
    agriweb_module = app_module.import_agriweb_source()
    if agriweb_module:
        print("✅ Module agriweb_source importé avec succès")
    else:
        print("⚠️ Module agriweb_source non disponible")
    
    print("6. Test des routes...")
    with app.test_client() as client:
        response = client.get('/')
        print(f"✅ Route / accessible - Status: {response.status_code}")
    
    print("🎉 Tous les tests d'import sont passés !")
    
except Exception as e:
    print(f"❌ Erreur lors du test: {e}")
    import traceback
    traceback.print_exc()
