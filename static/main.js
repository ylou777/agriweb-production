// === Gestion des sliders ===
function setupSliders() {
  const sliders = [
    // Section Adresse / Coordonnées / GeoJSON
    ['sirene_radius','sirene_radius_val',' km'],
    // Section Commune & Culture
    ['ht_max_distance','htMaxVal',' m'],
    ['bt_max_distance','btMaxVal',' m'],
    ['sirene_radius_commune','sireneCommVal',' km'],
    // Section Département (flux SSE)
    ['minSurface','minSurfaceVal',' ha'],
    ['maxSurface','maxSurfaceVal',' ha'],
    ['ht_max_distance_dept','htMaxValDept',' m'],
    ['bt_max_distance_dept','btMaxValDept',' m']
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

// === Utilitaires carte ===
function getMapFrame() {
  return document.getElementById("mapFrame")?.contentWindow;
}

function reloadMap(params = {}) {
  const frame = document.getElementById("mapFrame");
  if (!frame) return Promise.resolve();
  return new Promise(resolve => {
    frame.onload = () => {
      if (frame.contentWindow?.addGeoJsonToMap) resolve();
      else {
        const id = setInterval(() => {
          if (frame.contentWindow?.addGeoJsonToMap) {
            clearInterval(id);
            resolve();
          }
        }, 50);
      }
    };
    const ps = new URLSearchParams(params);
    ps.append("cb", Date.now());
    frame.src = "/map.html?" + ps.toString();
  });
}
function clearAndAddFeatures(data) {
  const mapFrame = getMapFrame();
  if (!mapFrame?.addGeoJsonToMap) return;
  mapFrame.clearMap?.();
  (data.rpg || []).forEach(f => mapFrame.addGeoJsonToMap(f, { color: "#2b7a78", weight: 2, fillOpacity: 0.25 }));
  (data.postes_bt || []).forEach(f => mapFrame.addGeoJsonToMap(f));
  (data.postes_hta || []).forEach(f => mapFrame.addGeoJsonToMap(f));
  (data.eleveurs || []).forEach(ev => mapFrame.addGeoJsonToMap(ev, { color: "cadetblue", radius: 5 }));
}

// === Info panel ===
function updateInfoPanel(dataArr) {
  const c = dataArr.length;
  const p = dataArr.reduce((s, r) => {
    if (Array.isArray(r.parcelles)) {
      return s + r.parcelles.length;
    } else if (r.parcelles && Array.isArray(r.parcelles.features)) {
      return s + r.parcelles.features.length;
    }
    return s;
  }, 0);
  const e = dataArr.reduce((s, r) => s + (r.eleveurs?.length || 0), 0);
  document.getElementById("info-panel").innerHTML =
    `<div class="alert alert-info mb-0">Communes : ${c} – Parcelles : ${p} – Éleveurs : ${e}</div>`;
}

// === Recherche par adresse/coordonnées ===
async function handleUnifiedSearch(event) {
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
  ps.append("sirene_radius", document.getElementById("sirene_radius").value);

  try {
    const res = await fetch("/search_by_address?" + ps.toString());
    const data = await res.json();
    if (data.error) return alert(data.error);
    document.getElementById("latitude").value = data.lat;
    document.getElementById("longitude").value = data.lon;
    document.getElementById("address").value = data.address || "";
    await reloadMap();
    clearAndAddFeatures(data);
    updateInfoPanel([data]);
  } catch {
    alert("Erreur de requête.");
  }
}

// === Recherche par commune ===
async function handleCommuneSearch() {
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

  try {
    const res = await fetch("/search_by_commune?" + ps.toString());
    const data = await res.json();
    if (data.error) return alert(data.error);
    await reloadMap();
    clearAndAddFeatures(data);
    updateInfoPanel([data]);
  } catch {
    alert("Erreur lors de la recherche par commune.");
  }
}

// === Recherche départementale SSE ===
async function handleDeptSearch() {
  const dept = document.getElementById("departmentInput")?.value.trim();
  if (!dept) return alert("Département requis.");

  // Prépare les paramètres pour la requête SSE ET pour la carte
  const params = {
    department: dept,
    min_area_ha: document.getElementById("minSurface")?.value || "",
    max_area_ha: document.getElementById("maxSurface")?.value || "",
    bt_max_distance: document.getElementById("bt_max_distance_dept")?.value || "",
    ht_max_distance: document.getElementById("ht_max_distance_dept")?.value || "",
    want_eleveurs: true,
    exclude_nature: document.getElementById("excludeNature")?.checked || false,
    exclude_historic: document.getElementById("excludeBuildings")?.checked || false,
    culture: document.getElementById("rpgType")?.value || ""
  };
  const ps = new URLSearchParams(params);

  const log = document.getElementById("deptLog");
  if (log) {
    log.textContent = "";
  }
  updateInfoPanel([]);

  let allResults = [];
  let es;

  try {
    es = new EventSource("/generate_reports_by_dept_sse?" + ps.toString());
  } catch (e) {
    if (log) log.textContent += "Erreur lors de la connexion SSE\n";
    return;
  }

  // Progress (texte)
  es.addEventListener("progress", e => {
    if (log) {
      log.textContent += e.data + "\n";
      log.scrollTop = log.scrollHeight;
    }
  });

  // À chaque résultat, recharge la carte avec les bons paramètres
  es.addEventListener("result", async e => {
    const result = JSON.parse(e.data);
    allResults.push(result);
    updateInfoPanel(allResults);
    // Recharge la carte avec les paramètres courants (centrage département, etc.)
    await reloadMap(params);

    // Ajoute dynamiquement les features à la carte (quand JS Folium est prêt)
    setTimeout(() => {
      const mapFrame = getMapFrame();
      if (!mapFrame?.addGeoJsonToMap) return;
      mapFrame.clearMap?.();
      allResults.forEach(r => clearAndAddFeatures(r));
    }, 200);
  });

  // Fin du flux
  es.addEventListener("end", e => {
    if (log) log.textContent += e.data + "\n";
    es.close();
  });

  // Gestion des erreurs
  es.onerror = () => {
    if (log) log.textContent += "❌ Erreur SSE\n";
    es.close();
  };
}

// === Génération de rapport (point courant) ===
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

// === Génération de rapport commune ===
function generateCommuneReport() {
  const commune = document.getElementById("commune")?.value.trim();
  if (!commune) return alert("Commune requise !");
  // Récupère les paramètres de filtrage si besoin
  const params = new URLSearchParams({
    commune: commune,
    culture: document.getElementById("culture")?.value || "",
    min_area_ha: document.getElementById("minSurface")?.value || 0,
    max_area_ha: document.getElementById("maxSurface")?.value || 1e9,
    ht_max_distance: document.getElementById("ht_max_distance")?.value || 5000,
    bt_max_distance: document.getElementById("bt_max_distance")?.value || 2000,
    sirene_radius: document.getElementById("sirene_radius_commune")?.value || 0.05
  });
  window.open(`/rapport_commune?${params.toString()}`, "_blank");
}

// === Génération de rapport département ===
function generateDeptReport() {
  const dept = document.getElementById("departmentInput")?.value.trim();
  if (!dept) return alert("Département requis !");
  // Récupère les paramètres de filtrage si besoin
  const params = new URLSearchParams({
    dept: dept,
    culture: document.getElementById("rpgType")?.value || "",
    min_area_ha: document.getElementById("minSurface")?.value || 0,
    max_area_ha: document.getElementById("maxSurface")?.value || 1e9,
    ht_max_distance: document.getElementById("ht_max_distance_dept")?.value || 5000,
    bt_max_distance: document.getElementById("bt_max_distance_dept")?.value || 2000,
    sirene_radius: document.getElementById("sirene_radius_commune")?.value || 0.05
  });
  window.open(`/rapport_departement?${params.toString()}`, "_blank");
}

// === Initialisation ===
window.addEventListener("DOMContentLoaded", () => {
  setupSliders();
  document.getElementById("unifiedSearchForm")?.addEventListener("submit", handleUnifiedSearch);
  document.getElementById("communeSearchButton")?.addEventListener("click", handleCommuneSearch);
  document.getElementById("deptSearchBtn")?.addEventListener("click", handleDeptSearch);

  // Boutons rapport commune et département
  document.getElementById("communeReportBtn")?.addEventListener("click", generateCommuneReport);
  document.getElementById("deptReportBtn")?.addEventListener("click", generateDeptReport);
});