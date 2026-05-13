#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  LINKEDIN AUTO-POSTER – HeliaPV                                              ║
║  Publie 1 dépêche solaire par jour sur LinkedIn (profil ou page entreprise)  ║
║                                                                              ║
║  Variables d'environnement :                                                 ║
║    LINKEDIN_CLIENT_ID       – App Client ID (requis pour OAuth)              ║
║    LINKEDIN_CLIENT_SECRET   – App Client Secret (requis pour OAuth)          ║
║    LINKEDIN_REDIRECT_URI    – URI callback OAuth                             ║
║    LINKEDIN_POST_HOUR       – Heure UTC de publication (défaut: 8)           ║
║    LINKEDIN_ORG_ID          – ID org optionnel (poster comme page entreprise)║
║    LINKEDIN_HASHTAGS        – Hashtags séparés par espaces (optionnel)       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Cycle de vie :
  1. Admin va sur /admin/linkedin et clique "Autoriser LinkedIn"
  2. Il est redirigé vers LinkedIn → accepte les permissions
  3. LinkedIn redirige sur /admin/linkedin/callback?code=...
  4. On échange le code contre un access_token, on récupère le person_urn
  5. Chaque jour à l'heure configurée, on sélectionne la meilleure dépêche
     du cache solaire et on la publie via l'API UGC Posts
"""

import json
import os
import re
import secrets
import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

# ── Chemins ──────────────────────────────────────────────────────────────────
_BASE_DIR    = Path(__file__).parent
STATE_FILE   = _BASE_DIR / "data" / "linkedin_state.json"

# ── Configuration depuis l'environnement ─────────────────────────────────────
LINKEDIN_CLIENT_ID     = os.environ.get("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_REDIRECT_URI  = os.environ.get(
    "LINKEDIN_REDIRECT_URI",
    "https://app.heliapv.fr/admin/linkedin/callback",
)
LINKEDIN_ORG_ID        = os.environ.get("LINKEDIN_ORG_ID", "")   # ex: "12345678"
LINKEDIN_POST_HOUR     = int(os.environ.get("LINKEDIN_POST_HOUR", "8"))  # UTC
LINKEDIN_HASHTAGS      = os.environ.get(
    "LINKEDIN_HASHTAGS",
    "#solaire #photovoltaïque #EnergiesRenouvelables #HeliaPV",
)

# ── URLs API LinkedIn ─────────────────────────────────────────────────────────
_LI_AUTH_URL    = "https://www.linkedin.com/oauth/v2/authorization"
_LI_TOKEN_URL   = "https://www.linkedin.com/oauth/v2/accessToken"
_LI_ME_URL      = "https://api.linkedin.com/v2/me"
_LI_UGCPOST_URL = "https://api.linkedin.com/v2/ugcPosts"

# ── Scopes demandés ───────────────────────────────────────────────────────────
_SCOPES = "w_member_social openid profile"


# ─────────────────────────────────────────────────────────────────────────────
#  Persistance de l'état
# ─────────────────────────────────────────────────────────────────────────────

def _default_state() -> dict:
    return {
        "access_token":     "",
        "token_expires_at": "",
        "person_urn":       "",     # "urn:li:person:abc123" ou "urn:li:organization:12345678"
        "posted_ids":       [],     # IDs d'articles déjà publiés (évite les doublons)
        "last_post_at":     "",     # ISO datetime du dernier post
        "enabled":          False,  # Publication automatique activée ?
        "post_hour":        LINKEDIN_POST_HOUR,
    }


def load_state() -> dict:
    """Charge l'état depuis le fichier JSON (thread-safe en lecture)."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                data = json.load(f)
            # Migration : s'assurer que tous les champs existent
            defaults = _default_state()
            for k, v in defaults.items():
                data.setdefault(k, v)
            return data
        except Exception as e:
            print(f"[LINKEDIN] ⚠ Impossible de lire l'état : {e}")
    return _default_state()


