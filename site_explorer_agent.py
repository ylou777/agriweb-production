#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║       AGRIWEB / HELIAPV - SITE EXPLORER AGENT v2                    ║
║  Test complet de toutes les fonctionnalités avec screenshots        ║
║  Version améliorée : recherches abouties, CRM complet, IA Helia     ║
╚══════════════════════════════════════════════════════════════════════╝

Usage:
    python site_explorer_agent.py [--url URL] [--username USER] [--password PASS]
    python site_explorer_agent.py  (interactive mode)
"""

import asyncio
import os
import sys
import json
import argparse
import base64
import traceback
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# ─── Répertoires de sortie ───────────────────────────────────────────────────
OUTPUT_DIR      = Path("site_explorer_output")
SCREENSHOTS_DIR = OUTPUT_DIR / "screenshots"

COMMUNE_TEST = "Verfeil"
LAT_TEST  = 43.6047
LON_TEST  = 1.4442


def ensure_dirs():
    OUTPUT_DIR.mkdir(exist_ok=True)
    SCREENSHOTS_DIR.mkdir(exist_ok=True)


def sanitize_filename(name: str) -> str:
    return (name.strip("/")
                .replace("/", "_").replace(" ", "_").replace("–", "-")
                .replace("é", "e").replace("è", "e").replace("ê", "e")
                .replace("à", "a").replace("ù", "u").replace("ô", "o")
                .replace("î", "i").replace("â", "a").replace("ç", "c")
                ) or "home"


def p(step, status="▶"):
    icons = {"▶":"▶","✅":"✅","❌":"❌","⏭":"⏭","📸":"📸","🔐":"🔐","🔍":"🔍","⏳":"⏳","🏆":"🏆"}
    print(f"  {icons.get(status,status)}  {step}")


class SiteExplorerAgent:

    def __init__(self, base_url, username, password, headless=True):
        self.base_url  = base_url.rstrip("/")
        self.username  = username
        self.password  = password
        self.headless  = headless
        self.results   = []
        self.is_logged_in = False
        self.prospect_id  = None
        self.ctx  = None   # browser context (for page recovery)
        self.page = None   # current page (rebuilt automatically if it crashes)

    async def _ensure_page(self):
        """Retourne la page courante. Si elle est fermée (crash), en crée une nouvelle."""
        try:
            await self.page.evaluate("1")   # simple test d'accessibilité
            return self.page
        except Exception:
            p("  Page fermée – recréation automatique…", "✅")
            self.page = await self.ctx.new_page()
            return self.page

    async def run(self):
        ensure_dirs()
        print("\n" + "═"*70)
        print("  ☀️   AGRIWEB / HELIAPV  ─  Site Explorer Agent v2")
        print("═"*70)
        print(f"\n  URL    : {self.base_url}")
        print(f"  User   : {self.username}")
        print(f"  Output : {OUTPUT_DIR.absolute()}\n")

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            self.ctx = await browser.new_context(
                viewport={"width": 1440, "height": 900},
                locale="fr-FR",
                timezone_id="Europe/Paris",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                ),
            )
            self.page = await self.ctx.new_page()
            await self._do_login(self.page)
            if self.is_logged_in:
                await self._fetch_prospect_id(self.page)
            await self._explore_all(self.page)
            await browser.close()

        self._generate_presentation()
        print(f"\n  🏆  Exploration terminée !")
        print(f"  📁  {OUTPUT_DIR.absolute()}")
        print(f"  📊  {(OUTPUT_DIR / 'presentation.html').absolute()}\n")

    # ── LOGIN ──────────────────────────────────────────────────────────────────

    async def _do_login(self, page):
        p("Tentative de connexion…", "🔐")
        for route in ["/auth/login", "/login"]:
            try:
                await page.goto(self.base_url + route, wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(1)
                email_ok = False
                for sel in ["input[name='email']","input[type='email']",
                             "input[name='username']","#email","#username"]:
                    try:
                        await page.fill(sel, self.username, timeout=2000)
                        email_ok = True; break
                    except Exception: pass
                pwd_ok = False
                for sel in ["input[type='password']","input[name='password']","#password"]:
                    try:
                        await page.fill(sel, self.password, timeout=2000)
                        pwd_ok = True; break
                    except Exception: pass
                if not (email_ok and pwd_ok): continue
                await page.screenshot(path=str(SCREENSHOTS_DIR / "00_login_form.png"))
                for sel in ["button[type='submit']","input[type='submit']","#login-btn",
                             "button:has-text('Connexion')","button:has-text('Login')"]:
                    try:
                        await page.click(sel, timeout=2000); break
                    except Exception: pass
                await asyncio.sleep(4)
                if "/login" not in page.url and "/auth/login" not in page.url:
                    self.is_logged_in = True
                    p(f"Connecté  →  {page.url}", "✅")
                    await page.screenshot(path=str(SCREENSHOTS_DIR / "00_login_success.png"), full_page=True)
                    return
            except Exception as e:
                p(f"Erreur sur {route}: {e}", "❌")
        p("Connexion impossible – mode non authentifié", "⏭")

    # ── PROSPECT ID ────────────────────────────────────────────────────────────

    async def _fetch_prospect_id(self, page):
        try:
            response = await page.evaluate("""
                async () => {
                    try {
                        const r = await fetch('/api/crm/prospects');
                        if (!r.ok) return null;
                        const data = await r.json();
                        const arr = Array.isArray(data) ? data : (data.prospects || data.data || []);
                        return arr.length > 0 ? arr[0].id : null;
                    } catch(e) { return null; }
                }
            """)
            if response:
                self.prospect_id = int(response)
                p(f"Prospect ID trouvé : {self.prospect_id}", "✅")
            else:
                p("Aucun prospect trouvé", "⏭")
        except Exception as e:
            p(f"Impossible de récupérer le prospect ID : {e}", "⏭")

    # ── EXPLORATION ────────────────────────────────────────────────────────────

    async def _explore_all(self, page):
        # Général
        await self._shot(page, "/",           "Page d_accueil",           "Landing page HeliaPV / AgriWeb",                    cat="Général", auth=False)
        await self._shot(page, "/auth/login", "Formulaire connexion",     "Interface d'authentification sécurisée",             cat="Général", auth=False, wait=2)
        # Application
        await self._shot(page, "/app",        "Carte principale",         "Application cartographique interactive avec données solaires", cat="Application", wait=6)
        await self._test_address_search(page)
        await self._test_commune_search(page)
        # CRM
        await self._shot(page, "/crm",            "CRM Tableau de bord",  "Gestion des prospects et pipeline commercial",      cat="CRM", wait=5)
        await self._shot(page, "/crm/stats",      "CRM Statistiques",     "Indicateurs et graphiques de performance",          cat="CRM", wait=5)
        await self._shot(page, "/crm/calendrier", "CRM Calendrier",       "Planification rendez-vous et suivi tâches",          cat="CRM", wait=3)
        # Fonctionnalités par prospect
        if self.prospect_id:
            await self._test_prospect_features(page)
        else:
            p("Pas de prospect – fonctionnalités CRM par-prospect ignorées", "⏭")
        # Rapports
        await self._test_rapports(page)
        # Outils
        await self._shot(page, "/ao-pv-batiment", "AO PV Batiment",       "Appels d'offres PV pour bâtiments tertiaires",      cat="Outils", wait=4)
        await self._shot(page, "/lidar/plan",     "Plan LiDAR HD",        "Analyse LiDAR haute définition des toitures",        cat="Outils", wait=5)
        await self._shot(page, "/saved_maps",     "Cartes sauvegardees",  "Bibliothèque des cartes et analyses sauvegardées",  cat="Outils", wait=3)
        # Admin
        await self._shot(page, "/admin",                "Administration",   "Panneau d'administration (utilisateurs, licences)",  cat="Administration", wait=3)
        await self._shot(page, "/api/crm/parametrage",  "Parametrages CRM", "Configuration et paramètres du système CRM",         cat="Administration", wait=3)
        # Helia IA
        await self._test_helia(page)
        # Pages publiques
        for route, label, desc in [
            ("/health",        "Statut Systeme",  "État de santé des services et de l'API"),
            ("/subscription",  "Abonnements",     "Offres et tarifs d'abonnement"),
            ("/demo",          "Demo Accueil",    "Page de démonstration de la plateforme"),
        ]:
            await self._shot(page, route, label, desc, cat="Pages publiques", auth=False, wait=2)

    # ── RECHERCHE ADRESSE ──────────────────────────────────────────────────────

    async def _test_address_search(self, page):
        p("Test : Recherche par adresse…", "🔍")
        page = await self._ensure_page()
        result = {
            "route": "/app#recherche-adresse",
            "label": "Recherche par adresse",
            "desc": "Saisie d'une adresse dans le panneau latéral → géolocalisation et analyse solaire de la parcelle",
            "category": "Recherche",
            "auth": True, "status": "ok",
            "screenshot": None, "extra_screenshots": [], "page_title": "Recherche par adresse", "error": None,
        }
        try:
            await page.goto(self.base_url + "/app", wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(3)
            # Ouvrir sidebar si nécessaire
            for sel in ["#openSidebarBtn", "button[data-bs-target='#sidebar']"]:
                try:
                    el = await page.query_selector(sel)
                    if el: await el.click(); await asyncio.sleep(1); break
                except Exception: pass
            # Ouvrir accordéon adresse
            for sel in ["button[data-bs-target='#acc-pane-addr']",
                         "button:has-text('Adresse')",
                         "button:has-text('adresse')"]:
                try:
                    await page.click(sel, timeout=2000); await asyncio.sleep(0.8); break
                except Exception: pass
            # Remplir
            address_filled = False
            for sel in ["#search_input","input[name='search']",
                         "input[placeholder*='adresse']","input[placeholder*='Adresse']",
                         "input[placeholder*='chercher']",".search-input","#address-input"]:
                try:
                    await page.fill(sel, "15 Rue de Nice, Toulouse", timeout=2000)
                    address_filled = True; break
                except Exception: pass
            if address_filled:
                sc1 = "recherche_adresse_saisie.png"
                await page.screenshot(path=str(SCREENSHOTS_DIR / sc1))
                result["extra_screenshots"].append({"label": "Saisie adresse", "filename": sc1})
                # Soumettre
                for sel in ["#unifiedSearchForm","form[id*='addr']","form[id*='search']"]:
                    try:
                        await page.evaluate(f"document.querySelector('{sel}') && document.querySelector('{sel}').dispatchEvent(new Event('submit',{{cancelable:true}}))")
                        break
                    except Exception: pass
                for sel in ["button[type='submit']","#searchBtn",".btn-search","button:has-text('Rechercher')"]:
                    try:
                        await page.click(sel, timeout=1500); break
                    except Exception: pass
                p("  Attente résultats adresse (30s)…", "⏳")
                await asyncio.sleep(25)
                fn = "recherche_adresse_resultats.png"
                await page.screenshot(path=str(SCREENSHOTS_DIR / fn), full_page=True)
                result["screenshot"] = fn
                p(f"  Screenshot: {fn}", "📸")
            else:
                fn = "recherche_adresse_app.png"
                await page.screenshot(path=str(SCREENSHOTS_DIR / fn), full_page=True)
                result["screenshot"] = fn; result["error"] = "Champ saisie non trouvé"
                p("  Champ adresse non trouvé", "⏭")
        except Exception as e:
            result["status"] = "error"; result["error"] = str(e)
            p(f"  Erreur recherche adresse : {e}", "❌")
            try:
                fn = "recherche_adresse_error.png"
                await page.screenshot(path=str(SCREENSHOTS_DIR / fn)); result["screenshot"] = fn
            except Exception: pass
        self.results.append(result)

    # ── RECHERCHE COMMUNE ──────────────────────────────────────────────────────

    async def _test_commune_search(self, page):
        p(f"Test : Recherche par commune ({COMMUNE_TEST})…", "🔍")
        page = await self._ensure_page()
        result = {
            "route": f"/search_by_commune?commune={COMMUNE_TEST}",
            "label": "Recherche par commune",
            "desc": f"Analyse complète de la commune de {COMMUNE_TEST} : parcelles RPG, postes électriques, données solaires, éleveurs",
            "category": "Recherche",
            "auth": True, "status": "ok",
            "screenshot": None, "extra_screenshots": [], "page_title": f"Commune – {COMMUNE_TEST}", "error": None,
        }
        try:
            url = (f"{self.base_url}/search_by_commune"
                   f"?commune={COMMUNE_TEST}&filter_rpg=true&rpg_min_area=1"
                   f"&rpg_max_area=50&ht_max_distance=3&bt_max_distance=3")
            p("  Lancement analyse commune (attente max 5 min)…", "⏳")
            await page.goto(url, wait_until="domcontentloaded", timeout=120000)
            await asyncio.sleep(5)
            fn1 = f"commune_{COMMUNE_TEST}_debut.png"
            await page.screenshot(path=str(SCREENSHOTS_DIR / fn1))
            result["extra_screenshots"].append({"label": "Lancement analyse", "filename": fn1})

            # ── Attente intelligente : scruter le DOM toutes les 15s jusqu'à 5 min ──
            RESULT_SELECTORS = [
                "table", ".result-table", "#resultats", ".results-container",
                "#map", ".leaflet-container", ".carte-container",
                "[id*='result']", "[class*='result']", "[id*='carte']",
                "h2", ".alert-success", ".panel-body",
            ]
            max_wait = 300   # 5 minutes
            check_interval = 15
            elapsed = 0
            while elapsed < max_wait:
                await asyncio.sleep(check_interval)
                elapsed += check_interval
                p(f"  Commune : {elapsed}s écoulées… (max {max_wait}s)", "⏳")

                # Screenshot intermédiaire toutes les 60s
                if elapsed % 60 == 0:
                    fn_int = f"commune_{COMMUNE_TEST}_{elapsed}s.png"
                    await page.screenshot(path=str(SCREENSHOTS_DIR / fn_int))
                    result["extra_screenshots"].append({"label": f"Progression {elapsed}s", "filename": fn_int})

                # Vérifier contenu substantiel dans la page
                content_len = await page.evaluate("() => document.body.innerText.length")

                # Détecter fin du spinner/loader
                spinner_gone = await page.evaluate("""
                    () => {
                        const loaders = document.querySelectorAll(
                            '.spinner,.loader,#loading,.loading,[class*="spin"],[class*="load"],.progress'
                        );
                        const visible = Array.from(loaders).filter(el => {
                            const s = window.getComputedStyle(el);
                            return s.display !== 'none' && s.visibility !== 'hidden' && s.opacity !== '0';
                        });
                        return visible.length === 0;
                    }
                """)

                # Contenu riche + pas de spinner + au moins 30s passées → terminé
                if content_len > 2000 and spinner_gone and elapsed >= 30:
                    p(f"  ✔  Résultats détectés après {elapsed}s (contenu: {content_len} chars)", "✅")
                    await asyncio.sleep(3)   # laisser les derniers éléments se rendre
                    break

            fn = f"commune_{COMMUNE_TEST}_resultats.png"
            # full_page=False : la page peut contenir 10MB+ de données (carte+tableaux)
            # ce qui fait timeout l'attente des polices web → on prend la vue visible
            await page.screenshot(path=str(SCREENSHOTS_DIR / fn), full_page=False, timeout=120000)
            result["screenshot"] = fn; result["page_title"] = await page.title()
            p(f"  Screenshot final: {fn}", "📸")
        except Exception as e:
            result["status"] = "error"; result["error"] = str(e)
            p(f"  Erreur commune : {e}", "❌")
            try:
                fn = f"commune_{COMMUNE_TEST}_error.png"
                await page.screenshot(path=str(SCREENSHOTS_DIR / fn), full_page=False, timeout=60000)
                result["screenshot"] = fn
            except Exception: pass
        self.results.append(result)

    # ── FONCTIONNALITÉS PAR PROSPECT ───────────────────────────────────────────

    async def _test_prospect_features(self, page):
        pid = self.prospect_id
        page = await self._ensure_page()
        p(f"Test fonctionnalités CRM prospect #{pid}…", "🔍")

        # Calpinage PV
        result_cal = {
            "route": f"/crm/prospect/{pid}/calpinage",
            "label": "Calpinage Photovoltaïque",
            "desc": "Outil de calpinage 3D des panneaux solaires sur toiture avec simulation PVGIS et autoconsommation",
            "category": "CRM – Outils", "auth": True, "status": "ok",
            "screenshot": None, "extra_screenshots": [], "page_title": "Calpinage PV", "error": None,
        }
        try:
            await page.goto(f"{self.base_url}/crm/prospect/{pid}/calpinage",
                             wait_until="domcontentloaded", timeout=25000)
            await asyncio.sleep(4)
            try: await page.wait_for_selector(".leaflet-container,canvas,#map", timeout=8000)
            except Exception: pass
            await asyncio.sleep(3)
            fn = f"calpinage_{pid}.png"
            await page.screenshot(path=str(SCREENSHOTS_DIR / fn), full_page=True)
            result_cal["screenshot"] = fn; result_cal["page_title"] = await page.title()
            p(f"  Screenshot calpinage: {fn}", "📸")
            # Bouton autoconsommation
            try:
                await page.click("#btnAutoconsommation, button:has-text('Autoconsommation')", timeout=3000)
                await asyncio.sleep(2)
                fn2 = f"calpinage_{pid}_autoconso.png"
                await page.screenshot(path=str(SCREENSHOTS_DIR / fn2))
                result_cal["extra_screenshots"].append({"label": "Panneau Autoconsommation", "filename": fn2})
            except Exception: pass
            # Bouton Plan de masse
            try:
                await page.click("button:has-text('Plan de masse'), #btnPlanMasse, button:has-text('Plan masse')", timeout=3000)
                await asyncio.sleep(2)
                fn3 = f"calpinage_{pid}_plan_masse.png"
                await page.screenshot(path=str(SCREENSHOTS_DIR / fn3))
                result_cal["extra_screenshots"].append({"label": "Plan de masse", "filename": fn3})
            except Exception: pass
        except Exception as e:
            result_cal["status"] = "error"; result_cal["error"] = str(e)
            p(f"  Erreur calpinage : {e}", "❌")
            try:
                fn = f"calpinage_{pid}_error.png"
                await page.screenshot(path=str(SCREENSHOTS_DIR / fn)); result_cal["screenshot"] = fn
            except Exception: pass
        self.results.append(result_cal)

        # Visite Technique
        await self._shot(page, f"/crm/prospect/{pid}/visite-technique",
                         "Visite Technique",
                         "Formulaire de visite technique : toiture, install. électrique, relevés terrain",
                         cat="CRM – Outils", wait=4)

        # Pré-étude / Proposition
        await self._shot(page, f"/crm/prospect/{pid}/proposition",
                         "Pre-etude Proposition",
                         "Génération de la proposition commerciale et pré-étude technique",
                         cat="CRM – Outils", wait=4)

        # Autoconsommation Collective
        await self._shot(page, f"/crm/autoconso-collective/{pid}",
                         "Autoconsommation Collective",
                         "Configuration et simulation d'une opération d'autoconsommation collective",
                         cat="CRM – Outils", wait=4)

        # Suivi Chantier
        await self._shot(page, f"/chantier/{pid}",
                         "Suivi de Chantier",
                         "Module de suivi chantier PV : planning, tâches, jalons, DOE, NCF, rapport IEC",
                         cat="CRM – Outils", wait=5)

        # CERFA (via API)
        result_cerfa = {
            "route": f"/api/crm/prospects/{pid}/generate-cerfa",
            "label": "Generation CERFA",
            "desc": "Génération automatique du CERFA de déclaration préalable pour raccordement PV",
            "category": "CRM – Documents", "auth": True, "status": "ok",
            "screenshot": None, "extra_screenshots": [], "page_title": "CERFA raccordement", "error": None,
        }
        try:
            api_result = await page.evaluate(f"""
                async () => {{
                    try {{
                        const r = await fetch('/api/crm/prospects/{pid}/generate-cerfa');
                        return {{ status: r.status, ok: r.ok }};
                    }} catch(e) {{ return {{ status: 0, error: e.message }}; }}
                }}
            """)
            result_cerfa["http_status"] = api_result.get("status","N/A")
            await page.goto(f"{self.base_url}/crm", wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(2)
            fn = f"cerfa_{pid}.png"
            await page.screenshot(path=str(SCREENSHOTS_DIR / fn), full_page=True)
            result_cerfa["screenshot"] = fn
            p(f"  Screenshot CERFA: {fn}", "📸")
        except Exception as e:
            result_cerfa["status"] = "error"; result_cerfa["error"] = str(e)
            p(f"  Erreur CERFA : {e}", "❌")
        self.results.append(result_cerfa)

    # ── RAPPORTS ───────────────────────────────────────────────────────────────

    async def _test_rapports(self, page):
        page = await self._ensure_page()
        # Rapport Commune
        p(f"Test : Rapport Commune ({COMMUNE_TEST})…", "🔍")
        result_rc = {
            "route": f"/rapport_commune?commune={COMMUNE_TEST}",
            "label": "Rapport Commune",
            "desc": f"Rapport complet commune de {COMMUNE_TEST} : carte, parcelles RPG, postes, PLU, données solaires",
            "category": "Rapports", "auth": True, "status": "ok",
            "screenshot": None, "extra_screenshots": [], "page_title": f"Rapport – {COMMUNE_TEST}", "error": None,
        }
        try:
            p("  Génération rapport commune (attente max 10 min)…", "⏳")
            # Le serveur calcule avant d'émettre le premier octet : timeout=600s
            await page.goto(f"{self.base_url}/rapport_commune?commune={COMMUNE_TEST}",
                             wait_until="commit", timeout=600000)
            await asyncio.sleep(5)
            fn1 = f"rapport_commune_{COMMUNE_TEST}_debut.png"
            await page.screenshot(path=str(SCREENSHOTS_DIR / fn1), full_page=False, timeout=60000)
            result_rc["extra_screenshots"].append({"label": "Début génération", "filename": fn1})
            max_wait_rc = 300; elapsed_rc = 0
            while elapsed_rc < max_wait_rc:
                await asyncio.sleep(15); elapsed_rc += 15
                p(f"  Rapport commune : {elapsed_rc}s…", "⏳")
                if elapsed_rc % 60 == 0:
                    fn_i = f"rapport_commune_{COMMUNE_TEST}_{elapsed_rc}s.png"
                    try:
                        await page.screenshot(path=str(SCREENSHOTS_DIR / fn_i), full_page=False, timeout=30000)
                        result_rc["extra_screenshots"].append({"label": f"Progression {elapsed_rc}s", "filename": fn_i})
                    except Exception: pass
                try:
                    content_len = await page.evaluate("() => document.body.innerText.length")
                    if content_len > 3000 and elapsed_rc >= 45:
                        p(f"  ✔  Rapport commune prêt après {elapsed_rc}s", "✅"); break
                except Exception: pass
            fn = f"rapport_commune_{COMMUNE_TEST}.png"
            await page.screenshot(path=str(SCREENSHOTS_DIR / fn), full_page=False, timeout=120000)
            result_rc["screenshot"] = fn; result_rc["page_title"] = await page.title()
            p(f"  Screenshot: {fn}", "📸")
        except Exception as e:
            result_rc["status"] = "error"; result_rc["error"] = str(e)
            p(f"  Erreur rapport commune : {e}", "❌")
            try:
                page = await self._ensure_page()
                fn = f"rapport_commune_{COMMUNE_TEST}_error.png"
                await page.screenshot(path=str(SCREENSHOTS_DIR / fn), full_page=False, timeout=30000)
                result_rc["screenshot"] = fn
            except Exception: pass
        self.results.append(result_rc)

        # Rapport Point GPS
        p(f"Test : Rapport Point GPS…", "🔍")
        result_rp = {
            "route": f"/rapport_map?lat={LAT_TEST}&lon={LON_TEST}",
            "label": "Rapport Point GPS",
            "desc": "Rapport détaillé pour coordonnées GPS : cadastre, RPG, PLU, ZAER, potentiel solaire, GeoRisques",
            "category": "Rapports", "auth": True, "status": "ok",
            "screenshot": None, "extra_screenshots": [], "page_title": "Rapport point GPS", "error": None,
        }
        try:
            p("  Génération rapport point GPS (attente max 5 min)…", "⏳")
            await page.goto(f"{self.base_url}/rapport_map?lat={LAT_TEST}&lon={LON_TEST}&address=Toulouse",
                             wait_until="commit", timeout=600000)
            await asyncio.sleep(5)
            fn1 = "rapport_point_debut.png"
            await page.screenshot(path=str(SCREENSHOTS_DIR / fn1), full_page=False, timeout=60000)
            result_rp["extra_screenshots"].append({"label": "Début rapport point", "filename": fn1})
            max_wait_rp = 180; elapsed_rp = 0
            while elapsed_rp < max_wait_rp:
                await asyncio.sleep(15); elapsed_rp += 15
                p(f"  Rapport point : {elapsed_rp}s…", "⏳")
                if elapsed_rp % 60 == 0:
                    fn_i = f"rapport_point_{elapsed_rp}s.png"
                    await page.screenshot(path=str(SCREENSHOTS_DIR / fn_i))
                    result_rp["extra_screenshots"].append({"label": f"Progression {elapsed_rp}s", "filename": fn_i})
                content_len = await page.evaluate("() => document.body.innerText.length")
                if content_len > 3000 and elapsed_rp >= 30:
                    p(f"  ✔  Rapport point prêt après {elapsed_rp}s", "✅"); break
            fn = "rapport_point_resultats.png"
            await page.screenshot(path=str(SCREENSHOTS_DIR / fn), full_page=True)
            result_rp["screenshot"] = fn; result_rp["page_title"] = await page.title()
            p(f"  Screenshot: {fn}", "📸")
        except Exception as e:
            result_rp["status"] = "error"; result_rp["error"] = str(e)
            p(f"  Erreur rapport point : {e}", "❌")
            try:
                fn = "rapport_point_error.png"
                await page.screenshot(path=str(SCREENSHOTS_DIR / fn)); result_rp["screenshot"] = fn
            except Exception: pass
        self.results.append(result_rp)

        # Rapport Commune Complet
        p(f"Test : Rapport Commune Complet…", "🔍")
        result_rcc = {
            "route": f"/rapport_commune_complet?commune={COMMUNE_TEST}",
            "label": "Rapport Commune Complet",
            "desc": "Version enrichie du rapport commune avec données supplémentaires et analyses approfondies",
            "category": "Rapports", "auth": True, "status": "ok",
            "screenshot": None, "extra_screenshots": [], "page_title": f"Rapport Complet – {COMMUNE_TEST}", "error": None,
        }
        try:
            p("  Génération rapport complet (attente max 10 min)…", "⏳")
            await page.goto(f"{self.base_url}/rapport_commune_complet?commune={COMMUNE_TEST}",
                             wait_until="commit", timeout=600000)
            await asyncio.sleep(5)
            fn1 = f"rapport_complet_{COMMUNE_TEST}_debut.png"
            await page.screenshot(path=str(SCREENSHOTS_DIR / fn1), full_page=False, timeout=60000)
            result_rcc["extra_screenshots"].append({"label": "Début rapport complet", "filename": fn1})
            max_wait_rcc = 300; elapsed_rcc = 0
            while elapsed_rcc < max_wait_rcc:
                await asyncio.sleep(15); elapsed_rcc += 15
                p(f"  Rapport complet : {elapsed_rcc}s…", "⏳")
                if elapsed_rcc % 60 == 0:
                    fn_i = f"rapport_complet_{COMMUNE_TEST}_{elapsed_rcc}s.png"
                    try:
                        await page.screenshot(path=str(SCREENSHOTS_DIR / fn_i), full_page=False, timeout=30000)
                        result_rcc["extra_screenshots"].append({"label": f"Progression {elapsed_rcc}s", "filename": fn_i})
                    except Exception: pass
                try:
                    content_len = await page.evaluate("() => document.body.innerText.length")
                    if content_len > 3000 and elapsed_rcc >= 60:
                        p(f"  ✔  Rapport complet prêt après {elapsed_rcc}s", "✅"); break
                except Exception: pass
            fn = f"rapport_complet_{COMMUNE_TEST}.png"
            await page.screenshot(path=str(SCREENSHOTS_DIR / fn), full_page=False, timeout=120000)
            result_rcc["screenshot"] = fn; result_rcc["page_title"] = await page.title()
            p(f"  Screenshot: {fn}", "📸")
        except Exception as e:
            result_rcc["status"] = "error"; result_rcc["error"] = str(e)
            p(f"  Erreur rapport complet : {e}", "❌")
            try:
                page = await self._ensure_page()
                fn = f"rapport_complet_{COMMUNE_TEST}_error.png"
                await page.screenshot(path=str(SCREENSHOTS_DIR / fn), full_page=False, timeout=30000)
                result_rcc["screenshot"] = fn
            except Exception: pass
        self.results.append(result_rcc)

    # ── HELIA IA ───────────────────────────────────────────────────────────────

    async def _test_helia(self, page):
        p("Test : Helia IA…", "🔍")
        page = await self._ensure_page()
        result = {
            "route": "/api/helia/status",
            "label": "Helia IA Assistant Solaire",
            "desc": "Assistant IA intégré spécialisé énergie solaire : analyse projets, recommandations, Q&A",
            "category": "Intelligence Artificielle", "auth": True, "status": "ok",
            "screenshot": None, "extra_screenshots": [], "page_title": "Helia IA", "error": None,
        }
        try:
            await page.goto(self.base_url + "/app", wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(3)
            for sel in ["#heliaBtn",".helia-btn","button[data-helia]",
                         "button:has-text('Helia')","button:has-text('IA')","#btn-helia"]:
                try:
                    await page.click(sel, timeout=2000); await asyncio.sleep(1.5); break
                except Exception: pass
            fn1 = "helia_interface.png"
            await page.screenshot(path=str(SCREENSHOTS_DIR / fn1))
            result["extra_screenshots"].append({"label": "Interface Helia IA", "filename": fn1})
            # Envoyer un message test
            for sel in ["#heliaInput",".helia-input","input[placeholder*='Helia']",
                         "textarea[placeholder*='Helia']","textarea[placeholder*='message']"]:
                try:
                    await page.fill(sel, "Quel est le potentiel solaire de Toulouse ?", timeout=2000); break
                except Exception: pass
            # Vérifier le statut API
            status_data = await page.evaluate("""
                async () => {
                    try {
                        const r = await fetch('/api/helia/status');
                        const data = await r.json();
                        return { status: r.status, data: data };
                    } catch(e) { return { status: 0, error: e.message }; }
                }
            """)
            result["http_status"] = status_data.get("status","N/A")
            fn = "helia_ia.png"
            await page.screenshot(path=str(SCREENSHOTS_DIR / fn), full_page=True)
            result["screenshot"] = fn
            p(f"  Screenshot Helia: {fn}", "📸")
        except Exception as e:
            result["status"] = "error"; result["error"] = str(e)
            p(f"  Erreur Helia : {e}", "❌")
            try:
                fn = "helia_ia_error.png"
                await page.screenshot(path=str(SCREENSHOTS_DIR / fn)); result["screenshot"] = fn
            except Exception: pass
        self.results.append(result)

    # ── SHOT HELPER ────────────────────────────────────────────────────────────

    async def _shot(self, page, route, label, desc, cat="Général", auth=True, wait=3):
        if auth and not self.is_logged_in:
            p(f"[SKIP] {label}", "⏭")
            self.results.append({
                "route": route,"label": label,"desc": desc,
                "category": cat,"auth": auth,"status": "skipped",
                "reason": "auth requise","screenshot": None,"extra_screenshots": [],"page_title": "","error": None,
            })
            return
        # Récupérer une page valide (recrée si crashée)
        page = await self._ensure_page()
        p(f"Page : {label}  ({route})", "▶")
        result = {
            "route": route,"label": label,"desc": desc,
            "category": cat,"auth": auth,"status": "ok",
            "screenshot": None,"extra_screenshots": [],"page_title": "","error": None,
        }
        try:
            resp = await page.goto(self.base_url + route, wait_until="domcontentloaded", timeout=60000)
            result["http_status"] = resp.status if resp else "N/A"
            await asyncio.sleep(wait)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
            await asyncio.sleep(0.4)
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(0.4)
            result["page_title"] = await page.title()
            fn = sanitize_filename(label) + ".png"
            await page.screenshot(path=str(SCREENSHOTS_DIR / fn), full_page=True, timeout=60000)
            result["screenshot"] = fn
            p(f"  Screenshot: {fn}", "📸")
        except Exception as e:
            result["status"] = "error"; result["error"] = str(e)
            p(f"  Erreur : {e}", "❌")
            try:
                page = await self._ensure_page()
                fn = sanitize_filename(label) + "_error.png"
                await page.screenshot(path=str(SCREENSHOTS_DIR / fn), full_page=False, timeout=30000)
                result["screenshot"] = fn
            except Exception: pass
        self.results.append(result)

    # ── GÉNÉRATION HTML ────────────────────────────────────────────────────────

    def _generate_presentation(self):
        p("Génération présentation HTML…", "▶")
        categories = {}
        for r in self.results:
            cat = r.get("category","Général")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r)

        def img_b64(filename):
            if not filename: return ""
            path = SCREENSHOTS_DIR / filename
            if path.exists():
                with open(path,"rb") as f:
                    return base64.b64encode(f.read()).decode()
            return ""

        now   = datetime.now().strftime("%d/%m/%Y à %H:%M")
        total = len(self.results)
        ok_n  = sum(1 for r in self.results if r["status"]=="ok")
        err_n = sum(1 for r in self.results if r["status"]=="error")
        skp_n = sum(1 for r in self.results if r["status"]=="skipped")

        sections_html = ""
        toc_links = ""

        for cat, items in categories.items():
            cat_id = (cat.lower()
                .replace(" ","_").replace("–","_").replace(" ","_")
                .replace("é","e").replace("è","e").replace("ê","e")
                .replace("à","a").replace("î","i"))
            toc_links += f'<a href="#{cat_id}">{cat}</a>\n'
            cards_html = ""
            for item in items:
                status = item["status"]
                shot   = item.get("screenshot")
                extras = item.get("extra_screenshots",[])
                badge_map = {
                    "ok":      '<span class="badge badge-ok">✅ OK</span>',
                    "error":   '<span class="badge badge-error">❌ Erreur</span>',
                    "skipped": '<span class="badge badge-skip">⏭ Ignoré</span>',
                }
                badge = badge_map.get(status, badge_map["ok"])
                if shot:
                    b64 = img_b64(shot)
                    img_html = (f'<div class="sw"><img src="data:image/png;base64,{b64}" '
                                f'alt="{item["label"]}" loading="lazy" '
                                f'onclick="openModal(this.src,\'{item["label"]}\')" />'
                                f'<div class="ov">🔍 Agrandir</div></div>') if b64 else (
                                '<div class="noss">Capture non disponible</div>')
                elif status == "skipped":
                    img_html = '<div class="noss skipped">🔒 Authentification requise</div>'
                else:
                    img_html = '<div class="noss">Pas de capture</div>'
                extras_html = ""
                for ex in extras:
                    ex_b64 = img_b64(ex["filename"])
                    if ex_b64:
                        extras_html += (f'<div class="extra">'
                            f'<p class="extra-lbl">{ex["label"]}</p>'
                            f'<img src="data:image/png;base64,{ex_b64}" '
                            f'alt="{ex["label"]}" loading="lazy" '
                            f'onclick="openModal(this.src,\'{ex["label"]}\')" /></div>')
                meta = ""
                if item.get("page_title"): meta += f'<span class="meta">📄 {item["page_title"][:60]}</span>'
                hs = item.get("http_status","")
                if hs: meta += f'<span class="meta" style="color:{("#10b981" if str(hs)=="200" else "#f59e0b")}">HTTP {hs}</span>'
                err_html = f'<p class="err">⚠️ {item["error"]}</p>' if item.get("error") else ""
                cards_html += f"""
