#!/usr/bin/env python3
"""
🔧 Solution rapide pour le problème de connexion
Crée automatiquement un utilisateur de test et affiche les infos
"""

import json
import os
import hashlib
import secrets
from datetime import datetime

def hash_password(password):
    """Hash le mot de passe avec salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{password_hash.hex()}"

def create_quick_user():
    """Crée rapidement un utilisateur de test"""
    users_file = 'users.json'
    
    # Charger les utilisateurs existants
    users = {}
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
        except:
            pass
    
    # Créer l'utilisateur de test
    email = "admin@agriweb.fr"
    password = "admin123"
    
    user_data = {
        "id": secrets.token_hex(16),
        "email": email,
        "password": hash_password(password),
        "subscription": "premium",
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "is_active": True
    }
    
    users[email] = user_data
    
    # Sauvegarder
    try:
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        
        print("✅ UTILISATEUR DE TEST CRÉÉ AVEC SUCCÈS!")
        print("="*50)
        print(f"📧 Email: {email}")
        print(f"🔑 Mot de passe: {password}")
        print("="*50)
        print("🌐 Connectez-vous sur: http://127.0.0.1:5001")
        print("🔐 Utilisez ces identifiants pour vous connecter")
        print()
        
        # Vérifier si le fichier a été créé
        if os.path.exists(users_file):
            size = os.path.getsize(users_file)
            print(f"💾 Fichier users.json créé ({size} bytes)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        return False

if __name__ == "__main__":
    print("🚀 SOLUTION RAPIDE - CRÉATION D'UTILISATEUR")
    print("="*50)
    create_quick_user()
