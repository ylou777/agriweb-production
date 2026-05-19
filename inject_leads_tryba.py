"""
Sélectionne 10 leads phares depuis une campagne mairies et les injecte
dans le CRM d'un utilisateur cible (Pascal Bouchart, Tryba Energy, user_id=40).

Stratégie de sélection :
- 5 leads "gros potentiel"   (puissance_totale_kwc maximale)
- 5 leads "engagement chaud" (multiplicité clicks / plan_clicked / opened)
- Diversité géographique     (max 2 leads par département)
- Dédoublonnage              (un recipient ne peut être à la fois gros ET chaud,
                              c'est le top potentiel qui prime)

Usage :
    # Dry-run (par défaut) : affiche la sélection, n'écrit rien
    DATABASE_URL=postgresql://... python inject_leads_tryba.py

    # Pour cibler une autre campagne :
    DATABASE_URL=... python inject_leads_tryba.py --campaign-id <uuid>

    # Pour cibler un autre user :
    DATABASE_URL=... python inject_leads_tryba.py --user-id 42

    # Injection réelle dans agriweb_prospects + project_fiches :
    DATABASE_URL=... python inject_leads_tryba.py --execute

L'injection est idempotente : un lead déjà présent (user_id + commune + adresse
+ type) est ignoré (skipped). Pas de risque de doublon en relançant.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    sys.exit("psycopg2 manquant — pip install psycopg2-binary")


# ─────────────────────────────────────────────────────────────────────────────
# Filtres regionaux (preset)
# ─────────────────────────────────────────────────────────────────────────────
REGIONS = {
    "grand-est": ["08", "10", "51", "52", "54", "55", "57", "67", "68", "88"],
    "auvergne-rhone-alpes": ["01", "03", "07", "15", "26", "38", "42", "43", "63", "69", "73", "74"],
    "nouvelle-aquitaine": ["16", "17", "19", "23", "24", "33", "40", "47", "64", "79", "86", "87"],
    "occitanie": ["09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82"],
    "ile-de-france": ["75", "77", "78", "91", "92", "93", "94", "95"],
    "bretagne": ["22", "29", "35", "56"],
    "normandie": ["14", "27", "50", "61", "76"],
    "hauts-de-france": ["02", "59", "60", "62", "80"],
    "bourgogne-franche-comte": ["21", "25", "39", "58", "70", "71", "89", "90"],
    "centre-val-de-loire": ["18", "28", "36", "37", "41", "45"],
    "pays-de-la-loire": ["44", "49", "53", "72", "85"],
    "paca": ["04", "05", "06", "13", "83", "84"],
    "corse": ["2A", "2B"],
}


def normalize_dept(d):
    """Normalise un departement : '8' -> '08', '2a' -> '2A'."""
    if not d:
        return ""
    d = str(d).strip().upper()
    if d.isdigit():
        return d.zfill(2)
    return d


# ─────────────────────────────────────────────────────────────────────────────
# Connexion + utilitaires
# ─────────────────────────────────────────────────────────────────────────────

def connect():
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit(
            "DATABASE_URL absente — exporte-la depuis Railway :\n"
            "  $env:DATABASE_URL='postgresql://...'   (PowerShell)\n"
            "  export DATABASE_URL='postgresql://...' (bash)"
        )
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
# Sélection campagne + recipients cliqués
# ─────────────────────────────────────────────────────────────────────────────

def list_campaigns(conn):
    return fetch_all(
        conn,
        """
        SELECT id, name, status, total, sent, opened, clicked, bounced, created_at
        FROM campaigns
        ORDER BY created_at DESC
        """,
    )


def pick_default_campaign(campaigns):
    """Plus gros volume de clics. Tie-break : status='finished' d'abord."""
    if not campaigns:
        sys.exit("Aucune campagne dans la base.")
    finished = [c for c in campaigns if c["status"] == "finished"]
    pool = finished or campaigns
    return max(pool, key=lambda c: c["clicked"] or 0)


