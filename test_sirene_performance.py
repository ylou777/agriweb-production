"""
Test de performance de l'API Sirene
Mesure le temps de réponse moyen et le taux de succès
"""

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean, median

# SIRET réels d'entreprises agricoles à tester
TEST_SIRETS = [
    "31252693800047",
    "44306184100047", 
    "89207591800018",
    "34957951600015",
    "38260949300012",
    "44150267100015",
    "51114554200011",
    "88449338800018",
    "92232968500015",
    "31360748300028",
    "33142943100017",
    "33357444000017",
    "37821617000019",
    "38171304900017",
    "38201140100017",
    "38881267900016",
    "39437277500012",
    "31714551400020",
    "32885708100017",
    "42157047400047"
]

def test_single_siret(siret, timeout=5):
    """Test un seul SIRET et mesure le temps"""
    url = f"https://entreprise.data.gouv.fr/api/sirene/v3/etablissements/{siret}"
    
    start = time.time()
    try:
        response = requests.get(url, timeout=timeout)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            return {
                'siret': siret,
                'success': True,
                'time': elapsed,
                'status': 200
            }
        else:
            return {
                'siret': siret,
                'success': False,
                'time': elapsed,
                'status': response.status_code
            }
    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        return {
            'siret': siret,
            'success': False,
            'time': elapsed,
            'status': 'TIMEOUT'
        }
    except requests.exceptions.ConnectionError as e:
        elapsed = time.time() - start
        error_str = str(e)
        if "10061" in error_str:
            status = 'REFUSED'
        elif "10054" in error_str:
            status = 'RESET'
        else:
            status = 'CONN_ERROR'
        return {
            'siret': siret,
            'success': False,
            'time': elapsed,
            'status': status
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            'siret': siret,
            'success': False,
            'time': elapsed,
            'status': f'ERROR: {type(e).__name__}'
        }

def test_sequential(sirets, timeout=5):
    """Test séquentiel (un par un)"""
    print("\n" + "="*80)
    print("TEST 1: SÉQUENTIEL (un SIRET à la fois)")
    print("="*80)
    
    results = []
    start_total = time.time()
    
    for i, siret in enumerate(sirets, 1):
        print(f"  [{i}/{len(sirets)}] Test SIRET {siret}...", end=" ")
        result = test_single_siret(siret, timeout)
        results.append(result)
        
        if result['success']:
            print(f"✓ OK ({result['time']:.2f}s)")
        else:
            print(f"✗ {result['status']} ({result['time']:.2f}s)")
    
    total_time = time.time() - start_total
    
    return results, total_time

def test_parallel(sirets, timeout=5, workers=10):
    """Test en parallèle (plusieurs simultanément)"""
    print("\n" + "="*80)
    print(f"TEST 2: PARALLÈLE ({workers} threads simultanés)")
    print("="*80)
    
    results = []
    start_total = time.time()
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_siret = {
            executor.submit(test_single_siret, siret, timeout): siret 
            for siret in sirets
        }
        
        completed = 0
        for future in as_completed(future_to_siret):
            result = future.result()
            results.append(result)
            completed += 1
            
            status = "✓" if result['success'] else "✗"
            print(f"  [{completed}/{len(sirets)}] {status} SIRET {result['siret']}: "
                  f"{result['status']} ({result['time']:.2f}s)")
    
    total_time = time.time() - start_total
    
    return results, total_time

