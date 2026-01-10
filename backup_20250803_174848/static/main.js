// ============================================================================
// main.js – version avancée (corrections : contexte, rapports, et save map)
// ============================================================================

// ----------------- LAYER CONFIG -----------------
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
  // Ne pas mettre ici les sous-couches urbanisme (dynamiques)
};
window.lastDeptResults = [];
window.lastSearchData = null;
window.lastCommuneSearch = null;
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
    try {
      console.log(`[displayAllLayers] Traitement de ${layerKey}:`, val);
      
      // Urbanisme (plusieurs sous-couches indépendantes)
      if (layerKey === "api_urbanisme" && val && typeof val === "object" && !Array.isArray(val) && !val.type) {
        Object.entries(val).forEach(([subkey, subval]) => {
          try {
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
          } catch (subErr) {
            console.error(`[displayAllLayers] Erreur sous-couche ${subkey}:`, subErr);
          }
        });
        return;
      }

    // Normalisation (toujours obtenir un FeatureCollection)
    if (!val || (Array.isArray(val) && val.length === 0)) return;
    let geojson = null;
    try {
      if (val.type === "FeatureCollection" && Array.isArray(val.features) && val.features.length) geojson = val;
      else if (val.type === "Feature" && val.geometry) geojson = { type: "FeatureCollection", features: [val] };
      else if (Array.isArray(val) && val[0] && val[0].type === "Feature" && val[0].geometry) geojson = { type: "FeatureCollection", features: val };
      if (!geojson) return;
      
      console.log(`[displayAllLayers] GeoJSON normalisé pour ${layerKey}:`, geojson);
    } catch (normalizeErr) {
      console.error(`[displayAllLayers] Erreur normalisation ${layerKey}:`, normalizeErr);
      return;
    }

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
    
    } catch (layerErr) {
      console.error(`[displayAllLayers] Erreur traitement couche ${layerKey}:`, layerErr);
    }
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
      // Mémorise le contexte pour rapport "point courant"
      window.lastSearchData = data;
      // Recharge la carte générée dans l'iframe
      if (data.carte_url) {
        document.getElementById("mapFrame").src = data.carte_url;
      }
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
async function handleCommuneSearch(e) {
  e?.preventDefault?.();
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
      // Mémorise le contexte pour rapport commune
      window.lastCommuneSearch = { commune: commune };
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
// Rapport "point courant" - VERSION ENRICHIE COMPLÈTE
function generateReport() {
    const data = window.lastSearchData;
    if (!data || !data.lat || !data.lon) return alert("Recherchez d'abord.");
    
    // 🔄 ENRICHISSEMENT COMPLET : Transmission de TOUTES les données collectées
    const params = new URLSearchParams({
        lat: data.lat,
        lon: data.lon,
        address: data.address || "",
        
        // === DONNÉES SUMMARY ===
        parcelle_numero: data.summary?.parcelle_numero || "",
        distance_poste_proche: data.summary?.distance_poste_proche || "",
        zone_plu: data.summary?.zone_plu || "",
        
        // === DONNÉES ÉNERGÉTIQUES ET TOPOGRAPHIQUES ===
        // Irradiation solaire (PVGIS)
        irradiation_solaire: data.pvgis_data?.yearly_pv_energy_production || 
                            data.kwh_per_kwc || 
                            data.irradiation || "",
        
        // Altitude
        altitude: data.altitude || data.altitude_m || "",
        
        // Potentiel solaire (zones)
        potentiel_solaire_count: data.solaire?.features?.length || 0,
        potentiel_solaire_zones: data.solaire?.features?.map(f => 
            f.properties?.nom || f.properties?.libelle || f.properties?.type
        ).filter(Boolean).join(",") || "",
        
        // === DONNÉES APIs EXTERNES ===
        // Cadastre
        api_cadastre_success: data.api_cadastre?.features?.length > 0 ? "true" : "false",
        api_cadastre_commune: data.api_cadastre?.features?.[0]?.properties?.nom_com || 
                             data.api_cadastre?.features?.[0]?.properties?.commune || "",
        api_cadastre_section: data.api_cadastre?.features?.[0]?.properties?.section || "",
        api_cadastre_numero: data.api_cadastre?.features?.[0]?.properties?.numero || "",
        
        // Urbanisme GPU
        api_urbanisme_layers: data.api_urbanisme ? Object.keys(data.api_urbanisme).length : 0,
        api_urbanisme_features: data.api_urbanisme ? 
            Object.values(data.api_urbanisme).reduce((sum, layer) => 
                sum + (layer?.features?.length || 0), 0) : 0,
        api_urbanisme_zones: data.api_urbanisme ? 
            Object.keys(data.api_urbanisme).join(",") : "",
        
        // Nature/Codes postaux
        api_nature_success: data.api_nature?.features?.length > 0 ? "true" : "false",
        api_nature_commune: data.api_nature?.features?.[0]?.properties?.nom_commune || "",
        api_nature_dept: data.api_nature?.features?.[0]?.properties?.nom_departement || "",
        api_nature_postal: data.api_nature?.features?.[0]?.properties?.code_postal || "",
        
        // === DONNÉES GÉOGRAPHIQUES AU POINT ===
        // Parcelles
        rpg_count: data.rpg?.features?.length || 0,
        rpg_cultures: data.rpg?.features?.map(f => 
            f.properties?.Culture || f.properties?.culture
        ).filter(Boolean).join(",") || "",
        rpg_surfaces: data.rpg?.features?.map(f => 
            f.properties?.SURF_PARC || f.properties?.surface_ha
        ).filter(Boolean).join(",") || "",
        
        parcelles_count: data.parcelles?.features?.length || 0,
        parcelles_sections: data.parcelles?.features?.map(f =>
            f.properties?.section
        ).filter(Boolean).join(",") || "",
        
        // PLU
        plu_count: data.plu?.features?.length || 0,
        plu_zones: data.plu?.features?.map(f => 
            f.properties?.typezone || f.properties?.libelle
        ).filter(Boolean).join(",") || "",
        plu_destdomi: data.plu?.features?.map(f =>
            f.properties?.destdomi
        ).filter(Boolean).join(",") || "",
        
        // ZAER
        zaer_count: data.zaer?.features?.length || 0,
        zaer_zones: data.zaer?.features?.map(f => 
            f.properties?.nom || f.properties?.filiere
        ).filter(Boolean).join(",") || "",
        zaer_filieres: data.zaer?.features?.map(f =>
            f.properties?.detail_fil
        ).filter(Boolean).join(",") || "",
        
        // === INFRASTRUCTURES ÉLECTRIQUES ===
        // Postes BT
        postes_bt_count: data.postes_bt?.features?.length || 0,
        postes_bt_distances: data.postes_bt?.features?.map(f =>
            f.distance || f.properties?.distance
        ).filter(Boolean).join(",") || "",
        
        // Postes HTA  
        postes_hta_count: data.postes_hta?.features?.length || 0,
        postes_hta_distances: data.postes_hta?.features?.map(f =>
            f.distance || f.properties?.distance
        ).filter(Boolean).join(",") || "",
        postes_hta_capacites: data.postes_hta?.features?.map(f =>
            f.properties?.Capacité || f.properties?.capacite
        ).filter(Boolean).join(",") || "",
        
        // Capacités réseau
        capacites_reseau_count: data.capacites_reseau?.features?.length || 0,
        
        // === CONTEXTE ÉCONOMIQUE ET ENVIRONNEMENTAL ===
        // Sirene (entreprises)
        sirene_count: data.sirene?.features?.length || 0,
        sirene_activites: data.sirene?.features?.map(f =>
            f.properties?.activitePrincipaleEtablissement || f.properties?.libelle_apet
        ).filter(Boolean).slice(0, 5).join(",") || "",
        
        // Éleveurs
        eleveurs_count: data.eleveurs?.features?.length || 0,
        
        // Parkings
        parkings_count: data.parkings?.features?.length || 0,
        
        // Friches
        friches_count: data.friches?.features?.length || 0,
        friches_types: data.friches?.features?.map(f =>
            f.properties?.type || f.properties?.libelle
        ).filter(Boolean).join(",") || "",
        
        // === MÉTADONNÉES ===
        search_timestamp: Date.now(),
        data_source: "search_by_address",
        search_radius: document.getElementById("sirene_radius")?.value || "0.05",
        interface_version: "3.2.1"
    });
    
    window.open(`/rapport_point?${params.toString()}`, "_blank");
}
// Rapport par commune
function generateCommuneReport() {
    const search = window.lastCommuneSearch;
    if (!search || !search.commune) return alert("Faites d’abord une recherche de commune !");
    const params = new URLSearchParams({
        commune: search.commune
    });
    window.open(`/rapport_commune?${params.toString()}`, "_blank");
}

// Rapport par département
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

// --------- ENREGISTRER LA CARTE (AJAX) ---------
// À brancher à un bouton ou à appeler après une modif de la carte pour sauvegarder côté backend (Flask doit avoir la route save_map_html !)
function saveCurrentMap(filename="carte_utilisateur.html") {
  const m = getMapFrame();
  if (!m || !m.getMapState) {
    alert("Carte non accessible ou non exportable !");
    return;
  }
  // Exemple d'appel AJAX à un endpoint Flask à implémenter :
  fetch('/save_map_html', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      filename,
      state: m.getMapState ? m.getMapState() : null // à adapter à ta méthode
    })
  })
    .then(r => r.json())
    .then(res => {
      if(res.success && res.path){
        alert("Carte enregistrée sous : " + res.path);
      } else {
        alert("Erreur à l'enregistrement : " + (res.error || "inconnue"));
      }
    })
    .catch(err => alert("Erreur de sauvegarde : " + err));
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

document.addEventListener('DOMContentLoaded', function() {
    // Branche sliders si tu utilises
    setupSliders();
    // Branche formulaires
    document.getElementById("unifiedSearchForm")?.addEventListener("submit", handleUnifiedSearch);
    document.getElementById("communeSearchForm")?.addEventListener("submit", handleCommuneSearch);
    // Branche recherche départementale si tu as un bouton
    document.getElementById("deptSearchBtn")?.addEventListener("click", handleDeptSearch);
    // Branche boutons de rapport
    document.getElementById("reportButton")?.addEventListener("click", generateReport);
    document.getElementById("communeReportBtn")?.addEventListener("click", generateCommuneReport);
    document.getElementById("deptReportBtn")?.addEventListener("click", generateDeptReport);
    document.getElementById("deptReportCarteBtn")?.addEventListener("click", generateDeptReport);
    // Branche bouton save map si besoin
    // document.getElementById("saveMapBtn")?.addEventListener("click", () => saveCurrentMap("mon_export.html"));
});
