"""Vérifier l'état de la base de données"""
from database_adapter import execute_query

# Compter les prospects
total = execute_query('SELECT COUNT(*) as total FROM agriweb_prospects')
print(f"📊 Total prospects: {total[0]['total'] if total else 0}")

# Derniers prospects
recent = execute_query('SELECT id, nom, adresse, commune, statut, created_at FROM agriweb_prospects ORDER BY id DESC LIMIT 10')
print(f"\n📋 10 derniers prospects:")
if recent:
    for p in recent:
        print(f"  #{p['id']}: {p['nom']} - {p['commune']} (statut: {p['statut']})")
else:
    print("  ❌ Aucun prospect trouvé!")

# Prospects par statut
stats = execute_query("""
    SELECT statut, COUNT(*) as count 
    FROM agriweb_prospects 
    GROUP BY statut 
    ORDER BY count DESC
""")
print(f"\n📈 Prospects par statut:")
if stats:
    for s in stats:
        print(f"  {s['statut']}: {s['count']}")
