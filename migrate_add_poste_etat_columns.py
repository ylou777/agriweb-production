"""
Migration: Ajout des colonnes poste_bt_etat et poste_hta_etat
"""

import sqlite3
import os

# Chercher dans tous les emplacements possibles
DB_PATHS = [
    "agriweb_crm.db",
    "instance/agriweb_crm.db",
    "../agriweb_crm.db",
    "../instance/agriweb_crm.db"
]

def find_database():
    """Trouve la base de données dans les emplacements possibles"""
    for path in DB_PATHS:
        if os.path.exists(path):
            return path
    return None

def check_column_exists(cursor, table_name, column_name):
    """Vérifie si une colonne existe dans une table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def migrate_database():
    """Ajoute les colonnes manquantes"""
    print("🔄 MIGRATION: Ajout colonnes poste_bt_etat et poste_hta_etat")
    print("=" * 60)
    
    DB_PATH = find_database()
    if not DB_PATH:
        print(f"❌ Base de données non trouvée dans:")
        for path in DB_PATHS:
            print(f"   - {path}")
        return False
    
    print(f"📍 Base trouvée: {DB_PATH}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Vérifier et ajouter poste_bt_etat
        if not check_column_exists(cursor, 'agriweb_prospects', 'poste_bt_etat'):
            print("➕ Ajout colonne: poste_bt_etat")
            cursor.execute("ALTER TABLE agriweb_prospects ADD COLUMN poste_bt_etat TEXT")
            print("   ✅ Colonne poste_bt_etat ajoutée")
        else:
            print("   ℹ️  Colonne poste_bt_etat existe déjà")
        
        # Vérifier et ajouter poste_hta_etat
        if not check_column_exists(cursor, 'agriweb_prospects', 'poste_hta_etat'):
            print("➕ Ajout colonne: poste_hta_etat")
            cursor.execute("ALTER TABLE agriweb_prospects ADD COLUMN poste_hta_etat TEXT")
            print("   ✅ Colonne poste_hta_etat ajoutée")
        else:
            print("   ℹ️  Colonne poste_hta_etat existe déjà")
        
        conn.commit()
        
        # Vérifier les colonnes finales
        cursor.execute("PRAGMA table_info(agriweb_prospects)")
        columns = cursor.fetchall()
        
        print("\n📋 Colonnes de la table agriweb_prospects:")
        poste_columns = [col for col in columns if 'poste' in col[1]]
        for col in poste_columns:
            print(f"   - {col[1]} ({col[2]})")
        
        conn.close()
        
        print("\n✅ Migration terminée avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    migrate_database()
