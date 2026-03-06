#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes Flask pour la veille solaire AFP-style.

Routes exposées :
    GET  /actualites-solaires          → Page HTML brèves AFP
    GET  /api/news/solaire             → JSON feed (query: ?lang=fr|en&limit=N)
    POST /api/news/solaire/refresh     → Force refresh (admin)
    GET  /widget/news-solaire          → Snippet HTML léger embeddable
"""

from flask import Blueprint, render_template, jsonify, request, Response
from solar_news_agent import load_cache, refresh_news_cache, start_background_refresh
import datetime

news_bp = Blueprint("news", __name__)

# Démarrage du thread dès l'import du blueprint
start_background_refresh()


@news_bp.route("/actualites-solaires")
def actualites_solaires():
    data     = load_cache()
    articles = data.get("articles", [])
    lang     = request.args.get("lang", "all")  # filtre optionnel

    france = [a for a in articles if a.get("flag") == "fr"]
    monde  = [a for a in articles if a.get("flag") == "en"]

    return render_template(
        "news/actualites_solaires.html",
        articles_france=france,
        articles_monde=monde,
        all_articles=articles,
        last_update=data.get("last_update"),
        total=len(articles),
        annee=datetime.datetime.now().year,
    )


@news_bp.route("/api/news/solaire")
def api_news_solaire():
    data     = load_cache()
    articles = data.get("articles", [])

    lang  = request.args.get("lang")
    limit = min(int(request.args.get("limit", 20)), 80)

    if lang in ("fr", "en"):
        articles = [a for a in articles if a.get("flag") == lang]

    return jsonify({
        "last_update": data.get("last_update"),
        "total":       len(articles),
        "articles":    articles[:limit],
    })


@news_bp.route("/api/news/solaire/refresh", methods=["POST"])
def api_news_refresh():
    """Force un rafraîchissement immédiat (usage admin)."""
    try:
        briefs = refresh_news_cache()
        return jsonify({"status": "ok", "count": len(briefs)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@news_bp.route("/widget/news-solaire")
def widget_news():
    """
    Snippet HTML léger (~6 brèves) embeddable dans n'importe quelle page
    via une <iframe> ou un include JS.
    """
    data     = load_cache()
    articles = data.get("articles", [])[:6]
    return render_template(
        "news/widget_news.html",
        articles=articles,
    )
