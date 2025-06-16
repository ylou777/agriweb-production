// ============================================================================
// main.js – version avancée avec calques Urbanisme séparés dans LayerControl
// ============================================================================

const LAYER_CONFIG = {
  rpg:            { label: "RPG Parcelles", color: "green" },
  postes_bt:      { label: "Postes BT", color: "orange" },
  postes_hta:     { label: "Postes HTA", color: "red" },
  capacites_reseau: { label: "Capacités Réseau", color: "purple" },
  eleveurs:       { label: "Éleveurs", color: "purple" },
  parcelles:      { label: "Parcelles", color: "blue" },
  api_cadastre:   { label: "Cadastre (API IGN)", color: "#FF6600" },
  api_nature:     { label: "Nature (API IGN)", color: "#22AA22" },
  plu:            { label: "PLU", color: "#880000" },
  parkings:       { label: "Parkings", color: "darkgreen" },
  friches:        { label: "Friches", color: "brown" },
  solaire:        { label: "Potentiel Solaire", color: "gold" },
  zaer:           { label: "ZAER", color: "cyan" },
  sirene:         { label: "Entreprises Sirene", color: "darkred" }
  // ! Ne mets pas ici les sous-couches urbanisme, elles sont dynamiques !
};
window.lastDeptResults = [];
let overlaysControl = null;
let dynamicLayers = {};

// --------- UI sliders ---------
function setupSliders() {
  [
    ["sirene_radius", "sirene_radius_val", " km"],
    ["ht_max_distance", "htMaxVal", " m"],
    ["bt_max_distance", "btMaxVal", " m"],
    ["capacite_max_distance", "capaciteMaxVal", " m"],
    ["sirene_radius_commune", "sireneCommVal", " km"],
    ["minSurface", "minSurfaceVal", " ha"],
    ["maxSurface", "maxSurfaceVal", " ha"],
    ["ht_max_distance_dept", "htMaxValDept", " m"],
    ["bt_max_distance_dept", "btMaxValDept", " m"],
    ["capacite_max_distance_dept", "capaciteMaxValDept", " m"],
  ].forEach(([id, out, unit]) => {
    const s = document.getElementById(id), o = document.getElementById(out);
    if (s && o) {
      o.textContent = s.value + unit;
      s.addEventListener("input", () => (o.textContent = s.value + unit));
    }
  });
}
function htmlifyField (key, value) {
  if (typeof value === "string" && /^https?:\/\//i.test(value)) {
    const anchorText = key.replace(/^lien_/, "")
                          .replace(/_/g, " ")
                          .replace(/\b\w/g, c => c.toUpperCase());
    return `<a href="${value}" target="_blank" rel="noopener">${anchorText}</a>`;
  }
  return value;
}
function buildPopup (properties, extra = {}) {
  let out = "";
  for (const [k, v] of Object.entries(properties || {}))
    out += `<b>${k}:</b> ${htmlifyField(k, v)}<br>`;
  for (const [k, v] of Object.entries(extra))
    out += `<b>${k}:</b> ${v}<br>`;
  return out;
}


function getMapFrame() {
  return document.getElementById("mapFrame")?.contentWindow;
}
function getBaseLayers() {
  const m = getMapFrame();
  if (m && typeof m.getBaseLayers === "function") return m.getBaseLayers();
  return { "Satellite": m?.sat, "OSM": m?.osm };
}

// --------- LAYERS CONTROL ---------
function updateLeafletLayersControl() {
  const m = getMapFrame();
  if (!m || !m.L || !m.map) return;
  if (overlaysControl) {
    try { m.map.removeControl(overlaysControl); } catch {}
  }
  overlaysControl = m.L.control.layers(getBaseLayers(), dynamicLayers, { position: "topright" }).addTo(m.map);
}

