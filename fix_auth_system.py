# -*- coding: utf-8 -*-
"""
Script de diagnostic et réactivation du système d'authentification
"""

import sqlite3
from datetime import datetime, timedelta

DATABASE_PATH = "agriweb_users.db"

def check_and_fix_auth_system():
    """Diagnostique et répare le système d'authentification"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print("=" * 60)
        print("🔍 DIAGNOSTIC DU SYSTÈME D'AUTHENTIFICATION")
        print("=" * 60)
        
        # 1. Vérifier la table users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        print(f"\n📊 Total utilisateurs: {total_users}")
        
        # 2. Vérifier les utilisateurs non vérifiés
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_email_verified = 0")
        unverified = cursor.fetchone()[0]
        print(f"❌ Utilisateurs non vérifiés: {unverified}")
        
        # 3. Vérifier les utilisateurs vérifiés
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_email_verified = 1")
        verified = cursor.fetchone()[0]
        print(f"✅ Utilisateurs vérifiés: {verified}")
        
        # 4. Vérifier les admin
        cursor.execute("SELECT email, name, is_email_verified FROM users WHERE is_admin = 1")
        admins = cursor.fetchall()
        print(f"\n👑 Administrateurs ({len(admins)}):")
        for admin in admins:
            status = "✅ Vérifié" if admin[2] else "❌ Non vérifié"
            print(f"   • {admin[1]} ({admin[0]}) - {status}")
        
        # 5. Lister tous les utilisateurs
        cursor.execute("SELECT id, email, name, is_email_verified, is_admin, subscription_status, created_at FROM users")
        all_users = cursor.fetchall()
        print(f"\n📋 LISTE DES UTILISATEURS:")
        print("-" * 100)
        for user in all_users:
            verified_icon = "✅" if user[3] else "❌"
            admin_icon = "👑" if user[4] else "👤"
            print(f"{admin_icon} {verified_icon} {user[2]} ({user[1]}) - {user[5]} - Créé: {user[6]}")
        
        print("\n" + "=" * 60)
        print("🔧 OPTIONS DE RÉPARATION")
        print("=" * 60)
        
        # Option 1: Auto-vérifier tous les utilisateurs non vérifiés
        if unverified > 0:
            print(f"\n1️⃣  Auto-vérifier les {unverified} utilisateurs non vérifiés")
            response = input("   Voulez-vous activer cette option? (o/N): ")
            if response.lower() == 'o':
                cursor.execute("""
                    UPDATE users 
                    SET is_email_verified = 1, 
                        email_verification_token = NULL,
                        email_verification_expires = NULL
                    WHERE is_email_verified = 0
                """)
                conn.commit()
                print(f"   ✅ {unverified} utilisateur(s) vérifiés automatiquement")
        
        # Option 2: Créer un compte admin test
        print(f"\n2️⃣  Créer un compte admin de test")
        response = input("   Voulez-vous créer un admin test (admin@sunstice.com)? (o/N): ")
        if response.lower() == 'o':
            import hashlib
            import secrets
            
            # Vérifier si admin existe
            cursor.execute("SELECT id FROM users WHERE email = ?", ('admin@sunstice.com',))
            if cursor.fetchone():
                print("   ⚠️  Admin admin@sunstice.com existe déjà")
                response2 = input("   Réinitialiser son mot de passe? (o/N): ")
                if response2.lower() == 'o':
                    salt = secrets.token_hex(32)
                    password = "Admin123!"
                    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
                    
                    cursor.execute("""
                        UPDATE users 
                        SET password_hash = ?, salt = ?, is_email_verified = 1, is_admin = 1, is_active = 1
                        WHERE email = ?
                    """, (password_hash, salt, 'admin@sunstice.com'))
                    conn.commit()
                    print(f"   ✅ Mot de passe réinitialisé pour admin@sunstice.com")
                    print(f"   🔑 Email: admin@sunstice.com")
                    print(f"   🔑 Mot de passe: Admin123!")
            else:
                salt = secrets.token_hex(32)
                password = "Admin123!"
                password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
                
                trial_end = datetime.now() + timedelta(days=365)
                
                cursor.execute("""
                    INSERT INTO users (
                        email, name, company, password_hash, salt, 
                        is_email_verified, is_admin, is_active,
                        subscription_status, trial_end_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'admin@sunstice.com', 'Administrateur Sunstice', 'Sunstice',
                    password_hash, salt, 1, 1, 1, 'active', trial_end
                ))
                conn.commit()
                print(f"   ✅ Compte admin créé avec succès !")
                print(f"   🔑 Email: admin@sunstice.com")
                print(f"   🔑 Mot de passe: Admin123!")
        
        # Option 3: Vérifier un utilisateur spécifique
        print(f"\n3️⃣  Vérifier un utilisateur spécifique")
        response = input("   Entrez l'email de l'utilisateur à vérifier (ou Entrée pour passer): ")
        if response.strip():
            cursor.execute("SELECT id, is_email_verified FROM users WHERE email = ?", (response.strip().lower(),))
            user = cursor.fetchone()
            if user:
                if not user[1]:
                    cursor.execute("UPDATE users SET is_email_verified = 1 WHERE id = ?", (user[0],))
                    conn.commit()
                    print(f"   ✅ Utilisateur {response.strip()} vérifié avec succès")
                else:
                    print(f"   ℹ️  Utilisateur {response.strip()} déjà vérifié")
            else:
                print(f"   ❌ Utilisateur {response.strip()} introuvable")
        
        # Option 4: Prolonger l'essai de tous les utilisateurs
        print(f"\n4️⃣  Prolonger l'essai de tous les utilisateurs (30 jours)")
        response = input("   Voulez-vous activer cette option? (o/N): ")
        if response.lower() == 'o':
            new_trial_end = datetime.now() + timedelta(days=30)
            cursor.execute("UPDATE users SET trial_end_date = ?", (new_trial_end,))
            conn.commit()
            print(f"   ✅ Essai prolongé jusqu'au {new_trial_end.strftime('%d/%m/%Y')}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ DIAGNOSTIC ET RÉPARATIONS TERMINÉS")
        print("=" * 60)
        print("\n📝 Prochaines étapes:")
        print("   1. Redémarrez votre serveur Flask si nécessaire")
        print("   2. Testez la connexion sur /auth/login")
        print("   3. Vérifiez que les utilisateurs peuvent se connecter")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    check_and_fix_auth_system()
