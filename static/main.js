// ============================================================================
// main.js – version avancée (corrections : contexte, rapports, et save map)
// ============================================================================

// ----------------- LAYER CONFIG -----------------
const LAYER_CONFIG = {
  rpg:              { label: "RPG Parcelles", color: "green" },
  postes_bt:        { label: "Postes BT", color: "orange" },
  postes_hta:       { label: "Postes HTA", color: "red" },
  capacites_reseau: { label: "Capacités Réseau", color: "purple" },
  eleveurs:         { label: "Éleveurs", color: "purple" },
  parcelles:        { label: "Parcelles", color: "blue" },
  api_cadastre:   { label: "Cadastre (API IGN)", color: "#FF6600" },
  api_nature:     { label: "Nature (API IGN)", color: "#22AA22" },
  plu:            { label: "PLU", color: "#880000" },
  parkings:       { label: "Parkings", color: "darkgreen" },
  friches:        { label: "Friches", color: "brown" },
  solaire:        { label: "Potentiel Solaire", color: "gold" },
  zaer:           { label: "ZAER", color: "cyan" },
  sirene:         { label: "Entreprises Sirene", color: "darkred" },
  enedis:         { label: "Consommations Électriques", color: "#FF5733" },
  hta_lignes_aeriennes:     { label: "Lignes HTA Aériennes", color: "orange" },
  hta_lignes_souterraines:  { label: "Lignes HTA Souterraines", color: "purple" }
  // Ne pas mettre ici les sous-couches urbanisme (dynamiques)
};

// ----------------- FRIENDLY LABELS -----------------
// Map internal property keys to human-friendly French labels for popups
const FRIENDLY_LABELS = {
  // Liens
  lien_streetview: "Street View",
  lien_annuaire: "Annuaire",

  // Distances
  min_distance_bt_m: "Distance BT (m)",
  min_distance_hta_m: "Distance HTA (m)",
  min_distance_total_m: "Distance poste min (m)",
  // Distances (commune/dept props)
  distance_bt: "Distance BT (m)",
  distance_hta: "Distance HTA (m)",

  // Surfaces
  surface_toiture_m2: "Surface toiture (m²)",
  surface_m2: "Surface (m²)",
  surface_ha: "Surface (ha)",

  // Cadastral
  parcelles_cadastrales: "Parcelles cadastrales",
  nb_parcelles_cadastrales: "Nb parcelles cadastrales",

  // Adresse / contexte
  adresse: "Adresse",
  commune: "Commune",
  search_method: "Méthode de recherche",
  source: "Source",
  building: "Type de bâtiment",
  osm_id: "OSM ID",

  // Zones
  zone_typezone: "Type de zone",
  zone_libelle: "Zone",
  zone_filter_applied: "Filtre zone",

  // Surface libre (optionnel)
  surface_batie_m2: "Surface bâtie (m²)",
  surface_libre_m2: "Surface libre (m²)",
  surface_libre_pct: "Surface libre (%)",
  batiments_count: "Bâtiments (#)"
};

