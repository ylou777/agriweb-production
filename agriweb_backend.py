#!/usr/bin/env python3
"""
🌾 AGRIWEB 2.0 - APPLICATION BACKEND
Lance l'application AgriWeb sur le port 5001 pour intégration commerciale
"""

import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    print("🌾 AgriWeb 2.0 - Backend Application")
    print("🌐 Interface backend: http://localhost:5001")
    print("🔗 Intégré avec le système commercial sur le port 5000")
    
    # Importer et lancer l'application sur le port 5001
    from agriweb_source import app
    
    app.run(host='127.0.0.1', port=5001, debug=False)
