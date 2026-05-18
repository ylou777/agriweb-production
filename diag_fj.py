from dotenv import load_dotenv; load_dotenv()
from mairies_diagnostic import _pg
from psycopg2.extras import RealDictCursor
conn = _pg()
cur = conn.cursor(cursor_factory=RealDictCursor)
cur.execute("SELECT forme_juridique, COUNT(*) n FROM proprietaires_parcelles GROUP BY forme_juridique ORDER BY n DESC LIMIT 20")
for r in cur.fetchall():
    print(r['forme_juridique'], r['n'])
conn.close()
