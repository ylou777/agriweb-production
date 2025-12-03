#!/usr/bin/env python3
"""
Script de migration pour ajouter les colonnes manquantes dans PostgreSQL Railway
"""
import os
import sys

# Importer l'adaptateur de base de données
import database_adapter

def migrate_columns():
    """Ajoute les colonnes manquantes à la table agriweb_prospects"""
    
    if not database_adapter.IS_RAILWAY:
        print("❌ Ce script est uniquement pour Railway (PostgreSQL)")
        print("DATABASE_URL non détectée")
        sys.exit(1)
    
    print("🔧 Début de la migration des colonnes...")
    
    columns_to_add = [
        ('poste_bt_nom', 'TEXT'),
        ('poste_bt_puissance', 'REAL'),
        ('poste_hta_nom', 'TEXT'),
        ('nom_prospect', 'TEXT'),
        ('representant_nom', 'TEXT'),
        ('representant_tel', 'TEXT'),
        ('representant_email', 'TEXT'),
        ('siren', 'TEXT'),
        ('dirigeant_nom', 'TEXT'),
        ('dirigeant_email', 'TEXT'),
        ('dirigeant_tel', 'TEXT'),
        ('siret', 'TEXT')
    ]
    
    with database_adapter.get_db_connection() as conn:
        cursor = conn.cursor()
        
        for col_name, col_type in columns_to_add:
            try:
                sql = f"ALTER TABLE agriweb_prospects ADD COLUMN {col_name} {col_type}"
                print(f"Ajout de la colonne {col_name}...")
                cursor.execute(sql)
                conn.commit()
                print(f"✅ Colonne {col_name} ajoutée avec succès")
            except Exception as e:
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg:
                    print(f"⚠️  Colonne {col_name} existe déjà (ignorée)")
                else:
                    print(f"❌ Erreur lors de l'ajout de {col_name}: {e}")
                    # On continue quand même avec les autres colonnes
        
        cursor.close()
    
    print("✅ Migration terminée avec succès!")
    print("\nVérification des colonnes...")
    
    # Vérifier que les colonnes existent maintenant
    with database_adapter.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'agriweb_prospects'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        cursor.close()
        
        print(f"\nColonnes présentes dans agriweb_prospects ({len(columns)}) :")
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")

if __name__ == "__main__":
    migrate_columns()
