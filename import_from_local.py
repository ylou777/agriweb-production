#!/usr/bin/env python3
"""
Import du fichier SQL.gz vers Railway PostgreSQL depuis votre PC local
"""

import gzip
import psycopg2
import os
from tqdm import tqdm

# Connexion Railway PostgreSQL (depuis les credentials Railway)
DATABASE_URL = "postgresql://postgres:WbjgkcXDKvbbYJhWprDDQQobbpnggYJc@viaduct.proxy.rlwy.net:21260/railway"

# Fichier SQL compressé
SQL_GZ_FILE = r"C:\Users\Utilisateur\Desktop\AG32.1\proprietaires_parcelles.sql.gz"

def import_sql_gz():
    """Import du fichier SQL.gz vers PostgreSQL"""
    
    print("🚀 Import des données MAJIC vers Railway PostgreSQL")
    print("=" * 80)
    print(f"📁 Fichier: {SQL_GZ_FILE}")
    
    # Vérifier que le fichier existe
    if not os.path.exists(SQL_GZ_FILE):
        print(f"❌ Fichier non trouvé: {SQL_GZ_FILE}")
        return
    
    file_size = os.path.getsize(SQL_GZ_FILE) / (1024 * 1024)
    print(f"📦 Taille: {file_size:.2f} MB")
    print()
    
    try:
        # Connexion à PostgreSQL
        print("🔌 Connexion à Railway PostgreSQL...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        print("✅ Connecté!")
        print()
        
        # Décompresser et lire le fichier
        print("📖 Lecture et décompression du fichier SQL...")
        with gzip.open(SQL_GZ_FILE, 'rt', encoding='utf-8') as f:
            sql_content = f.read()
        
        print(f"✅ Fichier décompressé: {len(sql_content)} caractères")
        print()
        
        # Compter les commandes SQL
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        total_statements = len(statements)
        print(f"📊 Nombre de commandes SQL: {total_statements}")
        print()
        
        # Exécuter les commandes SQL
        print("⚙️  Exécution des commandes SQL...")
        with tqdm(total=total_statements, unit="cmd") as pbar:
            for i, statement in enumerate(statements):
                if statement:
                    try:
                        cursor.execute(statement)
                        pbar.update(1)
                    except Exception as e:
                        # Afficher l'erreur mais continuer
                        if "already exists" not in str(e):
                            print(f"\n⚠️  Erreur à la commande {i+1}: {str(e)[:100]}")
        
        print()
        print("✅ Import terminé!")
        print()
        
        # Vérifier l'import
        print("🔍 Vérification...")
        cursor.execute("SELECT COUNT(*) FROM proprietaires_parcelles;")
        count = cursor.fetchone()[0]
        print(f"✅ Nombre de parcelles importées: {count:,}")
        
        cursor.execute("SELECT COUNT(DISTINCT departement) FROM proprietaires_parcelles;")
        dept_count = cursor.fetchone()[0]
        print(f"✅ Nombre de départements: {dept_count}")
        
        # Afficher un exemple
        cursor.execute("SELECT * FROM proprietaires_parcelles LIMIT 3;")
        rows = cursor.fetchall()
        print("\n📋 Exemple de données:")
        for row in rows:
            print(f"  - {row[2]} {row[4]}-{row[5]}: {row[7]} ({row[8]:.2f} ha)")
        
        cursor.close()
        conn.close()
        
        print()
        print("=" * 80)
        print("🎉 IMPORT RÉUSSI!")
        
    except psycopg2.OperationalError as e:
        print(f"❌ Erreur de connexion: {e}")
        print()
        print("⚠️  Causes possibles:")
        print("   1. Abonnement Railway expiré (voir le message en haut de l'interface)")
        print("   2. Connexion réseau bloquée")
        print("   3. Identifiants incorrects")
        print()
        print("💡 Solution: Payez l'abonnement Railway ou utilisez WeTransfer + Railway Shell")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import_sql_gz()
