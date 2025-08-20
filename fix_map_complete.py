#!/usr/bin/env python3
"""
Script de correction complète pour les problèmes de carte :
1. Styles orange à cause des fonctions lambda
2. Sélecteur de couches manquant dans map1.html
3. Zoom par défaut trop élevé dans la recherche d'adresse
"""

import re

def fix_agriweb_styles():
    """Corrige les problèmes de styles dans agriweb_hebergement_gratuit.py"""
    
    # Lire le fichier principal
    with open('agriweb_hebergement_gratuit.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Corriger le zoom par défaut dans la recherche d'adresse (revenir à 12)
    content = re.sub(
        r'zoom_level = 17',
        'zoom_level = 12',
        content
    )
    
    # 2. Remplacer les fonctions lambda par des styles statiques
    # Pattern pour les styles avec lambda
    lambda_patterns = [
        # Couleur orange problématique
        (r"'color': lambda x: '#FFA500'", "'color': '#FFA500'"),
        (r'"color": lambda x: "#FFA500"', '"color": "#FFA500"'),
        
        # Styles des différents types de couches
        (r"'color': lambda x: get_color_by_type\(x\)", "'color': '#3388ff'"),
        (r'"color": lambda x: get_color_by_type\(x\)', '"color": "#3388ff"'),
        
        # Styles spécifiques par type
        (r"'color': lambda x: '#FF6600' if x.get\('type'\) == 'parcelle' else '#3388ff'", "'color': '#FF6600'"),
        (r'"color": lambda x: "#FF6600" if x.get\("type"\) == "parcelle" else "#3388ff"', '"color": "#FF6600"'),
    ]
    
    for pattern, replacement in lambda_patterns:
        content = re.sub(pattern, replacement, content)
    
    # 3. Créer des styles statiques pour chaque type de couche
    styles_section = '''
# Styles statiques pour éviter les problèmes avec les fonctions lambda en production
STATIC_STYLES = {
    'parcelles': {'color': '#FF6600', 'fillColor': '#FFD700', 'fillOpacity': 0.3, 'weight': 2},
    'postes_bt': {'color': '#FFD700', 'fillColor': '#FFD700', 'fillOpacity': 0.6, 'weight': 2},
    'postes_hta': {'color': '#D12322', 'fillColor': '#D12322', 'fillOpacity': 0.6, 'weight': 2},
    'eleveurs': {'color': '#34ad41', 'fillColor': '#34ad41', 'fillOpacity': 0.5, 'weight': 2},
    'parkings': {'color': '#2ecc71', 'fillColor': '#2ecc71', 'fillOpacity': 0.5, 'weight': 2},
    'solaire': {'color': '#ffd700', 'fillColor': '#ffd700', 'fillOpacity': 0.5, 'weight': 2},
    'rpg': {'color': '#228B22', 'fillColor': '#90EE90', 'fillOpacity': 0.3, 'weight': 1},
    'api_cadastre': {'color': '#FF6600', 'fillColor': '#FFE4B5', 'fillOpacity': 0.3, 'weight': 1},
    'api_nature': {'color': '#22AA22', 'fillColor': '#98FB98', 'fillOpacity': 0.3, 'weight': 1},
    'api_urbanisme': {'color': '#0000FF', 'fillColor': '#ADD8E6', 'fillOpacity': 0.3, 'weight': 1},
    'default': {'color': '#3388ff', 'fillColor': '#8cc0ff', 'fillOpacity': 0.3, 'weight': 2}
}

def get_static_style(layer_type='default'):
    """Retourne un style statique pour le type de couche donné"""
    return STATIC_STYLES.get(layer_type, STATIC_STYLES['default'])
'''
    
    # Insérer la section de styles après les imports
    import_end = content.find('\n\n# Configuration')
    if import_end != -1:
        content = content[:import_end] + styles_section + content[import_end:]
    
    # 4. Remplacer les utilisations de styles dynamiques
    content = re.sub(
        r'style_function=lambda x: \{[^}]+\}',
        "style_function=get_static_style('default')",
        content
    )
    
    # Sauvegarder
    with open('agriweb_hebergement_gratuit.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Corrections appliquées à agriweb_hebergement_gratuit.py")

def fix_map1_layer_control():
    """Ajoute le contrôle de couches manquant dans map1.html"""
    
    with open('static/map1.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si le contrôle existe déjà
    if 'L.control.layers' in content:
        print("ℹ️  Le contrôle de couches existe déjà dans map1.html")
        return
    
    # Trouver où insérer le contrôle (après la définition de baseMaps)
    pattern = r'(var baseMaps = \{ "Satellite": sat, "OSM": osm \};)'
    replacement = r'\1\n    L.control.layers(baseMaps).addTo(map);'
    
    content = re.sub(pattern, replacement, content)
    
    with open('static/map1.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Contrôle de couches ajouté à map1.html")

def reset_zoom_defaults():
    """Remet les valeurs de zoom par défaut appropriées"""
    
    # map.html
    with open('static/map.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Changer le setView par défaut
    content = re.sub(r'map\.setView\([^)]+, zoom \|\| 8\)', 'map.setView([lat, lon], zoom || 13)', content)
    
    with open('static/map.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # map1.html
    with open('static/map1.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Assurer que le zoom par défaut est approprié
    content = re.sub(r'\.setView\(\[46\.8, 2\], 6\)', '.setView([46.8, 2], 6)', content)
    
    with open('static/map1.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Valeurs de zoom réinitialisées")

if __name__ == "__main__":
    print("🔧 Correction complète des problèmes de carte...")
    
    fix_agriweb_styles()
    fix_map1_layer_control() 
    reset_zoom_defaults()
    
    print("\n✅ Toutes les corrections ont été appliquées !")
    print("📝 Résumé des corrections :")
    print("   - Styles lambda remplacés par des styles statiques")
    print("   - Contrôle de couches ajouté à map1.html")
    print("   - Zoom par défaut ajusté (12 pour recherche, 13 pour setView)")
    print("\n⚡ Vous pouvez maintenant déployer avec : git add . && git commit -m 'Fix map styles and layer control' && git push production main")
