#!/usr/bin/env python3
"""Test des étapes dans la base de données"""

import psycopg2
import json

DATABASE_URL = "postgresql://postgres:WbjgkcXDKvbbYJhWprDDQQobbpnggYJc@yamanote.proxy.rlwy.net:42931/railway"

def test_etapes():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Vérifier si les tables existent
    print("=== TABLES ===")
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    tables = [t[0] for t in cur.fetchall()]
    print(f"Tables: {', '.join(sorted(tables))}")
    
    if 'project_fiches' not in tables:
        print("\n⚠️ La table project_fiches n'existe pas!")
        return
    
    if 'project_etapes' not in tables:
        print("\n⚠️ La table project_etapes n'existe pas!")
        return
    
    # Vérifier les projets récents
    print("\n=== PROJETS RÉCENTS ===")
    cur.execute("SELECT id, nom_projet, prospect_id FROM project_fiches ORDER BY id DESC LIMIT 5")
    projects = cur.fetchall()
    
    if not projects:
        print("  Aucun projet trouvé!")
    
    for p in projects:
        project_id, nom_projet, prospect_id = p
        print(f"\nProjet {project_id}: {nom_projet} (prospect {prospect_id})")
        
        # Vérifier les étapes
        cur.execute("SELECT ordre, nom_etape, statut FROM project_etapes WHERE project_id = %s ORDER BY ordre", (project_id,))
        etapes = cur.fetchall()
        
        if etapes:
            for e in etapes:
                ordre, nom_etape, statut = e
                icon = "✅" if statut == "termine" else "⏳" if statut == "en_cours" else "⬜"
                print(f"  {icon} {ordre}. {nom_etape} ({statut})")
        else:
            print("  ⚠️ AUCUNE ÉTAPE TROUVÉE")
    
    # Vérifier les prospects avec calpinage
    print("\n=== PROSPECTS AVEC CALPINAGE ===")
    cur.execute("SELECT id, proprietaire_denomination, data_json FROM agriweb_prospects WHERE data_json IS NOT NULL ORDER BY id DESC LIMIT 5")
    prospects = cur.fetchall()
    
    for p in prospects:
        prospect_id, nom, data_json = p
        if data_json:
            data = data_json if isinstance(data_json, dict) else json.loads(data_json) if data_json else {}
            has_calpinage = 'calpinage' in data and data['calpinage']
            has_rapport = 'rapport' in data and data['rapport']
            print(f"  Prospect {prospect_id}: {nom}")
            print(f"    - Rapport: {'✅ Oui' if has_rapport else '❌ Non'}")
            print(f"    - Calpinage: {'✅ Oui' if has_calpinage else '❌ Non'}")
            
            # Vérifier s'il y a un projet lié
            cur.execute("SELECT id FROM project_fiches WHERE prospect_id = %s", (prospect_id,))
            project = cur.fetchone()
            print(f"    - Projet lié: {'✅ ID=' + str(project[0]) if project else '❌ Aucun'}")
    
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    test_etapes()
