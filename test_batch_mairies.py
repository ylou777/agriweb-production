"""
Test batch sur ~10 communes aléatoires de taille et région variées.
Mesure : parcelles MAJIC, parkings, bâtiments, puissance, temps d'exécution.
"""

import json
import os
import time
import traceback

# ── 10 communes variées (taille / région / département) ──────────────────────
COMMUNES = [
    # Petites communes rurales
    {'nom_commune': 'Aurillac',       'code_insee': '15014', 'lat': 44.9277,  'lon': 2.4461,  'population':  26000, 'departement': '15'},
    {'nom_commune': 'Rodez',          'code_insee': '12202', 'lat': 44.3507,  'lon': 2.5728,  'population':  24000, 'departement': '12'},
    {'nom_commune': 'Mende',          'code_insee': '48095', 'lat': 44.5202,  'lon': 3.4992,  'population':  12000, 'departement': '48'},
    {'nom_commune': 'Digne-les-Bains','code_insee': '04070', 'lat': 44.0921,  'lon': 6.2359,  'population':  16000, 'departement': '04'},
    {'nom_commune': 'Gap',            'code_insee': '05061', 'lat': 44.5594,  'lon': 6.0782,  'population':  40000, 'departement': '05'},
    # Villes moyennes
    {'nom_commune': 'Alençon',        'code_insee': '61001', 'lat': 48.4296,  'lon': 0.0931,  'population':  26000, 'departement': '61'},
    {'nom_commune': 'Châteauroux',    'code_insee': '36044', 'lat': 46.8099,  'lon': 1.6909,  'population':  44000, 'departement': '36'},
    {'nom_commune': 'Privas',         'code_insee': '07186', 'lat': 44.7352,  'lon': 4.5976,  'population':   8000, 'departement': '07'},
    # Commune avec MAJIC potentiellement limité
    {'nom_commune': 'Foix',           'code_insee': '09122', 'lat': 42.9641,  'lon': 1.6060,  'population':  10000, 'departement': '09'},
    {'nom_commune': 'Tulle',          'code_insee': '19272', 'lat': 45.2671,  'lon': 1.7710,  'population':  14000, 'departement': '19'},
]

# ── Import des modules ─────────────────────────────────────────────────────────
from mairies_diagnostic import build_commune_diagnostic, diagnostic_summary
from mairies_campaign import build_email_html, BASE_URL, _build_obligations

OUT_DIR = os.path.dirname(__file__)

results = []

print("=" * 70)
print(f"  TEST BATCH — {len(COMMUNES)} communes")
print("=" * 70)
print(f"{'Commune':<22} {'Parcelles':>9} {'Parkings':>9} {'Bâtiments':>9} {'kWc':>8} {'Durée':>7}  Statut")
print("-" * 70)

for i, commune in enumerate(COMMUNES):
    nom    = commune['nom_commune']
    insee  = commune['code_insee']
    t0     = time.time()
    status = "OK"
    diag_full = None

    try:
        diag_full = build_commune_diagnostic(
            code_insee=insee,
            nom_commune=nom,
            lat=commune['lat'],
            lon=commune['lon'],
            max_parcelles=30,
        )
        duree = time.time() - t0

        print(f"{nom:<22} {diag_full['nb_parcelles']:>9} {diag_full['nb_parkings']:>9} "
              f"{diag_full['nb_batiments']:>9} {diag_full['puissance_totale_kwc']:>8.0f} "
              f"{duree:>6.1f}s  {status}")

        # Génère l'email HTML pour cette commune
        slug = nom.lower().replace(' ', '-')
        recipient = {**commune, 'id': f"test-{insee}", 'email': f'mairie@{slug}.fr', 'nom_maire': 'M. le Maire'}
        diag_email = diagnostic_summary(diag_full)
        diag_email['obligations'] = _build_obligations(commune.get('population', 0))
        diag_email['lat'] = commune['lat']
        diag_email['lon'] = commune['lon']
        diag_email['source'] = 'majic'

        email_html = build_email_html(
            recipient=recipient,
            diag=diag_email,
            tracking_pixel_url=f"{BASE_URL}/campaign/open/test-{insee}",
            cta_url=f"{BASE_URL}/diagnostic",
            plan_url=f"{BASE_URL}/campaign/plan/test-{insee}",
            diag_full=diag_full,
        )
        out_path = os.path.join(OUT_DIR, f"test_email_{insee}.html")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(email_html)

        results.append({
            'commune':    nom,
            'insee':      insee,
            'parcelles':  diag_full['nb_parcelles'],
            'parkings':   diag_full['nb_parkings'],
            'batiments':  diag_full['nb_batiments'],
            'kwc':        diag_full['puissance_totale_kwc'],
            'economie':   diag_full['economie_totale'],
            'duree_s':    round(duree, 1),
            'status':     status,
            'html':       f"test_email_{insee}.html",
        })

    except Exception as exc:
        duree = time.time() - t0
        status = f"ERREUR: {str(exc)[:50]}"
        print(f"{nom:<22} {'—':>9} {'—':>9} {'—':>9} {'—':>8} {duree:>6.1f}s  {status}")
        results.append({'commune': nom, 'insee': insee, 'status': status, 'duree_s': round(duree, 1)})
        traceback.print_exc()

print("=" * 70)

# ── Résumé JSON ───────────────────────────────────────────────────────────────
print("\n  RÉSUMÉ JSON\n")
print(json.dumps(results, indent=2, ensure_ascii=False, default=str))

ok = [r for r in results if r.get('status') == 'OK']
print(f"\n  ✅ {len(ok)}/{len(COMMUNES)} communes OK")
if ok:
    print(f"  Parcelles moy.  : {sum(r['parcelles'] for r in ok)/len(ok):.0f}")
    print(f"  Parkings moy.   : {sum(r['parkings'] for r in ok)/len(ok):.1f}")
    print(f"  Bâtiments moy.  : {sum(r['batiments'] for r in ok)/len(ok):.1f}")
    print(f"  kWc moy.        : {sum(r['kwc'] for r in ok)/len(ok):.0f}")
    print(f"  Durée moy.      : {sum(r['duree_s'] for r in ok)/len(ok):.1f}s")
    print(f"\n  Fichiers HTML générés :")
    for r in ok:
        print(f"    {r['html']}")
