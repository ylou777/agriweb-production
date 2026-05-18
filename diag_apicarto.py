import sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv; load_dotenv()
from mairies_diagnostic import get_parcelles_municipales, _apicarto_parcelle, enrich_parcelles_with_geometry

for code, nom in [('23058','Puy-Malsignat'), ('15096','Mandailles-Saint-Julien')]:
    parcelles = get_parcelles_municipales(code)
    print(f"\n{nom} ({code}) : {len(parcelles)} parcelles MAJIC")
    if parcelles:
        # Tester les 3 premières
        for p in parcelles[:3]:
            sec = p['section']
            num = p['numero']
            result = _apicarto_parcelle(code, sec, num)
            print(f"  Apicarto {code}/{sec}/{num} -> {'OK geom' if result and result.get('geometry') else 'ECHEC'}")
            if result:
                print(f"    surface_ign={result.get('surface_ign')} lat={result.get('lat')}")
