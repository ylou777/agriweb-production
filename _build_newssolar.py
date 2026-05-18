# -*- coding: utf-8 -*-
"""Script de construction du fichier newssolar_demo.py final."""

import os

BACKEND_LINES = 169
SRC = "newssolar_demo.py"
DST = "newssolar_demo.py"

with open(SRC, encoding="utf-8") as f:
    lines = f.readlines()
backend = "".join(lines[:BACKEND_LINES])

NEW_ROUTES = """
# ── HTML / Templates ─────────────────────────────────────────────────────────
# Importés depuis _newssolar_site.py pour garde la lisibilité du backend.
from _newssolar_site import _BASE_CSS, _HEADER_HTML, DASHBOARD_TEMPLATE, SIMULATION_TEMPLATE  # noqa: E402

# ── Données régions pour les templates ───────────────────────────────────────
_REGIONS_FOR_TEMPLATE = {
    k: {"label": v["label"], "dni": v["dnI"], "ghi": v["ghi"]}
    for k, v in IRRADIANCE_DB.items()
}

# ── Routes ────────────────────────────────────────────────────────────────────

@newssolar_demo_bp.route('/', methods=['GET'])
def dashboard():
    """Site complet multi-sections - MODE PRIVE."""
    user, redir = _require_auth()
    if redir:
        return redir
    sim = simulate_hst(1.0, "france_sud", "mono", ["electricity", "heat", "cold", "h2"])
    return render_template_string(
        DASHBOARD_TEMPLATE,
        user=user,
        sim=sim,
        irradiance_regions=_REGIONS_FOR_TEMPLATE
    )


@newssolar_demo_bp.route('/simulation', methods=['GET'])
def simulation_page():
    """Simulateur HST standalone."""
    user, redir = _require_auth()
    if redir:
        return redir
    return render_template_string(
        SIMULATION_TEMPLATE,
        user=user,
        irradiance_regions=_REGIONS_FOR_TEMPLATE
    )


@newssolar_demo_bp.route('/api/simulate', methods=['POST'])
def api_simulate():
    """API JSON de simulation HST."""
    user, redir = _require_auth()
    if redir:
        return jsonify({"error": "Non autorise"}), 401
    data = request.get_json(force=True) or {}
    surface_ha     = float(data.get("surface_ha", 1.0))
    region         = str(data.get("region", "france_sud"))
    converter_type = str(data.get("converter_type", "mono"))
    outputs        = list(data.get("outputs", ["electricity", "heat"]))
    # Sécurité : limites raisonnables
    surface_ha = max(0.01, min(surface_ha, 100_000))
    if region not in IRRADIANCE_DB:
        region = "france_sud"
    if converter_type not in ("mono", "bi", "photostatic"):
        converter_type = "mono"
    allowed_outputs = {"electricity", "heat", "cold", "h2", "nh3"}
    outputs = [o for o in outputs if o in allowed_outputs] or ["electricity"]
    result = simulate_hst(surface_ha, region, converter_type, outputs)
    return jsonify(result)
"""

new_content = backend + NEW_ROUTES
with open(DST, "w", encoding="utf-8") as f:
    f.write(new_content)

with open(DST, encoding="utf-8") as f:
    total = len(f.readlines())
print(f"OK — {DST} écrit : {total} lignes total")
