"""
Import des données MAJIC (propriétaires de parcelles) dans PostgreSQL Railway
Sans géométries - juste les données brutes pour requêtes par code_commune + section + numero
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from pathlib import Path
from tqdm import tqdm
import sys

class MajicToPostgres:
    def __init__(self, csv_folders, db_config):
        """
        Args:
            csv_folders: Liste de chemins vers les dossiers contenant les fichiers MAJIC CSV
            db_config: Dict avec les paramètres de connexion PostgreSQL
        """
        if isinstance(csv_folders, (str, Path)):
            self.csv_folders = [Path(csv_folders)]
        else:
            self.csv_folders = [Path(folder) for folder in csv_folders]
        
        self.db_config = db_config
        self.conn = None
        
    def connect_db(self):
        """Connexion à PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**self.db_config, connect_timeout=10)
            print(f"✅ Connecté à PostgreSQL: {self.db_config['host']}")
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            raise
        
    def create_table(self):
        """Crée la table proprietaires_parcelles si elle n'existe pas"""
        create_sql = """
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
        
        -- Index pour recherche rapide par commune + section + numero
        CREATE INDEX idx_proprietaires_commune_section_numero 
        ON proprietaires_parcelles(code_insee, section, numero);
        
        -- Index pour recherche par SIREN
        CREATE INDEX idx_proprietaires_siren 
        ON proprietaires_parcelles(siren);
        
        -- Index pour recherche par département
        CREATE INDEX idx_proprietaires_departement 
        ON proprietaires_parcelles(departement);
        """
        
        with self.conn.cursor() as cur:
            cur.execute(create_sql)
            self.conn.commit()
        
        print("✅ Table proprietaires_parcelles créée avec index")
    
    def parse_csv_file(self, csv_path):
        """
        Parse un fichier CSV MAJIC
        Format: Département;Code Commune;Section;N° plan;N° SIREN;Forme juridique;Dénomination;Contenance
        """
        try:
            df = pd.read_csv(
                csv_path,
                sep=';',
                encoding='latin-1',
                dtype=str,
                na_values=['', 'NA', 'N/A']
            )
            
            # Nettoyer les noms de colonnes (enlever guillemets)
            df.columns = [col.strip().strip('"') for col in df.columns]
            
            # Nettoyer les valeurs (enlever guillemets)
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].str.strip().str.strip('"')
            
            return df
            
        except Exception as e:
            print(f"❌ Erreur lecture {csv_path.name}: {e}")
            return None
    
    def insert_data(self, df, departement):
        """Insère les données d'un département dans PostgreSQL"""
        if df is None or len(df) == 0:
            return 0
        
        # Mapper les colonnes
        column_mapping = {
            'Département': 'departement',
            'Code Commune': 'code_commune',
            'Section': 'section',
            'N° plan': 'numero',
            'N° SIREN': 'siren',
            'Forme juridique': 'forme_juridique',
            'Dénomination': 'denomination',
            'Contenance': 'contenance'
        }
        
        # Renommer les colonnes
        df_clean = df.rename(columns=column_mapping)
        
        # Créer code_insee (département + code_commune)
        df_clean['code_insee'] = df_clean['departement'].astype(str) + df_clean['code_commune'].astype(str).str.zfill(3)
        
        # Nettoyer la contenance (convertir en entier)
        df_clean['contenance'] = pd.to_numeric(df_clean['contenance'], errors='coerce').fillna(0).astype(int)
        
        # Préparer les données pour insertion
        records = df_clean[[
            'departement', 'code_commune', 'code_insee', 'section', 'numero',
            'siren', 'forme_juridique', 'denomination', 'contenance'
        ]].values.tolist()
        
        # Insertion par batch
        insert_sql = """
        INSERT INTO proprietaires_parcelles 
        (departement, code_commune, code_insee, section, numero, siren, forme_juridique, denomination, contenance)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        with self.conn.cursor() as cur:
            execute_batch(cur, insert_sql, records, page_size=1000)
            self.conn.commit()
        
        return len(records)
    
    def import_all(self, departments=None):
        """
        Importe tous les fichiers MAJIC dans PostgreSQL
        
        Args:
            departments: Liste des départements à traiter (ex: ['06', '13']). Si None, traite tout.
        """
        print("=" * 80)
        print("🚀 IMPORT MAJIC CSV → POSTGRESQL")
        print("=" * 80)
        print()
        
        # Connexion et création table
        print("🔌 Connexion à PostgreSQL...")
        self.connect_db()
        print("📋 Création de la table...")
        self.create_table()
        print("✅ Table créée")
        
        # Collecter tous les fichiers CSV
        print("📁 Scan des dossiers...")
        all_files = []
        for folder in self.csv_folders:
            print(f"   Vérification: {folder}")
            if not folder.exists():
                print(f"⚠️  Dossier introuvable: {folder}")
                continue
            
            files = list(folder.glob("PM_*.txt"))
            all_files.extend(files)
            print(f"📁 Dossier: {folder.name}")
            print(f"   {len(files)} fichiers trouvés")
        
        print()
        
        # Filtrer par départements si spécifié
        if departments:
            departments = [d.zfill(3) if len(d) <= 2 else d for d in departments]
            filtered_files = []
            for f in all_files:
                # Extraire le code département du nom de fichier (ex: PM_19_NB_010.txt -> 010)
                parts = f.stem.split('_')
                if len(parts) >= 3:
                    dept_code = parts[-1]
                    if dept_code in departments or dept_code.lstrip('0') in [d.lstrip('0') for d in departments]:
                        filtered_files.append(f)
            
            all_files = filtered_files
            print(f"📋 Filtré: {len(all_files)} fichiers pour départements {departments}")
        else:
            print(f"📋 TOTAL: {len(all_files)} fichiers à traiter")
        
        print()
        
        # Traiter chaque fichier
        total_records = 0
        for csv_file in tqdm(all_files, desc="Départements"):
            # Extraire le code département
            parts = csv_file.stem.split('_')
            dept_code = parts[-1] if len(parts) >= 3 else "XX"
            
            # Parser le CSV
            df = self.parse_csv_file(csv_file)
            
            if df is not None:
                # Insérer dans PostgreSQL
                count = self.insert_data(df, dept_code)
                total_records += count
                tqdm.write(f"✅ {dept_code}: {count:,} parcelles importées")
        
        print()
        print("=" * 80)
        print(f"✅ IMPORT TERMINÉ")
        print(f"📊 Total: {total_records:,} parcelles importées")
        print("=" * 80)
        
        # Fermer connexion
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Importer fichiers MAJIC dans PostgreSQL")
    parser.add_argument(
        "--input-folders",
        nargs="+",
        default=[
            r"C:\Users\Public\Documents\personnes morales\PARCELLES  départements 1 A 61",
            r"C:\Users\Public\Documents\personnes morales\PARCELLES départements 62 A 976"
        ],
        help="Dossiers contenant les fichiers CSV MAJIC"
    )
    parser.add_argument(
        "--departments",
        nargs="+",
        help="Liste des départements à traiter (ex: 06 13 83 84). Si omis, traite tout"
    )
    parser.add_argument(
        "--db-host",
        default="viaduct.proxy.rlwy.net",
        help="Host PostgreSQL"
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
        help="Nom de la base de données"
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
    
    # Configuration DB
    db_config = {
        'host': args.db_host,
        'port': args.db_port,
        'database': args.db_name,
        'user': args.db_user,
        'password': args.db_password
    }
    
    # Créer l'importeur
    importer = MajicToPostgres(
        csv_folders=args.input_folders,
        db_config=db_config
    )
    
    # Lancer l'import
    try:
        importer.import_all(departments=args.departments)
    except KeyboardInterrupt:
        print("\n⚠️  Import interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
