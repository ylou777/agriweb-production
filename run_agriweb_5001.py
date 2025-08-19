#!/usr/bin/env python3
"""
Script pour lancer AgriWeb sur le port 5001
"""

if __name__ == '__main__':
    try:
        print("🚀 Démarrage AgriWeb sur port 5001...")
        
        # Import de l'application
        from agriweb_source import app
        
        print("✅ Application AgriWeb importée")
        print("🌐 URL: http://127.0.0.1:5001")
        
        # Lancement du serveur
        app.run(
            host='127.0.0.1',
            port=5001,
            debug=False,
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        import traceback
        traceback.print_exc()
