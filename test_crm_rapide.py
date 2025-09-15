#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test rapide pour vérifier les données CRM après recherche commune
"""

import requests
import json

def test_recherche_crm_simple():
    print("🔍 TEST RECHERCHE CRM - VERSION SIMPLE")
    print("=" * 50)
    
    params = {
        'commune': 'Lyon',
        'sirene_radius': '0.05',
        'filter_rpg': 'false',
        'filter_parkings': 'false',
        'filter_friches': 'false',
        'filter_zones': 'false',
        'filter_toitures': 'false'
    }
    
    try:
        print("🚀 Lancement recherche (sans timeout)...")
        r = requests.get('http://localhost:5000/search_by_commune', params=params)
        
        if r.status_code == 200:
            data = r.json()
            print("✅ Recherche terminée avec succès")
            
            # Vérification CRM
            crm_available = data.get('crm_available', False)
            crm_prospects = data.get('crm_prospects_detected', 0)
            
            print(f"🎯 CRM disponible: {crm_available}")
            print(f"👥 Prospects détectés: {crm_prospects}")
            
            # Recherche des clés CRM dans la réponse
            crm_keys = [key for key in data.keys() if 'crm' in key.lower()]
            print(f"🔑 Clés CRM trouvées: {crm_keys}")
            
            if 'crm_sirene_analysis' in data:
                analysis = data['crm_sirene_analysis']
                print(f"📊 Analyse SIRENE: {analysis}")
            
            # Vérification données SIRENE
            sirene_data = data.get('sirene', [])
            if isinstance(sirene_data, list):
                sirene_count = len(sirene_data)
            elif isinstance(sirene_data, dict):
                sirene_count = len(sirene_data.get('features', []))
            else:
                sirene_count = 0
                
            print(f"🏢 Entreprises SIRENE: {sirene_count}")
            
            # Diagnostic final
            if crm_available and crm_prospects > 0:
                print("🎉 DONNÉES CRM CORRECTES - Le widget devrait s'afficher")
                print("👉 Vérifiez maintenant l'interface web")
            else:
                print("❌ Problème avec les données CRM")
                if not crm_available:
                    print("   - CRM non disponible")
                if crm_prospects == 0:
                    print("   - Aucun prospect détecté")
                    
        else:
            print(f"❌ Erreur HTTP: {r.status_code}")
            print(f"Réponse: {r.text[:200]}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_recherche_crm_simple()