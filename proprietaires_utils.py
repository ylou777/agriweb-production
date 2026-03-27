"""
Fonction pour requêter les propriétaires depuis PostgreSQL Railway
Compatible avec Railway et environnement local (via DATABASE_URL)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import re

# Configuration PostgreSQL Railway
# En production Railway, DATABASE_URL est défini automatiquement
# En local, on utilise DATABASE_PUBLIC_URL
DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_PUBLIC_URL') or \
    "postgresql://postgres:WbjgkcXDKvbbYJhWprDDQQobbpnggYJc@yamanote.proxy.rlwy.net:42931/railway"

def parse_database_url(url):
    """Parse une URL PostgreSQL"""
    pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
    match = re.match(pattern, url)
    if match:
        return {
            'user': match.group(1),
            'password': match.group(2),
            'host': match.group(3),
            'port': int(match.group(4)),
            'database': match.group(5)
        }
    return None

DB_CONFIG = parse_database_url(DATABASE_URL)

def get_proprietaires_by_parcelle(code_insee, section, numero):
    """
    Récupère les propriétaires d'une parcelle depuis PostgreSQL Railway
    
    Args:
        code_insee: Code INSEE de la commune (ex: "06088")
        section: Section cadastrale (ex: "AB")
        numero: Numéro de parcelle (ex: "0123")
    
    Returns:
        Liste de dict avec les propriétaires
    """
    if not DB_CONFIG:
        print(f"⚠️  Configuration PostgreSQL invalide: {DATABASE_URL}")
        return []
    
    try:
        conn = psycopg2.connect(**DB_CONFIG, connect_timeout=10)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Normaliser les paramètres
        section = section.upper().strip()
        numero = numero.lstrip('0').zfill(4)  # Normaliser 123 → 0123
        
        # Requête (syntaxe PostgreSQL avec %s au lieu de ?)
        cur.execute("""
            SELECT DISTINCT
                siren,
                forme_juridique,
                denomination,
                SUM(contenance) as surface_totale_m2
            FROM proprietaires_parcelles
            WHERE code_insee = %s
              AND UPPER(section) = %s
              AND numero = %s
              AND denomination IS NOT NULL
            GROUP BY siren, forme_juridique, denomination
            ORDER BY surface_totale_m2 DESC
        """, (code_insee, section, numero))
        
        rows = cur.fetchall()
        conn.close()
        
        # Convertir en liste de dict
        proprietaires = []
        for row in rows:
            proprietaires.append({
                'siren': row['siren'],
                'forme_juridique': row['forme_juridique'],
                'denomination': row['denomination'],
                'surface_m2': row['surface_totale_m2'],
                'surface_ha': round(row['surface_totale_m2'] / 10000, 2) if row['surface_totale_m2'] else 0
            })
        
        return proprietaires
        
    except Exception as e:
        print(f"❌ Erreur get_proprietaires: {e}")
        return []


def get_proprietaires_by_commune(code_insee, limit=100):
    """
    Récupère les principaux propriétaires d'une commune
    
    Args:
        code_insee: Code INSEE de la commune
        limit: Nombre max de résultats
    
    Returns:
        Liste de dict avec les propriétaires
    """
    if not DB_CONFIG:
        return []
    
    try:
        conn = psycopg2.connect(**DB_CONFIG, connect_timeout=10)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                siren,
                forme_juridique,
                denomination,
                COUNT(DISTINCT section || '-' || numero) as nb_parcelles,
                SUM(contenance) as surface_totale_m2
            FROM proprietaires_parcelles
            WHERE code_insee = %s
              AND denomination IS NOT NULL
              AND siren IS NOT NULL
            GROUP BY siren, forme_juridique, denomination
            HAVING COUNT(DISTINCT section || '-' || numero) >= 3
            ORDER BY surface_totale_m2 DESC
            LIMIT %s
        """, (code_insee, limit))
        
        rows = cur.fetchall()
        conn.close()
        
        proprietaires = []
        for row in rows:
            proprietaires.append({
                'siren': row['siren'],
                'forme_juridique': row['forme_juridique'],
                'denomination': row['denomination'],
                'nb_parcelles': row['nb_parcelles'],
                'surface_m2': row['surface_totale_m2'],
                'surface_ha': round(row['surface_totale_m2'] / 10000, 2)
            })
        
        return proprietaires
        
    except Exception as e:
        print(f"❌ Erreur get_proprietaires_commune: {e}")
        return []


def get_parcelles_by_siren(siren, limit=500):
    """
    Récupère toutes les parcelles d'un propriétaire par SIREN sur toute la France.

    Args:
        siren: Numéro SIREN (9 chiffres)
        limit: Nombre max de parcelles à retourner

    Returns:
        Liste de dict {code_insee, section, numero, contenance, denomination, forme_juridique}
    """
    if not DB_CONFIG:
        return []

    try:
        conn = psycopg2.connect(**DB_CONFIG, connect_timeout=10)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                code_insee,
                section,
                numero,
                contenance,
                denomination,
                forme_juridique
            FROM proprietaires_parcelles
            WHERE siren = %s
              AND denomination IS NOT NULL
            ORDER BY code_insee, section, numero
            LIMIT %s
        """, (siren, limit))

        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    except Exception as e:
        print(f"❌ Erreur get_parcelles_by_siren: {e}")
        return []


# Exemple d'utilisation
if __name__ == "__main__":
    # Test avec une parcelle
    print("Test 1: Propriétaires de la parcelle 01001-A-0061")
    proprios = get_proprietaires_by_parcelle("01001", "A", "0061")
    print(f"Trouvé {len(proprios)} propriétaire(s):")
    for p in proprios:
        print(f"  - {p['denomination']} (SIREN: {p['siren']}) - {p['surface_ha']} ha")
    
    print("\nTest 2: Principaux propriétaires de la commune 01001")
    proprios_commune = get_proprietaires_by_commune("01001", limit=10)
    print(f"Top 10 propriétaires:")
    for p in proprios_commune:
        print(f"  - {p['denomination']}: {p['nb_parcelles']} parcelles, {p['surface_ha']} ha")
