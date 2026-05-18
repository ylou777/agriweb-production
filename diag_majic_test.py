import sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()
from mairies_diagnostic import get_parcelles_municipales, get_parcelles_publiques

for code, nom in [('23058','Puy-Malsignat'), ('19004','Albussac'), ('15096','Mandailles-Saint-Julien')]:
    mun = get_parcelles_municipales(code)
    pub = get_parcelles_publiques(code)
    print(f"\n{nom} ({code})")
    print(f"  municipales (fj=30) : {len(mun)}")
    print(f"  publiques (tous codes) : {len(pub)}")
    for r in mun[:3]:
        print(f"    section={r['section']} num={r['numero']} surface={r['contenance']} denom={r['denomination']} fj={r['forme_juridique']}")
    if not mun:
        # Tester sans filtre forme_juridique pour voir ce qu'il y a
        from mairies_diagnostic import _pg
        from psycopg2.extras import RealDictCursor
        try:
            conn = _pg()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT DISTINCT forme_juridique, denomination, COUNT(*) as n FROM proprietaires_parcelles WHERE code_insee=%s GROUP BY forme_juridique, denomination ORDER BY n DESC LIMIT 10", (code,))
            rows = cur.fetchall()
            conn.close()
            print(f"  Données brutes en base pour {code}:")
            for r in rows:
                print(f"    fj={r['forme_juridique']} denom={r['denomination']} n={r['n']}")
            if not rows:
                print(f"  → AUCUNE DONNÉE en base pour {code}")
        except Exception as e:
            print(f"  Erreur requête brute : {e}")
