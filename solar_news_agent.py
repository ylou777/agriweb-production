#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  AGENT DE VEILLE SOLAIRE – HeliaPV                                           ║
║  Scrape les flux RSS solaires FR + monde, formate en brèves AFP-style        ║
║                                                                              ║
║  Flux couverts :                                                             ║
║    🇫🇷 PV Magazine France, Enerzine, Actu-Environnement,                    ║
║       Connaissance des Énergies, RTE Actualités, SER                         ║
║    🌍 PV Magazine Intl, PV Tech, Electrek Solar, CleanTechnica,              ║
║       Solar Power Europe                                                     ║
║                                                                              ║
║  Rafraîchissement automatique toutes les 2h (thread daemon)                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import feedparser
import json
import re
import threading
import time
import hashlib
import calendar
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────
CACHE_FILE        = Path(__file__).parent / "data" / "solar_news_cache.json"
MAX_ARTICLES      = 200          # articles conservés en cache
MAX_PER_SOURCE    = 12           # articles max par source par cycle
REFRESH_INTERVAL  = 7200        # secondes entre deux rafraîchissements (2h)

# ── Sources RSS ────────────────────────────────────────────────────────────────
SOURCES = [
    # ══ FRANCE – Presse spécialisée ══════════════════════════════════════════
    {
        "name":    "PV Magazine France",
        "url":     "https://www.pv-magazine.fr/feed/",
        "country": "🇫🇷 France",
        "flag":    "fr",
        "lang":    "fr",
        "solar_only": True,
    },
    {
        "name":    "Enerzine",
        "url":     "https://www.enerzine.com/feed",
        "country": "🇫🇷 France",
        "flag":    "fr",
        "lang":    "fr",
        "solar_only": False,
    },
    {
        "name":    "Actu-Environnement",
        "url":     "https://www.actu-environnement.com/ae/news/rss.php4",
        "country": "🇫🇷 France",
        "flag":    "fr",
        "lang":    "fr",
        "solar_only": False,
    },
    {
        "name":    "Connaissance des Énergies",
        "url":     "https://www.connaissancedesenergies.org/rss.xml",
        "country": "🇫🇷 France",
        "flag":    "fr",
        "lang":    "fr",
        "solar_only": False,
    },
    {
        "name":    "Info Photovoltaïque",
        "url":     "https://www.info.photovoltaique.fr/feed/",
        "country": "🇫🇷 France",
        "flag":    "fr",
        "lang":    "fr",
        "solar_only": True,
    },
    {
        "name":    "Révolution Énergétique",
        "url":     "https://www.revolution-energetique.com/feed/",
        "country": "🇫🇷 France",
        "flag":    "fr",
        "lang":    "fr",
        "solar_only": False,
    },
    # ══ FRANCE – Institutionnel & régulateur ═════════════════════════════════
    {
        "name":    "ADEME Presse",
        "url":     "https://presse.ademe.fr/feed/",
        "country": "🇫🇷 France / ADEME",
        "flag":    "fr",
        "lang":    "fr",
        "solar_only": False,
    },
    {
        "name":    "Min. Transition Énergétique",
        "url":     "https://www.ecologie.gouv.fr/actualites/rss.xml",
        "country": "🇫🇷 France / Gouvernement",
        "flag":    "fr",
        "lang":    "fr",
        "solar_only": False,
    },
    {
        "name":    "CRE",
        "url":     "https://www.cre.fr/rss",
        "country": "🇫🇷 France / CRE",
        "flag":    "fr",
        "lang":    "fr",
        "solar_only": False,
    },
    {
        "name":    "RTE Actualités",
        "url":     "https://www.rte-france.com/RSS/actualites.xml",
        "country": "🇫🇷 France / RTE",
        "flag":    "fr",
        "lang":    "fr",
        "solar_only": False,
    },
    # ══ FRANCE – Syndicats & fédérations ═════════════════════════════════════
    {
        "name":    "SER – Syndicat ENR",
        "url":     "https://www.enr.fr/rss",
        "country": "🇫🇷 France / SER",
        "flag":    "fr",
        "lang":    "fr",
        "solar_only": False,
    },
    {
        "name":    "Enerplan",
        "url":     "https://www.enerplan.asso.fr/feed/",
        "country": "🇫🇷 France / Enerplan",
        "flag":    "fr",
        "lang":    "fr",
        "solar_only": True,
    },
    # ══ EUROPE ═══════════════════════════════════════════════════════════════
    {
        "name":    "Solar Power Europe",
        "url":     "https://www.solarpowereurope.org/feed/",
        "country": "🇪🇺 Europe",
        "flag":    "eu",
        "lang":    "en",
        "solar_only": True,
    },
    {
        "name":    "EASE – Energy Storage Europe",
        "url":     "https://ease-storage.eu/feed/",
        "country": "🇪🇺 Europe",
        "flag":    "eu",
        "lang":    "en",
        "solar_only": False,
    },
    # ══ INTERNATIONAL – Organisations ════════════════════════════════════════
    {
        "name":    "IRENA",
        "url":     "https://www.irena.org/rss.aspx",
        "country": "🌍 IRENA",
        "flag":    "en",
        "lang":    "en",
        "solar_only": False,
    },
    {
        "name":    "IEA – Int. Energy Agency",
        "url":     "https://www.iea.org/api/rss/en/news",
        "country": "🌍 IEA",
        "flag":    "en",
        "lang":    "en",
        "solar_only": False,
    },
    # ══ INTERNATIONAL – Presse spécialisée ═══════════════════════════════════
    {
        "name":    "PV Magazine International",
        "url":     "https://www.pv-magazine.com/feed/",
        "country": "🌍 International",
        "flag":    "en",
        "lang":    "en",
        "solar_only": True,
    },
    {
        "name":    "PV Tech",
        "url":     "https://www.pv-tech.org/feed/",
        "country": "🌍 International",
        "flag":    "en",
        "lang":    "en",
        "solar_only": True,
    },
    {
        "name":    "Electrek Solar",
        "url":     "https://electrek.co/guides/solar/feed/",
        "country": "🌍 International",
        "flag":    "en",
        "lang":    "en",
        "solar_only": True,
    },
    {
        "name":    "CleanTechnica Solar",
        "url":     "https://cleantechnica.com/category/cleantech-news/solar/feed/",
        "country": "🌍 International",
        "flag":    "en",
        "lang":    "en",
        "solar_only": True,
    },
    {
        "name":    "Solar Daily",
        "url":     "https://www.solardaily.com/backend/rss2.0.xml",
        "country": "🌍 International",
        "flag":    "en",
        "lang":    "en",
        "solar_only": True,
    },
    {
        "name":    "Renew Economy",
        "url":     "https://reneweconomy.com.au/feed/",
        "country": "🌍 International",
        "flag":    "en",
        "lang":    "en",
        "solar_only": False,
    },
    {
        "name":    "Energy Monitor",
        "url":     "https://www.energymonitor.ai/feed/",
        "country": "🌍 International",
        "flag":    "en",
        "lang":    "en",
        "solar_only": False,
    },
    {
        "name":    "Carbon Brief",
        "url":     "https://www.carbonbrief.org/feed/",
        "country": "🌍 International",
        "flag":    "en",
        "lang":    "en",
        "solar_only": False,
    },
]

