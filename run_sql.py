import os, psycopg2
url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
conn = psycopg2.connect(url)
cur = conn.cursor()

print("Execution SQL directe...")
sql = open('enrich_sql_direct.sql', 'r', encoding='utf-8').read()
queries = sql.split(';')

for i, q in enumerate(queries):
    q = q.strip()
    if q:
        print(f"Requete {i+1}...")
        cur.execute(q)
        if cur.description:
            result = cur.fetchone()
            if result:
                print(f"  Total: {result[0]}, SIREN: {result[1]}, Taux: {result[2]}%")
        conn.commit()

print("Termine")
conn.close()
