# run_app.py

# Import du serveur unifié final
import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    try:
        print("🚀 [STARTUP] Démarrage du serveur AgriWeb Hébergement Gratuit")
        print("🔧 [GEOSERVER] Intégration avec GeoServer activée")
        
        # Import et lancement du serveur hébergement gratuit avec toutes les corrections
        from agriweb_hebergement_gratuit import app
        
        print("✅ [SUCCESS] Serveur agriweb_hebergement_gratuit importé")
        print("🌐 [URL] http://localhost:5000")
        print("🔍 [STATUS] http://localhost:5000/status")
        
        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
        
    except ImportError as e:
        print(f"❌ [IMPORT ERROR] {e}")
        print("🔄 [FALLBACK] Tentative avec le serveur unifié...")
        
        # Fallback vers le serveur unifié
        from serveur_unifie_final import app
        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
        
    except Exception as e:
        print(f"❌ [ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()