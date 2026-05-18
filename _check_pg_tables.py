from mairies_campaign import list_campaigns, get_db

conn = get_db()
r = conn.execute(
    "SELECT table_name FROM information_schema.tables "
    "WHERE table_schema='public' AND table_name IN ('campaigns','recipients','unsubscribes')"
).fetchall()
print("Tables PG:", [x['table_name'] for x in r])
print("Campagnes:", list_campaigns())
conn.close()
