#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de démarrage debug pour AgriWeb
Évite les blocages au démarrage
"""

import os
import sys

# Configuration pour éviter les blocages
os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONUNBUFFERED'] = '1'

# Désactiver temporairement les vérifications externes qui peuvent bloquer
os.environ['SKIP_GEOSERVER_CHECK'] = '1'
os.environ['SKIP_NGROK_CHECK'] = '1'

print("🚀 [DEBUG] Démarrage AgriWeb en mode debug...")
print("🔧 [DEBUG] Variables d'environnement configurées")

try:
    # Importer et démarrer l'application
    from agriweb_hebergement_gratuit import app
    
    print("✅ [DEBUG] Application importée avec succès")
    print("🌐 [DEBUG] Démarrage sur http://localhost:5000")
    
    # Démarrer le serveur avec configuration simple
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=False,
        use_reloader=False,  # Éviter les rechargements automatiques
        threaded=True
    )
    
except Exception as e:
    print(f"❌ [DEBUG] Erreur au démarrage: {e}")
    import traceback
    traceback.print_exc()
    input("Appuyez sur Entrée pour fermer...")
