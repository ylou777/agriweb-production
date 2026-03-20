# -*- coding: utf-8 -*-
# NOUVEAU SITE NEWS-SOLAR — injection dans newssolar_demo.py
# Contenu: CSS, Header, Page principale SPA (5 sections), Simulateur standalone

# ── CSS global ───────────────────────────────────────────────────────────────

_BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#07091a; --bg2:#0a0d20; --card:#0d1124; --card2:#111428;
  --border:rgba(255,255,255,0.07); --border2:rgba(255,255,255,0.12);
  --gold:#FFB700; --gold2:#FF8C00;
  --green:#10b981; --blue:#3b82f6; --purple:#8b5cf6; --red:#ef4444;
  --text:#e2e8f0; --muted:#8892a4; --muted2:#b0bac8;
  --ns-blue:#0066CC; --ns-orange:#FF6600;
  --ns-grad:linear-gradient(135deg,#0066CC,#FF6600);
}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;min-height:100vh;overflow-y:auto}
a{color:var(--ns-blue);text-decoration:none}
a:hover{color:var(--ns-orange)}

/* ── SCROLLBAR ── */
::-webkit-scrollbar{width:10px;height:10px}
::-webkit-scrollbar-track{background:rgba(255,255,255,0.04)}
::-webkit-scrollbar-thumb{background:rgba(0,102,204,0.5);border-radius:5px;border:2px solid transparent;background-clip:content-box}
::-webkit-scrollbar-thumb:hover{background:rgba(0,102,204,0.85);border:2px solid transparent;background-clip:content-box}
*{scrollbar-width:thin;scrollbar-color:rgba(0,102,204,0.5) rgba(255,255,255,0.04)}

/* ── HEADER ── */
.ns-header{
  display:flex;align-items:center;justify-content:space-between;
  padding:0 2rem;height:62px;
  background:rgba(10,13,32,0.96);border-bottom:1px solid var(--border);
  position:sticky;top:0;z-index:200;backdrop-filter:blur(12px);
}
.ns-logo{height:42px;object-fit:contain}
.ns-badge{
  background:var(--ns-grad);color:#fff;font-size:0.68rem;font-weight:700;
  padding:0.18rem 0.6rem;border-radius:20px;letter-spacing:0.05em
}
.ns-nav{display:flex;gap:0.2rem;align-items:center}
.ns-nav a{
  color:var(--muted);font-size:0.84rem;font-weight:500;
  padding:0.4rem 0.85rem;border-radius:8px;transition:all 0.2s;
}
.ns-nav a:hover,.ns-nav a.active{background:rgba(255,255,255,0.06);color:var(--text)}
.ns-nav .cta{
  background:var(--ns-grad);color:#fff !important;
  padding:0.4rem 1rem;border-radius:8px;margin-left:0.4rem;
}
.ns-nav .cta:hover{opacity:0.9;background:var(--ns-grad)}

/* ── HERO FULL SCREEN ── */
.page-hero{
  position:relative;min-height:88vh;display:flex;align-items:center;
  overflow:hidden;
  background:radial-gradient(ellipse at 60% 50%, rgba(0,102,204,0.12) 0%, transparent 60%),
             radial-gradient(ellipse at 20% 70%, rgba(255,102,0,0.08) 0%, transparent 55%),
             var(--bg);
}
.hero-content{max-width:1300px;margin:0 auto;padding:4rem 2rem;width:100%;z-index:2;position:relative}
.hero-eyebrow{
  display:inline-flex;align-items:center;gap:0.5rem;
  background:rgba(0,102,204,0.12);border:1px solid rgba(0,102,204,0.3);
  color:var(--blue);font-size:0.78rem;font-weight:700;
  padding:0.3rem 0.9rem;border-radius:20px;margin-bottom:1.4rem;
  letter-spacing:0.05em;
}
.hero-content h1{
  font-size:clamp(2.4rem, 5vw, 4.2rem);
  font-weight:900;line-height:1.08;margin-bottom:1.4rem;
  letter-spacing:-0.02em;
}
.hero-content h1 .grad{
  background:var(--ns-grad);-webkit-background-clip:text;background-clip:text;
  -webkit-text-fill-color:transparent;
}
.hero-content p{
  font-size:1.08rem;color:var(--muted2);max-width:580px;line-height:1.72;margin-bottom:2rem;
}
.hero-stats{display:flex;gap:2.5rem;flex-wrap:wrap;margin-top:2.5rem}
.hero-stat-val{font-size:2.4rem;font-weight:900;color:var(--gold);line-height:1}
.hero-stat-lbl{font-size:0.76rem;color:var(--muted);font-weight:500;margin-top:0.3rem}
.hero-badges{display:flex;gap:0.7rem;flex-wrap:wrap;margin-bottom:2rem}
.badge{
  display:inline-flex;align-items:center;gap:0.35rem;
  background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);
  color:var(--muted2);font-size:0.78rem;font-weight:600;
  padding:0.3rem 0.75rem;border-radius:20px;
}
.badge.blue{background:rgba(59,130,246,0.1);border-color:rgba(59,130,246,0.25);color:var(--blue)}
.badge.gold{background:rgba(255,183,0,0.1);border-color:rgba(255,183,0,0.25);color:var(--gold)}
.badge.green{background:rgba(16,185,129,0.1);border-color:rgba(16,185,129,0.25);color:var(--green)}
.badge.orange{background:rgba(255,102,0,0.1);border-color:rgba(255,102,0,0.25);color:var(--ns-orange)}

/* ── SECTION ── */
.section{padding:5rem 0;border-top:1px solid var(--border)}
.section-inner{max-width:1300px;margin:0 auto;padding:0 2rem}
.section-eyebrow{
  display:inline-block;background:rgba(0,102,204,0.1);border:1px solid rgba(0,102,204,0.2);
  color:var(--blue);font-size:0.74rem;font-weight:700;letter-spacing:0.08em;
  padding:0.25rem 0.75rem;border-radius:20px;margin-bottom:1rem;text-transform:uppercase;
}
.section-title{font-size:clamp(1.6rem,3.5vw,2.6rem);font-weight:800;margin-bottom:0.8rem;letter-spacing:-0.02em}
.section-sub{font-size:1rem;color:var(--muted2);max-width:640px;line-height:1.68;margin-bottom:2.5rem}

/* ── CARDS ── */
.card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:1.5rem}
.card2{background:var(--card2);border:1px solid var(--border);border-radius:12px;padding:1.2rem}
.card-icon{font-size:2rem;margin-bottom:0.8rem}
.card-title{font-size:0.72rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem}

/* ── KPI ── */
.kpi-value{font-size:2rem;font-weight:800;line-height:1.1}
.kpi-unit{font-size:0.82rem;color:var(--muted);margin-left:0.2rem}
.kpi-delta{font-size:0.78rem;margin-top:0.3rem}
.gold{color:var(--gold)}.green{color:var(--green)}.blue{color:var(--blue)}
.purple{color:var(--purple)}.orange{color:var(--ns-orange)}.muted{color:var(--muted)}

/* ── GRIDS ── */
.grid-4{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:1.5rem}
.grid-2{display:grid;grid-template-columns:repeat(2,1fr);gap:1.5rem}
@media(max-width:1100px){.grid-4{grid-template-columns:repeat(2,1fr)}}
@media(max-width:900px){.grid-3,.grid-2{grid-template-columns:1fr}}
@media(max-width:600px){.grid-4{grid-template-columns:1fr}}

/* ── PROGRESS BAR ── */
.bar-wrap{background:rgba(255,255,255,0.06);border-radius:4px;height:6px;margin-top:0.5rem;overflow:hidden}
.bar-fill{height:100%;border-radius:4px;transition:width 0.8s ease}

/* ── STEPS ── */
.step{display:flex;gap:1rem;align-items:flex-start;padding:1.2rem 0;border-bottom:1px solid var(--border)}
.step:last-child{border-bottom:none}
.step-num{
  width:36px;height:36px;min-width:36px;
  background:var(--ns-grad);color:#fff;
  border-radius:10px;display:flex;align-items:center;justify-content:center;
  font-weight:800;font-size:0.9rem;flex-shrink:0;
}
.step-title{font-weight:700;font-size:1rem;margin-bottom:0.25rem}
.step-desc{font-size:0.85rem;color:var(--muted2);line-height:1.6}

/* ── COMPARATIF TABLE ── */
table.compare{width:100%;border-collapse:collapse}
table.compare th{font-size:0.72rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.06em;padding:0.6rem 1rem;border-bottom:2px solid var(--border);text-align:left}
table.compare td{padding:0.7rem 1rem;font-size:0.88rem;border-bottom:1px solid rgba(255,255,255,0.04)}
table.compare tr:last-child td{border-bottom:none}
table.compare tr:hover td{background:rgba(255,255,255,0.02)}
table.compare .highlight td{background:rgba(0,102,204,0.06)}
table.compare .winner td{color:var(--gold);font-weight:700}

