#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'intégration KPI pour AgriWeb
Permet à AgriWeb de communiquer avec l'API KPI SUNSTICE
"""

import sys
sys.path.insert(0, r'C:\Users\Utilisateur\Desktop\KPI')

from kpi_api_client import create_client

# Client API KPI
kpi_client = create_client(
    base_url='http://localhost:5000',
    api_key='dev_key_sunstice_2025'
)

def sync_agriculteur_to_kpi(agriculteur_data):
    """
    Envoie un agriculteur d'AgriWeb vers KPI
    
    Args:
        agriculteur_data: dict avec nom, email, telephone, adresse, etc.
        
    Returns:
        dict: Résultat de la création {'status': 'success', 'id': 123}
    """
    try:
        # Vérifier d'abord si c'est un doublon
        duplicate_check = kpi_client.check_duplicate(
            table='agriculteurs',
            nom=agriculteur_data.get('nom'),
            code_postal=agriculteur_data.get('code_postal')
        )
        
        if duplicate_check.get('duplicate'):
            print(f"⚠️  Doublon détecté: {agriculteur_data.get('nom')}")
            return {
                'status': 'duplicate',
                'message': 'Contact déjà existant dans KPI',
                'existing': duplicate_check.get('existing_record')
            }
        
        # Créer le nouveau contact
        result = kpi_client.create_agriculteur({
            'nom': agriculteur_data.get('nom'),
            'categorie': agriculteur_data.get('type', 'Exploitation'),
            'email': agriculteur_data.get('email'),
            'telephone': agriculteur_data.get('telephone'),
            'adresse': agriculteur_data.get('adresse'),
            'code_postal': agriculteur_data.get('code_postal'),
            'ville': agriculteur_data.get('ville'),
            'departement': agriculteur_data.get('departement'),
            'statut': 'Non contacté',
            'notes': f"Importé depuis AgriWeb le {agriculteur_data.get('date')}"
        })
        
        print(f"✅ Agriculteur synchronisé vers KPI: ID {result.get('id')}")
        return result
        
    except Exception as e:
        print(f"❌ Erreur synchro vers KPI: {e}")
        return {'status': 'error', 'message': str(e)}


def get_prospects_from_kpi(departement=None, limit=100):
    """
    Récupère les prospects depuis KPI pour les afficher dans AgriWeb
    
    Args:
        departement: Filtre par département (ex: "29")
        limit: Nombre max de résultats
        
    Returns:
        list: Liste des prospects KPI
    """
    try:
        # Récupérer les agriculteurs de KPI
        result = kpi_client.get_agriculteurs(
            departement=departement,
            limit=limit
        )
        
        agriculteurs = result.get('data', [])
        print(f"📥 {len(agriculteurs)} prospects récupérés depuis KPI")
        
        return agriculteurs
        
    except Exception as e:
        print(f"❌ Erreur récupération KPI: {e}")
        return []


def test_kpi_connection():
    """Test la connexion à l'API KPI"""
    try:
        if kpi_client.test_connection():
            print("✅ AgriWeb connecté à l'API KPI")
            stats = kpi_client.get_stats()
            print(f"   Base KPI contient:")
            for key, value in stats.get('data', {}).items():
                print(f"   - {key}: {value:,}")
            return True
        else:
            print("❌ API KPI non disponible")
            return False
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return False


# Auto-test au lancement
if __name__ == '__main__':
    print("=" * 70)
    print("TEST INTEGRATION AgriWeb -> KPI")
    print("=" * 70)
    
    # Test connexion
    test_kpi_connection()
    
    # Test récupération
    print("\nTest récupération prospects du 29:")
    prospects = get_prospects_from_kpi(departement="29", limit=5)
    for p in prospects[:3]:
        print(f"  - {p.get('nom')} ({p.get('ville', 'N/A')})")
    
    print("\n" + "=" * 70)
