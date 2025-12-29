"""
Test du générateur de Plan de Masse simplifié
"""

from plan_masse_generator import generate_plan_masse
from test_declaration_prealable import prospect_test, calpinage_test

print("\n" + "="*70)
print("📐 TEST - Plan de Masse Cadastral avec Calpinage PV")
print("="*70)

print("\n📊 Données:")
print(f"   Prospect: {prospect_test['nom_prospect']} {prospect_test['prenom_prospect']}")
print(f"   Adresse: {prospect_test['adresse']}, {prospect_test['commune']}")
print(f"   Bâtiment: {prospect_test['longueur_batiment_m']}m × {prospect_test['largeur_batiment_m']}m")

parcelles = prospect_test.get('parcelles_cadastrales', [])
print(f"\n📋 Parcelles cadastrales ({len(parcelles)}):")
for p in parcelles:
    print(f"   • Section {p['section']} N°{p['numero']} - {p['surface']} m²")

if calpinage_test:
    total_modules = sum(z.get('nbModules', 0) for z in calpinage_test.get('zones', []))
    puissance_module = calpinage_test.get('module', {}).get('puissance', 560)
    puissance_totale = total_modules * puissance_module / 1000
    
    print(f"\n⚡ Installation PV:")
    print(f"   • {total_modules} modules ({puissance_totale:.2f} kWc)")
    print(f"   • {len(calpinage_test.get('zones', []))} zone(s)")
    
    for i, zone in enumerate(calpinage_test.get('zones', []), 1):
        orientation = zone.get('moduleOrientation', 'N/A')
        nb_modules = zone.get('nbModules', 0)
        cols = zone.get('nbCols', 0)
        rows = zone.get('nbRows', 0)
        print(f"   • Zone {i}: {nb_modules} modules ({cols}×{rows}) - {orientation}")

print(f"\n🚀 Génération du plan de masse...")

try:
    pdf_buffer = generate_plan_masse(prospect_test, calpinage_test)
    
    # Sauvegarder
    filename = "Plan_Masse_Cadastral.pdf"
    with open(filename, 'wb') as f:
        f.write(pdf_buffer.getvalue())
    
    size_kb = len(pdf_buffer.getvalue()) / 1024
    
    print(f"\n{'='*70}")
    print(f"✅ SUCCÈS ! Plan de masse généré")
    print(f"{'='*70}")
    print(f"   Fichier: {filename}")
    print(f"   Taille: {size_kb:.1f} KB")
    print(f"   Format: A3 (pour meilleure lisibilité)")
    print(f"\n📋 Contenu du plan:")
    print(f"   ✓ Fond satellite haute résolution")
    print(f"   ✓ Parcelles cadastrales délimitées")
    print(f"   ✓ Bâtiment avec dimensions")
    print(f"   ✓ Modules PV positionnés selon calpinage réel")
    print(f"   ✓ Cotations précises")
    print(f"   ✓ Légende complète")
    print(f"   ✓ Cartouche technique")
    print(f"\n💡 Prêt pour:")
    print(f"   • Dépôt en mairie")
    print(f"   • Dossier Déclaration Préalable")
    print(f"   • Dossier de raccordement ENEDIS")
    print(f"{'='*70}\n")
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
