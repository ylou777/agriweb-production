# 🔧 Correction Plan de Masse - Problème d'étirement et positionnement modules

## 🔍 Problèmes identifiés

### 1. Image satellite étirée
L'image satellite est déformée car le ratio width/height n'est pas respecté lors de l'affichage dans le PDF.

### 2. Modules aux mauvais emplacements
Les modules ne sont PAS repositionnés selon leurs coordonnées GPS sauvegardées. Le plan de masse affiche simplement une image figée de la carte Leaflet.

---

## 📊 Comment les coordonnées GPS sont sauvegardées

Lors de la sauvegarde du calpinage (`templates/calpinage_pv.html`), les données suivantes sont enregistrées :

### Pour chaque ZONE :
```javascript
{
    coordinates: [              // 🔥 Coordonnées GPS du polygone de la zone
        {lat: 48.123, lng: 2.456},
        {lat: 48.124, lng: 2.457},
        // ... tous les coins du polygone
    ],
    modulesPositions: [         // 🔥 Position GPS de CHAQUE module individuel
        {
            lat: 48.1235,       // Centre du module
            lng: 2.4565,
            corners: [          // Les 4 coins du module
                {lat: 48.1234, lng: 2.4564},
                {lat: 48.1236, lng: 2.4564},
                {lat: 48.1236, lng: 2.4566},
                {lat: 48.1234, lng: 2.4566}
            ]
        },
        // ... un objet par module
    ]
}
```

### Configuration du module :
```javascript
module: {
    longueur: "2278",  // mm
    largeur: "1134",   // mm
    puissance: "560",  // W
    // ...
}
```

### Image capturée :
```javascript
screenshot_map: "data:image/png;base64,iVBORw0KGgoAAAANS..."
```

---

## ✅ Solutions à implémenter

### Solution 1 : Utiliser l'image capturée SANS distorsion

**Fichier : `plan_masse_generator_v2.py` (lignes 133-157)**

✅ **Déjà corrigé** - L'image est affichée avec `preserveAspectRatio=True` et centrée.

**Vérifier aussi dans `calpinage_pv.html` :**
- Ligne 3549 : `scale: 1` (et PAS `scale: 2`) ✅ Déjà corrigé

---

### Solution 2 : Redessiner les modules depuis leurs coordonnées GPS

**Actuellement**, le code dessine les modules dans `_draw_modules_from_calpinage()` (ligne 450) mais utilise seulement les `coordinates` de la zone (le polygone), PAS les positions individuelles des modules.

**Il faut UTILISER `modulesPositions`** au lieu de recalculer une grille :

```python
def _draw_modules_from_calpinage(self, c):
    """Dessine les modules PV depuis leurs positions GPS EXACTES"""
    if not self.calpinage or 'zones' not in self.calpinage:
        return
    
    proj = self.projection
    
    for zone in self.calpinage['zones']:
        # 🔥 UTILISER modulesPositions si disponible
        modules_positions = zone.get('modulesPositions', [])
        
        if modules_positions:
            # Dessiner chaque module à sa position GPS exacte
            for mod in modules_positions:
                corners = mod.get('corners', [])
                if len(corners) >= 4:
                    # Dessiner le rectangle du module
                    path = c.beginPath()
                    first = True
                    
                    for corner in corners:
                        lat, lon = corner.get('lat'), corner.get('lng')
                        if lat and lon:
                            pdf_x, pdf_y = self._gps_to_pdf(lat, lon)
                            
                            if first:
                                path.moveTo(pdf_x, pdf_y)
                                first = False
                            else:
                                path.lineTo(pdf_x, pdf_y)
                    
                    path.close()
                    
                    # Remplissage bleu semi-transparent
                    c.setFillColor(colors.HexColor('#4285F4'), alpha=0.4)
                    c.setStrokeColor(colors.HexColor('#1976D2'))
                    c.setLineWidth(0.5)
                    c.drawPath(path, stroke=1, fill=1)
        else:
            # Fallback : utiliser l'ancien système (grille calculée)
            # ... code existant ...
```

---

### Solution 3 : Vérifier la projection GPS → PDF

**Fichier : `plan_masse_generator_v2.py` (lignes 252-276)**

La fonction `_gps_to_pdf()` utilise une projection Web Mercator simplifiée. Elle doit être cohérente avec :

1. **La bbox de l'image satellite** récupérée
2. **Le centre GPS** (latitude/longitude du prospect)
3. **L'échelle mètres/pixel**

**Vérification nécessaire :**

```python
def _draw_plan_cadastral(self, c):
    # ...
    
    # 🔥 STOCKER la projection pour _gps_to_pdf
    lat = self.data.get('latitude')
    lon = self.data.get('longitude')
    
    # Calculer l'échelle réelle de l'image affichée
    # L'image a des dimensions réelles (img_width x img_height en pixels)
    # Elle est affichée dans (new_width x new_height en points PDF)
    
    self.projection = {
        'lat_center': lat,
        'lon_center': lon,
        'plan_x': plan_x + offset_x,     # Position réelle dans le PDF
        'plan_y': plan_y + offset_y,
        'plan_width': new_width,         # Taille réelle affichée
        'plan_height': new_height,
        'meters_per_pixel_x': ???,       # 🔥 À CALCULER depuis la bbox
        'meters_per_pixel_y': ???
    }
```

**Le problème** : `meters_per_pixel_x/y` n'est pas calculé correctement car on ne connaît pas la bbox GPS de l'image capturée.

---

## 🎯 Solution COMPLÈTE recommandée

