"""
Migration SQLite locale - Isolation des données par utilisateur
Pour la base de données locale (dev)
"""

import sqlite3
import os

# Utiliser le même chemin que database_adapter
DB_PATH = os.getenv('KPI_DATABASE_PATH', 
                   os.path.join(os.path.dirname(__file__), 'KPI', 'kpi_sunstice.db'))

def migrate_sqlite():
    """Migration pour SQLite local"""
    try:
        print("\n" + "="*70)
        print("🔄 [MIGRATION SQLITE] Isolation des données par utilisateur")
        print("="*70)
        print(f"📁 Base de données: {DB_PATH}")
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Vérifier si user_id existe
        print("\n1️⃣ Vérification colonne user_id...")
        cursor.execute("PRAGMA table_info(agriweb_prospects)")
        columns = [row['name'] for row in cursor.fetchall()]
        
        if 'user_id' in columns:
            print("   ✅ Colonne user_id existe déjà")
        else:
            print("   ➕ Ajout colonne user_id...")
            cursor.execute("ALTER TABLE agriweb_prospects ADD COLUMN user_id TEXT")
            conn.commit()
            print("   ✅ Colonne ajoutée")
        
        # 2. Vérifier table users
        print("\n2️⃣ Vérification table users...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            print("   ✅ Table users trouvée")
        else:
            print("   ⚠️  Table users n'existe pas")
            print("   💡 Lancez l'application Flask une fois pour créer les tables")
            conn.close()
            return False
        
        # 3. Compter prospects sans user_id
        print("\n3️⃣ Analyse des prospects...")
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN user_id IS NULL THEN 1 ELSE 0 END) as sans_user
            FROM agriweb_prospects
        """)
        row = cursor.fetchone()
        total = row['total']
        sans_user = row['sans_user']
        
        print(f"   📊 Total prospects: {total}")
        print(f"   🔴 Sans user_id: {sans_user}")
        
        if sans_user > 0:
            # 4. Trouver un utilisateur par défaut
            print("\n4️⃣ Recherche utilisateur par défaut...")
            cursor.execute("""
                SELECT id, email, name 
                FROM users 
                WHERE is_admin = 1
                ORDER BY id 
                LIMIT 1
            """)
            admin_user = cursor.fetchone()
            
            if not admin_user:
                cursor.execute("SELECT id, email, name FROM users ORDER BY id LIMIT 1")
                admin_user = cursor.fetchone()
            
            if not admin_user:
                print("   ❌ Aucun utilisateur trouvé")
                print("   💡 Inscrivez-vous via /register d'abord")
                conn.close()
                return False
            
            print(f"   👤 Utilisateur: {admin_user['email']}")
            
            # 5. Assigner les prospects
            print(f"\n5️⃣ Attribution de {sans_user} prospects...")
            cursor.execute("""
                UPDATE agriweb_prospects 
                SET user_id = ? 
                WHERE user_id IS NULL
            """, (admin_user['id'],))
            conn.commit()
            print(f"   ✅ {sans_user} prospects attribués à {admin_user['email']}")
        else:
            print("   ✅ Tous les prospects ont déjà un user_id")
        
        # 6. Vérification finale
        print("\n6️⃣ Vérification finale...")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN user_id IS NOT NULL THEN 1 ELSE 0 END) as avec_user,
                SUM(CASE WHEN user_id IS NULL THEN 1 ELSE 0 END) as sans_user
            FROM agriweb_prospects
        """)
        row = cursor.fetchone()
        
        print(f"   📊 Résultat:")
        print(f"      • Total: {row['total']}")
        print(f"      • Avec user_id: {row['avec_user']}")
        print(f"      • Sans user_id: {row['sans_user']}")
        
        conn.close()
        
        print("\n" + "="*70)
        print("✅ Migration SQLite réussie !")
        print("="*70)
        print("\n💡 Prochaines étapes:")
        print("   1. Relancer l'application Flask")
        print("   2. Les prospects sont maintenant isolés par utilisateur")
        print("   3. Les admins voient tous les prospects")
        print("\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_sqlite()
    if success:
        print("✅ Migration terminée")
    else:
        print("❌ Migration échouée")
