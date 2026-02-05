"""
Diagnostic complet: Vérifier pourquoi les prospects ont disparu
"""
import os
import sys

# Ajouter le répertoire courant au path pour importer database_adapter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database_adapter import execute_query
    
    print("="*70)
    print("🔍 DIAGNOSTIC BASE DE DONNÉES - PROSPECTS")
    print("="*70)
    
    # 1. Compter tous les prospects
    print("\n1️⃣ Comptage total:")
    total = execute_query('SELECT COUNT(*) as total FROM agriweb_prospects')
    if total:
        print(f"   ✅ Total prospects dans la base: {total[0]['total']}")
    else:
        print("   ❌ Erreur lors du comptage")
    
    # 2. Vérifier par statut
    print("\n2️⃣ Répartition par statut:")
    stats = execute_query("""
        SELECT statut, COUNT(*) as count 
        FROM agriweb_prospects 
        WHERE statut IS NOT NULL
        GROUP BY statut 
        ORDER BY count DESC
    """)
    if stats:
        for s in stats:
            print(f"   - {s['statut']}: {s['count']} prospects")
    
    # Compter les statuts NULL
    null_status = execute_query("SELECT COUNT(*) as count FROM agriweb_prospects WHERE statut IS NULL")
    if null_status and null_status[0]['count'] > 0:
        print(f"   - [NULL]: {null_status[0]['count']} prospects")
    
    # 3. Derniers prospects créés
    print("\n3️⃣ 15 derniers prospects créés:")
    recent = execute_query('''
        SELECT id, nom, adresse, commune, statut, created_at 
        FROM agriweb_prospects 
        ORDER BY created_at DESC NULLS LAST, id DESC 
        LIMIT 15
    ''')
    if recent:
        for p in recent:
            created = p.get('created_at', 'N/A')
            print(f"   #{p['id']:4d} | {p.get('nom', 'N/A'):30s} | {p.get('commune', 'N/A'):20s} | {p.get('statut', 'N/A'):15s} | {created}")
    else:
        print("   ❌ Aucun prospect trouvé!")
    
    # 4. Vérifier s'il y a des prospects sans commune
    print("\n4️⃣ Prospects sans commune (potentiellement corrompus):")
    no_commune = execute_query("""
        SELECT COUNT(*) as count 
        FROM agriweb_prospects 
        WHERE commune IS NULL OR commune = ''
    """)
    if no_commune:
        count = no_commune[0]['count']
        if count > 0:
            print(f"   ⚠️  {count} prospects sans commune")
            # Afficher quelques exemples
            examples = execute_query("""
                SELECT id, nom, adresse, statut 
                FROM agriweb_prospects 
                WHERE commune IS NULL OR commune = ''
                LIMIT 5
            """)
            if examples:
                for ex in examples:
                    print(f"      #{ex['id']}: {ex.get('nom', 'N/A')} - {ex.get('adresse', 'N/A')}")
        else:
            print(f"   ✅ Tous les prospects ont une commune")
    
    # 5. Vérifier s'il y a des prospects sans coordonnées GPS
    print("\n5️⃣ Prospects sans coordonnées GPS:")
    no_gps = execute_query("""
        SELECT COUNT(*) as count 
        FROM agriweb_prospects 
        WHERE latitude IS NULL OR longitude IS NULL
    """)
    if no_gps:
        count = no_gps[0]['count']
        if count > 0:
            print(f"   ⚠️  {count} prospects sans GPS")
        else:
            print(f"   ✅ Tous les prospects ont des coordonnées GPS")
    
    # 6. Vérifier la date de dernier prospect
    print("\n6️⃣ Date de création:")
    dates = execute_query("""
        SELECT 
            MIN(created_at) as premier,
            MAX(created_at) as dernier
        FROM agriweb_prospects
        WHERE created_at IS NOT NULL
    """)
    if dates and dates[0]:
        print(f"   Premier prospect: {dates[0].get('premier', 'N/A')}")
        print(f"   Dernier prospect: {dates[0].get('dernier', 'N/A')}")
    
    # 7. Prospects par commune (top 10)
    print("\n7️⃣ Top 10 communes avec le plus de prospects:")
    top_communes = execute_query("""
        SELECT commune, COUNT(*) as count 
        FROM agriweb_prospects 
        WHERE commune IS NOT NULL AND commune != ''
        GROUP BY commune 
        ORDER BY count DESC 
        LIMIT 10
    """)
    if top_communes:
        for i, c in enumerate(top_communes, 1):
            print(f"   {i}. {c['commune']:30s}: {c['count']:3d} prospects")
    
    print("\n" + "="*70)
    print("✅ Diagnostic terminé")
    print("="*70)
    
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("💡 Assurez-vous que database_adapter.py existe dans le répertoire courant")
except Exception as e:
    print(f"❌ Erreur lors du diagnostic: {e}")
    import traceback
    traceback.print_exc()