# ── Mots-clés de filtrage solaire ──────────────────────────────────────────────
SOLAR_KW_FR = [
    "solaire", "photovoltaïque", "photovoltaique", r"\bpv\b", "panneaux solaires",
    "parc solaire", "centrale solaire", "autoconsommation", "ombrière",
    "agrivoltaïque", "agrivoltaique", "agri-pv", "bifacial", "kilowatt-crête",
    "megawatt", "gigawatt", "gw solaire", "capacité solaire", "enr", "renouvelable",
    "transition énergétique", "transition energetique", "énergie renouvelable",
    "appel d'offres", "ao cre", "tarif d'achat", "injection", "raccordement",
]
SOLAR_KW_EN = [
    "solar", "photovoltaic", r"\bpv\b", "rooftop solar", "utility.scale",
    "agrivoltaic", "bifacial", "perovskite", "clean energy", "renewable",
    "gigawatt", "megawatt", "solar farm", "solar panel", "solar power",
    "energy transition", "decarboni", "net zero", "capacity", "auction",
    "feed.in tariff", "grid connection", "storage",
]

_STRIP_HTML = re.compile(r"<[^>]+>")
_MULTI_WS   = re.compile(r"\s+")


def _is_solar(title: str, summary: str, lang: str) -> bool:
    """Retourne True si l'article est lié au solaire/photovoltaïque."""
    text = (title + " " + summary).lower()
    kws  = SOLAR_KW_FR if lang == "fr" else SOLAR_KW_EN
    return any(re.search(kw, text) for kw in kws)


def _clean_html(s: str) -> str:
    s = _STRIP_HTML.sub(" ", s or "")
    return _MULTI_WS.sub(" ", s).strip()


