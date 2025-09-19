#!/usr/bin/env python3
"""
Test du filtrage HTA lignes corrigé
"""

import requests
import time

def test_fixed_hta_filtering():
    """Test le filtrage HTA lignes après correction"""
    
    print("⏳ Attente démarrage serveur...")
    time.sleep(8)
    
    base_url = "http://localhost:5000"
    
    print("\n🔍 Test avec filtrage HTA souterrain activé (500m)")
    params = {
        'department': '90',
        'reseau_types': 'HTA,BT',
        'min_area_ha': '5',
        'max_area_ha': '50',
        'hta_underground_max_distance': '0.5',  # 500m
        'filter_hta_lines_underground': 'true',  # Activer le filtre
        'culture': 'Prairie permanente - herbe prédominante (ressources fourragères ligneuses absentes ou peu présentes)',
        'want_eleveurs': 'true'
    }
    
    try:
        response = requests.get(f"{base_url}/generate_reports_by_dept_sse", params=params, stream=True, timeout=60)
        count_communes = 0
        count_rpg = 0
        rejected_count = 0
        hta_debug_lines = []
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                
                # Compter les communes traitées
                if 'SSE COMMUNE' in line_str and 'Traitement de' in line_str:
                    count_communes += 1
                    print(f"  📍 Commune {count_communes}")
                    if count_communes >= 3:  # Limiter à 3 communes pour test
                        break
                
                # Compter les parcelles RPG filtrées
                elif 'RPG filtré:' in line_str and 'parcelles retenues' in line_str:
                    rpg_count = int(line_str.split('filtré: ')[1].split(' ')[0])
                    count_rpg += rpg_count
                    if rpg_count > 0:
                        print(f"    ✅ {rpg_count} parcelles retenues")
                
                # Capturer les logs de debug HTA
                elif any(keyword in line_str for keyword in ['HTA UNDERGROUND', 'RPG REJECTED', 'Lignes HTA récupérées']):
                    hta_debug_lines.append(line_str.strip())
                    if 'RPG REJECTED' in line_str and 'lignes HTA' in line_str:
                        rejected_count += 1
        
        print(f"\n📊 Résultats du test:")
        print(f"   🏘️ Communes traitées: {count_communes}")
        print(f"   🌾 Parcelles RPG retenues: {count_rpg}")
        print(f"   ❌ Parcelles rejetées par filtre HTA: {rejected_count}")
        
        if hta_debug_lines:
            print(f"\n🔍 Debug HTA (premières 5 lignes):")
            for debug_line in hta_debug_lines[:5]:
                print(f"   {debug_line}")
        
        # Verdict
        if count_rpg > 0:
            print(f"\n✅ TEST RÉUSSI: {count_rpg} parcelles filtrées avec succès")
        elif rejected_count > 0:
            print(f"\n⚠️ TEST PARTIEL: Filtrage fonctionne (rejets: {rejected_count}) mais aucune parcelle retenue")
        else:
            print(f"\n❌ TEST ÉCHEC: Aucun filtrage détecté")
            
    except Exception as e:
        print(f"❌ Erreur test: {e}")

if __name__ == "__main__":
    test_fixed_hta_filtering()