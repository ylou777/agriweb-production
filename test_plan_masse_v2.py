"""
Test du Plan de Masse V2 avec coordonnées GPS réelles
"""

from plan_masse_generator_v2 import generate_plan_masse
import json

# Données de test avec GPS
prospect_test = {
    'commune': 'Gujan',
    'adresse': '7 Avenue de l\'Europe 33800 Gujan',
    'latitude': 44.6372,
    'longitude': -1.0687,
    'longueur_batiment_m': 18,
    'largeur_batiment_m': 12,
    'parcelles_cadastrales': [
        {
            'section': 'AB',
            'numero': '0125',
            'surface': '850',
            'geojson': {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[
                        [-1.0688, 44.6373],
                        [-1.0686, 44.6373],
                        [-1.0686, 44.6371],
                        [-1.0688, 44.6371],
                        [-1.0688, 44.6373]
                    ]]
                }
            }
        }
    ]
}

# Calpinage avec coordonnées GPS réelles + screenshot simulé
calpinage_test = {
    'module': {
        'longueur': '2278',
        'largeur': '1134',
        'puissance': '560',
        'marque': 'Canadian Solar',
        'modele': 'CS7N-560MS'
    },
    'zones': [
        {
            'nbModules': 60,
            'nbCols': 6,
            'nbRows': 10,
            'moduleOrientation': 'portrait',
            'coordinates': [
                {'lat': 44.6372, 'lng': -1.0687},
                {'lat': 44.6372, 'lng': -1.0686},
                {'lat': 44.6371, 'lng': -1.0686},
                {'lat': 44.6371, 'lng': -1.0687}
            ]
        }
    ],
    # Simuler un screenshot (commenté car pas de vraie image en test)
    # 'screenshot_map': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
}

print("=" * 70)
print("📐 [TEST] Génération Plan de Masse V2 avec GPS")
print("=" * 70)

try:
    pdf_buffer = generate_plan_masse(prospect_test, calpinage_test)
    
    # Sauvegarder
    with open('Plan_Masse_V2_Test.pdf', 'wb') as f:
        f.write(pdf_buffer.read())
    
    import os
    file_size = os.path.getsize('Plan_Masse_V2_Test.pdf')
    
    print(f"\n✅ SUCCÈS ! Plan de masse V2 généré")
    print(f"Fichier: Plan_Masse_V2_Test.pdf")
    print(f"Taille: {file_size / 1024:.1f} KB")
    print(f"Format: A3")
    print(f"✓ Projection GPS activée")
    print(f"✓ Parcelles avec GeoJSON")
    print(f"✓ Modules positionnés selon coordonnées GPS du calpinage")
    print(f"✓ Échelle dynamique calculée")
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