def _parse_date(entry) -> str:
    """Parse feedparser date → ISO 8601 UTC string."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        ts = calendar.timegm(entry.published_parsed)
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    return datetime.now(timezone.utc).isoformat()


def _age_label(iso_date: str) -> str:
    try:
        pub  = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        diff = datetime.now(timezone.utc) - pub
        h    = int(diff.total_seconds() // 3600)
        if h < 1:  return "il y a moins d'1h"
        if h < 24: return f"il y a {h}h"
        d = h // 24
        if d == 1: return "hier"
        if d < 7:  return f"il y a {d} jours"
        return pub.strftime("%d %b %Y")
    except Exception:
        return ""


def _format_brief(raw: dict) -> dict:
    """Formate un article brut en brève AFP-style."""
    summary = _clean_html(raw.get("summary", ""))
    if len(summary) > 280:
        # Couper à la dernière phrase complète avant 280 chars
        cut = summary[:280]
        dot = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))
        summary = (cut[:dot + 1] if dot > 80 else cut[:277] + "…")

    return {
        "id":        hashlib.md5(raw["url"].encode()).hexdigest()[:12],
        "titre":     raw["titre"],
        "resume":    summary,
        "source":    raw["source"],
        "country":   raw["country"],
        "flag":      raw["flag"],
        "lang":      raw["lang"],
        "url":       raw["url"],
        "date_pub":  raw["date_pub"],
        "age":       _age_label(raw["date_pub"]),
    }


# ── Fetch principal ────────────────────────────────────────────────────────────
def fetch_all_feeds() -> list:
    raw_articles = []
    seen_urls    = set()

    for src in SOURCES:
        try:
            feed = feedparser.parse(
                src["url"],
                request_headers={"User-Agent": "HeliaPV-NewsBotAgent/2.0"},
            )
            count = 0
            for entry in feed.entries:
                if count >= MAX_PER_SOURCE:
                    break
                url = getattr(entry, "link", "").strip()
                if not url or url in seen_urls:
                    continue

                title   = _clean_html(getattr(entry, "title",   ""))
                summary = _clean_html(
                    getattr(entry, "summary",     None) or
                    getattr(entry, "description", None) or ""
                )

                if not src["solar_only"] and not _is_solar(title, summary, src["lang"]):
                    continue

                seen_urls.add(url)
                raw_articles.append({
                    "titre":    title,
                    "summary":  summary,
                    "source":   src["name"],
                    "country":  src["country"],
                    "flag":     src["flag"],
                    "lang":     src["lang"],
                    "url":      url,
                    "date_pub": _parse_date(entry),
                })
                count += 1

            print(f"[NEWS] {src['name']:35s} → {count} articles OK")

        except Exception as e:
            print(f"[NEWS] ⚠ {src['name']} : {e}")

    # Tri chronologique (plus récent en premier)
    raw_articles.sort(key=lambda x: x["date_pub"], reverse=True)
    return raw_articles[:MAX_ARTICLES]


def refresh_news_cache() -> list:
    """Rafraîchit le cache JSON et retourne les brèves."""
    raw    = fetch_all_feeds()
    briefs = [_format_brief(a) for a in raw]

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_update": datetime.now(timezone.utc).isoformat(),
        "count":       len(briefs),
        "articles":    briefs,
    }
    tmp = CACHE_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp.replace(CACHE_FILE)   # écriture atomique
    print(f"[NEWS] ✓ Cache mis à jour : {len(briefs)} brèves")
    return briefs


def load_cache() -> dict:
    """Charge le cache depuis le disque."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_update": None, "count": 0, "articles": []}


# ── Thread de rafraîchissement en arrière-plan ─────────────────────────────────
_started = False
_lock    = threading.Lock()


def start_background_refresh():
    """Démarre le thread de rafraîchissement (idempotent)."""
    global _started
    with _lock:
        if _started:
            return
        _started = True

    def _loop():
        # Premier chargement si cache absent
        if not CACHE_FILE.exists():
            try:
                refresh_news_cache()
            except Exception as e:
                print(f"[NEWS] ⚠ Initial fetch failed : {e}")
        # Boucle infinie (toutes les REFRESH_INTERVAL secondes)
        while True:
            time.sleep(REFRESH_INTERVAL)
            try:
                refresh_news_cache()
            except Exception as e:
                print(f"[NEWS] ⚠ Refresh failed : {e}")

    t = threading.Thread(target=_loop, daemon=True, name="solar-news-refresh")
    t.start()
    print("[NEWS] 📰 Agent de veille solaire démarré (rafraîchissement toutes les 2h)")


# ── Exécution standalone ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print("▶ Lancement manuel de la veille solaire…")
    briefs = refresh_news_cache()
    print(f"\n{'─'*60}")
    for b in briefs[:10]:
        print(f"\n{b['country']}  {b['age']}")
        print(f"  {b['titre'][:90]}")
        print(f"  {b['resume'][:120]}")
        print(f"  [{b['source']}] → {b['url'][:60]}…")
