import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_PUBLIC_URL'])
cur = conn.cursor()

print("VERIFICATION DES ENRICHISSEMENTS CRM")
print("="*70)

# 1. Vérifier les colonnes
print("\n1. Colonnes proprietaire_* dans agriweb_prospects:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'agriweb_prospects' 
      AND column_name LIKE 'proprietaire_%'
    ORDER BY column_name;
""")

columns = cur.fetchall()
if columns:
    for col in columns:
        print(f"   - {col[0]}: {col[1]}")
else:
    print("   AUCUNE colonne proprietaire_* trouvée!")

# 2. Compter les enrichissements
print("\n2. Statistiques d'enrichissement:")
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE proprietaire_siren IS NOT NULL) as avec_siren,
        COUNT(*) FILTER (WHERE proprietaire_denomination IS NOT NULL) as avec_denom,
        COUNT(*) FILTER (WHERE parcelles_cadastrales IS NOT NULL AND parcelles_cadastrales != '' AND parcelles_cadastrales != '[]') as avec_parcelles
    FROM agriweb_prospects;
""")

stats = cur.fetchone()
print(f"   Total prospects: {stats[0]}")
print(f"   Avec SIREN: {stats[1]}")
print(f"   Avec dénomination: {stats[2]}")
print(f"   Avec parcelles: {stats[3]}")

# 3. Exemples de prospects enrichis
print("\n3. Exemples de prospects ENRICHIS (si existants):")
cur.execute("""
    SELECT id, nom_prospect, commune, proprietaire_siren, proprietaire_denomination, proprietaire_enrichi_date
    FROM agriweb_prospects
    WHERE proprietaire_siren IS NOT NULL
    ORDER BY proprietaire_enrichi_date DESC
    LIMIT 5;
""")

enriched = cur.fetchall()
if enriched:
    for p in enriched:
        print(f"   ID {p[0]}: {p[1] or '(sans nom)'} | {p[2]} | SIREN: {p[3]} | {p[4][:40] if p[4] else ''} | {p[5]}")
else:
    print("   AUCUN prospect enrichi trouvé!")

# 4. Exemples de prospects NON enrichis avec parcelles
print("\n4. Exemples de prospects NON enrichis (avec parcelles):")
cur.execute("""
    SELECT id, nom_prospect, commune, parcelles_cadastrales
    FROM agriweb_prospects
    WHERE parcelles_cadastrales IS NOT NULL 
      AND parcelles_cadastrales != ''
      AND parcelles_cadastrales != '[]'
      AND proprietaire_siren IS NULL
    ORDER BY id DESC
    LIMIT 5;
""")

not_enriched = cur.fetchall()
for p in not_enriched:
    parcelle_preview = p[3][:60] if p[3] and len(p[3]) > 60 else p[3]
    print(f"   ID {p[0]}: {p[1] or '(sans nom)'} | {p[2]} | {parcelle_preview}...")

# 5. Vérifier les triggers
print("\n5. Triggers actifs sur agriweb_prospects:")
cur.execute("""
    SELECT trigger_name, event_manipulation, action_timing
    FROM information_schema.triggers
    WHERE event_object_table = 'agriweb_prospects'
      AND trigger_name LIKE '%enrich%';
""")

triggers = cur.fetchall()
if triggers:
    for t in triggers:
        print(f"   - {t[0]}: {t[2]} {t[1]}")
else:
    print("   AUCUN trigger d'enrichissement trouvé!")

cur.close()
conn.close()

print("\n" + "="*70)
print("DIAGNOSTIC:")
if not columns:
    print("❌ Les colonnes proprietaire_* n'existent PAS - Le trigger n'a pas été déployé correctement")
elif not triggers:
    print("❌ Les triggers d'enrichissement ne sont PAS actifs")
elif stats[1] == 0:
    print("⚠️  Les colonnes et triggers existent mais AUCUN prospect n'est enrichi")
    print("   Raison probable: Les parcelles des prospects ne correspondent pas à celles dans proprietaires_parcelles")
else:
    print(f"✅ Système fonctionnel: {stats[1]} prospects enrichis sur {stats[0]}")
