#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de réparation du compte ylaurent.perso@gmail.com
Supprime et recrée le compte proprement
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta

DATABASE_PATH = "agriweb_users.db"

def hash_password(password, salt=None):
    """Hash sécurisé d'un mot de passe avec sel"""
    if salt is None:
        salt = secrets.token_hex(32)
    
    # PBKDF2 avec 100,000 itérations pour sécurité renforcée
    password_hash = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        100000
    )
    return password_hash.hex(), salt

def fix_ylaurent_account():
    """Répare le compte ylaurent.perso@gmail.com"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        email = "ylaurent.perso@gmail.com"
        name = "Yann Laurent"
        company = "AgriWeb User"
        password = "AgriWeb2025!"  # Mot de passe temporaire fort
        
        print("🔧 RÉPARATION DU COMPTE YLAURENT")
        print("=" * 50)
        
        # 1. Supprimer l'ancien compte s'il existe
        print("1. Suppression de l'ancien compte...")
        cursor.execute('DELETE FROM users WHERE email = ?', (email,))
        deleted_count = cursor.rowcount
        print(f"   ✅ {deleted_count} ancien(s) compte(s) supprimé(s)")
        
        # 2. Hasher le nouveau mot de passe
        print("2. Génération du hash sécurisé...")
        password_hash, salt = hash_password(password)
        print("   ✅ Hash généré")
        
        # 3. Calculer les dates d'essai
        trial_start = datetime.now()
        trial_end = trial_start + timedelta(days=30)
        
        # 4. Créer le nouveau compte
        print("3. Création du nouveau compte...")
        cursor.execute('''
            INSERT INTO users (
                email, name, company, password_hash, salt,
                is_email_verified, subscription_status,
                trial_start_date, trial_end_date,
                is_admin, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            email, name, company, password_hash, salt,
            1,  # Email vérifié
            'trial',  # Statut d'essai
            trial_start.isoformat(),
            trial_end.isoformat(),
            0,  # Pas admin
            1,  # Actif
            trial_start.isoformat()
        ))
        
        conn.commit()
        user_id = cursor.lastrowid
        print(f"   ✅ Compte créé avec ID: {user_id}")
        
        # 5. Vérification
        print("4. Vérification du compte...")
        cursor.execute('''
            SELECT email, name, is_email_verified, subscription_status
            FROM users WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        if user:
            print(f"   ✅ Email: {user[0]}")
            print(f"   ✅ Nom: {user[1]}")
            print(f"   ✅ Vérifié: {user[2]}")
            print(f"   ✅ Statut: {user[3]}")
        
        conn.close()
        
        print("\n🎉 RÉPARATION TERMINÉE !")
        print("=" * 50)
        print(f"📧 Email: {email}")
        print(f"🔐 Mot de passe temporaire: {password}")
        print("🌐 URL de connexion: https://ample-manifestation-production-7b1a.up.railway.app/auth/login")
        print("\n💡 Après connexion, vous pourrez changer le mot de passe via le profil.")
        
        return True, f"Compte {email} réparé avec succès"
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False, str(e)

if __name__ == "__main__":
    success, message = fix_ylaurent_account()
    if success:
        print(f"\n✅ {message}")
    else:
        print(f"\n❌ {message}")
