import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_PUBLIC_URL'])
cur = conn.cursor()

print("ANALYSE COMPLETE DE LA BASE proprietaires_parcelles")
print("="*70)

# 1. Statistiques générales
print("\n1. STATISTIQUES GENERALES:")
cur.execute("""
    SELECT 
        COUNT(*) as total_lignes,
        COUNT(DISTINCT siren) FILTER (WHERE siren IS NOT NULL) as total_siren_distincts,
        COUNT(DISTINCT code_commune) as communes_distinctes,
        COUNT(DISTINCT code_insee) FILTER (WHERE code_insee IS NOT NULL) as insee_distincts,
        COUNT(*) FILTER (WHERE siren IS NOT NULL) as lignes_avec_siren,
        COUNT(*) FILTER (WHERE siren IS NULL) as lignes_sans_siren
    FROM proprietaires_parcelles;
""")

stats = cur.fetchone()
print(f"  Total de lignes: {stats[0]:,}")
print(f"  Propriétaires distincts (SIREN): {stats[1]:,}")
print(f"  Communes distinctes (code_commune): {stats[2]:,}")
print(f"  Codes INSEE distincts: {stats[3]:,}")
print(f"  Parcelles avec propriétaire identifié: {stats[4]:,} ({round(100*stats[4]/stats[0],1)}%)")
print(f"  Parcelles sans propriétaire: {stats[5]:,} ({round(100*stats[5]/stats[0],1)}%)")

# 2. Départements couverts
print("\n2. DEPARTEMENTS COUVERTS:")
cur.execute("""
    SELECT 
        departement,
        COUNT(*) as nb_parcelles,
        COUNT(DISTINCT siren) FILTER (WHERE siren IS NOT NULL) as nb_proprietaires
    FROM proprietaires_parcelles
    WHERE departement IS NOT NULL
    GROUP BY departement
    ORDER BY COUNT(*) DESC
    LIMIT 10;
""")

print(f"  {'Dept':6} {'Parcelles':>12} {'Propriétaires':>15}")
print("  " + "-"*35)
for row in cur.fetchall():
    print(f"  {row[0]:6} {row[1]:>12,} {row[2]:>15,}")

# 3. Communes avec le plus de parcelles
print("\n3. TOP 10 COMMUNES (par nombre de parcelles):")
cur.execute("""
    SELECT 
        code_commune,
        code_insee,
        COUNT(*) as nb_parcelles,
        COUNT(DISTINCT siren) FILTER (WHERE siren IS NOT NULL) as nb_proprietaires
    FROM proprietaires_parcelles
    GROUP BY code_commune, code_insee
    ORDER BY COUNT(*) DESC
    LIMIT 10;
""")

print(f"  {'Code':6} {'INSEE':8} {'Parcelles':>12} {'Propriétaires':>15}")
print("  " + "-"*45)
for row in cur.fetchall():
    print(f"  {row[0]:6} {row[1] or 'N/A':8} {row[2]:>12,} {row[3]:>15,}")

# 4. Test de sections variées
print("\n4. DIVERSITE DES SECTIONS:")
cur.execute("""
    SELECT 
        LENGTH(section) as longueur,
        COUNT(DISTINCT section) as nb_sections_distinctes,
        COUNT(*) as nb_parcelles
    FROM proprietaires_parcelles
    WHERE section IS NOT NULL
    GROUP BY LENGTH(section)
    ORDER BY LENGTH(section);
""")

print(f"  {'Longueur':10} {'Sections':>10} {'Parcelles':>12}")
print("  " + "-"*35)
for row in cur.fetchall():
    print(f"  {row[0]:10} {row[1]:>10,} {row[2]:>12,}")

# 5. Exemples de sections à 2 lettres (comme dans vos prospects)
print("\n5. EXEMPLES DE SECTIONS A 2 LETTRES (format de vos prospects):")
cur.execute("""
    SELECT section, COUNT(*) as nb
    FROM proprietaires_parcelles
    WHERE LENGTH(section) = 2
    GROUP BY section
    ORDER BY COUNT(*) DESC
    LIMIT 10;
""")

sections = cur.fetchall()
print(f"  Sections trouvées: {', '.join([f'{s[0]} ({s[1]:,})' for s in sections[:5]])}")

# 6. Test de correspondance avec un prospect réel
print("\n6. TEST DE CORRESPONDANCE AVEC VOS PROSPECTS:")
cur.execute("""
    SELECT id, commune, parcelles_cadastrales
    FROM agriweb_prospects
    WHERE parcelles_cadastrales IS NOT NULL 
      AND parcelles_cadastrales != ''
      AND parcelles_cadastrales != '[]'
      AND proprietaire_siren IS NULL
    LIMIT 5;
""")

prospects_test = cur.fetchall()
import json

matches = 0
total_tested = 0

for p in prospects_test:
    try:
        parcelles = json.loads(p[2])
        if parcelles and len(parcelles) > 0:
            parcelle = parcelles[0]
            section = parcelle.get('section', '')
            numero = parcelle.get('numero', '').zfill(4)
            
            # Chercher SANS code_commune (comme fait le trigger maintenant)
            cur.execute("""
                SELECT COUNT(*) as matches
                FROM proprietaires_parcelles
                WHERE section = %s
                  AND numero = %s;
            """, (section, numero))
            
            count = cur.fetchone()[0]
            total_tested += 1
            
            status = "✓" if count > 0 else "✗"
            print(f"  {status} Prospect {p[0]} | {p[1]} | {section}-{numero} → {count} correspondance(s)")
            
            if count > 0:
                matches += 1
    except:
        pass

if total_tested > 0:
    print(f"\n  Résultat: {matches}/{total_tested} prospects ont des parcelles dans la base ({round(100*matches/total_tested,1)}%)")

cur.close()
conn.close()

print("\n" + "="*70)
print("CONCLUSION:")
print(f"  - Base contient {stats[0]:,} parcelles")
print(f"  - {stats[1]:,} propriétaires distincts identifiés")
print(f"  - Problème probable: Vos prospects utilisent section-numero mais SANS code_commune")
print(f"    ce qui crée des ambiguïtés (même section-numero existe dans plusieurs communes)")
