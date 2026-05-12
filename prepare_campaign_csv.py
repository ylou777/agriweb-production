"""
prepare_campaign_csv.py
=======================
Extrait les mairies depuis mairies_france_complet_20251022_1327.xlsx,
enrichit avec code_insee + population via geo.api.gouv.fr,
et produit un CSV prêt pour import_mairies_csv().

Usage :
    python prepare_campaign_csv.py --depts 23,19,15 --out mairies_campagne_23_19_15.csv
    python prepare_campaign_csv.py --depts 23       --dry-run   # 5 communes, test rapide
"""

import argparse
import csv
import json
import os
import sys
import time

import requests
import openpyxl

XLSX_PATH = os.path.join(os.path.dirname(__file__), "mairies_france_complet_20251022_1327.xlsx")
GEO_API   = "https://geo.api.gouv.fr/communes"
DELAY     = 0.15   # secondes entre requêtes (≈6 req/s — bien en dessous du rate-limit)

_ALL_COMMUNES_CACHE: dict = {}   # {code_postal: [{code, nom, population, lat, lon}]}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse_latlon(adresse_json: str) -> tuple:
    """Extrait (lat, lon) depuis le JSON adresse de Toutes_Mairies."""
    try:
        data = json.loads(adresse_json)
        if isinstance(data, list) and data:
            lat = data[0].get("latitude")
            lon = data[0].get("longitude")
            if lat and lon:
                return float(lat), float(lon)
    except Exception:
        pass
    return None, None