function getFriendlyLabel(key) {
  if (!key) return "";
  if (FRIENDLY_LABELS[key]) return FRIENDLY_LABELS[key];
  if (key.startsWith("lien_")) {
    const rest = key.slice(5).replace(/_/g, " ");
    return rest.replace(/\b\w/g, c => c.toUpperCase());
  }
  // Generic fallback: prettify the key
  return key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

// Rapport par commune - Version complète intégrée

// ============================================================================
// RAPPORT DIRECT - Sans passer par la recherche
// ============================================================================

/**
 * Rapport direct commune : lit les champs du formulaire et ouvre le rapport
 * sans passer par la recherche intermédiaire
 */
function directReportCommune() {
  const commune = document.getElementById('commune')?.value?.trim();
  if (!commune) return alert("Veuillez saisir un nom de commune !");

  const boolVal = (id, defVal=false) => {
    const el = document.getElementById(id);
    return el ? !!el.checked : defVal;
  };
  const numVal = (id, defVal=0) => {
    const el = document.getElementById(id);
    const v = el ? parseFloat(el.value) : defVal;
    return isNaN(v) ? defVal : v;
  };

  const params = new URLSearchParams();
  params.set('commune', commune);
  
  // Couches principales
  params.set('filter_rpg', String(boolVal('filter_rpg_commune', true)));
  params.set('rpg_min_area', String(numVal('rpg_min_area', 1)));
  params.set('rpg_max_area', String(numVal('rpg_max_area', 1000)));
  params.set('filter_parkings', String(boolVal('filter_parkings_commune', false)));
  params.set('parking_min_area', String(numVal('parking_min_area', 1500)));
  params.set('filter_friches', String(boolVal('filter_friches_commune', false)));
  params.set('friches_min_area', String(numVal('friches_min_area', 1000)));
  params.set('filter_zones', String(boolVal('filter_zones_commune', false)));
  params.set('zones_min_area', String(numVal('zones_min_area', 1000)));
  params.set('zones_type_filter', document.getElementById('zones_type_filter')?.value || '');
  params.set('filter_toitures', String(boolVal('filter_toitures_commune', false)));
  params.set('toitures_min_surface', String(numVal('min_surface_toiture', 100)));
  
  // Filtres distance
  params.set('filter_by_distance', String(boolVal('filter_by_distance_commune', false)));
  params.set('max_distance_bt', String(numVal('bt_max_distance_commune', 2000)));
  params.set('max_distance_hta', String(numVal('ht_max_distance_commune', 5000)));
  const posteType = document.querySelector('input[name="poste_type_filter"]:checked')?.value || 'ALL';
  params.set('poste_type_filter', posteType);
  
  params.set('export_format', 'html');
  window.open(`/rapport_commune_complet?${params.toString()}`, "_blank");
}

/**
 * Rapport direct adresse : géocode l'adresse puis ouvre le rapport point
 */
function directReportAddress() {
  const searchInput = document.getElementById('search_input')?.value?.trim();
  if (!searchInput) return alert("Veuillez saisir une adresse !");

  // Vérifier si c'est déjà des coordonnées (lat, lon)
  const coordMatch = searchInput.match(/^([+-]?\d+\.?\d*)[,;\s]+([+-]?\d+\.?\d*)$/);
  if (coordMatch) {
    const lat = parseFloat(coordMatch[1]);
    const lon = parseFloat(coordMatch[2]);
    window.open(`/rapport_map?lat=${lat}&lon=${lon}`, "_blank");
    return;
  }

  // Géocoder l'adresse via API Géoplateforme
  const btn = event?.target;
  if (btn) { btn.disabled = true; btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Géocodage...'; }
  
  fetch(`https://data.geopf.fr/geocodage/search?q=${encodeURIComponent(searchInput)}&limit=1`)
    .then(r => r.json())
    .then(data => {
      if (data.features && data.features.length > 0) {
        const coords = data.features[0].geometry.coordinates;
        const lon = coords[0];
        const lat = coords[1];
        const address = data.features[0].properties?.label || searchInput;
        window.open(`/rapport_map?lat=${lat}&lon=${lon}&address=${encodeURIComponent(address)}`, "_blank");
      } else {
        alert("❌ Adresse non trouvée. Essayez avec plus de détails.");
      }
    })
    .catch(err => {
      alert("❌ Erreur de géocodage: " + err.message);
    })
    .finally(() => {
      if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-file-earmark-text"></i> Rapport direct'; }
    });
}

function generateCommuneReport() {
  const search = window.lastCommuneSearch;
  if (!search || !search.commune) return alert("Faites d'abord une recherche de commune !");
  // Récupérer les filtres actuels de l'UI (mêmes IDs que pour l'analyse commune)
  const boolVal = (id, defVal=false) => {
    const el = document.getElementById(id);
    return el ? !!el.checked : defVal;
  };
  const numVal = (id, defVal=0) => {
    const el = document.getElementById(id);
    const v = el ? parseFloat(el.value) : defVal;
    return isNaN(v) ? defVal : v;
  };

  const params = new URLSearchParams();
  params.set('commune', search.commune);
  // Couches principales
  params.set('filter_rpg', String(boolVal('filter_rpg_commune', true)));
  params.set('rpg_min_area', String(numVal('rpg_min_area', 1)));
  params.set('rpg_max_area', String(numVal('rpg_max_area', 1000)));

  params.set('filter_parkings', String(boolVal('filter_parkings_commune', false)));
  params.set('parking_min_area', String(numVal('parking_min_area', 1500)));

  params.set('filter_friches', String(boolVal('filter_friches_commune', false)));
  params.set('friches_min_area', String(numVal('friches_min_area', 1000)));

  params.set('filter_zones', String(boolVal('filter_zones_commune', false)));
  params.set('zones_min_area', String(numVal('zones_min_area', 1000)));
  params.set('zones_type_filter', document.getElementById('zones_type_filter')?.value || '');

  params.set('filter_toitures', String(boolVal('filter_toitures_commune', false)));
  params.set('toitures_min_surface', String(numVal('min_surface_toiture', 100)));

  // Filtres distance unifiés
  const filterByDist = document.getElementById('filter_by_distance_commune')?.checked || false;
  params.set('filter_by_distance', String(filterByDist));
  params.set('max_distance_bt', String(numVal('bt_max_distance_commune', 2000)));
  params.set('max_distance_hta', String(numVal('ht_max_distance_commune', 5000)));
  const posteType = document.querySelector('input[name="poste_type_filter"]:checked')?.value || 'ALL';
  params.set('poste_type_filter', posteType);

  // Demander une page HTML
  params.set('export_format', 'html');
  window.open(`/rapport_commune_complet?${params.toString()}`, "_blank");
}
window.lastDeptResults = [];
window.lastSearchData = null;
window.lastCommuneSearch = null;
let overlaysControl = null;
let dynamicLayers = {};

// --------- UI sliders ---------
function setupSliders() {
  [
    ["ht_max_distance", "htMaxVal", " m"],
    ["bt_max_distance", "btMaxVal", " m"],
    ["capacite_max_distance", "capaciteMaxVal", " m"],
    ["ht_max_distance_commune", "htMaxValCommune", " m"],
    ["bt_max_distance_commune", "btMaxValCommune", " m"],
    ["minSurface", "minSurfaceVal", " ha"],
    ["maxSurface", "maxSurfaceVal", " ha"],
    ["ht_max_distance_dept", "htMaxValDept", " m"],
    ["bt_max_distance_dept", "btMaxValDept", " m"],
    ["capacite_max_distance_dept", "capaciteMaxValDept", " m"],
    ["hta_lines_aerial_distance_dept", "htaLinesAerialMaxValDept", " m"],
    ["hta_lines_underground_distance_dept", "htaLinesUndergroundMaxValDept", " m"],
  // Sliders pour les toitures (uniquement surface, distances via contrôle global)
  ["min_surface_toiture", "minSurfaceToitureVal", " m²"],
  ].forEach(([id, out, unit]) => {
    const s = document.getElementById(id), o = document.getElementById(out);
    if (s && o) {
      o.textContent = s.value + unit;
      s.addEventListener("input", () => (o.textContent = s.value + unit));
    }
  });
}
// Utilitaire pour logs d'avancement recherche commune
function setCommuneSearchLog(msg, color) {
  const el = document.getElementById('communeSearchLog');
  if (!el) return;
  // Ajout d'une animation de points si demandé
  if (msg && msg.endsWith('...')) {
    let dots = 0;
    if (window.communeLogInterval) clearInterval(window.communeLogInterval);
    el.innerHTML = `<span style='font-weight:bold;'>${msg}</span> <span id='communeLogDots'></span>`;
    el.style.color = color || '#0a58ca';
    window.communeLogInterval = setInterval(() => {
      dots = (dots + 1) % 4;
      document.getElementById('communeLogDots').textContent = '.'.repeat(dots);
    }, 400);
  } else {
    if (window.communeLogInterval) clearInterval(window.communeLogInterval);
    el.innerHTML = msg ? `<span style='font-weight:bold;'>${msg}</span>` : '';
    el.style.color = color || '#17a2b8';
  }
  // Effacement auto après succès
  if (msg && (msg.includes('terminée') || msg.includes('succès'))) {
    setTimeout(() => { if (el.textContent === msg) el.textContent = ''; }, 3500);
  }
}

// Enregistre la dernière commune recherchée (utilisée par le bouton rapport)
function setLastCommuneSearched(name) {
  window.lastCommuneSearch = { commune: name };
}
function htmlifyField (key, value) {
  if (typeof value === "string" && /^https?:\/\//i.test(value)) {
  const anchorText = getFriendlyLabel(key);
    return `<a href="${value}" target="_blank" rel="noopener">${anchorText}</a>`;
  }
  
  // Gestion spéciale pour les parcelles cadastrales
  if (key === "parcelles_cadastrales" && Array.isArray(value)) {
    if (value.length === 0) return "Aucune";
    return value.map(parcelle => {
      // Si la parcelle a une référence complète, l'utiliser
      if (parcelle && typeof parcelle === 'object' && parcelle.reference_complete) {
        return parcelle.reference_complete;
      }
      // Sinon, construire la référence à partir des composants
      if (parcelle && typeof parcelle === 'object') {
        const commune = parcelle.commune || '';
        const prefixe = parcelle.prefixe || '';
        const section = parcelle.section || '';
        const numero = parcelle.numero || '';
        return `${commune}${prefixe}${section}${numero}`.trim();
      }
      // Fallback pour les formats inattendus
      return String(parcelle);
    }).join(', ');
  }
  
  return value;
}

// --------- UTILITAIRES POUR LA RECHERCHE PAR ADRESSE ---------

// Créer ou récupérer l'élément de log pour la recherche par adresse
function createOrGetSearchLog() {
  let logElement = document.getElementById('searchLog');
  if (logElement) {
    // Rendre visible le log existant
    logElement.style.display = 'block';
    return logElement;
  }
  
  // Créer l'élément de log s'il n'existe pas (fallback)
  logElement = document.createElement('div');
  logElement.id = 'searchLog';
  logElement.className = 'form-text text-info mb-2';
  logElement.style.minHeight = '1.5em';
  logElement.style.fontSize = '0.9em';
  logElement.style.maxHeight = '120px';
  logElement.style.overflowY = 'auto';
  logElement.style.border = '1px solid #dee2e6';
  logElement.style.borderRadius = '4px';
  logElement.style.padding = '8px';
  logElement.style.backgroundColor = '#f8f9fa';
  logElement.style.display = 'block';
  
  // Insérer après le formulaire unifiedSearchForm
  const form = document.getElementById('unifiedSearchForm');
  if (form && form.parentNode) {
    form.parentNode.insertBefore(logElement, form.nextSibling);
  }
  
  return logElement;
}

// Afficher un log de recherche
function logSearch(message, type = 'info') {
  const logElement = createOrGetSearchLog();
  if (!logElement) return;
  
  const now = new Date();
  const timestamp = now.toLocaleTimeString();
  
  // Créer une nouvelle ligne de log
  const logLine = document.createElement('div');
  logLine.style.marginBottom = '2px';
  logLine.style.fontSize = '0.85em';
  
  // Couleurs selon le type
  const colors = {
    info: '#17a2b8',
    success: '#28a745', 
    error: '#dc3545',
    warning: '#ffc107'
  };
  
  logLine.style.color = colors[type] || colors.info;
  logLine.innerHTML = `<span style="color: #6c757d;">[${timestamp}]</span> ${message}`;
  
  logElement.appendChild(logLine);
  
  // Scroll automatique vers le bas
  logElement.scrollTop = logElement.scrollHeight;
  
  // Limiter le nombre de lignes (garder les 10 dernières)
  while (logElement.children.length > 10) {
    logElement.removeChild(logElement.firstChild);
  }
}

// Effacer les logs de recherche
function clearSearchLog() {
  const logElement = document.getElementById('searchLog');
  if (logElement) {
    logElement.innerHTML = '';
    logElement.style.display = 'none';
  }
}

// Changer l'état visuel du bouton de recherche
function setSearchStatus(status, button, text) {
  if (!button) return;
  
  switch (status) {
    case 'loading':
      button.disabled = true;
      button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>' + text;
      button.className = button.className.replace('btn-primary', 'btn-secondary');
      break;
    case 'idle':
      button.disabled = false;
      button.innerHTML = text;
      button.className = button.className.replace('btn-secondary', 'btn-primary');
      break;
  }
}

// Analyser les résultats de recherche pour les logs
function analyzeSearchResults(data) {
  const stats = [];
  
  if (data.parcelles && data.parcelles.features) {
    stats.push(`${data.parcelles.features.length} parcelle(s)`);
  }
  if (data.rpg && data.rpg.features) {
    stats.push(`${data.rpg.features.length} parcelle(s) RPG`);
  }
  if (data.postes_bt && data.postes_bt.features) {
    stats.push(`${data.postes_bt.features.length} poste(s) BT`);
  }
  if (data.postes_hta && data.postes_hta.features) {
    stats.push(`${data.postes_hta.features.length} poste(s) HTA`);
  }
  if (data.eleveurs && data.eleveurs.features) {
    stats.push(`${data.eleveurs.features.length} éleveur(s)`);
  }
  if (data.sirene && data.sirene.features) {
    stats.push(`${data.sirene.features.length} entreprise(s) Sirene`);
  }
  
  return stats.length > 0 ? stats.join(', ') : 'aucune donnée trouvée';
}
function buildPopup (properties, extra = {}) {
  let out = "";
  for (const [k, v] of Object.entries(properties || {}))
    out += `<b>${getFriendlyLabel(k)}:</b> ${htmlifyField(k, v)}<br>`;
  for (const [k, v] of Object.entries(extra))
    out += `<b>${getFriendlyLabel(k)}:</b> ${v}<br>`;
  return out;
}

function getMapFrame() {
  try {
    // 1) Accéder à l'iframe qui contient la carte
    const iframe = document.getElementById('mapFrame');
    if (iframe && iframe.contentWindow) {
      const w = iframe.contentWindow;
      // a) Cas map1.html: variable globale 'map'
      if (w.map && w.L) {
        return {
          map: w.map,
          L: w.L,
          clearMap: w.clearMap?.bind(w),
          setView: (lat, lon, z) => w.map.setView([lat, lon], z || w.map.getZoom?.() || 10),
          setOverlaysControl: w.setOverlaysControl?.bind(w),
          addGeoJsonToMap: w.addGeoJsonToMap?.bind(w),
          getBaseLayers: () => ({ "Satellite": w.sat, "OSM": w.osm })
        };
      }
      // b) Cas Folium: variable globale de type 'map_<id>'
      for (const key of Object.keys(w)) {
        if (key.startsWith('map_') && w[key] && w[key]._container) {
          return {
            map: w[key],
            L: w.L,
            setView: (lat, lon, z) => w[key].setView([lat, lon], z || w[key].getZoom?.() || 10),
            getBaseLayers: () => ({})
          };
        }
      }
    }

    // 2) Fallback improbable: si on est directement sur une page carte (sans iframe)
    if (window.map && window.L) {
      return { map: window.map, L: window.L };
    }
    for (const key of Object.keys(window)) {
      if (key.startsWith('map_') && window[key] && window[key]._container) {
        return { map: window[key], L: window.L };
      }
    }

    return null;
  } catch (err) {
    console.error("❌ Erreur getMapFrame:", err);
    return null;
  }
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
  
  const iframeWin = document.getElementById('mapFrame')?.contentWindow;
  const iframeDoc = iframeWin?.document;
  
  // === DÉTECTION DU LAYERCONTROL EXISTANT (multi-méthodes) ===
  let existingControl = m._layerControl || null;
  
  if (!existingControl) {
    // 1) Propriété Leaflet interne (définie par nous lors d'un précédent appel)
    if (m.map._controlLayers && typeof m.map._controlLayers.addOverlay === 'function') {
      existingControl = m.map._controlLayers;
      console.log("[DEBUG] Contrôle trouvé via _controlLayers");
    }
  }
  
  if (!existingControl) {
    // 2) Registre global côté iframe
    try {
      if (iframeWin) {
        if (iframeWin._layerControl && typeof iframeWin._layerControl.addOverlay === 'function') {
          existingControl = iframeWin._layerControl;
          console.log("[DEBUG] Contrôle trouvé via iframe._layerControl");
        } else if (iframeWin.leafletLayersControl && typeof iframeWin.leafletLayersControl.addOverlay === 'function') {
          existingControl = iframeWin.leafletLayersControl;
          console.log("[DEBUG] Contrôle trouvé via iframe.leafletLayersControl");
        }
      }
    } catch(e) {}
  }
  
  if (!existingControl) {
    // 3) Registre global parent
    if (window.leafletLayersControl && typeof window.leafletLayersControl.addOverlay === 'function') {
      existingControl = window.leafletLayersControl;
      console.log("[DEBUG] Contrôle trouvé via registre global parent");
    }
  }
  
  if (!existingControl) {
    // 4) MÉTHODE DOM → chercher l'objet Leaflet via les event handlers de la carte
    // Quand Folium crée un L.control.layers().addTo(map), Leaflet enregistre un handler
    // de l'événement 'layeradd' dont le contexte (ctx) est le LayerControl
    try {
      var events = m.map._events || {};
      var layerAddHandlers = events.layeradd || [];
      for (var i = 0; i < layerAddHandlers.length; i++) {
        var handler = layerAddHandlers[i];
        if (handler.ctx && typeof handler.ctx.addOverlay === 'function' && typeof handler.ctx.addBaseLayer === 'function') {
          existingControl = handler.ctx;
          console.log("[DEBUG] Contrôle trouvé via event handler layeradd");
          break;
        }
      }
    } catch(e) { console.log("[DEBUG] Erreur recherche event handlers:", e); }
  }
  
  if (!existingControl) {
    // 5) Dernière tentative : chercher dans les variables globales du script Folium
    // Folium nomme ses variables layer_control_XXXX
    try {
      if (iframeWin) {
        var keys = Object.keys(iframeWin);
        for (var i = 0; i < keys.length; i++) {
          if (keys[i].indexOf('layer_control') === 0) {
            var obj = iframeWin[keys[i]];
            if (obj && typeof obj.addOverlay === 'function') {
              existingControl = obj;
              console.log("[DEBUG] Contrôle trouvé via variable globale Folium:", keys[i]);
              break;
            }
          }
        }
      }
    } catch(e) {}
  }

  // === VÉRIFIER SI UN PANNEAU EXISTE DÉJÀ DANS LE DOM ===
  var domHasControl = iframeDoc && iframeDoc.querySelector('.leaflet-control-layers');

  // === UTILISER LE CONTRÔLE EXISTANT OU EN CRÉER UN NOUVEAU ===
  if (existingControl) {
    console.log("[DEBUG] Utilisation du contrôle Leaflet existant");
    
    if (!existingControl._addedLabels) {
      existingControl._addedLabels = new Set();
    }
    
    Object.entries(dynamicLayers).forEach(([layerName, layer]) => {
      const config = LAYER_CONFIG[layerName.toLowerCase()] || { label: layerName };
      const label = config.label || layerName;
      
      if (!existingControl._addedLabels.has(label)) {
        existingControl.addOverlay(layer, label);
        existingControl._addedLabels.add(label);
        console.log(`[DEBUG] Ajout du calque "${label}" au contrôle existant`);
      }
    });
    
    m._layerControl = existingControl;
    overlaysControl = existingControl;
    window.leafletLayersControl = existingControl;
    m.map._controlLayers = existingControl;
    if (iframeWin) iframeWin._layerControl = existingControl;
    
  } else if (domHasControl) {
    // Le DOM a un contrôle Leaflet (créé par Folium) mais on n'a pas trouvé l'objet JS
    // NE PAS en créer un second ! Juste s'assurer que le custom LC JS s'applique
    console.log("[DEBUG] LayerControl DOM détecté (Folium), pas de création d'un second contrôle");
    
  } else {
    // Aucun contrôle ni dans le DOM ni en JS — en créer un nouveau (cas map1.html)
    console.log("[DEBUG] Aucun contrôle Leaflet trouvé, création d'un nouveau");
    
    const bases = (typeof getBaseLayers === 'function') ? getBaseLayers() : {};
    overlaysControl = m.L.control.layers(bases || {}, dynamicLayers, { position: "topright", collapsed: true }).addTo(m.map);
    
    overlaysControl._addedLabels = new Set(Object.keys(dynamicLayers).map(layerName => {
      const config = LAYER_CONFIG[layerName.toLowerCase()] || { label: layerName };
      return config.label || layerName;
    }));
    
    m._layerControl = overlaysControl;
    window.leafletLayersControl = overlaysControl;
    m.map._controlLayers = overlaysControl;
    if (iframeWin) iframeWin._layerControl = overlaysControl;
  }
  
  // === RÉINITIALISER LE CUSTOM LAYER CONTROL (si le JS est chargé dans l'iframe) ===
  try {
    if (iframeWin) {
      // Reset l'init flag pour permettre une réinitialisation
      const panels = iframeWin.document.querySelectorAll('.leaflet-control-layers');
      panels.forEach(function(p) { 
        if (p.dataset) p.dataset.lcInit = ''; 
        // Supprimer l'ancien custom UI si existant
        var oldRoot = p.querySelector('.lc-custom-root');
        if (oldRoot) oldRoot.remove();
      });
      // Recharger le custom layer control JS
      var lcScript = iframeWin.document.createElement('script');
      lcScript.src = '/static/js/layer-control-dark.js?t=' + Date.now();
      iframeWin.document.body.appendChild(lcScript);
    }
  } catch(e) {
    console.log("[DEBUG] Impossible de réinit le custom LC:", e);
  }

  // NOUVELLE FONCTIONNALITÉ: Gestion des événements de cochage/décochage
  // Ajouter les écouteurs d'événements seulement s'ils n'existent pas déjà
  if (!m.map._layersControlEventsBound) {
    console.log("[DEBUG] Configuration des événements de contrôle des couches");
    
    // Événement décochage : retirer la couche de la carte
    m.map.on('overlayremove', function(e) {
      console.log(`[DEBUG] Couche décochée: "${e.name}" - retrait de la carte`);
      
      // Retirer la couche du dynamicLayers si elle existe
      if (dynamicLayers[e.name]) {
        console.log(`[DEBUG] Suppression de "${e.name}" des couches dynamiques`);
        delete dynamicLayers[e.name];
      }
      
      // La couche est automatiquement retirée de la carte par Leaflet
      // Nous n'avons rien d'autre à faire ici
    });
    
    // Événement cochage : ajouter la couche à la carte
    m.map.on('overlayadd', function(e) {
      console.log(`[DEBUG] Couche cochée: "${e.name}" - ajout sur la carte`);
      
      // La couche est automatiquement ajoutée à la carte par Leaflet
      // Nous pouvons ajouter d'autres logiques ici si nécessaire
      
      // S'assurer que la couche est dans dynamicLayers
      if (!dynamicLayers[e.name]) {
        dynamicLayers[e.name] = e.layer;
        console.log(`[DEBUG] Ajout de "${e.name}" aux couches dynamiques`);
      }
    });
    
    // Marquer que les événements sont configurés pour éviter la duplication
    m.map._layersControlEventsBound = true;
  }
  
  console.log("[DEBUG] Contrôle Leaflet configuré avec", Object.keys(dynamicLayers).length, "calques");
}

// --------- MISE À JOUR INCRÉMENTALE ---------
function addIncrementalData(newData) {
  console.log("[DEBUG] Mise à jour incrémentale avec nouvelles données:", newData);
  
  Object.entries(newData).forEach(([layerKey, val]) => {
    if (!val || (Array.isArray(val) && val.length === 0)) return;
    
    try {
      console.log(`[INCREMENTAL] Traitement de ${layerKey}:`, val);
      
      // Traitement spécial pour hta_lignes
      if (layerKey === "hta_lignes" && val && typeof val === "object" && !Array.isArray(val) && !val.type) {
        // Lignes aériennes
        if (val.aerienne && val.aerienne.features && val.aerienne.features.length > 0) {
          const existingLayer = dynamicLayers["Lignes HTA Aériennes"];
          if (existingLayer && typeof existingLayer.addData === 'function') {
            existingLayer.addData(val.aerienne);
            console.log(`[INCREMENTAL] ${val.aerienne.features.length} lignes aériennes ajoutées au calque existant`);
          } else {
            // Créer le calque s'il n'existe pas
            console.log("[INCREMENTAL] Création nouveau calque lignes aériennes");
            displayAllLayers({hta_lignes: val});
          }
        }
        
        // Lignes souterraines
        if (val.souterraine && val.souterraine.features && val.souterraine.features.length > 0) {
          const existingLayer = dynamicLayers["Lignes HTA Souterraines"];
          if (existingLayer && typeof existingLayer.addData === 'function') {
            existingLayer.addData(val.souterraine);
            console.log(`[INCREMENTAL] ${val.souterraine.features.length} lignes souterraines ajoutées au calque existant`);
          } else {
            // Créer le calque s'il n'existe pas
            console.log("[INCREMENTAL] Création nouveau calque lignes souterraines");
            displayAllLayers({hta_lignes: val});
          }
        }
        return;
      }
      
      // Traitement standard pour les autres couches
      if (val.type === "FeatureCollection" && val.features && val.features.length > 0) {
        const label = LAYER_CONFIG[layerKey]?.label || layerKey;
        const existingLayer = dynamicLayers[label];
        
        if (existingLayer && typeof existingLayer.addData === 'function') {
          existingLayer.addData(val);
          console.log(`[INCREMENTAL] ${val.features.length} features ajoutées au calque "${label}"`);
        } else {
          // Créer le calque s'il n'existe pas
          console.log(`[INCREMENTAL] Création nouveau calque "${label}"`);
          const singleLayerData = {};
          singleLayerData[layerKey] = val;
          displayAllLayers(singleLayerData);
        }
      }
    } catch (err) {
      console.error(`[INCREMENTAL] Erreur traitement ${layerKey}:`, err);
    }
  });
}

// --------- LAYER DISPLAY ---------
function displayAllLayers(data) {
  console.log("[DEBUG] displayAllLayers appelée avec data:", data);
  const m = getMapFrame();
  if (!m || !m.L || !m.map) {
    console.log("[DEBUG] Map frame non accessible");
    return;
  }
  
  // MODIFICATION: Ne plus supprimer toutes les couches, mais les enrichir
  // Cela permet de préserver l'état coché/décoché des couches dans le contrôle
  console.log("[DEBUG] Enrichissement des calques existants...");
  
  // Note: On ne vide plus dynamicLayers pour préserver les couches existantes

  Object.entries(data).forEach(([layerKey, val]) => {
    console.log("[DEBUG] Traitement calque:", layerKey, "valeur:", val);
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
                    popup += `<b>${getFriendlyLabel(k)}:</b> ${htmlifyField(k, v)}<br>`;
                if (popup) layer.bindPopup(popup);
              }
            });
            console.log("[DEBUG] Calque créé:", subLayerName, "utilisation de addOrMergeLayer pour éviter la superposition");
            // Utiliser la même logique de fusion que les autres calques
            addOrMergeLayer(subkey, subLayerName, leafletLayer);
          } catch (subErr) {
            console.error(`[displayAllLayers] Erreur sous-couche ${subkey}:`, subErr);
          }
        });
        return;
      }

      // Lignes HTA (structure spéciale avec aerienne et souterraine)
      if (layerKey === "hta_lignes" && val && typeof val === "object" && !Array.isArray(val) && !val.type) {
        console.log("[DEBUG] Traitement des lignes HTA:", val);
        
        // Traiter les lignes aériennes
        if (val.aerienne && val.aerienne.features && val.aerienne.features.length > 0) {
          try {
            const leafletLayerAer = m.L.geoJSON(val.aerienne, {
              style: { color: "orange", weight: 3, opacity: 0.9 },
              onEachFeature: function (feature, layer) {
                let popup = "<b>🔌 Ligne HTA Aérienne</b><br>";
                if (feature.properties) {
                  for (const [k, v] of Object.entries(feature.properties)) {
                    popup += `<b>${getFriendlyLabel(k)}:</b> ${htmlifyField(k, v)}<br>`;
                  }
                }
                layer.bindPopup(popup);
              }
            });
            addOrMergeLayer("hta_lignes_aeriennes", "Lignes HTA Aériennes", leafletLayerAer);
            console.log("[DEBUG] Lignes HTA aériennes ajoutées:", val.aerienne.features.length);
          } catch (aerErr) {
            console.error("[displayAllLayers] Erreur lignes aériennes:", aerErr);
          }
        }
        
        // Traiter les lignes souterraines
        if (val.souterraine && val.souterraine.features && val.souterraine.features.length > 0) {
          try {
            const leafletLayerSout = m.L.geoJSON(val.souterraine, {
              style: { color: "purple", weight: 3, opacity: 0.8, dashArray: "10,5" },
              onEachFeature: function (feature, layer) {
                let popup = "<b>🔌 Ligne HTA Souterraine</b><br>";
                if (feature.properties) {
                  for (const [k, v] of Object.entries(feature.properties)) {
                    popup += `<b>${getFriendlyLabel(k)}:</b> ${htmlifyField(k, v)}<br>`;
                  }
                }
                layer.bindPopup(popup);
              }
            });
            addOrMergeLayer("hta_lignes_souterraines", "Lignes HTA Souterraines", leafletLayerSout);
            console.log("[DEBUG] Lignes HTA souterraines ajoutées:", val.souterraine.features.length);
          } catch (soutErr) {
            console.error("[displayAllLayers] Erreur lignes souterraines:", soutErr);
          }
        }
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
      
    // Validation stricte du GeoJSON avant traitement
    if (!geojson || !geojson.type || geojson.type !== "FeatureCollection" || !Array.isArray(geojson.features)) {
      console.warn(`[displayAllLayers] GeoJSON invalide pour ${layerKey}:`, geojson);
      return;
    }
    
    // Filtrer les features avec geometry valide uniquement
    geojson.features = geojson.features.filter(feature => {
      if (!feature || !feature.geometry || !feature.geometry.type || !feature.geometry.coordinates) {
        console.warn(`[displayAllLayers] Feature sans géométrie valide ignorée:`, feature);
        return false;
      }
      return true;
    });
    
    // Si plus aucune feature valide, ignorer la couche
    if (geojson.features.length === 0) {
      console.warn(`[displayAllLayers] Aucune feature valide pour ${layerKey}, couche ignorée`);
      return;
    }
      console.log(`[displayAllLayers] GeoJSON validé pour ${layerKey}:`, geojson);
    } catch (normalizeErr) {
      console.error(`[displayAllLayers] Erreur normalisation ${layerKey}:`, normalizeErr);
      return;
    }

    const label = LAYER_CONFIG[layerKey]?.label || layerKey;
    const style = LAYER_CONFIG[layerKey]?.color ? { color: LAYER_CONFIG[layerKey].color } : {};

    // Fonction helper pour fusionner ou créer un calque (VERSION SIMPLIFIÉE)
    function addOrMergeLayer(layerKey, label, newLeafletLayer) {
      // Vérifier si un calque du même type existe déjà
      const existingLayer = dynamicLayers[label];
      
      if (existingLayer && typeof existingLayer.addData === 'function') {
        console.log(`[DEBUG] Fusion des nouvelles features avec le calque existant "${label}"`);
        
        // Extraire les features GeoJSON du nouveau calque
        const newFeatures = [];
        newLeafletLayer.eachLayer(function(layer) {
          if (layer.feature) {
            newFeatures.push(layer.feature);
          }
        });
        
        // Ajouter les nouvelles features au calque existant
        // Cette méthode utilise les mêmes fonctions de style du calque existant
        if (newFeatures.length > 0) {
          const newGeoJSON = {
            type: "FeatureCollection",
            features: newFeatures
          };
          existingLayer.addData(newGeoJSON);
          console.log(`[DEBUG] ${newFeatures.length} features ajoutées au calque existant "${label}" avec le même style`);
        }
        
        // IMPORTANT : Supprimer le nouveau calque de la carte pour éviter la superposition
        if (m.map.hasLayer(newLeafletLayer)) {
          m.map.removeLayer(newLeafletLayer);
          console.log(`[DEBUG] Nouveau calque temporaire "${label}" supprimé de la carte après fusion`);
        }
        
        return false; // Indique qu'on a fusionné, pas créé
      } else {
        console.log(`[DEBUG] Création d'un nouveau calque "${label}"`);
        // Créer un nouveau calque
        dynamicLayers[label] = newLeafletLayer;
        
        // S'assurer que le calque est ajouté à la carte
        if (!m.map.hasLayer(newLeafletLayer)) {
          newLeafletLayer.addTo(m.map);
        }
        
        // Ajouter le calque au contrôle s'il existe
        const control = m._layerControl || overlaysControl;
        if (control && typeof control.addOverlay === 'function') {
          // Vérifier si ce label n'est pas déjà dans le contrôle
          if (!control._addedLabels || !control._addedLabels.has(label)) {
            control.addOverlay(newLeafletLayer, label);
            if (control._addedLabels) {
              control._addedLabels.add(label);
            }
            console.log(`[DEBUG] Nouveau calque "${label}" ajouté au contrôle`);
          }
        }
        
        return true; // Indique qu'on a créé un nouveau calque
      }
    }
    


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
              popup += `<b>${k}:</b> ${v}<br>`;
            }
          }
          if (popup) layer.bindPopup(popup);
        }
      });
      addOrMergeLayer(layerKey, label, leafletLayer);
      return;
    }

    // ----------- Postes HTA ----------- (icône 2 éclairs orange)
    if (layerKey === "postes_hta") {
      try {
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
                popup += `<b>${k}:</b> ${v}<br>`;
              }
            }
            if (popup) layer.bindPopup(popup);
          }
        });
        addOrMergeLayer(layerKey, label, leafletLayer);
      } catch (htaErr) {
        console.error(`[displayAllLayers] Erreur création couche postes_hta:`, htaErr);
        console.log('[displayAllLayers] GeoJSON postes_hta problématique:', JSON.stringify(geojson, null, 2));
      }
      return;
    }

    // ----------- Éleveurs ----------- (popup personnalisé)
    if (layerKey === "eleveurs") {
      const leafletLayer = m.L.geoJSON(geojson, {
        pointToLayer: function (feature, latlng) {
          return m.L.marker(latlng, {
            icon: m.L.divIcon({
              html: `<span style="font-size:1.5em;color:purple;">🐄</span>`,
              className: 'eleveur-marker',
              iconSize: [28, 28],
              iconAnchor: [14, 28]
            })
          });
        },
        onEachFeature: function (feature, layer) {
          const props = feature.properties || {};
          
          // Construction du nom complet
          let nomComplet = "";
          if (props.prenom1Uni && props.nomUniteLe) {
            nomComplet = `${props.prenom1Uni} ${props.nomUniteLe}`;
          } else if (props.nomUniteLe) {
            nomComplet = props.nomUniteLe;
          } else if (props.denominati) {
            nomComplet = props.denominati;
          }
          
          // Construction du popup personnalisé
          let popup = `<div style="font-family: 'Poppins', Arial, sans-serif; font-size: 15px; min-width: 250px; max-width: 355px;">`;
          popup += `<div style="font-weight: 700; font-size: 18px; margin-bottom: 4px; letter-spacing: 0.3px; color: purple;">🐄 Éleveur</div>`;
          popup += `<table style="width: 100%;">`;
          
          function row(label, val) { 
            return val ? `<tr><th style="text-align: left; color: #28616a; font-weight: 500; min-width: 95px;">${label}</th><td style="color: #2d2d2d; max-width:200px; word-break: break-word;">${val}</td></tr>` : ""; 
          }
          
          if (nomComplet) popup += row("Nom", nomComplet);
          if (props.siret) popup += row("SIRET", props.siret);
          
          popup += `</table></div>`;
          layer.bindPopup(popup, {maxWidth: 400});
        }
      });
      addOrMergeLayer(layerKey, label, leafletLayer);
      return;
    }

    // ----------- Consommations Électriques Enedis ----------- (marqueurs proportionnels)
    if (layerKey === "enedis") {
      console.log("[ENEDIS] Traitement des données Enedis:", geojson);
      
      // Données Enedis: [{latitude, longitude, consommation_mwh, secteur, adresse, ...}]
      if (!Array.isArray(geojson) || geojson.length === 0) {
        console.log("[ENEDIS] Aucune donnée Enedis à afficher");
        return;
      }
      
      console.log(`[ENEDIS] ${geojson.length} points de consommation à afficher`);
      
      // Convertir en FeatureCollection si nécessaire
      const features = geojson.map(item => ({
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [item.longitude, item.latitude]
        },
        properties: item
      }));
      
      const featureCollection = {
        type: "FeatureCollection",
        features: features
      };
      
      const leafletLayer = m.L.geoJSON(featureCollection, {
        pointToLayer: function (feature, latlng) {
          const props = feature.properties;
          const conso = props.consommation_mwh || 0;
          
          // Taille du marqueur proportionnelle à la consommation
          let radius = 8; // Taille minimale
          if (conso > 100) radius = 20;
          else if (conso > 50) radius = 16;
          else if (conso > 20) radius = 12;
          else if (conso > 5) radius = 10;
          
          // Couleur selon le secteur
          let color = '#FF5733'; // Par défaut: rouge/orange
          if (props.secteur === 'INDUSTRIE') color = '#C70039';
          else if (props.secteur === 'TERTIAIRE') color = '#FF8C00';
          else if (props.secteur === 'AGRICULTURE') color = '#28A745';
          
          return m.L.circleMarker(latlng, {
            radius: radius,
            fillColor: color,
            color: '#fff',
            weight: 2,
            opacity: 0.9,
            fillOpacity: 0.7
          });
        },
        onEachFeature: function (feature, layer) {
          const props = feature.properties;
          
          // Popup informatif
          let popup = `<div style="font-family: 'Poppins', Arial, sans-serif; font-size: 14px; min-width: 280px;">`;
          popup += `<div style="font-weight: 700; font-size: 17px; margin-bottom: 8px; color: #FF5733;">⚡ Consommation Électrique</div>`;
          popup += `<table style="width: 100%;">`;
          
          function row(label, val, highlight = false) {
            const style = highlight ? 'font-weight: 700; font-size: 16px; color: #C70039;' : 'color: #2d2d2d;';
            return val ? `<tr><th style="text-align: left; color: #28616a; font-weight: 500; padding: 4px 8px 4px 0;">${label}</th><td style="${style} padding: 4px 0;">${val}</td></tr>` : "";
          }
          
          popup += row("Consommation", `${props.consommation_mwh.toFixed(2)} MWh/an`, true);
          popup += row("Secteur", props.secteur);
          popup += row("Adresse", props.adresse);
          popup += row("Commune", props.nom_commune);
          if (props.nombre_de_sites > 1) popup += row("Nb sites", props.nombre_de_sites);
          if (props.annee) popup += row("Année", props.annee);
          
          popup += `</table>`;
          
          // Calcul ROI indicatif
          const tarifMoyenKwh = 0.20; // €/kWh
          const economieAnnuelle = props.consommation_mwh * 1000 * tarifMoyenKwh;
          popup += `<div style="margin-top: 10px; padding: 8px; background: #f0f8ff; border-left: 3px solid #007bff;">`;
          popup += `<b>💡 Économies potentielles:</b><br>`;
          popup += `~${economieAnnuelle.toLocaleString('fr-FR', {maximumFractionDigits: 0})} €/an`;
          popup += `</div>`;
          
          popup += `</div>`;
          
          layer.bindPopup(popup, {maxWidth: 350});
        }
      });
      
      addOrMergeLayer(layerKey, label, leafletLayer);
      return;
    }

    // ----------- Cas par défaut pour autres types -----------
    const config = LAYER_CONFIG[layerKey] || {};
    const defaultStyle = config.color ? { color: config.color } : {};
    const leafletLayer = m.L.geoJSON(geojson, { 
      style: defaultStyle,
      onEachFeature: function (feature, layer) {
        let popup = `<b>${label || layerKey}</b><br>`;
        if (feature.properties) {
          for (const [k, v] of Object.entries(feature.properties)) {
            popup += `<b>${k}:</b> ${v}<br>`;
          }
        }
        layer.bindPopup(popup);
      }
    });
    addOrMergeLayer(layerKey, label, leafletLayer);

    } catch (layerErr) {
      console.error(`[displayAllLayers] Erreur traitement couche ${layerKey}:`, layerErr);
    }
  });

  // Rafraîchir le contrôle de couches côté parent
  updateLeafletLayersControl(); // Réactivé pour la synchronisation

  // Si la carte embarquée supporte la gestion propre des overlays, lui transmettre un snapshot
  try {
    const m2 = getMapFrame();
    if (m2 && typeof m2.setOverlaysControl === 'function') {
      const overlays = {};
      Object.entries(dynamicLayers).forEach(([label, layer]) => {
        try {
          if (layer && typeof layer.toGeoJSON === 'function') {
            const fc = layer.toGeoJSON();
            // Déterminer une clé de couche à partir du label pour récupérer la couleur
            let layerKeyFromLabel = Object.keys(LAYER_CONFIG).find(k => (LAYER_CONFIG[k]?.label || k) === label) || label;
            const color = LAYER_CONFIG[layerKeyFromLabel]?.color;
            // Taguer les features pour que map1.html détecte le type et applique les icônes
            const features = (fc.features || []).map(f => {
              try {
                if (f && f.properties) f.properties._layer = layerKeyFromLabel;
              } catch {}
              return f;
            });
            overlays[label] = { type: 'FeatureCollection', features, style: color ? { color } : {} };
          }
        } catch {}
      });
      m2.setOverlaysControl(overlays, {});
    }
  } catch (e) {
    console.warn('setOverlaysControl propagation failed:', e);
  }
}