// --------- LAYER DISPLAY ---------
function displayAllLayers(data) {
  const m = getMapFrame();
  if (!m || !m.L || !m.map) return;
  Object.values(dynamicLayers).forEach(l => { try { m.map.removeLayer(l); } catch {} });
  dynamicLayers = {};

  Object.entries(data).forEach(([layerKey, val]) => {
    // Urbanisme (plusieurs sous-couches indépendantes)
    if (layerKey === "api_urbanisme" && val && typeof val === "object" && !Array.isArray(val) && !val.type) {
      Object.entries(val).forEach(([subkey, subval]) => {
        if (!subval || !subval.type || !subval.features || subval.features.length === 0) return;
        const subLayerName = "Urbanisme – " + subkey.replace(/-/g, " ");
        const style = { color: "#2040C0", weight: 2 };
        const leafletLayer = m.L.geoJSON(subval, {
          style,
          onEachFeature: function (feature, layer) {
            let popup = "";
            if (feature.properties)
              for (const [k, v] of Object.entries(feature.properties))
                popup += `<b>${k}:</b> ${htmlifyField(k, v)}<br>`;
            if (popup) layer.bindPopup(popup);
          }
        });
        dynamicLayers[subLayerName] = leafletLayer;
        leafletLayer.addTo(m.map);
      });
      return;
    }

    // Normalisation (toujours obtenir un FeatureCollection)
    if (!val || (Array.isArray(val) && val.length === 0)) return;
    let geojson = null;
    if (val.type === "FeatureCollection" && Array.isArray(val.features) && val.features.length) geojson = val;
    else if (val.type === "Feature" && val.geometry) geojson = { type: "FeatureCollection", features: [val] };
    else if (Array.isArray(val) && val[0] && val[0].type === "Feature" && val[0].geometry) geojson = { type: "FeatureCollection", features: val };
    if (!geojson) return;

    const label = LAYER_CONFIG[layerKey]?.label || layerKey;
    const style = LAYER_CONFIG[layerKey]?.color ? { color: LAYER_CONFIG[layerKey].color } : {};

    // ----------- Postes BT ----------- (icône 1 éclair jaune)
    if (layerKey === "postes_bt") {
      const leafletLayer = m.L.geoJSON(geojson, {
        pointToLayer: function (feature, latlng) {
          return m.L.marker(latlng, {
            icon: m.L.divIcon({
              html: `<span style="font-size:1.8em;color:#FFD700;">&#9889;</span>`,
              className: 'bt-marker',
              iconSize: [32, 32],
              iconAnchor: [16, 32]
            })
          });
        },
        onEachFeature: function (feature, layer) {
          let popup = "";
          if (feature.properties) {
            for (const [k, v] of Object.entries(feature.properties)) {
              popup += `<b>${k}:</b> ${htmlifyField(k, v)}<br>`;

            }
          }
          if (popup) layer.bindPopup(popup);
        }
      });
      dynamicLayers[label] = leafletLayer;
      leafletLayer.addTo(m.map);
      return;
    }

    // ----------- Postes HTA ----------- (icône 2 éclairs orange)
    if (layerKey === "postes_hta") {
      const leafletLayer = m.L.geoJSON(geojson, {
        pointToLayer: function (feature, latlng) {
          return m.L.marker(latlng, {
            icon: m.L.divIcon({
              html: `<span style="font-size:1.8em;color:orange;">&#9889;&#9889;</span>`,
              className: 'hta-marker',
              iconSize: [32, 32],
              iconAnchor: [16, 32]
            })
          });
        },
        onEachFeature: function (feature, layer) {
          let popup = "";
          if (feature.properties) {
            for (const [k, v] of Object.entries(feature.properties)) {
              popup += `<b>${k}:</b> ${htmlifyField(k, v)}<br>`;

            }
          }
          if (popup) layer.bindPopup(popup);
        }
      });
      dynamicLayers[label] = leafletLayer;
      leafletLayer.addTo(m.map);
      return;
    }

    // --------- CAS GENERAL ---------
    const leafletLayer = m.L.geoJSON(geojson, {
      style,
      onEachFeature: function (feature, layer) {
        let popup = "";
        if (feature.properties) {
          for (const [k, v] of Object.entries(feature.properties)) {
            popup += `<b>${k}:</b> ${htmlifyField(k, v)}<br>`;

          }
        }
        if (popup) layer.bindPopup(popup);
      }
    });
    dynamicLayers[label] = leafletLayer;
    leafletLayer.addTo(m.map);
  });

  updateLeafletLayersControl();
}

// --------- INFO PANEL ---------
function updateInfoPanel(arr) {
  let c = arr.length, p = 0, e = 0;
  arr.forEach(r => {
    for (const [key, val] of Object.entries(r)) {
      if (key === "eleveurs") {
        if (Array.isArray(val)) e += val.length;
        else if (val && val.type === "FeatureCollection" && Array.isArray(val.features)) e += val.features.length;
      }
      if (val && val.type === "FeatureCollection" && Array.isArray(val.features)) p += val.features.length;
      if (Array.isArray(val) && val[0] && val[0].type === "Feature") p += val.length;
      if (Array.isArray(val) && typeof val[0] === "object" && val[0] && (val[0].coords || val[0].geometry)) p += val.length;
    }
  });
  document.getElementById("info-panel").innerHTML =
    `<div class="alert alert-info mb-0">Communes : ${c} – Objets : ${p} – Éleveurs : ${e}</div>`;
}

