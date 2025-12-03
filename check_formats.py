import os, psycopg2
conn = psycopg2.connect(os.environ.get('DATABASE_PUBLIC_URL'))
cur = conn.cursor()

# Format texte
cur.execute("""
    SELECT COUNT(*) 
    FROM agriweb_prospects 
    WHERE parcelles_cadastrales NOT LIKE '[%' 
      AND parcelles_cadastrales IS NOT NULL 
      AND parcelles_cadastrales != '' 
      AND proprietaire_siren IS NULL
""")
texte = cur.fetchone()[0]

# Format JSON
cur.execute("""
    SELECT COUNT(*) 
    FROM agriweb_prospects 
    WHERE parcelles_cadastrales LIKE '[%'
      AND proprietaire_siren IS NULL
""")
json_format = cur.fetchone()[0]

# Total enrichis
cur.execute("SELECT COUNT(*) FROM agriweb_prospects WHERE proprietaire_siren IS NOT NULL")
enrichis = cur.fetchone()[0]

print(f"Format texte sans SIREN: {texte}")
print(f"Format JSON sans SIREN: {json_format}")
print(f"Total enrichis: {enrichis}")

# Exemples format texte
cur.execute("""
    SELECT id, parcelles_cadastrales 
    FROM agriweb_prospects 
    WHERE parcelles_cadastrales NOT LIKE '[%' 
      AND parcelles_cadastrales IS NOT NULL
      AND proprietaire_siren IS NULL
    LIMIT 5
""")
print("\nExemples format texte:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()