def print_statistics(results, total_time, test_name):
    """Affiche les statistiques"""
    print(f"\n{'─'*80}")
    print(f"STATISTIQUES - {test_name}")
    print(f"{'─'*80}")
    
    success_count = sum(1 for r in results if r['success'])
    success_rate = (success_count / len(results)) * 100 if results else 0
    
    times = [r['time'] for r in results]
    success_times = [r['time'] for r in results if r['success']]
    
    print(f"  Total requêtes    : {len(results)}")
    print(f"  Succès            : {success_count} ({success_rate:.1f}%)")
    print(f"  Échecs            : {len(results) - success_count}")
    print(f"  Temps total       : {total_time:.2f}s")
    print(f"  Temps moyen/req   : {mean(times):.2f}s")
    print(f"  Temps médian      : {median(times):.2f}s")
    
    if success_times:
        print(f"  Temps moyen (OK)  : {mean(success_times):.2f}s")
        print(f"  Temps min (OK)    : {min(success_times):.2f}s")
        print(f"  Temps max (OK)    : {max(success_times):.2f}s")
    
    # Répartition des erreurs
    error_types = {}
    for r in results:
        if not r['success']:
            status = str(r['status'])
            error_types[status] = error_types.get(status, 0) + 1
    
    if error_types:
        print(f"\n  Types d'erreurs:")
        for error, count in sorted(error_types.items(), key=lambda x: -x[1]):
            print(f"    - {error}: {count}")

def estimate_time_for_932(avg_time_seq, avg_time_parallel, workers=20):
    """Estime le temps pour 932 éleveurs"""
    print(f"\n{'='*80}")
    print(f"ESTIMATION POUR 932 ÉLEVEURS")
    print(f"{'='*80}")
    
    time_seq = 932 * avg_time_seq
    time_parallel = (932 / workers) * avg_time_parallel
    
    print(f"\n  Mode SÉQUENTIEL:")
    print(f"    Temps estimé: {time_seq:.0f}s = {time_seq/60:.1f} minutes")
    
    print(f"\n  Mode PARALLÈLE ({workers} threads):")
    print(f"    Temps estimé: {time_parallel:.0f}s = {time_parallel/60:.1f} minutes")
    print(f"    Gain de temps: {(time_seq - time_parallel):.0f}s = {(time_seq - time_parallel)/60:.1f} minutes")
    print(f"    Accélération: x{time_seq/time_parallel:.1f}")

def main():
    print("="*80)
    print("TEST DE PERFORMANCE API SIRENE")
    print(f"Nombre de SIRET à tester: {len(TEST_SIRETS)}")
    print("="*80)
    
    # Test avec timeout de 0.5s (ce qu'on utilise dans le code)
    timeout = 0.5
    print(f"\nTimeout configuré: {timeout}s")
    
    # Test séquentiel
    results_seq, time_seq = test_sequential(TEST_SIRETS[:10], timeout)
    print_statistics(results_seq, time_seq, "SÉQUENTIEL (10 SIRET)")
    
    # Test parallèle avec 10 workers
    print("\n" + "⏳ Attente 2s avant test parallèle...")
    time.sleep(2)
    
    results_par, time_par = test_parallel(TEST_SIRETS[:10], timeout, workers=10)
    print_statistics(results_par, time_par, "PARALLÈLE 10 threads (10 SIRET)")
    
    # Calcul temps moyen
    if results_seq:
        avg_time_seq = mean([r['time'] for r in results_seq])
        avg_time_par = mean([r['time'] for r in results_par])
        
        estimate_time_for_932(avg_time_seq, avg_time_par, workers=20)
    
    # Recommandations
    print(f"\n{'='*80}")
    print("RECOMMANDATIONS")
    print(f"{'='*80}")
    
    success_rate = (sum(1 for r in results_par if r['success']) / len(results_par)) * 100
    
    if success_rate > 80:
        print("\n✅ API Sirene fonctionne correctement")
        print("   → Utiliser le mode PARALLÈLE avec 20 threads")
        print("   → Temps estimé pour 932 éleveurs: 20-30 secondes")
    elif success_rate > 20:
        print("\n⚠️ API Sirene instable")
        print("   → Mode parallèle OK mais beaucoup d'échecs")
        print("   → Le cache évitera de retester les mêmes SIRET")
        print("   → Certains éleveurs n'auront pas de données Sirene")
    else:
        print("\n❌ API Sirene actuellement inaccessible")
        print("   → Désactiver temporairement l'enrichissement Sirene")
        print("   → OU: Réduire timeout à 0.3s et accepter 0% de succès")
        print("   → Les rapports fonctionneront sans données Sirene")

if __name__ == "__main__":
    main()