// --------- FUSION DES RÉSULTATS SSE ---------
function mergeResults(arr) {
  const expectedKeys = Object.keys(LAYER_CONFIG);
  const res = {};
  expectedKeys.forEach(k => { res[k] = []; });
  arr.forEach(obj => {
    for (const [k, v] of Object.entries(obj)) {
      if (!res[k]) res[k] = [];
      if (v?.type === "FeatureCollection" && Array.isArray(v.features)) {
        res[k] = res[k].concat(v.features);
      } else if (Array.isArray(v) && v[0]?.type === "Feature") {
        res[k] = res[k].concat(v);
      }
    }
  });
  Object.keys(res).forEach(k => {
    res[k] = { type: "FeatureCollection", features: res[k] };
  });
  return res;
}

// --------- RECHERCHE UNIFIÉE (ADRESSE / COORDONNÉES) ---------
async function handleUnifiedSearch(e) {
  e.preventDefault();

  switchMap("/map.html", async () => {
    const v = document.getElementById("search_input").value.trim();
    if (!v) {
      alert("Saisissez une adresse (ex : Limoges) ou des coordonnées (ex : 45.85, 1.25)");
      return;
    }

    function parseLatLonInput(val) {
      try {
        const obj = JSON.parse(val);
        if (obj.type === "Point" && Array.isArray(obj.coordinates)) {
          let [lon, lat] = obj.coordinates;
          if (
            typeof lat === "number" && typeof lon === "number" &&
            Math.abs(lat) <= 90 && Math.abs(lon) <= 180
          ) {
            return { lat, lon };
          }
        }
      } catch {}
      const parts = val.split(",").map(x => parseFloat(x.trim()));
      if (parts.length === 2 && parts.every(n => !isNaN(n))) {
        let [a, b] = parts;
        if (Math.abs(a) <= 90 && Math.abs(b) <= 180) return { lat: a, lon: b };
        if (Math.abs(b) <= 90 && Math.abs(a) <= 180) return { lat: b, lon: a };
      }
      return null;
    }

    const coords = parseLatLonInput(v);
    const ps = new URLSearchParams();
    if (coords) {
      ps.append("lat", coords.lat);
      ps.append("lon", coords.lon);
    } else {
      ps.append("address", v);
    }
    ps.append("sirene_radius", document.getElementById("sirene_radius").value);

    try {
      const res = await fetch("/search_by_address?" + ps.toString());
      if (!res.ok) {
        alert("Erreur serveur : " + res.status);
        return;
      }
      const data = await res.json();
      if (data.error) {
        alert(data.error);
        return;
      }
      console.log("[Unifiée] Données reçues:", data);
      displayAllLayers(data);
      updateInfoPanel([data]);
      const m = getMapFrame();
      if (data.lat && data.lon && m?.setView) {
        let z = 14;
        if (data.parcelles && data.parcelles.features && data.parcelles.features.length === 1) z = 16;
        if (data.rpg && data.rpg.features && data.rpg.features.length === 1) z = 16;
        m.setView(data.lat, data.lon, z);
      }
    } catch (err) {
      alert("Erreur de requête : " + (err.message || err));
    }
  });
}

// --------- RECHERCHE PAR COMMUNE ---------
async function handleCommuneSearch() {
  switchMap("/map.html", async () => {
    const commune = document.getElementById("commune")?.value.trim();
    if (!commune) return alert("Commune requise.");
    const ps = new URLSearchParams({
      commune,
      culture: document.getElementById("culture")?.value || "",
      min_area_ha: document.getElementById("minSurface")?.value || 0,
      max_area_ha: document.getElementById("maxSurface")?.value || 1e9,
      ht_max_distance: document.getElementById("ht_max_distance")?.value || 5000,
      bt_max_distance: document.getElementById("bt_max_distance")?.value || 2000,
      sirene_radius: document.getElementById("sirene_radius_commune")?.value || 0.05
    });
    try {
      const res = await fetch("/search_by_commune?" + ps.toString());
      const data = await res.json();
      if (data.error) return alert(data.error);
      displayAllLayers(data);
      updateInfoPanel([data]);
      const m = getMapFrame();
      if (data.lat && data.lon && m?.setView) m.setView(data.lat, data.lon, 13);
    } catch (err) { alert("Erreur lors de la recherche par commune : " + err); }
  });
}

