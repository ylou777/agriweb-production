"""
Test rapide de l'autocomplétion de communes
Démonstration avec exemples de fautes de frappe
"""

import requests
import json

BASE_URL = "http://localhost:5000"
COMMUNE_ENDPOINT = f"{BASE_URL}/api/autocomplete/commune"

def test_commune(query):
    """Test une recherche de commune et affiche les résultats"""
    print(f"\n{'='*70}")
    print(f"🔍 Recherche: '{query}'")
    print('='*70)
    
    try:
        response = requests.get(COMMUNE_ENDPOINT, params={'q': query}, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get('suggestions', [])
            
            print(f"✅ {len(suggestions)} résultats trouvés\n")
            
            for i, sugg in enumerate(suggestions, 1):
                nom = sugg.get('nom', 'N/A')
                cp = sugg.get('code_postal', 'N/A')
                dept = sugg.get('code_departement', 'N/A')
                pop = sugg.get('population', 0)
                pop_formatted = f"{pop:,}".replace(',', ' ') if pop else 'N/A'
                
                print(f"{i}. 🏛️  {nom}")
                print(f"   📮 Code postal: {cp}")
                print(f"   📍 Département: {dept}")
                print(f"   👥 Population: {pop_formatted} habitants")
                
                if sugg.get('lat') and sugg.get('lon'):
                    print(f"   🌍 Coordonnées: {sugg['lat']:.4f}, {sugg['lon']:.4f}")
                print()
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

# ============================================================
# EXEMPLES DE RECHERCHES
# ============================================================

print("\n" + "="*70)
print("🧪 TESTS D'AUTOCOMPLÉTION DE COMMUNES - AgriWeb")
print("="*70)
print("\n💡 Ces tests démontrent la tolérance aux fautes de frappe\n")

# Test 1: Faute de typo classique
test_commune("montiers d'ahun")
input("⏸️  Appuyez sur Entrée pour continuer...")

# Test 2: Commune avec plusieurs résultats
test_commune("verdun")
input("⏸️  Appuyez sur Entrée pour continuer...")

# Test 3: Code postal
test_commune("23150")
input("⏸️  Appuyez sur Entrée pour continuer...")

# Test 4: Grande ville
test_commune("lyon")
input("⏸️  Appuyez sur Entrée pour continuer...")

# Test 5: Recherche partielle
test_commune("moutiers")
input("⏸️  Appuyez sur Entrée pour continuer...")

# Test 6: Commune avec tirets
test_commune("saint-etienne")
input("⏸️  Appuyez sur Entrée pour continuer...")

# Test 7: Sans accent
test_commune("saint-genevieve")
input("⏸️  Appuyez sur Entrée pour continuer...")

# Test 8: Commune avec numéro (arrondissement)
test_commune("paris 15")
input("⏸️  Appuyez sur Entrée pour continuer...")

print("\n" + "="*70)
print("✅ Tests terminés!")
print("="*70)
print("\n📝 NOTES:")
print("   • L'API tolère automatiquement les fautes de frappe")
print("   • Recherche possible par: nom, code postal, ou début de nom")
print("   • Résultats triés par pertinence")
print("   • Minimum 2 caractères requis")
print("   • Maximum 10 suggestions retournées")
print("="*70 + "\n")
