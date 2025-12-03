import os, psycopg2

conn = psycopg2.connect(os.environ.get('DATABASE_PUBLIC_URL'))
cur = conn.cursor()

# Voir quelques exemples de prospects enrichis
cur.execute("""
    SELECT 
        id,
        nom_prospect,
        commune,
        parcelles_cadastrales::text,
        proprietaire_siren,
        proprietaire_denomination,
        proprietaire_forme_juridique
    FROM agriweb_prospects
    WHERE proprietaire_siren IS NOT NULL
    LIMIT 10
""")

print("PROSPECTS ENRICHIS (exemples):")
print("="*80)

for row in cur.fetchall():
    pid, nom, commune, parcelles, siren, denom, forme = row
    parcelles_short = parcelles[:50] if parcelles else ""
    denom_short = denom[:40] if denom else ""
    print(f"\nID {pid}: {nom or 'Sans nom'} ({commune})")
    print(f"  Parcelles: {parcelles_short}...")
    print(f"  SIREN: {siren}")
    print(f"  Proprietaire: {denom_short}")
    print(f"  Forme juridique: {forme or 'N/A'}")

conn.close()
