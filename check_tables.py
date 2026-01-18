from database_adapter import execute_query

# Lister toutes les tables
tables = execute_query("SELECT name FROM sqlite_master WHERE type='table'", fetch_all=True)
print("\n📋 Tables dans la base de données:")
for table in tables:
    print(f"  - {table['name']}")

# Vérifier si la table users existe (sous différents noms possibles)
user_tables = [t['name'] for t in tables if 'user' in t['name'].lower()]
print(f"\n👤 Tables liées aux utilisateurs: {user_tables}")

# Afficher la structure de agriweb_prospects
print("\n🏗️  Structure de agriweb_prospects:")
columns = execute_query("PRAGMA table_info(agriweb_prospects)", fetch_all=True)
for col in columns:
    print(f"  - {col['name']}: {col['type']}")
