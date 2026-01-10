"""
Script à exécuter DIRECTEMENT sur Railway Shell pour analyser la base PostgreSQL
Usage: python check_railway_db.py
"""
import os
import sys

# Vérifier si on est sur Railway
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL non trouvée - ce script doit être exécuté sur Railway Shell")
    print("💡 Commande: railway shell puis python check_railway_db.py")
    sys.exit(1)

print("✅ Connexion Railway détectée")
print("=" * 80)

import psycopg2
from psycopg2.extras import RealDictCursor

# Corriger l'URL si nécessaire
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("📊 ANALYSE BASE DE DONNÉES RAILWAY (PostgreSQL)")
    print("=" * 80)
    
    # Liste des tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = [row['table_name'] for row in cursor.fetchall()]
    
    print(f"\n📁 Tables trouvées: {len(tables)}")
    for table in tables:
        print(f"   - {table}")
    
    # Analyse agriweb_prospects si elle existe
    if 'agriweb_prospects' in tables:
        print("\n" + "=" * 80)
        print("🎯 TABLE: agriweb_prospects")
        print("=" * 80)
        
        # Nombre total
        cursor.execute("SELECT COUNT(*) as count FROM agriweb_prospects")
        total = cursor.fetchone()['count']
        print(f"\n📊 Total prospects: {total}")
        
        # Par type
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM agriweb_prospects 
            GROUP BY type
            ORDER BY count DESC
        """)
        types = cursor.fetchall()
        print("\n📈 Répartition par type:")
        for t in types:
            print(f"   {t['type'] or 'NULL'}: {t['count']}")
        
        # Par statut
        cursor.execute("""
            SELECT statut, COUNT(*) as count 
            FROM agriweb_prospects 
            GROUP BY statut
            ORDER BY count DESC
        """)
        statuts = cursor.fetchall()
        print("\n📌 Répartition par statut:")
        for s in statuts:
            print(f"   {s['statut'] or 'NULL'}: {s['count']}")
        
        # Colonnes
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'agriweb_prospects'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        print(f"\n📋 Nombre de colonnes: {len(columns)}")
        print("\n📝 Colonnes:")
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"   {col['column_name']} ({col['data_type']}) {nullable}")
        
        # Exemples de données
        cursor.execute("""
            SELECT id, type, commune, nom_prospect, contact_nom, 
                   contact_telephone, statut, date_creation 
            FROM agriweb_prospects 
            ORDER BY date_creation DESC
            LIMIT 5
        """)
        examples = cursor.fetchall()
        print("\n📄 Exemples de données (5 plus récents):")
        for ex in examples:
            print(f"\n   ID: {ex['id']}")
            print(f"   Type: {ex['type']}")
            print(f"   Commune: {ex['commune']}")
            print(f"   Nom: {ex['nom_prospect']}")
            print(f"   Contact: {ex['contact_nom']}")
            print(f"   Téléphone: {ex['contact_telephone']}")
            print(f"   Statut: {ex['statut']}")
            print(f"   Créé le: {ex['date_creation']}")
        
        # Vérifier les données avec téléphone
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM agriweb_prospects 
            WHERE contact_telephone IS NOT NULL 
            AND contact_telephone != ''
        """)
        with_phone = cursor.fetchone()['count']
        print(f"\n📞 Prospects avec téléphone: {with_phone} / {total}")
        
        # Vérifier les données avec email
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM agriweb_prospects 
            WHERE contact_email IS NOT NULL 
            AND contact_email != ''
        """)
        with_email = cursor.fetchone()['count']
        print(f"📧 Prospects avec email: {with_email} / {total}")
        
        # Vérifier les données avec contact_nom
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM agriweb_prospects 
            WHERE contact_nom IS NOT NULL 
            AND contact_nom != ''
        """)
        with_contact = cursor.fetchone()['count']
        print(f"👤 Prospects avec nom contact: {with_contact} / {total}")
    
    # Autres tables CRM
    for table in ['project_fiches', 'project_etapes', 'project_documents']:
        if table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()['count']
            print(f"\n📊 {table}: {count} enregistrements")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ Analyse terminée")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
