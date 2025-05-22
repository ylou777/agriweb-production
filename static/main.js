// static/js/main.js

// ─────────────────────────────────────────────
// 🔧 Mise à jour dynamique des sliders
// ─────────────────────────────────────────────
function setupSliders() {
  const sliders = [
    ['sirene_radius','sirene_radius_val',' km'],
    ['ht_radius','ht_radius_val',' km'],
    ['bt_radius','bt_radius_val',' km'],
    ['minSurface','minSurfaceVal',' ha'],
    ['maxSurface','maxSurfaceVal',' ha'],
    ['btRadius','btRadiusVal',' m'],
    ['htRadius','htRadiusVal',' m'],
    ['ht_max_distance','htMaxVal',' km'],
    ['bt_max_distance','btMaxVal',' km'],
    ['sirene_radius_commune','sireneCommVal',' km']
  ];
  sliders.forEach(([id, out, unit]) => {
    const s = document.getElementById(id);
    const o = document.getElementById(out);
    if (s && o) {
      o.textContent = s.value + unit;
      s.addEventListener('input', () => {
        o.textContent = s.value + unit;
      });
    }
  });
}

// ─────────────────────────────────────────────
// 🔁 Recharge de la carte iframe
// ─────────────────────────────────────────────
function reloadMap() {
  const frame = document.getElementById("mapFrame");
  if (frame) frame.src = "/map.html?cb=" + Date.now();
}

// ─────────────────────────────────────────────
// ℹ️ Mise à jour panneau d'information
// ─────────────────────────────────────────────
function updateInfoPanel(data) {
  const c = data.length;
  const p = data.reduce((s, r) => s + (r.parcelles?.length || 0), 0);
  const e = data.reduce((s, r) => s + (r.eleveurs?.length || 0), 0);
  document.getElementById("info-panel").innerHTML =
    `<div class="alert alert-info mb-0">Communes : ${c} – Parcelles : ${p} – Éleveurs : ${e}</div>`;
}

// ─────────────────────────────────────────────
// 📍 Recherche par adresse / coordonnées
// ─────────────────────────────────────────────
function handleUnifiedSearch(event) {
  event.preventDefault();
  const input = document.getElementById("search_input").value.trim();
  if (!input) return alert("Saisissez une adresse ou des coordonnées.");

  let lat, lon;
  try {
    const obj = JSON.parse(input);
    if (obj.type === "Point") [lon, lat] = obj.coordinates;
  } catch {
    const parts = input.split(",");
    if (parts.length === 2) {
      lon = parseFloat(parts[0]);
      lat = parseFloat(parts[1]);
    }
  }

  const ps = new URLSearchParams();
  if (!isNaN(lat) && !isNaN(lon)) {
    ps.append("lat", lat);
    ps.append("lon", lon);
  } else {
    ps.append("address", input);
  }

  ["sirene_radius", "ht_radius", "bt_radius"].forEach(id => {
    ps.append(id, document.getElementById(id).value);
  });

  fetch("/search_by_address?" + ps.toString())
    .then(res => res.json())
    .then(data => {
      if (data.error) return alert(data.error);
      document.getElementById("latitude").value = data.lat;
      document.getElementById("longitude").value = data.lon;
      document.getElementById("address").value = data.address || "";
      updateInfoPanel([data]);
    })
    .catch(() => alert("Erreur de requête."));
}

