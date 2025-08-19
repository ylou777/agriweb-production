#!/usr/bin/env python3
"""
Test d'import d'agriweb_source pour vérifier la compatibilité
"""

try:
    print("🔄 Test d'import d'agriweb_source...")
    import agriweb_source
    print("✅ agriweb_source importé avec succès!")
    
    # Vérifier si l'application Flask existe
    if hasattr(agriweb_source, 'app'):
        print("✅ Application Flask trouvée dans agriweb_source")
        app = agriweb_source.app
        print(f"✅ Routes disponibles: {len(app.url_map._rules)} routes")
        
        # Lister quelques routes
        print("📍 Premières routes:")
        for rule in list(app.url_map.iter_rules())[:5]:
            print(f"  - {rule.rule} ({', '.join(rule.methods)})")
    else:
        print("❌ Pas d'application Flask trouvée dans agriweb_source")
    
    # Vérifier les fonctions principales
    functions = [attr for attr in dir(agriweb_source) if callable(getattr(agriweb_source, attr)) and not attr.startswith('_')]
    print(f"📦 Fonctions disponibles: {len(functions)}")
    print(f"🔧 Premières fonctions: {functions[:5]}")
    
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    if "DLL load failed" in str(e):
        print("💡 Problème de DLL géospatiale détecté")
    elif "pyproj" in str(e) or "_context" in str(e):
        print("💡 Problème avec pyproj détecté")
    else:
        print("💡 Autre problème d'import")
except Exception as e:
    print(f"❌ Erreur générale: {e}")

print("🔚 Test terminé")