// --------- RECHERCHE DEPARTEMENT SSE ---------
function handleDeptSearch() {
  switchMap("/static/map1.html", () => {
    const dept = document.getElementById("departmentInput")?.value.trim();
    if (!dept) return alert("Département requis.");
    const types = [];
    if (document.getElementById("filterHTA")?.checked) types.push("HTA");
    if (document.getElementById("filterBT")?.checked) types.push("BT");
    if (types.length === 0) return alert("Sélectionnez au moins un type de réseau.");
    const params = {
      department: dept,
      min_area_ha: document.getElementById("minSurface")?.value || "",
      max_area_ha: document.getElementById("maxSurface")?.value || "",
      bt_max_distance: document.getElementById("bt_max_distance_dept")?.value || "",
      ht_max_distance: document.getElementById("ht_max_distance_dept")?.value || "",
      want_eleveurs: true,
      exclude_nature: document.getElementById("excludeNature")?.checked || false,
      exclude_historic: document.getElementById("excludeBuildings")?.checked || false,
      culture: document.getElementById("rpgType")?.value || "",
      reseau_types: types.join(",")
    };
    const ps = new URLSearchParams(params);
    const logEl = document.getElementById("deptLog");
    if (logEl) logEl.textContent = "";
    updateInfoPanel([]);
    const m = getMapFrame();
    if (m?.clearMap) m.clearMap();
    window.lastDeptResults = [];
    const results = window.lastDeptResults;
    let es = null;
    try {
      es = new EventSource("/generate_reports_by_dept_sse?" + ps.toString());
    } catch {
      if (logEl) logEl.textContent += "Erreur SSE (connexion)\n";
      return;
    }
    if (!es) return;
    es.addEventListener("progress", e => {
      if (logEl) { logEl.textContent += e.data + "\n"; logEl.scrollTop = logEl.scrollHeight; }
    });
    es.addEventListener("result", e => {
      const r = JSON.parse(e.data);
      results.push(r);
      const merged = mergeResults(results);
      displayAllLayers(merged);
      updateInfoPanel(results);
      const m = getMapFrame();
      if (r.lat && r.lon && m?.setView) m.setView(r.lat, r.lon, 11);
    });
    es.addEventListener("end", e => {
      if (logEl) logEl.textContent += e.data + "\n";
      es.close();
    });
    es.onerror = () => {
      if (logEl) logEl.textContent += "❌ Erreur SSE\n";
      es.close();
    };
  });
}

// --------- RAPPORTS ---------
function generateReport() {
  const lat = document.getElementById("latitude")?.value;
  const lon = document.getElementById("longitude")?.value;
  const address = document.getElementById("address")?.value;
  if (!lat || !lon) return alert("Recherchez d’abord.");
  const fd = new FormData();
  fd.append("lat", lat); fd.append("lon", lon); fd.append("address", address || "");
  fetch("/rapport", { method: "POST", body: fd })
    .then(r => r.text()).then(html => { const w = window.open(); w.document.write(html); w.document.close(); });
}
function generateCommuneReport() {
  const commune = document.getElementById("commune")?.value.trim();
  if (!commune) return alert("Commune requise !");
  const params = new URLSearchParams({
    commune,
    culture: document.getElementById("culture")?.value || "",
    min_area_ha: document.getElementById("minSurface")?.value || 0,
    max_area_ha: document.getElementById("maxSurface")?.value || 1e9,
    ht_max_distance: document.getElementById("ht_max_distance")?.value || 5000,
    bt_max_distance: document.getElementById("bt_max_distance")?.value || 2000,
    sirene_radius: document.getElementById("sirene_radius_commune")?.value || 0.05
  });
  window.open(`/rapport_commune?${params.toString()}`, "_blank");
}
function generateDeptReport() {
  if (!window.lastDeptResults || window.lastDeptResults.length === 0) {
    alert("Faites d'abord une recherche départementale !");
    return;
  }
  const w = window.open("", "_blank");
  if (!w) {
    alert("Impossible d'ouvrir un nouvel onglet. Vérifiez que les popups ne sont pas bloqués.");
    return;
  }
  fetch('/rapport_departement_post', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: window.lastDeptResults })
  })
    .then(res => res.text())
    .then(html => {
      w.document.open();
      w.document.write(html);
      w.document.close();
    })
    .catch(err => {
      w.close();
      alert("Erreur lors de la génération du rapport : " + err);
    });
}

// --------- SWITCH MAP ---------
function switchMap(target = "/map.html", onReady) {
  const iframe = document.getElementById("mapFrame");
  if (!iframe) return;
  if (!iframe.src.endsWith(target)) {
    iframe.src = target;
    iframe.onload = () => { if (onReady) setTimeout(onReady, 70); };
  } else {
    if (onReady) setTimeout(onReady, 1);
  }
}

// --------- DOM READY ---------
window.addEventListener("DOMContentLoaded", () => {
  setupSliders();
  document.getElementById("unifiedSearchForm")?.addEventListener("submit", handleUnifiedSearch);
  document.getElementById("communeSearchButton")?.addEventListener("click", handleCommuneSearch);
  document.getElementById("deptSearchBtn")?.addEventListener("click", handleDeptSearch);
  document.getElementById("communeReportBtn")?.addEventListener("click", generateCommuneReport);
  document.getElementById("deptReportBtn")?.addEventListener("click", generateDeptReport);
  document.getElementById("deptReportCarteBtn")?.addEventListener("click", generateDeptReport);
});