// --------- INFO PANEL ---------
function updateInfoPanel(arr) {
  if (!arr || arr.length === 0) {
    document.getElementById("info-panel").innerHTML = 
      `<div class="alert alert-secondary mb-0">Aucune donnée disponible</div>`;
    return;
  }

  let html = '';
  let totalObjects = 0;
  const layerCounts = {};
  
  // Analyser les données pour chaque commune/résultat
  arr.forEach((data, index) => {
    const commune = data.commune || data.address || `Résultat ${index + 1}`;
    html += `<h6 class="text-primary mt-3 mb-2"><i class="fas fa-map-marker-alt"></i> ${commune}</h6>`;
    
    // Coordonnées si disponibles
    if (data.lat && data.lon) {
      html += `<p class="mb-2 small text-muted"><strong>Coordonnées:</strong> ${data.lat.toFixed(6)}, ${data.lon.toFixed(6)}</p>`;
    }
    
    let localCount = 0;
    
    // Analyser chaque type de données
    Object.entries(data).forEach(([key, val]) => {
      if (!val || key === 'lat' || key === 'lon' || key === 'commune' || key === 'address' || key === 'carte_url') return;
      
      let count = 0;
      let label = LAYER_CONFIG[key]?.label || key;
      
      // Compter les objets selon le type
      if (val.type === "FeatureCollection" && Array.isArray(val.features)) {
        count = val.features.length;
      } else if (Array.isArray(val)) {
        count = val.length;
      } else if (typeof val === 'object' && val !== null) {
        count = 1;
      }
      
      if (count > 0) {
        const color = LAYER_CONFIG[key]?.color || '#007bff';
        html += `<div class="d-flex justify-content-between align-items-center py-1">`;
        html += `<span><i class="fas fa-layer-group" style="color: ${color}"></i> ${label}</span>`;
        html += `<span class="badge bg-primary">${count}</span>`;
        html += `</div>`;
        
        localCount += count;
        layerCounts[label] = (layerCounts[label] || 0) + count;
      }
    });
    
    if (localCount === 0) {
      html += `<p class="text-muted small">Aucune donnée trouvée pour cette zone</p>`;
    }
    
    totalObjects += localCount;
  });
  
  // Résumé global en haut
  let summary = `<div class="alert alert-info mb-3">`;
  summary += `<h6 class="mb-2"><i class="fas fa-info-circle"></i> Résumé de la recherche</h6>`;
  summary += `<div class="row">`;
  summary += `<div class="col-4 text-center"><strong>${arr.length}</strong><br><small>Zone(s)</small></div>`;
  summary += `<div class="col-4 text-center"><strong>${totalObjects}</strong><br><small>Objets total</small></div>`;
  summary += `<div class="col-4 text-center"><strong>${Object.keys(layerCounts).length}</strong><br><small>Types de données</small></div>`;
  summary += `</div></div>`;
  
  document.getElementById("info-panel").innerHTML = summary + html;
  
  // Auto-ouverture désactivée pour éviter les boucles
  // if (totalObjects > 0) {
  //   const infoCollapse = document.getElementById("infoCollapse");
  //   if (infoCollapse && !infoCollapse.classList.contains("show")) {
  //     const infoButton = document.querySelector('[data-bs-target="#infoCollapse"]');
  //     if (infoButton) {
  //       infoButton.click();
  //     }
  //   }
  // }
}

