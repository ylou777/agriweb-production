"""
Test de la route de génération Déclaration Préalable
Simule un appel à l'API CRM pour générer le dossier DP complet
"""

import sys
import os

# Ajouter le dossier parent au path pour importer les modules
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from crm_routes import register_crm_routes
from database_adapter import execute_query
import json

# Créer une app Flask de test
app = Flask(__name__)
app.config['TESTING'] = True

# Enregistrer les routes CRM
register_crm_routes(app)

def test_dp_generation():
    """Test de génération DP avec données de test"""
    
    print("\n" + "="*70)
    print("🧪 TEST - Génération Déclaration Préalable")
    print("="*70)
    
    # 1. Utiliser les données de test directement
    print("\n📊 Utilisation des données de test...")
    
    prospect_id = 999  # ID fictif pour le test
    
    from test_declaration_prealable import prospect_test, calpinage_test
    
    print(f"✅ Prospect de test: {prospect_test['nom_prospect']}, {prospect_test['commune']}")
    print(f"   → Calpinage: {sum(z.get('nbModules', 0) for z in calpinage_test.get('zones', []))} modules")
    
    # 2. Tester l'endpoint
    print(f"\n🚀 Appel API: POST /api/crm/prospect/{prospect_id}/generer-dp")
    
    with app.test_client() as client:
        response = client.post(f'/api/crm/prospect/{prospect_id}/generer-dp')
        
        print(f"\n📥 Réponse:")
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.content_type}")
        
        if response.status_code == 200:
            # Vérifier que c'est bien un ZIP
            if response.content_type == 'application/zip':
                size_kb = len(response.data) / 1024
                print(f"   Taille: {size_kb:.1f} KB")
                
                # Sauvegarder le fichier ZIP pour inspection
                output_file = f"test_dossier_dp_{prospect_id}.zip"
                with open(output_file, 'wb') as f:
                    f.write(response.data)
                
                print(f"\n✅ SUCCÈS ! Fichier sauvegardé: {output_file}")
                print(f"   → Ouvrez ce fichier pour voir les 9 documents PDF")
                
            else:
                print(f"⚠️ Type inattendu: {response.content_type}")
                print(f"   Données: {response.data[:200]}")
        
        else:
            print(f"❌ ERREUR {response.status_code}")
            if response.is_json:
                error_data = response.get_json()
                print(f"   Message: {error_data.get('error', 'Erreur inconnue')}")
            else:
                print(f"   Réponse: {response.data.decode('utf-8')[:500]}")
    
    print("\n" + "="*70 + "\n")

if __name__ == '__main__':
    test_dp_generation()
