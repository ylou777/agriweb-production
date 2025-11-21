"""
Script de comparaison entre la base SQLite locale et PostgreSQL Railway
"""
import os
import sqlite3
from database_adapter import execute_query, IS_RAILWAY

def analyze_local_db():
    """Analyse la base SQLite locale"""
    db_path = os.path.join('..', 'KPI', 'kpi_sunstice.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Base locale introuvable: {db_path}")
        return None
    
    print("=" * 80)
    print("📊 ANALYSE BASE DE DONNÉES LOCALE (SQLite)")
    print("=" * 80)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Liste des tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"\n📁 Tables trouvées: {len(tables)}")
    for table in tables:
        print(f"   - {table}")
    
    # Analyse agriweb_prospects
    if 'agriweb_prospects' in tables:
        print("\n" + "=" * 80)
        print("🎯 TABLE: agriweb_prospects")
        print("=" * 80)
        
        # Nombre total
        cursor.execute("SELECT COUNT(*) FROM agriweb_prospects")
        total = cursor.fetchone()[0]
        print(f"\n📊 Total prospects: {total}")
        
        # Par type
        cursor.execute("SELECT type, COUNT(*) FROM agriweb_prospects GROUP BY type")
        types = cursor.fetchall()
        print("\n📈 Répartition par type:")
        for type_name, count in types:
            print(f"   {type_name or 'NULL'}: {count}")
        
        # Par statut
        cursor.execute("SELECT statut, COUNT(*) FROM agriweb_prospects GROUP BY statut")
        statuts = cursor.fetchall()
        print("\n📌 Répartition par statut:")
        for statut, count in statuts:
            print(f"   {statut or 'NULL'}: {count}")
        
        # Colonnes
        cursor.execute("PRAGMA table_info(agriweb_prospects)")
        columns = cursor.fetchall()
        print(f"\n📋 Nombre de colonnes: {len(columns)}")
        print("\n📝 Colonnes:")
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
        
        # Exemples de données
        cursor.execute("SELECT id, type, commune, nom_prospect, contact_nom, contact_telephone, statut FROM agriweb_prospects LIMIT 5")
        examples = cursor.fetchall()
        print("\n📄 Exemples de données (5 premiers):")
        for ex in examples:
            print(f"\n   ID: {ex[0]}")
            print(f"   Type: {ex[1]}")
            print(f"   Commune: {ex[2]}")
            print(f"   Nom: {ex[3]}")
            print(f"   Contact: {ex[4]}")
            print(f"   Téléphone: {ex[5]}")
            print(f"   Statut: {ex[6]}")
    
    conn.close()
    return {
        'tables': tables,
        'total_prospects': total if 'agriweb_prospects' in tables else 0,
        'types': dict(types) if 'agriweb_prospects' in tables else {},
        'statuts': dict(statuts) if 'agriweb_prospects' in tables else {},
        'columns': len(columns) if 'agriweb_prospects' in tables else 0
    }

