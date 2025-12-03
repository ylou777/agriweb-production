"""
Script pour enrichir la liste des acteurs du solaire photovoltaïque avec leurs numéros de téléphone
Utilise la base de données SIREN/SIRET + recherches web complémentaires
"""

import os
import psycopg2
import json
from typing import Dict, List, Optional

# Connexion à la base de données Railway
DATABASE_URL = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')

# Liste des sociétés à enrichir (classées par catégorie)
COMPANIES = {
    "A. GRANDS PRODUCTEURS / DÉVELOPPEURS NATIONAUX & INTERNATIONAUX": [
        "Neoen", "Fonroche Énergie", "Akuo Energy", "Arkolia Énergies", "Qair Group",
        "Valorem", "Eolfi", "Voltalia", "Engie Green", "TotalEnergies Renewables",
        "EDF Renouvelables", "CNR", "RWE Renewables France", "BayWa r.e.", "Iberdrola France",
        "VSB Énergies Nouvelles", "Amarenco", "SolaireDirect", "Sonnedix France", "Photosol",
        "Reden Solar", "Tenergie", "Sergies", "CVE", "Corfu Solaire", "Albioma",
        "Luxel", "Inelia", "Technique Solaire", "Enbridge Europe", "Octopus Energy RE",
        "Amarenco France", "JPee", "RES France", "Engie Solutions", "Urbasolar",
        "Quadran", "Wpd Solar", "AkuoCoop"
    ],
    "B. ACTEURS AGRIVOLTAÏQUES": [
        "Sun'Agri", "TSE", "Ombrea", "AgriPV Solutions", "Akuo Agrinergie",
        "Arkolia Agri", "Amarenco Agri", "Voltalia Agri"
    ],
    "C. DÉVELOPPEURS RÉGIONAUX / LOCAUX": [
        "Soleil du Sud", "Green Lighthouse", "Générale du Solaire", "Soleil du Midi",
        "Vol-V Solar", "Solaire France", "Centrales Villageoises", "Volta Énergies",
        "Alterna", "Eneria", "Enercoop Bretagne", "IEL Énergie", "Solaire 35"
    ],
    "D. INSTALLATEURS INDUSTRIELS / GRANDS INTÉGRATEURS": [
        "Langa Solar", "Dhamma Energy", "Sirea", "SunPower France", "Systeko",
        "Inelio", "Adjutor", "Ciel & Terre"
    ],
    "E. AUTOCONSOMMATION INDUSTRIELLE & COMMERCIALE": [
        "GreenYellow", "Compagnie des Négoces Électriques", "In Sun We Trust",
        "Comwatt", "DualSun", "Enercoop"
    ],
    "F. GÉNÉRATEURS SOLAIRES / FOURNISSEURS / OEM": [
        "Photowatt", "Voltec Solar", "Systovi", "Recom", "Sunpower Maxeon"
    ],
    "G. GRANDS INSTALLATEURS": [
        "Evasol", "Tryba Énergie", "Otovo France", "Effy", "Enersol",
        "Proxéo Solaire", "Hélios Énergie", "Solvéo Énergie", "Greenbirdie"
    ]
}

