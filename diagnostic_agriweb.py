#!/usr/bin/env python3
"""
🔧 DIAGNOSTIC AGRIWEB
Test d'import et de démarrage du module agriweb_source
"""

import sys
import traceback

print("🔍 DIAGNOSTIC AGRIWEB")
print("=" * 40)

try:
    print("1. Test d'import agriweb_source...")
    import agriweb_source
    print("✅ Import réussi")
    
    print(f"2. Type d'app: {type(agriweb_source.app)}")
    
    print("3. Test des routes...")
    routes = list(agriweb_source.app.url_map.iter_rules())
    print(f"   Nombre de routes: {len(routes)}")
    
    print("4. Quelques routes principales:")
    for rule in routes[:10]:
        print(f"   - {rule.rule} [{', '.join(rule.methods)}]")
    
    print("5. Test de démarrage...")
    print("   Tentative de lancement sur port 5000...")
    
    # Test de démarrage
    agriweb_source.app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
    
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    traceback.print_exc()
    
except Exception as e:
    print(f"❌ Erreur générale: {e}")
    print(f"   Type: {type(e)}")
    traceback.print_exc()
    
print("\n📋 Diagnostic terminé")