def analyze_railway_db():
    """Analyse la base PostgreSQL Railway"""
    print("\n\n" + "=" * 80)
    print("🚀 ANALYSE BASE DE DONNÉES RAILWAY (PostgreSQL)")
    print("=" * 80)
    
    if not IS_RAILWAY:
        print("\n⚠️ Mode local détecté - impossible de se connecter à Railway")
        print("💡 Pour tester la connexion Railway, définir DATABASE_URL")
        return None
    
    # Liste des tables
    tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """
    tables = execute_query(tables_query, fetch_all=True)
    table_names = [t['table_name'] for t in tables] if tables else []
    
    print(f"\n📁 Tables trouvées: {len(table_names)}")
    for table in table_names:
        print(f"   - {table}")
    
    # Analyse agriweb_prospects
    if 'agriweb_prospects' in table_names:
        print("\n" + "=" * 80)
        print("🎯 TABLE: agriweb_prospects")
        print("=" * 80)
        
        # Nombre total
        total = execute_query("SELECT COUNT(*) as count FROM agriweb_prospects", fetch_one=True)
        total_count = total['count'] if total else 0
        print(f"\n📊 Total prospects: {total_count}")
        
        # Par type
        types = execute_query("""
            SELECT type, COUNT(*) as count 
            FROM agriweb_prospects 
            GROUP BY type
        """, fetch_all=True)
        print("\n📈 Répartition par type:")
        for t in (types or []):
            print(f"   {t['type'] or 'NULL'}: {t['count']}")
        
        # Par statut
        statuts = execute_query("""
            SELECT statut, COUNT(*) as count 
            FROM agriweb_prospects 
            GROUP BY statut
        """, fetch_all=True)
        print("\n📌 Répartition par statut:")
        for s in (statuts or []):
            print(f"   {s['statut'] or 'NULL'}: {s['count']}")
        
        # Colonnes
        columns = execute_query("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'agriweb_prospects'
            ORDER BY ordinal_position
        """, fetch_all=True)
        print(f"\n📋 Nombre de colonnes: {len(columns) if columns else 0}")
        print("\n📝 Colonnes:")
        for col in (columns or []):
            print(f"   {col['column_name']} ({col['data_type']})")
        
        # Exemples de données
        examples = execute_query("""
            SELECT id, type, commune, nom_prospect, contact_nom, contact_telephone, statut 
            FROM agriweb_prospects 
            LIMIT 5
        """, fetch_all=True)
        print("\n📄 Exemples de données (5 premiers):")
        for ex in (examples or []):
            print(f"\n   ID: {ex.get('id')}")
            print(f"   Type: {ex.get('type')}")
            print(f"   Commune: {ex.get('commune')}")
            print(f"   Nom: {ex.get('nom_prospect')}")
            print(f"   Contact: {ex.get('contact_nom')}")
            print(f"   Téléphone: {ex.get('contact_telephone')}")
            print(f"   Statut: {ex.get('statut')}")
        
        return {
            'tables': table_names,
            'total_prospects': total_count,
            'types': {t['type']: t['count'] for t in (types or [])},
            'statuts': {s['statut']: s['count'] for s in (statuts or [])},
            'columns': len(columns) if columns else 0
        }
    
    return None

def compare_databases():
    """Compare les deux bases de données"""
    local_data = analyze_local_db()
    railway_data = analyze_railway_db()
    
    print("\n\n" + "=" * 80)
    print("🔍 COMPARAISON DES BASES DE DONNÉES")
    print("=" * 80)
    
    if local_data and railway_data:
        print(f"\n📊 Nombre de prospects:")
        print(f"   Local (SQLite):   {local_data['total_prospects']}")
        print(f"   Railway (PostgreSQL): {railway_data['total_prospects']}")
        diff = railway_data['total_prospects'] - local_data['total_prospects']
        print(f"   Différence: {diff:+d}")
        
        print(f"\n📋 Nombre de colonnes:")
        print(f"   Local:   {local_data['columns']}")
        print(f"   Railway: {railway_data['columns']}")
        
        print(f"\n📁 Nombre de tables:")
        print(f"   Local:   {len(local_data['tables'])}")
        print(f"   Railway: {len(railway_data['tables'])}")
        
        # Tables manquantes
        local_set = set(local_data['tables'])
        railway_set = set(railway_data['tables'])
        
        missing_in_railway = local_set - railway_set
        missing_in_local = railway_set - local_set
        
        if missing_in_railway:
            print(f"\n⚠️ Tables présentes en local mais absentes sur Railway:")
            for table in missing_in_railway:
                print(f"   - {table}")
        
        if missing_in_local:
            print(f"\n✅ Tables présentes sur Railway mais absentes en local:")
            for table in missing_in_local:
                print(f"   - {table}")
        
        if not missing_in_railway and not missing_in_local:
            print(f"\n✅ Les mêmes tables sont présentes dans les deux bases")
    
    elif local_data:
        print("\n✅ Analyse locale complète")
        print("⚠️ Pas de données Railway (mode local)")
    else:
        print("\n❌ Impossible d'analyser les bases de données")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    compare_databases()