<div class="card card-{status}">
  <div class="ch"><h3>{item["label"]}</h3>{badge}</div>
  <div class="cm">{meta}</div>
  <p class="cd">{item["desc"]}</p>
  <code class="cr">{item["route"]}</code>
  {img_html}{extras_html}{err_html}
</div>"""
            sections_html += f"""
<section class="cs" id="{cat_id}">
  <h2 class="ct">{cat}</h2>
  <div class="grid">{cards_html}</div>
</section>"""

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HeliaPV – Présentation complète</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#080d18;--surf:#0f1623;--surf2:#161f30;--acc:#f59e0b;--acc2:#6366f1;--txt:#dde4f0;--muted:#7b8ba5;--ok:#10b981;--err:#ef4444;--skip:#4b5563;--r:12px}}
html{{scroll-behavior:smooth}}
body{{background:var(--bg);color:var(--txt);font-family:'Segoe UI',system-ui,sans-serif}}
.hero{{background:linear-gradient(135deg,#080d18,#0e1535,#080d18);padding:60px 40px 44px;text-align:center;border-bottom:1px solid rgba(245,158,11,.15);position:relative;overflow:hidden}}
.hero::before{{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 20% 60%,rgba(245,158,11,.07) 0%,transparent 55%),radial-gradient(ellipse at 80% 30%,rgba(99,102,241,.07) 0%,transparent 55%)}}
.hero-ico{{font-size:3rem;margin-bottom:8px;position:relative}}
.hero h1{{font-size:clamp(1.6rem,3vw,2.7rem);font-weight:800;position:relative;background:linear-gradient(135deg,#f59e0b,#fcd34d,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.hero p{{color:var(--muted);font-size:.96rem;margin-top:6px;position:relative}}
.stats{{display:flex;gap:16px;justify-content:center;margin-top:26px;flex-wrap:wrap;position:relative}}
.stat{{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:12px 20px;text-align:center}}
.stat .n{{font-size:1.7rem;font-weight:700;color:var(--acc)}}
.stat .l{{font-size:.73rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}}
.toc{{background:var(--surf);border-bottom:1px solid rgba(255,255,255,.06);padding:13px 40px;display:flex;gap:9px;flex-wrap:wrap;align-items:center;position:sticky;top:0;z-index:100}}
.toc-lbl{{color:var(--muted);font-size:.8rem;margin-right:5px;flex-shrink:0}}
.toc a{{color:var(--muted);text-decoration:none;font-size:.8rem;padding:4px 11px;border-radius:20px;border:1px solid rgba(255,255,255,.1);transition:all .2s;white-space:nowrap}}
.toc a:hover{{background:var(--acc);color:#000;border-color:var(--acc)}}
main{{max-width:1600px;margin:0 auto;padding:38px}}
.cs{{margin-bottom:52px;scroll-margin-top:74px}}
.ct{{font-size:1.3rem;font-weight:700;color:var(--acc);border-left:4px solid var(--acc);padding-left:13px;margin-bottom:20px;text-transform:uppercase;letter-spacing:.07em}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(400px,1fr));gap:20px}}
.card{{background:var(--surf);border-radius:var(--r);border:1px solid rgba(255,255,255,.07);overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.35);transition:transform .2s,box-shadow .2s}}
.card:hover{{transform:translateY(-3px);box-shadow:0 8px 36px rgba(0,0,0,.5)}}
.card-ok{{border-top:3px solid var(--ok)}}
.card-error{{border-top:3px solid var(--err)}}
.card-skipped{{border-top:3px solid var(--skip);opacity:.65}}
.ch{{display:flex;align-items:center;justify-content:space-between;padding:14px 17px 6px;gap:9px}}
.ch h3{{font-size:.96rem;font-weight:600;flex:1}}
.cm{{padding:0 17px 6px;display:flex;gap:9px;flex-wrap:wrap}}
.meta{{font-size:.71rem;color:var(--muted);background:rgba(255,255,255,.05);padding:2px 8px;border-radius:4px}}
.cd{{padding:0 17px 7px;font-size:.84rem;color:var(--muted)}}
.cr{{display:block;padding:2px 17px 11px;font-family:'Consolas',monospace;font-size:.77rem;color:var(--acc2)}}
.badge{{font-size:.71rem;padding:3px 10px;border-radius:20px;font-weight:600;white-space:nowrap}}
.badge-ok{{background:rgba(16,185,129,.12);color:var(--ok);border:1px solid var(--ok)}}
.badge-error{{background:rgba(239,68,68,.12);color:var(--err);border:1px solid var(--err)}}
.badge-skip{{background:rgba(75,85,99,.2);color:var(--skip);border:1px solid var(--skip)}}
.sw{{position:relative;overflow:hidden;background:#000;cursor:zoom-in;border-top:1px solid rgba(255,255,255,.06)}}
.sw img{{width:100%;display:block;transition:transform .3s,opacity .3s;opacity:.92}}
.sw:hover img{{transform:scale(1.015);opacity:1}}
.ov{{position:absolute;inset:0;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;opacity:0;transition:opacity .2s;color:#fff;font-size:.92rem;font-weight:600;pointer-events:none}}
.sw:hover .ov{{opacity:1}}
.noss{{padding:36px 17px;text-align:center;color:var(--muted);background:var(--surf2);font-size:.84rem}}
.noss.skipped{{color:var(--skip)}}
.extra{{border-top:1px solid rgba(255,255,255,.06);padding-top:5px}}
.extra-lbl{{font-size:.71rem;color:var(--muted);padding:3px 17px;font-style:italic}}
.extra img{{width:100%;display:block;cursor:zoom-in;opacity:.88;transition:opacity .2s}}
.extra img:hover{{opacity:1}}
.err{{padding:9px 17px;color:var(--err);font-size:.78rem;background:rgba(239,68,68,.07)}}
.modal{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.93);z-index:9999;align-items:center;justify-content:center;cursor:zoom-out;padding:18px}}
.modal.open{{display:flex}}
.mi{{max-width:95vw;max-height:95vh;position:relative}}
.mi img{{max-width:100%;max-height:90vh;border-radius:8px;display:block;box-shadow:0 0 60px rgba(0,0,0,.8)}}
.ml{{position:absolute;bottom:-26px;left:0;right:0;text-align:center;color:#999;font-size:.81rem}}
.mc{{position:fixed;top:16px;right:16px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);color:#fff;border-radius:50%;width:36px;height:36px;font-size:1.05rem;cursor:pointer;display:flex;align-items:center;justify-content:center}}
.mc:hover{{background:var(--err)}}
footer{{text-align:center;padding:34px;color:var(--muted);border-top:1px solid rgba(255,255,255,.06);font-size:.82rem}}
@media(max-width:768px){{.grid{{grid-template-columns:1fr}}main{{padding:20px}}.hero{{padding:38px 20px 28px}}.toc{{padding:11px 18px}}}}
</style>
</head>
<body>
<header class="hero">
  <div class="hero-ico">☀️</div>
  <h1>AgriWeb / HeliaPV — Présentation complète des fonctionnalités</h1>
  <p>Exploration automatisée réalisée le <strong>{now}</strong></p>
  <p style="margin-top:4px;font-size:.86rem;color:#4b5563">Site Explorer Agent v2 &nbsp;·&nbsp; {self.base_url}</p>
  <div class="stats">
    <div class="stat"><div class="n">{total}</div><div class="l">Fonctionnalités</div></div>
    <div class="stat"><div class="n" style="color:var(--ok)">{ok_n}</div><div class="l">Succès</div></div>
    <div class="stat"><div class="n" style="color:var(--err)">{err_n}</div><div class="l">Erreurs</div></div>
    <div class="stat"><div class="n" style="color:var(--skip)">{skp_n}</div><div class="l">Ignorés</div></div>
    <div class="stat"><div class="n">{len(categories)}</div><div class="l">Catégories</div></div>
  </div>
</header>
<nav class="toc"><span class="toc-lbl">📑 Navigation :</span>{toc_links}</nav>
<main>{sections_html}</main>
<footer><p>🌐 Présentation générée par <strong>Site Explorer Agent v2</strong></p><p style="margin-top:4px">AgriWeb · HeliaPV · {now}</p></footer>
<div class="modal" id="modal" onclick="closeModal()">
  <div class="mi" onclick="event.stopPropagation()">
    <img id="mimg" src="" alt="" /><div class="ml" id="mlbl"></div>
  </div>
  <button class="mc" onclick="closeModal()">✕</button>
</div>
<script>
function openModal(src,lbl){{document.getElementById('mimg').src=src;document.getElementById('mlbl').textContent=lbl;document.getElementById('modal').classList.add('open');document.body.style.overflow='hidden'}}
function closeModal(){{document.getElementById('modal').classList.remove('open');document.body.style.overflow=''}}
document.addEventListener('keydown',e=>{{if(e.key==='Escape')closeModal()}});
const io=new IntersectionObserver(entries=>{{entries.forEach(e=>{{if(e.isIntersecting){{e.target.style.opacity='1';e.target.style.transform='translateY(0)'}}}})}},{{threshold:0.04}});
document.querySelectorAll('.card').forEach(c=>{{c.style.opacity='0';c.style.transform='translateY(14px)';c.style.transition='opacity .4s ease,transform .4s ease,box-shadow .2s';io.observe(c)}});
</script>
</body>
</html>"""

        out = OUTPUT_DIR / "presentation.html"
        out.write_text(html, encoding="utf-8")

        json_path = OUTPUT_DIR / "rapport.json"
        with open(json_path,"w",encoding="utf-8") as f:
            json.dump({
                "generated_at": now,
                "base_url": self.base_url,
                "prospect_id": self.prospect_id,
                "stats": {"total": total,"ok": ok_n,"errors": err_n,"skipped": skp_n},
                "results": [{k:v for k,v in r.items() if k!="screenshot"} for r in self.results],
            }, f, ensure_ascii=False, indent=2)

        p(f"Présentation HTML : {out}", "✅")
        p(f"Rapport JSON      : {json_path}", "✅")