def fetch_clicked_recipients(conn, campaign_id):
    return fetch_all(
        conn,
        """
        SELECT id, email, nom_commune, code_insee, departement, population,
               nom_maire, lat, lon, diagnostic_json,
               opened_at, clicked_at, plan_clicked_at
        FROM recipients
        WHERE campaign_id = %s
          AND (clicked_at IS NOT NULL OR plan_clicked_at IS NOT NULL)
        """,
        (campaign_id,),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Scoring
# ─────────────────────────────────────────────────────────────────────────────

def parse_diag(raw):
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _num(v):
    try:
        return float(v)
    except Exception:
        return 0.0


def enrich(rec):
    """Calcule kwc_total, surface_total, n_assets, score_potential, score_engagement."""
    diag = parse_diag(rec.get("diagnostic_json"))
    rec["_diag"] = diag

    rec["kwc_total"]     = _num(diag.get("puissance_totale_kwc"))
    rec["kwh_total"]     = _num(diag.get("prod_totale_kwh"))
    rec["nb_batiments"]  = int(_num(diag.get("nb_batiments")))
    rec["nb_parkings"]   = int(_num(diag.get("nb_parkings")))
    rec["nb_parcelles"]  = int(_num(diag.get("nb_parcelles")))

    assets = diag.get("map_assets") or diag.get("top_assets") or []
    rec["n_assets"] = len(assets)
    rec["surface_total"] = sum(
        _num(a.get("surface_m2") or a.get("surface") or 0) for a in assets
    )

    # Potentiel : kwc principal, fallback surface
    rec["score_potential"] = rec["kwc_total"] or rec["surface_total"] / 6.0

    # Engagement : plan_clicked (geste fort) > clicked > opened
    s = 0.0
    if rec.get("plan_clicked_at"): s += 3.0
    if rec.get("clicked_at"):      s += 1.5
    if rec.get("opened_at"):       s += 0.5
    rec["score_engagement"] = s
    return rec


# ─────────────────────────────────────────────────────────────────────────────
# Sélection top 10 (5 gros + 5 chauds + diversité géo)
# ─────────────────────────────────────────────────────────────────────────────

def select_top10(records, max_per_dept=2, dept_filter=None):
    """dept_filter: liste de departements normalises (['67','68',...]) ou None."""
    enriched = [enrich(r) for r in records]
    # Garde seulement ceux avec un minimum de potentiel exploitable
    pool = [r for r in enriched if r["score_potential"] > 0 and r["n_assets"] > 0]
    if dept_filter:
        wanted = set(dept_filter)
        pool = [r for r in pool if normalize_dept(r.get("departement") or (r.get("code_insee") or "")[:2]) in wanted]

    by_potential = sorted(pool, key=lambda r: r["score_potential"], reverse=True)
    by_engagement = sorted(pool, key=lambda r: r["score_engagement"], reverse=True)

    picked = []
    picked_ids = set()
    picked_communes = set()
    dept_count = Counter()

    def commune_key(r):
        # Dedup sur code_insee si dispo (plus fiable), sinon nom_commune
        return (r.get("code_insee") or "").strip() or (r.get("nom_commune") or "").strip().lower()

    def can_take(r):
        if r["id"] in picked_ids:
            return False
        if commune_key(r) in picked_communes:
            return False
        if dept_count[r["departement"]] >= max_per_dept:
            return False
        return True

    def take(r, bucket):
        r["_bucket"] = bucket
        picked.append(r)
        picked_ids.add(r["id"])
        picked_communes.add(commune_key(r))
        dept_count[r["departement"]] += 1

    for r in by_potential:
        if sum(1 for x in picked if x["_bucket"] == "potential") >= 5:
            break
        if can_take(r):
            take(r, "potential")

    for r in by_engagement:
        if sum(1 for x in picked if x["_bucket"] == "engagement") >= 5:
            break
        if can_take(r):
            take(r, "engagement")

    # Si on est < 10 (contrainte dept trop serrée), relâche dept mais garde
    # la dedup commune (pas deux fois la même mairie quoi qu'il arrive).
    if len(picked) < 10:
        for r in by_potential + by_engagement:
            if len(picked) >= 10:
                break
            if r["id"] in picked_ids:
                continue
            if commune_key(r) in picked_communes:
                continue
            take(r, "fill")

    return picked


# ─────────────────────────────────────────────────────────────────────────────
# Rollback : supprime les injections taguees tryba_handoff
# ─────────────────────────────────────────────────────────────────────────────

def rollback(conn, user_id):
    """Supprime toutes les fiches injectees par ce script pour user_id donne.
    Filtre par data_json::jsonb->>'source' = 'tryba_handoff'. Idempotent."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # 1) Identifie les prospects taggues
        cur.execute(
            """SELECT id FROM agriweb_prospects
               WHERE user_id = %s
                 AND data_json::jsonb->>'source' = 'tryba_handoff'""",
            (str(user_id),),
        )
        prospect_ids = [r["id"] for r in cur.fetchall()]
        if not prospect_ids:
            print("[ROLLBACK] Aucune fiche tryba_handoff trouvee, rien a supprimer.")
            return 0

        # 2) Trouve les project_fiches lies (pour les etapes ensuite)
        cur.execute(
            "SELECT id FROM project_fiches WHERE prospect_id = ANY(%s)",
            (prospect_ids,),
        )
        project_ids = [r["id"] for r in cur.fetchall()]

        # 3) Supprime cascade : etapes -> fiches -> prospects
        if project_ids:
            cur.execute("DELETE FROM project_etapes WHERE project_id = ANY(%s)",
                        (project_ids,))
            etapes_del = cur.rowcount
            cur.execute("DELETE FROM project_fiches WHERE id = ANY(%s)",
                        (project_ids,))
            fiches_del = cur.rowcount
        else:
            etapes_del = fiches_del = 0

        cur.execute("DELETE FROM agriweb_prospects WHERE id = ANY(%s)",
                    (prospect_ids,))
        prospects_del = cur.rowcount

        conn.commit()
        print(f"[ROLLBACK] Supprime : {prospects_del} prospects, "
              f"{fiches_del} fiches projet, {etapes_del} etapes workflow.")
        return prospects_del


# ─────────────────────────────────────────────────────────────────────────────
# Injection CRM (mêmes invariants que routes/commune_ao_routes.py:inject_crm)
# ─────────────────────────────────────────────────────────────────────────────

def inject_lead(conn, rec, user_id):
    """Pour 1 recipient, injecte tous ses map_assets dans agriweb_prospects
    + project_fiches (via auto_create_project_for_prospect qui cree aussi
    les 12 etapes du workflow). Retourne (injected, skipped).

    NOTE: auto_create_project_for_prospect utilise database_adapter.execute_query
    qui ouvre ses propres connexions. On commit donc apres chaque INSERT pour
    que le prospect soit visible quand auto_create relit la base.
    """
    from crm_routes import auto_create_project_for_prospect
    from database_adapter import execute_query

    diag = rec["_diag"]
    assets = diag.get("map_assets") or diag.get("top_assets") or []
    nom_commune = rec["nom_commune"] or diag.get("nom_commune") or rec["code_insee"]
    code_insee = rec["code_insee"] or ""
    dept = (code_insee[:2] if len(code_insee) >= 2 else rec.get("departement") or "")

    injected = 0
    skipped = 0

    for asset in assets:
        lat = asset.get("lat")
        lon = asset.get("lon")
        surface = _num(asset.get("surface_m2") or asset.get("surface") or 0)
        raw_name = asset.get("name") or ""
        asset_type = asset.get("type") or ""
        kwc = _num(asset.get("kwc") or asset.get("puissance_kwc") or 0)
        crm_type = "parking" if "parking" in asset_type.lower() else "toiture"
        # Fix dedup : si le nom est vide ou generique, suffixer par lat,lon
        # pour eviter que plusieurs assets distincts dans la meme commune
        # ne se collisionnent sur (commune, adresse, type) dans inject_crm.
        generic = raw_name.strip().lower() in ("", "parking", "toiture", asset_type.lower())
        if generic and lat is not None and lon is not None:
            name = f"{crm_type} @ {float(lat):.5f}, {float(lon):.5f}"
        else:
            name = raw_name or crm_type

        # Anti-doublon (meme cle que inject_crm existante)
        existing = execute_query(
            """SELECT id FROM agriweb_prospects
               WHERE user_id = %s AND commune = %s AND adresse = %s AND type = %s
               LIMIT 1""",
            (str(user_id), nom_commune, name, crm_type),
            fetch_one=True,
        )
        if existing:
            skipped += 1
            continue

        result = execute_query(
            """
            INSERT INTO agriweb_prospects (
                type, commune, departement, adresse,
                latitude, longitude, surface_m2, surface_ha,
                data_json, user_id
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
            """,
            (
                crm_type,
                nom_commune,
                dept,
                name,
                lat,
                lon,
                surface,
                (surface / 10000) if surface else None,
                json.dumps({
                    "source": "tryba_handoff",
                    "campaign_recipient_id": rec["id"],
                    "code_insee": code_insee,
                    "type": asset_type,
                    "name": name,
                    "surface_m2": surface,
                    "puissance_kwc": kwc,
                    "economie_annuelle": _num(
                        asset.get("eco") or asset.get("economie_annuelle") or 0
                    ),
                    "lat": lat,
                    "lon": lon,
                    "geom": asset.get("geom"),
                }),
                str(user_id),
            ),
            fetch_one=True,
        )
        if result and result.get("id"):
            prospect_id = result["id"]
            project_id = auto_create_project_for_prospect(
                prospect_id, commune=nom_commune, adresse=name, user_id=user_id
            )
            if project_id:
                # Renommage avec contexte Tryba
                execute_query(
                    "UPDATE project_fiches SET nom_projet = %s WHERE id = %s",
                    (f"AO Mairie {nom_commune} — {name}", project_id),
                )
            injected += 1
    return injected, skipped


# ─────────────────────────────────────────────────────────────────────────────
# Affichage dry-run
# ─────────────────────────────────────────────────────────────────────────────

def fmt_int(n):
    return f"{int(n):>6,}".replace(",", " ")


def fmt_kwc(v):
    return f"{v:>7.1f} kWc"


def print_summary(picked, user, campaign):
    bucket_label = {"potential": "GROS POTENTIEL", "engagement": "ENGAGEMENT CHAUD", "fill": "COMPLEMENT"}
    print()
    print("━" * 110)
    print(f"  Campagne : {campaign['name']} (id={campaign['id']}) — {campaign['clicked']} clics au total")
    nom = user.get('nom') or '-'
    comp = user.get('company') or ''
    print(f"  Cible    : user_id={user['id']}  email={user['email']}  nom={nom}  societe={comp}")
    print(f"  Selection: {len(picked)} leads")
    print("━" * 110)
    print(f"  {'#':>2}  {'bucket':<18} {'dept':<5} {'commune':<28} {'kwc tot':>11} {'n_assets':>9} {'engag':>6}  email")
    print("  " + "─" * 106)
    for i, r in enumerate(picked, 1):
        print(
            f"  {i:>2}  {bucket_label[r['_bucket']]:<18} "
            f"{(r['departement'] or '')[:5]:<5} "
            f"{(r['nom_commune'] or '')[:28]:<28} "
            f"{fmt_kwc(r['kwc_total'])} "
            f"{r['n_assets']:>9} "
            f"{r['score_engagement']:>6.1f}  "
            f"{r['email']}"
        )
    print()
    print(f"  Couverture : {len(set(r['departement'] for r in picked))} departements distincts")
    print(f"  Total kWc  : {sum(r['kwc_total'] for r in picked):,.1f}".replace(",", " "))
    print(f"  Total assets a injecter : {sum(r['n_assets'] for r in picked)}")
    print("━" * 110)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--user-id", type=int, default=40, help="ID user CRM cible (defaut 40 = Pascal)")
    p.add_argument("--campaign-id", default=None, help="UUID campagne (sinon: campagne finished avec le + de clics)")
    p.add_argument("--n", type=int, default=10, help="Nombre total de leads a selectionner")
    p.add_argument("--max-per-dept", type=int, default=2, help="Max leads par departement")
    p.add_argument("--region", default=None, choices=sorted(REGIONS.keys()),
                   help="Preset region (filtre les departements). Ex: --region grand-est (Tryba)")
    p.add_argument("--departements", default=None,
                   help="Liste de departements separes par virgule. Ex: --departements 67,68,57")
    p.add_argument("--execute", action="store_true", help="Injecter (sans ce flag, dry-run)")
    p.add_argument("--list-campaigns", action="store_true", help="Lister les campagnes et sortir")
    p.add_argument("--rollback", action="store_true",
                   help="Supprime toutes les fiches injectees par ce script pour --user-id "
                        "(filtrage par data_json.source='tryba_handoff'). Demande confirmation.")
    p.add_argument("--yes", action="store_true",
                   help="Skip la confirmation interactive (a utiliser uniquement en automation)")
    args = p.parse_args()

    # Filtre departements (region preset > liste manuelle)
    dept_filter = None
    if args.region:
        dept_filter = REGIONS[args.region]
    elif args.departements:
        dept_filter = [normalize_dept(d) for d in args.departements.split(",")]

    conn = connect()
    print("[OK] connecte a la base PostgreSQL")

    # 0) Mode rollback : prioritaire, court-circuite tout le reste
    if args.rollback:
        user = fetch_one(
            conn,
            """SELECT id, email, COALESCE(name, '') AS nom FROM users WHERE id = %s""",
            (args.user_id,),
        )
        if not user:
            sys.exit(f"User id={args.user_id} introuvable")
        # Compte avant pour info
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT COUNT(*) AS n FROM agriweb_prospects
                   WHERE user_id = %s AND data_json::jsonb->>'source' = 'tryba_handoff'""",
                (str(args.user_id),),
            )
            n = (cur.fetchone() or {}).get("n", 0)
        print(f"[ROLLBACK] {n} prospects tryba_handoff seront supprimes pour "
              f"user_id={user['id']} ({user['email']}).")
        if n == 0:
            return
        if not args.yes:
            ans = input("  Tape YES pour confirmer (autre chose = abort) : ")
            if ans.strip() != "YES":
                sys.exit("Annule par l'utilisateur.")
        rollback(conn, args.user_id)
        return

    # 1) Campagnes
    campaigns = list_campaigns(conn)
    if args.list_campaigns:
        for c in campaigns:
            print(f"  {c['id']}  {c['status']:<10} clic={c['clicked']:>5}  envoyes={c['sent']:>5}  {c['name']}")
        return

    if args.campaign_id:
        camp = next((c for c in campaigns if c["id"] == args.campaign_id), None)
        if not camp:
            sys.exit(f"Campagne {args.campaign_id} introuvable")
    else:
        camp = pick_default_campaign(campaigns)
    print(f"[OK] Campagne ciblee : '{camp['name']}' (id={camp['id']}, clics={camp['clicked']})")

    # 2) User cible
    print(f"[..] Verification user_id={args.user_id} dans la table users...")
    user = fetch_one(
        conn,
        """SELECT id, email, COALESCE(name, '') AS nom,
                  COALESCE(company, '') AS company, is_admin
           FROM users WHERE id = %s""",
        (args.user_id,),
    )
    if not user:
        sys.exit(f"User id={args.user_id} introuvable dans la table users")
    print(f"[OK] User trouve : {user['email']} (nom={user.get('nom') or '-'})")

    # 3) Recipients cliques (lourd : transfere les diagnostic_json)
    print(f"[..] Telechargement des recipients cliques (peut prendre 20-60s)...", flush=True)
    clicked = fetch_clicked_recipients(conn, camp["id"])
    print(f"[OK] {len(clicked)} recipients cliques recuperes")

    # 4) Selection top N (avec filtre region eventuel)
    if dept_filter:
        zone_label = args.region or ("depts " + ",".join(dept_filter))
        print(f"[OK] Filtre region : {zone_label} ({len(dept_filter)} departements)")
    picked = select_top10(clicked, max_per_dept=args.max_per_dept, dept_filter=dept_filter)
    if not picked:
        sys.exit(
            "Aucun lead cliquant dans la zone demandee. "
            "Relache --max-per-dept, change de --region, ou retire le filtre."
        )
    if args.n != 10:
        picked = picked[: args.n]

    # 5) Affichage
    print_summary(picked, user, camp)

    # 6) Execution
    if not args.execute:
        print()
        print("  Mode DRY-RUN : aucune ecriture. Pour injecter dans le CRM,")
        print("  relance avec --execute en gardant les memes filtres :")
        cmd = "python inject_leads_tryba.py --execute"
        if args.region:
            cmd += f" --region {args.region}"
        elif args.departements:
            cmd += f" --departements {args.departements}"
        if args.user_id != 40:
            cmd += f" --user-id {args.user_id}"
        if args.n != 10:
            cmd += f" --n {args.n}"
        if args.max_per_dept != 2:
            cmd += f" --max-per-dept {args.max_per_dept}"
        print(f"  {cmd}")
        print()
        return

    # Garde-fou : confirmation interactive avant ecriture en base
    if not args.yes:
        zone = args.region or args.departements or "TOUTE LA FRANCE (aucun filtre region)"
        print()
        print(f"  >> Tu vas injecter {len(picked)} leads de la zone : {zone}")
        print(f"  >> dans le CRM de user_id={user['id']} ({user['email']}).")
        ans = input("  Tape YES pour confirmer (autre chose = abort) : ")
        if ans.strip() != "YES":
            sys.exit("Annule par l'utilisateur. Aucune ecriture en base.")

    print()
    print(f"[EXEC] Injection en cours pour user_id={user['id']} ({user['email']})...")
    total_injected = 0
    total_skipped = 0
    for r in picked:
        try:
            inj, skp = inject_lead(conn, r, user["id"])
            print(f"  -> {r['nom_commune']:<28} injected={inj:>2} skipped={skp:>2}")
            total_injected += inj
            total_skipped += skp
        except Exception as e:
            conn.rollback()
            print(f"  !! {r['nom_commune']} : {e}")
    print()
    print(f"[DONE] Total assets injectes : {total_injected}  (skipped doublons : {total_skipped})")
    print(f"       Pascal verra ces fiches dans son CRM a l'adresse https://app.heliapv.fr/crm")


if __name__ == "__main__":
    main()
