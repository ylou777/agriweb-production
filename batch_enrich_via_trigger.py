import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_PUBLIC_URL'])
cur = conn.cursor()

print("ENRICHISSEMENT DES PROSPECTS EXISTANTS VIA TRIGGER UPDATE")
print("="*70)

# Forcer le trigger UPDATE sur tous les prospects avec parcelles
print("\nMise à jour de tous les prospects avec parcelles pour déclencher le trigger...")

cur.execute("""
    UPDATE agriweb_prospects
    SET parcelles_cadastrales = parcelles_cadastrales
    WHERE parcelles_cadastrales IS NOT NULL
      AND parcelles_cadastrales != ''
      AND parcelles_cadastrales != '[]'
      AND proprietaire_siren IS NULL
    RETURNING id;
""")

updated_ids = cur.fetchall()
conn.commit()

print(f"✓ {len(updated_ids)} prospects mis à jour")

# Vérifier combien ont été enrichis
print("\nVérification des enrichissements...")
cur.execute("""
    SELECT 
        COUNT(*) FILTER (WHERE proprietaire_siren IS NOT NULL) as enrichis,
        COUNT(*) as total
    FROM agriweb_prospects
    WHERE parcelles_cadastrales IS NOT NULL
      AND parcelles_cadastrales != ''
      AND parcelles_cadastrales != '[]';
""")

stats = cur.fetchone()
print(f"  Total avec parcelles: {stats[1]}")
print(f"  Enrichis: {stats[0]}")
print(f"  Taux: {round(100*stats[0]/stats[1], 1)}%")

# Exemples enrichis
print("\n5 Exemples de prospects enrichis:")
cur.execute("""
    SELECT id, nom_prospect, commune, proprietaire_siren, proprietaire_denomination
    FROM agriweb_prospects
    WHERE proprietaire_siren IS NOT NULL
    ORDER BY proprietaire_enrichi_date DESC NULLS LAST
    LIMIT 5;
""")

for p in cur.fetchall():
    print(f"  ID {p[0]}: {p[1] or '(sans nom)'} | {p[2]} | SIREN: {p[3]} | {p[4][:40] if p[4] else ''}")

cur.close()
conn.close()

print("\n" + "="*70)
print("✅ ENRICHISSEMENT BATCH TERMINE!")
