/**
 * Gestionnaire de calques custom dark-mode
 * Remplace le panneau Leaflet par défaut par un panneau groupé avec recherche.
 * Ce script s'exécute APRÈS le chargement complet de la page.
 */
(function () {
  "use strict";

  /* ===================== CONFIG GROUPES ===================== */
  var GROUPS = [
    { icon: "\uD83D\uDDFA\uFE0F", title: "Fonds de carte",      re: /^(Satellite|Fond OSM|OpenStreetMap)/i, isBase: true },
    { icon: "\uD83D\uDCD0", title: "Cadastre & Parcelles",       re: /cadastre|parcell/i },
    { icon: "\uD83C\uDFD7\uFE0F", title: "Urbanisme & PLU",     re: /urbanisme|plu|zone urba|prescription|secteur|info surf|assiette/i },
    { icon: "\u26A1",     title: "\u00C9nergie & R\u00E9seau",   re: /poste|bt(?!\s*\w)|hta|capac|potentiel solaire|enedis|consommation/i },
    { icon: "\uD83C\uDF3F", title: "Environnement",              re: /natur|ppri|georisques|zaer/i },
    { icon: "\uD83D\uDC04", title: "Agriculture",                re: /rpg|\u00e9leveur|agri/i },
    { icon: "\uD83C\uDFE2", title: "Activit\u00E9s & Commerce", re: /sirene|entreprise|parking|friche/i }
  ];

  /* ===================== DOT COLORS ===================== */
  function dotColor(n) {
    n = n.toLowerCase();
    if (/satellite|imagery/i.test(n)) return "#6366f1";
    if (/osm/i.test(n))               return "#22c55e";
    if (/cadastre|parcell/i.test(n))   return "#f59e0b";
    if (/urbanisme|plu|zone/i.test(n)) return "#8b5cf6";
    if (/prescription/i.test(n))       return "#a78bfa";
    if (/bt(?!\s*\w)/i.test(n))        return "#22d3ee";
    if (/hta|capac/i.test(n))          return "#f97316";
    if (/solaire/i.test(n))            return "#fbbf24";
    if (/ppri/i.test(n))               return "#ef4444";
    if (/georisques/i.test(n))         return "#dc2626";
    if (/zaer/i.test(n))               return "#10b981";
    if (/natur/i.test(n))              return "#34d399";
    if (/rpg/i.test(n))                return "#84cc16";
    if (/eleveur|éleveur/i.test(n))    return "#a3e635";
    if (/sirene|entreprise/i.test(n))  return "#3b82f6";
    if (/parking/i.test(n))            return "#64748b";
    if (/friche/i.test(n))             return "#78716c";
    if (/consommation|enedis/i.test(n))return "#06b6d4";
    return "#94a3b8";
  }

  /* ===================== INIT ===================== */
  function initLayerControl() {
    var panel = document.querySelector(".leaflet-control-layers");
    if (!panel) { console.log("[LC] Pas de panneau Leaflet trouvé"); return; }

    /* --- Empêcher double init --- */
    if (panel.dataset.lcInit === "1") return;
    panel.dataset.lcInit = "1";

    var list = panel.querySelector(".leaflet-control-layers-list");
    if (!list) { console.log("[LC] Pas de liste trouvée"); return; }

    /* ---- COLLECTER COUCHES ---- */
    var baseLayers = [], overlays = [];
    list.querySelectorAll(".leaflet-control-layers-base label").forEach(function (lbl) {
      baseLayers.push({ input: lbl.querySelector("input"), name: (lbl.textContent || "").trim() });
    });
    list.querySelectorAll(".leaflet-control-layers-overlays label").forEach(function (lbl) {
      overlays.push({ input: lbl.querySelector("input"), name: (lbl.textContent || "").trim() });
    });

    var totalCount = baseLayers.length + overlays.length;
    if (totalCount === 0) { console.log("[LC] Aucune couche détectée"); return; }

    /* ---- CLASSER EN GROUPES ---- */
    var groups = GROUPS.map(function (g) {
      return { icon: g.icon, title: g.title, re: g.re, isBase: g.isBase || false, layers: g.isBase ? baseLayers.slice() : [] };
    });
    var otherGroup = { icon: "\uD83D\uDCCC", title: "Autres couches", layers: [] };

    overlays.forEach(function (o) {
      var placed = false;
      for (var i = 0; i < groups.length; i++) {
        if (groups[i].re && groups[i].re.test(o.name)) { groups[i].layers.push(o); placed = true; break; }
      }
      if (!placed) otherGroup.layers.push(o);
    });
    if (otherGroup.layers.length) groups.push(otherGroup);

    /* ---- BUILD HTML ---- */
    var html = '<div class="lc-header"><span>\uD83D\uDDC2\uFE0F Calques</span><span class="lc-count">' + totalCount + "</span></div>";
    html += '<div class="lc-search"><input type="text" placeholder="Rechercher un calque\u2026" id="lcFilter"></div>';
    html += '<div class="lc-scroll" id="lcScroll">';

    groups.forEach(function (g, gi) {
      if (!g.layers.length) return;
      html += '<div class="lc-group" data-gi="' + gi + '">';
      html += '<div class="lc-group-hdr" data-gi="' + gi + '">' + g.icon + " " + g.title;
      html += '<span class="lc-group-cnt">(' + g.layers.length + ")</span>";
      html += '<span class="lc-chevron">\u25BC</span></div>';
      html += '<div class="lc-group-body" data-bi="' + gi + '">';
      g.layers.forEach(function (l, li) {
        html += '<div class="lc-item" data-name="' + l.name.toLowerCase().replace(/"/g, "") + '">';
        html += '<label>';
        html += '<span class="lc-dot" style="background:' + dotColor(l.name) + '"></span>';
        html += l.name;
        html += "</label></div>";
      });
      html += "</div></div>";
    });
    html += "</div>";

    /* ---- INJECT CONTAINER ---- */
    var container = document.createElement("div");
    container.className = "lc-custom-root";
    container.innerHTML = html;
    panel.insertBefore(container, list);

    /* ---- MOVE INPUTS ---- */
    groups.forEach(function (g, gi) {
      g.layers.forEach(function (l, li) {
        var grpEl = container.querySelector('[data-gi="' + gi + '"] .lc-group-body');
        if (!grpEl) return;
        var items = grpEl.querySelectorAll(".lc-item");
        var item = items[li];
        if (!item || !l.input) return;
        var lbl = item.querySelector("label");
        l.input.style.cssText = "accent-color:#3b82f6;width:15px;height:15px;cursor:pointer;flex-shrink:0;";
        lbl.prepend(l.input);
      });
    });

    /* ---- COLLAPSE TOGGLE ---- */
    container.querySelectorAll(".lc-group-hdr").forEach(function (hdr) {
      hdr.addEventListener("click", function () {
        var idx = this.getAttribute("data-gi");
        var body = container.querySelector('[data-bi="' + idx + '"]');
        if (!body) return;
        body.classList.toggle("hidden");
        this.classList.toggle("collapsed");
      });
    });

    /* ---- SEARCH ---- */
    var filterInput = container.querySelector("#lcFilter");
    if (filterInput) {
      filterInput.addEventListener("input", function () {
        var q = this.value.toLowerCase();
        container.querySelectorAll(".lc-item").forEach(function (item) {
          var nm = item.getAttribute("data-name") || "";
          item.style.display = (!q || nm.indexOf(q) >= 0) ? "" : "none";
        });
        container.querySelectorAll(".lc-group").forEach(function (grp) {
          var hasVisible = false;
          grp.querySelectorAll(".lc-item").forEach(function (it) {
            if (it.style.display !== "none") hasVisible = true;
          });
          grp.style.display = hasVisible ? "" : "none";
        });
      });
      /* empêcher la fermeture du panneau quand on tape */
      filterInput.addEventListener("mousedown", function(e) { e.stopPropagation(); });
      filterInput.addEventListener("click", function(e) { e.stopPropagation(); });
    }

    /* ---- GARDER LE PANNEAU OUVERT ---- */
    panel.addEventListener("mouseleave", function () {
      /* léger délai avant de collapse pour éviter les faux départs */
      this._closeTimeout = setTimeout(function () {
        panel.classList.remove("leaflet-control-layers-expanded");
      }, 400);
    });
    panel.addEventListener("mouseenter", function () {
      clearTimeout(this._closeTimeout);
      panel.classList.add("leaflet-control-layers-expanded");
    });

    console.log("[LC] \u2705 Custom layer control initialisé (" + totalCount + " calques, " + groups.filter(function(g){return g.layers.length}).length + " groupes)");
  }

  /* ===================== BOOT ===================== */
  function boot() {
    /* Attend que le DOM + Leaflet soient prêts avec retry */
    var attempts = 0;
    var maxAttempts = 30;
    function tryInit() {
      attempts++;
      var panel = document.querySelector(".leaflet-control-layers");
      if (panel) {
        initLayerControl();
      } else if (attempts < maxAttempts) {
        setTimeout(tryInit, 200);
      } else {
        console.log("[LC] Abandon après " + maxAttempts + " tentatives");
      }
    }
    tryInit();
  }

  /* Le script est injecté APRÈS les scripts Folium, donc le DOM est prêt */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { boot(); });
  } else {
    /* readyState = interactive ou complete : lancer immédiatement */
    boot();
  }
})();
