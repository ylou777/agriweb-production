#!/usr/bin/env python3
"""
Point d'entrée Railway avec CRM et PostgreSQL
Lance AgriWeb avec support base de données adaptative
"""

import sys
import os

print("🚀 RAILWAY STARTUP - AgriWeb avec CRM")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

# Initialiser la base de données
try:
    print("📊 Initialisation de la base de données...")
    import database_adapter
    database_adapter.init_database()
    print("✅ Base de données initialisée")
except Exception as e:
    print(f"⚠️ Avertissement init DB: {e}")

# Démarrer l'application
try:
    print("📝 Import de agriweb_railway_deploy...")
    import agriweb_railway_deploy
    print("✅ Import réussi")
    
    print("🌾 Lancement de l'application AgriWeb avec CRM...")
    agriweb_railway_deploy.main()
    
except Exception as e:
    print(f"❌ Erreur de démarrage: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
