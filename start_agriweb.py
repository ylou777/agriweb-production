#!/usr/bin/env python3
"""
🚀 DÉMARRAGE SIMPLIFIÉ AGRIWEB 2.0
Lance votre application AgriWeb directement sans authentification
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    print("🌾 AgriWeb 2.0 - Démarrage Direct")
    print("=" * 50)
    print("🌐 Interface: http://localhost:5000")
    print("📊 Toutes les fonctionnalités disponibles")
    print("✅ Accès direct sans authentification")
    print("=" * 50)
    
    # Importer et lancer l'application directement
    from agriweb_source import app
    
    print("🚀 Lancement du serveur...")
    app.run(host='127.0.0.1', port=5000, debug=False)
