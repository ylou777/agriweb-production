import os
import psycopg2
import csv

# Liste des sociétés à enrichir
societes = [
    "Neoen", "Fonroche Energie", "Akuo Energy", "Arkolia Energies", "Qair Group",
    "Valorem", "Eolfi", "Voltalia", "Engie Green", "TotalEnergies Renewables",
    "EDF Renouvelables", "CNR", "RWE Renewables France", "BayWa r.e.", "Iberdrola France",
    "VSB Energies Nouvelles", "Amarenco", "SolaireDirect", "Sonnedix France", "Photosol",
    "Reden Solar", "Tenergie", "Sergies", "CVE", "Corfu Solaire", "Albioma", "Luxel",
    "Inelia", "Technique Solaire", "Enbridge Europe", "Octopus Energy", "JPee", "RES France",
    "Engie Solutions", "Urbasolar", "Quadran", "Wpd Solar", "AkuoCoop", "Sun'Agri", "TSE",
    "Ombrea", "AgriPV Solutions", "Akuo Agrinergie", "Arkolia Agri", "Amarenco Agri",
    "Voltalia Agri", "Soleil du Sud", "Green Lighthouse", "Generale du Solaire",
    "Soleil du Midi", "Vol-V Solar", "Solaire France", "Centrales Villageoises",
    "Volta Energies", "Alterna", "Eneria", "Enercoop Bretagne", "IEL Energie",
    "Solaire 35", "Langa Solar", "Dhamma Energy", "Sirea", "SunPower France",
    "Systeko", "Inelio", "Adjutor", "Ciel & Terre", "GreenYellow", "Compagnie des Negoces Electriques",
    "In Sun We Trust", "Comwatt", "DualSun", "Enercoop", "Photowatt", "Voltec Solar",
    "Systovi", "Recom", "Sunpower Maxeon", "Evasol", "Tryba Energie", "Otovo France",
    "Effy", "Enersol", "Proxeo Solaire", "Helios Energie", "Solveo Energie", "Greenbirdie"
]

# Connexion à la base
DATABASE_URL = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

resultats = []

for societe in societes:
    print(f"Recherche: {societe}...")
    
    # Recherche dans proprietaires_parcelles
    cur.execute("""
        SELECT DISTINCT siren, denomination
        FROM proprietaires_parcelles
        WHERE LOWER(denomination) LIKE LOWER(%s)
        LIMIT 5
    """, (f'%{societe}%',))
    
    rows = cur.fetchall()
    
    if rows:
        for row in rows:
            resultats.append({
                'societe_recherchee': societe,
                'siren': row[0],
                'denomination': row[1]
            })
            print(f"  -> Trouve: {row[1]} (SIREN: {row[0]})")
    else:
        resultats.append({
            'societe_recherchee': societe,
            'siren': 'NON TROUVE',
            'denomination': 'NON TROUVE'
        })
        print(f"  -> Non trouve")

cur.close()
conn.close()

# Ecrire dans un CSV
with open('societes_pv_enrichies.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['societe_recherchee', 'siren', 'denomination'])
    writer.writeheader()
    writer.writerows(resultats)

print(f"\n=== Resultats ecrits dans societes_pv_enrichies.csv ===")
print(f"Total: {len(resultats)} resultats")
print(f"Trouves: {len([r for r in resultats if r['siren'] != 'NON TROUVE'])}")
print(f"Non trouves: {len([r for r in resultats if r['siren'] == 'NON TROUVE'])}")
