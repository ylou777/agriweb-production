import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_PUBLIC_URL'])
cur = conn.cursor()

print("ANALYSE DES COMMUNES DANS proprietaires_parcelles")
print("="*70)

# Trouver des communes avec beaucoup de parcelles
cur.execute("""
    SELECT 
        code_commune,
        code_insee,
        COUNT(*) as nb_parcelles,
        COUNT(DISTINCT siren) FILTER (WHERE siren IS NOT NULL) as nb_proprietaires
    FROM proprietaires_parcelles
    GROUP BY code_commune, code_insee
    HAVING COUNT(*) > 100
    ORDER BY COUNT(*) DESC
    LIMIT 20;
""")

print("\nCommunes avec le plus de parcelles:")
print(f"{'Code':8} {'INSEE':8} {'Parcelles':>10} {'Propriétaires':>13}")
print("-" * 45)

communes_dispo = []
for row in cur.fetchall():
    print(f"{row[0]:8} {row[1] or 'N/A':8} {row[2]:>10} {row[3]:>13}")
    if row[1]:  # Si code INSEE disponible
        communes_dispo.append(row[1])

# Chercher le nom des communes via code INSEE
if communes_dispo:
    print("\n" + "="*70)
    print("Pour tester l'enrichissement, utilisez des prospects de ces communes:")
    print("="*70)
    
    import requests
    for code_insee in communes_dispo[:5]:  # Top 5
        try:
            response = requests.get(f"https://geo.api.gouv.fr/communes/{code_insee}", timeout=3)
            if response.status_code == 200:
                data = response.json()
                nom_commune = data.get('nom', 'Inconnu')
                
                # Compter les prospects de cette commune
                cur.execute("""
                    SELECT COUNT(*)
                    FROM agriweb_prospects
                    WHERE LOWER(commune) = LOWER(%s)
                      AND parcelles_cadastrales IS NOT NULL
                      AND parcelles_cadastrales != ''
                      AND parcelles_cadastrales != '[]';
                """, (nom_commune,))
                
                nb_prospects = cur.fetchone()[0]
                print(f"{nom_commune:30} (INSEE: {code_insee}) → {nb_prospects} prospects")
        except:
            pass

cur.close()
conn.close()

print("\n💡 SOLUTION:")
print("   1. Soit créer des prospects avec des parcelles REELLES de ces communes")
print("   2. Soit charger plus de données dans proprietaires_parcelles")
