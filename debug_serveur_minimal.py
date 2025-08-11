#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test de lancement avec gestion d'erreur explicite
"""

import sys
import traceback

def test_serveur_avec_debug():
    """Test le serveur avec gestion d'erreur complète"""
    
    try:
        print("🔧 [DEBUG] Import de agriweb_source...")
        import agriweb_source
        print("✅ [DEBUG] Import réussi")
        
        print("🔧 [DEBUG] Récupération de l'app Flask...")
        app = agriweb_source.app
        print(f"✅ [DEBUG] App récupérée: {type(app)}")
        
        print("🔧 [DEBUG] Tentative de lancement du serveur...")
        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
        print("✅ [DEBUG] Serveur lancé avec succès")
        
    except KeyboardInterrupt:
        print("🛑 [INFO] Arrêt par Ctrl+C")
        
    except Exception as e:
        print(f"❌ [ERREUR] Exception capturée: {e}")
        print(f"❌ [TYPE] Type d'erreur: {type(e)}")
        print("❌ [TRACEBACK] Traceback complet:")
        traceback.print_exc()
        
        # Chercher spécifiquement l'erreur WinError 233
        tb_str = traceback.format_exc()
        if "WinError 233" in tb_str:
            print("🎯 [IDENTIFIÉ] C'est bien l'erreur WinError 233!")
            
            # Extraire la ligne problématique
            lines = tb_str.split('\n')
            for i, line in enumerate(lines):
                if "agriweb_source.py" in line and "line" in line:
                    print(f"📍 [LIGNE] {line.strip()}")
                    if i + 1 < len(lines):
                        print(f"📝 [CODE] {lines[i+1].strip()}")

if __name__ == "__main__":
    test_serveur_avec_debug()