/* ── PRODUCT CARDS ── */
.product-card{
  background:var(--card);border:1px solid var(--border);border-radius:16px;
  padding:1.5rem;transition:all 0.2s;cursor:default;
}
.product-card:hover{border-color:rgba(0,102,204,0.35);box-shadow:0 8px 24px rgba(0,102,204,0.1)}
.product-badge{
  display:inline-block;font-size:0.68rem;font-weight:700;text-transform:uppercase;
  letter-spacing:0.07em;padding:0.2rem 0.6rem;border-radius:20px;margin-bottom:0.8rem;
}
.product-badge.hot{background:rgba(255,102,0,0.15);color:var(--ns-orange)}
.product-badge.new{background:rgba(16,185,129,0.12);color:var(--green)}
.product-badge.pro{background:rgba(0,102,204,0.12);color:var(--blue)}
.product-name{font-size:1.2rem;font-weight:800;margin-bottom:0.4rem}
.product-temp{font-size:2rem;font-weight:900;color:var(--gold);line-height:1;margin:0.6rem 0}
.product-desc{font-size:0.83rem;color:var(--muted2);line-height:1.6}
.product-specs{margin-top:1rem;display:flex;flex-direction:column;gap:0.3rem}
.spec-row{display:flex;justify-content:space-between;align-items:center;font-size:0.8rem;padding:0.3rem 0;border-bottom:1px solid rgba(255,255,255,0.04)}
.spec-row:last-child{border-bottom:none}
.spec-key{color:var(--muted)}
.spec-val{font-weight:600}

/* ── INVEST ── */
.invest-point{
  display:flex;gap:0.9rem;align-items:flex-start;padding:0.9rem 0;
  border-bottom:1px solid rgba(255,255,255,0.05);
}
.invest-point:last-child{border-bottom:none}
.invest-icon{color:var(--gold);font-size:1.1rem;flex-shrink:0;margin-top:0.1rem}
.invest-text{font-size:0.88rem;color:var(--muted2);line-height:1.6}

