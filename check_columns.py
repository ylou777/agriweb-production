import psycopg2

DATABASE_URL = "postgresql://postgres:WbjgkcXDKvbbYJhWprDDQQobbpnggYJc@yamanote.proxy.rlwy.net:42931/railway"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'agriweb_prospects'
    ORDER BY ordinal_position
""")

print("Colonnes de la table agriweb_prospects :")
for col, dtype in cur.fetchall():
    print(f"  - {col} ({dtype})")

cur.close()
conn.close()
