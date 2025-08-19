#!/usr/bin/env python3
"""
🚀 LANCEUR AGRIWEB 2.0 AVEC AUTHENTIFICATION
Intègre l'authentification simple à votre application existante
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importer l'application existante
from agriweb_source import app

# Importer et appliquer l'authentification
from auth_simple import add_auth_to_app

if __name__ == '__main__':
    print("🔐 AgriWeb 2.0 avec Authentification")
    print("=" * 50)
    print("🌐 Interface: http://localhost:5000")
    print("🔐 Connexion: http://localhost:5000/auth")
    print("📊 Statut: http://localhost:5000/status")
    print("=" * 50)
    
    # Ajouter l'authentification à l'application
    add_auth_to_app(app)
    
    print("✅ Authentification intégrée")
    print("🚀 Démarrage du serveur...")
    
    # Lancer l'application
    app.run(host='127.0.0.1', port=5000, debug=False)
