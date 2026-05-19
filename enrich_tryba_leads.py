"""
Enrichit les fiches injectees par inject_leads_tryba.py (source=tryba_handoff)
avec les donnees riches manquantes :
  - parcelles_cadastrales (id_parcelle depuis diagnostic_json)
  - adresse precise (denomination depuis diagnostic_json)
  - surface_m2 reelle (depuis diagnostic_json, pas le bbox simplifie)
  - proprietaire_siren, proprietaire_denomination, proprietaire_forme_juridique
    (lookup table proprietaires_parcelles MAJIC)

Optionnel via --with-postes : enrichit aussi poste_bt_nom, poste_bt_distance_m,
poste_bt_puissance via appel HTTP au GeoServer (slow, ~10-30s par prospect).

Usage :
    $env:DATABASE_URL='postgresql://...'
    python enrich_tryba_leads.py                     # dry-run
    python enrich_tryba_leads.py --execute           # ecrit en base
    python enrich_tryba_leads.py --execute --with-postes
    python enrich_tryba_leads.py --user-id 40        # cible un autre user
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    sys.exit("psycopg2 manquant — pip install psycopg2-binary")


# ─────────────────────────────────────────────────────────────────────────────
# Connexion
# ─────────────────────────────────────────────────────────────────────────────

def connect():
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL absente — exporte-la depuis Railway.")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(url)


def fetch_all(conn, sql, params=()):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def fetch_one(conn, sql, params=()):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        r = cur.fetchone()
        return dict(r) if r else None


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _num(v):
    try:
        return float(v)
    except Exception:
        return 0.0


def parse_id_parcelle(id_parcelle, code_insee_fallback=None):
    """
    Parse un id_parcelle dans deux formats possibles :
      1) Long IGN (14 chars) : '67218000AY0852' -> ('67218', '000', 'AY', '0852')
      2) Court (section-numero) : 'AY-0852' -> (code_insee_fallback, '', 'AY', '0852')
         Necessite code_insee_fallback (pris du data_json ou commune).
    Retourne (code_insee, prefix, section, numero) ou None.
    """
    if not id_parcelle:
        return None
    s = str(id_parcelle).strip().upper()

    # Format court : SECTION-NUMERO
    if "-" in s and len(s) <= 10:
        parts = s.split("-", 1)
        if len(parts) == 2:
            section = parts[0].strip()
            numero = parts[1].strip().lstrip("0").zfill(4)
            if section and numero.isdigit() and code_insee_fallback:
                return code_insee_fallback, "", section, numero
        return None

    # Format long IGN (13-14 chars)
    if 13 <= len(s) <= 14:
        code_insee = s[:5]
        prefix = s[5:8]
        section = s[8:10].strip()
        numero = s[10:14] if len(s) >= 14 else s[10:].zfill(4)
        if code_insee.isdigit() and numero.isdigit():
            return code_insee, prefix, section, numero

    return None


DEBUG = False  # mis a True par --debug


def find_matching_asset(prospect, recipient_diag):
    """
    Trouve l'asset du diagnostic qui correspond au prospect.

    STRATEGIE : les prospects injectes par inject_leads_tryba ont latitude
    et longitude = NULL (le top_assets allege ne contient pas ces champs).
    On retrouve l'asset via le 'name' qu'on a stocke dans data_json, et on
    cherche en priorite dans _diag_full.assets (version riche).

    Retourne l'asset (dict) ou None.
    """
    dj = prospect.get("data_json")
    if isinstance(dj, str):
        try:
            dj = json.loads(dj)
        except Exception:
            dj = {}
    if not isinstance(dj, dict):
        dj = {}

    target_name = (dj.get("name") or "").strip()
    target_type = (dj.get("type") or "").strip()
    target_surface = _num(dj.get("surface_m2"))

    if DEBUG:
        print(f"      stored name='{target_name}', type='{target_type}', surface={target_surface}")

    # Pools : _diag_full.assets en priorite (riche), top_assets en fallback
    pools = []
    if isinstance(recipient_diag, dict):
        full = recipient_diag.get("_diag_full") or {}
        if isinstance(full, dict) and full.get("assets"):
            pools.append(("_diag_full.assets", full["assets"]))
        if recipient_diag.get("assets"):
            pools.append(("assets", recipient_diag["assets"]))
        if recipient_diag.get("top_assets"):
            pools.append(("top_assets", recipient_diag["top_assets"]))
        if recipient_diag.get("map_assets"):
            pools.append(("map_assets", recipient_diag["map_assets"]))

    if DEBUG:
        print(f"      pools : {[(k, len(v)) for k, v in pools]}")
        if pools:
            sample = pools[0][1][0] if pools[0][1] else {}
            print(f"      sample asset[0] keys = {list(sample.keys())[:20]}")

    def asset_name(a):
        return (a.get("denomination") or a.get("name") or "").strip()

    def asset_type_of(a):
        return (a.get("type") or "").strip()

    # 1) Match exact sur le name
    if target_name:
        for pool_name, pool in pools:
            for a in pool:
                if asset_name(a) == target_name and asset_type_of(a) == target_type:
                    if DEBUG:
                        print(f"      MATCH NAME dans {pool_name}")
                    return a

    # 2) Match generique : on a injecte sous '@lat,lon' pour les noms generiques.
    #    Si target_name commence par 'parking @' ou 'toiture @', on extrait lat,lon
    #    et on matche par coordonnees dans le pool.
    if target_name and " @ " in target_name:
        try:
            coord_str = target_name.split(" @ ", 1)[1]
            tlat, tlon = [float(x.strip()) for x in coord_str.split(",")]
            for pool_name, pool in pools:
                for a in pool:
                    alat = _num(a.get("lat") or a.get("latitude"))
                    alon = _num(a.get("lon") or a.get("longitude"))
                    if abs(alat - tlat) < 1e-4 and abs(alon - tlon) < 1e-4:
                        if DEBUG:
                            print(f"      MATCH COORDS-FROM-NAME dans {pool_name}")
                        return a
        except Exception:
            pass

    # 3) Match par (type + surface) si on a une surface significative
    if target_type and target_surface > 0:
        for pool_name, pool in pools:
            for a in pool:
                if asset_type_of(a) == target_type:
                    a_surf = _num(a.get("surface_m2") or a.get("surface"))
                    if a_surf > 0 and abs(a_surf - target_surface) / max(target_surface, 1) < 0.05:
                        if DEBUG:
                            print(f"      MATCH SURFACE dans {pool_name} (a_surf={a_surf})")
                        return a

    return None


def lookup_proprietaire(conn, id_parcelle, code_insee_fallback=None):
    """Retourne (siren, denomination, forme_juridique) le plus grand
    proprietaire de la parcelle, ou (None, None, None).
    code_insee_fallback est requis quand id_parcelle est au format court."""
    parts = parse_id_parcelle(id_parcelle, code_insee_fallback)
    if not parts:
        return None, None, None
    code_insee, _prefix, section, numero = parts
    numero_norm = numero.lstrip("0").zfill(4)
    try:
        row = fetch_one(conn, """
            SELECT siren, forme_juridique, denomination,
                   SUM(contenance) AS surf
            FROM proprietaires_parcelles
            WHERE code_insee = %s
              AND UPPER(section) = %s
              AND numero = %s
              AND denomination IS NOT NULL
            GROUP BY siren, forme_juridique, denomination
            ORDER BY surf DESC
            LIMIT 1
        """, (code_insee, section, numero_norm))
        if row:
            return row["siren"], row["denomination"], row["forme_juridique"]
    except Exception as e:
        print(f"  [WARN] lookup proprietaire {id_parcelle} : {e}")
    return None, None, None


# ─────────────────────────────────────────────────────────────────────────────
# Enrichissement
# ─────────────────────────────────────────────────────────────────────────────

def enrich_prospect(conn, prospect):
    """Enrichit un prospect : retourne dict de updates ou {} si rien a faire."""
    data_json = prospect.get("data_json")
    if isinstance(data_json, str):
        try:
            dj = json.loads(data_json)
        except Exception:
            dj = {}
    else:
        dj = data_json or {}

    recipient_id = dj.get("campaign_recipient_id")
    if not recipient_id:
        return {}, "pas de campaign_recipient_id"

    rec = fetch_one(conn,
        "SELECT diagnostic_json FROM recipients WHERE id = %s",
        (recipient_id,)
    )
    if not rec or not rec.get("diagnostic_json"):
        return {}, "recipient introuvable ou diagnostic_json vide"

    diag_raw = rec["diagnostic_json"]
    diag = json.loads(diag_raw) if isinstance(diag_raw, str) else diag_raw

    asset = find_matching_asset(prospect, diag)
    if not asset:
        return {}, "asset non matche par lat/lon"

    updates = {}

    # latitude / longitude (CRITIQUE — la vignette satellite en depend)
    alat = _num(asset.get("lat") or asset.get("latitude"))
    alon = _num(asset.get("lon") or asset.get("longitude"))
    cur_lat = _num(prospect.get("latitude"))
    cur_lon = _num(prospect.get("longitude"))
    if alat != 0 and alon != 0 and (cur_lat == 0 or cur_lon == 0
                                     or abs(alat - cur_lat) > 1e-5
                                     or abs(alon - cur_lon) > 1e-5):
        updates["latitude"] = alat
        updates["longitude"] = alon

    # parcelles_cadastrales (id_parcelle MAJIC)
    id_parcelle = (asset.get("id_parcelle") or "").strip()
    if id_parcelle and id_parcelle != (prospect.get("parcelles_cadastrales") or ""):
        updates["parcelles_cadastrales"] = id_parcelle

    # adresse plus precise (denomination plutot que 'parking @ lat, lon')
    denomination = (asset.get("denomination") or asset.get("name") or "").strip()
    cur_adresse = (prospect.get("adresse") or "").strip()
    # On remplace si la denomination est plus informative que ce qu'on a
    if denomination and denomination not in ("parking", "toiture", "") and \
       (" @ " in cur_adresse or denomination != cur_adresse):
        updates["adresse"] = denomination

    # surface_m2 reelle (BD TOPO) si dispo et differente
    surf = _num(asset.get("surface_m2") or asset.get("surface"))
    cur_surf = _num(prospect.get("surface_m2"))
    if surf > 0 and abs(surf - cur_surf) > 1:
        updates["surface_m2"] = surf
        updates["surface_ha"] = round(surf / 10000, 4)

    # proprietaire MAJIC (lookup par id_parcelle, avec code_insee de fallback)
    if id_parcelle:
        code_insee = dj.get("code_insee") if isinstance(dj, dict) else None
        siren, propr_denom, forme = lookup_proprietaire(conn, id_parcelle, code_insee)
        if siren and siren != (prospect.get("proprietaire_siren") or ""):
            updates["proprietaire_siren"] = siren
            updates["proprietaire_denomination"] = propr_denom or ""
            updates["proprietaire_forme_juridique"] = forme or ""

    return updates, None


def apply_updates(conn, prospect_id, updates):
    """Applique un dict d'updates sur agriweb_prospects."""
    if not updates:
        return
    set_clauses = []
    params = []
    for k, v in updates.items():
        set_clauses.append(f"{k} = %s")
        params.append(v)
    params.append(prospect_id)
    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE agriweb_prospects SET {', '.join(set_clauses)} WHERE id = %s",
            params,
        )
    conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Dump structure complete diagnostic_json (pour trouver ou sont les infos)
