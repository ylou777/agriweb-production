#!/usr/bin/env python3
"""
Test de l'inscription utilisateur - AgriWeb 2.0
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

try:
    from agriweb_hebergement_gratuit import SimpleUserManager
    
    def test_user_registration():
        print("🧪 Test d'inscription utilisateur...")
        
        # Créer une instance du gestionnaire
        user_manager = SimpleUserManager()
        
        # Test de création d'utilisateur
        email = "test@example.com"
        password = "motdepasse123"
        name = "Utilisateur Test"
        
        try:
            user_id = user_manager.create_user(email, password, name)
            print(f"✅ Utilisateur créé avec ID: {user_id}")
            
            # Test d'authentification
            user = user_manager.authenticate_user(email, password)
            if user:
                print(f"✅ Authentification réussie: {user['name']} ({user['email']})")
                print(f"📊 Type de licence: {user['license_type']}")
                print(f"🔍 Recherches disponibles: {user['searches_limit'] - user['searches_used']}")
                return True
            else:
                print("❌ Échec de l'authentification")
                return False
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    if __name__ == "__main__":
        success = test_user_registration()
        if success:
            print("\n🎉 Test d'inscription réussi!")
        else:
            print("\n💥 Test d'inscription échoué!")
        
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("Assurez-vous que agriweb_hebergement_gratuit.py est dans le même répertoire")