def install_playwright():
    import subprocess
    p("Installation Playwright…")
    subprocess.run([sys.executable,"-m","pip","install","playwright","--quiet"],check=True)
    subprocess.run([sys.executable,"-m","playwright","install","chromium"],check=True)
    p("Playwright installé.", "✅")


def main():
    parser = argparse.ArgumentParser(description="Site Explorer Agent v2")
    parser.add_argument("--url",      default="", help="URL de base")
    parser.add_argument("--username", default="", help="Email / identifiant")
    parser.add_argument("--password", default="", help="Mot de passe")
    parser.add_argument("--visible",  action="store_true", help="Navigateur visible")
    parser.add_argument("--install",  action="store_true", help="Installer Playwright")
    args = parser.parse_args()

    if args.install:
        install_playwright(); return

    if not PLAYWRIGHT_AVAILABLE:
        print("\n  ⚠️  Playwright non installé.")
        print("  Exécutez :  python site_explorer_agent.py --install\n")
        sys.exit(1)

    url = args.url; username = args.username; password = args.password

    if not url:
        print("\n  ╔════════════════════════════════════╗")
        print("  ║  Site Explorer Agent v2 – Config   ║")
        print("  ╚════════════════════════════════════╝\n")
        url      = input("  URL du site  [https://app.heliapv.fr] : ").strip() or "https://app.heliapv.fr"
        username = input("  Email / identifiant                    : ").strip()
        password = input("  Mot de passe                           : ").strip()

    asyncio.run(SiteExplorerAgent(
        base_url=url, username=username, password=password, headless=not args.visible
    ).run())


if __name__ == "__main__":
    main()