### Option A : Utiliser UNIQUEMENT l'image capturée (SIMPLE)

**Avantages :**
- Pas de conversion GPS → PDF nécessaire
- L'image contient DÉJÀ les modules au bon endroit
- Juste besoin de préserver le ratio

**À faire :**
1. ✅ Vérifier `scale: 1` dans html2canvas
2. ✅ Afficher l'image avec `preserveAspectRatio=True`
3. Ajouter UNIQUEMENT les overlays (parcelles cadastrales, légendes)

**Code actuel (lignes 133-157) :** ✅ Déjà correct !

---

### Option B : Redessiner TOUT depuis les coordonnées GPS (COMPLEXE)

**Avantages :**
- Contrôle total du rendu
- Possibilité d'ajouter des styles personnalisés
- Génération vectorielle (PDF scalable)

**À faire :**
1. Sauvegarder la **bbox GPS** de l'image lors de la capture
2. Calculer `meters_per_pixel_x/y` depuis cette bbox
3. Redessiner les modules depuis `modulesPositions`
4. Redessiner les équipements (onduleurs, TGBT, etc.)

**Modifications nécessaires :**

#### Dans `calpinage_pv.html` :
```javascript
async function captureMapScreenshot() {
    // ...
    
    // 🔥 AJOUTER : Récupérer la bbox GPS de la vue actuelle
    const bounds = map.getBounds();
    const mapBbox = {
        north: bounds.getNorth(),
        south: bounds.getSouth(),
        east: bounds.getEast(),
        west: bounds.getWest(),
        width_px: rect.width,
        height_px: rect.height
    };
    
    return {
        screenshot: canvas.toDataURL('image/png'),
        bbox: mapBbox  // 🔥 Ajouter la bbox
    };
}

// Modifier la sauvegarde :
data.screenshot_map = await captureMapScreenshot();
// Au lieu de : data.screenshot_map = screenshot_string
```

#### Dans `plan_masse_generator_v2.py` :
```python
def _get_calpinage_screenshot(self):
    """Récupère l'image ET sa bbox GPS"""
    if not self.calpinage:
        return None, None
    
    screenshot_data = self.calpinage.get('screenshot_map')
    
    if isinstance(screenshot_data, dict):
        # Nouveau format avec bbox
        return screenshot_data.get('screenshot'), screenshot_data.get('bbox')
    else:
        # Ancien format (juste l'image)
        return screenshot_data, None

def _draw_plan_cadastral(self, c):
    # ...
    
    calpinage_image, map_bbox = self._get_calpinage_screenshot()
    
    if map_bbox:
        # 🔥 Calculer l'échelle réelle
        # Largeur en degrés GPS
        width_deg = map_bbox['east'] - map_bbox['west']
        
        # Conversion en mètres (approximation)
        lat_center = (map_bbox['north'] + map_bbox['south']) / 2
        meters_per_deg_lon = 111000 * math.cos(math.radians(lat_center))
        width_meters = width_deg * meters_per_deg_lon
        
        # Échelle mètres/pixel de l'image ORIGINALE
        meters_per_px_orig_x = width_meters / map_bbox['width_px']
        
        # Échelle mètres/pixel dans le PDF affiché
        # new_width points PDF = width_meters mètres
        meters_per_px_pdf_x = width_meters / new_width
        
        self.projection = {
            'lat_center': lat,
            'lon_center': lon,
            'plan_x': plan_x + offset_x,
            'plan_y': plan_y + offset_y,
            'plan_width': new_width,
            'plan_height': new_height,
            'meters_per_pixel_x': meters_per_px_pdf_x,
            'meters_per_pixel_y': meters_per_px_pdf_y,
            'bbox': map_bbox
        }
```

---

## 🚀 Action immédiate recommandée

### Si l'image est déjà correcte mais étirée :

**VÉRIFIER** dans `calpinage_pv.html` ligne 3549 :
```javascript
scale: 1,  // Doit être 1, PAS 2
```

**TESTER** la génération du plan de masse. Si l'image s'affiche correctement maintenant, le problème est résolu !

---

### Si les modules sont décalés PAR RAPPORT à l'image :

C'est que l'image satellite et les modules sont dessinés avec **2 systèmes de projection différents**.

**Solution :**
- Utiliser UNIQUEMENT l'image capturée (qui contient déjà les modules)
- NE PAS redessiner les modules par-dessus

**Dans `plan_masse_generator_v2.py`, COMMENTER les lignes qui redessinent les modules :**

```python
def _draw_plan_cadastral(self, c):
    # ... affichage de l'image ...
    
    # NE PAS redessiner les modules si l'image les contient déjà
    # self._draw_modules_from_calpinage(c)  # ❌ COMMENTER
    
    # Afficher SEULEMENT les overlays (parcelles, légendes)
    self._draw_parcelles_overlay(c, plan_x, plan_y, plan_width, plan_height)
```

---

## 📝 Résumé

| Donnée | Où elle est sauvegardée | Comment l'utiliser |
|--------|------------------------|-------------------|
| **Image satellite + modules** | `screenshot_map` (base64) | Afficher avec `preserveAspectRatio=True` |
| **Coordonnées zone** | `coordinates[]` | Dessiner le contour de la zone |
| **Position modules** | `modulesPositions[]` | Redessiner chaque module individuellement |
| **Bbox GPS de l'image** | ❌ **PAS sauvegardée** | 🔥 À ajouter pour calcul précis |

**Recommandation :** Utiliser l'image capturée telle quelle (Option A) pour une solution rapide et fiable.
