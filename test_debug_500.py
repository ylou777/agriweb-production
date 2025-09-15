#!/usr/bin/env python3
"""
Script de diagnostic pour l'erreur 500 dans AgriWeb
"""

import requests
import json

def test_server():
    print('🔍 TEST DIAGNOSTIC ERREUR 500')
    print('=' * 40)
    
    try:
        print('📍 Test connexion de base...')
        r = requests.get('http://localhost:5000/', timeout=5)
        print(f'✅ Connexion OK (status: {r.status_code})')
        
        print('\n🔍 Test recherche Lyon...')
        params = {
            'commune': 'Lyon',
            'sirene_radius': '0.05',
            'filter_rpg': 'false',
            'filter_parkings': 'false', 
            'filter_friches': 'false',
            'filter_zones': 'false',
            'filter_toitures': 'false'
        }
        
        response = requests.get('http://localhost:5000/search_by_commune', params=params, timeout=30)
        print(f'📊 Status Code: {response.status_code}')
        
        if response.status_code == 500:
            print('❌ ERREUR 500 DÉTECTÉE!')
            print('🔍 Détails de l\'erreur:')
            print('-' * 50)
            error_content = response.text
            print(error_content[:1500])  
            print('-' * 50)
            
            # Essayer de parser le JSON d'erreur si possible
            try:
                error_json = response.json()
                print('📋 Structure JSON de l\'erreur:')
                print(json.dumps(error_json, indent=2)[:500])
            except:
                print('⚠️ Pas de JSON valide dans la réponse d\'erreur')
                
        elif response.status_code == 200:
            print('✅ Recherche réussie!')
            data = response.json()
            crm_available = data.get('crm_available', False)
            prospects_detected = data.get('crm_prospects_detected', 0)
            print(f'🎯 CRM disponible: {crm_available}')
            print(f'📈 Prospects détectés: {prospects_detected}')
            
            if crm_available and prospects_detected > 0:
                print('🎉 LE WIDGET CRM DEVRAIT S\'AFFICHER!')
            
        else:
            print(f'⚠️ Status inattendu: {response.status_code}')
            print(f'Contenu: {response.text[:300]}')
            
    except requests.exceptions.ConnectionError:
        print('❌ SERVEUR NON ACCESSIBLE')
        print('🔧 Le serveur n\'est pas en cours d\'exécution sur localhost:5000')
    except requests.exceptions.Timeout:
        print('⏱️ TIMEOUT')
        print('🔧 La requête a pris trop de temps')
    except Exception as e:
        print(f'❌ Erreur inattendue: {e}')
        print(f'Type: {type(e).__name__}')

if __name__ == '__main__':
    test_server()