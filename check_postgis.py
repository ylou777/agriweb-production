"""
Vérifier et activer PostGIS sur Railway
"""
import psycopg2
import os

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Vérifier les extensions disponibles
print("📋 Extensions PostGIS disponibles:")
cur.execute("SELECT name, default_version, installed_version FROM pg_available_extensions WHERE name LIKE 'postgis%';")
for row in cur.fetchall():
    print(f"   - {row[0]}: version {row[1]}, installée: {row[2] or 'NON'}")

# Essayer d'activer PostGIS
print("\n🔧 Tentative d'activation de PostGIS...")
try:
    cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    conn.commit()
    print("✅ PostGIS activé!")
    
    # Vérifier la version
    cur.execute("SELECT PostGIS_version();")
    version = cur.fetchone()[0]
    print(f"   Version: {version}")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    conn.rollback()

cur.close()
conn.close()
