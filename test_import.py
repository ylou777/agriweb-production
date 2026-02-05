#!/usr/bin/env python3
"""Test si agriweb_hebergement_gratuit peut être importé sans erreur"""

import sys
import traceback

print("="*80)
print("TEST D'IMPORT DU MODULE AGRIWEB")
print("="*80)

try:
    print("\n1. Import du module...")
    import agriweb_hebergement_gratuit
    print("✅ Import réussi!")
    
    print("\n2. Vérification de l'objet app...")
    app = agriweb_hebergement_gratuit.app
    print(f"✅ App trouvée: {app}")
    
    print("\n3. Test du endpoint /health...")
    with app.test_client() as client:
        response = client.get('/health')
        print(f"Status: {response.status_code}")
        print(f"Response: {response.get_json()}")
        
    if response.status_code == 200:
        print("\n✅✅✅ TOUS LES TESTS PASSENT ✅✅✅")
    else:
        print(f"\n❌ Health check a échoué avec status {response.status_code}")
        
except Exception as e:
    print(f"\n❌ ERREUR LORS DE L'IMPORT:")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {str(e)}")
    print("\nTraceback complet:")
    traceback.print_exc()
    sys.exit(1)
