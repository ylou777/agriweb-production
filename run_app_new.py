# run_app.py

# Import du serveur unifié final
import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    try:
        print("🚀 [STARTUP] Démarrage du serveur AgriWeb 2.0 Complet avec Authentification")
        print("🔐 [AUTH] Système d'authentification activé")
        print("🗺️ [MAPS] Cartes et recherche intégrées")
        
        # Import et lancement du serveur avec authentification
        from agriweb_hebergement_gratuit import app
        
        print("✅ [SUCCESS] Application AgriWeb complète importée")
        print("🌐 [URL] http://localhost:5001")
        print("📊 [FEATURES] Carte, Recherche, Rapports disponibles")
        
        app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)
        
    except ImportError as e:
        print(f"❌ [IMPORT ERROR] {e}")
        print("🔄 [FALLBACK] Tentative avec l'application source directe...")
        
        # Fallback vers l'application source directe
        try:
            import agriweb_source
            print("✅ [FALLBACK] Application source importée")
            agriweb_source.app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)
        except Exception as fallback_error:
            print(f"❌ [FALLBACK ERROR] {fallback_error}")
        
    except Exception as e:
        print(f"❌ [ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
