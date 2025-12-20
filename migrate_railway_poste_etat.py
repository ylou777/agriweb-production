"""
Migration Railway: Ajout colonnes poste_bt_etat et poste_hta_etat
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Essayer de charger .env.railway s'il existe
if os.path.exists('.env.railway'):
    load_dotenv('.env.railway')
    print("📋 Chargement .env.railway")
else:
    load_dotenv()
    print("📋 Chargement .env")

def migrate_railway():
    """Ajoute les colonnes etat aux postes BT et HTA"""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("\n❌ DATABASE_URL non trouvée dans l'environnement")
        print("\n💡 Options:")
        print("1. Créer un fichier .env.railway avec DATABASE_URL=postgresql://...")
        print("2. Récupérer l'URL depuis Railway dashboard > Variables")
        print("3. Définir la variable: $env:DATABASE_URL='postgresql://...'")
        return False
    
    print(f"🔗 Connexion à Railway PostgreSQL...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Vérifier si les colonnes existent déjà
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'agriweb_prospects' 
            AND column_name IN ('poste_bt_etat', 'poste_hta_etat')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        if 'poste_bt_etat' in existing_columns and 'poste_hta_etat' in existing_columns:
            print("✅ Colonnes poste_bt_etat et poste_hta_etat déjà présentes")
        else:
            print("📝 Ajout des colonnes manquantes...")
            
            if 'poste_bt_etat' not in existing_columns:
                cursor.execute("ALTER TABLE agriweb_prospects ADD COLUMN poste_bt_etat TEXT")
                print("   ✅ Colonne poste_bt_etat ajoutée")
            
            if 'poste_hta_etat' not in existing_columns:
                cursor.execute("ALTER TABLE agriweb_prospects ADD COLUMN poste_hta_etat TEXT")
                print("   ✅ Colonne poste_hta_etat ajoutée")
            
            conn.commit()
            print("✅ Migration terminée avec succès")
        
        # Afficher quelques statistiques
        cursor.execute("SELECT COUNT(*) FROM agriweb_prospects")
        count = cursor.fetchone()[0]
        print(f"📊 Nombre total de prospects: {count}")
        
        cursor.execute("""
            SELECT COUNT(*) FROM agriweb_prospects 
            WHERE poste_bt_nom IS NOT NULL OR poste_hta_nom IS NOT NULL
        """)
        count_with_poste = cursor.fetchone()[0]
        print(f"📊 Prospects avec info poste: {count_with_poste}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur migration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    migrate_railway()
