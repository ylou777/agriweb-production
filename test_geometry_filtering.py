#!/usr/bin/env python3
"""
Test de validation des corrections HTA lignes avec filtrage géométrique
"""

import requests
import time
import json

def test_hta_filtering_with_geometry():
    """Test du filtrage HTA lignes avec contour de commune"""
    
    # Attendre que le serveur soit prêt
    print("⏳ Attente démarrage serveur...")
    time.sleep(8)
    
    base_url = "http://localhost:5000"
    
    print("\n🔍 Test: Filtrage HTA lignes avec contour de commune")
    params = {
        'department': '90',  # Territoire de Belfort
        'reseau_types': 'HTA,BT',
        'min_area_ha': '10',
        'max_area_ha': '30',
        'hta_underground_max_distance': '0.5',  # 500m
        'filter_hta_lines_underground': 'true',  # Activer le filtre souterrain
        'culture': 'Prairie permanente - herbe prédominante (ressources fourragères ligneuses absentes ou peu présentes)',
        'want_eleveurs': 'true'
    }
    
    try:
        response = requests.get(f"{base_url}/generate_reports_by_dept_sse", params=params, stream=True, timeout=60)
        count_communes = 0
        count_rpg = 0
        debug_lines = []
        hta_lines_info = []
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                
                # Compter les communes traitées
                if 'SSE COMMUNE' in line_str and 'Traitement de' in line_str:
                    count_communes += 1
                    commune_name = line_str.split('Traitement de ')[-1].strip()
                    print(f"\n📍 Commune {count_communes}: {commune_name}")
                    
                    if count_communes >= 3:  # Limiter à 3 communes pour test
                        break
                
                # Capturer les infos sur les lignes HTA
                if any(keyword in line_str for keyword in [
                    'Lignes HTA dans commune',
                    'Avant filtrage géométrique',
                    'Bbox englobant',
                    'HTA UNDERGROUND',
                    'RPG filtré:'
                ]):
                    debug_lines.append(line_str.strip())
                    print(f"  🔍 {line_str.strip()}")
                
                # Compter les parcelles RPG retenues
                if 'RPG filtré:' in line_str and 'parcelles retenues' in line_str:
                    parcelles_count = int(line_str.split('filtré: ')[1].split(' ')[0])
                    count_rpg += parcelles_count
                    if parcelles_count > 0:
                        print(f"  ✅ {parcelles_count} parcelles RPG retenues !")
        
        print(f"\n📊 Résultats du test:")
        print(f"   - Communes traitées: {count_communes}")
        print(f"   - Total parcelles RPG retenues: {count_rpg}")
        
        if count_rpg > 0:
            print("🎉 SUCCESS: Le filtrage des parcelles RPG par distance aux lignes HTA fonctionne !")
        else:
            print("⚠️  ATTENTION: Aucune parcelle RPG retenue - vérifier la logique de filtrage")
        
        # Analyser les logs de debug
        bbox_lines = [line for line in debug_lines if 'Bbox englobant' in line]
        hta_lines = [line for line in debug_lines if 'Lignes HTA dans commune' in line]
        filtrage_lines = [line for line in debug_lines if 'Avant filtrage géométrique' in line]
        
        print(f"\n🔍 Analyse des logs:")
        print(f"   - Bbox calculés: {len(bbox_lines)}")
        print(f"   - Lignes HTA récupérées: {len(hta_lines)}")
        print(f"   - Filtrage géométrique: {len(filtrage_lines)}")
        
        if hta_lines:
            print("📋 Exemples de récupération de lignes HTA:")
            for line in hta_lines[:3]:
                print(f"   {line}")
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")

if __name__ == "__main__":
    test_hta_filtering_with_geometry()