#!/usr/bin/env python3
"""
🚀 RAILWAY DEPLOYMENT - AGRIWEB COMPLET
Lanceur spécial pour Railway avec configuration automatique
"""

import os
import sys

# Configuration pour Railway
def configure_railway_environment():
    """Configure l'environnement Railway"""
    
    # Port Railway
    port = int(os.environ.get("PORT", 5000))
    
    # Variables d'environnement par défaut
    os.environ.setdefault("FLASK_ENV", "production")
    os.environ.setdefault("FLASK_DEBUG", "False")
    
    print(f"🚀 [RAILWAY] Configuration pour le port {port}")
    print(f"📁 [RAILWAY] Répertoire de travail: {os.getcwd()}")
    print(f"🐍 [RAILWAY] Version Python: {sys.version}")
    
    return port

if __name__ == "__main__":
    try:
        print("🌟 [RAILWAY] Démarrage AgriWeb Production")
        
        # Configuration Railway
        port = configure_railway_environment()
        
        # Import du programme principal
        print("📥 [RAILWAY] Import du programme AgriWeb complet...")
        from agriweb_hebergement_gratuit import app
        
        print("✅ [RAILWAY] Programme AgriWeb importé avec succès")
        print(f"🌐 [RAILWAY] Démarrage sur le port {port}")
        
        # Lancement avec configuration Railway
        app.run(
            host="0.0.0.0",  # Railway nécessite 0.0.0.0
            port=port,
            debug=False,
            use_reloader=False
        )
        
    except Exception as e:
        print(f"❌ [RAILWAY] Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
