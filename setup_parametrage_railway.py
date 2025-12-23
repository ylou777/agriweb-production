"""
Script pour créer les tables de paramétrage en base de données Railway
"""
import psycopg2
import os

DATABASE_URL = "postgresql://postgres:zDSMToBBVwIZDDOwzgZPPIuoCeNdBQou@junction.proxy.rlwy.net:43445/railway"

print("🔗 Connexion à Railway PostgreSQL...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Lire le fichier SQL
    with open('create_tables_parametrage.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    print("📄 Exécution du script SQL...")
    cursor.execute(sql_script)
    conn.commit()
    
    print("✅ Tables créées avec succès!")
    
    # Vérifier les données insérées
    cursor.execute("SELECT nom_entreprise, telephone, email FROM parametrage_entreprise")
    entreprise = cursor.fetchone()
    if entreprise:
        print(f"\n📋 Entreprise configurée: {entreprise[0]}")
        print(f"   Tél: {entreprise[1]}, Email: {entreprise[2]}")
    
    cursor.execute("SELECT COUNT(*) FROM parametrage_prix_organes")
    nb_prix = cursor.fetchone()[0]
    print(f"💰 {nb_prix} prix d'organes configurés")
    
    cursor.execute("SELECT COUNT(*) FROM parametrage_main_oeuvre")
    nb_mo = cursor.fetchone()[0]
    print(f"👷 {nb_mo} prestations main d'œuvre configurées")
    
    cursor.close()
    conn.close()
    
    print("\n✨ Paramétrage initial terminé!")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
