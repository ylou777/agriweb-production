"""
Migration pour ajouter l'isolation des données par utilisateur
- Ajoute la colonne user_id à agriweb_prospects
- Assigne les prospects existants à un utilisateur par défaut
- Compatible SQLite ET PostgreSQL
"""

import os
from database_adapter import execute_query, get_db_connection

def is_sqlite():
    """Détecte si on utilise SQLite ou PostgreSQL"""
    db_url = os.getenv('DATABASE_URL', '')
    return 'sqlite' in db_url.lower() or not db_url or db_url.startswith('sqlite://')

def migrate_add_user_id():
    """Ajoute la colonne user_id à la table agriweb_prospects"""
    try:
        print("\n" + "="*70)
        print("🔄 [MIGRATION] Ajout de l'isolation des données par utilisateur")
        print("="*70)
        
        sqlite_mode = is_sqlite()
        db_type = "SQLite" if sqlite_mode else "PostgreSQL"
        print(f"\n💾 Base de données: {db_type}")
        
        # 1. Vérifier si la colonne existe déjà
        print("\n1️⃣ Vérification de la colonne user_id...")
        
        if sqlite_mode:
            # SQLite: utiliser PRAGMA
            check = execute_query("PRAGMA table_info(agriweb_prospects)", fetch_all=True)
            column_exists = any(col['name'] == 'user_id' for col in (check or []))
        else:
            # PostgreSQL: utiliser information_schema
            check = execute_query("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'agriweb_prospects' 
                AND column_name = 'user_id'
            """, fetch_one=True)
            column_exists = check is not None
        
        if column_exists:
            print("   ℹ️  La colonne user_id existe déjà")
        else:
            print("   ➕ Ajout de la colonne user_id...")
            if sqlite_mode:
                execute_query("ALTER TABLE agriweb_prospects ADD COLUMN user_id TEXT")
            else:
                execute_query("ALTER TABLE agriweb_prospects ADD COLUMN user_id VARCHAR(36)")
            print("   ✅ Colonne user_id ajoutée")
        
        # 2. Vérifier si la table users existe
        print("\n2️⃣ Vérification de la table users...")
        
        if sqlite_mode:
            # SQLite: vérifier dans sqlite_master
            users_check = execute_query("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='users'
            """, fetch_one=True)
            users_exists = users_check is not None
        else:
            # PostgreSQL: utiliser information_schema
            users_check = execute_query("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                ) as exists
            """, fetch_one=True)
            users_exists = users_check and users_check.get('exists')
        
        if not users_exists:
            print("   ⚠️  Table users n'existe pas - création nécessaire")
            print("   💡 Exécutez d'abord le script de création de la table users")
            return False
        else:
            print("   ✅ Table users trouvée")
        
        # 3. Compter les prospects sans user_id
        print("\n3️⃣ Analyse des prospects existants...")
        count = execute_query("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN user_id IS NULL THEN 1 END) as sans_user
            FROM agriweb_prospects
        """, fetch_one=True)
        
        print(f"   📊 Total prospects: {count['total']}")
        print(f"   🔴 Sans user_id: {count['sans_user']}")
        
        if count['sans_user'] > 0:
            # 4. Récupérer le premier utilisateur (admin)
            print("\n4️⃣ Recherche d'un utilisateur par défaut...")
            
            if sqlite_mode:
                # SQLite: requête simple
                admin_user = execute_query("""
                    SELECT id, email, name 
                    FROM users 
                    WHERE is_admin = 1
                    ORDER BY created_at 
                    LIMIT 1
                """, fetch_one=True)
                
                if not admin_user:
                    admin_user = execute_query("""
                        SELECT id, email, name 
                        FROM users 
                        ORDER BY created_at 
                        LIMIT 1
                    """, fetch_one=True)
            else:
                # PostgreSQL
                admin_user = execute_query("""
                    SELECT id, email, name 
                    FROM users 
                    WHERE role = 'admin' OR is_admin = true
                    ORDER BY created_at 
                    LIMIT 1
                """, fetch_one=True)
                
                if not admin_user:
                    admin_user = execute_query("""
                        SELECT id, email, name 
                        FROM users 
                        ORDER BY created_at 
                        LIMIT 1
                    """, fetch_one=True)
            
            if not admin_user:
                print("   ❌ Aucun utilisateur trouvé dans la base")
                print("   💡 Créez d'abord un utilisateur via /register")
                return False
            
            print(f"   👤 Utilisateur par défaut: {admin_user['email']} ({admin_user['name']})")
            
            # 5. Assigner les prospects à cet utilisateur
            print(f"\n5️⃣ Attribution des {count['sans_user']} prospects à {admin_user['email']}...")
            
            if sqlite_mode:
                execute_query("""
                    UPDATE agriweb_prospects 
                    SET user_id = ? 
                    WHERE user_id IS NULL
                """, (admin_user['id'],))
            else:
                execute_query("""
                    UPDATE agriweb_prospects 
                    SET user_id = %s 
                    WHERE user_id IS NULL
                """, (admin_user['id'],))
            
            print(f"   ✅ {count['sans_user']} prospects attribués")
        else:
            print("   ✅ Tous les prospects ont déjà un user_id")
        
        # 6. Ajouter une contrainte foreign key (optionnel mais recommandé)
        print("\n6️⃣ Vérification des contraintes...")
        
        if sqlite_mode:
            print("   ℹ️  SQLite: Foreign keys gérées au niveau de la base")
            print("   ⚠️  Pour activer: PRAGMA foreign_keys = ON;")
        else:
            # PostgreSQL: vérifier et ajouter FK
            fk_check = execute_query("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'agriweb_prospects' 
                AND constraint_name = 'fk_prospects_user_id'
            """, fetch_one=True)
            
            if not fk_check:
                print("   ➕ Ajout de la contrainte foreign key...")
                try:
                    execute_query("""
                        ALTER TABLE agriweb_prospects 
                        ADD CONSTRAINT fk_prospects_user_id 
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                    """)
                    print("   ✅ Contrainte foreign key ajoutée")
                except Exception as e:
                    print(f"   ⚠️  Impossible d'ajouter la contrainte FK: {e}")
                    print("   ℹ️  Ce n'est pas bloquant, la migration continue")
            else:
                print("   ✅ Contrainte foreign key existe déjà")
        
        # 7. Vérification finale
        print("\n7️⃣ Vérification finale...")
        final_count = execute_query("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN user_id IS NOT NULL THEN 1 END) as avec_user,
                COUNT(CASE WHEN user_id IS NULL THEN 1 END) as sans_user
            FROM agriweb_prospects
        """, fetch_one=True)
        
        print(f"   📊 Résultat:")
        print(f"      • Total prospects: {final_count['total']}")
        print(f"      • Avec user_id: {final_count['avec_user']}")
        print(f"      • Sans user_id: {final_count['sans_user']}")
        
        print("\n" + "="*70)
        print("✅ Migration terminée avec succès !")
        print("="*70)
        print("\n💡 Prochaines étapes:")
        print("   1. Redémarrez l'application Flask")
        print("   2. Les utilisateurs ne verront que leurs propres prospects")
        print("   3. Les nouveaux prospects seront automatiquement associés au créateur")
        print("\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_add_user_id()
    if success:
        print("✅ Migration réussie")
    else:
        print("❌ Migration échouée - vérifiez les logs ci-dessus")