def save_state(state: dict) -> None:
    """Sauvegarde l'état de manière atomique."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    tmp.replace(STATE_FILE)


# ─────────────────────────────────────────────────────────────────────────────
#  OAuth 2.0
# ─────────────────────────────────────────────────────────────────────────────

def build_auth_url(csrf_state: str) -> str:
    """Construit l'URL d'autorisation LinkedIn (étape 1 du flow OAuth)."""
    from urllib.parse import urlencode
    params = {
        "response_type": "code",
        "client_id":     LINKEDIN_CLIENT_ID,
        "redirect_uri":  LINKEDIN_REDIRECT_URI,
        "state":         csrf_state,
        "scope":         _SCOPES,
    }
    return f"{_LI_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    """
    Échange le code d'autorisation contre un access token.
    Retourne un dict avec les clés : access_token, expires_in, scope, …
    Lève ValueError si l'échange échoue.
    """
    resp = requests.post(
        _LI_TOKEN_URL,
        data={
            "grant_type":    "authorization_code",
            "code":          code,
            "redirect_uri":  LINKEDIN_REDIRECT_URI,
            "client_id":     LINKEDIN_CLIENT_ID,
            "client_secret": LINKEDIN_CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    if not resp.ok:
        raise ValueError(
            f"LinkedIn token exchange failed ({resp.status_code}): {resp.text}"
        )
    return resp.json()


def fetch_person_id(access_token: str) -> str:
    """
    Récupère l'ID du profil LinkedIn (person URN).
    Si LINKEDIN_ORG_ID est défini, retourne l'URN d'organisation à la place.
    """
    if LINKEDIN_ORG_ID:
        return f"urn:li:organization:{LINKEDIN_ORG_ID}"

    resp = requests.get(
        _LI_ME_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if not resp.ok:
        raise ValueError(
            f"LinkedIn /me failed ({resp.status_code}): {resp.text}"
        )
    data = resp.json()
    person_id = data.get("id", "")
    if not person_id:
        raise ValueError("LinkedIn /me returned no id field")
    return f"urn:li:person:{person_id}"


def save_token(token_data: dict) -> str:
    """
    Sauvegarde le token dans l'état et récupère le person_urn.
    Retourne le person_urn.
    """
    access_token = token_data["access_token"]
    expires_in   = token_data.get("expires_in", 5184000)  # 60 jours par défaut
    expires_at   = (
        datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    ).isoformat()

    person_urn = fetch_person_id(access_token)

    state = load_state()
    state["access_token"]     = access_token
    state["token_expires_at"] = expires_at
    state["person_urn"]       = person_urn
    save_state(state)
    print(f"[LINKEDIN] ✓ Token enregistré — auteur : {person_urn} — expire : {expires_at}")
    return person_urn


def is_token_valid() -> bool:
    """Retourne True si un access_token valide est enregistré."""
    state = load_state()
    token = state.get("access_token", "")
    if not token:
        return False
    exp = state.get("token_expires_at", "")
    if not exp:
        return True  # On ne connaît pas la date → on tente
    try:
        expires = datetime.fromisoformat(exp.replace("Z", "+00:00"))
        # Considérer invalide 1h avant l'expiration
        return datetime.now(timezone.utc) < expires - timedelta(hours=1)
    except Exception:
        return True


# ─────────────────────────────────────────────────────────────────────────────
#  Sélection et composition du post
# ─────────────────────────────────────────────────────────────────────────────

def _load_news_cache() -> list:
    """Charge les articles depuis le cache du solar_news_agent."""
    try:
        from solar_news_agent import load_cache
        return load_cache().get("articles", [])
    except Exception as e:
        print(f"[LINKEDIN] ⚠ Impossible de charger le cache news : {e}")
        return []


def pick_best_article(lang_pref: str = "fr") -> dict | None:
    """
    Choisit le meilleur article non encore publié.
    Priorité : langue préférée (fr), solar_only, plus récent.
    Retourne None si aucun article candidat.
    """
    articles = _load_news_cache()
    if not articles:
        return None

    state      = load_state()
    posted_ids = set(state.get("posted_ids", []))

    # Filtrer : non déjà publié
    candidates = [a for a in articles if a.get("id") not in posted_ids]

    # Priorité à la langue préférée
    pref = [a for a in candidates if a.get("flag") == lang_pref]
    if pref:
        candidates = pref

    # Plus récent en premier (les articles sont déjà triés par date)
    return candidates[0] if candidates else None


def build_post_text(article: dict) -> str:
    """
    Compose le texte du post LinkedIn à partir d'un article.
    Le texte reste sous 3000 caractères (limite LinkedIn).
    """
    titre   = article.get("titre", "")
    resume  = article.get("resume", "")
    source  = article.get("source", "")
    flag    = article.get("flag", "")
    hashtags = LINKEDIN_HASHTAGS

    # Emoji selon la zone géographique
    flag_emoji = {"fr": "🇫🇷", "eu": "🇪🇺", "en": "🌍"}.get(flag, "☀️")

    # Introduction accroche
    intro = f"☀️ Actu solaire du jour — {flag_emoji}"

    # Résumé tronqué à 250 chars pour garder de la place
    if len(resume) > 250:
        cut = resume[:250]
        dot = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))
        resume = cut[:dot + 1] if dot > 50 else cut[:247] + "…"

    # Lien vers la page dépêches HeliaPV
    promo = "📡 Retrouvez toutes les dépêches solaires en temps réel sur HeliaPV :\nhttps://app.heliapv.fr/actualites-solaires"

    lines = [
        intro,
        "",
        f"**{titre}**",
        "",
        resume,
        "",
        f"📰 {source}",
        "",
        promo,
        "",
        hashtags,
    ]
    text = "\n".join(lines)

    # Sécurité : LinkedIn rejette au-delà de 3000 chars
    if len(text) > 2900:
        text = text[:2897] + "…"

    return text


# ─────────────────────────────────────────────────────────────────────────────
#  Publication LinkedIn
# ─────────────────────────────────────────────────────────────────────────────

def post_article(article: dict) -> dict:
    """
    Publie l'article sur LinkedIn via l'API UGC Posts.
    Retourne un dict avec les clés : success (bool), post_id, error.
    """
    state = load_state()
    token = state.get("access_token", "")
    urn   = state.get("person_urn", "")

    if not token or not urn:
        return {"success": False, "error": "Token ou person_urn manquant — veuillez d'abord autoriser l'application"}

    post_text  = build_post_text(article)
    article_url = article.get("url", "")
    titre       = article.get("titre", "")
    resume      = article.get("resume", "")

    # Construire le payload UGC Posts
    visibility_key = (
        "com.linkedin.ugc.MemberNetworkVisibility"
        if urn.startswith("urn:li:person:")
        else "com.linkedin.ugc.OrganizationNetworkVisibility"
    )

    payload = {
        "author":         urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": post_text,
                },
                "shareMediaCategory": "ARTICLE",
                "media": [
                    {
                        "status":      "READY",
                        "originalUrl": article_url,
                        "title":       {"text": titre[:200]},
                        "description": {"text": resume[:400]},
                    }
                ],
            }
        },
        "visibility": {
            visibility_key: "PUBLIC",
        },
    }

    try:
        resp = requests.post(
            _LI_UGCPOST_URL,
            json=payload,
            headers={
                "Authorization":             f"Bearer {token}",
                "Content-Type":              "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            timeout=20,
        )
    except requests.RequestException as e:
        return {"success": False, "error": f"Erreur réseau : {e}"}

    if resp.status_code in (200, 201):
        post_id  = resp.headers.get("x-restli-id") or resp.json().get("id", "")
        now_iso  = datetime.now(timezone.utc).isoformat()
        article_id = article.get("id", "")

        # Mettre à jour l'état
        state = load_state()  # recharger pour éviter les race conditions
        if article_id and article_id not in state["posted_ids"]:
            state["posted_ids"].append(article_id)
            # Garder au maximum 500 IDs en mémoire
            if len(state["posted_ids"]) > 500:
                state["posted_ids"] = state["posted_ids"][-500:]
        state["last_post_at"] = now_iso
        save_state(state)

        print(f"[LINKEDIN] ✓ Post publié — ID : {post_id} — article : {titre[:60]}")
        return {"success": True, "post_id": post_id, "posted_at": now_iso}

    # Erreur LinkedIn
    error_body = ""
    try:
        error_body = resp.json().get("message") or resp.text
    except Exception:
        error_body = resp.text
    print(f"[LINKEDIN] ✗ Erreur API ({resp.status_code}) : {error_body}")
    return {"success": False, "error": f"LinkedIn API {resp.status_code}: {error_body}"}


# ─────────────────────────────────────────────────────────────────────────────
#  Scheduler quotidien
# ─────────────────────────────────────────────────────────────────────────────

_scheduler_started = False
_scheduler_lock    = threading.Lock()


def _already_posted_today() -> bool:
    """Retourne True si un post a déjà été publié aujourd'hui (UTC)."""
    state      = load_state()
    last_post  = state.get("last_post_at", "")
    if not last_post:
        return False
    try:
        ts   = datetime.fromisoformat(last_post.replace("Z", "+00:00"))
        today = datetime.now(timezone.utc).date()
        return ts.date() == today
    except Exception:
        return False


