"""
Migration Railway: Ajout colonnes géographiques postes BT/HTA
Ajoute: commune, code_commune, epci, code_epci, departement, code_departement, region, code_region
"""
import os
import sys

# Utiliser directement psycopg2 avec DATABASE_URL de l'environnement Railway
try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("❌ psycopg2 non installé. Installez-le avec: pip install psycopg2-binary")
    sys.exit(1)

def migrate_railway():
    """Ajoute les colonnes géographiques aux postes BT et HTA"""
    
    # Railway injecte automatiquement DATABASE_URL
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL non trouvée dans l'environnement")
        print("💡 Ce script doit être exécuté sur Railway ou avec DATABASE_URL définie")
        return False
    
    # Railway peut fournir postgres:// au lieu de postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    print(f"🔗 Connexion à Railway PostgreSQL...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Liste des colonnes à ajouter (BT)
        bt_columns = [
            ('poste_bt_commune', 'TEXT'),
            ('poste_bt_code_commune', 'TEXT'),
            ('poste_bt_epci', 'TEXT'),
            ('poste_bt_code_epci', 'TEXT'),
            ('poste_bt_departement', 'TEXT'),
            ('poste_bt_code_departement', 'TEXT'),
            ('poste_bt_region', 'TEXT'),
            ('poste_bt_code_region', 'TEXT'),
        ]
        
        # Liste des colonnes à ajouter (HTA)
        hta_columns = [
            ('poste_hta_commune', 'TEXT'),
            ('poste_hta_code_commune', 'TEXT'),
            ('poste_hta_epci', 'TEXT'),
            ('poste_hta_code_epci', 'TEXT'),
            ('poste_hta_departement', 'TEXT'),
            ('poste_hta_code_departement', 'TEXT'),
            ('poste_hta_region', 'TEXT'),
            ('poste_hta_code_region', 'TEXT'),
        ]
        
        all_columns = bt_columns + hta_columns
        
        print(f"📊 Vérification des colonnes existantes...")
        
        # Vérifier quelles colonnes existent déjà
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'agriweb_prospects'
        """)
        existing_columns = {row[0] for row in cursor.fetchall()}
        
        added_count = 0
        skipped_count = 0
        
        for column_name, column_type in all_columns:
            if column_name in existing_columns:
                print(f"⏭️  Colonne '{column_name}' déjà existante, ignorée")
                skipped_count += 1
            else:
                print(f"➕ Ajout de la colonne '{column_name}' ({column_type})...")
                cursor.execute(
                    sql.SQL("ALTER TABLE agriweb_prospects ADD COLUMN {} {}").format(
                        sql.Identifier(column_name),
                        sql.SQL(column_type)
                    )
                )
                added_count += 1
        
        # Compter les prospects
        cursor.execute("SELECT COUNT(*) FROM agriweb_prospects")
        total_prospects = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n✅ Migration terminée avec succès!")
        print(f"   - Colonnes ajoutées: {added_count}")
        print(f"   - Colonnes ignorées (déjà présentes): {skipped_count}")
        print(f"   - Total prospects dans la base: {total_prospects}")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Erreur PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*80)
    print("🚀 MIGRATION RAILWAY - Colonnes géographiques postes BT/HTA")
    print("="*80)
    success = migrate_railway()
    sys.exit(0 if success else 1)