# ─────────────────────────────────────────────────────────────────────────────

def dump_diagnostic_structure(conn, user_id, source):
    """Dumpe le diagnostic_json du 1er recipient lie a un prospect tryba_handoff.
    Affiche : top-level keys, _diag_full keys, 1er asset complet."""
    # Trouve le premier prospect taggue et son recipient
    p = fetch_one(conn, """
        SELECT data_json FROM agriweb_prospects
        WHERE user_id = %s AND data_json::jsonb->>'source' = %s
        ORDER BY id LIMIT 1
    """, (str(user_id), source))
    if not p:
        print("[DUMP] Aucun prospect taggue.")
        return
    dj = p["data_json"]
    if isinstance(dj, str):
        dj = json.loads(dj)
    rid = dj.get("campaign_recipient_id")
    if not rid:
        print("[DUMP] Pas de campaign_recipient_id dans data_json.")
        return

    rec = fetch_one(conn, "SELECT * FROM recipients WHERE id = %s", (rid,))
    if not rec:
        print(f"[DUMP] Recipient {rid} introuvable.")
        return

    diag_raw = rec.get("diagnostic_json")
    if not diag_raw:
        print("[DUMP] diagnostic_json vide.")
        return
    diag = json.loads(diag_raw) if isinstance(diag_raw, str) else diag_raw

    print(f"[DUMP] Commune : {rec.get('nom_commune')} (insee={rec.get('code_insee')}, email={rec.get('email')})")
    print(f"[DUMP] Recipient id : {rid}")
    print()

    # Top-level
    print("=" * 70)
    print("TOP-LEVEL keys du diagnostic_json :")
    print("=" * 70)
    for k in sorted(diag.keys()):
        v = diag[k]
        t = type(v).__name__
        if isinstance(v, (list, tuple)):
            sample_keys = list(v[0].keys()) if v and isinstance(v[0], dict) else "(items not dict)"
            print(f"  {k:<35} {t:<10} len={len(v):<4} sample_item_keys={sample_keys}")
        elif isinstance(v, dict):
            print(f"  {k:<35} {t:<10} keys={list(v.keys())[:15]}")
        else:
            sv = repr(v)
            if len(sv) > 60:
                sv = sv[:57] + "..."
            print(f"  {k:<35} {t:<10} = {sv}")

    # _diag_full
    full = diag.get("_diag_full") or {}
    if full:
        print()
        print("=" * 70)
        print("_diag_full keys :")
        print("=" * 70)
        for k in sorted(full.keys()):
            v = full[k]
            t = type(v).__name__
            if isinstance(v, (list, tuple)):
                sample_keys = list(v[0].keys()) if v and isinstance(v[0], dict) else "(items not dict)"
                print(f"  {k:<35} {t:<10} len={len(v):<4} sample_item_keys={sample_keys}")
            elif isinstance(v, dict):
                print(f"  {k:<35} {t:<10} keys={list(v.keys())[:15]}")
            else:
                sv = repr(v)
                if len(sv) > 60:
                    sv = sv[:57] + "..."
                print(f"  {k:<35} {t:<10} = {sv}")

        # Dump complet du 1er asset
        assets = full.get("assets") or []
        if assets:
            print()
            print("=" * 70)
            print(f"PREMIER ASSET COMPLET (sur {len(assets)} assets dans _diag_full.assets) :")
            print("=" * 70)
            a0 = assets[0]
            for k in sorted(a0.keys()):
                v = a0[k]
                sv = repr(v)
                if len(sv) > 250:
                    sv = sv[:247] + "..."
                print(f"  {k:<25} = {sv}")

    # Top assets
    top = diag.get("top_assets") or []
    if top:
        print()
        print("=" * 70)
        print(f"PREMIER TOP_ASSET COMPLET (sur {len(top)} top_assets) :")
        print("=" * 70)
        for k in sorted(top[0].keys()):
            v = top[0][k]
            sv = repr(v)
            if len(sv) > 250:
                sv = sv[:247] + "..."
            print(f"  {k:<25} = {sv}")