def search_company_in_db(company_name: str) -> Optional[Dict]:
    """
    Recherche une entreprise dans la base de données proprietaires_parcelles
    Retourne SIREN, dénomination, adresse, forme juridique si trouvé
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Recherche par dénomination (LIKE insensible à la casse)
        # Nettoyer le nom pour la recherche
        search_name = company_name.upper()
        # Enlever les suffixes courants
        search_name = search_name.replace(' FRANCE', '').replace(' ENERGIE', '').replace(' ENERGIES', '')
        
        query = """
        SELECT DISTINCT 
            siren, 
            denomination, 
            forme_juridique
        FROM proprietaires_parcelles 
        WHERE UPPER(denomination) LIKE %s
        LIMIT 1
        """
        
        cur.execute(query, (f'%{search_name}%',))
        result = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if result:
            return {
                'siren': result[0],
                'denomination': result[1],
                'forme_juridique': result[2],
                'found_in_db': True
            }
        
        return None
        
    except Exception as e:
        print(f"Erreur recherche {company_name}: {e}")
        return None

def get_company_phone_from_siren(siren: str) -> Optional[str]:
    """
    Tenterait de récupérer le téléphone depuis une API (pappers.fr, societe.com, etc.)
    Pour l'instant, retourne None - à implémenter avec API externe
    """
    # TODO: Intégration API Pappers.fr ou équivalent
    # Exemple: GET https://api.pappers.fr/v2/entreprise?api_token=XXX&siren=XXX
    return None

def enrich_companies():
    """
    Enrichit toutes les sociétés et affiche le résultat formaté
    """
    print("=" * 100)
    print("ENRICHISSEMENT DES ACTEURS DU PHOTOVOLTAÏQUE EN FRANCE")
    print("=" * 100)
    print()
    
    results = {}
    total_found = 0
    total_companies = 0
    
    for category, companies in COMPANIES.items():
        print(f"\n{'=' * 80}")
        print(f"[*] {category}")
        print(f"{'=' * 80}\n")
        
        category_results = []
        
        for company in companies:
            total_companies += 1
            print(f"Recherche: {company:<40}", end=" ")
            
            # Recherche dans la base de données
            db_info = search_company_in_db(company)
            
            if db_info:
                total_found += 1
                print(f"[OK] TROUVE")
                print(f"  |-- Denomination complete: {db_info['denomination']}")
                print(f"  |-- SIREN: {db_info['siren']}")
                print(f"  |-- Forme juridique: {db_info['forme_juridique']}")
                
                # Tentative de récupération du téléphone
                phone = get_company_phone_from_siren(db_info['siren'])
                if phone:
                    print(f"  |-- Telephone: {phone}")
                    db_info['telephone'] = phone
                else:
                    print(f"  |-- Telephone: A rechercher manuellement")
                    db_info['telephone'] = None
                
                category_results.append({
                    'name': company,
                    'info': db_info
                })
            else:
                print(f"[X] NON TROUVE dans la base")
                category_results.append({
                    'name': company,
                    'info': None
                })
            
            print()
        
        results[category] = category_results
    
    # Résumé
    print("\n" + "=" * 100)
    print(f"RÉSUMÉ: {total_found}/{total_companies} sociétés trouvées dans la base ({total_found*100/total_companies:.1f}%)")
    print("=" * 100)
    
    # Génération d'un fichier Markdown avec les résultats
    generate_markdown_report(results, total_found, total_companies)
    
    return results

def generate_markdown_report(results: Dict, total_found: int, total_companies: int):
    """
    Génère un fichier Markdown avec les résultats enrichis
    """
    output_file = "societes_photovoltaique_enrichies.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# ACTEURS DU PHOTOVOLTAÏQUE EN FRANCE - DONNÉES ENRICHIES\n\n")
        f.write(f"**Enrichissement:** {total_found}/{total_companies} sociétés ({total_found*100/total_companies:.1f}%)\n\n")
        f.write("---\n\n")
        
        for category, companies in results.items():
            f.write(f"## {category}\n\n")
            f.write("| Société | SIREN | Forme juridique | Téléphone | Statut |\n")
            f.write("|---------|-------|-----------------|-----------|--------|\n")
            
            for company_data in companies:
                name = company_data['name']
                info = company_data['info']
                
                if info:
                    siren = info.get('siren', 'N/A')
                    forme = info.get('forme_juridique', 'N/A')
                    tel = info.get('telephone', 'A rechercher')
                    status = "Enrichi"
                else:
                    siren = "N/A"
                    forme = "N/A"
                    tel = "A rechercher"
                    status = "Non trouvé"
                
                f.write(f"| {name} | {siren} | {forme} | {tel} | {status} |\n")
            
            f.write("\n")
        
        f.write("\n---\n\n")
        f.write("## NOTES\n\n")
        f.write("- Les donnees SIREN/forme juridique proviennent de la base proprietaires_parcelles\n")
        f.write("- Les numeros de telephone necessitent une recherche manuelle ou une API externe (Pappers.fr, Societe.com)\n")
        f.write("- Certaines societes peuvent avoir plusieurs etablissements avec des coordonnees differentes\n")
    
    print(f"\n✅ Rapport généré: {output_file}\n")

if __name__ == "__main__":
    enrich_companies()
