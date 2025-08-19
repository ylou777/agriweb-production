#!/usr/bin/env python3
"""
🚀 AGRIWEB 2.0 - VERSION COMPLÈTE
Serveur AgriWeb entièrement fonctionnel avec toutes les routes d'origine
"""

import sys
import os
import traceback
from datetime import datetime

def safe_print(*args, **kwargs):
    """Print sécurisé qui ignore les erreurs de canal fermé"""
    try:
        print(*args, **kwargs)
    except OSError:
        pass

def main():
    """Fonction principale pour lancer AgriWeb complet"""
    
    safe_print("=" * 80)
    safe_print("🚀 [AGRIWEB 2.0] === DÉMARRAGE SERVEUR COMPLET ===")
    safe_print(f"📅 Date/Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    safe_print("=" * 80)
    
    try:
        # Import du module AgriWeb original
        safe_print("📦 [IMPORT] Chargement du module agriweb_source...")
        
        # Vérifier que le fichier existe
        if not os.path.exists("agriweb_source.py"):
            safe_print("❌ [ERREUR] Fichier agriweb_source.py non trouvé !")
            return False
            
        # Import dynamique avec gestion d'erreur
        import agriweb_source
        safe_print("✅ [IMPORT] Module agriweb_source importé avec succès")
        
        # Vérifier que l'app Flask existe
        if not hasattr(agriweb_source, 'app'):
            safe_print("❌ [ERREUR] Application Flask 'app' non trouvée dans agriweb_source !")
            return False
            
        app = agriweb_source.app
        safe_print("✅ [FLASK] Application Flask récupérée")
        
        # Compter les routes disponibles
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(rule.rule)
        
        safe_print(f"📊 [ROUTES] {len(routes)} routes détectées :")
        for i, route in enumerate(sorted(routes), 1):
            safe_print(f"   {i:2d}. {route}")
        
        safe_print("=" * 80)
        safe_print("🌐 [SERVEUR] Configuration du serveur Flask")
        safe_print("🔗 Interface Web: http://localhost:5000")
        safe_print("🗺️ GeoServer: http://localhost:8080/geoserver")
        safe_print("📊 Fonctionnalités: TOUTES les fonctionnalités AgriWeb")
        safe_print("🎯 Status: PRODUCTION READY")
        safe_print("=" * 80)
        
        # Configuration pour la production
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.config['DEBUG'] = True  # Mode debug pour développement
        
        # Démarrage du serveur Flask
        safe_print("🚀 [DÉMARRAGE] Lancement du serveur Flask...")
        safe_print("⏰ Démarrage en cours...")
        
        # Lancer le serveur
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            use_reloader=True,
            threaded=True
        )
        
    except ImportError as e:
        safe_print(f"❌ [ERREUR IMPORT] Erreur d'importation: {e}")
        safe_print("🔧 [SOLUTION] Vérifiez que toutes les dépendances sont installées:")
        safe_print("   - Flask")
        safe_print("   - Folium") 
        safe_print("   - Shapely")
        safe_print("   - GeoPandas")
        safe_print("   - PyProj")
        safe_print("   - Requests")
        return False
        
    except Exception as e:
        safe_print(f"❌ [ERREUR CRITIQUE] Erreur lors du démarrage: {e}")
        safe_print(f"📋 [TRACEBACK] {traceback.format_exc()}")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    if not success:
        safe_print("\n💡 [AIDE] Pour résoudre les problèmes:")
        safe_print("   1. Vérifiez que agriweb_source.py est dans le même dossier")
        safe_print("   2. Installez les dépendances manquantes")
        safe_print("   3. Vérifiez que le port 5000 est libre")
        safe_print("   4. Redémarrez le terminal et réessayez")
        sys.exit(1)