# ─────────────────────────────────────────────────────────────────────────────
# Probe MAJIC : pourquoi la lookup proprietaire ne renvoie rien ?
# ─────────────────────────────────────────────────────────────────────────────

def probe_majic(conn, user_id, source):
    """Diagnostique la table proprietaires_parcelles pour les leads taggues."""
    # 1) Existe-t-elle ?
    try:
        row = fetch_one(conn,
            "SELECT COUNT(*) AS n FROM proprietaires_parcelles", ())
        total = row.get("n", 0) if row else 0
        print(f"[PROBE] proprietaires_parcelles existe : {total:,} lignes au total".replace(",", " "))
    except Exception as e:
        print(f"[PROBE] table proprietaires_parcelles introuvable ou inaccessible : {e}")
        return

    # 2) Distribution par departement (premier chiffre de code_insee)
    try:
        rows = fetch_all(conn, """
            SELECT LEFT(code_insee, 2) AS dept, COUNT(*) AS n,
                   COUNT(DISTINCT code_insee) AS communes
            FROM proprietaires_parcelles
            GROUP BY LEFT(code_insee, 2)
            ORDER BY n DESC
            LIMIT 30
        """)
        print(f"[PROBE] Top departements couverts :")
        for r in rows:
            print(f"        dept {r['dept']}: {r['n']:>9,} lignes, {r['communes']:>4} communes".replace(",", " "))
    except Exception as e:
        print(f"[PROBE] erreur stat depts: {e}")

    # 3) Pour chaque prospect tryba_handoff, tester la lookup
    prospects = fetch_all(conn, """
        SELECT id, parcelles_cadastrales, commune, departement, data_json
        FROM agriweb_prospects
        WHERE user_id = %s
          AND data_json::jsonb->>'source' = %s
        ORDER BY id
    """, (str(user_id), source))
    print(f"\n[PROBE] Test lookup proprietaire sur {len(prospects)} prospects taggues :")
    print(f"{'ID':<5} {'commune':<25} {'parcelle':<18} {'parse':<32} {'siren':<11} {'denomination':<35}")
    print("-" * 130)
    for p in prospects:
        pid = p["id"]
        ip = (p.get("parcelles_cadastrales") or "").strip()
        # Recupere code_insee depuis data_json (pour parser le format court SECTION-NUMERO)
        dj = p.get("data_json") or {}
        if isinstance(dj, str):
            try:
                dj = json.loads(dj)
            except Exception:
                dj = {}
        code_insee_fallback = dj.get("code_insee") if isinstance(dj, dict) else None
        if not ip:
            print(f"{pid:<5} {p['commune'][:25]:<25} {'-':<18} {'(pas de parcelle)':<32}")
            continue
        parsed = parse_id_parcelle(ip, code_insee_fallback)
        parse_str = f"{parsed}" if parsed else "(parse echec)"
        if not parsed:
            print(f"{pid:<5} {p['commune'][:25]:<25} {ip[:18]:<18} {parse_str[:25]:<25}")
            continue
        code_insee, _pfx, section, numero = parsed
        numero_norm = numero.lstrip("0").zfill(4)
        # Lookup AVEC filtre denomination
        row = fetch_one(conn, """
            SELECT siren, denomination FROM proprietaires_parcelles
            WHERE code_insee = %s AND UPPER(section) = %s AND numero = %s
              AND denomination IS NOT NULL
            ORDER BY contenance DESC NULLS LAST LIMIT 1
        """, (code_insee, section, numero_norm))
        if row:
            print(f"{pid:<5} {p['commune'][:25]:<25} {ip[:18]:<18} {parse_str[:25]:<25} "
                  f"{(row['siren'] or '-'):<11} {(row['denomination'] or '-')[:35]:<35}")
        else:
            # Sans filtre denomination
            row2 = fetch_one(conn, """
                SELECT siren, denomination FROM proprietaires_parcelles
                WHERE code_insee = %s AND UPPER(section) = %s AND numero = %s
                LIMIT 1
            """, (code_insee, section, numero_norm))
            # Sample brut sans filtre numero (juste meme code_insee + section)
            cnt = fetch_one(conn, """
                SELECT COUNT(*) AS n FROM proprietaires_parcelles
                WHERE code_insee = %s AND UPPER(section) = %s
            """, (code_insee, section))
            n_section = cnt.get("n", 0) if cnt else 0
            note = ""
            if row2:
                note = f"trouve sans filtre denom (siren={row2.get('siren')!r}, denom={row2.get('denomination')!r})"
            else:
                note = f"absent : section a {n_section} parcelles, mais pas notre numero"
            print(f"{pid:<5} {p['commune'][:25]:<25} {ip[:18]:<18} {parse_str[:25]:<25} "
                  f"{'NONE':<11} {note[:35]:<35}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--user-id", type=int, default=40,
                   help="user_id cible (defaut 40 = Pascal Bouchart)")
    p.add_argument("--source", default="tryba_handoff",
                   help="source filter (defaut tryba_handoff)")
    p.add_argument("--execute", action="store_true",
                   help="Applique les UPDATE (sans : dry-run)")
    p.add_argument("--debug", action="store_true",
                   help="Affiche les pools et coords pour comprendre les SKIP")
    p.add_argument("--limit", type=int, default=None,
                   help="Limite le nombre de prospects traites (debug)")
    p.add_argument("--probe-majic", action="store_true",
                   help="Diagnostique pourquoi la lookup proprietaire echoue : "
                        "affiche les id_parcelle injectes, leur parsing, et le "
                        "resultat de la requete MAJIC (avec et sans filtre denomination).")
    p.add_argument("--dump-diag", action="store_true",
                   help="Dumpe la structure complete du diagnostic_json du premier "
                        "recipient cible : top-level keys + _diag_full keys + 1er asset complet. "
                        "Permet de voir ou sont stockees les infos proprietaire / poste BT.")
    args = p.parse_args()

    global DEBUG
    DEBUG = args.debug

    conn = connect()
    print("[OK] connecte a la base PostgreSQL")

    # Mode probe MAJIC : diagnostic dedie a la lookup proprietaire
    if args.probe_majic:
        probe_majic(conn, args.user_id, args.source)
        return

    # Mode dump-diag : dumpe la structure complete du 1er diagnostic
    if args.dump_diag:
        dump_diagnostic_structure(conn, args.user_id, args.source)
        return

    prospects = fetch_all(conn, """
        SELECT id, latitude, longitude, surface_m2, adresse,
               parcelles_cadastrales, proprietaire_siren, data_json
        FROM agriweb_prospects
        WHERE user_id = %s
          AND data_json::jsonb->>'source' = %s
        ORDER BY id
    """, (str(args.user_id), args.source))

    print(f"[OK] {len(prospects)} prospects cibles a enrichir")
    if not prospects:
        return

    if args.limit:
        prospects = prospects[: args.limit]
        print(f"[OK] limite a {len(prospects)} prospects (--limit)")

    if DEBUG and prospects:
        # Dump des top-level keys du premier recipient pour comprendre
        first_data = prospects[0].get("data_json")
        if isinstance(first_data, str):
            first_data = json.loads(first_data)
        rid = first_data.get("campaign_recipient_id") if first_data else None
        if rid:
            rec = fetch_one(conn, "SELECT diagnostic_json FROM recipients WHERE id = %s", (rid,))
            if rec and rec.get("diagnostic_json"):
                d_raw = rec["diagnostic_json"]
                d = json.loads(d_raw) if isinstance(d_raw, str) else d_raw
                print(f"[DEBUG] diagnostic_json top-level keys du recipient {rid} :")
                print(f"        {list(d.keys())[:25]}")

    n_updated = 0
    n_skipped = 0
    n_errors = 0
    summary_rows = []

    for p in prospects:
        if DEBUG:
            print(f"\n  ── prospect {p['id']} ─────")
        try:
            updates, err = enrich_prospect(conn, p)
        except Exception as e:
            print(f"  [ERR] prospect {p['id']} : {e}")
            n_errors += 1
            continue

        if err:
            n_skipped += 1
            summary_rows.append((p["id"], "SKIP", err, {}))
            continue
        if not updates:
            n_skipped += 1
            summary_rows.append((p["id"], "OK   ", "deja a jour", {}))
            continue

        summary_rows.append((p["id"], "UPDATE", "", updates))
        if args.execute:
            apply_updates(conn, p["id"], updates)
        n_updated += 1

    # ─── Affichage resume ────────────────────────────────────────────────────
    print()
    print("━" * 110)
    print(f"  {'ID':<5} {'STATUT':<7} {'CHAMPS':<60}  notes")
    print("  " + "─" * 106)
    for pid, status, note, updates in summary_rows:
        fields = ", ".join(updates.keys()) if updates else "-"
        if len(fields) > 60:
            fields = fields[:57] + "..."
        print(f"  {pid:<5} {status:<7} {fields:<60}  {note}")
    print("━" * 110)
    print(f"  Updated : {n_updated}")
    print(f"  Skipped : {n_skipped}")
    print(f"  Errors  : {n_errors}")
    print()

    if not args.execute and n_updated > 0:
        print("  Mode DRY-RUN. Pour appliquer :")
        print(f"    python enrich_tryba_leads.py --execute --user-id {args.user_id}")
        print()


if __name__ == "__main__":
    main()
