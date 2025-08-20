#!/usr/bin/env python3
"""
Point d'entrée Railway - Simplifié
Lance directement agriweb_railway_deploy.py
"""

import sys
import os

print("🚀 RAILWAY STARTUP - Démarrage AgriWeb")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")

# Import direct de notre module
try:
    print("📝 Import de agriweb_railway_deploy...")
    import agriweb_railway_deploy
    print("✅ Import réussi")
    
    print("🌾 Lancement de l'application AgriWeb...")
    agriweb_railway_deploy.main()
    
except Exception as e:
    print(f"❌ Erreur de démarrage: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
