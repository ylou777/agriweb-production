"""
Adaptateur de base de données pour Railway
Gère la connexion PostgreSQL ou SQLite selon l'environnement
"""
import os
import sqlite3
from contextlib import contextmanager

# Détecter l'environnement
DATABASE_URL = os.environ.get('DATABASE_URL')
IS_RAILWAY = DATABASE_URL is not None

if IS_RAILWAY:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    # Railway fournit l'URL au format postgres://, PostgreSQL nécessite postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    print(f"🐘 [DATABASE] Mode PostgreSQL détecté (Railway)")
else:
    print(f"💾 [DATABASE] Mode SQLite détecté (Local)")

@contextmanager
def get_db_connection():
    """Retourne une connexion à la base de données appropriée"""
    if IS_RAILWAY:
        # Connexion PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        try:
            yield conn
        finally:
            conn.close()
    else:
        # Connexion SQLite
        db_path = os.getenv('KPI_DATABASE_PATH', 
                           os.path.join(os.path.dirname(__file__), '..', 'KPI', 'kpi_sunstice.db'))
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Exécute une requête et retourne les résultats"""
    with get_db_connection() as conn:
        if IS_RAILWAY:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
        else:
            cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # IMPORTANT: Commit AVANT le fetch pour INSERT...RETURNING
        if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
            conn.commit()
        
        if fetch_one:
            result = cursor.fetchone()
            cursor.close()
            return dict(result) if result else None
        elif fetch_all:
            results = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in results]
        else:
            cursor.close()
            return None

def migrate_existing_table():
    """Ajoute les colonnes manquantes à une table existante"""
    if not IS_RAILWAY:
        return
    
    print("🔧 [MIGRATION] Vérification des colonnes manquantes...")
    
    # Les tables project_* ont déjà été DROP et recréées dans init_database()
    # On vérifie juste les colonnes de agriweb_prospects
    
    columns_to_add = [
        ('poste_bt_nom', 'TEXT'),
        ('poste_bt_puissance', 'REAL'),
        ('poste_bt_lat', 'REAL'),
        ('poste_bt_lon', 'REAL'),
        ('poste_hta_nom', 'TEXT'),
        ('poste_hta_puissance', 'REAL'),
        ('poste_hta_lat', 'REAL'),
        ('poste_hta_lon', 'REAL'),
        ('nom_prospect', 'TEXT'),
        ('representant_nom', 'TEXT'),
        ('representant_tel', 'TEXT'),
        ('representant_email', 'TEXT'),
        ('siren', 'TEXT'),
        ('dirigeant_nom', 'TEXT'),
        ('dirigeant_email', 'TEXT'),
        ('dirigeant_tel', 'TEXT'),
        ('siret', 'TEXT')
    ]
    
    # Chaque colonne a sa propre transaction pour éviter les blocages
    for col_name, col_type in columns_to_add:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(f"ALTER TABLE agriweb_prospects ADD COLUMN {col_name} {col_type}")
                conn.commit()
                print(f"✅ Colonne {col_name} ajoutée")
            except Exception as e:
                conn.rollback()
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg:
                    pass  # Colonne existe déjà, c'est normal
                else:
                    print(f"⚠️ Migration {col_name}: {e}")
            finally:
                cursor.close()
    
    # Migration pour project_etapes - ajouter date_debut_prevue
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE project_etapes ADD COLUMN date_debut_prevue TIMESTAMP")
            conn.commit()
            print(f"✅ Colonne date_debut_prevue ajoutée à project_etapes")
        except Exception as e:
            conn.rollback()
            error_msg = str(e).lower()
            if 'already exists' in error_msg or 'duplicate' in error_msg:
                pass  # Colonne existe déjà
            else:
                print(f"⚠️ Migration date_debut_prevue: {e}")
        finally:
            cursor.close()
    
    print("✅ [MIGRATION] Vérification terminée")

def init_database():
    """Initialise les tables CRM dans PostgreSQL ou SQLite"""
    print("📊 [DATABASE] Initialisation des tables CRM...")
    
    if IS_RAILWAY:
        # FIX: DROP et recréer project_fiches AVANT tout pour éviter "database is locked"
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                print("🔄 [INIT] DROP des tables project_* pour recréation...")
                cursor.execute("DROP TABLE IF EXISTS project_documents CASCADE")
                cursor.execute("DROP TABLE IF EXISTS project_etapes CASCADE")
                cursor.execute("DROP TABLE IF EXISTS project_fiches CASCADE")
                conn.commit()
                print("✅ [INIT] Tables project_* supprimées")
        except Exception as e:
            print(f"⚠️ [INIT] Erreur DROP tables: {e}")
        
        # Schéma PostgreSQL
        schema = """
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
            poste_bt_nom TEXT,
            poste_bt_puissance REAL,
            poste_bt_lat REAL,
            poste_bt_lon REAL,
            poste_hta_distance_m REAL,
            poste_hta_nom TEXT,
            poste_hta_puissance REAL,
            poste_hta_lat REAL,
            poste_hta_lon REAL,
            lien_streetview TEXT,
            lien_annuaire TEXT,
            statut TEXT DEFAULT 'nouveau',
            priorite TEXT DEFAULT 'moyenne',
            notes TEXT,
            contact_nom TEXT,
            contact_email TEXT,
            contact_telephone TEXT,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_json TEXT,
            nom_prospect TEXT,
            representant_nom TEXT,
            representant_tel TEXT,
            representant_email TEXT,
            siren TEXT,
            dirigeant_nom TEXT,
            dirigeant_email TEXT,
            dirigeant_tel TEXT,
            siret TEXT,
            osm_amenity TEXT,
            osm_shop TEXT,
            osm_building TEXT,
            osm_landuse TEXT,
            osm_office TEXT,
            osm_industrial TEXT
        );

        CREATE TABLE IF NOT EXISTS prospect_proposals (
            id SERIAL PRIMARY KEY,
            prospect_id INTEGER NOT NULL REFERENCES agriweb_prospects(id) ON DELETE CASCADE,
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
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS project_fiches (
            id SERIAL PRIMARY KEY,
            prospect_id INTEGER,
            nom_projet TEXT,
            client_nom TEXT,
            client_email TEXT,
            client_telephone TEXT,
            adresse_projet TEXT,
            parcelles_cadastrales TEXT,
            commune TEXT,
            departement TEXT,
            surface_totale REAL,
            puissance_estimee REAL,
            statut_projet TEXT DEFAULT 'etude',
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            data_json TEXT,
            type_projet TEXT,
            client_adresse TEXT,
            statut_global TEXT,
            date_fin_prevue TIMESTAMP,
            date_fin_reelle TIMESTAMP,
            responsable TEXT
        );

        CREATE TABLE IF NOT EXISTS project_etapes (
            id SERIAL PRIMARY KEY,
            project_id INTEGER REFERENCES project_fiches(id) ON DELETE CASCADE,
            nom_etape TEXT NOT NULL,
            statut TEXT DEFAULT 'en_attente',
            date_debut TIMESTAMP,
            date_debut_prevue TIMESTAMP,
            date_fin_prevue TIMESTAMP,
            date_fin_reelle TIMESTAMP,
            responsable TEXT,
            notes TEXT,
            ordre INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS project_documents (
            id SERIAL PRIMARY KEY,
            project_id INTEGER REFERENCES project_fiches(id) ON DELETE CASCADE,
            nom_document TEXT NOT NULL,
            type_document TEXT,
            chemin_fichier TEXT,
            date_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            taille_octets INTEGER,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS crm_appointments (
            id SERIAL PRIMARY KEY,
            prospect_id INTEGER REFERENCES agriweb_prospects(id),
            title TEXT NOT NULL,
            description TEXT,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            location TEXT,
            type TEXT DEFAULT 'visite',
            status TEXT DEFAULT 'planifie',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    else:
        # Schéma SQLite
        schema = """
        CREATE TABLE IF NOT EXISTS agriweb_prospects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            contact_nom TEXT,
            contact_email TEXT,
            contact_telephone TEXT,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_json TEXT,
            poste_bt_nom TEXT,
            poste_bt_puissance REAL,
            poste_hta_nom TEXT,
            nom_prospect TEXT,
            representant_nom TEXT,
            representant_tel TEXT,
            representant_email TEXT,
            siren TEXT,
            dirigeant_nom TEXT,
            dirigeant_email TEXT,
            dirigeant_tel TEXT,
            siret TEXT,
            osm_amenity TEXT,
            osm_shop TEXT,
            osm_building TEXT,
            osm_landuse TEXT,
            osm_office TEXT,
            osm_industrial TEXT
        );

        CREATE TABLE IF NOT EXISTS prospect_proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        );

        CREATE TABLE IF NOT EXISTS project_fiches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER REFERENCES agriweb_prospects(id),
            nom_projet TEXT,
            client_nom TEXT,
            client_email TEXT,
            client_telephone TEXT,
            adresse_projet TEXT,
            commune TEXT,
            departement TEXT,
            surface_totale REAL,
            puissance_estimee REAL,
            statut_projet TEXT DEFAULT 'etude',
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            data_json TEXT
        );

        CREATE TABLE IF NOT EXISTS project_etapes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER REFERENCES project_fiches(id) ON DELETE CASCADE,
            nom_etape TEXT NOT NULL,
            statut TEXT DEFAULT 'en_attente',
            date_debut TIMESTAMP,
            date_debut_prevue TIMESTAMP,
            date_fin_prevue TIMESTAMP,
            date_fin_reelle TIMESTAMP,
            responsable TEXT,
            notes TEXT,
            ordre INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS project_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER REFERENCES project_fiches(id),
            nom_document TEXT NOT NULL,
            type_document TEXT,
            chemin_fichier TEXT,
            date_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            taille_octets INTEGER,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS crm_appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER REFERENCES agriweb_prospects(id),
            title TEXT NOT NULL,
            description TEXT,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            location TEXT,
            type TEXT DEFAULT 'visite',
            status TEXT DEFAULT 'planifie',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    
    # Exécuter le schéma
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for statement in schema.split(';'):
            if statement.strip():
                cursor.execute(statement)
        conn.commit()
        cursor.close()
    
    # Migration des colonnes pour tables existantes
    migrate_existing_table()
    
    print("✅ [DATABASE] Tables CRM initialisées avec succès!")

if __name__ == "__main__":
    init_database()
