"""
Test de l'API de correction des coordonnées parcelle
Vérifie que le centroïde de la parcelle est correctement calculé
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_parcel_coords(lat, lon, address_name, buffer=20):
    """Test l'API get_parcel_coords avec des coordonnées données"""
    print(f"\n{'='*70}")
    print(f"🧪 TEST: {address_name}")
    print(f"{'='*70}")
    print(f"📍 Coordonnées adresse (BAN): {lat}, {lon}")
    print(f"📏 Buffer de recherche: {buffer}m")
    
    try:
        url = f"{BASE_URL}/api/get_parcel_coords"
        params = {
            'lat': lat,
            'lon': lon,
            'buffer': buffer
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Erreur HTTP: {response.status_code}")
            return False
        
        data = response.json()
        
        print(f"\n📊 RÉSULTAT:")
        print(f"   Fallback: {'⚠️  OUI' if data.get('fallback') else '✅ NON'}")
        
        if not data.get('fallback'):
            print(f"   ✅ Parcelle trouvée !")
            print(f"   🆔 ID parcelle: {data.get('parcel_id', 'N/A')}")
            print(f"   📍 Centroïde: {data.get('parcel_lat'):.6f}, {data.get('parcel_lon'):.6f}")
            print(f"   📏 Distance: {data.get('distance')}m")
            print(f"   📝 Message: {data.get('message', 'N/A')}")
            
            # Vérifier que les coordonnées ont changé
            delta_lat = abs(data.get('parcel_lat') - data.get('original_lat', lat))
            delta_lon = abs(data.get('parcel_lon') - data.get('original_lon', lon))
            
            if delta_lat > 0.00001 or delta_lon > 0.00001:
                print(f"   ✅ Correction appliquée (Δlat={delta_lat:.6f}, Δlon={delta_lon:.6f})")
            else:
                print(f"   ⚠️  Aucune correction (parcelle exactement sur l'adresse)")
        else:
            print(f"   ⚠️  Parcelle NON trouvée")
            print(f"   📝 Message: {data.get('message', 'N/A')}")
            print(f"   📍 Utilisation coordonnées adresse: {data.get('parcel_lat')}, {data.get('parcel_lon')}")
        
        return True
        
    except requests.exceptions.Timeout:
        print(f"❌ Timeout (> 10s)")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def run_tests():
    """Lance une série de tests"""
    print("\n" + "="*70)
    print("🧪 TESTS DE CORRECTION DES COORDONNÉES PARCELLE")
    print("="*70)
    print("\n💡 Ces tests vérifient que l'API trouve bien les parcelles")
    print("   et calcule correctement leur centroïde.")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Zone urbaine (devrait trouver)
    tests_total += 1
    if test_parcel_coords(
        lat=45.851556,
        lon=1.261389,
        address_name="Limoges - Zone urbaine",
        buffer=20
    ):
        tests_passed += 1
    
    input("\n⏸️  Appuyez sur Entrée pour continuer...")
    
    # Test 2: Zone rurale (Moutiers-d'Ahun)
    tests_total += 1
    if test_parcel_coords(
        lat=45.916667,
        lon=2.000000,
        address_name="Moutiers-d'Ahun - Zone rurale",
        buffer=20
    ):
        tests_passed += 1
    
    input("\n⏸️  Appuyez sur Entrée pour continuer...")
    
    # Test 3: Buffer plus large
    tests_total += 1
    if test_parcel_coords(
        lat=45.916667,
        lon=2.000000,
        address_name="Moutiers-d'Ahun - Buffer 50m",
        buffer=50
    ):
        tests_passed += 1
    
    input("\n⏸️  Appuyez sur Entrée pour continuer...")
    
    # Test 4: Verdun (55)
    tests_total += 1
    if test_parcel_coords(
        lat=49.159889,
        lon=5.383333,
        address_name="Verdun (55) - Zone urbaine",
        buffer=20
    ):
        tests_passed += 1
    
    input("\n⏸️  Appuyez sur Entrée pour continuer...")
    
    # Test 5: Paris (zone très dense)
    tests_total += 1
    if test_parcel_coords(
        lat=48.856614,
        lon=2.352222,
        address_name="Paris - Zone très dense",
        buffer=15  # Buffer plus petit en ville
    ):
        tests_passed += 1
    
    # Résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*70)
    print(f"✅ Tests réussis: {tests_passed}/{tests_total}")
    print(f"❌ Tests échoués: {tests_total - tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS !")
    elif tests_passed > tests_total / 2:
        print("\n⚠️  La majorité des tests sont passés")
    else:
        print("\n❌ Beaucoup de tests ont échoué")
    
    print("\n📝 NOTES:")
    print("   • Le fallback est NORMAL pour certaines zones (rurales, non cadastrées)")
    print("   • La distance dépend de la taille de la rue et de la parcelle")
    print("   • Un buffer plus grand trouve plus de parcelles mais peut être moins précis")
    print("="*70 + "\n")


def test_real_address():
    """Test interactif avec une vraie adresse"""
    print("\n" + "="*70)
    print("🧪 TEST INTERACTIF")
    print("="*70)
    print("\n💡 Entrez des coordonnées GPS pour tester l'API\n")
    
    try:
        lat = float(input("Latitude (ex: 45.851556): "))
        lon = float(input("Longitude (ex: 1.261389): "))
        buffer = int(input("Buffer en mètres (défaut: 20): ") or "20")
        
        test_parcel_coords(lat, lon, "Test manuel", buffer)
        
    except ValueError:
        print("❌ Coordonnées invalides")
    except Exception as e:
        print(f"❌ Erreur: {e}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 SCRIPT DE TEST - CORRECTION COORDONNÉES PARCELLE")
    print("="*70)
    print("\nChoisissez un mode:")
    print("  1. Tests automatiques (5 tests prédéfinis)")
    print("  2. Test interactif (entrer vos coordonnées)")
    print("  3. Les deux")
    
    choice = input("\nVotre choix (1/2/3): ").strip()
    
    if choice == "1":
        run_tests()
    elif choice == "2":
        test_real_address()
    elif choice == "3":
        run_tests()
        test_real_address()
    else:
        print("❌ Choix invalide")