def _fetch_insee(commune: str, code_postal: str) -> dict:
    """
    Retourne {'code_insee': ..., 'population': ...} via geo.api.gouv.fr.
    Utilise le cache bulk si disponible, sinon requête individuelle.
    Fallback : code vide, population 0.
    """
    global _ALL_COMMUNES_CACHE
    if _ALL_COMMUNES_CACHE:
        # Recherche dans le cache (code_postal exact, puis fuzzy sur le nom)
        candidates = _ALL_COMMUNES_CACHE.get(str(code_postal).zfill(5), [])
        if candidates:
            nom_up = commune.upper().strip()
            for c in candidates:
                if c['nom'].upper() == nom_up:
                    return {'code_insee': c['code'], 'population': c['population']}
            # fallback : première commune du même code postal
            return {'code_insee': candidates[0]['code'], 'population': candidates[0]['population']}
        return {'code_insee': '', 'population': 0}

    result = {"code_insee": "", "population": 0}
    try:
        params = {
            "q": commune,
            "fields": "code,nom,population,centre",
            "limit": 1,
            "boost": "population",
        }
        if code_postal:
            params["codePostal"] = str(code_postal)

        r = requests.get(GEO_API, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        if data:
            result["code_insee"] = data[0].get("code", "")
            result["population"] = data[0].get("population", 0) or 0
    except Exception as e:
        sys.stderr.write(f"  [WARN] geo.api.gouv.fr échoué pour {commune}: {e}\n")
    return result


def preload_all_communes():
    """
    Télécharge toutes les communes françaises depuis geo.api.gouv.fr en un seul appel
    (~35k communes, ~3 Mo JSON) et indexe par code postal.
    Beaucoup plus rapide que 36 000 requêtes individuelles.
    """
    global _ALL_COMMUNES_CACHE
    if _ALL_COMMUNES_CACHE:
        return  # déjà chargé

    print("Chargement de toutes les communes (geo.api.gouv.fr)…", flush=True)
    try:
        r = requests.get(
            GEO_API,
            params={'fields': 'code,nom,population,codesPostaux,centre', 'limit': 40000},
            timeout=60
        )
        r.raise_for_status()
        communes = r.json()
        print(f"  → {len(communes)} communes reçues", flush=True)
        index: dict = {}
        for c in communes:
            code  = c.get('code', '')
            nom   = c.get('nom', '')
            pop   = c.get('population', 0) or 0
            coords = c.get('centre', {}).get('coordinates', [None, None])
            lat   = coords[1] if coords[1] else None
            lon   = coords[0] if coords[0] else None
            for cp in (c.get('codesPostaux') or []):
                cp5 = str(cp).zfill(5)
                index.setdefault(cp5, []).append(
                    {'code': code, 'nom': nom, 'population': pop, 'lat': lat, 'lon': lon}
                )
        _ALL_COMMUNES_CACHE = index
        print(f"  → Index {len(index)} codes postaux OK", flush=True)
    except Exception as e:
        sys.stderr.write(f"  [WARN] Chargement bulk échoué : {e} — enrichissement commune par commune\n")


# ── Lecture Excel ──────────────────────────────────────────────────────────────

def _dept_from_cp(code_postal) -> str:
    """
    Dérive le code département INSEE à 2 caractères depuis le code postal.
    Gère les cas spéciaux : Corse (20 → 2A/2B indéterminable → '20'),
    DOM-TOM (97x → 3 chiffres).
    """
    cp = str(code_postal or "").strip().zfill(5)
    if cp.startswith("97") or cp.startswith("98"):
        return cp[:3]
    prefix = cp[:2]
    # code postal Corse : 200xx-201xx = 2A, 202xx-206xx = 2B (approx)
    if prefix == "20":
        n = int(cp[2]) if cp[2].isdigit() else 0
        return "2A" if n <= 1 else "2B"
    return prefix.lstrip("0") or "0"   # '01' → '1' mais on normalise plus bas


def load_mairies(xlsx_path: str, dept_filter: set | None) -> list:
    """
    Lit la feuille Toutes_Mairies et filtre par département réel (dérivé du code postal).
    Le champ 'departement' interne du fichier est un compteur arbitraire — on l'ignore.
    Si dept_filter est None → toutes les communes (mode --all-depts).
    Retourne liste de dicts : nom, email, commune, code_postal, lat, lon, departement.
    """
    # Normaliser le filtre (ex: {'23','19','15'} mais aussi gérer '09' vs '9')
    dept_filter_norm = None
    if dept_filter is not None:
        dept_filter_norm = set()
        for d in dept_filter:
            dept_filter_norm.add(d.lstrip("0") or "0")
            dept_filter_norm.add(d.zfill(2))

    print(f"Ouverture {os.path.basename(xlsx_path)}…")
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb["Toutes_Mairies"]

    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        # Colonnes : nom, email, telephone, commune, code_postal, adresse, departement, departement_nom
        nom, email, _tel, commune, code_postal, adresse = (
            row[0], row[1], row[2], row[3], row[4], row[5]
        )
        if not email or "@" not in str(email):
            continue

        dept_real = _dept_from_cp(code_postal)
        if dept_filter_norm is not None and dept_real not in dept_filter_norm:
            continue

        lat, lon = _parse_latlon(str(adresse)) if adresse else (None, None)
        rows.append({
            "nom":         str(nom or "").strip(),
            "email":       str(email).strip().lower(),
            "commune":     str(commune or "").strip(),
            "code_postal": str(code_postal or "").strip(),
            "lat":         lat,
            "lon":         lon,
            "departement": dept_real.zfill(2),
        })

    wb.close()
    # Dédupliquer par email (garder la première occurrence)
    seen = set()
    unique_rows = []
    for r in rows:
        if r["email"] not in seen:
            seen.add(r["email"])
            unique_rows.append(r)
    dupes = len(rows) - len(unique_rows)
    if dupes:
        print(f"  (dédoublonné : {dupes} doublon(s) supprimé(s))")
    scope = ', '.join(sorted(dept_filter)) if dept_filter else 'TOUS LES DEPARTEMENTS'
    print(f"  → {len(unique_rows)} mairies avec email ({scope})")
    return unique_rows


# ── Enrichissement INSEE ───────────────────────────────────────────────────────

def enrich_with_insee(rows: list, dry_run: bool = False) -> list:
    """Ajoute code_insee et population à chaque entrée.
    Si le cache bulk est chargé, aucune requête HTTP individuelle n'est faite.
    """
    limit = 5 if dry_run else len(rows)
    enriched = []
    use_cache = bool(_ALL_COMMUNES_CACHE)
    for i, row in enumerate(rows[:limit]):
        if i % 50 == 0:
            print(f"  Enrichissement INSEE… {i}/{limit}", end="\r", flush=True)

        info = _fetch_insee(row["commune"], row["code_postal"])
        row["code_insee"] = info["code_insee"]
        row["population"] = info["population"]
        # Fallback lat/lon depuis le cache bulk si absent du XLSX
        if use_cache and (not row.get('lat') or not row.get('lon')):
            cp5 = str(row.get('code_postal', '')).zfill(5)
            candidates = _ALL_COMMUNES_CACHE.get(cp5, [])
            if candidates:
                nom_up = row['commune'].upper().strip()
                best = next((c for c in candidates if c['nom'].upper() == nom_up), candidates[0])
                row['lat'] = row.get('lat') or best.get('lat')
                row['lon'] = row.get('lon') or best.get('lon')
        enriched.append(row)
        if not use_cache:
            time.sleep(DELAY)

    print(f"\n  → {len(enriched)} communes enrichies")
    return enriched


# ── Export CSV ─────────────────────────────────────────────────────────────────

CSV_FIELDNAMES = [
    "email", "nom_commune", "code_insee", "departement",
    "population", "nom_maire", "lat", "lon"
]


def write_csv(rows: list, out_path: str):
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        w.writeheader()
        for row in rows:
            w.writerow({
                "email":       row["email"],
                "nom_commune": row["commune"],
                "code_insee":  row.get("code_insee", ""),
                "departement": row["departement"],
                "population":  row.get("population", 0),
                "nom_maire":   "",          # non disponible dans le fichier source
                "lat":         row["lat"] or "",
                "lon":         row["lon"] or "",
            })
    print(f"CSV écrit : {out_path}  ({len(rows)} lignes)")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Prépare le CSV mairies pour la campagne email")
    parser.add_argument("--depts", default="23,19,15",
                        help="Codes dept séparés par virgule (ex: 23,19,15)")
    parser.add_argument("--all-depts", action="store_true",
                        help="Inclure TOUS les départements (ignore --depts)")
    parser.add_argument("--min-pop", type=int, default=0,
                        help="Population minimale (ex: --min-pop 2000)")
    parser.add_argument("--out", default="",
                        help="Fichier CSV de sortie (défaut: mairies_campagne_<depts>.csv)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mode test : 5 communes seulement, pas d'écriture CSV")
    args = parser.parse_args()

    if args.all_depts:
        dept_filter = None
        label = "france"
    else:
        dept_filter = {d.strip().zfill(2) for d in args.depts.split(",")}
        label = '_'.join(sorted(dept_filter))

    pop_suffix = f"_pop{args.min_pop}" if args.min_pop > 0 else ""
    out_path = args.out or f"mairies_campagne_{label}{pop_suffix}.csv"

    # Pré-charger toutes les communes en un seul appel (beaucoup plus rapide)
    preload_all_communes()

    rows = load_mairies(XLSX_PATH, dept_filter)
    if not rows:
        print("Aucune ligne trouvée — vérifier les codes département.")
        sys.exit(1)

    rows = enrich_with_insee(rows, dry_run=args.dry_run)

    # Filtre population
    if args.min_pop > 0:
        before = len(rows)
        rows = [r for r in rows if (r.get('population') or 0) >= args.min_pop]
        print(f"  Filtre population >= {args.min_pop} hab : {before} → {len(rows)} communes")

    if args.dry_run:
        print("\n── Aperçu dry-run ──")
        for r in rows:
            print(f"  {r['commune']:30s}  {r['email']:40s}  insee={r['code_insee']}  pop={r['population']}  lat={r['lat']}  lon={r['lon']}")
        print("\n(dry-run : aucun CSV écrit)")
    else:
        write_csv(rows, out_path)
        scope = "tous depts" if args.all_depts else args.depts
        print(f"\nProchaine étape :")
        print(f"  python -c \"")
        print(f"  from mairies_campaign import create_campaign, import_mairies_csv")
        print(f"  cid = create_campaign('Campagne {scope} pop>={args.min_pop}', 'Diagnostic solaire — votre commune est concernée par la loi APER')")
        print(f"  n = import_mairies_csv('{out_path}', cid)")
        print(f"  print(f'{{n}} communes importées dans la campagne {{cid}}')\"")


if __name__ == "__main__":
    main()
