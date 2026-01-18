"""
Script de diagnostic et réparation du CRM PostgreSQL
Vérifie et répare la base de données CRM sur Railway
"""
import os
import sys

# Vérifier si on est sur Railway
DATABASE_URL = os.environ.get('DATABASE_URL')
IS_RAILWAY = DATABASE_URL is not None

if IS_RAILWAY:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    # Correction de l'URL si nécessaire
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    print(f"🐘 Mode PostgreSQL détecté (Railway)")
    print(f"📊 URL Database: {DATABASE_URL[:30]}...")
else:
    print(f"❌ DATABASE_URL non trouvée - Ce script doit être exécuté sur Railway")
    print(f"ℹ️  Pour tester localement, définissez DATABASE_URL")
    sys.exit(1)

def check_crm_tables():
    """Vérifie l'existence des tables CRM"""
    print("\n" + "="*70)
    print("🔍 DIAGNOSTIC DES TABLES CRM POSTGRESQL")
    print("="*70)
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Lister toutes les tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    
    print(f"\n📋 Tables existantes dans PostgreSQL ({len(tables)} tables):")
    crm_tables_found = []
    for table in tables:
        table_name = table['table_name']
        print(f"   • {table_name}")
        if 'prospect' in table_name.lower() or 'project' in table_name.lower():
            crm_tables_found.append(table_name)
    
    # Vérifier spécifiquement les tables CRM requises
    required_tables = [
        'agriweb_prospects',
        'prospect_actions',
        'prospect_appointments',
        'prospect_proposals',
        'project_fiches',
        'project_etapes',
        'project_documents'
    ]
    
    print(f"\n🎯 Tables CRM requises:")
    missing_tables = []
    for table_name in required_tables:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            )
        """, (table_name,))
        exists = cursor.fetchone()['exists']
        
        if exists:
            # Compter les enregistrements
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            count = cursor.fetchone()['count']
            print(f"   ✅ {table_name}: {count} enregistrements")
        else:
            print(f"   ❌ {table_name}: MANQUANTE")
            missing_tables.append(table_name)
    
    cursor.close()
    conn.close()
    
    return missing_tables

def create_crm_tables():
    """Crée les tables CRM manquantes"""
    print("\n" + "="*70)
    print("🔧 CRÉATION DES TABLES CRM")
    print("="*70)
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Table principale des prospects
    print("\n📊 Création de agriweb_prospects...")
    cursor.execute('''
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
            
            -- Poste BT
            poste_bt_distance_m REAL,
            poste_bt_nom TEXT,
            poste_bt_puissance REAL,
            poste_bt_etat TEXT,
            poste_bt_lat REAL,
            poste_bt_lon REAL,
            poste_bt_commune TEXT,
            poste_bt_code_commune TEXT,
            poste_bt_epci TEXT,
            poste_bt_code_epci TEXT,
            poste_bt_departement TEXT,
            poste_bt_code_departement TEXT,
            poste_bt_region TEXT,
            poste_bt_code_region TEXT,
            
            -- Poste HTA
            poste_hta_distance_m REAL,
            poste_hta_nom TEXT,
            poste_hta_puissance REAL,
            poste_hta_etat TEXT,
            poste_hta_lat REAL,
            poste_hta_lon REAL,
            poste_hta_commune TEXT,
            poste_hta_code_commune TEXT,
            poste_hta_epci TEXT,
            poste_hta_code_epci TEXT,
            poste_hta_departement TEXT,
            poste_hta_code_departement TEXT,
            poste_hta_region TEXT,
            poste_hta_code_region TEXT,
            
            -- Liens et infos
            lien_streetview TEXT,
            lien_annuaire TEXT,
            
            -- Données OSM
            osm_amenity TEXT,
            osm_shop TEXT,
            osm_building TEXT,
            osm_landuse TEXT,
            osm_office TEXT,
            osm_industrial TEXT,
            
            -- Contact et gestion
            statut TEXT DEFAULT 'nouveau',
            priorite TEXT DEFAULT 'moyenne',
            notes TEXT,
            nom_prospect TEXT,
            contact_nom TEXT,
            contact_email TEXT,
            contact_telephone TEXT,
            
            -- Données SIRENE
            representant_nom TEXT,
            representant_tel TEXT,
            representant_email TEXT,
            siren TEXT,
            dirigeant_nom TEXT,
            dirigeant_email TEXT,
            dirigeant_tel TEXT,
            siret TEXT,
            
            -- Dates
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Données complètes en JSON
            data_json TEXT
        )
    ''')
    conn.commit()
    print("   ✅ agriweb_prospects créée")
    
    # Index pour recherches rapides
    print("\n🔍 Création des index...")
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_agriweb_commune ON agriweb_prospects(commune)",
        "CREATE INDEX IF NOT EXISTS idx_agriweb_type ON agriweb_prospects(type)",
        "CREATE INDEX IF NOT EXISTS idx_agriweb_statut ON agriweb_prospects(statut)",
        "CREATE INDEX IF NOT EXISTS idx_agriweb_departement ON agriweb_prospects(departement)"
    ]
    for idx_sql in indexes:
        cursor.execute(idx_sql)
    conn.commit()
    print("   ✅ Index créés")
    
    # Table des actions
    print("\n📋 Création de prospect_actions...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prospect_actions (
            id SERIAL PRIMARY KEY,
            prospect_id INTEGER NOT NULL,
            type_action TEXT NOT NULL,
            description TEXT,
            date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prospect_id) REFERENCES agriweb_prospects(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    print("   ✅ prospect_actions créée")
    
    # Table des rendez-vous
    print("\n📅 Création de prospect_appointments...")
    cursor.execute('''
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
    conn.commit()
    print("   ✅ prospect_appointments créée")
    
    # Table des propositions commerciales
    print("\n💰 Création de prospect_proposals...")
    cursor.execute('''
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
    conn.commit()
    print("   ✅ prospect_proposals créée")
    
    # Table des fiches projets
    print("\n📁 Création de project_fiches...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_fiches (
            id SERIAL PRIMARY KEY,
            prospect_id INTEGER NOT NULL,
            nom_projet TEXT NOT NULL,
            type_projet TEXT DEFAULT 'autoconsommation',
            
            -- Infos client
            client_nom TEXT,
            client_email TEXT,
            client_telephone TEXT,
            client_adresse TEXT,
            
            -- Localisation projet
            adresse_projet TEXT,
            commune TEXT,
            code_postal TEXT,
            latitude REAL,
            longitude REAL,
            
            -- Infos cadastre
            parcelles TEXT,
            surface_m2 REAL,
            
            -- Technique
            puissance_kwc REAL,
            nombre_panneaux INTEGER,
            type_panneaux TEXT,
            puissance_panneau_wc INTEGER,
            
            -- Commercial
            prix_total_ht REAL,
            prix_total_ttc REAL,
            aides_subventions REAL,
            
            -- Production
            production_annuelle_kwh REAL,
            taux_autoconso_pct REAL,
            economies_annuelles REAL,
            
            -- Gestion
            statut_projet TEXT DEFAULT 'etude',
            notes TEXT,
            
            -- Dates
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_derniere_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_signature DATE,
            date_installation_prevue DATE,
            
            -- JSON data
            data_json TEXT,
            
            FOREIGN KEY (prospect_id) REFERENCES agriweb_prospects(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    print("   ✅ project_fiches créée")
    
    # Table des étapes projets
    print("\n📋 Création de project_etapes...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_etapes (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL,
            nom_etape TEXT NOT NULL,
            ordre INTEGER NOT NULL,
            statut TEXT DEFAULT 'a_faire',
            date_debut DATE,
            date_fin DATE,
            date_debut_prevue TIMESTAMP,
            date_fin_prevue TIMESTAMP,
            notes TEXT,
            responsable TEXT,
            documents TEXT,
            FOREIGN KEY (project_id) REFERENCES project_fiches(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    print("   ✅ project_etapes créée")
    
    # Table des documents projets
    print("\n📄 Création de project_documents...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_documents (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL,
            type_document TEXT NOT NULL,
            nom_fichier TEXT,
            chemin_fichier TEXT,
            taille_octets INTEGER,
            date_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploadeur TEXT,
            notes TEXT,
            FOREIGN KEY (project_id) REFERENCES project_fiches(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    print("   ✅ project_documents créée")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Toutes les tables CRM créées avec succès!")

def main():
    """Fonction principale"""
    try:
        # Diagnostic
        missing_tables = check_crm_tables()
        
        # Réparation si nécessaire
        if missing_tables:
            print(f"\n⚠️  {len(missing_tables)} table(s) manquante(s) détectée(s)")
            response = input("\n❓ Voulez-vous créer les tables manquantes? (oui/non): ")
            if response.lower() in ['oui', 'o', 'yes', 'y']:
                create_crm_tables()
                print("\n🔄 Re-vérification...")
                check_crm_tables()
            else:
                print("\n⏭️  Création annulée")
        else:
            print("\n✅ Toutes les tables CRM sont présentes!")
        
        print("\n" + "="*70)
        print("✅ DIAGNOSTIC TERMINÉ")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