// --------- FUSION DES RÉSULTATS SSE ---------
function mergeResults(arr) {
  const expectedKeys = Object.keys(LAYER_CONFIG);
  const res = {};
  expectedKeys.forEach(k => { res[k] = []; });
  
  // Structure spéciale pour hta_lignes
  res.hta_lignes = { aerienne: { features: [] }, souterraine: { features: [] } };
  
  arr.forEach(obj => {
    for (const [k, v] of Object.entries(obj)) {
      // Traitement spécial pour hta_lignes
      if (k === "hta_lignes" && v && typeof v === "object") {
        if (v.aerienne && v.aerienne.features && Array.isArray(v.aerienne.features)) {
          res.hta_lignes.aerienne.features = res.hta_lignes.aerienne.features.concat(v.aerienne.features);
        }
        if (v.souterraine && v.souterraine.features && Array.isArray(v.souterraine.features)) {
          res.hta_lignes.souterraine.features = res.hta_lignes.souterraine.features.concat(v.souterraine.features);
        }
        continue;
      }
      
      // Traitement standard pour les autres couches
      if (!res[k]) res[k] = [];
      if (v?.type === "FeatureCollection" && Array.isArray(v.features)) {
        res[k] = res[k].concat(v.features);
      } else if (Array.isArray(v) && v[0]?.type === "Feature") {
        res[k] = res[k].concat(v);
      }
    }
  });
  
  Object.keys(res).forEach(k => {
    if (k === "hta_lignes") {
      // Garder la structure spéciale pour hta_lignes
      res[k].aerienne.type = "FeatureCollection";
      res[k].souterraine.type = "FeatureCollection";
    } else {
      res[k] = { type: "FeatureCollection", features: res[k] };
    }
  });
  return res;
}