// ─────────────────────────────────────────────
// 🏘️ Recherche par commune
// ─────────────────────────────────────────────
function handleCommuneSearch() {
  reloadMap(); // Recharge AVANT tout
  const commune = document.getElementById("commune").value.trim();
  if (!commune) return alert("Commune requise.");

  const ps = new URLSearchParams({
    commune: commune,
    culture: document.getElementById("culture").value,
    min_area_ha: document.getElementById("minSurface").value,
    max_area_ha: document.getElementById("maxSurface").value,
    ht_max_distance: document.getElementById("ht_max_distance").value,
    bt_max_distance: document.getElementById("bt_max_distance").value,
    sirene_radius: document.getElementById("sirene_radius_commune").value
  });

  fetch("/search_by_commune?" + ps.toString())
    .then(res => res.json())
    .then(data => {
      if (data.error) return alert(data.error);
      const mapFrame = document.getElementById("mapFrame")?.contentWindow;
      if (!mapFrame?.addGeoJsonToMap) return alert("Carte non prête.");

      (data.rpg || []).forEach(f => mapFrame.addGeoJsonToMap(f, { color: "#2b7a78", weight: 2, fillOpacity: 0.25 }));
      (data.postes_bt || []).forEach(f => mapFrame.addGeoJsonToMap(f));
      (data.postes_hta || []).forEach(f => mapFrame.addGeoJsonToMap(f));
      (data.eleveurs || []).forEach(ev => mapFrame.addGeoJsonToMap(ev, { color: "cadetblue", radius: 5 }));

      // ❌ NE PAS RECHARGER LA CARTE ICI
      updateInfoPanel([data]);
    })
    .catch(() => alert("Erreur lors de la recherche par commune."));
}

// ─────────────────────────────────────────────
// 📍 Recherche départementale SSE
// ─────────────────────────────────────────────
function handleDeptSearch() {
    reloadMap(); // Recharge AVANT tout
  const dept = document.getElementById("departmentInput").value.trim();
  if (!dept) return alert("Département requis.");

  const ps = new URLSearchParams({
    department: dept,
    min_parcelle_area_ha: document.getElementById("minSurface").value,
    max_parcelle_area_ha: document.getElementById("maxSurface").value,
    max_bt_dist_m: document.getElementById("btRadius").value,
    max_ht_dist_m: document.getElementById("htRadius").value,
    has_eleveurs: true,
    exclude_nature: document.getElementById("excludeNature").checked,
    exclude_historic: document.getElementById("excludeBuildings").checked,
    culture_codes: document.getElementById("rpgType").value
  });

  const log = document.getElementById("deptLog");
  log.textContent = "";
  updateInfoPanel([]);

  const es = new EventSource("/generate_reports_by_dept_sse?" + ps.toString());

  es.addEventListener("progress", e => {
    log.textContent += e.data + "\n";
    log.scrollTop = log.scrollHeight;
  });

  es.addEventListener("result", e => {
    const result = JSON.parse(e.data);
    const mapFrame = document.getElementById("mapFrame")?.contentWindow;
    if (!mapFrame?.addGeoJsonToMap) return;

    (result.rpg || []).forEach(f => mapFrame.addGeoJsonToMap(f, { color: "#2b7a78", weight: 2, fillOpacity: 0.25 }));
    (result.postes_bt || []).forEach(f => mapFrame.addGeoJsonToMap(f));
    (result.postes_hta || []).forEach(f => mapFrame.addGeoJsonToMap(f));
    (result.eleveurs || []).forEach(ev => mapFrame.addGeoJsonToMap(ev, { color: "cadetblue", radius: 5 }));

    updateInfoPanel([result]);
  });

  es.addEventListener("end", e => {
    log.textContent += e.data + "\n";
    es.close();
  });

  es.onerror = () => {
    log.textContent += "❌ Erreur SSE\n";
    es.close();
  };
}

// ─────────────────────────────────────────────
// 📝 Génération de rapport
// ─────────────────────────────────────────────
function generateReport() {
  const lat = document.getElementById("latitude").value;
  const lon = document.getElementById("longitude").value;
  const address = document.getElementById("address").value;
  if (!lat || !lon) return alert("Recherchez d’abord.");

  const fd = new FormData();
  fd.append("lat", lat);
  fd.append("lon", lon);
  fd.append("address", address || "");

  fetch("/rapport", { method: "POST", body: fd })
    .then(r => r.text())
    .then(html => {
      const w = window.open();
      w.document.write(html);
      w.document.close();
    });
}

// ─────────────────────────────────────────────
// 🚀 Initialisation
// ─────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
  setupSliders();
  document.getElementById("unifiedSearchForm")?.addEventListener("submit", handleUnifiedSearch);
  document.getElementById("communeSearchButton")?.addEventListener("click", handleCommuneSearch);
  document.getElementById("deptSearchBtn")?.addEventListener("click", handleDeptSearch);
});
