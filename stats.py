import os, psycopg2
conn = psycopg2.connect(os.environ.get('DATABASE_PUBLIC_URL'))
cur = conn.cursor()

cur.execute("""
    SELECT 
        COUNT(*) as total_json,
        COUNT(CASE WHEN proprietaire_siren IS NOT NULL THEN 1 END) as enrichis
    FROM agriweb_prospects
    WHERE parcelles_cadastrales LIKE '[%'
      AND parcelles_cadastrales != '[]'
""")

r = cur.fetchone()
total, enrichis = r
pct = enrichis/total*100 if total > 0 else 0

print(f"STATUT ENRICHISSEMENT:")
print(f"  Total prospects JSON valides: {total}")
print(f"  Enrichis: {enrichis} ({pct:.1f}%)")
print(f"  Non enrichis: {total - enrichis}")

conn.close()
