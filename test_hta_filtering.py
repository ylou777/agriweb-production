#!/usr/bin/env python3
"""
Test du filtrage HTA lignes pour debug
"""

import requests
import time
import json

def test_hta_filtering():
    """Test du filtrage HTA lignes avec debug détaillé"""
    
    # Attendre que le serveur soit prêt
    print("⏳ Attente démarrage serveur...")
    time.sleep(5)
    
    base_url = "http://localhost:5000"
    
    # Test 1: Sans filtrage (pour référence)
    print("\n🔍 Test 1: Sans filtrage HTA lignes")
    params1 = {
        'department': '90',
        'reseau_types': 'HTA,BT',
        'min_area_ha': '10',
        'max_area_ha': '20',
        'culture': 'Prairie permanente - herbe prédominante (ressources fourragères ligneuses absentes ou peu présentes)',
        'want_eleveurs': 'true'
    }
    
    try:
        response1 = requests.get(f"{base_url}/generate_reports_by_dept_sse", params=params1, stream=True, timeout=30)
        count_communes = 0
        count_rpg = 0
        for line in response1.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if 'SSE COMMUNE' in line_str and 'Traitement de' in line_str:
                    count_communes += 1
                    if count_communes >= 3:  # Limiter à 3 communes pour test
                        break
                elif 'RPG filtré:' in line_str and 'parcelles retenues' in line_str:
                    count_rpg += int(line_str.split('filtré: ')[1].split(' ')[0])
        print(f"✅ Test 1 terminé: {count_communes} communes, {count_rpg} parcelles RPG")
    except Exception as e:
        print(f"❌ Erreur Test 1: {e}")
    
    # Test 2: Avec filtrage souterrain activé
    print("\n🔍 Test 2: Avec filtrage HTA souterrain activé (500m)")
    params2 = {
        'department': '90',
        'reseau_types': 'HTA,BT',
        'min_area_ha': '10',
        'max_area_ha': '20',
        'hta_underground_max_distance': '0.5',  # 500m
        'filter_hta_lines_underground': 'true',  # Activer le filtre
        'culture': 'Prairie permanente - herbe prédominante (ressources fourragères ligneuses absentes ou peu présentes)',
        'want_eleveurs': 'true'
    }
    
    try:
        response2 = requests.get(f"{base_url}/generate_reports_by_dept_sse", params=params2, stream=True, timeout=30)
        count_communes = 0
        count_rpg = 0
        debug_lines = []
        for line in response2.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if 'SSE COMMUNE' in line_str and 'Traitement de' in line_str:
                    count_communes += 1
                    if count_communes >= 3:  # Limiter à 3 communes pour test
                        break
                elif 'RPG filtré:' in line_str and 'parcelles retenues' in line_str:
                    count_rpg += int(line_str.split('filtré: ')[1].split(' ')[0])
                elif any(keyword in line_str for keyword in ['HTA UNDERGROUND', 'RPG REJECTED', 'Filtres HTA lignes']):
                    debug_lines.append(line_str.strip())
        
        print(f"✅ Test 2 terminé: {count_communes} communes, {count_rpg} parcelles RPG")
        if debug_lines:
            print("🔍 Debug info:")
            for debug_line in debug_lines[:10]:  # Limiter à 10 lignes
                print(f"  {debug_line}")
    except Exception as e:
        print(f"❌ Erreur Test 2: {e}")

if __name__ == "__main__":
    test_hta_filtering()