// --------- RECHERCHE UNIFIÉE (ADRESSE / COORDONNÉES) ---------
// Variable globale pour le debouncing
let lastAddressSearchTime = 0;
let isSearchInProgress = false;

async function handleUnifiedSearch(e) {
  e?.preventDefault?.();
  
  // Protection contre les exécutions concurrentes (une seule recherche à la fois)
  if (isSearchInProgress) {
    console.log('🔄 Recherche déjà en cours, annulation');
    return;
  }
  
  // Protection contre les doubles clics et recherches multiples (2s)
  const now = Date.now();
  const minDelay = 2000; // 2 secondes minimum entre deux recherches
  
  if (now - lastAddressSearchTime < minDelay) {
    console.log('🔄 Recherche en cours ou trop rapide, annulation');
    return;
  }
  
  lastAddressSearchTime = now;
  isSearchInProgress = true;
  
  // Obtenir les éléments de l'interface - CORRECTION: chercher spécifiquement le bouton du formulaire d'adresse
  const addressForm = document.getElementById('unifiedSearchForm');
  const submitBtn = addressForm ? addressForm.querySelector('button[type="submit"]') : null;
  const searchInput = document.getElementById("search_input");
  const logElement = createOrGetSearchLog();
  
  console.log('[handleUnifiedSearch] Formulaire:', addressForm ? 'trouvé' : 'NON TROUVÉ');
  console.log('[handleUnifiedSearch] Bouton submit:', submitBtn ? submitBtn.textContent : 'NON TROUVÉ');
  
  // État initial - BLOQUER LE BOUTON
  const originalBtnText = submitBtn ? submitBtn.textContent : 'Rechercher';
  
  // Fonction pour débloquer le bouton (utilisée partout)
  const unlockButton = () => {
    console.log('🔓 Tentative de déblocage du bouton...', submitBtn);
    if (submitBtn) {
      // Débloquer complètement
      submitBtn.disabled = false;
      submitBtn.removeAttribute('disabled');
      
      // Nettoyer toutes les classes problématiques
      submitBtn.classList.remove('disabled');
      submitBtn.classList.remove('btn-secondary');
      
      // Forcer la classe btn-primary
      if (!submitBtn.classList.contains('btn-primary')) {
        submitBtn.classList.add('btn-primary');
      }
      
      submitBtn.innerHTML = '<i class="bi bi-search"></i> Rechercher';
      
      console.log('✅ Bouton débloqué - État:', {
        disabled: submitBtn.disabled,
        hasDisabledAttr: submitBtn.hasAttribute('disabled'),
        classes: submitBtn.className,
        innerHTML: submitBtn.innerHTML
      });
    } else {
      console.error('❌ Bouton introuvable pour déblocage');
    }
    isSearchInProgress = false;
  };
  
  try {
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.classList.add('disabled');
      submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Recherche en cours...';
    }
    setSearchStatus('loading', submitBtn, 'Recherche en cours...');
    logSearch('🔍 Initialisation de la recherche...');
    
    const v = searchInput.value.trim();
    if (!v) {
      logSearch('❌ Erreur : Aucune adresse saisie', 'error');
      alert("Saisissez une adresse (ex : Limoges) ou des coordonnées (ex : 45.85, 1.25)");
      return;
    }

    logSearch(`📍 Analyse de l'entrée : "${v}"`);

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
      logSearch(`📌 Coordonnées détectées : ${coords.lat.toFixed(6)}, ${coords.lon.toFixed(6)}`);
      ps.append("lat", coords.lat);
      ps.append("lon", coords.lon);
    } else {
      logSearch(`🏠 Adresse détectée : géocodage en cours...`);
      ps.append("address", v);
    }
    
    ps.append("sirene_radius", "0.05");
    ps.append("ht_radius", (document.getElementById("ht_max_distance").value / 1000).toString());
    ps.append("bt_radius", (document.getElementById("bt_max_distance").value / 1000).toString());

    logSearch('🌐 Envoi de la requête au serveur...');
    
    const res = await fetch("/search_by_address?" + ps.toString());
    
    if (!res.ok) {
      logSearch(`❌ Erreur serveur : ${res.status}`, 'error');
      alert("Erreur serveur : " + res.status);
      return;
    }
    
    logSearch('📦 Réception des données...');
    const data = await res.json();
    
    if (data.error) {
      logSearch(`❌ Erreur : ${data.error}`, 'error');
      alert(data.error);
      return;
    }

    // Analyser les données reçues
    const stats = analyzeSearchResults(data);
    logSearch(`✅ Données reçues : ${stats}`);
    
    // Mémorise le contexte pour rapport "point courant"
    window.lastSearchData = data;
    
    // Fonction pour afficher les couches une fois l'iframe prête
    const applyLayersAndZoom = (skipLayers) => {
      if (!skipLayers) {
        logSearch('🎨 Affichage des couches de données...');
        try {
          displayAllLayers(data);
        } catch (displayErr) {
          console.error('[handleUnifiedSearch] Erreur displayAllLayers:', displayErr);
          logSearch('⚠️ Certaines couches n\'ont pas pu être affichées', 'warning');
        }
      }
      try {
        updateInfoPanel([data]);
      } catch (infoPanelErr) {
        console.error('[handleUnifiedSearch] Erreur updateInfoPanel:', infoPanelErr);
      }
      const m = getMapFrame();
      if (data.lat && data.lon && m?.setView) {
        let z = 14;
        if (data.parcelles && data.parcelles.features && data.parcelles.features.length === 1) z = 16;
        if (data.rpg && data.rpg.features && data.rpg.features.length === 1) z = 16;
        logSearch(`🎯 Centrage de la carte sur ${data.lat.toFixed(6)}, ${data.lon.toFixed(6)} (zoom ${z})`);
        m.setView(data.lat, data.lon, z);
      }
    };

    // Recharge la carte générée dans l'iframe
    if (data.carte_url) {
      logSearch('🗺️ Chargement de la carte interactive...');
      console.log("[DEBUG] Chargement nouvelle carte:", data.carte_url);
      const iframe = document.getElementById("mapFrame");
      const newSrc = data.carte_url + (data.carte_url.includes('?') ? '&' : '?') + 'cache=' + Date.now();
      console.log("[DEBUG] URL finale iframe:", newSrc);
      // Reset les couches dynamiques car Folium a déjà tout
      dynamicLayers = {};
      window.leafletLayersControl = null;
      // Attendre que l'iframe finisse de charger
      iframe.onload = () => {
        console.log("[DEBUG] Iframe Folium chargée, skip displayAllLayers (Folium a déjà toutes les couches)");
        // skipLayers=true car la carte Folium contient déjà toutes les couches
        setTimeout(() => applyLayersAndZoom(true), 150);
      };
      iframe.src = newSrc;
    } else {
      // Pas de carte_url, appliquer directement
      applyLayersAndZoom();
    }
    
    logSearch('🎉 Recherche terminée avec succès !', 'success');
    
    // Effacer les logs après quelques secondes si succès
    setTimeout(() => {
      if (logElement && logElement.textContent.includes('succès')) {
        clearSearchLog();
      }
    }, 5000);
    
  } catch (err) {
    logSearch(`❌ Erreur de requête : ${err.message || err}`, 'error');
    console.error('[handleUnifiedSearch] Erreur:', err);
    alert("Erreur de requête : " + (err.message || err));
  } finally {
    // TOUJOURS débloquer le bouton, même en cas d'erreur
    unlockButton();
  }
}

