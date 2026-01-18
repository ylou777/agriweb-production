"""
Script de migration CRM : SQLite → PostgreSQL Railway
Migre la table agriweb_prospects et tables associées
"""
import psycopg2
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration PostgreSQL Railway
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL non trouvée dans les variables d'environnement")
    exit(1)

print(f"📊 Migration CRM SQLite → PostgreSQL Railway")
print(f"=" * 80)

# Connexion PostgreSQL
try:
    pg_conn = psycopg2.connect(DATABASE_URL)
    pg_cursor = pg_conn.cursor()
    print("✅ Connexion PostgreSQL établie")
except Exception as e:
    print(f"❌ Erreur connexion PostgreSQL: {e}")
    exit(1)

# Créer les tables PostgreSQL pour le CRM
print("\n📝 Création des tables PostgreSQL...")

# Table principale prospects
pg_cursor.execute('''
    CREATE TABLE IF NOT EXISTS agriweb_prospects (
        id SERIAL PRIMARY KEY,
        type TEXT NOT NULL,
        commune TEXT NOT NULL,
        departement TEXT,
        adresse TEXT,
        latitude REAL,
        longitude REAL,
        surface_m2 REAL,
        surface_ha REAL,
        parcelles_cadastrales TEXT,
        poste_bt_distance_m REAL,
        poste_hta_distance_m REAL,
        lien_streetview TEXT,
        lien_annuaire TEXT,
        statut TEXT DEFAULT 'nouveau',
        priorite TEXT DEFAULT 'moyenne',
        notes TEXT,
        nom_prospect TEXT,
        contact_nom TEXT,
        contact_email TEXT,
        contact_telephone TEXT,
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        data_json TEXT
    )
''')

# Index
pg_cursor.execute('CREATE INDEX IF NOT EXISTS idx_agriweb_commune ON agriweb_prospects(commune)')
pg_cursor.execute('CREATE INDEX IF NOT EXISTS idx_agriweb_type ON agriweb_prospects(type)')
pg_cursor.execute('CREATE INDEX IF NOT EXISTS idx_agriweb_statut ON agriweb_prospects(statut)')
pg_cursor.execute('CREATE INDEX IF NOT EXISTS idx_agriweb_departement ON agriweb_prospects(departement)')

# Table actions
pg_cursor.execute('''
    CREATE TABLE IF NOT EXISTS prospect_actions (
        id SERIAL PRIMARY KEY,
        prospect_id INTEGER NOT NULL,
        type_action TEXT NOT NULL,
        description TEXT,
        date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (prospect_id) REFERENCES agriweb_prospects(id) ON DELETE CASCADE
    )
''')

# Table rendez-vous
pg_cursor.execute('''
    CREATE TABLE IF NOT EXISTS prospect_appointments (
        id SERIAL PRIMARY KEY,
        prospect_id INTEGER NOT NULL,
        date_rdv TEXT NOT NULL,
        type_rdv TEXT NOT NULL,
        notes TEXT,
        statut TEXT DEFAULT 'prevu',
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (prospect_id) REFERENCES agriweb_prospects(id) ON DELETE CASCADE
    )
''')

# Table propositions
pg_cursor.execute('''
    CREATE TABLE IF NOT EXISTS prospect_proposals (
        id SERIAL PRIMARY KEY,
        prospect_id INTEGER NOT NULL,
        puissance_kwc REAL,
        prix_kwc REAL,
        production_kwh_kwc REAL,
        tarif_rachat REAL,
        investissement_total REAL,
        production_annuelle REAL,
        revenus_annuels REAL,
        rentabilite_pct REAL,
        roi_annees REAL,
        notes TEXT,
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (prospect_id) REFERENCES agriweb_prospects(id) ON DELETE CASCADE
    )
''')

pg_conn.commit()
print("✅ Tables PostgreSQL créées")

# Vérifier si SQLite existe
sqlite_paths = [
    os.path.join(os.path.dirname(__file__), '..', 'KPI', 'kpi_sunstice.db'),
    os.path.join(os.path.dirname(__file__), '..', 'KPI', 'kpi.db'),
    'kpi.db',
    'kpi_sunstice.db'
]

sqlite_db = None
for path in sqlite_paths:
    if os.path.exists(path):
        sqlite_db = path
        break

if sqlite_db:
    print(f"\n📦 SQLite trouvée: {sqlite_db}")
    
    try:
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Vérifier si la table existe
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agriweb_prospects'")
        if sqlite_cursor.fetchone():
            # Migrer les données
            sqlite_cursor.execute("SELECT COUNT(*) FROM agriweb_prospects")
            count = sqlite_cursor.fetchone()[0]
            print(f"📊 {count} prospects trouvés dans SQLite")
            
            if count > 0:
                sqlite_cursor.execute("SELECT * FROM agriweb_prospects")
                rows = sqlite_cursor.fetchall()
                columns = [desc[0] for desc in sqlite_cursor.description]
                
                # Insérer dans PostgreSQL (en ignorant l'ID auto-généré)
                insert_cols = [c for c in columns if c != 'id']
                placeholders = ', '.join(['%s'] * len(insert_cols))
                insert_query = f"INSERT INTO agriweb_prospects ({', '.join(insert_cols)}) VALUES ({placeholders})"
                
                migrated = 0
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    values = [row_dict[c] for c in insert_cols]
                    
                    try:
                        pg_cursor.execute(insert_query, values)
                        migrated += 1
                    except Exception as e:
                        print(f"⚠️ Erreur migration prospect: {e}")
                
                pg_conn.commit()
                print(f"✅ {migrated} prospects migrés vers PostgreSQL")
        else:
            print("ℹ️ Pas de table agriweb_prospects dans SQLite")
        
        sqlite_conn.close()
    except Exception as e:
        print(f"⚠️ Erreur lecture SQLite: {e}")
else:
    print("\nℹ️ Aucune base SQLite trouvée - tables vides créées dans PostgreSQL")

# Compter les prospects dans PostgreSQL
pg_cursor.execute("SELECT COUNT(*) FROM agriweb_prospects")
total = pg_cursor.fetchone()[0]

print(f"\n{'=' * 80}")
print(f"✅ Migration terminée")
print(f"📊 Total prospects dans PostgreSQL: {total}")
print(f"🎯 Le CRM utilise maintenant PostgreSQL Railway")
print(f"{'=' * 80}")

pg_conn.close()
