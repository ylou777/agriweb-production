"""
Script pour enrichir les prospects CRM avec les données des propriétaires
Croise les données de parcelles_cadastrales et communes avec la base proprietaires_parcelles
"""

import os
import sys
import re
from datetime import datetime
import sqlite3
import psycopg2
from urllib.parse import urlparse

# Configuration de la connexion Railway
DATABASE_URL = os.getenv('DATABASE_PUBLIC_URL', 
                         'postgresql://postgres:WbjgkcXDKvbbYJhWprDDQQobbpnggYJc@yamanote.proxy.rlwy.net:42931/railway')

def get_raw_db_connection():
    """
    Crée une connexion directe à la base sans context manager
    Returns:
        conn: Connexion SQLite ou PostgreSQL brute
    """
    database_url = os.getenv('DATABASE_URL') or os.getenv('DATABASE_PUBLIC_URL')
    
    if database_url and 'postgresql' in database_url:
        print("💾 [DATABASE] Mode PostgreSQL Railway")
        return psycopg2.connect(database_url)
    else:
        print("💾 [DATABASE] Mode SQLite (Local)")
        db_path = os.getenv('DATABASE_PATH', 'agriweb.db')
        return sqlite3.connect(db_path)

def parse_parcelle_cadastrale(parcelle_str):
    """
    Parse une référence cadastrale pour extraire code_commune, section, numero
    Formats possibles:
    - "01001-A-0061" (standard)
    - "01001 A 0061" (avec espaces)
    - "A 0061" (sans code commune)
    - "A0061" (compact)
    
    Returns:
        dict: {'code_commune': '01001', 'section': 'A', 'numero': '0061'}
    """
    if not parcelle_str or parcelle_str.strip() == '':
        return None
    
    # Nettoyer la chaîne
    parcelle_clean = parcelle_str.strip().upper()
    
    # Pattern 1: "01001-A-0061" ou "01001 A 0061"
    match = re.match(r'(\d{5})[-\s]+([A-Z]{1,3})[-\s]+(\d{4})', parcelle_clean)
    if match:
        return {
            'code_commune': match.group(1),
            'section': match.group(2),
            'numero': match.group(3).zfill(4)  # Padding avec zéros
        }
    
    # Pattern 2: "A 0061" ou "A0061" (sans code commune)
    match = re.match(r'([A-Z]{1,3})[-\s]*(\d{1,4})', parcelle_clean)
    if match:
        return {
            'code_commune': None,  # À compléter avec le code commune du prospect
            'section': match.group(1),
            'numero': match.group(2).zfill(4)
        }
    
    print(f"⚠️ [PARSE] Format non reconnu: {parcelle_str}")
    return None

def get_code_insee_from_commune(commune_name):
    """
    Récupère le code INSEE d'une commune depuis son nom
    Utilise l'API Geo.gouv.fr
    """
    import requests
    
    try:
        url = f"https://geo.api.gouv.fr/communes"
        params = {
            'nom': commune_name,
            'fields': 'code,nom',
            'limit': 1
        }
        
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                code_insee = data[0].get('code')
                nom = data[0].get('nom')
                print(f"✅ [GEO] {commune_name} -> {code_insee} ({nom})")
                return code_insee
        
        print(f"⚠️ [GEO] Commune non trouvée: {commune_name}")
        return None
        
    except Exception as e:
        print(f"❌ [GEO] Erreur API: {e}")
        return None

def get_proprietaire_from_parcelle(code_commune, section, numero, cursor):
    """
    Interroge la table proprietaires_parcelles pour trouver le propriétaire
    
    Args:
        code_commune: Code INSEE (ex: '01001')
        section: Section cadastrale (ex: 'A')
        numero: Numéro de parcelle (ex: '0061')
        cursor: Curseur PostgreSQL/SQLite
    
    Returns:
        dict: Données du propriétaire ou None
    """
    try:
        query = """
            SELECT DISTINCT 
                siren, 
                denomination, 
                forme_juridique,
                adresse_proprietaire,
                code_postal,
                ville
            FROM proprietaires_parcelles
            WHERE code_commune = ? 
              AND section = ? 
              AND numero = ?
            LIMIT 1
        """
        
        cursor.execute(query, (code_commune, section, numero))
        result = cursor.fetchone()
        
        if result:
            return {
                'siren': result[0],
                'denomination': result[1],
                'forme_juridique': result[2],
                'adresse_proprietaire': result[3],
                'code_postal': result[4],
                'ville': result[5]
            }
        
        return None
        
    except Exception as e:
        print(f"❌ [DB] Erreur requête proprietaires: {e}")
        return None

