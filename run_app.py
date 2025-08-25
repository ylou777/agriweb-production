# run_app.py

# Import du serveur unifié final
import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    try:
        print("🚀 [STARTUP] Démarrage du serveur AgriWeb 2.0 Unifié")
        print("� [GEOSERVER] Intégration avec GeoServer activée")
        
        # Import et lancement du serveur unifié
        from agriweb_hebergement_gratuit import app
        
        print("✅ [SUCCESS] Serveur unifié importé")
        print("🌐 [URL] http://localhost:5000")
        print("� [STATUS] http://localhost:5000/status")
        
        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
        
    except ImportError as e:
        print(f"❌ [IMPORT ERROR] {e}")
        print("� [FALLBACK] Tentative avec l'ancien système...")
        
        # Fallback vers l'ancien système
        import agriweb_hebergement_gratuit
        agriweb_hebergement_gratuit.app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
        
    except Exception as e:
        print(f"❌ [ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()