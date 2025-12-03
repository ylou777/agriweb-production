#!/usr/bin/env python3
"""
Script de déploiement du trigger d'enrichissement automatique sur Railway (sans emojis)
"""
import os
import sys
import psycopg2

# Force UTF-8 pour Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def deploy_trigger():
    """Déploie le trigger d'enrichissement sur Railway PostgreSQL"""
    
    database_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('PGDATABASE_URL') or os.environ.get('DATABASE_URL')
    
    if database_url and 'railway.internal' in database_url:
        print("[!] URL interne Railway détectée (non accessible)")
        print("[i] Essayez avec une URL publique: railway run python deploy_trigger_simple.py")
        return False
    
    if not database_url:
        print("[X] DATABASE_URL non défini")
        print("[i] Lancez: railway run python deploy_trigger_simple.py")
        return False
    
    print("[*] Connexion à Railway PostgreSQL...")
    print(f"    URL: {database_url[:30]}...{database_url[-20:]}")
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Lire le fichier SQL
        print("\n[*] Lecture de create_auto_enrich_trigger.sql...")
        with open('create_auto_enrich_trigger.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Exécuter le SQL
        print("[*] Exécution du script SQL...")
        cursor.execute(sql_content)
        conn.commit()
        print("[OK] Script SQL exécuté avec succès!")
        
        # Vérifier les triggers
        print("\n[*] Vérification des triggers créés...")
        cursor.execute("""
            SELECT trigger_name, event_manipulation, action_timing
            FROM information_schema.triggers
            WHERE event_object_table = 'agriweb_prospects'
            ORDER BY trigger_name;
        """)
        
        triggers = cursor.fetchall()
        if triggers:
            print(f"[OK] {len(triggers)} trigger(s) actif(s):")
            for trigger in triggers:
                print(f"     - {trigger[0]}: {trigger[2]} {trigger[1]}")
        else:
            print("[!] Aucun trigger trouvé")
        
        # Vérifier les colonnes
        print("\n[*] Vérification des colonnes proprietaire_*...")
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'agriweb_prospects'
              AND column_name LIKE 'proprietaire_%'
            ORDER BY column_name;
        """)
        
        columns = cursor.fetchall()
        if columns:
            print(f"[OK] {len(columns)} colonne(s) créée(s):")
            for col in columns:
                print(f"     - {col[0]} ({col[1]})")
        else:
            print("[!] Aucune colonne proprietaire_* trouvée")
        
        # Test d'insertion
        print("\n[*] Test d'insertion avec enrichissement...")
        from datetime import datetime
        
        cursor.execute("""
            INSERT INTO agriweb_prospects 
            (nom_prospect, commune, statut, date_creation, parcelles_cadastrales)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, proprietaire_siren, proprietaire_denomination;
        """, (
            f'Test Auto-Enrich {datetime.now()}',
            'Toulouse',
            'Nouveau',
            datetime.now(),
            '[{"commune": "", "numero": "0123", "section": "AB", "ref": "31555-AB-0123"}]'
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        if result:
            test_id, siren, denom = result
            print(f"[OK] Test d'insertion réussi:")
            print(f"     ID: {test_id}")
            print(f"     SIREN: {siren or 'Non enrichi'}")
            print(f"     Denomination: {denom or 'Non enrichi'}")
            
            if siren:
                print("\n[SUCCESS] ENRICHISSEMENT AUTOMATIQUE FONCTIONNE!")
            else:
                print("\n[!] Prospect créé mais non enrichi")
        
        # Stats
        print("\n[*] Statistiques actuelles:")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(proprietaire_siren) as avec_siren,
                COUNT(CASE WHEN parcelles_cadastrales IS NOT NULL AND parcelles_cadastrales != '' THEN 1 END) as avec_parcelles
            FROM agriweb_prospects;
        """)
        
        stats = cursor.fetchone()
        if stats:
            total, avec_siren, avec_parcelles = stats
            pct = (avec_siren / total * 100) if total > 0 else 0
            print(f"     Total prospects: {total}")
            print(f"     Avec SIREN: {avec_siren} ({pct:.1f}%)")
            print(f"     Avec parcelles: {avec_parcelles}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("[SUCCESS] DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Erreur lors du déploiement:")
        print(f"        {type(e).__name__}: {str(e)}")
        return False

if __name__ == '__main__':
    success = deploy_trigger()
    sys.exit(0 if success else 1)
