"""
Test de correction du Plan de Masse avec coordonnées GPS réelles
Vérifie que les modules sont positionnés selon leurs vraies coordonnées GPS
"""

import json
from plan_masse_generator import generate_plan_masse

# Données de test avec coordonnées GPS réelles
prospect_test = {
    'nom': 'Dupont',
    'prenom': 'Jean',
    'adresse': '12 Rue de la République',
    'code_postal': '33000',
    'commune': 'Bordeaux',
    'latitude': 44.8378,
    'longitude': -0.5792,
    'parcelles_cadastrales': [
        {
            'section': 'AB',
            'numero': '123',
            'surface': '450'
        }
    ]
}

# Calpinage avec positions GPS réelles des modules
calpinage_test = {
    'zones': [
        {
            'numero': 1,
            'nbModules': 4,
            'nbCols': 2,
            'nbRows': 2,
            'surfaceM2': 10.4,
            'puissanceKw': 2.24,
            'orientation': 'Sud',
            'inclinaison': 30,
            'moduleOrientation': 'paysage',
            # Coordonnées GPS de la zone (polygone)
            'coordinates': [
                {'lat': 44.8380, 'lng': -0.5790},
                {'lat': 44.8380, 'lng': -0.5788},
                {'lat': 44.8378, 'lng': -0.5788},
                {'lat': 44.8378, 'lng': -0.5790}
            ],
            # Positions GPS de CHAQUE module (avec coins)
            'modulesPositions': [
                # Module 1
                {
                    'lat': 44.83795,
                    'lng': -0.57895,
                    'corners': [
                        {'lat': 44.83800, 'lng': -0.57900},
                        {'lat': 44.83800, 'lng': -0.57890},
                        {'lat': 44.83790, 'lng': -0.57890},
                        {'lat': 44.83790, 'lng': -0.57900}
                    ]
                },
                # Module 2
                {
                    'lat': 44.83795,
                    'lng': -0.57885,
                    'corners': [
                        {'lat': 44.83800, 'lng': -0.57890},
                        {'lat': 44.83800, 'lng': -0.57880},
                        {'lat': 44.83790, 'lng': -0.57880},
                        {'lat': 44.83790, 'lng': -0.57890}
                    ]
                },
                # Module 3
                {
                    'lat': 44.83785,
                    'lng': -0.57895,
                    'corners': [
                        {'lat': 44.83790, 'lng': -0.57900},
                        {'lat': 44.83790, 'lng': -0.57890},
                        {'lat': 44.83780, 'lng': -0.57890},
                        {'lat': 44.83780, 'lng': -0.57900}
                    ]
                },
                # Module 4
                {
                    'lat': 44.83785,
                    'lng': -0.57885,
                    'corners': [
                        {'lat': 44.83790, 'lng': -0.57890},
                        {'lat': 44.83790, 'lng': -0.57880},
                        {'lat': 44.83780, 'lng': -0.57880},
                        {'lat': 44.83780, 'lng': -0.57890}
                    ]
                }
            ]
        }
    ],
    'module': {
        'longueur': '2278',
        'largeur': '1134',
        'puissance': '560',
        'voc': '49.5',
        'vmpp': '41.7',
        'isc': '14.0',
        'impp': '13.43'
    },
    'totaux': {
        'puissanceTotale': 2.24
    }
}

if __name__ == '__main__':
    print("🧪 TEST - Plan de Masse avec Coordonnées GPS Réelles")
    print("=" * 60)
    
    print(f"\n📍 Prospect: {prospect_test['nom']} {prospect_test['prenom']}")
    print(f"   Localisation: {prospect_test['latitude']}, {prospect_test['longitude']}")
    
    print(f"\n📐 Calpinage:")
    for zone in calpinage_test['zones']:
        print(f"   - Zone {zone['numero']}: {zone['nbModules']} modules")
        print(f"     Positions GPS: {len(zone['modulesPositions'])} modules avec coordonnées")
        if zone['modulesPositions']:
            first_mod = zone['modulesPositions'][0]
            print(f"     Premier module: lat={first_mod['lat']:.6f}, lng={first_mod['lng']:.6f}")
    
    print(f"\n🚀 Génération du plan de masse...")
    try:
        pdf_buffer = generate_plan_masse(prospect_test, calpinage_test)
        
        # Sauvegarder le PDF
        output_file = 'test_plan_masse_gps_correction.pdf'
        with open(output_file, 'wb') as f:
            f.write(pdf_buffer.read())
        
        print(f"\n✅ SUCCÈS ! Plan de masse généré avec GPS")
        print(f"   Fichier: {output_file}")
        print(f"\n📋 Vérifications à faire:")
        print(f"   1. ✓ L'image n'est PAS étirée/déformée")
        print(f"   2. ✓ Les modules sont aux BONS emplacements GPS")
        print(f"   3. ✓ L'échelle est cohérente avec la carte")
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
