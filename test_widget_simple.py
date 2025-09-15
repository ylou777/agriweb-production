#!/usr/bin/env python3
"""
Test simple pour vérifier si le widget CRM fonctionne
"""

import requests
import json

def test_widget_crm():
    print('🔍 Test connexion serveur...')
    
    try:
        # Test connexion
        r = requests.get('http://localhost:5000/health', timeout=3)
        print(f'✅ Serveur actif (status: {r.status_code})')
        
        # Test recherche commune
        print('🧪 Test recherche commune avec CRM...')
        params = {
            'commune': 'Lyon',
            'sirene_radius': '0.05'
        }
        
        r2 = requests.get('http://localhost:5000/search_by_commune', params=params, timeout=10)
        print(f'📊 Recherche: status {r2.status_code}')
        
        if r2.status_code == 200:
            data = r2.json()
            crm_available = data.get('crm_available', False)
            prospects = data.get('crm_prospects_detected', 0)
            
            print(f'🎯 CRM disponible: {crm_available}')
            print(f'🏢 Prospects détectés: {prospects}')
            
            if crm_available and prospects > 0:
                print('🎉 SUCCESS: Les données CRM sont présentes!')
                print('   Le widget devrait apparaître dans l\'interface')
                
                # Vérifier analyse SIRENE
                if 'crm_sirene_analysis' in data:
                    analysis = data['crm_sirene_analysis']
                    total = analysis.get('total_enterprises', 0)
                    qualified = analysis.get('qualified_prospects', 0)
                    print(f'📈 Analyse SIRENE: {qualified}/{total} entreprises qualifiées')
                
                return True
            else:
                print('⚠️ Pas de prospects CRM détectés')
                return False
        else:
            print(f'❌ Erreur recherche: {r2.status_code}')
            return False
            
    except Exception as e:
        print(f'❌ Erreur: {e}')
        return False

if __name__ == "__main__":
    success = test_widget_crm()
    
    if success:
        print('\n🎯 ÉTAPES SUIVANTES:')
        print('1. Ouvrez http://localhost:5000 dans votre navigateur')
        print('2. Recherchez "Lyon" avec "Données SIRENE" coché')
        print('3. Le widget CRM vert devrait apparaître après les résultats')
        print('4. Si pas visible, ouvrez F12 et regardez la console JavaScript')
    else:
        print('\n❌ Le widget CRM ne peut pas fonctionner actuellement')