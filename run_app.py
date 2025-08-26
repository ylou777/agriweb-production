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
        from serveur_unifie_final import app
        
        # Configuration Railway
        port = int(os.getenv('PORT', 5000))
        host = os.getenv('HOST', '0.0.0.0')  # Railway nécessite 0.0.0.0
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        print("✅ [SUCCESS] Serveur unifié importé")
        print(f"🌐 [URL] http://{host}:{port}")
        print(f"📊 [STATUS] http://{host}:{port}/status")
        
        app.run(host=host, port=port, debug=debug, use_reloader=False)
        
    except ImportError as e:
        print(f"❌ [IMPORT ERROR] {e}")
        print("� [FALLBACK] Tentative avec l'ancien système...")
        
        # Fallback vers l'ancien système
        import agriweb_source
        agriweb_source.app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
        
    except Exception as e:
        print(f"❌ [ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()