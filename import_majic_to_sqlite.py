"""
Import des données MAJIC (propriétaires de parcelles) dans SQLite local
Puis upload sur Railway via script Python
"""

import pandas as pd
import sqlite3
from pathlib import Path
from tqdm import tqdm
import sys

class MajicToSQLite:
    def __init__(self, csv_folders, output_db="proprietaires_parcelles.db"):
        """
        Args:
            csv_folders: Liste de chemins vers les dossiers contenant les fichiers MAJIC CSV
            output_db: Chemin vers la base SQLite de sortie
        """
        if isinstance(csv_folders, (str, Path)):
            self.csv_folders = [Path(csv_folders)]
        else:
            self.csv_folders = [Path(folder) for folder in csv_folders]
        
        self.output_db = output_db
        self.conn = None
        
    def connect_db(self):
        """Connexion à SQLite"""
        self.conn = sqlite3.connect(self.output_db)
        print(f"✅ Base SQLite créée: {self.output_db}")
        
    def create_table(self):
        """Crée la table proprietaires_parcelles"""
        create_sql = """
        DROP TABLE IF EXISTS proprietaires_parcelles;
        
        CREATE TABLE proprietaires_parcelles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            departement TEXT NOT NULL,
            code_commune TEXT NOT NULL,
            code_insee TEXT NOT NULL,
            section TEXT NOT NULL,
            numero TEXT NOT NULL,
            siren TEXT,
            forme_juridique TEXT,
            denomination TEXT,
            contenance INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_proprietaires_commune_section_numero 
        ON proprietaires_parcelles(code_insee, section, numero);
        
        CREATE INDEX idx_proprietaires_siren 
        ON proprietaires_parcelles(siren);
        
        CREATE INDEX idx_proprietaires_departement 
        ON proprietaires_parcelles(departement);
        """
        
        self.conn.executescript(create_sql)
        self.conn.commit()
        print("✅ Table proprietaires_parcelles créée avec index")
    
    def parse_csv_file(self, csv_path):
        """Parse un fichier CSV MAJIC"""
        try:
            df = pd.read_csv(
                csv_path,
                sep=';',
                encoding='latin-1',
                dtype=str,
                na_values=['', 'NA', 'N/A']
            )
            
            # Nettoyer les colonnes
            df.columns = [col.strip().strip('"') for col in df.columns]
            
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].str.strip().str.strip('"')
            
            return df
            
        except Exception as e:
            print(f"❌ Erreur lecture {csv_path.name}: {e}")
            return None
    
    def insert_data(self, df, departement):
        """Insère les données dans SQLite"""
        if df is None or len(df) == 0:
            return 0
        
        column_mapping = {
            'Département (Champ géographique)': 'departement',
            'Code Commune (Champ géographique)': 'code_commune',
            'Section (Références cadastrales)': 'section',
            'N° plan (Références cadastrales)': 'numero',
            'N° SIREN (Propriétaire(s) parcelle)': 'siren',
            'Forme juridique (Propriétaire(s) parcelle)': 'forme_juridique',
            'Dénomination (Propriétaire(s) parcelle)': 'denomination',
            'Contenance (Caractéristiques parcelle)': 'contenance'
        }
        
        # Renommer uniquement les colonnes qui existent
        existing_mapping = {k: v for k, v in column_mapping.items() if k in df.columns}
        df_clean = df.rename(columns=existing_mapping)
        
        # Vérifier les colonnes requises
        required = ['departement', 'code_commune', 'section', 'numero']
        missing = [col for col in required if col not in df_clean.columns]
        if missing:
            return 0
        
        # Remplir les valeurs NULL et filtrer les lignes invalides
        df_clean['departement'] = df_clean['departement'].fillna('').astype(str)
        df_clean['code_commune'] = df_clean['code_commune'].fillna('').astype(str)
        df_clean['section'] = df_clean['section'].fillna('').astype(str)
        df_clean['numero'] = df_clean['numero'].fillna('').astype(str)
        
        # Filtrer les lignes avec section ou numero vides
        df_clean = df_clean[(df_clean['section'] != '') & (df_clean['numero'] != '')]
        
        if len(df_clean) == 0:
            return 0
        
        # Créer code_insee
        df_clean['code_insee'] = df_clean['departement'].astype(str).str.zfill(2) + df_clean['code_commune'].astype(str).str.zfill(3)
        
        # Gérer contenance (peut ne pas exister)
        if 'contenance' in df_clean.columns:
            df_clean['contenance'] = pd.to_numeric(df_clean['contenance'], errors='coerce').fillna(0).astype(int)
        else:
            df_clean['contenance'] = 0
        
        # S'assurer que toutes les colonnes existent
        for col in ['siren', 'forme_juridique', 'denomination']:
            if col not in df_clean.columns:
                df_clean[col] = None
        
        # Insertion dans SQLite
        df_clean[[
            'departement', 'code_commune', 'code_insee', 'section', 'numero',
            'siren', 'forme_juridique', 'denomination', 'contenance'
        ]].to_sql('proprietaires_parcelles', self.conn, if_exists='append', index=False)
        
        return len(df_clean)
    
    def import_all(self, departments=None):
        """Importe tous les fichiers MAJIC dans SQLite"""
        print("=" * 80)
        print("🚀 IMPORT MAJIC CSV → SQLITE")
        print("=" * 80)
        print()
        
        self.connect_db()
        self.create_table()
        
        # Collecter fichiers
        print("📁 Scan des dossiers...")
        all_files = []
        for folder in self.csv_folders:
            if not folder.exists():
                print(f"⚠️  Dossier introuvable: {folder}")
                continue
            
            files = list(folder.glob("PM_*.txt"))
            all_files.extend(files)
            print(f"📁 {folder.name}: {len(files)} fichiers")
        
        print()
        
        # Filtrer par départements
        if departments:
            departments = [d.zfill(3) if len(d) <= 2 else d for d in departments]
            filtered_files = []
            for f in all_files:
                parts = f.stem.split('_')
                if len(parts) >= 3:
                    dept_code = parts[-1]
                    if dept_code in departments or dept_code.lstrip('0') in [d.lstrip('0') for d in departments]:
                        filtered_files.append(f)
            all_files = filtered_files
            print(f"📋 Filtré: {len(all_files)} fichiers")
        else:
            print(f"📋 TOTAL: {len(all_files)} fichiers")
        
        print()
        
        # Traiter chaque fichier
        total_records = 0
        for csv_file in tqdm(all_files, desc="Import"):
            parts = csv_file.stem.split('_')
            dept_code = parts[-1] if len(parts) >= 3 else "XX"
            
            df = self.parse_csv_file(csv_file)
            if df is not None:
                count = self.insert_data(df, dept_code)
                total_records += count
                tqdm.write(f"✅ {dept_code}: {count:,} parcelles")
        
        print()
        print("=" * 80)
        print(f"✅ IMPORT TERMINÉ")
        print(f"📊 Total: {total_records:,} parcelles")
        print(f"📁 Fichier: {self.output_db}")
        print("=" * 80)
        
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Importer fichiers MAJIC dans SQLite local")
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
        "--output",
        default="proprietaires_parcelles.db",
        help="Fichier SQLite de sortie"
    )
    parser.add_argument(
        "--departments",
        nargs="+",
        help="Liste des départements (ex: 06 13 83 84). Si omis, traite tout"
    )
    
    args = parser.parse_args()
    
    importer = MajicToSQLite(
        csv_folders=args.input_folders,
        output_db=args.output
    )
    
    try:
        importer.import_all(departments=args.departments)
        
        print()
        print("📤 PROCHAINE ÉTAPE:")
        print("   Uploadez ce fichier sur Railway et importez dans PostgreSQL")
        print(f"   Fichier: {args.output}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Import interrompu")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
