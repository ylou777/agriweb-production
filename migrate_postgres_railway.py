"""
Migration Railway PostgreSQL: Ajout colonnes géographiques postes BT/HTA
Exécuter avec: python migrate_postgres_railway.py
"""
import os
import psycopg2

# Remplacez cette URL par celle de Railway (onglet Credentials)
DATABASE_URL = input("Collez la DATABASE_URL de Railway (onglet Credentials): ").strip()

# Convertir postgres:// en postgresql://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

print(f"\n🔗 Connexion à Railway PostgreSQL...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("✅ Connecté avec succès!")
    
    # Liste des colonnes à ajouter
    colonnes = [
        ('poste_bt_commune', 'TEXT'),
        ('poste_bt_code_commune', 'TEXT'),
        ('poste_bt_epci', 'TEXT'),
        ('poste_bt_code_epci', 'TEXT'),
        ('poste_bt_departement', 'TEXT'),
        ('poste_bt_code_departement', 'TEXT'),
        ('poste_bt_region', 'TEXT'),
        ('poste_bt_code_region', 'TEXT'),
        ('poste_hta_commune', 'TEXT'),
        ('poste_hta_code_commune', 'TEXT'),
        ('poste_hta_epci', 'TEXT'),
        ('poste_hta_code_epci', 'TEXT'),
        ('poste_hta_departement', 'TEXT'),
        ('poste_hta_code_departement', 'TEXT'),
        ('poste_hta_region', 'TEXT'),
        ('poste_hta_code_region', 'TEXT'),
    ]
    
    print(f"\n📊 Ajout de {len(colonnes)} colonnes à agriweb_prospects...")
    
    for nom_col, type_col in colonnes:
        try:
            # Vérifier si la colonne existe déjà
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='agriweb_prospects' AND column_name=%s
            """, (nom_col,))
            
            if cursor.fetchone():
                print(f"  ⏭️  {nom_col} existe déjà")
            else:
                # Ajouter la colonne
                cursor.execute(f"ALTER TABLE agriweb_prospects ADD COLUMN {nom_col} {type_col}")
                print(f"  ✅ {nom_col} ajoutée")
        except Exception as e:
            print(f"  ⚠️  Erreur {nom_col}: {e}")
    
    conn.commit()
    print(f"\n✅ Migration terminée avec succès!")
    
    # Afficher le nombre de prospects
    cursor.execute("SELECT COUNT(*) FROM agriweb_prospects")
    count = cursor.fetchone()[0]
    print(f"📊 Nombre de prospects dans la base: {count}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    print("\n💡 Vérifiez que:")
    print("  1. La DATABASE_URL est correcte")
    print("  2. Vous avez psycopg2 installé: pip install psycopg2-binary")
