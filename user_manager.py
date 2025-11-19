#!/usr/bin/env python3
"""
🔧 Utilitaire de gestion des utilisateurs AgriWeb
Permet de créer, supprimer et réinitialiser les utilisateurs
"""

import json
import os
import hashlib
import secrets
from datetime import datetime

class UserManagerUtils:
    def __init__(self):
        self.users_file = 'users.json'
        self.load_users()
    
    def load_users(self):
        """Charge les utilisateurs depuis le fichier"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            else:
                self.users = {}
        except Exception as e:
            print(f"Erreur lecture users.json: {e}")
            self.users = {}
    
    def save_users(self):
        """Sauvegarde les utilisateurs dans le fichier"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erreur sauvegarde users.json: {e}")
            return False
    
    def hash_password(self, password):
        """Hash le mot de passe avec salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def create_test_user(self, email="test@agriweb.fr", password="test123"):
        """Crée un utilisateur de test"""
        user_data = {
            "id": secrets.token_hex(16),
            "email": email.lower(),
            "password": self.hash_password(password),
            "subscription": "premium",
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "is_active": True
        }
        
        self.users[email.lower()] = user_data
        if self.save_users():
            print(f"✅ Utilisateur créé avec succès:")
            print(f"   📧 Email: {email}")
            print(f"   🔑 Mot de passe: {password}")
            print(f"   🆔 ID: {user_data['id']}")
            return True
        else:
            print("❌ Erreur lors de la création")
            return False
    
    def list_users(self):
        """Liste tous les utilisateurs"""
        if not self.users:
            print("👥 Aucun utilisateur trouvé")
            return
        
        print(f"👥 {len(self.users)} utilisateur(s) trouvé(s):")
        for email, user in self.users.items():
            status = "🟢 Actif" if user.get('is_active', True) else "🔴 Inactif"
            subscription = user.get('subscription', 'trial')
            last_login = user.get('last_login', 'Jamais')
            print(f"   📧 {email}")
            print(f"      {status} | 💎 {subscription} | 🕒 Dernière connexion: {last_login}")
            print()
    
    def delete_user(self, email):
        """Supprime un utilisateur"""
        email = email.lower()
        if email in self.users:
            del self.users[email]
            if self.save_users():
                print(f"✅ Utilisateur {email} supprimé")
                return True
        print(f"❌ Utilisateur {email} non trouvé")
        return False
    
    def reset_all_users(self):
        """Supprime tous les utilisateurs"""
        self.users = {}
        if self.save_users():
            print("✅ Tous les utilisateurs ont été supprimés")
            return True
        print("❌ Erreur lors de la suppression")
        return False
    
    def verify_user_login(self, email, password):
        """Vérifie les identifiants d'un utilisateur"""
        email = email.lower()
        if email not in self.users:
            print(f"❌ Utilisateur {email} non trouvé")
            return False
        
        user = self.users[email]
        stored_password = user['password']
        
        if ':' in stored_password:
            salt, hash_hex = stored_password.split(':', 1)
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            if password_hash.hex() == hash_hex:
                print(f"✅ Identifiants corrects pour {email}")
                return True
            else:
                print(f"❌ Mot de passe incorrect pour {email}")
                return False
        else:
            print(f"❌ Format de mot de passe invalide pour {email}")
            return False

def main():
    """Menu principal"""
    utils = UserManagerUtils()
    
    while True:
        print("\n" + "="*50)
        print("🔧 GESTIONNAIRE D'UTILISATEURS AGRIWEB")
        print("="*50)
        print("1. 👥 Lister les utilisateurs")
        print("2. ➕ Créer un utilisateur de test")
        print("3. ➕ Créer un utilisateur personnalisé")
        print("4. ✅ Vérifier identifiants")
        print("5. 🗑️  Supprimer un utilisateur")
        print("6. 🔄 Réinitialiser tous les utilisateurs")
        print("7. 🚪 Quitter")
        print()
        
        choice = input("Votre choix (1-7): ").strip()
        
        if choice == '1':
            utils.list_users()
        
        elif choice == '2':
            print("\n🛠️ Création d'un utilisateur de test...")
            utils.create_test_user()
        
        elif choice == '3':
            print("\n🛠️ Création d'un utilisateur personnalisé...")
            email = input("📧 Email: ").strip()
            password = input("🔑 Mot de passe: ").strip()
            if email and password:
                utils.create_test_user(email, password)
            else:
                print("❌ Email et mot de passe requis")
        
        elif choice == '4':
            print("\n🔍 Vérification des identifiants...")
            email = input("📧 Email: ").strip()
            password = input("🔑 Mot de passe: ").strip()
            if email and password:
                utils.verify_user_login(email, password)
            else:
                print("❌ Email et mot de passe requis")
        
        elif choice == '5':
            print("\n🗑️ Suppression d'un utilisateur...")
            email = input("📧 Email à supprimer: ").strip()
            if email:
                utils.delete_user(email)
            else:
                print("❌ Email requis")
        
        elif choice == '6':
            print("\n⚠️ ATTENTION: Cette action supprimera TOUS les utilisateurs!")
            confirm = input("Tapez 'OUI' pour confirmer: ").strip().upper()
            if confirm == 'OUI':
                utils.reset_all_users()
            else:
                print("❌ Annulé")
        
        elif choice == '7':
            print("👋 Au revoir!")
            break
        
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main()