/* ── FORMS ── */
.form-group{margin-bottom:1rem}
label.fl{font-size:0.8rem;font-weight:700;color:var(--muted);display:block;margin-bottom:0.35rem;letter-spacing:0.03em}
select,input[type=number],input[type=text]{
  width:100%;background:rgba(255,255,255,0.04);border:1px solid var(--border);
  border-radius:10px;color:var(--text);padding:0.65rem 0.9rem;font-size:0.9rem;font-family:inherit;
  transition:border-color 0.2s;
}
select:focus,input:focus{border-color:var(--ns-blue);outline:none;background:rgba(0,102,204,0.06)}
option{background:#0d1124}
.checkbox-group{display:flex;flex-wrap:wrap;gap:0.6rem}
.cb-label{display:flex;align-items:center;gap:0.4rem;font-size:0.85rem;cursor:pointer;padding:0.3rem 0.7rem;border:1px solid var(--border);border-radius:8px;transition:all 0.2s}
.cb-label:hover{border-color:rgba(0,102,204,0.3);background:rgba(0,102,204,0.05)}
.cb-label input{width:auto}

/* ── BUTTONS ── */
.btn{display:inline-flex;align-items:center;gap:0.45rem;padding:0.7rem 1.5rem;border-radius:10px;font-size:0.9rem;font-weight:700;border:none;cursor:pointer;font-family:inherit;transition:all 0.25s;text-decoration:none}
.btn-primary{background:var(--ns-grad);color:#fff;box-shadow:0 4px 14px rgba(0,102,204,0.25)}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,102,204,0.4);color:#fff}
.btn-ghost{background:rgba(255,255,255,0.05);color:var(--muted);border:1px solid var(--border)}
.btn-ghost:hover{background:rgba(255,255,255,0.09);color:var(--text)}
.btn-outline{background:transparent;color:var(--ns-blue);border:1.5px solid var(--ns-blue)}
.btn-outline:hover{background:rgba(0,102,204,0.12);color:var(--ns-blue)}

/* ── SIMULATOR PANEL ── */
.sim-layout{display:flex;gap:1.5rem;align-items:flex-start;flex-wrap:wrap}
.sim-controls{width:320px;min-width:280px;flex-shrink:0}
.sim-results{flex:1;min-width:0}
.spin{animation:spin 0.7s linear infinite;display:inline-block}
@keyframes spin{to{transform:rotate(360deg)}}
.updating{opacity:0.55;pointer-events:none;transition:opacity 0.2s}

/* ── DISCLAIMER ── */
.disclaimer{background:rgba(255,183,0,0.05);border:1px solid rgba(255,183,0,0.15);border-radius:10px;padding:0.7rem 1rem;font-size:0.78rem;color:var(--muted);margin-top:1rem}

/* ── CONFIDENTIAL RIBBON ── */
.ribbon{
  background:linear-gradient(90deg,rgba(0,102,204,0.15),rgba(255,102,0,0.1));
  border-bottom:1px solid rgba(0,102,204,0.2);
  padding:0.45rem 2rem;text-align:center;
  font-size:0.74rem;font-weight:700;color:var(--muted);letter-spacing:0.06em;
}

/* ── GAUGE ROW ── */
.gauge-row{display:flex;align-items:center;justify-content:space-between;padding:0.5rem 0;border-bottom:1px solid rgba(255,255,255,0.04)}
.gauge-row:last-child{border-bottom:none}
.gauge-label{font-size:0.82rem;color:var(--muted)}
.gauge-val{font-size:1rem;font-weight:700}

/* ── TEMP COLORS ── */
.temp-high{color:#ff4444}.temp-mid{color:var(--gold)}.temp-low{color:var(--green)}

/* ── MEDIA ── */
@media(max-width:768px){
  .page-hero{min-height:auto;padding:4rem 0}
  .hero-stats{gap:1.5rem}
  .sim-controls{width:100%}
  .ns-nav a:not(.cta){display:none}
}
"""

# ── Header HTML ───────────────────────────────────────────────────────────────

_HEADER_HTML = """
<div class="ribbon">
  🔒 DOCUMENT CONFIDENTIEL — RÉSERVÉ AUX INVESTISSEURS QUALIFIÉS — NEWS-SOLAR © 2026
</div>
<header class="ns-header">
  <div style="display:flex;align-items:center;gap:0.9rem">
    <img src="/static/images/logo_news_solar.png" alt="NEWS SOLAR" class="ns-logo">
    <span class="ns-badge">DÉMO PRIVÉE</span>
  </div>
  <nav class="ns-nav">
    <a href="#hero">Accueil</a>
    <a href="#technologie">Technologie</a>
    <a href="#produits">Produits</a>
    <a href="#investisseurs">Investisseurs</a>
    <a href="#simulateur">Simulateur</a>
    <a href="/auth/logout" class="btn-ghost" style="font-size:0.8rem;padding:0.35rem 0.8rem;border-radius:8px">Déconnexion</a>
  </nav>
</header>
"""

# ── Page principale ───────────────────────────────────────────────────────────

DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NEWS-SOLAR — Espace Investisseurs Privé</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<style>""" + _BASE_CSS + """</style>
</head>
<body>
""" + _HEADER_HTML + """

<!-- ══════════════════ SECTION 1 — HERO ══════════════════ -->
<section class="page-hero" id="hero">
  <div class="hero-content">
    <div class="hero-eyebrow">⚡ Technologie HST — High Solar Temperature — Brevetée à l'international</div>
    <h1>La fin de l'intermittence<br><span class="grad">des énergies renouvelables</span></h1>
    <p>NEWS-SOLAR capte 95&nbsp;% de l'énergie solaire et la stocke jusqu'à 3&nbsp;000°C pour produire en continu 8&nbsp;760&nbsp;h/an : électricité, chaleur, froid, H₂, NH₃, SAF/e-SAF — sans intermittence et dès 25&nbsp;€/MWh.</p>

    <div class="hero-badges">
      <span class="badge blue">🏭 Fabricant français</span>
      <span class="badge gold">⚡ 95% rendement captation</span>
      <span class="badge green">♻️ 100% décarbonation</span>
      <span class="badge orange">📅 8 760 h/an</span>
      <span class="badge">📋 &gt;45 brevets internationaux</span>
    </div>

    <div style="display:flex;gap:1rem;flex-wrap:wrap">
      <a href="#simulateur" class="btn btn-primary">▶&nbsp; Simuler mon projet</a>
      <a href="#technologie" class="btn btn-outline">En savoir plus</a>
    </div>

    <div class="hero-stats">
      <div>
        <div class="hero-stat-val">9,5 MWc</div>
        <div class="hero-stat-lbl">par hectare (10 000 m²)</div>
      </div>
      <div>
        <div class="hero-stat-val">×8</div>
        <div class="hero-stat-lbl">productivité vs PV (cogénération)</div>
      </div>
      <div>
        <div class="hero-stat-val">&gt;25&nbsp;€</div>
        <div class="hero-stat-lbl">/ MWh en grande puissance</div>
      </div>
      <div>
        <div class="hero-stat-val">20%</div>
        <div class="hero-stat-lbl">ROI sur certaines configurations</div>
      </div>
    </div>
  </div>
</section>

<!-- ══════════════════ SECTION 2 — TECHNOLOGIE ══════════════════ -->
<section class="section" id="technologie">
  <div class="section-inner">
    <span class="section-eyebrow">🔬 Technologie HST</span>
    <h2 class="section-title">Comment fonctionne le procédé HST ?</h2>
    <p class="section-sub">Notre centrale solaire à hyper concentration capte 95&nbsp;% de l'énergie solaire, la stocke dans une <strong>Batterie Thermique</strong> permettant une production en continu 8&nbsp;760&nbsp;h/an quelle que soit la météo, restituée sous toutes les formes d'énergies nécessaires.</p>

    <!-- Chaîne 5 étapes -->
    <div class="grid-2" style="margin-bottom:3rem">
      <div class="card">
        <div style="font-size:0.9rem;font-weight:700;color:var(--muted);margin-bottom:1rem;text-transform:uppercase;letter-spacing:0.07em">Chaîne énergétique HST — 5 étapes</div>
        <div class="step">
          <div class="step-num">1</div>
          <div>
            <div class="step-title">Source Solaire</div>
            <div class="step-desc">Le soleil délivre jusqu'à 1&nbsp;000&nbsp;W/m². Nous en captons 95&nbsp;%, soit jusqu'à 9,5&nbsp;MWc thermique par hectare (10&nbsp;000 m²).</div>
          </div>
        </div>
        <div class="step">
          <div class="step-num">2</div>
          <div>
            <div class="step-title">Hyper Concentration ×15&nbsp;000</div>
            <div class="step-desc">Procédé unique au monde et breveté — la lumière est concentrée plus de 15&nbsp;000 fois sur un absorbeur de très faible dimension, générant de très hautes températures avec un rendement optique de 95&nbsp;%. La surface active ne représente que 1/10&nbsp;000 de la surface de réception.</div>
          </div>
        </div>
        <div class="step">
          <div class="step-num">3</div>
          <div>
            <div class="step-title">Batterie Thermique — jusqu'à 3&nbsp;000°C</div>
            <div class="step-desc">Stockage thermique de 1,3 à 1,5&nbsp;MWh/m³ — soit presque 6× une batterie Li-Ion. Rendement 98&nbsp;%, perte thermique &lt;1&nbsp;%/jour, production garantie 8&nbsp;760&nbsp;h/an. Aucun risque d'incendie ni d'explosion. Durée de vie &gt;25&nbsp;ans.</div>
          </div>
        </div>
        <div class="step">
          <div class="step-num">4</div>
          <div>
            <div class="step-title">Conversion Continue</div>
            <div class="step-desc">Convertisseurs thermodynamiques brevetés à cinématique linéaire — rendement 35&nbsp;% (mono-étagé) à 60&nbsp;% (bi-étagé). MTBF &gt;220&nbsp;000 h. Aucune maintenance. Unités hermétiques sans pièces tournantes.</div>
          </div>
        </div>
        <div class="step">
          <div class="step-num">5</div>
          <div>
            <div class="step-title">Applications Multi-Énergies</div>
            <div class="step-desc">Électricité — Chaleur (jusqu'à 1&nbsp;600°C) — Froid (jusqu'à –60°C) — Climatisation — Vapeur — H₂/NH₃ — SAF/e-SAF. Disponibles sur site ou via batterie thermique mobile VHT.</div>
          </div>
        </div>
      </div>

      <!-- Avantages clés -->
      <div style="display:flex;flex-direction:column;gap:1rem">
        <div class="card" style="background:linear-gradient(135deg,rgba(0,102,204,0.08),transparent)">
          <div class="card-title">🏆 Avantages vs PV et CSP</div>
          <div style="margin-top:0.8rem;display:flex;flex-direction:column;gap:0.5rem">
            {% set avs = [
              ('Rendement captation', '95%', 'gold', '20% PV'),
              ('Production annuelle', '8 760 h/an', 'gold', '1 500 h PV'),
              ('Productivite electrique', 'x3 vs PV', 'green', 'Ref. PV'),
              ('Cogeneration', 'x8 vs PV', 'ns-orange', 'Non disponible PV'),
              ('Stockage', 'x1500 vs Li-Ion', 'blue', 'Limite Li-Ion'),
              ('Hydrogene', 'x4 vs ENR', 'green', 'ENR standard'),
              ('Tarif production', 'des 25 EUR/MWh', 'gold', '80-120 EUR PV'),
            ] %}
            {% for label, val, color, ref in avs %}
            <div style="display:flex;align-items:center;justify-content:space-between;padding:0.45rem 0;border-bottom:1px solid rgba(255,255,255,0.04)">
              <span style="font-size:0.83rem;color:var(--muted)">{{ label }}</span>
              <div style="text-align:right">
                <span style="font-weight:700;font-size:0.88rem;color:var(--{{ color }})">{{ val }}</span>
                <span style="font-size:0.72rem;color:var(--muted);margin-left:0.5rem">({{ ref }})</span>
              </div>
            </div>
            {% endfor %}
          </div>
        </div>

        <div class="card">
          <div class="card-title">🌡️ Températures batterie — profil illustratif 24h</div>
          <canvas id="tempChart" height="160"></canvas>
          <div style="display:flex;gap:1rem;margin-top:0.7rem;flex-wrap:wrap">
            <div class="gauge-row" style="flex:1;min-width:150px">
              <span class="gauge-label">T° max batterie</span>
              <span class="gauge-val temp-high">3 000°C</span>
            </div>
            <div class="gauge-row" style="flex:1;min-width:150px">
              <span class="gauge-label">T° sortie process</span>
              <span class="gauge-val temp-mid">jusqu'a 1 600°C</span>
            </div>
          </div>
          <div class="disclaimer">Valeurs temp. illustratives — Non contractuel</div>
        </div>
      </div>
    </div>

    <!-- Comparatif technico-économique -->
    <div class="card" style="margin-bottom:2rem">
      <div class="card-title" style="margin-bottom:1rem">💰 Comparatif technico-économique — base 1 MWc, tarif 80&nbsp;€/MWh</div>
      <div style="overflow-x:auto">
        <table class="compare">
          <tr>
            <th>Technologie</th>
            <th>Heures/an</th>
            <th>Production 1 MWc</th>
            <th>CA annuel</th>
            <th>CA 25 ans</th>
            <th>Ratio</th>
          </tr>
          <tr>
            <td>PV standard (rendement 20%)</td>
            <td class="muted">1 500 h</td>
            <td class="muted">1 500 MWh</td>
            <td class="muted">120 k€</td>
            <td class="muted">3 M€</td>
            <td class="muted">ref.</td>
          </tr>
          <tr class="highlight">
            <td><strong>NEWS-SOLAR HST électricité seule (40%)</strong></td>
            <td class="gold">8 760 h</td>
            <td class="gold">8 760 MWh</td>
            <td class="gold">701 k€</td>
            <td class="gold">17,5 M€</td>
            <td class="gold">×5,8</td>
          </tr>
          <tr class="winner">
            <td><strong>NEWS-SOLAR HST + cogénération</strong></td>
            <td class="gold">8 760 h</td>
            <td class="orange">1,6 MWc elec</td>
            <td class="orange">>1,12 M€</td>
            <td class="orange">28 M€</td>
            <td class="orange">×9,3</td>
          </tr>
        </table>
      </div>
    </div>

    <!-- Pourquoi l'IA -->
    <div class="grid-3">
      {% set ia_points = [
        ('🎯', 'Optimisation production', "Prévision d'ensoleillement par IA, pilotage en temps réel des héliostats, maximisation du rendement thermique et anticipation des variations météo."),
        ('🔋', 'Gestion stockage thermique', "Modélisation dynamique de la batterie, optimisation des cycles de charge/décharge via machine learning, prédiction des pics de demande."),
        ('🔌', 'Intégration réseau', "Equilibrage temps réel, coordination avec d'autres sources (batteries, H₂, réseau), optimisation des ventes d'énergie sur les marchés spot."),
        ('🛠️', 'Maintenance prédictive', "Surveillance continue des capteurs, détection précoce d'anomalies, planification d'interventions avant panne — MTBF global >220 000 h."),
        ('📊', 'Reporting & ROI', "Tableau de bord de performance en temps réel, maximisation du retour sur investissement grâce à la data et aux algorithmes proprietaires."),
        ('⚡', 'IA brevetee FR2505822', "Notre IA propriétaire brevetée gère les opérations énergétiques boursières pour la solution GigaPower — jusqu'à 58,74 M€/an de CA sur 1 GWh."),
      ] %}
      {% for icon, title, desc in ia_points %}
      <div class="card">
        <div class="card-icon">{{ icon }}</div>
        <div style="font-weight:700;font-size:0.95rem;margin-bottom:0.5rem">{{ title }}</div>
        <div style="font-size:0.83rem;color:var(--muted2);line-height:1.65">{{ desc }}</div>
      </div>
      {% endfor %}
    </div>
  </div>
</section>

<!-- ══════════════════ SECTION 3 — PRODUITS ══════════════════ -->
<section class="section" id="produits" style="background:var(--bg2)">
  <div class="section-inner">
    <span class="section-eyebrow">🏭 Catalogue produits</span>
    <h2 class="section-title">Gamme de produits NEWS-SOLAR</h2>
    <p class="section-sub">Tous nos équipements sont pilotés par notre IA adaptative propriétaire. Disponibles en vente, location, leasing ou PPA 5 à 25 ans. Réservés aux professionnels agréés.</p>

    <!-- Concentrateurs -->
    <div class="card-title" style="font-size:0.85rem;margin-bottom:1rem;color:var(--muted2)">⚡ Concentrateurs solaires — Séries 2025</div>
    <div class="grid-3" style="margin-bottom:2rem">
      {% set concentrateurs = [
        ('X 300', 'CPC', 'hot', 'Cylindro-parabolique', '< 450°C', 'hot', '100 m²+', '1 axe', 'Entrée de gamme — toitures, eau chaude, process agro-alimentaire. Film autonettoyant optionnel.'),
        ('X 3 000', 'PC', 'pro', 'Parabolique standard', '< 1 200°C', 'gold', '10–1 000 m²', '2 axes', 'Conversion thermique ou electrique. Nacelle multi-convertisseurs. Tracker haute precision.'),
        ('X 12 000', 'HC < 1 MWc', 'new', 'Hyper concentrateur', '< 2 500°C', 'green', '10–1 100 m²', '2 axes', 'Micro-centrale 10 à 25 m² delivrant 9,5 à 24 KWc th. Toiture ou champ solaire.'),
        ('X 15 000', 'HC > 1 MWc', 'hot', 'Hyper concentrateur forte puissance', '< 3 000°C', 'temp-high', '> 1 000 m²', '2 axes', 'Ideal installations > 1 MWc. Puissance max > 10 GW. Absorbeur 360° version forte puissance.'),
        ('X 30 000 Magnifier', 'MAG', 'pro', 'Hyper injection', '> 4 000°C', 'temp-high', 'Sur commande', 'Combine avec X12000/X15000', 'Densites lumineuses > 10 KWc/cm². Couplage FOS. Applications experimentales et industrielles.'),
        ('X 60 000 SOF', 'SOF', 'new', 'Solar Optical Fiber', '> 5 000°C', 'temp-high', 'Sur commande', 'Transport distant', 'Concentration native > x60 000 par compression optique. Thermophotolyse. Dissociation eau.'),
      ] %}
      {% for ref, serie, badge_type, type_name, temp, temp_color, surface, tracker, desc in concentrateurs %}
      <div class="product-card">
        <div class="product-badge {{ badge_type }}">Série {{ serie }}</div>
        <div class="product-name">{{ ref }}</div>
        <div style="font-size:0.82rem;color:var(--muted);margin-bottom:0.4rem">{{ type_name }}</div>
        <div class="product-temp {{ temp_color }}">{{ temp }}</div>
        <div class="product-specs">
          <div class="spec-row"><span class="spec-key">Surface</span><span class="spec-val">{{ surface }}</span></div>
          <div class="spec-row"><span class="spec-key">Suivi solaire</span><span class="spec-val">{{ tracker }}</span></div>
          <div class="spec-row"><span class="spec-key">Film optique</span><span class="spec-val gold">95% rendement</span></div>
        </div>
        <div style="font-size:0.79rem;color:var(--muted2);margin-top:0.8rem;line-height:1.55">{{ desc }}</div>
      </div>
      {% endfor %}
    </div>

    <!-- Tarifs concentrateurs -->
    <div class="card" style="margin-bottom:2rem">
      <div class="card-title" style="margin-bottom:1rem">💶 Tarifs concentrateurs série X 12 000 (< 1 MWc) — commande minimum</div>
      <div style="overflow-x:auto">
        <table class="compare">
          <tr><th>Modele</th><th>Surface</th><th>Puissance th</th><th>Prix HT (a partir de)</th><th>Commande min</th><th>Delai</th></tr>
          <tr><td><strong>T10</strong></td><td>10 m²</td><td class="gold">9,5 KWc Th</td><td>9 700 €</td><td>x10 unites</td><td>~2 mois</td></tr>
          <tr class="highlight"><td><strong>T25</strong></td><td>25 m²</td><td class="gold">24 KWc Th</td><td>15 800 €</td><td>x6 unites</td><td>~2 mois</td></tr>
          <tr><td><strong>T50</strong></td><td>50 m²</td><td class="gold">47 KWc Th</td><td>Sur demande</td><td>Sur demande</td><td>Sur demande</td></tr>
          <tr><td><strong>T250</strong></td><td>250 m²</td><td class="gold">235 KWc Th</td><td>Sur demande</td><td>Sur demande</td><td>Sur demande</td></tr>
          <tr><td><strong>T1.000</strong></td><td>1 100 m²</td><td class="gold">1 MWc Th</td><td>Sur demande</td><td>Sur demande</td><td>Sur demande</td></tr>
        </table>
      </div>
    </div>

    <!-- Batteries thermiques -->
    <div class="card-title" style="font-size:0.85rem;margin-bottom:1rem;color:var(--muted2)">🔋 Batteries thermiques THT — Modeles TB</div>
    <div class="grid-3" style="margin-bottom:2rem">
      {% set batteries = [
        ('TB 10', '< 10 MWh', '1x container 10\'\'', '2,99 x 2,43 x 2,59 m', '410 k€ HT', 'x2 minimum', '~2 mois'),
        ('TB 25', '< 25 MWh', '1x container 15\'\'', '4,50 x 2,43 x 2,59 m', '922 k€ HT', 'x1 minimum', '>2 mois'),
        ('TB 50', '< 50 MWh', '1x container 20\'\'', '6,05 x 2,43 x 2,59 m', '1 660 k€ HT', 'x1 minimum', '>2,5 mois'),
        ('TB 100', '< 100 MWh', '1x container 40\'\'', '12,10 x 2,43 x 2,59 m', '2 500 k€ HT', 'x1 minimum', '>3 mois'),
        ('TB 1.000', '< 1 GWh', 'Batiment industriel', '25 x 10 x 3,2 m (800 m³)', 'Nous consulter', 'Sur demande', '>8 mois'),
      ] %}
      {% for nom, capa, format_, dims, prix, cmd, delai in batteries %}
      <div class="product-card">
        <div class="product-badge hot">Batterie thermique</div>
        <div class="product-name">{{ nom }}</div>
        <div class="product-temp gold">{{ capa }}</div>
        <div class="product-specs">
          <div class="spec-row"><span class="spec-key">Format</span><span class="spec-val">{{ format_ }}</span></div>
          <div class="spec-row"><span class="spec-key">Dimensions</span><span class="spec-val" style="font-size:0.75rem">{{ dims }}</span></div>
          <div class="spec-row"><span class="spec-key">Prix HT</span><span class="spec-val green">{{ prix }}</span></div>
          <div class="spec-row"><span class="spec-key">Commande min</span><span class="spec-val">{{ cmd }}</span></div>
          <div class="spec-row"><span class="spec-key">Delai livraison</span><span class="spec-val">{{ delai }}</span></div>
          <div class="spec-row"><span class="spec-key">Duree de vie</span><span class="spec-val gold">>25 ans</span></div>
          <div class="spec-row"><span class="spec-key">Risque incendie</span><span class="spec-val green">Aucun</span></div>
        </div>
      </div>
      {% endfor %}
    </div>

    <!-- Convertisseurs -->
    <div class="card-title" style="font-size:0.85rem;margin-bottom:1rem;color:var(--muted2)">⚡ Convertisseurs electriques thermodynamiques — rendement 35 a 60%</div>
    <div class="grid-2" style="margin-bottom:2rem">
      <div class="card">
        <div class="product-badge pro">Série MTC — Mono-etagé 35%</div>
        <div style="font-size:0.85rem;color:var(--muted2);margin-bottom:1rem;line-height:1.6">Free piston et turbo générateur solarisé mono-étagé. Unités hermétiques sans maintenance — MTBF &gt;220&nbsp;000 h. Source chaude 180 à 1&nbsp;000°C.</div>
        <table class="compare" style="font-size:0.82rem">
          <tr><th>Modele</th><th>Puissance</th><th>Dimensions</th><th>Tarif</th></tr>
          <tr><td>MTC 4</td><td class="gold">4 KWc</td><td>L300 D150 mm</td><td>980 €</td></tr>
          <tr class="highlight"><td>MTC 12</td><td class="gold">12 KWc</td><td>L540 D270 mm</td><td>2 940 €</td></tr>
          <tr><td>MTC 30</td><td class="gold">30 KWc</td><td>L756 D324 mm</td><td>8 820 €</td></tr>
          <tr><td>MTC 50</td><td class="gold">60 KWc</td><td>L1058 D389 mm</td><td>17 640 €</td></tr>
          <tr><td>MTC 100</td><td class="gold">120 KWc</td><td>L1375 D466 mm</td><td>Nous consulter</td></tr>
          <tr><td>MTC 200</td><td class="gold">250 KWc</td><td>L1788 D560 mm</td><td>Nous consulter</td></tr>
        </table>
      </div>
      <div class="card">
        <div class="product-badge hot">Série TSC — Bi-etagé 60%</div>
        <div style="font-size:0.85rem;color:var(--muted2);margin-bottom:1rem;line-height:1.6">Turbo générateur solarisé bi-étagé — rendement maxi 60%. Unités 30 à 1&nbsp;000 KWc. Maintenance limitée, durée de vie projetée 25 ans.</div>
        <table class="compare" style="font-size:0.82rem">
          <tr><th>Modele</th><th>Puissance</th><th>Dimensions</th><th>Tarif</th></tr>
          <tr><td>TSC 30</td><td class="orange">30 KWc</td><td>L1134 D486 mm</td><td>Nous consulter</td></tr>
          <tr class="highlight"><td>TSC 60</td><td class="orange">60 KWc</td><td>L1587 D583 mm</td><td>Nous consulter</td></tr>
          <tr><td>TSC 100</td><td class="orange">120 KWc</td><td>L2064 D699 mm</td><td>Nous consulter</td></tr>
          <tr><td>TSC 250</td><td class="orange">250 KWc</td><td>L2683 D840 mm</td><td>Nous consulter</td></tr>
          <tr><td>TSC 500</td><td class="orange">500 KWc</td><td>L4024 D1260 mm</td><td>@ 2026</td></tr>
          <tr><td>TSC 1.000</td><td class="orange">1 000 KWc</td><td>L6037 D1889 mm</td><td>@ 2026</td></tr>
        </table>
      </div>
    </div>

    <!-- H2 / GigaPower -->
    <div class="grid-2">
      <div class="card">
        <div class="card-icon">💧</div>
        <div style="font-weight:800;font-size:1.1rem;margin-bottom:0.6rem">Generateurs H₂ — SOEC</div>
        <p style="font-size:0.85rem;color:var(--muted2);line-height:1.65;margin-bottom:1rem">Notre procede de production d'H₂ vert atteint 30% de rendement (mono) et 50% (bi-etage) grace aux stacks SOEC de rendement >90% a 750°C — soit 4× les ENR standards — 8760 h/an. Production possible de NH₃ et SAF/e-SAF avec hautes pressions natives sans compresseur dédié.</p>
        <div class="grid-2" style="gap:0.8rem">
          <div class="card2">
            <div class="product-badge pro">H2S10</div>
            <div style="font-weight:700">10 KWc · 3,6 Nm³/h</div>
            <div style="font-size:0.8rem;color:var(--muted);margin-top:0.3rem">120 cellules SOEC · 650–850°C · Delai >90 j</div>
          </div>
          <div class="card2">
            <div class="product-badge hot">H2S100</div>
            <div style="font-weight:700">105 KWc · >36 Nm³/h</div>
            <div style="font-size:0.8rem;color:var(--muted);margin-top:0.3rem">1 200 cellules SOEC · 650–850°C · Delai >120 j</div>
          </div>
        </div>
      </div>
      <div class="card" style="background:linear-gradient(135deg,rgba(255,183,0,0.06),rgba(0,102,204,0.06))">
        <div class="card-icon">⚡</div>
        <div style="font-weight:800;font-size:1.1rem;margin-bottom:0.6rem">GigaPower — Trading energetique</div>
        <p style="font-size:0.85rem;color:var(--muted2);line-height:1.65;margin-bottom:1rem">Centrale electro-solaire autonome a hyper concentration et tres forte puissance — stockage 1 GWh a >1 TWh. Achat d'electricite a prix SPOT negatif, stockage THT, revente aux pointes tarifaires.</p>
        <div style="background:rgba(255,183,0,0.08);border:1px solid rgba(255,183,0,0.2);border-radius:10px;padding:1rem;margin-bottom:0.8rem">
          <div style="font-size:0.82rem;color:var(--muted);margin-bottom:0.3rem">Exemple 2025 — installation 1 GWh</div>
          <div class="kpi-value gold">58,74 M€</div>
          <div style="font-size:0.8rem;color:var(--muted2);margin-top:0.3rem">Delta tarifaire de 160,93 €/MWh (de –3 a +157,93 €/MWh)</div>
        </div>
        <div style="font-size:0.75rem;color:var(--muted)">Brevets : FR2505603 · FR2505822 · FR2505867</div>
      </div>
    </div>
  </div>
</section>

<!-- ══════════════════ SECTION 4 — INVESTISSEURS ══════════════════ -->
<section class="section" id="investisseurs">
  <div class="section-inner">
    <span class="section-eyebrow">💼 Espace Investisseurs</span>
    <h2 class="section-title">Opportunite d'investissement a fort ROI</h2>
    <p class="section-sub">Rejoignez la transition energetique avec un rendement attractif jusqu'a 15% sur certaines configurations. Marche annuel mondial &gt;10&nbsp;000 Milliards $/an.</p>

    <div class="grid-2" style="margin-bottom:2rem;align-items:start">
      <!-- Pourquoi investir -->
      <div class="card">
        <div class="card-title" style="margin-bottom:1rem">✅ Pourquoi investir dans NEWS-SOLAR ?</div>
        {% set invest_points = [
          ('📈', 'Rendement superieur aux placements traditionnels — ROI jusqu\'a 20% sur certaines configurations.'),
          ('💰', 'Flux de revenus stables et recurrents sur 5 a 30 ans via contrats PPA (Power Purchase Agreement).'),
          ('🌱', 'Impact environnemental positif, conformite ESG, credits carbone >100 €/T @ 2030.'),
          ('🛡️', 'Decorrelation des marches fossiles, protection contre la volatilite, contrats a prix garantis.'),
          ('🏗️', 'Constitution de SPV (Special Purpose Vehicle) independantes et portant entierement le projet.'),
          ('🌍', 'Marche >10 000 Mds$/an — electricite + thermique — positionnement strategique mondial.'),
          ('📋', 'Protection industrielle haute level : >45 brevets internationaux @ 2025.'),
          ('✈️', 'Signature en cours avec de grands operateurs ENR, projets Power 1 (1 MWc) et Power 10 (10 MWc).'),
          ('♻️', 'Materiaux 100% recyclables — fusion via nos procedes solaires HST — empreinte quasi nulle.'),
          ('📊', 'Avantages fiscaux et subventions disponibles selon pays d\'implantation.'),
        ] %}
        {% for icon, text in invest_points %}
        <div class="invest-point">
          <span class="invest-icon">{{ icon }}</span>
          <span class="invest-text">{{ text }}</span>
        </div>
        {% endfor %}
      </div>

      <!-- KPI investissement & profils -->
      <div style="display:flex;flex-direction:column;gap:1rem">
        <div class="card" style="background:linear-gradient(135deg,rgba(0,102,204,0.1),rgba(255,102,0,0.06))">
          <div class="card-title">💡 Indicateurs financiers (ordre de grandeur)</div>
          <div style="display:flex;flex-direction:column;gap:0.5rem;margin-top:0.8rem">
            {% set fin_kpis = [
              ('ROI installations Power', 'jusqu\'a 20%', 'gold'),
              ('Tarif vente energie', 'des 25 EUR/MWh', 'gold'),
              ('Duree contrats PPA', '5 a 30 ans', 'green'),
              ('CA annuel 1 MWc (elec+chaleur)', '>1 M€/an', 'green'),
              ('CA 25 ans vs PV (coef)', 'x9,3', 'orange'),
              ('H2 vert cout production', 'x4 inferieur aux ENR std', 'blue'),
              ('Trading GigaPower 1 GWh', '>58 M€ CA/an (ex. 2025)', 'gold'),
            ] %}
            {% for label, val, color in fin_kpis %}
            <div class="gauge-row">
              <span class="gauge-label">{{ label }}</span>
              <span class="gauge-val {{ color }}">{{ val }}</span>
            </div>
            {% endfor %}
          </div>
        </div>

        <div class="card">
          <div class="card-title" style="margin-bottom:0.8rem">👤 Profils d'investisseurs recherches</div>
          {% set profils = [
            ('🏦', 'Fonds d\'investissement et institutionnels', 'Actifs verts rentables, conformite ESG'),
            ('🏭', 'Grands groupes industriels', 'Decarbonation, optimisation bilan carbone, tarifs stables'),
            ('🏢', 'PME/ETI consommatrices d\'energie', 'Tarifs avantageux, autonomie energetique 365 j/an'),
            ('👨‍👩‍👧', 'Particuliers & Family Offices', 'Via vehicules d\'investissement dedies (SPV)'),
            ('🌆', 'Collectivites territoriales', 'Transition energetique, souverainete, emploi local'),
          ] %}
          {% for icon, type_, desc in profils %}
          <div style="display:flex;gap:0.8rem;align-items:flex-start;padding:0.6rem 0;border-bottom:1px solid rgba(255,255,255,0.04)">
            <span style="font-size:1.3rem;flex-shrink:0">{{ icon }}</span>
            <div>
              <div style="font-weight:700;font-size:0.88rem">{{ type_ }}</div>
              <div style="font-size:0.79rem;color:var(--muted2)">{{ desc }}</div>
            </div>
          </div>
          {% endfor %}
        </div>

        <div class="card" style="background:rgba(255,183,0,0.06);border-color:rgba(255,183,0,0.2)">
          <div style="font-size:0.85rem;font-weight:700;color:var(--gold);margin-bottom:0.5rem">📧 Contact investissement</div>
          <div style="font-size:0.88rem;color:var(--muted2);line-height:1.65">
            <strong>NEWS-SOLAR</strong> — 2 rue Madier de Montjau, 26000 Valence<br>
            📧 <a href="mailto:contact@news-solar.com" style="color:var(--ns-blue)">contact@news-solar.com</a><br>
            📞 +33 09 85 188 787 / +33 07 69 66 68 62<br>
            <em style="font-size:0.75rem;color:var(--muted)">Cette offre s'inscrit dans une demarche de financement prive reservee a un cercle restreint d'investisseurs qualifies.</em>
          </div>
        </div>
      </div>
    </div>

    <!-- Solutions PPA -->
    <div class="card">
      <div class="card-title" style="margin-bottom:1rem">⚡ Nos modeles d'investissement</div>
      <div class="grid-3">
        {% set modeles = [
          ('Vente d\'energie PPA', '📋', 'Nous finançons, installons et gerons la centrale. Vous achetez l\'energie a tarif garanti 5-25 ans, sans investissement initial. Revenus via Delta tarifaire sur contrats PPA.', 'green'),
          ('Investissement direct dans une SPV', '🏗️', 'Vous investissez dans une SPV entierement dedie au projet. Production autofinancee, retour sur capital via revenus de revente d\'energies. ROI jusqu\'a 20%.', 'gold'),
          ('Trading energetique GigaPower', '⚡', 'Achat d\'electricite a prix spot negatif, stockage dans nos batteries THT, revente aux pointes. Gestion par notre IA brevetee FR2505822. Exemple 2025 : 58,74 M€/an sur 1 GWh.', 'orange'),
        ] %}
        {% for title, icon, desc, color in modeles %}
        <div style="background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:12px;padding:1.3rem">
          <div style="font-size:1.7rem;margin-bottom:0.6rem">{{ icon }}</div>
          <div style="font-weight:700;font-size:0.95rem;color:var(--{{ color }});margin-bottom:0.6rem">{{ title }}</div>
          <div style="font-size:0.83rem;color:var(--muted2);line-height:1.65">{{ desc }}</div>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>
</section>

<!-- ══════════════════ SECTION 5 — SIMULATEUR ══════════════════ -->
<section class="section" id="simulateur" style="background:var(--bg2)">
  <div class="section-inner">
    <span class="section-eyebrow">🔬 Simulateur interactif</span>
    <h2 class="section-title">Calculez votre projet HST</h2>
    <p class="section-sub">Estimez la production annuelle d'energies et la rentabilite de votre installation HST NEWS-SOLAR selon votre superficie et localisation.</p>

    <div class="sim-layout">
      <!-- CONTROLS -->
      <div class="sim-controls">
        <div class="card">
          <div style="font-size:0.8rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.07em;margin-bottom:1rem">Parametres de simulation</div>

          <div class="form-group">
            <label class="fl">🌍 Region / ensoleillement</label>
            <select id="p_region">
              {% for key, val in irradiance_regions.items() %}
              <option value="{{ key }}" {% if key=="france_sud" %}selected{% endif %}>{{ val.label }}</option>
              {% endfor %}
            </select>
          </div>

          <div class="form-group">
            <label class="fl">📐 Surface installee (hectares)</label>
            <input type="number" id="p_surface" value="1" min="0.1" max="10000" step="0.5">
            <div style="display:flex;gap:0.4rem;margin-top:0.5rem">
              {% for v in [0.5, 1, 5, 10, 50] %}
              <button class="btn btn-ghost" style="flex:1;padding:0.3rem;font-size:0.72rem;border-radius:6px" onclick="setHa({{ v }})">{{ v }}ha</button>
              {% endfor %}
            </div>
          </div>

          <div class="form-group">
            <label class="fl">⚡ Convertisseur electrique</label>
            <select id="p_converter">
              <option value="mono">Mono-etage — 35% rdt</option>
              <option value="bi">Bi-etage — 60% rdt (haute perf.)</option>
              <option value="photostatic">PhotoStatique — 42% rdt</option>
            </select>
          </div>

          <div class="form-group">
            <label class="fl">🧩 Energies souhaitees</label>
            <div class="checkbox-group" style="flex-direction:column;gap:0.4rem">
              <label class="cb-label"><input type="checkbox" value="electricity" checked> ⚡ Electricite</label>
              <label class="cb-label"><input type="checkbox" value="heat" checked> 🔥 Chaleur process</label>
              <label class="cb-label"><input type="checkbox" value="cold" checked> ❄️ Froid industriel</label>
              <label class="cb-label"><input type="checkbox" value="h2" checked> 💧 Hydrogene H₂</label>
              <label class="cb-label"><input type="checkbox" value="nh3"> 🌿 Ammoniac NH₃</label>
            </div>
          </div>

          <button class="btn btn-primary" style="width:100%;margin-top:0.5rem" onclick="runSim()">
            <span id="btn-icon">▶</span> Calculer
          </button>
          <div id="sim-info" style="margin-top:0.6rem;font-size:0.76rem;color:var(--muted);text-align:center"></div>
        </div>
      </div>

      <!-- RESULTS -->
      <div class="sim-results" id="sim-results">
        <!-- Hero résumé -->
        <div style="background:linear-gradient(135deg,rgba(0,102,204,0.1),rgba(255,102,0,0.06));border:1px solid var(--border);border-radius:14px;padding:1.1rem 1.4rem;margin-bottom:1.2rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem">
          <div>
            <div style="font-size:0.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.3rem">Simulation active</div>
            <div style="font-size:0.9rem">
              <span id="hero-region" style="font-weight:700;color:var(--text)">{{ sim.region_label }}</span> ·
              <span id="hero-surface" style="color:var(--gold)">{{ sim.surface_ha }} ha</span> ·
              <span id="hero-conv" style="color:var(--muted2)">{{ sim.converter_type }} ({{ sim.conv_eff_pct }}%)</span>
            </div>
          </div>
          <div style="text-align:right">
            <div style="font-size:0.72rem;color:var(--muted)">Production continue</div>
            <div style="font-size:1.5rem;font-weight:900;color:var(--gold)">8 760 h/an</div>
          </div>
        </div>

        <!-- KPI énergétiques -->
        <div class="grid-4" style="margin-bottom:1.2rem">
          <div class="card">
            <div class="card-title">Electricite</div>
            <div class="kpi-value gold"><span id="kpi-elec">{{ "{:,.0f}".format(sim.electricity_mwh) }}</span><span class="kpi-unit">MWh/an</span></div>
            <div class="bar-wrap"><div class="bar-fill" id="bar-elec" style="background:var(--gold)"></div></div>
            <div style="font-size:0.76rem;color:var(--muted);margin-top:0.5rem" id="kpi-elec-info">{{ sim.converter_type }} · {{ sim.conv_eff_pct }}% rdt</div>
          </div>
          <div class="card">
            <div class="card-title">Chaleur process</div>
            <div class="kpi-value orange"><span id="kpi-heat">{{ "{:,.0f}".format(sim.heat_mwh) }}</span><span class="kpi-unit">MWh/an</span></div>
            <div class="bar-wrap"><div class="bar-fill" id="bar-heat" style="background:var(--ns-orange)"></div></div>
            <div style="font-size:0.76rem;color:var(--muted);margin-top:0.5rem">Chaleur directe THT</div>
          </div>
          <div class="card">
            <div class="card-title">Froid industriel</div>
            <div class="kpi-value blue"><span id="kpi-cold">{{ "{:,.0f}".format(sim.cold_mwh) }}</span><span class="kpi-unit">MWh/an</span></div>
            <div class="bar-wrap"><div class="bar-fill" id="bar-cold" style="width:30%;background:var(--blue)"></div></div>
            <div style="font-size:0.76rem;color:var(--muted);margin-top:0.5rem">Cycle absorption</div>
          </div>
          <div class="card">
            <div class="card-title">Hydrogene H₂</div>
            <div class="kpi-value green"><span id="kpi-h2">{{ "{:,.0f}".format(sim.h2_kg) }}</span><span class="kpi-unit">kg/an</span></div>
            <div class="bar-wrap"><div class="bar-fill" id="bar-h2" style="width:55%;background:var(--green)"></div></div>
            <div style="font-size:0.76rem;color:var(--muted);margin-top:0.5rem">Electrolyse HTE 60%</div>
          </div>
        </div>

        <!-- Finance + Comparatif PV -->
        <div class="grid-2" style="margin-bottom:1.2rem">
          <div class="card">
            <div class="card-title" style="margin-bottom:0.8rem">💰 Indicateurs financiers estimatifs</div>
            <div style="margin-bottom:1rem">
              <div style="font-size:0.75rem;color:var(--muted)">CAPEX estimatif</div>
              <div class="kpi-value gold" style="font-size:1.6rem"><span id="kpi-capex">{{ "{:,.0f}".format(sim.capex_eur / 1000) }}</span> k€</div>
            </div>
            <div class="gauge-row"><span class="gauge-label">Revenus annuels</span><span class="gauge-val green"><span id="kpi-rev">{{ "{:,.0f}".format(sim.revenue_annual_eur / 1000) }}</span> k€</span></div>
            <div class="gauge-row"><span class="gauge-label">ROI estime</span><span class="gauge-val gold"><span id="kpi-roi">{{ sim.roi_years }}</span> ans</span></div>
            <div class="gauge-row"><span class="gauge-label">CA cumule 25 ans</span><span class="gauge-val orange"><span id="kpi-ca25">{{ "{:,.0f}".format(sim.revenue_25y / 1000) }}</span> k€</span></div>
          </div>
          <div class="card">
            <div class="card-title" style="margin-bottom:0.8rem">📊 Comparatif vs PV standard (meme surface)</div>
            <div style="font-size:0.75rem;color:var(--muted);margin-bottom:0.3rem">Productivite electrique NEWS-SOLAR HST vs PV</div>
            <div class="kpi-value gold" style="font-size:2.2rem">×<span id="kpi-ratio">{{ sim.electricity_ratio }}</span></div>
            <div class="gauge-row" style="margin-top:0.8rem"><span class="gauge-label">PV standard (900 KWc/ha)</span><span class="gauge-val muted"><span id="kpi-pv">{{ "{:,.0f}".format(sim.pv_electricity_mwh) }}</span> MWh/an</span></div>
            <div class="gauge-row"><span class="gauge-label">NEWS-SOLAR HST</span><span class="gauge-val green"><span id="kpi-hst">{{ "{:,.0f}".format(sim.electricity_mwh) }}</span> MWh/an</span></div>
            <div class="gauge-row"><span class="gauge-label">Heures prod. HST</span><span class="gauge-val gold">8 760 h/an</span></div>
            <div class="gauge-row"><span class="gauge-label">Heures prod. PV</span><span class="gauge-val muted">~1 500 h/an</span></div>
          </div>
        </div>

        <div class="disclaimer">
          ⚠️ <strong>Document confidentiel — Espace investisseurs prive.</strong> Toutes les valeurs sont a titre illustratif — non contractuel. Donnees non libres de droit — Copyright NEWS-SOLAR 2026. Brevets internationaux deposes.
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Footer -->
<footer style="background:var(--bg);border-top:1px solid var(--border);padding:2rem;text-align:center">
  <div style="max-width:1300px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem">
    <div style="display:flex;align-items:center;gap:0.8rem">
      <img src="/static/images/logo_news_solar.png" alt="NEWS SOLAR" style="height:36px;object-fit:contain">
      <span style="font-size:0.8rem;color:var(--muted)">Fabricant francais de technologies ENR innovantes — Valence (26)</span>
    </div>
    <div style="font-size:0.76rem;color:var(--muted)">
      © 2026 NEWS-SOLAR · contact@news-solar.com · Tous brevets deposes · Document prive non contractuel
    </div>
  </div>
</footer>

<script>
// ── Graphique temperature initial ─────────────────────────────────────────
const tp0 = {{ sim.temp_profile | tojson }};
const tempChart = new Chart(document.getElementById('tempChart'), {
  type:'line',
  data:{
    labels: tp0.hours.map(h => h+'h'),
    datasets:[
      {label:'Batterie (°C)',data:tp0.battery_temp,borderColor:'#ff4444',backgroundColor:'rgba(255,68,68,0.07)',tension:0.4,pointRadius:0,borderWidth:2},
      {label:'Sortie process (°C)',data:tp0.output_temp,borderColor:'#FFB700',backgroundColor:'rgba(255,183,0,0.07)',tension:0.4,pointRadius:0,borderWidth:2}
    ]
  },
  options:{
    plugins:{legend:{labels:{color:'#8892a4',font:{size:10}}}},
    scales:{
      x:{ticks:{color:'#8892a4',font:{size:9}},grid:{color:'rgba(255,255,255,0.04)'}},
      y:{ticks:{color:'#8892a4',font:{size:9}},grid:{color:'rgba(255,255,255,0.04)'}}
    },
    animation:{duration:600},maintainAspectRatio:true
  }
});

// ── Init barres KPI ────────────────────────────────────────────────────────
(function initBars(){
  const therm = {{ sim.stored_thermal_mwh }} || 1;
  document.getElementById('bar-elec').style.width = Math.min({{ sim.electricity_mwh }} / therm * 100, 100) + '%';
  document.getElementById('bar-heat').style.width = Math.min({{ sim.heat_mwh }} / therm * 100, 100) + '%';
})();

// ── Helpers ────────────────────────────────────────────────────────────────
function fmt(n){ return Number(n).toLocaleString('fr-FR',{maximumFractionDigits:0}); }
function setHa(v){ document.getElementById('p_surface').value = v; runSim(); }

// ── Simulation dynamique ───────────────────────────────────────────────────
let _deb = null;
function schedSim(){ clearTimeout(_deb); _deb = setTimeout(runSim, 500); }

['p_region','p_converter'].forEach(id => document.getElementById(id).addEventListener('change', runSim));
document.getElementById('p_surface').addEventListener('input', schedSim);
document.querySelectorAll('.checkbox-group input').forEach(cb => cb.addEventListener('change', runSim));

async function runSim(){
  const icon = document.getElementById('btn-icon');
  const info = document.getElementById('sim-info');
  const res  = document.getElementById('sim-results');
  icon.textContent = '⟳'; icon.classList.add('spin');
  res.classList.add('updating');
  info.textContent = 'Calcul en cours...';

  const outputs = [...document.querySelectorAll('.checkbox-group input:checked')].map(c => c.value);
  const body = {
    region:         document.getElementById('p_region').value,
    surface_ha:     parseFloat(document.getElementById('p_surface').value) || 1,
    converter_type: document.getElementById('p_converter').value,
    outputs:        outputs.length ? outputs : ['electricity']
  };
  try {
    const r  = await fetch('/newssolar/api/simulate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    const d  = await r.json();
    applyResults(d, body);
    info.textContent = '✓ Mis a jour';
  } catch(e) {
    info.textContent = 'Erreur de calcul';
  } finally {
    icon.textContent = '▶'; icon.classList.remove('spin');
    res.classList.remove('updating');
  }
}

function applyResults(d, params){
  // Hero
  document.getElementById('hero-region').textContent  = d.region_label;
  document.getElementById('hero-surface').textContent = d.surface_ha + ' ha';
  const cl = {mono:'mono (35%)',bi:'bi-etage (60%)',photostatic:'photostatique (42%)'}[params.converter_type] || params.converter_type;
  document.getElementById('hero-conv').textContent = cl;

  // KPI
  const therm = d.stored_thermal_mwh || 1;
  document.getElementById('kpi-elec').textContent    = fmt(d.electricity_mwh);
  document.getElementById('bar-elec').style.width    = Math.min(d.electricity_mwh / therm * 100, 100) + '%';
  document.getElementById('kpi-elec-info').textContent = params.converter_type + ' · ' + d.conv_eff_pct + '% rdt';
  document.getElementById('kpi-heat').textContent    = fmt(d.heat_mwh);
  document.getElementById('bar-heat').style.width    = Math.min(d.heat_mwh / therm * 100, 100) + '%';
  document.getElementById('kpi-cold').textContent    = fmt(d.cold_mwh);
  document.getElementById('kpi-h2').textContent      = fmt(d.h2_kg);

  // Finance
  document.getElementById('kpi-capex').textContent   = fmt(d.capex_eur / 1000);
  document.getElementById('kpi-rev').textContent     = fmt(d.revenue_annual_eur / 1000);
  document.getElementById('kpi-roi').textContent     = d.roi_years;
  document.getElementById('kpi-ca25').textContent    = fmt(d.revenue_25y / 1000);

  // Comparatif
  document.getElementById('kpi-ratio').textContent   = d.electricity_ratio;
  document.getElementById('kpi-pv').textContent      = fmt(d.pv_electricity_mwh);
  document.getElementById('kpi-hst').textContent     = fmt(d.electricity_mwh);
}

// ── Smooth scroll depuis nav ────────────────────────────────────────────────
document.querySelectorAll('.ns-nav a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    e.preventDefault();
    document.querySelector(a.getAttribute('href'))?.scrollIntoView({behavior:'smooth'});
  });
});
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if(target){ e.preventDefault(); target.scrollIntoView({behavior:'smooth'}); }
  });
});
</script>
</body></html>
"""

# ── Simulateur standalone ─────────────────────────────────────────────────────

SIMULATION_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NEWS-SOLAR — Simulateur HST</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<style>""" + _BASE_CSS + """
.result-panel{display:none}
.result-panel.visible{display:block}
</style>
</head>
<body>
""" + _HEADER_HTML + """

<div style="background:linear-gradient(135deg,rgba(0,102,204,0.1),rgba(255,102,0,0.07));padding:2.5rem 2rem;border-bottom:1px solid var(--border)">
  <div style="max-width:1300px;margin:0 auto">
    <span style="display:inline-block;background:rgba(0,102,204,0.12);border:1px solid rgba(0,102,204,0.25);color:var(--blue);font-size:0.76rem;font-weight:700;padding:0.25rem 0.75rem;border-radius:20px;margin-bottom:0.8rem;letter-spacing:0.05em">🔬 Simulateur interactif HST</span>
    <h1 style="font-size:2rem;font-weight:800;margin-bottom:0.5rem">Calculez votre production <span style="color:var(--gold)">multi-energies</span></h1>
    <p style="color:var(--muted2);max-width:560px;line-height:1.68">Estimez la production annuelle et la rentabilite de votre installation HST selon votre superficie et region.</p>
  </div>
</div>

<div style="max-width:1300px;margin:0 auto;padding:2rem">
<div class="grid-2">
  <div class="card">
    <div style="font-weight:700;margin-bottom:1.2rem;font-size:1rem">⚙️ Parametres</div>
    <form id="sf">
      <div class="form-group">
        <label class="fl">Region / localisation</label>
        <select name="region" id="sel_region">
          {% for key, val in irradiance_regions.items() %}
          <option value="{{ key }}" {% if key=="france_sud" %}selected{% endif %}>{{ val.label }}</option>
          {% endfor %}
        </select>
      </div>
      <div class="form-group">
        <label class="fl">Surface installee (hectares)</label>
        <input type="number" name="surface_ha" id="inp_surface" value="1" min="0.1" max="10000" step="0.1">
        <div style="font-size:0.75rem;color:var(--muted);margin-top:0.3rem">1 ha = 10 000 m² · Toiture, ombriere ou terrain</div>
      </div>
      <div class="form-group">
        <label class="fl">Convertisseur electrique</label>
        <select name="converter_type" id="sel_converter">
          <option value="mono">Mono-etage — rendement 35%</option>
          <option value="bi">Bi-etage — rendement 60% (haute performance)</option>
          <option value="photostatic">PhotoStatique multi-jonctions — rendement 42%</option>
        </select>
      </div>
      <div class="form-group">
        <label class="fl">Energies souhaitees en sortie</label>
        <div class="checkbox-group" style="flex-direction:column;gap:0.4rem">
          <label class="cb-label"><input type="checkbox" name="outputs" value="electricity" checked> ⚡ Electricite</label>
          <label class="cb-label"><input type="checkbox" name="outputs" value="heat" checked> 🔥 Chaleur</label>
          <label class="cb-label"><input type="checkbox" name="outputs" value="cold"> ❄️ Froid</label>
          <label class="cb-label"><input type="checkbox" name="outputs" value="h2"> 💧 H₂</label>
          <label class="cb-label"><input type="checkbox" name="outputs" value="nh3"> 🌿 NH₃</label>
        </div>
      </div>
      <button type="submit" class="btn btn-primary" id="btnSim" style="width:100%">▶ Lancer la simulation</button>
    </form>
  </div>

  <div>
    <div id="placeholder" class="card" style="text-align:center;padding:3rem;color:var(--muted)">
      <div style="font-size:2.5rem;margin-bottom:0.8rem">🔬</div>
      <div style="font-weight:600;margin-bottom:0.4rem">Configurez les parametres</div>
      <div style="font-size:0.85rem">Les resultats apparaissent ici</div>
    </div>
    <div id="resultPanel" class="result-panel">
      <div class="card" style="margin-bottom:1rem">
        <div style="font-size:0.78rem;color:var(--muted);margin-bottom:0.8rem" id="res_region">—</div>
        <div class="grid-2" id="res_kpis" style="gap:0.8rem"></div>
      </div>
      <div class="card" style="margin-bottom:1rem">
        <div class="card-title" style="margin-bottom:0.8rem">Production comparee vs PV standard</div>
        <canvas id="chartCompare" height="160"></canvas>
      </div>
      <div class="card">
        <div class="card-title" style="margin-bottom:0.8rem">Synthese financiere estimative</div>
        <table id="res_finance" style="width:100%;border-collapse:collapse"></table>
        <div class="disclaimer">⚠️ Valeurs estimatives — Non contractuel — NEWS-SOLAR 2026</div>
      </div>
    </div>
  </div>
</div>
</div>

<script>
let compareChart = null;
document.getElementById('sf').addEventListener('submit', async e => {
  e.preventDefault();
  const btn = document.getElementById('btnSim');
  btn.innerHTML = '<span class="spin">⟳</span> Calcul...'; btn.disabled = true;
  const fd = new FormData(e.target);
  const outputs = [...document.querySelectorAll('input[name=outputs]:checked')].map(c=>c.value);
  const payload = {region:fd.get('region'),surface_ha:parseFloat(fd.get('surface_ha')),converter_type:fd.get('converter_type'),outputs};
  try {
    const r = await fetch('/newssolar/api/simulate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    renderResults(await r.json());
  } catch(err){ alert('Erreur: '+err); }
  finally { btn.innerHTML='▶ Lancer la simulation'; btn.disabled=false; }
});
function fmt(n){return new Intl.NumberFormat('fr-FR').format(Math.round(n))}
function renderResults(d){
  document.getElementById('placeholder').style.display='none';
  document.getElementById('resultPanel').classList.add('visible');
  document.getElementById('res_region').textContent = d.region_label+' · '+d.surface_ha+' ha · '+d.converter_type+' ('+d.conv_eff_pct+'%)';
  const kpis=[
    {label:'Electricite',val:fmt(d.electricity_mwh)+' MWh/an',c:'var(--gold)'},
    {label:'Chaleur',val:fmt(d.heat_mwh)+' MWh/an',c:'var(--ns-orange)'},
    {label:'Froid',val:fmt(d.cold_mwh)+' MWh/an',c:'var(--blue)'},
    {label:'H₂',val:fmt(d.h2_kg)+' kg/an',c:'var(--green)'},
    {label:'NH₃',val:d.nh3_tons>0?fmt(d.nh3_tons)+' t/an':'—',c:'var(--purple)'},
    {label:'Stockage brut',val:fmt(d.stored_thermal_mwh)+' MWh/an',c:'var(--muted)'},
  ];
  document.getElementById('res_kpis').innerHTML=kpis.map(k=>
    `<div style="background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:10px;padding:0.8rem">
      <div style="font-size:0.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em">${k.label}</div>
      <div style="font-size:1.2rem;font-weight:800;color:${k.c};margin-top:0.2rem">${k.val}</div>
    </div>`).join('');
  if(compareChart)compareChart.destroy();
  compareChart=new Chart(document.getElementById('chartCompare'),{type:'bar',data:{labels:['PV standard','NEWS-SOLAR HST'],datasets:[{data:[d.pv_electricity_mwh,d.electricity_mwh],backgroundColor:['rgba(100,100,120,0.5)','rgba(255,183,0,0.65)'],borderColor:['rgba(100,100,120,0.8)','#FFB700'],borderWidth:1,borderRadius:6}]},options:{plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#8892a4'},grid:{color:'rgba(255,255,255,0.04)'}},y:{ticks:{color:'#8892a4'},grid:{color:'rgba(255,255,255,0.04)'}}}}});
  document.getElementById('res_finance').innerHTML=`
    <tr style="border-bottom:1px solid rgba(255,255,255,0.08)"><th style="text-align:left;padding:0.5rem 0.8rem;font-size:0.75rem;color:var(--muted);text-transform:uppercase">Poste</th><th style="text-align:left;padding:0.5rem 0.8rem;font-size:0.75rem;color:var(--muted);text-transform:uppercase">Valeur</th></tr>
    <tr><td style="padding:0.6rem 0.8rem;font-size:0.85rem;border-bottom:1px solid rgba(255,255,255,0.04)">CAPEX estimatif</td><td style="padding:0.6rem 0.8rem;font-size:0.85rem;font-weight:700;color:var(--gold);border-bottom:1px solid rgba(255,255,255,0.04)">${fmt(d.capex_eur)} €</td></tr>
    <tr><td style="padding:0.6rem 0.8rem;font-size:0.85rem;border-bottom:1px solid rgba(255,255,255,0.04)">Revenus annuels estimes</td><td style="padding:0.6rem 0.8rem;font-size:0.85rem;font-weight:700;color:var(--green);border-bottom:1px solid rgba(255,255,255,0.04)">${fmt(d.revenue_annual_eur)} €/an</td></tr>
    <tr><td style="padding:0.6rem 0.8rem;font-size:0.85rem;border-bottom:1px solid rgba(255,255,255,0.04)">ROI estime</td><td style="padding:0.6rem 0.8rem;font-size:0.85rem;font-weight:700;color:var(--gold);border-bottom:1px solid rgba(255,255,255,0.04)">${d.roi_years} ans</td></tr>
    <tr><td style="padding:0.6rem 0.8rem;font-size:0.85rem;border-bottom:1px solid rgba(255,255,255,0.04)">CA cumule 25 ans</td><td style="padding:0.6rem 0.8rem;font-size:0.85rem;font-weight:700;color:var(--ns-orange);border-bottom:1px solid rgba(255,255,255,0.04)">${fmt(d.revenue_25y)} €</td></tr>
    <tr><td style="padding:0.6rem 0.8rem;font-size:0.85rem">Productivite elec. vs PV</td><td style="padding:0.6rem 0.8rem;font-size:0.85rem;font-weight:700;color:var(--gold)">x${d.electricity_ratio}</td></tr>
  `;
}
</script>
</body></html>
"""
