"""
Export SQLite → SQL dump compressé pour upload Railway
Plus léger que le fichier .db complet
"""

import sqlite3
import gzip
import os

def export_to_sql_gz(sqlite_db, output_file="proprietaires_parcelles.sql.gz"):
    """Exporte SQLite en SQL compressé"""
    
    print("=" * 80)
    print("📦 EXPORT SQLITE → SQL.GZ")
    print("=" * 80)
    print()
    
    print(f"📂 Lecture: {sqlite_db}")
    conn = sqlite3.connect(sqlite_db)
    
    print(f"📝 Export SQL en cours...")
    
    with gzip.open(output_file, 'wt', encoding='utf-8') as f:
        # Header
        f.write("-- MAJIC Propriétaires Parcelles\n")
        f.write("-- 18,740,957 parcelles\n\n")
        
        # CREATE TABLE
        f.write("DROP TABLE IF EXISTS proprietaires_parcelles CASCADE;\n\n")
        f.write("""CREATE TABLE proprietaires_parcelles (
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
);\n\n""")
        
        # INSERT par batch
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM proprietaires_parcelles")
        total = cur.fetchone()[0]
        
        print(f"📊 {total:,} lignes à exporter")
        
        batch_size = 10000
        offset = 0
        
        from tqdm import tqdm
        with tqdm(total=total, desc="Export", unit=" lignes") as pbar:
            while True:
                cur.execute(f"""
                    SELECT departement, code_commune, code_insee, section, numero,
                           siren, forme_juridique, denomination, contenance
                    FROM proprietaires_parcelles
                    LIMIT {batch_size} OFFSET {offset}
                """)
                
                rows = cur.fetchall()
                if not rows:
                    break
                
                # Générer INSERT
                f.write("INSERT INTO proprietaires_parcelles ")
                f.write("(departement, code_commune, code_insee, section, numero, siren, forme_juridique, denomination, contenance) VALUES\n")
                
                for i, row in enumerate(rows):
                    # Escape les valeurs
                    values = []
                    for val in row:
                        if val is None:
                            values.append("NULL")
                        elif isinstance(val, str):
                            # Escape single quotes
                            escaped = val.replace("'", "''")
                            values.append(f"'{escaped}'")
                        else:
                            values.append(str(val))
                    
                    f.write(f"  ({', '.join(values)})")
                    f.write(",\n" if i < len(rows) - 1 else ";\n\n")
                
                pbar.update(len(rows))
                offset += batch_size
        
        # Index
        f.write("\n-- Index\n")
        f.write("CREATE INDEX idx_proprietaires_commune_section_numero ON proprietaires_parcelles(code_insee, section, numero);\n")
        f.write("CREATE INDEX idx_proprietaires_siren ON proprietaires_parcelles(siren) WHERE siren IS NOT NULL;\n")
        f.write("CREATE INDEX idx_proprietaires_departement ON proprietaires_parcelles(departement);\n")
    
    conn.close()
    
    file_size = os.path.getsize(output_file) / (1024**2)  # MB
    
    print()
    print("=" * 80)
    print(f"✅ EXPORT TERMINÉ")
    print(f"📁 Fichier: {output_file}")
    print(f"📦 Taille: {file_size:.2f} MB (compressé)")
    print("=" * 80)
    print()
    print("📤 PROCHAINE ÉTAPE:")
    print("   1. Uploadez ce fichier sur Railway")
    print("   2. Depuis Railway Shell:")
    print("      gunzip proprietaires_parcelles.sql.gz")
    print("      psql $DATABASE_URL < proprietaires_parcelles.sql")

if __name__ == "__main__":
    export_to_sql_gz("C:/Users/Utilisateur/Desktop/AG32.1/proprietaires_parcelles.db")
