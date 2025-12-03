"""
Upload SQLite local vers PostgreSQL Railway
À exécuter APRÈS import_majic_to_sqlite.py
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
from tqdm import tqdm
import sys

def upload_to_railway(sqlite_db, pg_config):
    """Upload SQLite → PostgreSQL Railway"""
    
    print("=" * 80)
    print("📤 UPLOAD SQLITE → POSTGRESQL RAILWAY")
    print("=" * 80)
    print()
    
    # Connexion SQLite
    print(f"📂 Lecture SQLite: {sqlite_db}")
    sqlite_conn = sqlite3.connect(sqlite_db)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Compter les records
    count = sqlite_cursor.execute("SELECT COUNT(*) FROM proprietaires_parcelles").fetchone()[0]
    print(f"📊 {count:,} parcelles à uploader")
    print()
    
    # Connexion PostgreSQL Railway
    print("🔌 Connexion à Railway PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(**pg_config, connect_timeout=30)
        print("✅ Connecté à Railway")
    except Exception as e:
        print(f"❌ Erreur connexion Railway: {e}")
        print()
        print("💡 SOLUTION: Railway PostgreSQL n'est pas accessible depuis votre machine locale.")
        print("   Uploadez le fichier .db sur Railway et lancez ce script DEPUIS Railway:")
        print()
        print("   1. Uploadez proprietaires_parcelles.db dans votre projet Railway")
        print("   2. Sur Railway Shell, lancez:")
        print("      railway run python upload_sqlite_to_railway.py")
        sys.exit(1)
    
    # Créer la table sur Railway
    print("📋 Création table PostgreSQL...")
    with pg_conn.cursor() as cur:
        cur.execute("""
        DROP TABLE IF EXISTS proprietaires_parcelles CASCADE;
        
        CREATE TABLE proprietaires_parcelles (
            id SERIAL PRIMARY KEY,
            departement VARCHAR(3) NOT NULL,
            code_commune VARCHAR(5) NOT NULL,
            code_insee VARCHAR(5) NOT NULL,
            section VARCHAR(5) NOT NULL,
            numero VARCHAR(10) NOT NULL,
            siren VARCHAR(20),
            forme_juridique VARCHAR(100),
            denomination VARCHAR(255),
            contenance INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_proprietaires_commune_section_numero 
        ON proprietaires_parcelles(code_insee, section, numero);
        
        CREATE INDEX idx_proprietaires_siren 
        ON proprietaires_parcelles(siren);
        
        CREATE INDEX idx_proprietaires_departement 
        ON proprietaires_parcelles(departement);
        """)
        pg_conn.commit()
    print("✅ Table créée")
    print()
    
    # Upload par batch
    print("📤 Upload en cours...")
    batch_size = 10000
    offset = 0
    total_uploaded = 0
    
    with tqdm(total=count, desc="Upload") as pbar:
        while True:
            # Lire batch depuis SQLite
            rows = sqlite_cursor.execute(f"""
                SELECT departement, code_commune, code_insee, section, numero,
                       siren, forme_juridique, denomination, contenance
                FROM proprietaires_parcelles
                LIMIT {batch_size} OFFSET {offset}
            """).fetchall()
            
            if not rows:
                break
            
            # Insérer dans PostgreSQL
            insert_sql = """
            INSERT INTO proprietaires_parcelles 
            (departement, code_commune, code_insee, section, numero, siren, forme_juridique, denomination, contenance)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            with pg_conn.cursor() as cur:
                execute_batch(cur, insert_sql, rows, page_size=1000)
                pg_conn.commit()
            
            total_uploaded += len(rows)
            pbar.update(len(rows))
            offset += batch_size
    
    print()
    print("=" * 80)
    print(f"✅ UPLOAD TERMINÉ")
    print(f"📊 {total_uploaded:,} parcelles uploadées sur Railway")
    print("=" * 80)
    
    # Fermer connexions
    sqlite_conn.close()
    pg_conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload SQLite → Railway PostgreSQL")
    parser.add_argument(
        "--sqlite-db",
        default="proprietaires_parcelles.db",
        help="Fichier SQLite source"
    )
    parser.add_argument(
        "--db-host",
        default="viaduct.proxy.rlwy.net",
        help="Host PostgreSQL Railway"
    )
    parser.add_argument(
        "--db-port",
        type=int,
        default=21260,
        help="Port PostgreSQL"
    )
    parser.add_argument(
        "--db-name",
        default="railway",
        help="Nom de la base"
    )
    parser.add_argument(
        "--db-user",
        default="postgres",
        help="Utilisateur PostgreSQL"
    )
    parser.add_argument(
        "--db-password",
        default="bXrjKvPXzSPAqKrDXKhdMIGXLMlPWcpQ",
        help="Mot de passe PostgreSQL"
    )
    
    args = parser.parse_args()
    
    pg_config = {
        'host': args.db_host,
        'port': args.db_port,
        'database': args.db_name,
        'user': args.db_user,
        'password': args.db_password
    }
    
    try:
        upload_to_railway(args.sqlite_db, pg_config)
    except KeyboardInterrupt:
        print("\n⚠️  Upload interrompu")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
