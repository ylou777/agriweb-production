import os, psycopg2

conn = psycopg2.connect(os.environ.get('DATABASE_PUBLIC_URL'))
cur = conn.cursor()

cur.execute("""
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_name = 'agriweb_prospects'
    ORDER BY column_name
""")

print("COLONNES CRM (agriweb_prospects):")
print("="*60)

proprietaire_cols = []
other_cols = []

for col in cur.fetchall():
    col_name, data_type, max_len = col
    type_str = data_type if not max_len else f"{data_type}({max_len})"
    
    if col_name.startswith('proprietaire_'):
        proprietaire_cols.append(f"  {col_name:35} {type_str}")
    else:
        other_cols.append(f"  {col_name:35} {type_str}")

print("\nCOLONNES PROPRIETAIRE (enrichissement automatique):")
for c in proprietaire_cols:
    print(c)

print(f"\nAUTRES COLONNES ({len(other_cols)} colonnes):")
for c in other_cols[:20]:  # Limiter l'affichage
    print(c)
if len(other_cols) > 20:
    print(f"  ... et {len(other_cols) - 20} autres colonnes")

# Vérifier si enrichies
cur.execute("SELECT COUNT(*) FROM agriweb_prospects WHERE proprietaire_siren IS NOT NULL")
enrichis = cur.fetchone()[0]

print(f"\n{enrichis} prospects ont des données de propriétaire enrichies")

conn.close()
