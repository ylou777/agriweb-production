#!/usr/bin/env python3
"""
🚀 LANCEUR COMPLET AGRIWEB 2.0 COMMERCIAL
Démarre le système commercial complet
"""

import subprocess
import sys
import time
import os

def start_servers():
    print("🚀 Démarrage AgriWeb 2.0 - Système Commercial Complet")
    print("=" * 70)
    
    # Démarrer l'application backend AgriWeb sur le port 5001
    print("📊 1. Démarrage du backend AgriWeb (port 5001)...")
    backend_process = subprocess.Popen([
        sys.executable, "agriweb_backend.py"
    ], cwd=os.path.dirname(os.path.abspath(__file__)))
    
    # Attendre 3 secondes
    time.sleep(3)
    
    # Démarrer le système commercial sur le port 5000
    print("🏪 2. Démarrage du système commercial (port 5000)...")
    commercial_process = subprocess.Popen([
        sys.executable, "production_commercial.py"
    ], cwd=os.path.dirname(os.path.abspath(__file__)))
    
    print("=" * 70)
    print("✅ SYSTÈME OPÉRATIONNEL")
    print("🌐 Site commercial: http://localhost:5000")
    print("🔐 Connexion: http://localhost:5000/login")
    print("🎯 Application: http://localhost:5000/app")
    print("👥 Administration: http://localhost:5000/admin")
    print("📊 Backend AgriWeb: http://localhost:5001")
    print("=" * 70)
    print("💡 Fonctionnalités:")
    print("   - Essai gratuit 7 jours")
    print("   - Authentification complète")
    print("   - Interface commerciale")
    print("   - Gestion des licences")
    print("   - Administration des utilisateurs")
    print("=" * 70)
    
    try:
        # Attendre que les processus se terminent
        backend_process.wait()
        commercial_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt des serveurs...")
        backend_process.terminate()
        commercial_process.terminate()
        print("✅ Serveurs arrêtés")

if __name__ == '__main__':
    start_servers()
