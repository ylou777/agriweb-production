"""
Script de migration des données SQLite → PostgreSQL
Utilisez ce script pour migrer vos prospects existants vers Railway
"""

import os
import sys
import sqlite3

# Importer l'adaptateur Railway
sys.path.insert(0, os.path.dirname(__file__))
from database_adapter import get_db_connection, IS_RAILWAY

def migrate_prospects(sqlite_db_path):
    """Migre les prospects de SQLite vers PostgreSQL"""
    
    if not IS_RAILWAY:
        print("❌ Ce script doit être exécuté sur Railway (PostgreSQL)")
        print("   Pour l'utiliser, déployez d'abord sur Railway, puis exécutez :")
        print("   railway run python migrate_data.py")
        return
    
    if not os.path.exists(sqlite_db_path):
        print(f"❌ Fichier SQLite introuvable : {sqlite_db_path}")
        return
    
    print(f"📊 Migration depuis SQLite : {sqlite_db_path}")
    
    # Connexion SQLite
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # Compter les prospects
    count = sqlite_cursor.execute("SELECT COUNT(*) FROM agriweb_prospects").fetchone()[0]
    print(f"📈 {count} prospects à migrer")
    
    # Lire tous les prospects
    prospects = sqlite_cursor.execute("SELECT * FROM agriweb_prospects").fetchall()
    
    # Connexion PostgreSQL
    migrated = 0
    errors = 0
    
    with get_db_connection() as pg_conn:
        pg_cursor = pg_conn.cursor()
        
        for prospect in prospects:
            try:
                # Convertir Row en dict
                data = dict(prospect)
                prospect_id = data.pop('id')  # Retirer l'ID SQLite
                
                # Construire la requête d'insertion
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['%s'] * len(data))
                
                query = f"""
                    INSERT INTO agriweb_prospects ({columns})
                    VALUES ({placeholders})
                """
                
                pg_cursor.execute(query, list(data.values()))
                migrated += 1
                
                if migrated % 10 == 0:
                    print(f"   Migré : {migrated}/{count}")
                    
            except Exception as e:
                errors += 1
                print(f"⚠️ Erreur prospect #{prospect_id}: {e}")
        
        pg_conn.commit()
    
    sqlite_conn.close()
    
    print(f"\n✅ Migration terminée !")
    print(f"   ✓ Migrés : {migrated}")
    print(f"   ✗ Erreurs : {errors}")

if __name__ == "__main__":
    # Chemin vers votre base SQLite locale
    # Modifiez ce chemin selon votre configuration
    SQLITE_DB = "../KPI/kpi_sunstice.db"
    
    if len(sys.argv) > 1:
        SQLITE_DB = sys.argv[1]
    
    print("🔄 MIGRATION SQLite → PostgreSQL")
    print("="*50)
    migrate_prospects(SQLITE_DB)
