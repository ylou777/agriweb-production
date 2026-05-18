import sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()
from mairies_diagnostic import get_parcelles_municipales, _apicarto_parcelle, enrich_parcelles_with_geometry

for code, nom in [('23058','Puy-Malsignat'), ('15096','Mandailles-Saint-Julien')]:
    parcelles = get_parcelles_municipales(code)
    print(f"\n{nom} ({code}) : {len(parcelles)} parcelles MAJIC")
    if parcelles:
        # Tester Apicarto sur les 3 premières
        ok, fail = 0, 0
        for p in parcelles[:5]:
            try:
                result = _apicarto_parcelle(code, p['section'], p['numero'])
                if result:
                    ok += 1
                    print(f"  OK  section={p['section']} num={p['numero']} → geom={result.get('geometry',{}).get('type','?')}")
                else:
                    fail += 1
                    print(f"  VIDE section={p['section']} num={p['numero']}")
            except Exception as e:
                fail += 1
                print(f"  ERR section={p['section']} num={p['numero']} : {e}")
        print(f"  Résultat : {ok} géom OK / {fail} échecs sur 5 tests")
