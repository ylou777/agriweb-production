"""
Script de diagnostic CRM PostgreSQL
Vérifier l'état de la base de données CRM sur Railway
"""
import requests
import json

# URL de votre application Railway
RAILWAY_URL = "https://ample-manifestation-production-7b1a.up.railway.app"

print("=" * 80)
print("🔍 DIAGNOSTIC CRM POSTGRESQL RAILWAY")
print("=" * 80)

# 1. Vérifier les statistiques CRM
print("\n📊 Récupération des statistiques CRM...")
try:
    response = requests.get(f"{RAILWAY_URL}/api/crm/stats", timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            stats = data.get('stats', {})
            print(f"✅ Total prospects: {stats.get('total', 0)}")
            print(f"📈 Par statut: {stats.get('by_status', {})}")
            print(f"📊 Par type: {stats.get('by_type', {})}")
        else:
            print(f"❌ Erreur API: {data.get('error')}")
    else:
        print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
except Exception as e:
    print(f"❌ Erreur requête: {e}")

# 2. Récupérer les prospects
print("\n👥 Récupération de la liste des prospects...")
try:
    response = requests.get(f"{RAILWAY_URL}/api/crm/prospects", timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            prospects = data.get('prospects', [])
            print(f"✅ {len(prospects)} prospects trouvés")
            if prospects:
                print("\n🔍 Premiers prospects:")
                for p in prospects[:5]:
                    print(f"  - #{p.get('id')}: {p.get('type')} à {p.get('commune')} ({p.get('statut')})")
        else:
            print(f"❌ Erreur API: {data.get('error')}")
    else:
        print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
except Exception as e:
    print(f"❌ Erreur requête: {e}")

# 3. Tester un export
print("\n📤 Test d'export vers CRM...")
test_export = {
    "prospectData": {
        "type": "test",
        "commune": "TEST",
        "departement": "00",
        "adresse": "Test address",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "surface_m2": 100,
        "surface_ha": 0.01,
        "parcelles": ["TEST001"],
        "poste_bt_proche": {
            "distance_m": 50,
            "nom": "Test BT"
        },
        "poste_hta_proche": {
            "distance_m": 200,
            "nom": "Test HTA"
        },
        "lien_streetview": "",
        "lien_annuaire": "",
        "priorite": "test"
    }
}

try:
    response = requests.post(
        f"{RAILWAY_URL}/api/crm/export",
        json=test_export,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ Prospect test créé avec ID: {data.get('prospect_id')}")
        else:
            print(f"❌ Erreur export: {data.get('error')}")
    else:
        print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
except Exception as e:
    print(f"❌ Erreur requête: {e}")

print("\n" + "=" * 80)
print("✅ Diagnostic terminé")
print("=" * 80)