def add_proprietaire_columns():
    """
    Ajoute les colonnes proprietaire à la table agriweb_prospects si elles n'existent pas
    Compatible SQLite et PostgreSQL
    """
    print("\n🔧 [MIGRATION] Ajout des colonnes proprietaire...")
    
    columns_to_add = [
        ("proprietaire_siren", "VARCHAR(9)"),
        ("proprietaire_denomination", "TEXT"),
        ("proprietaire_forme_juridique", "VARCHAR(100)"),
        ("proprietaire_adresse", "TEXT"),
        ("proprietaire_code_postal", "VARCHAR(5)"),
        ("proprietaire_ville", "TEXT"),
        ("proprietaire_enrichi_date", "TIMESTAMP")
    ]
    
    # Détecter le type de base de données
    database_url = os.getenv('DATABASE_URL') or os.getenv('DATABASE_PUBLIC_URL')
    is_postgres = database_url and 'postgresql' in database_url
    
    conn = None
    cursor = None
    
    try:
        # Connexion directe sans context manager
        conn = get_raw_db_connection()
        cursor = conn.cursor()
        
        for column_name, column_type in columns_to_add:
            try:
                if is_postgres:
                    # PostgreSQL supporte IF NOT EXISTS
                    alter_query = f"""
                        ALTER TABLE agriweb_prospects 
                        ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                    """
                else:
                    # SQLite: vérifier si la colonne existe d'abord
                    cursor.execute("PRAGMA table_info(agriweb_prospects)")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    if column_name not in columns:
                        alter_query = f"""
                            ALTER TABLE agriweb_prospects 
                            ADD COLUMN {column_name} {column_type}
                        """
                    else:
                        print(f"  ⏭️ Colonne {column_name} existe déjà")
                        continue
                
                cursor.execute(alter_query)
                print(f"  ✅ Colonne {column_name} ajoutée")
            except Exception as e:
                print(f"  ⚠️ Colonne {column_name}: {e}")
        
        conn.commit()
        print("✅ [MIGRATION] Migration terminée\n")
        
    except Exception as e:
        print(f"❌ [MIGRATION] Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def enrich_prospects_with_proprietaires(limit=None, dry_run=False):
    """
    Enrichit les prospects CRM avec les données des propriétaires
    
    Args:
        limit: Limite de prospects à traiter (None = tous)
        dry_run: Si True, simule sans modifier la base
    """
    print("\n🚀 [ENRICHISSEMENT] Démarrage de l'enrichissement CRM...\n")
    print(f"Mode: {'DRY RUN (simulation)' if dry_run else 'PRODUCTION (modification réelle)'}")
    print(f"Limite: {limit if limit else 'Tous les prospects'}\n")
    
    conn = None
    cursor = None
    
    try:
        # Connexion directe sans context manager
        conn = get_raw_db_connection()
        cursor = conn.cursor()
        
        # Récupérer les prospects avec parcelles cadastrales
        query = """
            SELECT id, commune, parcelles_cadastrales, nom_prospect
            FROM agriweb_prospects
            WHERE parcelles_cadastrales IS NOT NULL 
              AND parcelles_cadastrales != ''
              AND (proprietaire_siren IS NULL OR proprietaire_denomination IS NULL)
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        prospects = cursor.fetchall()
        
        total = len(prospects)
        print(f"📊 [STATS] {total} prospects à enrichir\n")
        
        if total == 0:
            print("✅ Tous les prospects sont déjà enrichis ou n'ont pas de parcelles")
            return
        
        # Statistiques
        enriched = 0
        failed = 0
        no_parcelle = 0
        no_proprietaire = 0
        
        for i, prospect in enumerate(prospects, 1):
            prospect_id, commune, parcelles_cadastrales, nom_prospect = prospect
            
            print(f"\n[{i}/{total}] Prospect #{prospect_id}: {nom_prospect or 'Sans nom'}")
            print(f"  Commune: {commune}")
            print(f"  Parcelles: {parcelles_cadastrales}")
            
            # Parser les parcelles (peut être une liste séparée par des virgules)
            parcelle_list = [p.strip() for p in parcelles_cadastrales.split(',')]
            
            proprietaire_found = None
            
            for parcelle_str in parcelle_list:
                parcelle = parse_parcelle_cadastrale(parcelle_str)
                
                if not parcelle:
                    print(f"  ⚠️ Parcelle non parsable: {parcelle_str}")
                    no_parcelle += 1
                    continue
                
                # Compléter le code commune si manquant
                if not parcelle['code_commune']:
                    code_insee = get_code_insee_from_commune(commune)
                    if code_insee:
                        parcelle['code_commune'] = code_insee
                    else:
                        print(f"  ⚠️ Code INSEE non trouvé pour: {commune}")
                        no_parcelle += 1
                        continue
                
                # Rechercher le propriétaire
                proprietaire = get_proprietaire_from_parcelle(
                    parcelle['code_commune'],
                    parcelle['section'],
                    parcelle['numero'],
                    cursor  # Passer le curseur au lieu de conn
                )
                
                if proprietaire:
                    proprietaire_found = proprietaire
                    print(f"  ✅ Propriétaire trouvé: {proprietaire['denomination']} (SIREN: {proprietaire['siren']})")
                    break  # Prendre le premier propriétaire trouvé
            
            if proprietaire_found:
                if not dry_run:
                    # Mettre à jour le prospect avec les données du propriétaire
                    update_query = """
                        UPDATE agriweb_prospects
                        SET proprietaire_siren = %s,
                            proprietaire_denomination = %s,
                            proprietaire_forme_juridique = %s,
                            proprietaire_adresse = %s,
                            proprietaire_code_postal = %s,
                            proprietaire_ville = %s,
                            proprietaire_enrichi_date = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """
                    
                    cursor.execute(update_query, (
                        proprietaire_found['siren'],
                        proprietaire_found['denomination'],
                        proprietaire_found['forme_juridique'],
                        proprietaire_found['adresse_proprietaire'],
                        proprietaire_found['code_postal'],
                        proprietaire_found['ville'],
                        prospect_id
                    ))
                    
                    conn.commit()
                    print(f"  💾 Prospect mis à jour")
                else:
                    print(f"  [DRY RUN] Prospect serait mis à jour")
                
                enriched += 1
            else:
                print(f"  ❌ Aucun propriétaire trouvé")
                no_proprietaire += 1
        
            # Résumé final
            print("\n" + "="*60)
            print("📊 RÉSUMÉ DE L'ENRICHISSEMENT")
            print("="*60)
            print(f"Total prospects traités: {total}")
            print(f"✅ Enrichis avec succès: {enriched}")
            print(f"❌ Échecs (parcelle non parsable): {no_parcelle}")
            print(f"❌ Échecs (propriétaire non trouvé): {no_proprietaire}")
            print(f"📈 Taux de succès: {100*enriched/total:.1f}%")
            print("="*60)
        
    except Exception as e:
        print(f"\n❌ [ERREUR] Erreur globale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def test_enrichissement():
    """
    Test rapide sur 5 prospects pour vérifier le fonctionnement
    """
    print("\n🧪 [TEST] Mode test sur 5 prospects")
    enrich_prospects_with_proprietaires(limit=5, dry_run=True)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrichissement CRM avec données propriétaires')
    parser.add_argument('--test', action='store_true', help='Mode test (5 prospects, dry run)')
    parser.add_argument('--dry-run', action='store_true', help='Simulation sans modification')
    parser.add_argument('--limit', type=int, help='Limite de prospects à traiter')
    parser.add_argument('--add-columns', action='store_true', help='Ajouter les colonnes proprietaire')
    parser.add_argument('--enrich', action='store_true', help='Lancer l\'enrichissement')
    
    args = parser.parse_args()
    
    # Ajouter les colonnes si demandé
    if args.add_columns:
        add_proprietaire_columns()
        # Ne pas continuer après --add-columns seul
        if not args.enrich and not args.test:
            sys.exit(0)
    
    # Mode test
    if args.test:
        test_enrichissement()
    # Mode enrichissement
    elif args.enrich or (not args.add_columns and not args.test):
        # Mode production/simulation (par défaut si aucun flag)
        enrich_prospects_with_proprietaires(
            limit=args.limit,
            dry_run=args.dry_run
        )
