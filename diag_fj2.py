from dotenv import load_dotenv; load_dotenv()
from mairies_diagnostic import _pg
from psycopg2.extras import RealDictCursor
conn = _pg()
cur = conn.cursor(cursor_factory=RealDictCursor)
# Top dénominations pour les codes les plus fréquents
for fj in ['7210', '7220', '7313', '9900', '9220', '7113']:
    cur.execute(
        "SELECT denomination, COUNT(*) n FROM proprietaires_parcelles "
        "WHERE forme_juridique=%s GROUP BY denomination ORDER BY n DESC LIMIT 3",
        (fj,)
    )
    rows = cur.fetchall()
    denoms = [r['denomination'] for r in rows]
    print(f"fj={fj}: {denoms}")
conn.close()
