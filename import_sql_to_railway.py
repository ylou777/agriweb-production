"""
Import du fichier SQL compressé vers Railway PostgreSQL
Utilise les credentials Railway pour connexion directe
"""

import os
import gzip
import psycopg2
from tqdm import tqdm

def import_sql_to_railway():
    """Importe le fichier SQL.gz directement dans Railway PostgreSQL"""
    
    # Chemins des fichiers
    sql_gz_path = r"C:\Users\Utilisateur\Desktop\AG32.1\proprietaires_parcelles.sql.gz"
    
    print("=" * 80)
    print("IMPORT PROPRIÉTAIRES MAJIC VERS RAILWAY POSTGRESQL")
    print("=" * 80)
    
    # Vérifier que le fichier existe
    if not os.path.exists(sql_gz_path):
        print(f"❌ Fichier SQL.gz introuvable: {sql_gz_path}")
        return
    
    file_size_mb = os.path.getsize(sql_gz_path) / (1024 * 1024)
    print(f"\n📁 Fichier: {sql_gz_path}")
    print(f"📊 Taille: {file_size_mb:.2f} MB (compressé)")
    
    # Connexion Railway PostgreSQL avec les credentials de l'interface
    DATABASE_URL = "postgresql://postgres:WbjgkcXDKvbbYJhWprDDQQobbpnggYJc@viaduct.proxy.rlwy.net:21260/railway"
    
    print(f"\n🔌 Connexion à Railway PostgreSQL...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cursor = conn.cursor()
        print("✅ Connexion établie")
        
        # Décompresser et lire le SQL
        print(f"\n📂 Décompression et lecture du fichier SQL...")
        
        with gzip.open(sql_gz_path, 'rt', encoding='utf-8') as f:
            sql_content = f.read()
        
        print(f"✅ Fichier décompressé: {len(sql_content) / (1024*1024):.2f} MB")
        
        # Séparer les commandes SQL
        print(f"\n⚙️  Exécution des commandes SQL...")
        
        # Exécuter DROP TABLE si existe
        print("  - Suppression de la table existante (si elle existe)...")
        cursor.execute("DROP TABLE IF EXISTS proprietaires_parcelles CASCADE;")
        
        # Exécuter CREATE TABLE
        print("  - Création de la table...")
        create_table_start = sql_content.find("CREATE TABLE")
        create_table_end = sql_content.find(");", create_table_start) + 2
        create_table_sql = sql_content[create_table_start:create_table_end]
        cursor.execute(create_table_sql)
        
        # Compter les INSERT
        insert_count = sql_content.count("INSERT INTO proprietaires_parcelles")
        print(f"  - Nombre d'INSERT à exécuter: {insert_count:,}")
        
        # Exécuter les INSERT par lots
        print(f"\n📥 Import des données (par lots de 1000 INSERT)...")
        
        # Extraire tous les INSERT
        inserts_start = sql_content.find("INSERT INTO proprietaires_parcelles")
        inserts_section = sql_content[inserts_start:]
        
        # Diviser en commandes individuelles
        insert_statements = []
        current_pos = 0
        
        while True:
            insert_pos = inserts_section.find("INSERT INTO", current_pos)
            if insert_pos == -1:
                break
            
            next_insert = inserts_section.find("INSERT INTO", insert_pos + 1)
            if next_insert == -1:
                # Dernier INSERT
                insert_statements.append(inserts_section[insert_pos:].strip().rstrip(';'))
                break
            else:
                insert_statements.append(inserts_section[insert_pos:next_insert].strip().rstrip(';'))
                current_pos = next_insert
        
        # Exécuter par lots
        batch_size = 1000
        total = len(insert_statements)
        
        with tqdm(total=total, desc="Import", unit="INSERT") as pbar:
            for i in range(0, total, batch_size):
                batch = insert_statements[i:i+batch_size]
                
                for stmt in batch:
                    if stmt.strip():
                        cursor.execute(stmt)
                
                # Commit tous les 10 lots
                if (i // batch_size) % 10 == 0:
                    conn.commit()
                
                pbar.update(len(batch))
        
        # Commit final
        conn.commit()
        print("\n✅ Toutes les données importées")
        
        # Créer les index
        print(f"\n🔧 Création des index...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_proprietaires_parcelle ON proprietaires_parcelles(code_insee, section, numero);",
            "CREATE INDEX IF NOT EXISTS idx_proprietaires_siren ON proprietaires_parcelles(siren);",
            "CREATE INDEX IF NOT EXISTS idx_proprietaires_dept ON proprietaires_parcelles(departement);",
            "CREATE INDEX IF NOT EXISTS idx_proprietaires_denom ON proprietaires_parcelles(denomination);"
        ]
        
        for idx_sql in indexes:
            print(f"  - {idx_sql.split('idx_')[1].split(' ON')[0]}...")
            cursor.execute(idx_sql)
        
        conn.commit()
        print("✅ Index créés")
        
        # Vérification
        print(f"\n🔍 Vérification de l'import...")
        cursor.execute("SELECT COUNT(*) FROM proprietaires_parcelles;")
        count = cursor.fetchone()[0]
        print(f"✅ Nombre de lignes importées: {count:,}")
        
        cursor.execute("SELECT COUNT(DISTINCT departement) FROM proprietaires_parcelles;")
        dept_count = cursor.fetchone()[0]
        print(f"✅ Nombre de départements: {dept_count}")
        
        # Exemple de données
        print(f"\n📊 Exemple de données:")
        cursor.execute("""
            SELECT code_insee, section, numero, denomination, contenance 
            FROM proprietaires_parcelles 
            LIMIT 5;
        """)
        
        for row in cursor.fetchall():
            print(f"  - {row[0]} {row[1]} {row[2]}: {row[3]} ({row[4]} ha)")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("✅ IMPORT TERMINÉ AVEC SUCCÈS")
        print("=" * 80)
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ Erreur de connexion Railway: {e}")
        print("\n⚠️  Causes possibles:")
        print("  1. Abonnement Railway expiré (vérifiez le paiement)")
        print("  2. Connexion réseau bloquée")
        print("  3. Credentials PostgreSQL incorrects")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'import: {e}")
        import traceback
        traceback.print_exc()
        
        if conn:
            conn.rollback()

if __name__ == "__main__":
    import_sql_to_railway()
