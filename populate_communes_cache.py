#!/usr/bin/env python3
"""
Peuple la table communes_insee_cache avec toutes les communes de France
via l'API Geo.gouv.fr
"""
import psycopg2
import requests
import os
from time import sleep

def populate_communes_cache():
    """Récupère toutes les communes de France et les insère dans la cache"""
    
    database_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_PUBLIC_URL non défini")
        return False
    
    print("="*70)
    print("PEUPLEMENT DU CACHE COMMUNES → CODE INSEE")
    print("="*70)
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # 1. Créer la table
        print("\n1. Création de la table communes_insee_cache...")
        with open('create_communes_cache.sql', 'r', encoding='utf-8') as f:
            sql = f.read()
        cur.execute(sql)
        conn.commit()
        print("   ✓ Table créée")
        
        # 2. Récupérer toutes les communes via API
        print("\n2. Récupération des communes via API Geo.gouv.fr...")
        url = "https://geo.api.gouv.fr/communes"
        params = {
            'fields': 'nom,code,codeDepartement,codesPostaux',
            'format': 'json',
            'limit': 50000  # Toutes les communes
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"   ❌ Erreur API: {response.status_code}")
            return False
        
        communes = response.json()
        print(f"   ✓ {len(communes)} communes récupérées")
        
        # 3. Insérer dans la base
        print("\n3. Insertion dans la base de données...")
        inserted = 0
        skipped = 0
        
        for i, commune in enumerate(communes):
            try:
                nom = commune.get('nom', '')
                code_insee = commune.get('code', '')
                code_dept = commune.get('codeDepartement', '')
                codes_postaux = commune.get('codesPostaux', [])
                
                if not nom or not code_insee:
                    skipped += 1
                    continue
                
                # Construire le nom complet avec codes postaux
                nom_complet = f"{nom} ({', '.join(codes_postaux[:3])})" if codes_postaux else nom
                
                cur.execute("""
                    INSERT INTO communes_insee_cache 
                        (nom_commune, nom_commune_lower, code_insee, code_departement, nom_complet)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (nom_commune_lower, code_insee) DO NOTHING;
                """, (nom, nom.lower(), code_insee, code_dept, nom_complet))
                
                inserted += 1
                
                # Commit par batch de 1000
                if inserted % 1000 == 0:
                    conn.commit()
                    print(f"   ⏳ {inserted} communes insérées...", end='\r')
                    
            except Exception as e:
                print(f"\n   ⚠️  Erreur pour {commune.get('nom', '?')}: {e}")
                skipped += 1
        
        # Commit final
        conn.commit()
        print(f"\n   ✓ {inserted} communes insérées, {skipped} ignorées")
        
        # 4. Vérifier les communes des prospects existants
        print("\n4. Vérification des communes de vos prospects...")
        cur.execute("""
            SELECT DISTINCT commune, COUNT(*) as nb
            FROM agriweb_prospects
            WHERE commune IS NOT NULL
            GROUP BY commune
            ORDER BY COUNT(*) DESC
            LIMIT 10;
        """)
        
        prospects_communes = cur.fetchall()
        print(f"\n   Top 10 communes dans vos prospects:")
        
        found = 0
        not_found = 0
        
        for commune, nb in prospects_communes:
            # Tester si elle est dans le cache
            cur.execute("""
                SELECT code_insee 
                FROM communes_insee_cache 
                WHERE nom_commune_lower = LOWER(%s)
                LIMIT 1;
            """, (commune,))
            
            result = cur.fetchone()
            if result:
                print(f"   ✓ {commune:30} ({nb:>4} prospects) → INSEE: {result[0]}")
                found += 1
            else:
                print(f"   ✗ {commune:30} ({nb:>4} prospects) → NON TROUVE dans cache")
                not_found += 1
        
        print(f"\n   Résultat: {found}/{found+not_found} communes trouvées dans le cache")
        
        # 5. Statistiques finales
        print("\n5. Statistiques du cache:")
        cur.execute("SELECT COUNT(*) FROM communes_insee_cache;")
        total_cache = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT code_departement) FROM communes_insee_cache;")
        total_depts = cur.fetchone()[0]
        
        print(f"   Total communes en cache: {total_cache}")
        print(f"   Départements couverts: {total_depts}")
        
        cur.close()
        conn.close()
        
        print("\n" + "="*70)
        print("✅ CACHE CREE ET PEUPLE AVEC SUCCES!")
        print("="*70)
        print("\n💡 Prochaine étape: Mettre à jour le trigger pour utiliser ce cache")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    import sys
    success = populate_communes_cache()
    sys.exit(0 if success else 1)
