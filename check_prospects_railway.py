"""
Script pour vérifier les prospects dans PostgreSQL Railway
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# URL de connexion Railway (à définir en variable d'environnement)
DATABASE_URL = os.environ.get('DATABASE_URL', '')

if not DATABASE_URL:
    print("⚠️ Variable DATABASE_URL non définie")
    print("📋 Pour Railway, récupérez l'URL dans : Railway > PostgreSQL > Connect > Database URL")
    print("\nPuis exécutez:")
    print('$env:DATABASE_URL="postgresql://..."')
    print("python check_prospects_railway.py")
    exit(1)

try:
    print("🔌 Connexion à PostgreSQL Railway...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # 1. Vérifier le nombre total de prospects
    print("\n📊 VÉRIFICATION TABLE agriweb_prospects")
    print("=" * 60)
    
    cursor.execute("SELECT COUNT(*) as total FROM agriweb_prospects")
    result = cursor.fetchone()
    total = result['total']
    print(f"✅ Total prospects: {total}")
    
    # 2. Vérifier par statut
    cursor.execute("""
        SELECT statut, COUNT(*) as count 
        FROM agriweb_prospects 
        GROUP BY statut
        ORDER BY count DESC
    """)
    statuts = cursor.fetchall()
    
    if statuts:
        print("\n📈 Répartition par statut:")
        for row in statuts:
            print(f"  - {row['statut']}: {row['count']}")
    
    # 3. Vérifier par type
    cursor.execute("""
        SELECT type, COUNT(*) as count 
        FROM agriweb_prospects 
        GROUP BY type
        ORDER BY count DESC
    """)
    types = cursor.fetchall()
    
    if types:
        print("\n🏷️  Répartition par type:")
        for row in types:
            print(f"  - {row['type']}: {row['count']}")
    
    # 4. Afficher les 5 derniers prospects
    if total > 0:
        cursor.execute("""
            SELECT id, type, commune, adresse, statut, date_creation
            FROM agriweb_prospects
            ORDER BY date_creation DESC
            LIMIT 5
        """)
        derniers = cursor.fetchall()
        
        print("\n📋 5 derniers prospects créés:")
        for p in derniers:
            print(f"  ID {p['id']}: {p['type']} - {p['commune']} ({p['statut']})")
            print(f"    └─ {p['adresse'][:60]}...")
            print(f"    └─ Créé: {p['date_creation']}")
    else:
        print("\n⚠️  AUCUN PROSPECT TROUVÉ !")
        print("\n💡 La table existe mais est vide.")
        print("   Vous devez exporter des rapports vers le CRM pour créer des prospects.")
    
    # 5. Vérifier les autres tables CRM
    print("\n\n📊 AUTRES TABLES CRM")
    print("=" * 60)
    
    tables = [
        'crm_appointments',
        'prospect_proposals', 
        'project_fiches',
        'project_etapes',
        'project_documents'
    ]
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) as total FROM {table}")
            result = cursor.fetchone()
            print(f"✅ {table}: {result['total']} entrées")
        except Exception as e:
            print(f"⚠️  {table}: Erreur - {e}")
    
    conn.close()
    print("\n✅ Diagnostic terminé")
    
except psycopg2.Error as e:
    print(f"\n❌ Erreur PostgreSQL: {e}")
    print("\n💡 Vérifiez que:")
    print("   1. La variable DATABASE_URL est correcte")
    print("   2. Vous avez accès à la base Railway")
    print("   3. Les tables CRM sont bien créées")
except Exception as e:
    print(f"\n❌ Erreur: {e}")
