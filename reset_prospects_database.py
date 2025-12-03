"""
Script pour réinitialiser la base de données prospects
- Sauvegarde les prospects actuels
- Vide la table agriweb_prospects
- Réinitialise les séquences
"""

import psycopg2
import os
from datetime import datetime
import json

# Connexion Railway
DATABASE_URL = os.getenv('DATABASE_PUBLIC_URL') or "postgresql://postgres:WbjgkcXDKvbbYJhWprDDQQobbpnggYJc@yamanote.proxy.rlwy.net:42931/railway"

def sauvegarder_prospects():
    """Sauvegarde tous les prospects actuels dans un fichier JSON"""
    print("📦 Sauvegarde des prospects actuels...")
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            id, type, commune, departement, adresse, latitude, longitude, 
            surface_m2, surface_ha, parcelles_cadastrales,
            poste_bt_distance_m, poste_hta_distance_m, lien_streetview, lien_annuaire,
            statut, priorite, notes, 
            contact_nom, contact_email, contact_telephone,
            nom_prospect, representant_nom, representant_tel, representant_email,
            siren, dirigeant_nom, dirigeant_email, dirigeant_tel, siret,
            poste_bt_nom, poste_bt_puissance, poste_bt_lat, poste_bt_lon, poste_bt_proprietaire,
            poste_hta_nom, poste_hta_puissance, poste_hta_lat, poste_hta_lon, poste_hta_proprietaire,
            osm_amenity, osm_shop, osm_building, osm_landuse, osm_office, osm_industrial,
            proprietaire_siren, proprietaire_siret, proprietaire_denomination,
            proprietaire_forme_juridique, proprietaire_adresse, 
            proprietaire_code_postal, proprietaire_ville, proprietaire_enrichi_date,
            date_creation, date_modification, data_json
        FROM agriweb_prospects
        ORDER BY id
    """)
    
    prospects = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    
    # Convertir en liste de dictionnaires
    prospects_list = []
    for row in prospects:
        prospect_dict = {}
        for i, col in enumerate(columns):
            value = row[i]
            # Convertir les dates en string
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            prospect_dict[col] = value
        prospects_list.append(prospect_dict)
    
    # Sauvegarder dans un fichier JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'sauvegarde_prospects_{timestamp}.json'
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(prospects_list, f, ensure_ascii=False, indent=2)
    
    cur.close()
    conn.close()
    
    print(f"✅ {len(prospects_list)} prospects sauvegardés dans {filename}")
    return len(prospects_list)

def reset_database():
    """Vide la table prospects et réinitialise les séquences"""
    print("\n🗑️  Réinitialisation de la base de données...")
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Compter les prospects avant suppression
    cur.execute("SELECT COUNT(*) FROM agriweb_prospects")
    count_before = cur.fetchone()[0]
    print(f"   Prospects actuels : {count_before}")
    
    # Vider la table
    cur.execute("DELETE FROM agriweb_prospects")
    
    # Réinitialiser la séquence d'ID
    cur.execute("ALTER SEQUENCE agriweb_prospects_id_seq RESTART WITH 1")
    
    conn.commit()
    
    # Vérifier
    cur.execute("SELECT COUNT(*) FROM agriweb_prospects")
    count_after = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    print(f"✅ Table vidée : {count_before} prospects supprimés")
    print(f"✅ Séquence réinitialisée : prochain ID = 1")
    print(f"✅ Prospects restants : {count_after}")

def main():
    print("=" * 60)
    print("🔄 RÉINITIALISATION DE LA BASE DE DONNÉES PROSPECTS")
    print("=" * 60)
    
    confirmation = input("\n⚠️  Cette opération va supprimer TOUS les prospects.\nTapez 'OUI' pour confirmer : ")
    
    if confirmation.upper() != 'OUI':
        print("❌ Opération annulée")
        return
    
    try:
        # Étape 1 : Sauvegarde
        nb_prospects = sauvegarder_prospects()
        
        # Étape 2 : Réinitialisation
        reset_database()
        
        print("\n" + "=" * 60)
        print("✅ RÉINITIALISATION TERMINÉE AVEC SUCCÈS")
        print("=" * 60)
        print(f"\n📊 Résumé :")
        print(f"   - {nb_prospects} prospects sauvegardés")
        print(f"   - Base de données vidée")
        print(f"   - Séquences réinitialisées")
        print(f"\n🚀 Vous pouvez maintenant créer de nouveaux prospects enrichis !")
        
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
