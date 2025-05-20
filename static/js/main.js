// static/js/main.js

// ---------------------------
// 1) FONCTIONS UTILITAIRES
// ---------------------------
function parseGeoJSONPoint(str) {
  try {
    const obj = JSON.parse(str);
    if (obj.type === "Point" && Array.isArray(obj.coordinates) && obj.coordinates.length === 2) {
      return { lat: obj.coordinates[1], lon: obj.coordinates[0] };
    }
  } catch {}
  return null;
}

function parseLonLat(str) {
  const parts = str.split(',');
  if (parts.length !== 2) return null;
  const lon = parseFloat(parts[0]), lat = parseFloat(parts[1]);
  if (isNaN(lat) || isNaN(lon)) return null;
  return { lat, lon };
}

function addGeoJsonToIframe(geojson, style) {
  const frame = document.getElementById('mapFrame');
  if (frame?.contentWindow?.addGeoJsonToMap) {
    frame.contentWindow.addGeoJsonToMap(geojson, style);
  }
}

function reloadMap() {
  const frame = document.getElementById('mapFrame');
  frame.src = `/map.html?cb=${Date.now()}`;
}

// ---------------------------
// 2) PANNEAU D’INFO (unifié)
// ---------------------------
function updateInfoPanel(data) {
  let html = `
    <div class="card mb-3">
      <div class="card-header bg-primary text-white">Coordonnées</div>
      <div class="card-body">
        <p><strong>Lat :</strong> ${data.lat ?? 'N/A'}</p>
        <p><strong>Lon :</strong> ${data.lon ?? 'N/A'}</p>
        ${data.address ? `<p><strong>Adresse :</strong> ${data.address}</p>` : ''}
      </div>
    </div>`;

  // Parcelle cadastrale
  if (data.parcelle?.geometry) {
    const p = data.parcelle;
    html += `
      <div class="card mb-3">
        <div class="card-header bg-secondary text-white">Parcelle cadastrale</div>
        <div class="card-body">
          ${Object.entries(p)
            .filter(([k]) => k !== 'geometry')
            .map(([k, v]) => `<p><strong>${k} :</strong> ${v}</p>`)
            .join('')}
        </div>
      </div>`;
    addGeoJsonToIframe(p.geometry, { color: '#00F', weight: 2, opacity: 0.7 });
  }

  // Postes BT
  if (data.postes_bt && data.postes_bt.length) {
    html += `<div class="card mb-3">
      <div class="card-header bg-info text-white">Postes BT</div>
      <ul class="list-group list-group-flush">` +
      data.postes_bt.map((poste, i) =>
        `<li class="list-group-item">
           <strong>#${i+1}</strong> — ${poste.properties.distance} m<br>` +
           Object.entries(poste.properties)
             .map(([k,v]) => `${k}: ${v}`)
             .join('<br>')
        + `</li>`
      ).join('') +
    `</ul></div>`;
  }

  // Postes HTA
  if (data.postes_hta && data.postes_hta.length) {
    html += `<div class="card mb-3">
      <div class="card-header bg-warning text-dark">Postes HTA</div>
      <ul class="list-group list-group-flush">` +
      data.postes_hta.map((poste, i) =>
        `<li class="list-group-item">
           <strong>#${i+1}</strong> — ${poste.properties.distance} m<br>` +
           Object.entries(poste.properties)
             .map(([k,v]) => `${k}: ${v}`)
             .join('<br>')
        + `</li>`
      ).join('') +
    `</ul></div>`;
  }

  // Parcelles RPG
  if (data.rpg && data.rpg.length) {
    html += `<div class="card mb-3">
      <div class="card-header bg-dark text-white">Parcelles RPG</div>
      <ul class="list-group list-group-flush">` +
      data.rpg.map((f, i) =>
        `<li class="list-group-item">
           <strong>#${i+1}</strong><br>` +
           Object.entries(f.properties)
             .map(([k,v]) => `${k}: ${v}`)
             .join('<br>')
        + `</li>`
      ).join('') +
    `</ul></div>`;
    data.rpg.forEach(feat => {
      if (feat.geometry) addGeoJsonToIframe(feat.geometry, { color:'#800080', weight:2, fillOpacity:0.3 });
    });
  }

  // Éleveurs
  if (data.eleveurs && data.eleveurs.length) {
    html += `<div class="card mb-3">
      <div class="card-header bg-danger text-white">Éleveurs</div>
      <ul class="list-group list-group-flush">` +
      data.eleveurs.map((e, i) => {
        const props = e.properties || {};
        // adresse complète
        const street = [props.numeroVoie, props.typeVoieEt, props.libelleVoi].filter(Boolean).join(' ');
        const city   = [props.codePostal, props.libelleCom].filter(Boolean).join(' ');
        return `<li class="list-group-item">
          <strong>#${i+1}</strong><br>
          <strong>SIRET :</strong> ${props.siret || 'N/A'}<br>
          <strong>Dénomination :</strong> ${props.denominati || 'N/A'}<br>
          <strong>Nom :</strong> ${props.nomUniteLe || 'N/A'}<br>
          <strong>Prénom :</strong> ${props.prenom1Uni || 'N/A'}<br>
          <strong>Adresse :</strong> ${street}<br>${city}<br>
          <strong>Activité :</strong> ${props.activite_1 || props.activitePr || 'N/A'}
        </li>`;
      }).join('') +
    `</ul></div>`;
  }

  document.getElementById('info-panel').innerHTML = html;
}

