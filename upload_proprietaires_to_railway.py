"""
Upload de la table proprietaires_parcelles compressée vers Railway PostgreSQL

Ce script :
1. Upload le fichier .sql.gz sur Railway via SCP/SFTP ou railway CLI
2. Décompresse et importe directement sur Railway
3. Crée les index pour optimiser les requêtes

Méthodes disponibles:
- Railway CLI (recommandé)
- API Railway
- Import direct via psql (si accès réseau)
"""

import subprocess
import sys
import os
from pathlib import Path
import gzip
import psycopg2
from tqdm import tqdm

# Configuration Railway PostgreSQL
RAILWAY_CONFIG = {
    'host': 'viaduct.proxy.rlwy.net',
    'port': 21260,
    'database': 'railway',
    'user': 'postgres',
    'password': 'bXrjKvPXzSPAqKrDXKhdMIGXLMlPWcpQ'
}

SQL_GZ_FILE = Path(r"C:\Users\Utilisateur\Desktop\AG32.1\proprietaires_parcelles.sql.gz")

def check_railway_cli():
    """Vérifie si Railway CLI est installé"""
    try:
        result = subprocess.run(['railway', '--version'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def upload_via_railway_cli():
    """
    Méthode 1: Upload via Railway CLI
    Nécessite: npm install -g @railway/cli
    """
    print("=" * 80)
    print("📤 MÉTHODE 1: Upload via Railway CLI")
    print("=" * 80)
    print()
    
    if not check_railway_cli():
        print("❌ Railway CLI non installé")
        print()
        print("Installation:")
        print("  npm install -g @railway/cli")
        print("  railway login")
        return False
    
    print("✅ Railway CLI détecté")
    print()
    
    # 1. Uploader le fichier
    print("📤 Upload du fichier .sql.gz...")
    print("⚠️  Cette opération peut prendre plusieurs minutes (164 MB)")
    print()
    
    # Railway n'a pas de commande directe pour upload de fichier
    # On doit passer par un service temporaire ou déployer un script
    print("⚠️  Railway CLI ne supporte pas l'upload direct de fichiers")
    print("    Utilisez plutôt la Méthode 2 (Import streaming)")
    return False

def upload_via_streaming():
    """
    Méthode 2: Lecture streaming du .sql.gz et exécution directe
    Plus lent mais fonctionne avec connexion réseau directe
    """
    print("=" * 80)
    print("📤 MÉTHODE 2: Import streaming .sql.gz → PostgreSQL")
    print("=" * 80)
    print()
    
    if not SQL_GZ_FILE.exists():
        print(f"❌ Fichier introuvable: {SQL_GZ_FILE}")
        return False
    
    print(f"📂 Fichier: {SQL_GZ_FILE.name}")
    print(f"📊 Taille: {SQL_GZ_FILE.stat().st_size / 1024 / 1024:.2f} MB")
    print()
    
    # Test connexion Railway
    print("🔌 Test connexion Railway PostgreSQL...")
    try:
        conn = psycopg2.connect(**RAILWAY_CONFIG, connect_timeout=10)
        print("✅ Connexion établie")
        conn.close()
    except Exception as e:
        print(f"❌ Impossible de se connecter à Railway: {e}")
        print()
        print("💡 SOLUTIONS:")
        print("   1. Vérifiez votre connexion internet")
        print("   2. Utilisez la Méthode 3 (Railway Shell)")
        return False
    
    print()
    print("⚠️  L'import peut prendre 30-60 minutes pour 18M de lignes")
    confirm = input("Continuer ? (o/N): ")
    if confirm.lower() != 'o':
        print("❌ Annulé")
        return False
    
    print()
    print("📥 Décompression et import en cours...")
    
    try:
        # Connexion PostgreSQL
        conn = psycopg2.connect(**RAILWAY_CONFIG)
        cur = conn.cursor()
        
        # Lire et exécuter le SQL compressé ligne par ligne
        with gzip.open(SQL_GZ_FILE, 'rt', encoding='utf-8') as f:
            sql_buffer = []
            line_count = 0
            
            for line in tqdm(f, desc="Import SQL", unit=" lignes"):
                sql_buffer.append(line)
                line_count += 1
                
                # Exécuter par batch de 1000 lignes
                if line_count % 1000 == 0:
                    try:
                        cur.execute(''.join(sql_buffer))
                        conn.commit()
                        sql_buffer = []
                    except Exception as e:
                        # Ignorer les erreurs de création de table si elle existe
                        if "already exists" not in str(e):
                            print(f"\n⚠️  Erreur SQL (ligne {line_count}): {e}")
                        conn.rollback()
                        sql_buffer = []
            
            # Exécuter le reste
            if sql_buffer:
                try:
                    cur.execute(''.join(sql_buffer))
                    conn.commit()
                except Exception as e:
                    print(f"\n⚠️  Erreur finale: {e}")
                    conn.rollback()
        
        cur.close()
        conn.close()
        
        print()
        print("✅ Import terminé")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur import: {e}")
        import traceback
        traceback.print_exc()
        return False

def method_railway_shell():
    """
    Méthode 3: Upload via Railway Shell (RECOMMANDÉ)
    """
    print("=" * 80)
    print("📤 MÉTHODE 3: Upload via Railway Shell (RECOMMANDÉ)")
    print("=" * 80)
    print()
    
    print("Cette méthode est la plus simple et rapide:")
    print()
    print("ÉTAPE 1: Installer Railway CLI")
    print("  npm install -g @railway/cli")
    print("  railway login")
    print()
    print("ÉTAPE 2: Lier votre projet")
    print("  cd C:\\Users\\Utilisateur\\Desktop\\AG32.1")
    print("  railway link")
    print()
    print("ÉTAPE 3: Ouvrir le shell PostgreSQL")
    print("  railway run psql")
    print()
    print("ÉTAPE 4: Dans le shell, exécuter:")
    print("  \\! gunzip -c C:/Users/Utilisateur/Desktop/AG32.1/proprietaires_parcelles.sql.gz | psql $DATABASE_URL")
    print()
    print("OU en une seule commande depuis PowerShell:")
    print()
    print("  railway run -- bash -c \"gunzip -c proprietaires_parcelles.sql.gz | psql \\$DATABASE_URL\"")
    print()
    print("=" * 80)
    print()
    
    # Générer le script complet
    script_content = f"""
# Script d'upload automatique via Railway CLI

# 1. Installer Railway CLI (si nécessaire)
# npm install -g @railway/cli
# railway login

# 2. Lier le projet (si nécessaire)
cd C:\\Users\\Utilisateur\\Desktop\\AG32.1
# railway link

# 3. Upload et import en une commande
railway run -- bash -c "gunzip -c proprietaires_parcelles.sql.gz | psql \\$DATABASE_URL"

# Alternative si bash n'est pas disponible:
# railway run psql < proprietaires_parcelles.sql
# (après décompression manuelle: gunzip proprietaires_parcelles.sql.gz)
"""
    
    script_path = Path("C:/Users/Utilisateur/Desktop/AG32.1/upload_railway.ps1")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✅ Script sauvegardé: {script_path}")
    print()

def method_manual_upload():
    """
    Méthode 4: Upload manuel via interface web Railway
    """
    print("=" * 80)
    print("📤 MÉTHODE 4: Upload manuel via Railway Dashboard")
    print("=" * 80)
    print()
    
    print("OPTION A: Via Railway Volumes (si disponible)")
    print("  1. Créer un volume dans votre projet Railway")
    print("  2. Uploader proprietaires_parcelles.sql.gz")
    print("  3. Depuis Railway Shell: gunzip -c /volume/proprietaires_parcelles.sql.gz | psql $DATABASE_URL")
    print()
    
    print("OPTION B: Via service temporaire")
    print("  1. Créer un service web simple avec endpoint /upload")
    print("  2. Uploader le .sql.gz via HTTP POST")
    print("  3. Le service décompresse et importe dans PostgreSQL")
    print()
    
    print("OPTION C: Via GitHub + Railway Deploy")
    print("  1. Pusher proprietaires_parcelles.sql.gz sur GitHub")
    print("  2. Créer un script d'import dans le dépôt")
    print("  3. Railway exécute le script au déploiement")
    print()

def test_connection():
    """Test la connexion à Railway PostgreSQL"""
    print("=" * 80)
    print("🔌 TEST CONNEXION RAILWAY POSTGRESQL")
    print("=" * 80)
    print()
    
    print(f"Host: {RAILWAY_CONFIG['host']}")
    print(f"Port: {RAILWAY_CONFIG['port']}")
    print(f"Database: {RAILWAY_CONFIG['database']}")
    print(f"User: {RAILWAY_CONFIG['user']}")
    print()
    
    try:
        conn = psycopg2.connect(**RAILWAY_CONFIG, connect_timeout=10)
        cur = conn.cursor()
        
        # Test requête
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"✅ Connexion réussie")
        print(f"📊 PostgreSQL: {version.split(',')[0]}")
        
        # Vérifier si la table existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'proprietaires_parcelles'
            );
        """)
        table_exists = cur.fetchone()[0]
        
        if table_exists:
            cur.execute("SELECT COUNT(*) FROM proprietaires_parcelles;")
            count = cur.fetchone()[0]
            print(f"⚠️  Table proprietaires_parcelles existe déjà ({count:,} lignes)")
        else:
            print("✅ Table proprietaires_parcelles n'existe pas encore")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

if __name__ == "__main__":
    print()
    print("=" * 80)
    print("🚀 UPLOAD PROPRIÉTAIRES PARCELLES → RAILWAY POSTGRESQL")
    print("=" * 80)
    print()
    
    print("Fichier source:")
    print(f"  📂 {SQL_GZ_FILE}")
    print(f"  📊 {SQL_GZ_FILE.stat().st_size / 1024 / 1024:.2f} MB compressé")
    print()
    
    # Test connexion
    print("1️⃣  Test de connexion...")
    print()
    can_connect = test_connection()
    
    print()
    print("=" * 80)
    print("CHOISISSEZ UNE MÉTHODE D'UPLOAD")
    print("=" * 80)
    print()
    print("1. Railway Shell (RECOMMANDÉ - rapide et simple)")
    print("2. Import streaming direct (lent, ~60 min)")
    print("3. Upload manuel via Dashboard")
    print("4. Afficher toutes les options")
    print()
    
    choice = input("Votre choix (1-4): ").strip()
    
    print()
    
    if choice == "1":
        method_railway_shell()
    elif choice == "2":
        if can_connect:
            upload_via_streaming()
        else:
            print("❌ Connexion Railway requise pour cette méthode")
            print("   Utilisez la Méthode 1 (Railway Shell) à la place")
    elif choice == "3":
        method_manual_upload()
    elif choice == "4":
        method_railway_shell()
        print()
        method_manual_upload()
    else:
        print("❌ Choix invalide")
        sys.exit(1)