// --------- RECHERCHE PAR COMMUNE ---------
let lastCommuneSearchTime = 0;
let isCommuneSearchRunning = false; // Flag pour éviter les recherches simultanées

async function handleCommuneSearch(e) {
  console.log('🚀 [COMMUNE_SEARCH] Fonction handleCommuneSearch appelée', {
    event: e?.type,
    isCommuneSearchRunning,
    timestamp: new Date().toISOString()
  });
  
  // PROTECTION 1: Empêcher le comportement par défaut du formulaire
  if (e) {
    e.preventDefault();
    e.stopPropagation();
    console.log('✅ [COMMUNE_SEARCH] preventDefault et stopPropagation appelés');
  }
  
  // PROTECTION 2: Éviter les recherches simultanées
  if (isCommuneSearchRunning) {
    console.warn('🔄 [PROTECTION] Recherche commune déjà en cours, annulation');
    return;
  }
  
  // PROTECTION 3: Debouncing - minimum 1 seconde entre deux recherches
  const now = Date.now();
  const minDelay = 1000;
  
  if (now - lastCommuneSearchTime < minDelay) {
    console.log('🔄 [DEBOUNCE] Recherche commune trop rapide, annulation');
    return;
  }
  
  console.log('✅ [START] Démarrage recherche commune');
  lastCommuneSearchTime = now;
  isCommuneSearchRunning = true;
  
  // PROTECTION 4: Bloquer le bouton de recherche
  const searchBtn = document.querySelector('#communeSearchForm button[type="submit"]');
  const originalBtnText = searchBtn ? searchBtn.innerHTML : '';
  if (searchBtn) {
    searchBtn.disabled = true;
    searchBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Recherche en cours...';
    searchBtn.style.opacity = '0.6';
  }
  
  setCommuneSearchLog('⏳ Connexion au serveur...', '#0a58ca');
  
  // Fonction de nettoyage (sans timeout - recherche illimitée)
  const cleanup = () => {
    isCommuneSearchRunning = false;
    // Réactiver le bouton
    if (searchBtn) {
      searchBtn.disabled = false;
      searchBtn.innerHTML = originalBtnText;
      searchBtn.style.opacity = '1';
    }
    console.log('🧹 [CLEANUP] Flag réinitialisé et bouton réactivé');
  };
  
  switchMap("/static/map.html", async () => {
    const commune = document.getElementById("commune")?.value.trim();
    if (!commune) {
      setCommuneSearchLog('❗️ Veuillez saisir une commune.', 'red');
      cleanup();
      alert("Commune requise.");
      return;
    }
    
    setCommuneSearchLog('🔄 Envoi de la requête... Calculs en cours...', '#0a58ca');
    const ps = new URLSearchParams({
      commune,
      culture: document.getElementById("culture")?.value || "",
      min_area_ha: document.getElementById("minSurface")?.value || 0,
      max_area_ha: document.getElementById("maxSurface")?.value || 1e9,
      ht_max_distance: document.getElementById("ht_max_distance_commune")?.value || 5000,
      bt_max_distance: document.getElementById("bt_max_distance_commune")?.value || 2000,
      sirene_radius: 0.05,
      // Filtres RPG
      filter_rpg: document.getElementById("filter_rpg_commune")?.checked || false,
      rpg_min_area: document.getElementById("rpg_min_area")?.value || 1,
      rpg_max_area: document.getElementById("rpg_max_area")?.value || 1000,
      // Filtres Parkings  
      filter_parkings: document.getElementById("filter_parkings_commune")?.checked || false,
      parking_min_area: document.getElementById("parking_min_area")?.value || 1500,
      // Filtres Friches
      filter_friches: document.getElementById("filter_friches_commune")?.checked || false,
      friches_min_area: document.getElementById("friches_min_area")?.value || 1000,
      // Filtres Zones
      filter_zones: document.getElementById("filter_zones_commune")?.checked || false,
      zones_min_area: document.getElementById("zones_min_area")?.value || 1000,
      zones_type_filter: document.getElementById("zones_type_filter")?.value || "",
      // Filtres Toitures
      filter_toitures: document.getElementById("filter_toitures_commune")?.checked || false,
      toitures_min_surface: document.getElementById("min_surface_toiture")?.value || 100,
    // Distances globales
    filter_by_distance: document.getElementById("filter_by_distance_commune")?.checked || false,
    max_distance_bt: document.getElementById("bt_max_distance_commune")?.value || 2000,
    max_distance_hta: document.getElementById("ht_max_distance_commune")?.value || 5000,
    distance_logic: (document.querySelector('input[name="distance_logic"]:checked')?.value || 'OR'),
    poste_type_filter: (document.querySelector('input[name="poste_type_filter"]:checked')?.value || 'ALL'),
    // Filtres HTA aériens/souterrains
    filter_hta_lines_aerial: document.getElementById("filter_hta_lines_aerial")?.checked || false,
    filter_hta_lines_underground: document.getElementById("filter_hta_lines_underground")?.checked || false,
    hta_aerial_max_km: document.getElementById("hta_aerial_max_km")?.value || 1000,
    hta_underground_max_km: document.getElementById("hta_underground_max_km")?.value || 500
    });
    try {
      setCommuneSearchLog('📦 Traitement des données reçues...', '#0a58ca');
      const res = await fetch("/search_by_commune?" + ps.toString());
      if (!res.ok) {
        setCommuneSearchLog('❌ Erreur serveur : ' + res.status, 'red');
        cleanup();
        alert('Erreur serveur : ' + res.status);
        return;
      }
      const data = await res.json();
      if (data.error) {
        setCommuneSearchLog('❌ Erreur : ' + data.error, 'red');
        cleanup();
        alert(data.error);
        return;
      }
      // Fonction pour appliquer couches + zoom une fois iframe prête
      const applyCommuneLayers = (skipLayers) => {
        setCommuneSearchLog('🖼️ Affichage des résultats...', '#198754');
        try {
          window.lastCommuneSearch = { commune: commune, timestamp: Date.now() };
        } catch (storageError) {
          console.warn('⚠️ [STORAGE] Impossible de sauvegarder lastCommuneSearch:', storageError);
        }
        if (!skipLayers) {
          displayAllLayers(data);
        }
        updateInfoPanel([data]);
        const m = getMapFrame();
        if (data.lat && data.lon && m?.setView) m.setView(data.lat, data.lon, 13);
      };

      // Charger la carte générée si disponible
      if (data.carte_url) {
        setCommuneSearchLog('🗺️ Chargement de la carte interactive...', '#198754');
        const iframe = document.getElementById('mapFrame');
        if (iframe) {
          try {
            // Reset les couches dynamiques car Folium a déjà tout
            dynamicLayers = {};
            window.leafletLayersControl = null;
            const newSrc = data.carte_url + (data.carte_url.includes('?') ? '&' : '?') + 't=' + Date.now();
            iframe.onload = () => {
              console.log('✅ [IFRAME] Carte commune Folium chargée, skip displayAllLayers');
              // skipLayers=true car Folium a déjà toutes les couches
              setTimeout(() => applyCommuneLayers(true), 150);
            };
            iframe.src = newSrc;
            console.log('✅ [IFRAME] Chargement lancé:', newSrc);
          } catch (storageError) {
            console.warn('⚠️ [STORAGE] Erreur accès storage (Tracking Prevention):', storageError);
            iframe.src = data.carte_url;
            setTimeout(() => applyCommuneLayers(true), 500);
          }
        }
      } else {
        // Pas de carte_url, appliquer directement
        applyCommuneLayers(false);
      }
      setCommuneSearchLog('✅ Recherche terminée avec succès !', '#198754');
      
      // Réinitialiser le flag et nettoyer
      console.log('✅ [SUCCESS] Recherche terminée');
      cleanup();
      
    } catch (err) {
      setCommuneSearchLog('❌ Erreur lors de la recherche : ' + err, 'red');
      alert("Erreur lors de la recherche par commune : " + err);
      
      // Réinitialiser le flag en cas d'erreur aussi
      console.error('❌ [ERROR] Erreur recherche:', err);
      cleanup();
    }
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
    if (document.getElementById("filterHtaLinesAerial")?.checked) types.push("HTA_LINES_AERIAL");
    if (document.getElementById("filterHtaLinesUnderground")?.checked) types.push("HTA_LINES_UNDERGROUND");
    if (types.length === 0) return alert("Sélectionnez au moins un type de réseau.");
    // Convertir les sliders (mètres) en kilomètres pour le backend SSE
    const bt_m = parseFloat(document.getElementById("bt_max_distance_dept")?.value || "");
    const ht_m = parseFloat(document.getElementById("ht_max_distance_dept")?.value || "");
    const hta_aerial_m = parseFloat(document.getElementById("hta_lines_aerial_distance_dept")?.value || "");
    const hta_underground_m = parseFloat(document.getElementById("hta_lines_underground_distance_dept")?.value || "");
    const bt_km = isNaN(bt_m) ? "" : (bt_m / 1000);
    const ht_km = isNaN(ht_m) ? "" : (ht_m / 1000);
    const hta_aerial_km = isNaN(hta_aerial_m) ? "" : (hta_aerial_m / 1000);
    const hta_underground_km = isNaN(hta_underground_m) ? "" : (hta_underground_m / 1000);
    const params = {
      department: dept,
      min_area_ha: document.getElementById("minSurface")?.value || "",
      max_area_ha: document.getElementById("maxSurface")?.value || "",
      bt_max_distance: bt_km,
      ht_max_distance: ht_km,
      hta_aerial_max_distance: hta_aerial_km,
      hta_underground_max_distance: hta_underground_km,
      filter_hta_lines_aerial: document.getElementById("filterHtaLinesAerial")?.checked || false,
      filter_hta_lines_underground: document.getElementById("filterHtaLinesUnderground")?.checked || false,
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
      // Mise à jour incrémentale : ajouter seulement les nouvelles données
      addIncrementalData(r);
      updateInfoPanel(results);
      const m = getMapFrame();
      if (r.lat && r.lon && m?.setView) m.setView(r.lat, r.lon, 11);
    });
    es.addEventListener("end", async e => {
      if (logEl) logEl.textContent += e.data + "\n";
      console.log("[DEBUG] Fin SSE, aucun traitement supplémentaire nécessaire (mise à jour incrémentale)");
      es.close();
      
      // 🗺️ SAUVEGARDE AUTO: Générer une carte département avec toutes les données
      if (results.length > 0) {
        console.log(`✅ [DEPT] Recherche terminée: ${results.length} résultats. Génération carte...`);
        const deptNum = params.department || dept;
        
        try {
          // Envoyer une requête pour générer la carte finale
          const saveResponse = await fetch('/api/save_dept_map', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
              department: deptNum,
              results: results,
              params: params
            })
          });
          
          const saveData = await saveResponse.json();
          if (saveData.success) {
            console.log(`✅ [DEPT] Carte sauvegardée: ${saveData.filename}`);
            if (logEl) logEl.textContent += `\n✅ Carte sauvegardée: ${saveData.filename}\n`;
          } else {
            console.warn(`⚠️ [DEPT] Erreur sauvegarde carte: ${saveData.error}`);
          }
        } catch (err) {
          console.error(`❌ [DEPT] Erreur lors de la sauvegarde:`, err);
        }
      }
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
        search_radius: "0.05",
        interface_version: "3.2.1"
    });
    
    window.open(`/rapport_point?${params.toString()}`, "_blank");
}
// Rapport par commune
// (Supprimé: doublon qui ouvrait l'ancienne route /rapport_commune)

