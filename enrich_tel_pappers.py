import csv
import requests
import time

# IMPORTANT: Remplacer par votre clé API Pappers
# Obtenir une clé gratuite sur https://www.pappers.fr/api
API_KEY = "e17b5b017e050f8ef37cf5853557ea8bc90afb11c1bcfbc2"

# Lire le fichier CSV généré précédemment
input_file = 'societes_pv_enrichies.csv'
output_file = 'societes_pv_avec_telephones.csv'

resultats = []

with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    donnees = list(reader)

print(f"Traitement de {len(donnees)} lignes...")

for idx, row in enumerate(donnees, 1):
    societe = row['societe_recherchee']
    siren = row['siren']
    denomination = row['denomination']
    
    telephone = 'N/A'
    email = 'N/A'
    adresse = 'N/A'
    
    if siren and siren != 'NON TROUVE':
        print(f"[{idx}/{len(donnees)}] Interrogation API pour {denomination} (SIREN: {siren})...")
        
        try:
            # Appel API Pappers - Méthode 1: header api-key
            url = f"https://api.pappers.fr/v2/entreprise?siren={siren}&api_token={API_KEY}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Récupérer le téléphone du siège
                if 'siege' in data and data['siege']:
                    telephone = data['siege'].get('telephone', 'N/A')
                
                # Récupérer l'email
                if 'email' in data:
                    email = data.get('email', 'N/A')
                
                # Récupérer l'adresse complète
                if 'siege' in data and data['siege']:
                    siege = data['siege']
                    adresse_parts = []
                    if siege.get('numero_voie'):
                        adresse_parts.append(siege['numero_voie'])
                    if siege.get('type_voie'):
                        adresse_parts.append(siege['type_voie'])
                    if siege.get('libelle_voie'):
                        adresse_parts.append(siege['libelle_voie'])
                    if siege.get('code_postal'):
                        adresse_parts.append(siege['code_postal'])
                    if siege.get('ville'):
                        adresse_parts.append(siege['ville'])
                    
                    if adresse_parts:
                        adresse = ' '.join(adresse_parts)
                
                print(f"  -> Tel: {telephone}, Email: {email}")
                
            elif response.status_code == 404:
                print(f"  -> Entreprise non trouvee dans Pappers")
            elif response.status_code == 401:
                print(f"  -> ERREUR: Cle API incorrecte!")
                break
            else:
                print(f"  -> Erreur API: {response.status_code}")
            
            # Pause pour respecter les limites de l'API (gratuit = 100 requêtes/mois)
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  -> Erreur: {e}")
    else:
        print(f"[{idx}/{len(donnees)}] {societe} - SIREN non trouve, skip")
    
    resultats.append({
        'societe_recherchee': societe,
        'siren': siren,
        'denomination': denomination,
        'telephone': telephone,
        'email': email,
        'adresse': adresse
    })

# Ecrire les résultats
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['societe_recherchee', 'siren', 'denomination', 'telephone', 'email', 'adresse'])
    writer.writeheader()
    writer.writerows(resultats)

print(f"\n=== Terminé ===")
print(f"Fichier créé: {output_file}")
print(f"Téléphones trouvés: {len([r for r in resultats if r['telephone'] != 'N/A'])}")
print(f"Emails trouvés: {len([r for r in resultats if r['email'] != 'N/A'])}")
