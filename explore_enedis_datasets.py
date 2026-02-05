"""
Explorer les datasets disponibles sur l'API Enedis Open Data
"""
import requests
import json

def list_enedis_datasets():
    """Liste tous les datasets disponibles sur Enedis Open Data"""
    
    base_url = "https://opendata.enedis.fr/data-fair/api/v1/datasets"
    
    print("🔍 Recherche des datasets Enedis disponibles...\n")
    
    try:
        # Récupérer la liste des datasets
        response = requests.get(base_url, params={'size': 100}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            datasets = data.get('results', [])
            
            print(f"✅ {len(datasets)} datasets trouvés\n")
            print("="*80)
            
            # Filtrer ceux qui contiennent "consommation" ou "entreprise"
            relevant = []
            for ds in datasets:
                title = ds.get('title', '')
                id_ds = ds.get('id', '')
                description = ds.get('description', '')
                count = ds.get('count', 0)
                
                if any(word in title.lower() for word in ['consommation', 'entreprise', 'autoconso', 'collective']):
                    relevant.append(ds)
                    print(f"📊 {title}")
                    print(f"   ID: {id_ds}")
                    print(f"   Enregistrements: {count:,}")
                    print(f"   Description: {description[:150]}...")
                    print("-"*80)
            
            print(f"\n💡 {len(relevant)} datasets pertinents trouvés")
            
            # Tester le dataset principal
            if relevant:
                print("\n" + "="*80)
                print("🧪 Test du premier dataset pertinent")
                print("="*80)
                
                ds = relevant[0]
                test_dataset(ds['id'])
            
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")


def test_dataset(dataset_id):
    """Teste un dataset spécifique"""
    
    url = f"https://opendata.enedis.fr/data-fair/api/v1/datasets/{dataset_id}"
    
    print(f"\n📡 Test de: {dataset_id}")
    
    try:
        # Récupérer quelques enregistrements
        response = requests.get(f"{url}/lines", params={'size': 3}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            total = data.get('total', 0)
            
            print(f"✅ Total d'enregistrements: {total:,}")
            print(f"📋 Échantillon de {len(results)} enregistrements:\n")
            
            if results:
                # Afficher les colonnes disponibles
                sample = results[0]
                print("Colonnes disponibles:")
                for key in sample.keys():
                    val = sample[key]
                    if isinstance(val, str) and len(val) > 50:
                        val = val[:50] + "..."
                    print(f"  - {key}: {val}")
                
                print("\n" + "-"*80)
                
                # Vérifier s'il y a des coordonnées GPS
                has_gps = any('geo' in key.lower() or 'lat' in key.lower() or 'lon' in key.lower() for key in sample.keys())
                print(f"\n{'✅' if has_gps else '❌'} Coordonnées GPS disponibles: {has_gps}")
                
                return True
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


if __name__ == "__main__":
    list_enedis_datasets()