def run_daily_post() -> dict:
    """
    Sélectionne et publie le meilleur article si :
      - enabled=True dans l'état
      - le token est valide
      - aucun post n'a encore été fait aujourd'hui
    Retourne un dict de résultat (utilisable aussi pour un appel manuel).
    """
    state = load_state()

    if not state.get("enabled", False):
        return {"skipped": True, "reason": "Publication automatique désactivée"}

    if not is_token_valid():
        return {"skipped": True, "reason": "Token LinkedIn expiré ou absent"}

    if _already_posted_today():
        return {"skipped": True, "reason": "Déjà posté aujourd'hui"}

    article = pick_best_article()
    if not article:
        return {"skipped": True, "reason": "Aucun article disponible dans le cache"}

    return post_article(article)


def start_linkedin_scheduler() -> None:
    """
    Démarre le thread de publication quotidienne (idempotent).
    Vérifie toutes les 5 minutes si c'est l'heure de poster.
    """
    global _scheduler_started
    with _scheduler_lock:
        if _scheduler_started:
            return
        _scheduler_started = True

    def _loop():
        print(f"[LINKEDIN] ⏰ Scheduler démarré — publication chaque jour à {LINKEDIN_POST_HOUR}h UTC")
        while True:
            try:
                now = datetime.now(timezone.utc)
                state = load_state()
                post_hour = int(state.get("post_hour", LINKEDIN_POST_HOUR))

                # Déclencher dans la fenêtre [post_hour:00 → post_hour:09]
                if now.hour == post_hour and now.minute < 10:
                    result = run_daily_post()
                    if result.get("success"):
                        print(f"[LINKEDIN] ✓ Post automatique publié : {result.get('post_id')}")
                    elif result.get("skipped"):
                        pass  # Normal — déjà posté ou désactivé
                    else:
                        print(f"[LINKEDIN] ✗ Échec post automatique : {result.get('error')}")
            except Exception as e:
                print(f"[LINKEDIN] ⚠ Erreur scheduler : {e}")

            time.sleep(300)  # Vérification toutes les 5 minutes

    t = threading.Thread(target=_loop, daemon=True, name="linkedin-daily-poster")
    t.start()


# ─────────────────────────────────────────────────────────────────────────────
#  Résumé de l'état (pour l'UI admin)
# ─────────────────────────────────────────────────────────────────────────────

def get_status() -> dict:
    """Retourne un résumé lisible de l'état courant pour le dashboard admin."""
    state         = load_state()
    token_valid   = is_token_valid()
    next_article  = pick_best_article() if token_valid else None
    posted_count  = len(state.get("posted_ids", []))

    return {
        "configured":    bool(LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET),
        "token_valid":   token_valid,
        "person_urn":    state.get("person_urn", ""),
        "token_expires": state.get("token_expires_at", ""),
        "enabled":       state.get("enabled", False),
        "post_hour":     state.get("post_hour", LINKEDIN_POST_HOUR),
        "last_post_at":  state.get("last_post_at", ""),
        "posted_count":  posted_count,
        "already_today": _already_posted_today(),
        "next_article":  next_article,
        "next_post_text": build_post_text(next_article) if next_article else "",
    }
