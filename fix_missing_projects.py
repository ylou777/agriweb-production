#!/usr/bin/env python3
"""Créer les projets et étapes manquants pour les prospects avec rapport/calpinage"""

import psycopg2
import json

DATABASE_URL = "postgresql://postgres:WbjgkcXDKvbbYJhWprDDQQobbpnggYJc@yamanote.proxy.rlwy.net:42931/railway"

def fix_missing_projects():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Trouver les prospects avec rapport ou calpinage mais sans projet
    print("=== RECHERCHE DES PROSPECTS SANS PROJET ===")
    cur.execute("""
        SELECT p.id, p.proprietaire_denomination, p.commune, p.data_json
        FROM agriweb_prospects p
        LEFT JOIN project_fiches pf ON pf.prospect_id = p.id
        WHERE p.data_json IS NOT NULL 
        AND pf.id IS NULL
    """)
    prospects = cur.fetchall()
    
    print(f"Trouvé {len(prospects)} prospects sans projet")
    
    etapes_autoconso = [
        ('Rapport de recherche AgriWeb', 1),
        ('Étude d\'adresse & visite technique', 2),
        ('Calepinage', 3),
        ('Étude d\'autoconsommation', 4),
        ('Devis commercial', 5),
        ('Signature & Facture', 6),
        ('Déclaration Préalable de Travaux (DP)', 7),
        ('Déclaration de Raccordement (DDR)', 8),
        ('Installation & DOE', 9),
        ('Consuel', 10),
        ('Mise en service & Maintenance', 11)
    ]
    
    for p in prospects:
        prospect_id, nom, commune, data_json = p
        
        if not data_json:
            continue
            
        data = data_json if isinstance(data_json, dict) else json.loads(data_json)
        has_rapport = 'rapport' in data and data['rapport']
        has_calpinage = 'calpinage' in data and data['calpinage']
        
        if not has_rapport and not has_calpinage:
            continue
            
        print(f"\n📌 Prospect {prospect_id}: {nom}")
        print(f"   Rapport: {'✅' if has_rapport else '❌'} | Calpinage: {'✅' if has_calpinage else '❌'}")
        
        # Créer le projet
        cur.execute("""
            INSERT INTO project_fiches (prospect_id, nom_projet, commune, statut_projet, data_json)
            VALUES (%s, %s, %s, 'etude', %s)
            RETURNING id
        """, (prospect_id, f"Projet {nom or commune or 'Nouveau'}", commune, json.dumps(data)))
        
        result = cur.fetchone()
        if result:
            project_id = result[0]
            print(f"   ✅ Projet {project_id} créé")
            
            # Créer les étapes
            for etape_nom, ordre in etapes_autoconso:
                # Déterminer le statut de chaque étape
                if ordre == 1 and has_rapport:
                    statut = 'termine'
                elif ordre == 3 and has_calpinage:
                    statut = 'termine'
                else:
                    statut = 'a_faire'
                
                cur.execute("""
                    INSERT INTO project_etapes (project_id, nom_etape, ordre, statut, date_fin_reelle)
                    VALUES (%s, %s, %s, %s, CASE WHEN %s = 'termine' THEN CURRENT_DATE ELSE NULL END)
                """, (project_id, etape_nom, ordre, statut, statut))
            
            print(f"   ✅ 11 étapes créées (Rapport: {'terminé' if has_rapport else 'à faire'}, Calepinage: {'terminé' if has_calpinage else 'à faire'})")
    
    conn.commit()
    print("\n✅ Tous les projets ont été créés avec succès!")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    fix_missing_projects()
