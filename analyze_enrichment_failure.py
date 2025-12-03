import psycopg2
import os
import json

conn = psycopg2.connect(os.environ['DATABASE_PUBLIC_URL'])
cur = conn.cursor()

print("ANALYSE: Pourquoi si peu de prospects sont enrichis?")
print("="*70)

# Tester 50 prospects aléatoires
cur.execute("""
    SELECT id, commune, parcelles_cadastrales
    FROM agriweb_prospects
    WHERE parcelles_cadastrales IS NOT NULL 
      AND parcelles_cadastrales != ''
      AND parcelles_cadastrales != '[]'
      AND proprietaire_siren IS NULL
      AND commune NOT LIKE 'Commune %'
    ORDER BY RANDOM()
    LIMIT 50;
""")

prospects = cur.fetchall()

stats = {
    'total': 0,
    'commune_non_trouvee': 0,
    'parcelle_non_trouvee': 0,
    'siren_null': 0,
    'enrichissable': 0
}

for p in prospects:
    try:
        parcelles = json.loads(p[2])
        if not parcelles or len(parcelles) == 0:
            continue
        
        stats['total'] += 1
        parcelle = parcelles[0]
        section = parcelle.get('section', '')
        numero = parcelle.get('numero', '').zfill(4)
        commune = p[1]
        
        # Vérifier cache commune
        cur.execute("""
            SELECT code_insee FROM communes_insee_cache
            WHERE nom_commune_lower = LOWER(%s) LIMIT 1;
        """, (commune,))
        
        cache = cur.fetchone()
        if not cache:
            stats['commune_non_trouvee'] += 1
            print(f"[X] Prospect {p[0]:4} | Commune '{commune}' non trouvee dans cache")
            continue
        
        code_insee = cache[0]
        
        # Chercher la parcelle
        cur.execute("""
            SELECT siren, denomination
            FROM proprietaires_parcelles
            WHERE (code_commune = %s OR code_insee = %s)
              AND section = %s
              AND numero = %s
            LIMIT 1;
        """, (code_insee, code_insee, section, numero))
        
        prop = cur.fetchone()
        if not prop:
            stats['parcelle_non_trouvee'] += 1
            print(f"[X] Prospect {p[0]:4} | {commune:20} | Parcelle {code_insee}-{section}-{numero} non trouvee")
        elif prop[0] is None:
            stats['siren_null'] += 1
            print(f"[!] Prospect {p[0]:4} | {commune:20} | Parcelle trouvee mais SIREN NULL")
        else:
            stats['enrichissable'] += 1
            print(f"[OK] Prospect {p[0]:4} | {commune:20} | {code_insee}-{section}-{numero} -> {prop[0]} | {prop[1][:30]}")
    except Exception as e:
        print(f"[ERR] Erreur prospect {p[0]}: {e}")

print("\n" + "="*70)
print("STATISTIQUES SUR 50 PROSPECTS:")
print(f"  Total testés: {stats['total']}")
print(f"  Commune non trouvée dans cache: {stats['commune_non_trouvee']} ({round(100*stats['commune_non_trouvee']/stats['total'],1)}%)")
print(f"  Parcelle non trouvée: {stats['parcelle_non_trouvee']} ({round(100*stats['parcelle_non_trouvee']/stats['total'],1)}%)")
print(f"  Parcelle trouvée mais SIREN NULL: {stats['siren_null']} ({round(100*stats['siren_null']/stats['total'],1)}%)")
print(f"  ENRICHISSABLES: {stats['enrichissable']} ({round(100*stats['enrichissable']/stats['total'],1)}%)")

print("\n💡 CONCLUSION:")
if stats['parcelle_non_trouvee'] > stats['total'] * 0.5:
    print("   La majorité des parcelles n'existent PAS dans proprietaires_parcelles")
elif stats['siren_null'] > stats['total'] * 0.5:
    print("   La majorité des parcelles existent mais n'ont PAS de propriétaire identifié (SIREN NULL)")
else:
    print(f"   {round(100*stats['enrichissable']/stats['total'],1)}% des prospects PEUVENT être enrichis")

cur.close()
conn.close()
