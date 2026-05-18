import sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()
import requests
from mairies_diagnostic import get_parcelles_municipales, _APICARTO

for code, nom in [('23058','Puy-Malsignat'), ('15096','Mandailles-Saint-Julien')]:
    parcelles = get_parcelles_municipales(code)
    if not parcelles:
        print(f"{nom}: 0 parcelles MAJIC")
        continue
    
    # Prendre la 1ère section
    sect = parcelles[0]['section'].strip().upper()
    nums_majic = {p['numero'].strip().zfill(4) for p in parcelles if p['section'].strip().upper() == sect}
    
    # Requête Apicarto section
    r = requests.get(_APICARTO, params={'code_insee': code, 'section': sect, '_limit': 500}, timeout=12)
    features = r.json().get('features', [])
    nums_apicarto = {str(f['properties'].get('numero','')).strip().zfill(4) for f in features}
    
    # Trouver les numéros MAJIC dans Apicarto
    match = nums_majic & nums_apicarto
    print(f"\n{nom} ({code}) section={sect}")
    print(f"  MAJIC numero (zfill4): {sorted(nums_majic)[:5]}")
    print(f"  Apicarto numero (zfill4): {sorted(nums_apicarto)[:5]}")
    print(f"  Intersection : {len(match)}/{len(nums_majic)} parcelles matchent")
    
    # Si 0 match, afficher format brut
    if not match:
        p0 = [p for p in parcelles if p['section'].strip().upper() == sect][0]
        f0 = features[0] if features else None
        print(f"  MAJIC brut  : section='{p0['section']}' numero='{p0['numero']}'")
        if f0:
            print(f"  Apicarto brut: section='{f0['properties'].get('section_prefixe','')}' numero='{f0['properties'].get('numero','')}'")
            print(f"  Toutes props Apicarto: {dict(list(f0['properties'].items())[:10])}")
