#!/usr/bin/env python3
import os, sys, psycopg2

url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
conn = psycopg2.connect(url)
cur = conn.cursor()

# Créer fonction
sql = open('create_enrich_function.sql', 'r', encoding='utf-8').read()
cur.execute(sql)
conn.commit()
print("Fonction creee")

# Tester sur prospect 158
cur.execute("SELECT * FROM enrich_one_prospect(158)")
r = cur.fetchone()
print(f"ID:{r[0]} SIREN:{r[1]} Denom:{r[2][:50]} Success:{r[3]}")

# Stats
cur.execute("SELECT COUNT(*), COUNT(proprietaire_siren) FROM agriweb_prospects WHERE parcelles_cadastrales IS NOT NULL")
r = cur.fetchone()
print(f"Total parcelles:{r[0]} SIREN:{r[1]} ({r[1]/r[0]*100:.1f}%)")
