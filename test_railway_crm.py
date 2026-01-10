"""
Test rapide de l'API CRM déployée sur Railway
"""
import requests

# URL de votre application Railway
BASE_URL = "https://ample-manifestation-production-7b1a.up.railway.app"

print("=" * 80)
print("🚀 TEST API CRM SUR RAILWAY")
print("=" * 80)

# Test 1: Récupérer les prospects
print("\n📊 Test 1: Récupération des prospects...")
try:
    response = requests.get(f"{BASE_URL}/api/crm/prospects", timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            prospects = data.get('prospects', [])
            stats = data.get('stats', {})
            
            print(f"✅ Succès!")
            print(f"\n📈 Statistiques:")
            print(f"   Total prospects: {stats.get('total', 0)}")
            print(f"   Parkings: {stats.get('parkings', 0)}")
            print(f"   Toitures: {stats.get('toitures', 0)}")
            print(f"   Friches: {stats.get('friches', 0)}")
            print(f"   RPG: {stats.get('rpg', 0)}")
            
            if prospects:
                print(f"\n📄 Exemples (3 premiers):")
                for i, p in enumerate(prospects[:3], 1):
                    print(f"\n   Prospect {i}:")
                    print(f"   ID: {p.get('id')}")
                    print(f"   Type: {p.get('type')}")
                    print(f"   Commune: {p.get('commune')}")
                    print(f"   Nom: {p.get('nom_prospect')}")
                    print(f"   Contact: {p.get('contact_nom')}")
                    print(f"   Téléphone: {p.get('contact_tel')} (mappé)")
                    print(f"   Téléphone (BDD): {p.get('contact_telephone')}")
                    print(f"   Email: {p.get('contact_email')}")
                    print(f"   Statut: {p.get('statut')}")
            else:
                print("\n⚠️ Aucun prospect trouvé sur Railway")
        else:
            print(f"❌ Erreur API: {data.get('error')}")
    else:
        print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
except requests.exceptions.Timeout:
    print("❌ Timeout - L'application Railway met trop de temps à répondre")
except requests.exceptions.RequestException as e:
    print(f"❌ Erreur de connexion: {e}")

# Test 2: Vérifier que le CRM est accessible
print("\n\n🌐 Test 2: Accès à l'interface CRM...")
try:
    response = requests.get(f"{BASE_URL}/crm", timeout=10)
    if response.status_code == 200:
        print("✅ Interface CRM accessible")
    else:
        print(f"⚠️ Status {response.status_code}")
except Exception as e:
    print(f"❌ Erreur: {e}")

# Test 3: Stats CRM
print("\n\n📊 Test 3: Statistiques CRM...")
try:
    response = requests.get(f"{BASE_URL}/api/crm/stats", timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            stats = data.get('stats', {})
            print(f"✅ Stats récupérées:")
            print(f"   Total: {stats.get('total', 0)}")
            print(f"   Nouveau: {stats.get('nouveau', 0)}")
            print(f"   Contacté: {stats.get('contacte', 0)}")
            print(f"   Qualifié: {stats.get('qualifie', 0)}")
            print(f"   Perdu: {stats.get('perdu', 0)}")
        else:
            print(f"❌ Erreur: {data.get('error')}")
    else:
        print(f"⚠️ Status {response.status_code}")
except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n" + "=" * 80)
print("✅ Tests terminés")
print("=" * 80)
