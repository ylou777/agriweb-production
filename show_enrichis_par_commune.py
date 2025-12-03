"""
Afficher la répartition des prospects enrichis par commune
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Connexion Railway - utiliser DATABASE_PUBLIC_URL pour connexion externe
DATABASE_URL = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')

if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

print("🔍 Répartition des 41 prospects enrichis par commune\n")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# Compter par commune
cursor.execute("""
    SELECT 
        commune,
        COUNT(*) as nb_enrichis,
        STRING_AGG(DISTINCT proprietaire_denomination, ', ' ORDER BY proprietaire_denomination) as proprietaires
    FROM agriweb_prospects
    WHERE proprietaire_siren IS NOT NULL
    GROUP BY commune
    ORDER BY nb_enrichis DESC, commune
""")

results = cursor.fetchall()

print(f"{'Commune':<30} {'Nb enrichis':<15} {'Propriétaires'}")
print("=" * 120)

total = 0
for row in results:
    commune = row['commune'] or 'N/A'
    nb = row['nb_enrichis']
    proprietaires = row['proprietaires'][:80] + '...' if len(row['proprietaires']) > 80 else row['proprietaires']
    
    print(f"{commune:<30} {nb:<15} {proprietaires}")
    total += nb

print("=" * 120)
print(f"{'TOTAL':<30} {total:<15}")

cursor.close()
conn.close()