// ---------------------------
// 3) INITIALISATION CARTE SSE
// ---------------------------
let sseMap,
    deptLayer, markersLayer, polysLayer,
    btLayer, htaLayer,
    cadastreLayer, natureLayer, urbanismeLayer,
    pluLayer, parkingsLayer, frichesLayer,
    solaireLayer, zaerLayer;

function clearSSEMap() {
  [deptLayer, markersLayer, polysLayer, btLayer, htaLayer,
   cadastreLayer, natureLayer, urbanismeLayer,
   pluLayer, parkingsLayer, frichesLayer,
   solaireLayer, zaerLayer].forEach(l => l.clearLayers());
}

// ---------------------------
// 4) MISE EN PLACE DES HANDLERS
// ---------------------------
document.addEventListener('DOMContentLoaded', () => {
  // --- a) initialisation map SSE avec deux fonds ---
  const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OSM' });
  const satellite = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { attribution: 'Esri Satellite' }
  );

  sseMap = L.map('mapSSE', {
    center: [46.6, 1.9],
    zoom: 6,
    layers: [satellite]
  });

  // création des calques
  deptLayer     = L.geoJSON(null, { style:{ color:'#ff7800', weight:2 } }).addTo(sseMap);
  markersLayer  = L.layerGroup().addTo(sseMap);
  polysLayer    = L.layerGroup().addTo(sseMap);
  btLayer       = L.layerGroup().addTo(sseMap);
  htaLayer      = L.layerGroup().addTo(sseMap);
  cadastreLayer = L.layerGroup().addTo(sseMap);
  natureLayer   = L.layerGroup().addTo(sseMap);
  urbanismeLayer= L.layerGroup().addTo(sseMap);
  pluLayer      = L.layerGroup().addTo(sseMap);
  parkingsLayer = L.layerGroup().addTo(sseMap);
  frichesLayer  = L.layerGroup().addTo(sseMap);
  solaireLayer  = L.layerGroup().addTo(sseMap);
  zaerLayer     = L.layerGroup().addTo(sseMap);

  // contrôle de calques
  L.control.layers(
    { "Satellite": satellite, "OSM": osm },
    {
      "Limite Dept.":   deptLayer,
      "Éleveurs":       markersLayer,
      "Parcelles RPG":  polysLayer,
      "Postes BT":      btLayer,
      "Postes HTA":     htaLayer,
      "Cadastre":       cadastreLayer,
      "Nature":         natureLayer,
      "Urbanisme":      urbanismeLayer,
      "PLU":            pluLayer,
      "Parkings":       parkingsLayer,
      "Friches":        frichesLayer,
      "Solaire":        solaireLayer,
      "ZAER":           zaerLayer
    }
  ).addTo(sseMap);

  document.querySelectorAll('input[type=range]').forEach(slider => {
    const out = document.getElementById(slider.id + '_val');
    if (!out) return;
    out.textContent = slider.value + ' km';
    slider.addEventListener('input', () => {
      out.textContent = slider.value + ' km';
    });
  });

  // --- mode de recherche dynamique ---
  function updateSearchMode() {
    const mode = document.querySelector('input[name="search_mode"]:checked').value;
    document.getElementById('form_address').style.display = mode === 'address' ? 'block' : 'none';
    document.getElementById('form_commune').style.display = mode === 'commune' ? 'block' : 'none';
    document.getElementById('form_dept').style.display    = mode === 'department' ? 'block' : 'none';
    document.getElementById('ssePanel').style.display      = mode === 'department' ? 'block' : 'none';
  }
  document.querySelectorAll('.search-mode').forEach(el => el.addEventListener('change', updateSearchMode));
  updateSearchMode();

  // --- c) recherche unifiée (adresse / coordonnées) ---
  document.getElementById('unifiedSearchForm').addEventListener('submit', e => {
    e.preventDefault();
    const str = document.getElementById('search_input').value.trim();
    let lat, lon;
    const geo = parseGeoJSONPoint(str);
    if (geo) { lat = geo.lat; lon = geo.lon; }
    else {
      const c = parseLonLat(str);
      if (c) { lat = c.lat; lon = c.lon; }
    }
    const qs = (lat !== undefined)
      ? `lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`
      : `address=${encodeURIComponent(str)}`;
    const fullQs = [
      qs,
      `sirene_radius=${encodeURIComponent(document.getElementById('sirene_radius').value)}`,
      `ht_radius=${encodeURIComponent(document.getElementById('ht_radius').value)}`,
      `bt_radius=${encodeURIComponent(document.getElementById('bt_radius').value)}`
    ].join('&');

    fetch(`/search_by_address?${fullQs}`)
      .then(r => r.json())
      .then(d => {
        if (d.error) return alert(d.error);
        updateInfoPanel(d);
        reloadMap();
      })
      .catch(console.error);
  });

  // --- d) recherche par commune simple (sans SSE) ---
  document.getElementById('communeSearchButton').addEventListener('click', () => {
    const commune = document.getElementById('commune').value.trim();
    if (!commune) return alert('Entrez une commune');
    const params = new URLSearchParams({
      commune:          commune,
      culture:          document.getElementById('culture').value || '',
      min_area_ha:      document.getElementById('min_surface').value || 0,
      max_area_ha:      document.getElementById('max_surface').value || '',
      ht_max_distance:  document.getElementById('ht_max_distance').value,
      bt_max_distance:  document.getElementById('bt_max_distance').value,
      sirene_radius:    document.getElementById('sirene_radius_commune').value
    });

    fetch(`/search_by_commune?${params}`)
      .then(r => r.json())
      .then(d => {
        if (d.error) return alert(d.error);
        document.querySelector('#resultsTable tbody').innerHTML = `
          <tr>
            <td>${commune}</td>
            <td>${d.rpg.length}</td>
            <td>${d.eleveurs.length}</td>
          </tr>`;
        document.getElementById('totalEleveurs').textContent = d.eleveurs.length;
        reloadMap();
      })
      .catch(console.error);
  });

  // --- e) recherche par département via SSE ---
  document.getElementById('deptSearchButton').addEventListener('click', () => {
    const code = document.getElementById('dept_input').value.trim();
    if (!/^\d{2}$/.test(code)) return alert('Code département invalide.');

    clearSSEMap();
    document.querySelector('#resultsTable tbody').innerHTML = '';
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('progressBar').textContent = '0%';
    document.getElementById('totalEleveurs').textContent = '0';
    document.getElementById('log').textContent = '';

    // tracer la limite
    fetch(`https://geo.api.gouv.fr/departements/${code}?fields=contour`)
      .then(r => r.json())
      .then(d => {
        deptLayer.addData(d.contour);
        sseMap.fitBounds(deptLayer.getBounds());
      })
      .catch(console.error);

    const params = new URLSearchParams({
      department:       code,
      culture:          document.getElementById('culture').value || '',
      min_area_ha:      document.getElementById('min_surface').value || 0,
      max_area_ha:      document.getElementById('max_surface').value || '',
      ht_max_distance:  document.getElementById('ht_max_distance').value,
      bt_max_distance:  document.getElementById('bt_max_distance').value,
      sirene_radius:    document.getElementById('sirene_radius_commune').value,
      want_eleveurs:    'true'
    });

    const es = new EventSource(`/generate_reports_by_dept_sse?${params}`);
    es.addEventListener('progress', e => {
      const msg = e.data;
      document.getElementById('log').textContent = msg;
      const m = msg.match(/\[(\d+)\/(\d+)\]/);
      if (m) {
        const pct = Math.round((+m[1]) / (+m[2]) * 100);
        document.getElementById('progressBar').style.width = pct + '%';
        document.getElementById('progressBar').textContent = pct + '%';
      }
    });

    es.addEventListener('result', e => {
      const res = JSON.parse(e.data);

      // tableau SSE
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${res.commune}</td>
        <td>${res.rpg.length}</td>
        <td>${res.eleveurs.length}</td>`;
      document.querySelector('#resultsTable tbody').appendChild(tr);
      document.getElementById('totalEleveurs').textContent =
        +document.getElementById('totalEleveurs').textContent + res.eleveurs.length;

      // Éleveurs
      res.eleveurs.forEach(feat => {
        const p = feat.properties || {};
        const street = [p.numeroVoie,p.typeVoieEt,p.libelleVoi].filter(Boolean).join(' ');
        const city   = [p.codePostal,p.libelleCom].filter(Boolean).join(' ');
        const htmlP = `
          <strong>SIRET :</strong> ${p.siret || 'N/A'}<br>
          <strong>Dénomination :</strong> ${p.denominati || 'N/A'}<br>
          <strong>Nom :</strong> ${p.nomUniteLe || 'N/A'}<br>
          <strong>Prénom :</strong> ${p.prenom1Uni || 'N/A'}<br>
          <strong>Adresse :</strong> ${street}<br>${city}<br>
          <strong>Activité :</strong> ${p.activite_1||p.activitePr||'N/A'}`;
        L.geoJSON(feat, {
          pointToLayer: (_,latlng) => L.circleMarker(latlng,{radius:5,color:'red',fillOpacity:0.7})
        }).bindPopup(htmlP).addTo(markersLayer);
      });

      // Parcelles RPG
      res.rpg.forEach(f => {
        L.geoJSON(f, { style:{ color:'#800080', weight:2, fillOpacity:0.3 }})
         .bindPopup(Object.entries(f.properties).map(([k,v])=>`${k}: ${v}`).join('<br>'))
         .addTo(polysLayer);
      });

      // Postes BT & HTA
      res.postes_bt.forEach(p => {
        L.geoJSON(p, {
          pointToLayer: (_,latlng) => L.circleMarker(latlng,{radius:6,color:'green',fillOpacity:0.8})
        }).bindPopup(`Poste BT — ${p.properties.distance} m`).addTo(btLayer);
      });
      res.postes_hta.forEach(p => {
        L.geoJSON(p, {
          pointToLayer: (_,latlng) => L.circleMarker(latlng,{radius:6,color:'orange',fillOpacity:0.8})
        }).bindPopup(`Poste HTA — ${p.properties.distance} m`).addTo(htaLayer);
      });

      // Parcelles cadastrales
      if (res.parcelles?.features) {
        L.geoJSON(res.parcelles, { style:{ color:'#663399',weight:1,fillOpacity:0.1 }})
         .addTo(cadastreLayer);
      }

      // API Cadastre & Nature
      if (res.api_cadastre?.features) {
        L.geoJSON(res.api_cadastre, { style:{ color:'#FF5500',weight:2 }})
         .addTo(cadastreLayer);
      }
      if (res.api_nature?.features) {
        L.geoJSON(res.api_nature, { style:{ color:'#22AA22',weight:2 }})
         .addTo(natureLayer);
      }

      // Urbanisme GPU
      Object.entries(res.api_urbanisme||{}).forEach(([type,fc])=>{
        if (fc?.features) {
          L.geoJSON(fc, { style:_=>({ weight:1, color:'#0000FF', opacity:0.3 })})
           .bindPopup(`<strong>${type}</strong>`)
           .addTo(urbanismeLayer);
        }
      });

      // PLU, parkings, friches, solaire, zaer
      ;[ ['plu',pluLayer], ['parkings',parkingsLayer],
         ['friches',frichesLayer], ['solaire',solaireLayer],
         ['zaer',zaerLayer] ]
      .forEach(([key,layer])=>{
        (res[key]||[]).forEach(feat=>{
          L.geoJSON(feat).addTo(layer);
        });
      });
    });

    es.addEventListener('end', e => {
      document.getElementById('log').textContent = e.data;
      es.close();
    });
    es.addEventListener('error', e => {
      document.getElementById('log').textContent = '❌ Erreur SSE';
      es.close();
    });
  });
});
