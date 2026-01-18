"""
Vérification rapide: les parcelles cadastrales sont-elles bien dans le PDF ?
"""

from declaration_prealable_generator import DeclarationPrealableGenerator
from test_declaration_prealable import prospect_test

# Afficher les parcelles détectées
gen = DeclarationPrealableGenerator(prospect_test)
parcelles = gen._extract_parcelles()

print("\n" + "="*70)
print("🔍 VÉRIFICATION PARCELLES CADASTRALES")
print("="*70)

print(f"\n📊 Données prospect:")
print(f"   parcelles_cadastrales: {prospect_test.get('parcelles_cadastrales')}")

print(f"\n📋 Parcelles extraites par _extract_parcelles():")
print(f"   Nombre: {len(parcelles)}")
for i, p in enumerate(parcelles, 1):
    section = p.get('section', '')
    numero = p.get('numero', '')
    surface = p.get('surface', '')
    print(f"   {i}. Section {section} N°{numero} - {surface} m²")

print(f"\n✅ Ces {len(parcelles)} parcelles devraient apparaître dans:")
print(f"   - CERFA 13703*09 (Cadre 2 - Localisation)")
print(f"   - Plan DP2 (mention cadastrale)")

print("\n💡 Ouvrez 'DP_Formulaire_CERFA_13703.pdf' pour vérifier visuellement")
print("   Cherchez dans le cadre '2. LOCALISATION DU TERRAIN'")
print("="*70 + "\n")