// Rapport par département
function generateDeptReport() {
  console.log("[generateDeptReport] Début");
  console.log("[generateDeptReport] window.lastDeptResults:", window.lastDeptResults);
  
  if (!window.lastDeptResults || window.lastDeptResults.length === 0) {
    alert("Faites d'abord une recherche départementale !");
    return;
  }
  
  console.log("[generateDeptReport] Nombre de rapports:", window.lastDeptResults.length);
  
  const w = window.open("", "_blank");
  if (!w) {
    alert("Impossible d'ouvrir un nouvel onglet. Vérifiez que les popups ne sont pas bloqués.");
    return;
  }
  
  // Afficher un message de chargement dans la fenêtre
  w.document.write('<html><body><h2>Génération du rapport en cours...</h2><p>Veuillez patienter.</p></body></html>');
  
  console.log("[generateDeptReport] Envoi requête POST");
  
  fetch('/rapport_departement_post', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: window.lastDeptResults })
  })
    .then(res => {
      console.log("[generateDeptReport] Réponse reçue, status:", res.status);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      return res.text();
    })
    .then(html => {
      console.log("[generateDeptReport] HTML reçu, taille:", html.length, "caractères");
      if (html.length < 100) {
        console.warn("[generateDeptReport] HTML suspicieusement court:", html);
      }
      w.document.open();
      w.document.write(html);
      w.document.close();
      console.log("[generateDeptReport] Rapport affiché avec succès");
    })
    .catch(err => {
      console.error("[generateDeptReport] Erreur:", err);
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

// --------- ENVOI VERS KPI ---------
async function sendToKPI(lat, lon, type, properties, buttonElement) {
  console.log('📤 [KPI] Envoi vers KPI:', { lat, lon, type, properties });
  
  // Afficher un message de chargement
  let originalContent = null;
  if (buttonElement) {
    originalContent = buttonElement.innerHTML;
    buttonElement.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Envoi...';
    buttonElement.disabled = true;
  }
  
  try {
    const response = await fetch('/api/send_to_kpi', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lat: lat,
        lon: lon,
        type: type,
        properties: properties
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      alert(`✅ Dossier envoyé vers KPI !\n\n📋 ${result.summary}\n\n📊 Statistiques:\n- Postes BT: ${result.stats.postes_bt}\n- Postes HTA: ${result.stats.postes_hta}\n- Zones PLU: ${result.stats.zones_plu}\n- Risques: ${result.stats.risques}\n\nID KPI: ${result.kpi_id || 'N/A (KPI non disponible)'}\n💾 Backup: ${result.backup_file}`);
      console.log('✅ [KPI] Envoi réussi:', result);
    } else {
      alert(`❌ Erreur d'envoi vers KPI:\n${result.error || 'Erreur inconnue'}`);
      console.error('❌ [KPI] Erreur:', result);
    }
  } catch (error) {
    alert(`❌ Erreur de connexion:\n${error.message}`);
    console.error('❌ [KPI] Exception:', error);
  } finally {
    if (buttonElement && originalContent !== null) {
      buttonElement.innerHTML = originalContent;
      buttonElement.disabled = false;
    }
  }
}

// Fonction globale accessible depuis les popups Folium
window.sendToKPI = sendToKPI;

// Écouter les messages postMessage depuis les iframes Folium
window.addEventListener('message', function(event) {
  // Accepter les messages de n'importe quelle origine pour les popups Folium (data: URLs)
  if (event.data && event.data.action === 'sendToKPI') {
    console.log('📨 [KPI] Message reçu depuis popup:', event.data);
    sendToKPI(event.data.lat, event.data.lon, event.data.type, event.data.properties, null);
  }
});

// --------- SWITCH MAP ---------
function switchMap(target = "/static/map.html", onReady) {
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
    // Protection contre l'ajout multiple de listeners
    if (window.listenersAttached) {
        console.log('⚠️ Listeners déjà attachés, skip');
        return;
    }
    window.listenersAttached = true;
    
    console.log('🔧 [INIT] Attachement des event listeners');

    // ========== INJECTION GLOBALE DU LAYER CONTROL DARK-MODE ==========
    // À chaque chargement d'une carte dans l'iframe, on injecte le CSS + JS custom
    const mapIframe = document.getElementById('mapFrame');
    if (mapIframe) {
        mapIframe.addEventListener('load', function() {
            try {
                const iDoc = mapIframe.contentDocument || mapIframe.contentWindow?.document;
                if (!iDoc) return;
                
                // Vérifier qu'il y a un contrôle Leaflet dans la page
                // (sinon pas besoin d'injecter)
                setTimeout(function() {
                    try {
                        // Injecter le CSS s'il n'est pas déjà là
                        if (!iDoc.querySelector('link[href*="layer-control-dark"]')) {
                            var cssLink = iDoc.createElement('link');
                            cssLink.rel = 'stylesheet';
                            cssLink.href = '/static/css/layer-control-dark.css';
                            (iDoc.head || iDoc.documentElement).appendChild(cssLink);
                            console.log('[LC-INJECT] CSS injecté dans iframe');
                        }
                        // Injecter le JS s'il n'est pas déjà là
                        if (!iDoc.querySelector('script[src*="layer-control-dark"]')) {
                            var jsScript = iDoc.createElement('script');
                            jsScript.src = '/static/js/layer-control-dark.js?t=' + Date.now();
                            (iDoc.body || iDoc.documentElement).appendChild(jsScript);
                            console.log('[LC-INJECT] JS injecté dans iframe');
                        }
                    } catch(innerErr) {
                        console.log('[LC-INJECT] Erreur injection:', innerErr);
                    }
                }, 300); // Attendre 300ms que Leaflet finisse de s'initialiser
            } catch(e) {
                console.log('[LC-INJECT] Cannot access iframe:', e);
            }
        });
        console.log('✅ [INIT] Listener layer-control-dark attaché sur iframe');
    }
    // ==================================================================
    
    // Branche sliders si tu utilises
    setupSliders();
    
    // Branche formulaires
    document.getElementById("unifiedSearchForm")?.addEventListener("submit", handleUnifiedSearch);
    
    // FORMULAIRE COMMUNE : Protection maximale
    const communeForm = document.getElementById("communeSearchForm");
    if (communeForm) {
        // Retirer tout listener précédent (au cas où)
        communeForm.removeEventListener("submit", handleCommuneSearch);
        // Ajouter avec capture pour intercepter avant tout
        communeForm.addEventListener("submit", handleCommuneSearch, { capture: true });
        console.log('✅ [INIT] Listener commune attaché avec capture');
    }
    
    // Branche recherche départementale si tu as un bouton
    document.getElementById("deptSearchBtn")?.addEventListener("click", handleDeptSearch);
    // Branche boutons de rapport
    document.getElementById("reportButton")?.addEventListener("click", generateReport);
    document.getElementById("communeReportBtn")?.addEventListener("click", generateCommuneReport);
    document.getElementById("deptReportBtn")?.addEventListener("click", generateDeptReport);
    document.getElementById("deptReportCarteBtn")?.addEventListener("click", generateDeptReport);
    // Branche bouton save map si besoin
    // document.getElementById("saveMapBtn")?.addEventListener("click", () => saveCurrentMap("mon_export.html"));
    
    // 🚀 AUTO-SEARCH depuis URL (démo integration)
    const urlParams = new URLSearchParams(window.location.search);
    const searchQuery = urlParams.get('search');
    if (searchQuery && !window.autoSearchTriggered) {
        console.log('🔍 Auto-search détecté:', searchQuery);
        window.autoSearchTriggered = true; // Protection contre la boucle
        
        const addressInput = document.getElementById('search_input');
        if (addressInput) {
            addressInput.value = searchQuery;
            // Trigger search automatiquement après 500ms
            setTimeout(() => {
                console.log('🎯 Lancement auto-search pour:', searchQuery);
                const searchForm = document.getElementById('unifiedSearchForm');
                if (searchForm) {
                    searchForm.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
                }
            }, 500);
        }
    }
});
