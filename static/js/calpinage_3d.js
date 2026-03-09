/**
 * Calpinage 3D Viewer — LiDAR + BD TOPO + OSM
 * 
 * Visualisation 3D réaliste utilisant :
 * - LiDAR IGN (MNS/MNT) pour le relief terrain réel
 * - BD TOPO IGN pour les bâtiments avec hauteur réelle
 * - OSM pour les emprises bâtiments complémentaires
 * - Satellite IGN pour la texture sol
 * - Three.js + OrbitControls
 */

class Calpinage3DViewer {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.isActive = false;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.animationId = null;
        this.ground = null;
        this.buildings = [];
        this.modules3D = [];
        this.roads = [];
        this.vegetation = [];
        this.sunLight = null;
        this.lidarData = null;
        this.terrainMesh = null;
        this.loadingOverlay = null;
        
        // Conversion constants
        this.LAT_TO_M = 111320;
        this.centerLat = 0;
        this.centerLon = 0;
        this.LNG_TO_M = 0;
        
        // Cache de textures procédurales
        this._textureCache = {};
        
        // Informations sur les pans de toiture du bâtiment principal
        this.roofPanelsInfo = null;
        
        // Coordonnées géo du bâtiment PV principal (pour matching zone→pan)
        this.pvBuildingCoords = null;
        
        console.log('✅ Calpinage3DViewer créé pour:', containerId);
    }
    
    /**
     * Active/désactive la vue 3D
     */
    toggle() {
        if (this.isActive) {
            this.dispose();
            this.isActive = false;
        } else {
            this.init();
            this.isActive = true;
        }
    }
    
    /**
     * Initialise la scène Three.js
     */
    init() {
        if (!this.container) {
            console.error('❌ Container 3D introuvable:', this.containerId);
            return;
        }
        
        const w = this.container.clientWidth || 800;
        const h = this.container.clientHeight || 600;
        
        // Scène
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x87CEEB); // Ciel bleu
        this.scene.fog = new THREE.FogExp2(0x87CEEB, 0.002);
        
        // Caméra
        this.camera = new THREE.PerspectiveCamera(55, w / h, 0.5, 2000);
        this.camera.position.set(60, 80, 60);
        this.camera.lookAt(0, 0, 0);
        
        // Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setSize(w, h);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.outputEncoding = THREE.sRGBEncoding;
        this.container.appendChild(this.renderer.domElement);
        
        // Contrôles orbitaux
        if (THREE.OrbitControls) {
            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.08;
            this.controls.maxPolarAngle = Math.PI / 2.05;
            this.controls.minDistance = 10;
            this.controls.maxDistance = 500;
            this.controls.target.set(0, 5, 0);
        }
        
        // Éclairage
        this._setupLighting();
        
        // Sol temporaire (sera remplacé par le terrain LiDAR)
        this._createDefaultGround();
        
        // Resize handler
        this._resizeHandler = () => this._onResize();
        window.addEventListener('resize', this._resizeHandler);
        
        // Boucle de rendu
        this._animate();
        
        console.log('✅ Scène 3D initialisée');
    }
    
    /**
     * Configure l'éclairage réaliste
     */
    _setupLighting() {
        // Lumière ambiante douce
        const ambient = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambient);
        
        // Lumière hémisphérique (ciel bleu / sol vert)
        const hemi = new THREE.HemisphereLight(0x87CEEB, 0x556B2F, 0.3);
        this.scene.add(hemi);
        
        // Soleil directionnel avec ombres
        this.sunLight = new THREE.DirectionalLight(0xfff5e0, 0.9);
        this.sunLight.position.set(50, 80, 30);
        this.sunLight.castShadow = true;
        this.sunLight.shadow.mapSize.width = 2048;
        this.sunLight.shadow.mapSize.height = 2048;
        this.sunLight.shadow.camera.near = 0.5;
        this.sunLight.shadow.camera.far = 300;
        this.sunLight.shadow.camera.left = -100;
        this.sunLight.shadow.camera.right = 100;
        this.sunLight.shadow.camera.top = 100;
        this.sunLight.shadow.camera.bottom = -100;
        this.sunLight.shadow.bias = -0.001;
        this.scene.add(this.sunLight);
    }
    
    /**
     * Sol par défaut (plat, avant chargement LiDAR)
     */
    _createDefaultGround() {
        const groundGeo = new THREE.PlaneGeometry(200, 200);
        const groundMat = new THREE.MeshLambertMaterial({ color: 0x4a7c3f });
        this.ground = new THREE.Mesh(groundGeo, groundMat);
        this.ground.rotation.x = -Math.PI / 2;
        this.ground.receiveShadow = true;
        this.scene.add(this.ground);
    }
    
    /**
     * Charge les données LiDAR 3D depuis l'API et construit la scène
     */
    async loadLidarData(lat, lon, radius) {
        this.centerLat = lat;
        this.centerLon = lon;
        this.LNG_TO_M = this.LAT_TO_M * Math.cos(lat * Math.PI / 180);
        
        this._showLoading('Chargement LiDAR + BD TOPO...');
        
        try {
            const url = `/api/lidar/3d-data?lat=${lat}&lon=${lon}&radius=${radius || 100}`;
            console.log('📡 Chargement données 3D:', url);
            
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            this.lidarData = await response.json();
            console.log('✅ Données 3D reçues:', {
                terrain: !!this.lidarData.terrain,
                terrainInfo: this.lidarData.terrain ? {
                    gridSize: this.lidarData.terrain.grid_size,
                    altBase: this.lidarData.terrain.altitude_base,
                    mntRange: `${this.lidarData.terrain.mnt_min}-${this.lidarData.terrain.mnt_max}m`,
                    mnhMax: this.lidarData.terrain.mnh_max + 'm'
                } : 'N/A',
                bdtopo: this.lidarData.buildings_bdtopo?.length || 0,
                osm: this.lidarData.buildings_osm?.length || 0,
                roads: this.lidarData.roads?.length || 0,
                vegetation: this.lidarData.vegetation?.length || 0
            });
            
            if (this.lidarData.buildings_bdtopo?.length > 0) {
                const b0 = this.lidarData.buildings_bdtopo[0];
                console.log('🏠 Premier bâtiment BD TOPO:', {
                    hauteur: b0.hauteur,
                    usage: b0.usage,
                    nature: b0.nature,
                    coords: b0.coords?.length + ' points',
                    firstCoord: b0.coords?.[0]
                });
            }
            
            // ✅ Les plans RANSAC building_hd sont conservés — utilisés directement pour le toit

            // Construire la scène 3D
            if (this.lidarData.terrain) {
                this._buildTerrainMesh(this.lidarData.terrain, radius || 100);
            }
            
            // Charger la texture satellite
            await this._loadSatelliteTexture(lat, lon, radius || 100);
            
            // Lancer l'analyse IA du type de toiture EN PARALLÈLE
            // (ne bloque pas la construction 3D — le résultat arrive après)
            this.aiRoofPromise = this._fetchAIRoofType(lat, lon);
            
            // Construire les bâtiments
            await this._buildBuildings(this.lidarData);

            // Toit PV : uniquement via COPC LAZ brut (~15-35s).
            // Si COPC échoue, fallback sur les plans MNH stockés dans lidarData.
            if ((this.pvBuildingCoords?.length ?? 0) >= 3) {
                this._fetchAndApplyCOPCRoof(lat, lon).catch(e => {
                    console.warn('⚠️ COPC (non critique):', e.message);
                    // Supprimer le toit MNH initial avant d'ajouter le fallback
                    this._removePVRoofMeshes();
                    // Fallback MNH : construire le toit depuis les plans RANSAC initiaux
                    const _fd = this.lidarData?.building_hd;
                    if (_fd?.roof_planes?.length) {
                        const _bc = _fd.building_center;
                        const _bh = this._mainBldgBh      ?? 6;
                        const _th = this._mainBldgTerrainH ?? 0;
                        const _rt = this._mainBldgRoofType ?? 'default';
                        if (!this._buildRoofHeightField(_fd.roof_planes, _bc, _bh, _th, this.pvBuildingCoords, _rt, true)) {
                            this._buildRoofFromPlanes(_fd.roof_planes, _bc, _bh, _th, _rt, true);
                        }
                    }
                });
            }

            // Construire les routes
            this._buildRoads(this.lidarData);
            
            // Construire la végétation
            this._buildVegetation(this.lidarData);
            
            // Ajuster la caméra
            this._fitCamera(radius || 100);
            
            this._hideLoading();
            
        } catch (error) {
            console.error('❌ Erreur chargement 3D:', error);
            this._hideLoading();
            this._showError('Erreur chargement données 3D: ' + error.message);
        }
    }
    
    /**
     * Appel IA pour classifier le type de toiture via image satellite
     * Retourne une Promise avec {roof_type, nb_pans, confidence, ridge_direction}
     */
    async _fetchAIRoofType(lat, lon) {
        try {
            const url = `/api/ai/roof-type?lat=${lat}&lon=${lon}`;
            console.log('🤖 Lancement analyse IA du toit...');
            const response = await fetch(url, { signal: AbortSignal.timeout(20000) });
            if (!response.ok) {
                console.warn(`🤖 AI Roof: HTTP ${response.status}`);
                return null;
            }
            const data = await response.json();
            if (data.success && data.confidence >= 0.5) {
                console.log(`🤖 AI Roof: ${data.roof_type} (${data.nb_pans} pans, conf=${data.confidence}, dir=${data.ridge_direction}) — ${data.details}`);
                return data;
            } else {
                console.warn(`🤖 AI Roof: confiance insuffisante ou échec`, data);
                return null;
            }
        } catch (err) {
            console.warn('🤖 AI Roof timeout/erreur:', err.message);
            return null;
        }
    }
    
    /**
     * Construit le mesh terrain à partir du MNT LiDAR
     */
    _buildTerrainMesh(terrain, radiusM) {
        // Supprimer l'ancien sol
        if (this.ground) {
            this.scene.remove(this.ground);
            this.ground.geometry.dispose();
            this.ground.material.dispose();
        }
        if (this.terrainMesh) {
            this.scene.remove(this.terrainMesh);
            this.terrainMesh.geometry.dispose();
            this.terrainMesh.material.dispose();
        }
        
        const gridSize = terrain.grid_size;
        const mnt = terrain.mnt; // Grille 2D altitudes relatives
        
        console.log(`🗺️ Terrain: gridSize=${gridSize}, radiusM=${radiusM}`);
        console.log(`🗺️ MNT range: min=${terrain.mnt_min}m, max=${terrain.mnt_max}m, delta=${(terrain.mnt_max - terrain.mnt_min).toFixed(1)}m`);
        
        // Exagération verticale pour rendre le relief visible
        const altDelta = terrain.mnt_max - terrain.mnt_min;
        // Exagération modérée pour réalisme — trop d'exagération crée des escaliers
        // et des bâtiments flottants
        let verticalExaggeration;
        if (radiusM <= 40) {
            verticalExaggeration = altDelta < 2 ? 1.5 : (altDelta < 5 ? 1.2 : 1.0);
        } else if (radiusM <= 80) {
            verticalExaggeration = altDelta < 3 ? 1.8 : (altDelta < 10 ? 1.3 : 1.0);
        } else {
            verticalExaggeration = altDelta < 5 ? 2.5 : (altDelta < 15 ? 1.8 : 1.2);
        }
        this._verticalExaggeration = verticalExaggeration;
        console.log(`🗺️ Exagération verticale: x${verticalExaggeration} (delta=${altDelta.toFixed(1)}m)`);
        
        // ═══════════════════════════════════════════════════════════
        // TERRAIN SUBDIVISÉ : interpolation bilinéaire pour éliminer
        // l'effet d'escalier dans la couche satellite
        // ═══════════════════════════════════════════════════════════
        // Limiter meshRes pour éviter RangeError sur grandes grilles
        // Three.js r128 utilise des indices 16-bit (max 65535 vertices)
        // → max 255 segments (256² = 65536), on prend 200 pour marge
        const maxMeshRes = 200;
        const subdivFactor = 3;
        const meshRes = Math.min((gridSize - 1) * subdivFactor, maxMeshRes);
        const meshVerts = meshRes + 1;                  // nombre de vertices par axe
        
        const geo = new THREE.PlaneGeometry(
            radiusM * 2, radiusM * 2,
            meshRes, meshRes
        );
        
        // Fonction d'interpolation bilinéaire sur la grille MNT
        const sampleMNT = (fx, fy) => {
            // fx, fy en coordonnées continues de grille [0, gridSize-1]
            const x0 = Math.max(0, Math.min(gridSize - 2, Math.floor(fx)));
            const y0 = Math.max(0, Math.min(gridSize - 2, Math.floor(fy)));
            const x1 = x0 + 1;
            const y1 = y0 + 1;
            const tx = fx - x0;
            const ty = fy - y0;
            
            const v00 = mnt[y0] ? (mnt[y0][x0] || 0) : 0;
            const v10 = mnt[y0] ? (mnt[y0][x1] || 0) : 0;
            const v01 = mnt[y1] ? (mnt[y1][x0] || 0) : 0;
            const v11 = mnt[y1] ? (mnt[y1][x1] || 0) : 0;
            
            return v00 * (1 - tx) * (1 - ty) + v10 * tx * (1 - ty)
                 + v01 * (1 - tx) * ty       + v11 * tx * ty;
        };
        this._sampleMNTBilinear = sampleMNT; // stocker pour _getTerrainHeight
        
        // Appliquer les altitudes interpolées
        const positions = geo.attributes.position.array;
        let maxZ = 0;
        let minZ = Infinity;
        let nonZeroCount = 0;
        
        for (let iy = 0; iy < meshVerts; iy++) {
            for (let ix = 0; ix < meshVerts; ix++) {
                const idx = (iy * meshVerts + ix) * 3;
                // Coordonnées continues dans la grille MNT
                const gx = ix / meshRes * (gridSize - 1);
                const gy = iy / meshRes * (gridSize - 1);
                const altitude = sampleMNT(gx, gy);
                const exaggeratedAlt = altitude * verticalExaggeration;
                positions[idx + 2] = exaggeratedAlt;
                if (exaggeratedAlt > maxZ) maxZ = exaggeratedAlt;
                if (exaggeratedAlt < minZ) minZ = exaggeratedAlt;
                if (altitude !== 0) nonZeroCount++;
            }
        }
        
        geo.attributes.position.needsUpdate = true;
        geo.computeVertexNormals();
        
        console.log(`🗺️ Terrain: ${meshVerts}x${meshVerts} vertices (MNT ${gridSize}x${gridSize}, subdiv x${subdivFactor}), Z range: ${minZ.toFixed(1)} - ${maxZ.toFixed(1)}m`);
        
        // Matériau terrain
        const mat = new THREE.MeshLambertMaterial({
            color: 0x5a8f4a,
            wireframe: false,
            side: THREE.DoubleSide
        });
        
        this.terrainMesh = new THREE.Mesh(geo, mat);
        this.terrainMesh.rotation.x = -Math.PI / 2;
        this.terrainMesh.receiveShadow = true;
        this.terrainMesh.castShadow = false;
        this.scene.add(this.terrainMesh);
        
        // Sol secondaire plus grand pour l'environnement
        const bigGroundGeo = new THREE.PlaneGeometry(600, 600);
        const bigGroundMat = new THREE.MeshLambertMaterial({ color: 0x4a7c3f });
        this.ground = new THREE.Mesh(bigGroundGeo, bigGroundMat);
        this.ground.rotation.x = -Math.PI / 2;
        this.ground.position.y = -0.5;
        this.ground.receiveShadow = true;
        this.scene.add(this.ground);
        
        console.log(`✅ Terrain LiDAR: MNT ${gridSize}x${gridSize} → mesh ${meshVerts}x${meshVerts}, exagération x${verticalExaggeration}`);
    }
    
    /**
     * Charge la texture satellite IGN sur le terrain (via proxy serveur pour CORS)
     */
    async _loadSatelliteTexture(lat, lon, radiusM) {
        try {
            // Demander une image satellite couvrant exactement le même rayon que le terrain
            // pour un alignement pixel-parfait avec les bâtiments
            const satRadius = Math.ceil(radiusM);
            const proxyUrl = `/api/satellite-tile?lat=${lat}&lon=${lon}&radius=${satRadius}`;
            console.log('🛰️ Chargement texture satellite via proxy:', proxyUrl);
            
            const response = await fetch(proxyUrl);
            if (!response.ok) {
                console.warn(`⚠ Satellite proxy HTTP ${response.status}`);
                return;
            }
            
            const blob = await response.blob();
            const objectUrl = URL.createObjectURL(blob);
            console.log('🛰️ Image satellite reçue:', (blob.size / 1024).toFixed(0), 'Ko');
            
            // Charger l'image pour appliquer contraste/saturation
            const img = new Image();
            img.onload = () => {
                // Créer un canvas pour booster le contraste
                const canvas = document.createElement('canvas');
                canvas.width = img.width;
                canvas.height = img.height;
                const ctx = canvas.getContext('2d');
                
                // Dessiner l'image originale
                ctx.drawImage(img, 0, 0);
                
                // Booster le contraste et la saturation
                ctx.globalCompositeOperation = 'source-over';
                // Augmenter le contraste via courbe S
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const d = imageData.data;
                const contrast = 1.3; // 1.0 = normal, 1.3 = +30%
                const satBoost = 1.25; // +25% saturation
                for (let i = 0; i < d.length; i += 4) {
                    // Contraste
                    let r = ((d[i] / 255 - 0.5) * contrast + 0.5) * 255;
                    let g = ((d[i+1] / 255 - 0.5) * contrast + 0.5) * 255;
                    let b = ((d[i+2] / 255 - 0.5) * contrast + 0.5) * 255;
                    
                    // Saturation
                    const gray = 0.299 * r + 0.587 * g + 0.114 * b;
                    r = gray + (r - gray) * satBoost;
                    g = gray + (g - gray) * satBoost;
                    b = gray + (b - gray) * satBoost;
                    
                    d[i]   = Math.max(0, Math.min(255, r));
                    d[i+1] = Math.max(0, Math.min(255, g));
                    d[i+2] = Math.max(0, Math.min(255, b));
                }
                ctx.putImageData(imageData, 0, 0);
                
                const tex = new THREE.CanvasTexture(canvas);
                tex.wrapS = THREE.ClampToEdgeWrapping;
                tex.wrapT = THREE.ClampToEdgeWrapping;
                tex.minFilter = THREE.LinearMipMapLinearFilter;
                tex.magFilter = THREE.LinearFilter;
                tex.anisotropy = 4; // Meilleur rendu en perspective
                
                if (this.terrainMesh) {
                    this.terrainMesh.material.map = tex;
                    this.terrainMesh.material.color.set(0xffffff);
                    this.terrainMesh.material.needsUpdate = true;
                }
                
                // Ne PAS appliquer au sol secondaire (600x600) :
                // la même image satellite étirée sur un plan 3x plus grand
                // crée un doublon flou et hors échelle
                
                console.log('✅ Texture satellite contrastée appliquée au terrain');
                URL.revokeObjectURL(objectUrl);
            };
            img.onerror = () => {
                console.warn('⚠ Erreur chargement image satellite');
                URL.revokeObjectURL(objectUrl);
            };
            img.src = objectUrl;
        } catch (e) {
            console.warn('⚠ Erreur texture satellite:', e);
        }
    }
    
    /**
     * Convertit lat/lon en coordonnées locales 3D (mètres depuis le centre)
     */
    _geoToLocal(lat, lon) {
        return {
            x: (lon - this.centerLon) * this.LNG_TO_M,
            z: -(lat - this.centerLat) * this.LAT_TO_M // Z inversé (Three.js)
        };
    }
    
    /**
     * Convertit coordonnées locales 3D → lat/lon (inverse de _geoToLocal)
     */
    _localToGeo(x, z) {
        return {
            lat: this.centerLat + (-z) / this.LAT_TO_M,
            lng: this.centerLon + x / this.LNG_TO_M
        };
    }
    
    /**
     * Remplissage automatique des pans de toiture avec des modules PV.
     * Calcule tout en 3D (position, orientation, pente) et retourne des données
     * utilisables à la fois pour l'affichage 3D et pour la projection en 2D.
     *
     * @param {number} moduleW - Largeur module en m (ex: 1.134)
     * @param {number} moduleH - Hauteur module en m (ex: 2.278)
     * @param {number} espacement - Espacement en m (ex: 0.05)
     * @param {string} disposition - 'paysage' ou 'portrait'
     * @param {Array<number>} [panelIndices] - Indices des pans à remplir (null = tous)
     * @returns {Array<Object>} Zones générées [{panelName, orientation, inclinaison, modules: [{lat, lng, corners}]}]
     */
    autoFillRoofPanels(moduleW, moduleH, espacement, disposition, panelIndices, obstacleRects, options) {
        if (!this.roofPanelsInfo || !this.roofPanelsInfo.panels.length) {
            console.warn('⚠️ Pas de roofPanelsInfo pour le remplissage auto');
            return [];
        }
        
        const obb = this.roofPanelsInfo.buildingOBB;
        if (!obb) {
            console.warn('⚠️ Pas de buildingOBB');
            return [];
        }
        
        const info = this.roofPanelsInfo;
        const halfShort = obb.shortDim / 2;
        const halfLong = obb.longDim / 2;
        const cosA = Math.cos(obb.angle);
        const sinA = Math.sin(obb.angle);
        
        // Dimensions du module selon la disposition
        let modAlong, modAcross;
        if (disposition === 'paysage') {
            modAlong = Math.max(moduleW, moduleH);
            modAcross = Math.min(moduleW, moduleH);
        } else {
            modAlong = Math.min(moduleW, moduleH);
            modAcross = Math.max(moduleW, moduleH);
        }
        
        // Marge depuis le bord du toit (acrotère, rive, etc.)
        // Pour un toit plat avec acrotère (parapet), 80cm ; pour toit incliné, 30cm.
        // Si le LiDAR a détecté un acrotère, on utilise sa largeur + 20cm de sécurité.
        const isFlat = info.type === 'flat' || !info.type;
        const marge = (() => {
            if (this.roofPanelsInfo && this.roofPanelsInfo._acrotereWidth) {
                return this.roofPanelsInfo._acrotereWidth + 0.20;
            }
            return isFlat ? 0.80 : 0.30;
        })();
        
        const generatedZones = [];
        
        // Supprimer anciens modules 3D
        this.modules3D.forEach(m => {
            this.scene.remove(m);
            if (m.children) m.children.forEach(c => { if (c.geometry) c.geometry.dispose(); if (c.material) { if (Array.isArray(c.material)) c.material.forEach(mat => mat.dispose()); else c.material.dispose(); } });
            if (m.geometry) m.geometry.dispose();
            if (m.material) { if (Array.isArray(m.material)) m.material.forEach(mat => mat.dispose()); else m.material.dispose(); }
        });
        this.modules3D = [];
        
        const panelMat = new THREE.MeshPhongMaterial({
            color: 0x1a237e, specular: 0x4444ff, shininess: 80,
            transparent: true, opacity: 0.92,
            depthWrite: true,
            polygonOffset: true,
            polygonOffsetFactor: -2,
            polygonOffsetUnits: -2,
        });
        
        // Hauteur de pose : utiliser les MÊMES valeurs que _createBuilding3D
        // pour éviter un décalage entre le toit 3D et les modules
        const terrainH = info.buildingTerrainH || this._getTerrainHeight(obb.cx, obb.cz);
        const wallH = info.buildingWallH || this._findBuildingWallHeight(obb.cx, obb.cz);
        const eaveY = terrainH + wallH;
        // Hauteur du faîtage au-dessus de l'égout (pour positionner le pivot de rotation)
        const ridgeExtra = info.hauteurFaitageRelatif || 0;

        // Offsets bâtiment → monde pour conversion des coordonnées plans Solar
        const _bCenterGeo = info.buildingCenterGeo || { lat: this.centerLat, lng: this.centerLon };
        const _lngToM = this.LAT_TO_M * Math.cos(_bCenterGeo.lat * Math.PI / 180);
        const _bldgOffX = (_bCenterGeo.lng - this.centerLon) * _lngToM;
        const _bldgOffZ = -(_bCenterGeo.lat - this.centerLat) * this.LAT_TO_M;
        
        // Polygone réel du bâtiment pour filtrer les modules hors emprise
        const buildingPoly = info.buildingLocalCoords || null;
        
        const panels = info.panels;
        const opts = options || {};
        const sunshineThresholdH   = opts.sunshineThresholdH   || 0;
        const sunshineThresholdMax  = (opts.sunshineThresholdMax > 0 && isFinite(opts.sunshineThresholdMax))
                                      ? opts.sunshineThresholdMax : Infinity;
        const maxPowerKw            = (opts.maxPowerKw > 0 && isFinite(opts.maxPowerKw)) ? opts.maxPowerKw : Infinity;
        const modulePowerW          = opts.modulePowerW || 400;

        // Trier par ensoleillement décroissant — placer en priorité les meilleurs pans
        let indicesToProcess = panelIndices || panels.map((_, i) => i);
        indicesToProcess = [...indicesToProcess].sort((a, b) =>
            ((panels[b]?.sunshineAnnual || 0) - (panels[a]?.sunshineAnnual || 0))
        );
        // Filtrer par plage d'irradiance min–max
        // Si sunshineAnnual est absent ET que rejectMissingData=true (données Solar présentes) → rejeter
        // Si rejectMissingData=false (pas de données Solar) → conserver les pans sans irradiance
        const rejectMissingData = opts.rejectMissingData === true;
        if (sunshineThresholdH > 0 || isFinite(sunshineThresholdMax)) {
            indicesToProcess = indicesToProcess.filter(i => {
                const v = panels[i]?.sunshineAnnual;
                if (v === undefined || v === null) return !rejectMissingData; // selon disponibilité données Solar
                return v >= sunshineThresholdH && v <= sunshineThresholdMax;
            });
            if (indicesToProcess.length === 0)
                console.warn(`⚠️ Aucun pan dans la plage [${sunshineThresholdH}–${isFinite(sunshineThresholdMax) ? sunshineThresholdMax : '∞'}] kWh/m²/an`);
        }

        let totalModules = 0;
        let modulesRemaining = isFinite(maxPowerKw) ? Math.floor(maxPowerKw * 1000 / modulePowerW) : Infinity;
        let powerLimitReached = false;

        // === Grille d'occupation inter-panneaux ===
        // Évite les superpositions de modules entre panneaux Solar dont les polygon_2d
        // se chevauchent ou sont adjacents. La résolution de cellule = demi-dimension
        // minimale du module → deux modules à des positions identiques ou très proches
        // partagent la même clé et seul le premier (meilleur pan en ensoleillement) est conservé.
        const _occCellSize = Math.min(modAlong, modAcross) * 0.5;
        const _occGrid = new Set();
        const _occKey = (wx, wz) => {
            const gx = Math.round(wx / _occCellSize);
            const gz = Math.round(wz / _occCellSize);
            return `${gx},${gz}`;
        };

        indicesToProcess.forEach(pi => {
            if (powerLimitReached) return;
            const panel = panels[pi];
            if (!panel) return;
            
            const penteDeg = panel.pente_deg;
            const penteRad = penteDeg * Math.PI / 180;
            const azimutDeg = panel.orientation_deg;
            const azimutRad = azimutDeg * Math.PI / 180;

            // Angle 2D pour la projection des coins en coordonnées Leaflet.
            // Les pans Solar (mnh_a/b définis) sont orientés par leur azimut réel :
            //   rotation.y = π - azimutRad en 3D  →  long axe = (-cos az, sin az) dans XZ.
            // Pour les pans OBB paramétriques (fallback), on garde l'axe OBB du bâtiment.
            const _isSolarPan = (panel.mnh_a !== undefined && panel.mnh_b !== undefined);
            // Axes du pan en coordonnées monde (X=Est, Z=Sud) :
            //   crête (along)  : d_al = ( cos az,  sin az)  — parallèle au faîtage
            //   pente (across) : d_ac = ( sin az, -cos az)  — sens de la descente
            // Note : cos2D/sin2D forment la matrice de rotation pour les coins Leaflet
            // et doivent être identiques à d_al pour que grille et coins soient cohérents.
            const cos2D = _isSolarPan ?  Math.cos(azimutRad) : cosA;
            const sin2D = _isSolarPan ?  Math.sin(azimutRad) : sinA;
            
            // === Calculer le rectangle disponible sur ce pan ===
            let panAlongStart, panAlongEnd, panAcrossStart, panAcrossEnd;

            // ── Priorité : bornes projetées sur les axes du pan (azimut pour Solar, OBB sinon) ──
            // Les axes du pan sont dérivés de rotation.y = π - az (cohérent avec cos2D/sin2D) :
            //   along : d_al = (-cos az, sin az)   (parallèle au faîtage)
            //   across : d_ac = (-sin az, -cos az)  (sens de la pente)
            // On projette en coordonnées monde absolues (pas relatives à obb.cx)
            // pour que les centres worldX/worldZ soient dans le même repère que les coins.
            if (_isSolarPan && panel.polygon_2d && panel.polygon_2d.length >= 3) {
                const d_al_x =  Math.cos(azimutRad), d_al_z =  Math.sin(azimutRad);
                const d_ac_x =  Math.sin(azimutRad), d_ac_z = -Math.cos(azimutRad);
                let minAl = Infinity, maxAl = -Infinity;
                let minAc = Infinity, maxAc = -Infinity;
                for (const [px, py] of panel.polygon_2d) {
                    const wx = _bldgOffX + px;
                    const wz = _bldgOffZ - py;
                    const al = wx * d_al_x + wz * d_al_z;
                    const ac = wx * d_ac_x + wz * d_ac_z;
                    if (al < minAl) minAl = al;
                    if (al > maxAl) maxAl = al;
                    if (ac < minAc) minAc = ac;
                    if (ac > maxAc) maxAc = ac;
                }
                panAlongStart  = minAl + marge;
                panAlongEnd    = maxAl - marge;
                panAcrossStart = minAc + marge;
                panAcrossEnd   = maxAc - marge;
            } else if (!_isSolarPan && panel.polygon_2d && panel.polygon_2d.length >= 3) {
                let minAl = Infinity, maxAl = -Infinity;
                let minAc = Infinity, maxAc = -Infinity;
                for (const [px, py] of panel.polygon_2d) {
                    const wx = _bldgOffX + px;
                    const wz = _bldgOffZ - py;
                    const dwx = wx - obb.cx, dwz = wz - obb.cz;
                    const al =  dwx * cosA + dwz * sinA;
                    const ac = -dwx * sinA + dwz * cosA;
                    if (al < minAl) minAl = al;
                    if (al > maxAl) maxAl = al;
                    if (ac < minAc) minAc = ac;
                    if (ac > maxAc) maxAc = ac;
                }
                panAlongStart  = minAl + marge;
                panAlongEnd    = maxAl - marge;
                panAcrossStart = minAc + marge;
                panAcrossEnd   = maxAc - marge;
            } else if (info.type === 'gable') {
                // Pan rectangulaire : longueur = axe principal, largeur = demi-shortDim
                panAlongStart = -halfLong + marge;
                panAlongEnd = halfLong - marge;
                if (pi === 0) {
                    panAcrossStart = marge;
                    panAcrossEnd = halfShort - marge;
                } else {
                    panAcrossStart = -halfShort + marge;
                    panAcrossEnd = -marge;
                }
            } else if (info.type === 'hip') {
                if (pi < 2) {
                    // Pans principaux (trapézoïdaux) — simplification rectangulaire
                    const ridgeHalfLen = halfLong * 0.45;
                    panAlongStart = -ridgeHalfLen + marge;
                    panAlongEnd = ridgeHalfLen - marge;
                    if (pi === 0) {
                        panAcrossStart = marge;
                        panAcrossEnd = halfShort - marge;
                    } else {
                        panAcrossStart = -halfShort + marge;
                        panAcrossEnd = -marge;
                    }
                } else {
                    // Croupes — trop petites en général, skip
                    console.log(`⏭️ Croupe ${panel.name} ignorée (surface trop petite)`);
                    return;
                }
            } else if (info.type === 'shed') {
                panAlongStart = -halfLong + marge;
                panAlongEnd = halfLong - marge;
                panAcrossStart = -halfShort + marge;
                panAcrossEnd = halfShort - marge;
            } else if (info.type === 'multi-gable') {
                // Multi-gable : chaque section a 2 pans (A et B)
                const nRidges = info.nRidges || 1;
                const sectionWidth = obb.shortDim / nRidges;
                const halfSection = sectionWidth / 2;
                const ridgeIdx = Math.floor(pi / 2); // quel faîtage
                const sideIdx = pi % 2;               // côté A (0) ou B (1)
                
                panAlongStart = -halfLong + marge;
                panAlongEnd = halfLong - marge;
                
                const sectionStart = -halfShort + ridgeIdx * sectionWidth;
                if (sideIdx === 0) {
                    panAcrossStart = sectionStart + marge;
                    panAcrossEnd = sectionStart + halfSection - marge;
                } else {
                    panAcrossStart = sectionStart + halfSection + marge;
                    panAcrossEnd = sectionStart + sectionWidth - marge;
                }
            } else if (info.type === 'multi-shed') {
                // Multi-shed : 1 pan incliné par section
                const nRidges = info.nRidges || 1;
                const sectionWidth = obb.shortDim / nRidges;
                
                panAlongStart = -halfLong + marge;
                panAlongEnd = halfLong - marge;
                
                const sectionStart = -halfShort + pi * sectionWidth;
                panAcrossStart = sectionStart + marge;
                panAcrossEnd = sectionStart + sectionWidth - marge;
            } else {
                // Plat
                panAlongStart = -halfLong + marge;
                panAlongEnd = halfLong - marge;
                panAcrossStart = -halfShort + marge;
                panAcrossEnd = halfShort - marge;
            }
            
            // Dimensions utilisables
            const usableAlong = panAlongEnd - panAlongStart;
            const usableAcross = Math.abs(panAcrossEnd - panAcrossStart);
            
            // Nombre de modules
            const nbAlong = Math.floor(usableAlong / (modAlong + espacement));
            const nbAcross = Math.floor(usableAcross / (modAcross + espacement));
            
            if (nbAlong <= 0 || nbAcross <= 0) {
                console.log(`⏭️ Pan ${panel.name} : pas assez de place (${usableAlong.toFixed(1)}x${usableAcross.toFixed(1)}m)`);
                return;
            }
            
            // Centrer la grille dans l'espace disponible
            const gridAlong = nbAlong * (modAlong + espacement) - espacement;
            const gridAcross = nbAcross * (modAcross + espacement) - espacement;
            const offsetAlong = panAlongStart + (usableAlong - gridAlong) / 2;
            const offsetAcross = (panAcrossStart < panAcrossEnd)
                ? panAcrossStart + (usableAcross - gridAcross) / 2
                : panAcrossEnd + (usableAcross - gridAcross) / 2;
            
            // Créer le groupe 3D pour ce pan.
            // Pour les pans Solar : pivot au centroïde 3D du plan (via équation du plan),
            // pas au centre OBB — sinon la rotation emporte les modules vers le mauvais côté.
            // Pour les pans paramétriques : pivot au faîtage (eaveY + ridgeExtra).
            const panGroup = new THREE.Group();
            let _pivotX = obb.cx, _pivotZ = obb.cz;
            let _pivotY = eaveY + ridgeExtra;
            if (panel.mnh_a !== undefined && panel.mnh_b !== undefined && panel.polygon_2d) {
                // Centroïde du polygone du plan Solar en coordonnées Solar locales
                const _pcx = panel.polygon_2d.reduce((s, p) => s + p[0], 0) / panel.polygon_2d.length;
                const _pcy = panel.polygon_2d.reduce((s, p) => s + p[1], 0) / panel.polygon_2d.length;
                _pivotX = _bldgOffX + _pcx;
                _pivotZ = _bldgOffZ - _pcy;
                const _mnh = panel.mnh_a * _pcx + panel.mnh_b * _pcy + panel.mnh_c;
                _pivotY = terrainH + Math.max(wallH, _mnh);
            }
            panGroup.position.set(_pivotX, _pivotY, _pivotZ);
            
            const modules = [];
            
            // Vecteurs pour back-projection des centres (Solar = azimut absolu, OBB sinon)
            // crête : (cos az, sin az), pente : (sin az, -cos az) — cohérent avec cos2D/sin2D
            const _d_al_x = _isSolarPan ?  Math.cos(azimutRad) : cosA;
            const _d_al_z = _isSolarPan ?  Math.sin(azimutRad) : sinA;
            const _d_ac_x = _isSolarPan ?  Math.sin(azimutRad) : -sinA;
            const _d_ac_z = _isSolarPan ? -Math.cos(azimutRad) :  cosA;
            const _refX   = _isSolarPan ? 0 : obb.cx;
            const _refZ   = _isSolarPan ? 0 : obb.cz;

            outerLoop: for (let iAlong = 0; iAlong < nbAlong; iAlong++) {
                for (let iAcross = 0; iAcross < nbAcross; iAcross++) {
                    const along = offsetAlong + iAlong * (modAlong + espacement) + modAlong / 2;
                    const across = offsetAcross + iAcross * (modAcross + espacement) + modAcross / 2;
                    
                    // Back-projeter en coordonnées monde via les vecteurs du pan
                    const worldX = _refX + along * _d_al_x + across * _d_ac_x;
                    const worldZ = _refZ + along * _d_al_z + across * _d_ac_z;

                    // === Filtrage par polygone Solar du plan (PRIORITÉ 0) ===
                    // Evite tout chevauchement inter-zones lorsque les AABB OBB se recoupent.
                    if (panel.polygon_2d && panel.polygon_2d.length >= 3) {
                        const sPx = worldX - _bldgOffX;
                        const sPy = -(worldZ - _bldgOffZ);
                        // Point-in-polygon Raycasting en coords Solar 2D
                        let insideSolar = false;
                        const spoly = panel.polygon_2d;
                        for (let si = 0, sj = spoly.length - 1; si < spoly.length; sj = si++) {
                            const xi = spoly[si][0], yi = spoly[si][1];
                            const xj = spoly[sj][0], yj = spoly[sj][1];
                            if (((yi > sPy) !== (yj > sPy)) &&
                                (sPx < (xj - xi) * (sPy - yi) / (yj - yi) + xi)) {
                                insideSolar = !insideSolar;
                            }
                        }
                        if (!insideSolar) continue;
                    }
                    
                    // === Filtrage par polygone réel du bâtiment ===
                    // Vérifier que les 4 coins du module sont dans l'emprise réelle
                    if (buildingPoly) {
                        const halfW = modAlong / 2;
                        const halfH = modAcross / 2;
                        const corners = [
                            { x: worldX + (-halfW)*cos2D - (-halfH)*sin2D, z: worldZ + (-halfW)*sin2D + (-halfH)*cos2D },
                            { x: worldX + ( halfW)*cos2D - (-halfH)*sin2D, z: worldZ + ( halfW)*sin2D + (-halfH)*cos2D },
                            { x: worldX + ( halfW)*cos2D - ( halfH)*sin2D, z: worldZ + ( halfW)*sin2D + ( halfH)*cos2D },
                            { x: worldX + (-halfW)*cos2D - ( halfH)*sin2D, z: worldZ + (-halfW)*sin2D + ( halfH)*cos2D },
                        ];
                        // Au moins 3 coins sur 4 doivent être dans le polygone
                        const insideCount = corners.filter(c => 
                            this._pointInPolygon2D(c.x, c.z, buildingPoly.map(p => ({x: p.x, y: p.z})))
                        ).length;
                        if (insideCount < 3) continue; // Module hors emprise → skip
                    }
                    
                    // === Filtrage par obstacles (cheminées, acrotères, trappes...) ===
                    if (obstacleRects && obstacleRects.length > 0) {
                        // Convertir le centre du module en lat/lng
                        const modGeo = this._localToGeo(worldX, worldZ);
                        // Vérifier si le module ou ses coins chevauchent un obstacle (+ buffer 0.5m)
                        const halfW2 = modAlong / 2;
                        const halfH2 = modAcross / 2;
                        const modCorners = [
                            this._localToGeo(worldX + (-halfW2)*cos2D - (-halfH2)*sin2D, worldZ + (-halfW2)*sin2D + (-halfH2)*cos2D),
                            this._localToGeo(worldX + ( halfW2)*cos2D - (-halfH2)*sin2D, worldZ + ( halfW2)*sin2D + (-halfH2)*cos2D),
                            this._localToGeo(worldX + ( halfW2)*cos2D - ( halfH2)*sin2D, worldZ + ( halfW2)*sin2D + ( halfH2)*cos2D),
                            this._localToGeo(worldX + (-halfW2)*cos2D - ( halfH2)*sin2D, worldZ + (-halfW2)*sin2D + ( halfH2)*cos2D),
                        ];
                        
                        let hitObstacle = false;
                        for (const obs of obstacleRects) {
                            // Vérifier si le centre du module est dans le rectangle obstacle
                            if (modGeo.lat >= obs.minLat && modGeo.lat <= obs.maxLat &&
                                modGeo.lng >= obs.minLng && modGeo.lng <= obs.maxLng) {
                                hitObstacle = true;
                                break;
                            }
                            // Vérifier si AUCUN coin du module ne chevauche l'obstacle
                            for (const c of modCorners) {
                                if (c.lat >= obs.minLat && c.lat <= obs.maxLat &&
                                    c.lng >= obs.minLng && c.lng <= obs.maxLng) {
                                    hitObstacle = true;
                                    break;
                                }
                            }
                            if (hitObstacle) break;
                        }
                        if (hitObstacle) continue; // Module touche un obstacle → skip
                    }

                    // === Vérification anti-superposition inter-panneaux ===
                    const _key = _occKey(worldX, worldZ);
                    if (_occGrid.has(_key)) continue; // Cellule déjà occupée par un autre pan → skip
                    _occGrid.add(_key);

                    // === Position et rotation du module 3D ===
                    const panel3d = new THREE.Mesh(
                        new THREE.BoxGeometry(modAlong, 0.04, modAcross),
                        panelMat
                    );

                    if (panel.mnh_a !== undefined && panel.mnh_b !== undefined) {
                        // ── Positionnement direct depuis l'équation de plan Solar ──
                        // Chaque module est positionné à son Y exact sur la surface du plan
                        // + offset perpendiculaire ≈ 0.06m. Pas de rotation du groupe.
                        // → élimine tout chevauchement géométrique inter-zones.
                        const sPx = worldX - _bldgOffX;
                        const sPy = -(worldZ - _bldgOffZ);
                        const mnh = panel.mnh_a * sPx + panel.mnh_b * sPy + panel.mnh_c;
                        // Composante Y de l'offset perpendiculaire (0.06m le long de la normale)
                        const normLen = Math.sqrt(panel.mnh_a*panel.mnh_a + panel.mnh_b*panel.mnh_b + 1);
                        const offsetY = 0.06 * normLen; // ≈ 0.06 for gentle slopes
                        const modY = terrainH + Math.max(wallH, mnh) + offsetY;
                        // panel3d.position est en espace LOCAL du panGroup → soustraire le pivot monde
                        panel3d.position.set(worldX - _pivotX, modY - _pivotY, worldZ - _pivotZ);
                        // Orienter le module : long axe (X) perpendiculaire au versant (axe faîtage),
                        // puis incliner rotation.x pour suivre la pente du pan.
                        // rotation.y = π - az → X aligne le long du faîtage, Z pointe dans le sens de descente
                        // rotation.x = penteRad → incline le côté "bas" dans la direction de descente
                        panel3d.rotation.order = 'YXZ';
                        panel3d.rotation.y = Math.PI - azimutRad;
                        panel3d.rotation.x = penteRad;
                    } else {
                        // ── Positionnement OBB paramétrique (fallback) ──
                        const localX = worldX - _pivotX;
                        const localZ = worldZ - _pivotZ;
                        panel3d.position.set(localX, 0.25, localZ);
                        panel3d.rotation.y = -obb.angle;
                    }

                    panel3d.castShadow = true;
                    panel3d.receiveShadow = true;
                    panel3d.renderOrder = 10; // S'afficher au-dessus du toit
                    panGroup.add(panel3d);
                    
                    // Calculer les 4 coins en coordonnées géo (lat/lng) pour la projection 2D
                    // Utiliser cos2D/sin2D (azimut réel du pan) pour aligner les modules
                    // sur la pente de toiture et non sur l'OBB du bâtiment.
                    const halfW = modAlong / 2;
                    const halfH = modAcross / 2;
                    const cornersLocal = [
                        { x: worldX + (-halfW) * cos2D - (-halfH) * sin2D, z: worldZ + (-halfW) * sin2D + (-halfH) * cos2D },
                        { x: worldX + ( halfW) * cos2D - (-halfH) * sin2D, z: worldZ + ( halfW) * sin2D + (-halfH) * cos2D },
                        { x: worldX + ( halfW) * cos2D - ( halfH) * sin2D, z: worldZ + ( halfW) * sin2D + ( halfH) * cos2D },
                        { x: worldX + (-halfW) * cos2D - ( halfH) * sin2D, z: worldZ + (-halfW) * sin2D + ( halfH) * cos2D },
                    ];
                    
                    const cornersGeo = cornersLocal.map(c => this._localToGeo(c.x, c.z));
                    const centerGeo = this._localToGeo(worldX, worldZ);
                    
                    modules.push({
                        lat: centerGeo.lat,
                        lng: centerGeo.lng,
                        corners: cornersGeo
                    });

                    totalModules++;
                    if (isFinite(modulesRemaining)) {
                        modulesRemaining--;
                        if (modulesRemaining <= 0) { powerLimitReached = true; break outerLoop; }
                    }
                }
            }
            
            // Appliquer la pente au groupe (uniquement pans paramétriques OBB)
            // Les pans Solar sont déjà positionnés directement en world space → pas de rotation groupe
            const isSolarPlan = (panel.mnh_a !== undefined && panel.mnh_b !== undefined);
            if (!isSolarPlan && penteRad > 0.001) {
                const tiltAxis = new THREE.Vector3(
                    -Math.cos(azimutRad), 0, -Math.sin(azimutRad)
                ).normalize();
                panGroup.rotateOnWorldAxis(tiltAxis, penteRad);
            }
            
            this.scene.add(panGroup);
            this.modules3D.push(panGroup);
            
            generatedZones.push({
                panelIndex: pi,
                panelName: panel.name,
                orientation: azimutDeg,
                inclinaison: penteDeg,
                orientationLabel: panel.orientation_label,
                nbModules: modules.length,
                nbCols: nbAlong,
                nbRows: nbAcross,
                modulesPositions: modules
            });
            
            console.log(`✅ Pan ${panel.name} : ${nbAlong}x${nbAcross} = ${modules.length} modules (${azimutDeg}°, pente ${penteDeg}°)`);
        });
        
        console.log(`✅ Remplissage auto toiture: ${totalModules} modules sur ${generatedZones.length} pan(s)`);
        return generatedZones;
    }
    
    /**
     * Récupère l'altitude du terrain à une position locale (avec exagération).
     * Utilise l'interpolation bilinéaire pour correspondre exactement au mesh terrain
     * et éviter les bâtiments flottants.
     */
    _getTerrainHeight(x, z) {
        if (!this.lidarData || !this.lidarData.terrain) return 0;
        
        const terrain = this.lidarData.terrain;
        const bbox = terrain.bbox;
        const gridSize = terrain.grid_size;
        
        // Convertir x, z en coordonnées continues de grille
        const radiusM = (bbox.north - bbox.south) * this.LAT_TO_M / 2;
        const fx = (x + radiusM) / (radiusM * 2) * (gridSize - 1);
        const fy = (z + radiusM) / (radiusM * 2) * (gridSize - 1);
        
        // Interpolation bilinéaire (même fonction que le terrain mesh)
        if (this._sampleMNTBilinear) {
            const alt = this._sampleMNTBilinear(fx, fy);
            return alt * (this._verticalExaggeration || 1);
        }
        
        // Fallback : nearest-neighbor
        const ix = Math.min(gridSize - 1, Math.max(0, Math.round(fx)));
        const iy = Math.min(gridSize - 1, Math.max(0, Math.round(fy)));
        const alt = terrain.mnt[iy] ? (terrain.mnt[iy][ix] || 0) : 0;
        return alt * (this._verticalExaggeration || 1);
    }
    
    /**
     * Construit les bâtiments 3D depuis BD TOPO et OSM
     */
    async _buildBuildings(data) {
        // Préserver les meshes Solar si la heatmap est déjà active.
        // _buildBuildings est rappelé après chaque mise à jour LiDAR/RANSAC ;
        // sans cette protection, les quads Solar sont supprimés et remplacés
        // par de nouveaux meshes RANSAC visibles.
        const _solarSet = new Set([
            ...(this._solarRoofMeshes  || []),
            ...(this._solarPanelMeshes || []),
        ]);
        const _solarActive = _solarSet.size > 0;

        // Supprimer les anciens bâtiments (sauf meshes Solar à préserver)
        this.buildings.forEach(b => {
            if (_solarActive && _solarSet.has(b)) return;  // garder
            this.scene.remove(b);
            if (b.geometry) b.geometry.dispose();
            if (b.material) { if (Array.isArray(b.material)) b.material.forEach(m => m.dispose()); else b.material.dispose(); }
        });
        this.buildings = _solarActive
            ? this.buildings.filter(b => _solarSet.has(b))
            : [];
        if (_solarActive) {
            console.log(`ℹ️ _buildBuildings: Solar actif (${_solarSet.size} meshes) — conservés, RANSAC créés masqués`);
        }
        
        const allBuildings = [];
        
        // BD TOPO buildings (prioritaire - ont hauteur réelle)
        if (data.buildings_bdtopo) {
            data.buildings_bdtopo.forEach((b, idx) => {
                // === Hauteur corniche = hauteur réelle des murs (pour extrusion) ===
                // altitude_toit_min = corniche/acrotère = sommet des murs sans le toit
                let computedEave = null;
                if (b.altitude_toit_min != null && b.altitude_sol_min != null) {
                    const d = b.altitude_toit_min - b.altitude_sol_min;
                    if (d > 1.0 && d < 80) computedEave = d;
                }
                // Fallback : 70% du faîtage (approximation corniche pour toit avec pente)
                if (!computedEave && b.hauteur && b.hauteur > 1.0) computedEave = b.hauteur * 0.7;
                if (!computedEave && b.nb_etages && b.nb_etages > 0) computedEave = b.nb_etages * 3.0;
                if (!computedEave) computedEave = 6;

                // === Hauteur faîtage (compat, non utilisée pour extrusion) ===
                let computedH = null;
                if (b.hauteur && b.hauteur > 1.0) computedH = b.hauteur;
                else if (b.altitude_toit_max != null && b.altitude_sol_min != null) {
                    const d = b.altitude_toit_max - b.altitude_sol_min;
                    if (d > 1.0 && d < 80) computedH = d;
                }
                if (!computedH && b.nb_etages && b.nb_etages > 0) computedH = b.nb_etages * 3.0;
                if (!computedH) computedH = computedEave;

                allBuildings.push({
                    coords: b.coords,
                    height: computedH,       // faîtage (non utilisé pour extrusion)
                    height_eave: computedEave, // corniche → extrusion des murs
                    source: 'bdtopo',
                    _bdtopoIdx: idx,
                    usage: b.usage,
                    nature: b.nature,
                    materiaux_toit: b.materiaux_toit,
                    materiaux_murs: b.materiaux_murs,
                    alt_toit_min: b.altitude_toit_min,
                    alt_toit_max: b.altitude_toit_max,
                    nb_etages: b.nb_etages,
                });
            });
        }
        
        // OSM buildings (complément)
        if (data.buildings_osm) {
            data.buildings_osm.forEach(b => {
                // Vérifier que ce bâtiment n'est pas déjà dans BD TOPO (overlap)
                const center = this._polygonCenter(b.coords);
                const isOverlap = allBuildings.some(existing => {
                    const ec = this._polygonCenter(existing.coords);
                    const dist = Math.sqrt(
                        Math.pow((ec.x - center.x) * this.LNG_TO_M, 2) +
                        Math.pow((ec.y - center.y) * this.LAT_TO_M, 2)
                    );
                    return dist < 5; // < 5m = même bâtiment
                });
                
                if (!isOverlap) {
                    allBuildings.push({
                        coords: b.coords,
                        height: b.hauteur || 6,
                        source: 'osm',
                        type: b.type,
                        roof_shape: b.roof_shape,
                    });
                }
            });
        }
        
        // === Sélectionner le bâtiment cible (celui qui porte la centrale PV) ===
        //
        // Stratégie en 3 niveaux, du plus précis au moins précis :
        //  1. Le bâtiment dont le polygone CONTIENT le centre de la scène
        //     (cas normal : adresse sur le bâtiment, polygone BD TOPO couvre l'adresse)
        //  2. Le bâtiment dont l'ARÊTE du polygone est la plus proche du centre
        //     (cas : adresse sur la route devant le bâtiment — le bâtiment cible est
        //      à quelques mètres, pas son centroïde)
        //
        // Attention : NE PAS utiliser la distance centroïde-à-centre comme critère
        // principal — un voisin avec un petit polygone peut avoir un centroïde plus proche
        // même si le bâtiment cible est juste de l'autre côté de la route.

        const _pInPolyGeo = (lon, lat, coords) => {
            let inside = false;
            const n = coords.length;
            for (let i = 0, j = n - 1; i < n; j = i++) {
                const xi = coords[i][0], yi = coords[i][1];
                const xj = coords[j][0], yj = coords[j][1];
                if (((yi > lat) !== (yj > lat)) &&
                    (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi)) {
                    inside = !inside;
                }
            }
            return inside;
        };

        // Distance minimale d'un point (lon,lat) à chaque arête du polygone
        const _minEdgeDistGeo = (lon, lat, coords) => {
            let minD = Infinity;
            const n = coords.length;
            const sx = this.LNG_TO_M, sy = this.LAT_TO_M;
            for (let i = 0, j = n - 1; i < n; j = i++) {
                const ax = (coords[i][0] - lon) * sx, ay = (coords[i][1] - lat) * sy;
                const bx = (coords[j][0] - lon) * sx, by = (coords[j][1] - lat) * sy;
                const dxAB = bx - ax, dyAB = by - ay;
                const lenSq = dxAB*dxAB + dyAB*dyAB;
                let t = lenSq > 0 ? Math.max(0, Math.min(1, -(ax*dxAB + ay*dyAB) / lenSq)) : 0;
                const px = ax + t*dxAB, py = ay + t*dyAB;
                const d = Math.sqrt(px*px + py*py);
                if (d < minD) minD = d;
            }
            return minD;
        };

        // ── Sélection du bâtiment PV principal ────────────────────────────────
        // PRIORITÉ : building_hd.building_index (index retourné par le backend).
        // Le backend choisit le bâtiment le plus proche du point cliqué dans la
        // liste buildings_bdtopo. Si on utilise un index différent côté JS :
        //   - les murs sont posés sur le bâtiment A
        //   - le toit RANSAC (calculé pour bâtiment B) est placé aux coordonnées de B
        //   → décalage visible de 10-50m entre murs et toit.
        // On fait confiance à building_hd.building_index quand disponible.
        const _hdBuildingIdx = this.lidarData?.building_hd?.building_index;
        let selectedIdx = -1;

        if (_hdBuildingIdx !== undefined && _hdBuildingIdx >= 0 && _hdBuildingIdx < allBuildings.length) {
            selectedIdx = _hdBuildingIdx;
            console.log(`🏗️ Bâtiment PV sélectionné par building_hd.building_index (idx=${selectedIdx})`);
        }

        // Fallback si pas de building_hd ou index invalide :
        if (selectedIdx === -1) {
            // Niveau 1 : containment (centre exact dans le polygone)
            for (let i = 0; i < allBuildings.length; i++) {
                if (_pInPolyGeo(this.centerLon, this.centerLat, allBuildings[i].coords)) {
                    selectedIdx = i;
                    console.log(`🏗️ Bâtiment PV sélectionné par containment (idx=${i})`);
                    break;
                }
            }
        }

        // Niveau 2 : distance à l'arête la plus proche (centre sur route)
        if (selectedIdx === -1) {
            let minEdgeDist = Infinity;
            allBuildings.forEach((b, i) => {
                const d = _minEdgeDistGeo(this.centerLon, this.centerLat, b.coords);
                if (d < minEdgeDist) { minEdgeDist = d; selectedIdx = i; }
            });
            if (selectedIdx >= 0)
                console.log(`🏗️ Bâtiment PV sélectionné par distance bord (${minEdgeDist.toFixed(1)}m au centre)`);
        }

        const pvBuilding = selectedIdx >= 0 ? allBuildings[selectedIdx] : null;
        // Stocker les coordonnées géo du bâtiment PV pour le matching zone→pan
        this.pvBuildingCoords = pvBuilding ? pvBuilding.coords : null;
        console.log(`🏗️ Construction ${allBuildings.length} bâtiments (PV idx=${selectedIdx})...`);

        // Les voisins utilisent uniquement BD TOPO + LiDAR MNS (pas d'appel Google Solar)
        this._neighborSolarMap = {};

        // ═══════════════════════════════════════════════════════════════════
        // CONSTRUCTION 3D de TOUS les bâtiments
        // Ordre : PV principal en premier (priorité affichage + roofPanelsInfo)
        // puis tous les voisins
        // ═══════════════════════════════════════════════════════════════════
        let successCount = 0;

        // 1. Bâtiment PV principal
        if (pvBuilding) {
            try {
                await this._createBuilding3D(pvBuilding);
                successCount++;
            } catch(err) {
                console.warn(`⚠ Bâtiment PV échoué:`, err.message);
            }
        }

        // 2. Bâtiments voisins (tous sauf le PV)
        for (let i = 0; i < allBuildings.length; i++) {
            if (i === selectedIdx) continue;
            try {
                await this._createBuilding3D(allBuildings[i], i);
                successCount++;
            } catch(err) {
                console.warn(`⚠ Bâtiment voisin idx=${i} échoué:`, err.message);
            }
        }

        console.log(`✅ ${successCount}/${allBuildings.length} bâtiments créés`);
    }
    
    /**
     * Centre d'un polygone [lon, lat]
     */
    _polygonCenter(coords) {
        let x = 0, y = 0;
        coords.forEach(c => { x += c[0]; y += c[1]; });
        return { x: x / coords.length, y: y / coords.length };
    }
    
    /**
     * Calcule l'orientation et les dimensions du bâtiment depuis son polygone.
     * Retourne l'angle de l'axe principal, les dimensions long/court, et le centre.
     */
    _computeBuildingOrientation(localCoords) {
        // Trouver l'arête la plus longue du polygone = axe principal du bâtiment
        let maxLen = 0;
        let bestAngle = 0;
        
        for (let i = 0; i < localCoords.length; i++) {
            const j = (i + 1) % localCoords.length;
            const dx = localCoords[j].x - localCoords[i].x;
            const dz = localCoords[j].z - localCoords[i].z;
            const len = Math.sqrt(dx * dx + dz * dz);
            if (len > maxLen) {
                maxLen = len;
                bestAngle = Math.atan2(dz, dx);
            }
        }
        
        // Centroïde initial du polygone (pour la projection)
        const cxInit = localCoords.reduce((s, c) => s + c.x, 0) / localCoords.length;
        const czInit = localCoords.reduce((s, c) => s + c.z, 0) / localCoords.length;
        
        // Projeter tous les points sur le repère orienté pour les dimensions
        const cosA = Math.cos(-bestAngle);
        const sinA = Math.sin(-bestAngle);
        
        let minL = Infinity, maxL = -Infinity;
        let minS = Infinity, maxS = -Infinity;
        
        for (const c of localCoords) {
            const dx = c.x - cxInit;
            const dz = c.z - czInit;
            const projL = dx * cosA - dz * sinA; // le long de l'axe principal
            const projS = dx * sinA + dz * cosA; // perpendiculaire
            minL = Math.min(minL, projL);
            maxL = Math.max(maxL, projL);
            minS = Math.min(minS, projS);
            maxS = Math.max(maxS, projS);
        }
        
        // Centre VRAI de la boîte orientée (milieu des projections),
        // reconverti en coordonnées monde. C'est ce centre qui aligne
        // le toit OBB avec l'emprise réelle du polygone.
        const midL = (minL + maxL) / 2;
        const midS = (minS + maxS) / 2;
        const cosB = Math.cos(bestAngle);
        const sinB = Math.sin(bestAngle);
        const cx = cxInit + midL * cosB - midS * sinB;
        const cz = czInit + midL * sinB + midS * cosB;
        
        return {
            cx, cz,
            angle: bestAngle,
            longDim: Math.max(maxL - minL, 2),
            shortDim: Math.max(maxS - minS, 2),
        };
    }
    
    /**
     * Aire signée 2D d'un polygone (positif = sens antihoraire)
     */
    _signedArea2D(points) {
        let area = 0;
        for (let i = 0; i < points.length; i++) {
            const j = (i + 1) % points.length;
            area += points[i].x * points[j].y;
            area -= points[j].x * points[i].y;
        }
        return area / 2;
    }
    
    /**
     * Teste si un point (px, py) est dans un polygone 2D (ray casting)
     */
    _pointInPolygon2D(px, py, poly) {
        let inside = false;
        for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
            const xi = poly[i].x, yi = poly[i].y;
            const xj = poly[j].x, yj = poly[j].y;
            if (((yi > py) !== (yj > py)) && (px < (xj - xi) * (py - yi) / (yj - yi) + xi)) {
                inside = !inside;
            }
        }
        return inside;
    }
    
    /**
     * Échantillonne les altitudes MNS LiDAR sur l'emprise d'un bâtiment.
     * Retourne les points 3D du toit {x_local, z_local, altitude_mns, hauteur_mnh}
     * permettant de reconstituer la forme réelle du toit.
     */
    _sampleMNSOnBuilding(geoCoords, buildingIndex) {
        if (!this.lidarData || !this.lidarData.terrain || !this.lidarData.terrain.mns) return null;
        
        // ── Essayer d'abord la grille LiDAR HD (50cm) si disponible ──
        const hdData = this.lidarData.building_hd;
        if (hdData && hdData.building_index === buildingIndex) {
            const hdPoints = this._sampleFromHDGrid(geoCoords, hdData);
            if (hdPoints && hdPoints.length >= 4) {
                console.log(`✓ LiDAR HD sampling: ${hdPoints.length} pts à ${hdData.resolution}m/px`);
                return hdPoints;
            }
        }
        
        // ── Fallback : grille terrain WMS (1m) ──
        const terrain = this.lidarData.terrain;
        const mns = terrain.mns;
        const mnt = terrain.mnt;
        const mnh = terrain.mnh;
        const gridSize = terrain.grid_size;
        const bbox = terrain.bbox;
        
        // Polygone en coordonnées lat/lon
        const polyGeo = geoCoords.map(c => ({x: c[0], y: c[1]}));
        
        // Bounding box du bâtiment en lat/lon
        const lons = geoCoords.map(c => c[0]);
        const lats = geoCoords.map(c => c[1]);
        const bMinLon = Math.min(...lons), bMaxLon = Math.max(...lons);
        const bMinLat = Math.min(...lats), bMaxLat = Math.max(...lats);
        
        // Indices de grille correspondant au bbox du bâtiment
        const ixMin = Math.max(0, Math.floor((bMinLon - bbox.west) / (bbox.east - bbox.west) * gridSize));
        const ixMax = Math.min(gridSize - 1, Math.ceil((bMaxLon - bbox.west) / (bbox.east - bbox.west) * gridSize));
        const iyMin = Math.max(0, Math.floor((bbox.north - bMaxLat) / (bbox.north - bbox.south) * gridSize));
        const iyMax = Math.min(gridSize - 1, Math.ceil((bbox.north - bMinLat) / (bbox.north - bbox.south) * gridSize));
        
        const roofPoints = [];
        
        for (let iy = iyMin; iy <= iyMax; iy++) {
            for (let ix = ixMin; ix <= ixMax; ix++) {
                // Position géographique du pixel
                const pxLon = bbox.west + (ix + 0.5) / gridSize * (bbox.east - bbox.west);
                const pxLat = bbox.north - (iy + 0.5) / gridSize * (bbox.north - bbox.south);
                
                // Test d'inclusion dans le polygone du bâtiment
                if (!this._pointInPolygon2D(pxLon, pxLat, polyGeo)) continue;
                
                const mnhVal = mnh[iy] ? (mnh[iy][ix] || 0) : 0;
                if (mnhVal < 1.5) continue; // Pas sur un bâtiment (trop bas)
                
                const mnsVal = mns[iy] ? (mns[iy][ix] || 0) : 0;
                const mntVal = mnt[iy] ? (mnt[iy][ix] || 0) : 0;
                
                const local = this._geoToLocal(pxLat, pxLon);
                roofPoints.push({
                    x: local.x,
                    z: local.z,
                    mns: mnsVal,
                    mnt: mntVal,
                    mnh: mnhVal,
                });
            }
        }
        
        return roofPoints.length >= 4 ? roofPoints : null;
    }
    
    /**
     * Échantillonne les points MNS/MNT/MNH depuis la grille LiDAR HD (50cm)
     * retournée par l'API altimétrie IGN.
     * @param {Array} geoCoords - [[lon, lat], ...] polygone bâtiment
     * @param {Object} hdData - {mns, mnt, mnh, grid_w, grid_h, bbox, altitude_base}
     * @returns {Array|null} Points {x, z, mns, mnt, mnh}
     */
    _sampleFromHDGrid(geoCoords, hdData) {
        const { mns, mnt, mnh, grid_w, grid_h, bbox } = hdData;
        if (!mns || !mnt || !mnh) return null;
        
        const polyGeo = geoCoords.map(c => ({x: c[0], y: c[1]}));
        
        const roofPoints = [];
        for (let iy = 0; iy < grid_h; iy++) {
            if (!mns[iy] || !mnt[iy] || !mnh[iy]) continue;
            for (let ix = 0; ix < grid_w; ix++) {
                // Position géographique du pixel HD
                const pxLon = bbox.west + (ix + 0.5) / grid_w * (bbox.east - bbox.west);
                const pxLat = bbox.north - (iy + 0.5) / grid_h * (bbox.north - bbox.south);
                
                // Test d'inclusion dans le polygone du bâtiment
                if (!this._pointInPolygon2D(pxLon, pxLat, polyGeo)) continue;
                
                const mnhVal = mnh[iy][ix] || 0;
                if (mnhVal < 1.5) continue; // Pas sur un bâtiment
                
                const mnsVal = mns[iy][ix] || 0;
                const mntVal = mnt[iy][ix] || 0;
                
                const local = this._geoToLocal(pxLat, pxLon);
                roofPoints.push({
                    x: local.x,
                    z: local.z,
                    mns: mnsVal,
                    mnt: mntVal,
                    mnh: mnhVal,
                });
            }
        }
        
        return roofPoints.length >= 4 ? roofPoints : null;
    }
    
    /**
     * Analyse la forme du toit à partir des points MNS LiDAR échantillonnés.
     * Détecte :
     * - La ligne de faîtage (direction + position) via test bi-directionnel
     * - Le type de toit (gable/bi-pan, hip/4-pan, flat, mono-pente, multi-gable, multi-shed)
     * - La pente réelle et la hauteur du faîtage
     * - Les toitures dont le faîtage suit l'axe court (bâtiments plus larges que profonds)
     *
     * @param {Array} roofPoints - Points {x, z, mns, mnt, mnh}
     * @param {Object} obb - Oriented bounding box {cx, cz, angle, longDim, shortDim}
     * @returns {Object} Analyse du toit
     */
    _analyzeRoofShape(roofPoints, obb) {
        if (!roofPoints || roofPoints.length < 4) return null;
        
        const cx = obb.cx;
        const cz = obb.cz;
        
        // Altitudes toit relatives (MNS - base MNT moyen)
        const mntMean = roofPoints.reduce((s, p) => s + p.mnt, 0) / roofPoints.length;
        const relativeH = roofPoints.map(p => p.mns - mntMean);
        
        let hMin = Infinity, hMax = -Infinity;
        for (let i = 0; i < relativeH.length; i++) {
            if (relativeH[i] < hMin) hMin = relativeH[i];
            if (relativeH[i] > hMax) hMax = relativeH[i];
        }
        const hRange = hMax - hMin;
        
        if (hRange < 0.3) {
            return { type: 'flat', ridgeExtra: 0 };
        }
        
        // ═══════════════════════════════════════════════════════════
        // HELPER : Construire et scorer un profil transversal pour une direction donnée
        // ═══════════════════════════════════════════════════════════
        const buildProfile = (angle) => {
            const cosA = Math.cos(-angle);
            const sinA = Math.sin(-angle);
            
            const projected = roofPoints.map((p, i) => {
                const dx = p.x - cx;
                const dz = p.z - cz;
                return {
                    along: dx * cosA - dz * sinA,
                    across: dx * sinA + dz * cosA,
                    h: relativeH[i],
                };
            });
            
            // Profil transversal adaptatif : ~1 bande par 1.2m pour détecter multi-sections
            // Un bâtiment de 42m → ~35 bandes (vs 11 avant) : résolution suffisante pour 7 sections
            let acrossMin = Infinity, acrossMax = -Infinity;
            for (let i = 0; i < projected.length; i++) {
                if (projected[i].across < acrossMin) acrossMin = projected[i].across;
                if (projected[i].across > acrossMax) acrossMax = projected[i].across;
            }
            const acrossRange = acrossMax - acrossMin;
            
            if (acrossRange < 0.5) return null;
            
            const nBands = Math.max(15, Math.min(50, Math.round(acrossRange / 1.2)));
            
            const profile = [];
            for (let b = 0; b < nBands; b++) {
                const bStart = acrossMin + (b / nBands) * acrossRange;
                const bEnd = acrossMin + ((b + 1) / nBands) * acrossRange;
                const bandPts = projected.filter(p => p.across >= bStart && p.across < bEnd);
                if (bandPts.length > 0) {
                    // Utiliser le 85e percentile au lieu de la moyenne
                    // pour réduire l'impact du bruit LiDAR (retours sol près des bords)
                    const sorted = bandPts.map(p => p.h).sort((a, b) => a - b);
                    const pctIdx = Math.min(Math.floor(sorted.length * 0.85), sorted.length - 1);
                    const robustH = sorted[pctIdx];
                    const meanAcross = (bStart + bEnd) / 2;
                    profile.push({
                        pos: (meanAcross - acrossMin) / acrossRange,
                        h: robustH,
                        rawAcross: meanAcross
                    });
                }
            }
            
            if (profile.length < 3) return null;
            
            // ── Lisser le profil pour réduire le bruit LiDAR ──
            const smoothH = profile.map((p, i) => {
                if (i === 0 || i === profile.length - 1) return p.h;
                return (profile[i - 1].h + 2 * p.h + profile[i + 1].h) / 4;
            });
            
            // ── Trouver le pic global ──
            let maxProfileH = -Infinity, maxIdx = 0;
            smoothH.forEach((h, i) => {
                if (h > maxProfileH) { maxProfileH = h; maxIdx = i; }
            });
            
            const ridgePos = profile[maxIdx].pos;
            const edgeH = (smoothH[0] + smoothH[smoothH.length - 1]) / 2;
            const ridgeExtra = Math.max(0, maxProfileH - edgeH);
            
            // Si le profil est essentiellement plat, retourner directement
            if (ridgeExtra < 0.2) {
                return {
                    profile, projected, ridgePos, ridgeExtra,
                    ridgeOffset: ridgePos - 0.5, acrossRange,
                    score: ridgeExtra * 0.1,
                    leftDrop: 0, rightDrop: 0,
                    bestN: 1, bestModel: 'gable', bestR2: 0,
                    sawtoothScore: 0, nDetectedRidges: 1
                };
            }
            
            // ═══════════════════════════════════════════════════════════
            // AJUSTEMENT TRIGONOMÉTRIQUE : tester N=1..maxN
            // ═══════════════════════════════════════════════════════════
            // Positions normalisées [0, 1] et hauteurs lissées
            const xs = profile.map(p => p.pos);
            const ys = smoothH.slice();
            const n = xs.length;
            
            // Moyenne et variance totale de y (pour calcul R²)
            const yMean = ys.reduce((s, y) => s + y, 0) / n;
            const ssTot = ys.reduce((s, y) => s + (y - yMean) ** 2, 0);
            
            if (ssTot < 0.001) {
                return {
                    profile, projected, ridgePos, ridgeExtra,
                    ridgeOffset: ridgePos - 0.5, acrossRange,
                    score: ridgeExtra * 0.1,
                    leftDrop: 0, rightDrop: 0,
                    bestN: 1, bestModel: 'gable', bestR2: 0,
                    sawtoothScore: 0, nDetectedRidges: 1
                };
            }
            
            // ── Fonctions modèles ──
            // Triangle wave (multi-gable) : /\/\/\ avec N pics
            // Pour N sections, chaque section a un pic au centre
            const triangleWave = (x, N) => {
                const xn = ((x * N) % 1 + 1) % 1; // position dans la section [0,1]
                return 1 - Math.abs(2 * xn - 1);   // 0 aux bords, 1 au centre
            };
            
            // Sawtooth wave (multi-shed) : /|/|/| avec N sections
            const sawtoothWave = (x, N) => {
                return ((x * N) % 1 + 1) % 1; // rampe 0→1 dans chaque section
            };
            
            // ── Régression linéaire y = a*model(x) + b ──
            // Minimise sum((yi - a*mi - b)²) → a et b analytiques
            const fitModel = (modelFunc, N) => {
                let sumM = 0, sumY = 0, sumMY = 0, sumM2 = 0;
                for (let i = 0; i < n; i++) {
                    const m = modelFunc(xs[i], N);
                    sumM += m;
                    sumY += ys[i];
                    sumMY += m * ys[i];
                    sumM2 += m * m;
                }
                const denom = n * sumM2 - sumM * sumM;
                if (Math.abs(denom) < 1e-10) return { a: 0, b: yMean, r2: 0, ssRes: ssTot };
                
                const a = (n * sumMY - sumM * sumY) / denom;
                const b = (sumY - a * sumM) / n;
                
                let ssRes = 0;
                for (let i = 0; i < n; i++) {
                    const predicted = a * modelFunc(xs[i], N) + b;
                    ssRes += (ys[i] - predicted) ** 2;
                }
                const r2 = 1 - ssRes / ssTot;
                return { a, b, r2, ssRes };
            };
            
            // ── Tester N = 1 à maxN pour chaque modèle ──
            // maxN limité par la résolution du profil (au moins 3 bandes par section)
            const maxN = Math.min(12, Math.max(1, Math.floor(profile.length / 3)));
            
            let bestGable = { N: 1, r2: -1, a: 0, b: 0 };
            let bestShed = { N: 1, r2: -1, a: 0, b: 0 };
            
            for (let N = 1; N <= maxN; N++) {
                // Tester avec décalage de phase pour le triangle (le faîtage n'est pas
                // forcément à x=0.5/N)
                // On teste 3 phases : 0, 0.25/N, 0.5/N
                for (const phase of [0, 0.25 / N, 0.5 / N]) {
                    const gableFit = fitModel((x, nn) => triangleWave(x + phase, nn), N);
                    if (gableFit.r2 > bestGable.r2 && gableFit.a > 0) {
                        bestGable = { N, r2: gableFit.r2, a: gableFit.a, b: gableFit.b, phase };
                    }
                }
                
                // Shed : tester aussi la phase inverse (descente au lieu de montée)
                const shedFit = fitModel(sawtoothWave, N);
                const shedFitInv = fitModel((x, nn) => 1 - sawtoothWave(x, nn), N);
                const bestShedFit = shedFit.r2 > shedFitInv.r2 ? shedFit : shedFitInv;
                if (bestShedFit.r2 > bestShed.r2 && Math.abs(bestShedFit.a) > 0) {
                    bestShed = { N, r2: bestShedFit.r2, a: bestShedFit.a, b: bestShedFit.b };
                }
            }
            
            // ── Pénalité de complexité (BIC-like) ──
            // Éviter de surajuster avec trop de sections
            // Ajuster R² par une pénalité logarithmique : R²_adj = R² - penalty * log(N)
            const penalty = 0.03;
            const adjGableR2 = bestGable.r2 - penalty * Math.log(bestGable.N);
            const adjShedR2 = bestShed.r2 - penalty * Math.log(bestShed.N);
            
            // ── Déterminer le meilleur modèle ──
            let bestN, bestModel, bestR2;
            if (adjGableR2 >= adjShedR2) {
                bestN = bestGable.N;
                bestModel = bestN >= 2 ? 'multi-gable' : 'gable';
                bestR2 = bestGable.r2;
            } else {
                bestN = bestShed.N;
                bestModel = bestN >= 2 ? 'multi-shed' : 'shed';
                bestR2 = bestShed.r2;
            }
            
            // Vérifier que le N>1 apporte un gain significatif par rapport à N=1
            const fitN1 = fitModel(triangleWave, 1);
            const r2Gain = bestR2 - fitN1.r2;
            if (bestN >= 2 && r2Gain < 0.05) {
                // Le multi-section n'apporte pas assez → revenir à N=1
                bestN = 1;
                bestModel = 'gable';
                bestR2 = fitN1.r2;
            }
            
            // sawtoothScore basé sur le ratio R²(shed) / R²(gable)
            const sawtoothScore = (bestShed.r2 > 0 && bestGable.r2 > 0) 
                ? Math.max(0, bestShed.r2 - bestGable.r2) * 3 
                : 0;
            
            console.log(`📊 Profil [${(angle * 180 / Math.PI).toFixed(0)}°]: ${profile.length} bandes, across=${acrossRange.toFixed(1)}m, ridgeExtra=${ridgeExtra.toFixed(2)}m`);
            console.log(`   📐 Gable: bestN=${bestGable.N}, R²=${bestGable.r2.toFixed(3)}, A=${bestGable.a.toFixed(2)}`);
            console.log(`   📐 Shed:  bestN=${bestShed.N}, R²=${bestShed.r2.toFixed(3)}, A=${bestShed.a.toFixed(2)}`);
            console.log(`   ✅ Choix: ${bestModel} N=${bestN}, R²=${bestR2.toFixed(3)}, gain=${r2Gain.toFixed(3)}`);
            
            // ── Score de qualité du profil en tant que faîtage ──
            const leftDrop = maxProfileH - smoothH[0];
            const rightDrop = maxProfileH - smoothH[smoothH.length - 1];
            const symmetry = 1 - Math.abs(leftDrop - rightDrop) / Math.max(leftDrop + rightDrop, 0.1);
            const centeredness = 1 - Math.abs(ridgePos - 0.5) * 2;
            const contrast = ridgeExtra / Math.max(acrossRange * 0.08, 0.3);
            
            // Score composite : favorise les profils avec pic haut, centré, symétrique
            const score = ridgeExtra * (0.4 + 0.3 * symmetry + 0.2 * centeredness + 0.1 * Math.min(contrast, 2));
            
            return {
                profile,
                projected,
                ridgePos,
                ridgeExtra,
                ridgeOffset: ridgePos - 0.5,
                acrossRange,
                score,
                leftDrop,
                rightDrop,
                bestN,
                bestModel,
                bestR2,
                sawtoothScore,
                nDetectedRidges: bestN
            };
        };
        
        // ═══════════════════════════════════════════════════════════
        // TEST BI-DIRECTIONNEL : faîtage le long de longDim OU shortDim
        // ═══════════════════════════════════════════════════════════
        const dir1 = buildProfile(obb.angle);                    // faîtage le long de longDim (défaut)
        const dir2 = buildProfile(obb.angle + Math.PI / 2);      // faîtage le long de shortDim
        
        // Choisir la direction avec le meilleur profil de faîtage
        let bestDir, ridgeAlongShort = false;
        
        if (!dir1 && !dir2) return { type: 'flat', ridgeExtra: 0 };
        if (!dir1) { bestDir = dir2; ridgeAlongShort = true; }
        else if (!dir2) { bestDir = dir1; }
        else {
            // Comparer les scores : la direction avec le profil transversal le plus net l'emporte
            // Marge de 15% pour préférer la direction par défaut (longDim) en cas d'ambiguïté
            if (dir2.score > dir1.score * 1.15) {
                bestDir = dir2;
                ridgeAlongShort = true;
                console.log(`🔄 Faîtage détecté le long de l'axe court (score ${dir2.score.toFixed(2)} vs ${dir1.score.toFixed(2)})`);
            } else {
                bestDir = dir1;
            }
        }
        
        if (bestDir.ridgeExtra < 0.3) return { type: 'flat', ridgeExtra: 0 };
        
        // let (pas const) car la méthode bbox peut corriger le sens du faîtage
        let { projected, ridgePos, ridgeExtra, ridgeOffset, bestN, bestModel, bestR2, sawtoothScore, nDetectedRidges, acrossRange } = bestDir;
        
        // ═══════════════════════════════════════════════════════════
        // DÉTECTION DU TYPE DE TOIT
        // ═══════════════════════════════════════════════════════════
        let roofType;
        let nRidges = 1;
        
        // ── Type de toit déterminé par ajustement trigonométrique ──
        // bestModel déjà calculé dans buildProfile (gable, multi-gable, shed, multi-shed)
        // Mais on doit encore vérifier hip vs gable pour N=1
        if (bestN >= 2 && bestR2 > 0.3) {
            // Multi-faîtage confirmé par R² > 0.3
            nRidges = bestN;
            if (bestModel === 'multi-shed' || sawtoothScore > 0.15) {
                roofType = 'multi-shed';
                console.log(`🏭 Multi-shed confirmé : ${nRidges} sections, R²=${bestR2.toFixed(3)}`);
            } else {
                roofType = 'multi-gable';
                console.log(`🏠 Multi-gable confirmé : ${nRidges} faîtages, R²=${bestR2.toFixed(3)}`);
            }
        }
        
        if (!roofType && Math.abs(ridgeOffset) > 0.38) {
            // ── Mono-pente (shed) ──
            // Le pic doit être très proche d'un bord (offset > 0.38 → pic à pos > 0.88 ou < 0.12)
            // ET le profil doit être strictement monotone (pas de creux/bosses)
            const prof = bestDir.profile;
            let monotoneRise = 0, monotoneFall = 0;
            for (let i = 1; i < prof.length; i++) {
                // Tolérance réduite : seulement le bruit LiDAR réel (~5cm), pas 10cm
                if (prof[i].h >= prof[i - 1].h - 0.05) monotoneRise++;
                if (prof[i].h <= prof[i - 1].h + 0.05) monotoneFall++;
            }
            const totalSteps = prof.length - 1;
            // Exiger 85% de monotonie (plus strict que 75%)
            const isMonotone = (monotoneRise / totalSteps > 0.85) || (monotoneFall / totalSteps > 0.85);
            
            // Vérification supplémentaire : le R² du modèle shed doit être bon
            const shedFitGood = bestDir.sawtoothScore > 0.05 || 
                (bestDir.bestModel === 'shed' && bestDir.bestR2 > 0.5);
            
            if (isMonotone && shedFitGood) {
                roofType = 'shed';
                console.log(`🏠 Shed confirmé: offset=${ridgeOffset.toFixed(2)}, monotone=${(Math.max(monotoneRise, monotoneFall) / totalSteps * 100).toFixed(0)}%, R²=${bestDir.bestR2?.toFixed(3)}`);
            } else {
                // Pic décalé mais pas vraiment monotone → gable asymétrique
                roofType = 'gable';
                console.log(`🏠 Gable asymétrique détecté (offset=${ridgeOffset.toFixed(2)}, monotone=${(Math.max(monotoneRise, monotoneFall) / totalSteps * 100).toFixed(0)}%, shedFitGood=${shedFitGood})`);
            }
        } else if (!roofType) {
            // ═══════════════════════════════════════════════════════════
            // DÉTECTION GABLE vs HIP : 3 tests indépendants
            //
            // 1) CONSTANCE DU FAÎTAGE : hauteur max le long du bâtiment
            //    Gable = faîtage constant d'un bout à l'autre
            //    Hip = faîtage qui chute aux extrémités (croupes)
            //
            // 2) FIT BBOX ÷2 vs ÷4 dans les 2 sens
            //    Le bon sens = celui où ÷2 donne le meilleur fit
            //    Hip si ÷4 améliore significativement vs ÷2
            //
            // 3) Vote majoritaire : au moins 2/3 signaux hip pour confirmer
            // ═══════════════════════════════════════════════════════════
            
            let hipVotes = 0;
            let gableVotes = 0;
            
            // ── TEST 1 : Constance du faîtage le long du bâtiment ──
            // Pour chaque direction, on prend les points proches du faîtage
            // et on regarde si leur hauteur est stable le long du bâtiment
            const testRidgeConstancy = (dirData, label) => {
                if (!dirData || !dirData.projected || !dirData.profile) return null;
                const proj = dirData.projected;
                
                let cMin = Infinity, cMax = -Infinity;
                let aMin = Infinity, aMax = -Infinity;
                for (const p of proj) {
                    if (p.across < cMin) cMin = p.across;
                    if (p.across > cMax) cMax = p.across;
                    if (p.along < aMin) aMin = p.along;
                    if (p.along > aMax) aMax = p.along;
                }
                const cRange = cMax - cMin;
                const aRange = aMax - aMin;
                if (cRange < 1 || aRange < 2) return null;
                
                // Zone du faîtage : bande de ±15% autour de la position ridge
                const ridgeAcross = cMin + dirData.ridgePos * cRange;
                const ridgeBandWidth = cRange * 0.15;
                const ridgePts = proj.filter(p => 
                    Math.abs(p.across - ridgeAcross) < ridgeBandWidth
                );
                
                if (ridgePts.length < 6) return null;
                
                // Diviser le faîtage en bandes le long du bâtiment
                const nBands = Math.max(5, Math.min(12, Math.round(aRange / 1.5)));
                const bandMaxH = [];
                for (let b = 0; b < nBands; b++) {
                    const bStart = aMin + (b / nBands) * aRange;
                    const bEnd = aMin + ((b + 1) / nBands) * aRange;
                    const bandPts = ridgePts.filter(p => p.along >= bStart && p.along < bEnd);
                    if (bandPts.length >= 2) {
                        // Prendre le 85e percentile pour robustesse
                        const sorted = bandPts.map(p => p.h).sort((a, b) => a - b);
                        const idx85 = Math.min(Math.floor(sorted.length * 0.85), sorted.length - 1);
                        bandMaxH.push({ pos: (b + 0.5) / nBands, h: sorted[idx85], n: bandPts.length });
                    }
                }
                
                if (bandMaxH.length < 4) return null;
                
                // Hauteur du faîtage au centre (bands centrales, 30%-70%)
                const centerBands = bandMaxH.filter(b => b.pos > 0.3 && b.pos < 0.7);
                const endBandsLeft = bandMaxH.filter(b => b.pos < 0.2);
                const endBandsRight = bandMaxH.filter(b => b.pos > 0.8);
                
                if (centerBands.length < 1 || (endBandsLeft.length < 1 && endBandsRight.length < 1)) return null;
                
                const centerH = centerBands.reduce((s, b) => s + b.h, 0) / centerBands.length;
                const leftH = endBandsLeft.length > 0 
                    ? endBandsLeft.reduce((s, b) => s + b.h, 0) / endBandsLeft.length 
                    : centerH;
                const rightH = endBandsRight.length > 0
                    ? endBandsRight.reduce((s, b) => s + b.h, 0) / endBandsRight.length
                    : centerH;
                
                const dropLeft = centerH - leftH;
                const dropRight = centerH - rightH;
                const maxDrop = Math.max(dropLeft, dropRight);
                const minDrop = Math.min(dropLeft, dropRight);
                
                // Coefficient de variation de la hauteur du faîtage
                const allH = bandMaxH.map(b => b.h);
                const meanH = allH.reduce((s, h) => s + h, 0) / allH.length;
                const stdH = Math.sqrt(allH.reduce((s, h) => s + (h - meanH) ** 2, 0) / allH.length);
                const cv = meanH > 0 ? stdH / meanH : 0;
                
                console.log(`📏 ${label} faîtage: centre=${centerH.toFixed(2)}m, gauche=${leftH.toFixed(2)}m, droite=${rightH.toFixed(2)}m`);
                console.log(`   chute gauche=${dropLeft.toFixed(2)}m, droite=${dropRight.toFixed(2)}m, CV=${(cv * 100).toFixed(1)}%`);
                
                return { centerH, leftH, rightH, dropLeft, dropRight, maxDrop, minDrop, cv, label };
            };
            
            const ridge1 = testRidgeConstancy(dir1, 'longDim');
            const ridge2 = testRidgeConstancy(dir2, 'shortDim');
            
            // Choisir la direction de faîtage via lequel le ridge est le plus haut
            // (le vrai faîtage est toujours la ligne la plus haute)
            let ridgeTest = null;
            if (ridge1 && ridge2) {
                ridgeTest = ridge1.centerH >= ridge2.centerH ? ridge1 : ridge2;
            } else {
                ridgeTest = ridge1 || ridge2;
            }
            
            if (ridgeTest) {
                // Hip = chute significative aux DEUX extrémités
                // Seuils : > 1.0m absolu ET > 30% du ridgeExtra
                const hipDropThreshold = Math.max(1.0, ridgeExtra * 0.30);
                
                if (ridgeTest.minDrop > hipDropThreshold) {
                    // Les DEUX côtés chutent → hip
                    hipVotes++;
                    console.log(`✅ Test faîtage → HIP (les 2 côtés chutent > ${hipDropThreshold.toFixed(1)}m)`);
                } else if (ridgeTest.maxDrop > hipDropThreshold * 1.5 && ridgeTest.minDrop > hipDropThreshold * 0.5) {
                    // Un côté chute beaucoup, l'autre un peu → hip partiel
                    hipVotes++;
                    console.log(`✅ Test faîtage → HIP partiel (maxDrop=${ridgeTest.maxDrop.toFixed(1)}m)`);
                } else {
                    gableVotes++;
                    console.log(`✅ Test faîtage → GABLE (chutes faibles: ${ridgeTest.maxDrop.toFixed(2)}m < seuil ${hipDropThreshold.toFixed(1)}m)`);
                }
                
                // CV très bas = faîtage ultra-constant → gable supplémentaire
                if (ridgeTest.cv < 0.03) {
                    gableVotes++;
                    console.log(`✅ Test CV → GABLE (CV=${(ridgeTest.cv * 100).toFixed(1)}% < 3%)`);
                }
            }
            
            // ── TEST 2 : Fit plan ÷2 vs ÷4 dans les 2 sens ──
            const fitPlane = (pts) => {
                const n = pts.length;
                if (n < 4) return { residualVar: Infinity, n: n };
                
                let sX = 0, sY = 0, sZ = 0;
                let sXX = 0, sXY = 0, sXZ = 0, sYY = 0, sYZ = 0;
                for (const p of pts) {
                    sX += p.across; sY += p.along; sZ += p.h;
                    sXX += p.across * p.across;
                    sXY += p.across * p.along;
                    sXZ += p.across * p.h;
                    sYY += p.along * p.along;
                    sYZ += p.along * p.h;
                }
                const det3 = (m) =>
                    m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
                  - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
                  + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
                const M = [[sXX, sXY, sX], [sXY, sYY, sY], [sX, sY, n]];
                const D = det3(M);
                if (Math.abs(D) < 1e-10) return { residualVar: Infinity, n: n };
                const rhs = [sXZ, sYZ, sZ];
                const a = det3([[rhs[0], M[0][1], M[0][2]], [rhs[1], M[1][1], M[1][2]], [rhs[2], M[2][1], M[2][2]]]) / D;
                const b = det3([[M[0][0], rhs[0], M[0][2]], [M[1][0], rhs[1], M[1][2]], [M[2][0], rhs[2], M[2][2]]]) / D;
                const c = det3([[M[0][0], M[0][1], rhs[0]], [M[1][0], M[1][1], rhs[1]], [M[2][0], M[2][1], rhs[2]]]) / D;
                let ssRes = 0;
                for (const p of pts) {
                    const pred = a * p.across + b * p.along + c;
                    ssRes += (p.h - pred) ** 2;
                }
                return { a, b, c, residualVar: ssRes / n, n: n };
            };
            
            const analyzeBboxDirection = (dirData, label) => {
                if (!dirData || !dirData.projected) return null;
                const proj = dirData.projected;
                let aMin = Infinity, aMax = -Infinity;
                let cMin = Infinity, cMax = -Infinity;
                for (const p of proj) {
                    if (p.along < aMin) aMin = p.along;
                    if (p.along > aMax) aMax = p.along;
                    if (p.across < cMin) cMin = p.across;
                    if (p.across > cMax) cMax = p.across;
                }
                const aRange = aMax - aMin;
                const cRange = cMax - cMin;
                if (aRange < 1 || cRange < 1) return null;
                
                const ridgeCut = cMin + dirData.ridgePos * cRange;
                const alongMid = (aMin + aMax) / 2;
                const totalN = proj.length;
                
                const h1 = proj.filter(p => p.across <= ridgeCut);
                const h2 = proj.filter(p => p.across > ridgeCut);
                const f2a = fitPlane(h1);
                const f2b = fitPlane(h2);
                const var2 = (f2a.residualVar * h1.length + f2b.residualVar * h2.length) / totalN;
                
                const q1 = proj.filter(p => p.across <= ridgeCut && p.along <= alongMid);
                const q2 = proj.filter(p => p.across >  ridgeCut && p.along <= alongMid);
                const q3 = proj.filter(p => p.across <= ridgeCut && p.along >  alongMid);
                const q4 = proj.filter(p => p.across >  ridgeCut && p.along >  alongMid);
                const f4a = fitPlane(q1);
                const f4b = fitPlane(q2);
                const f4c = fitPlane(q3);
                const f4d = fitPlane(q4);
                const var4 = (f4a.residualVar * q1.length + f4b.residualVar * q2.length
                            + f4c.residualVar * q3.length + f4d.residualVar * q4.length) / totalN;
                
                const improvement = var2 > 1e-6 ? (var2 - var4) / var2 : 0;
                const minQPts = Math.min(q1.length, q2.length, q3.length, q4.length);
                
                console.log(`📐 ${label}: Var(÷2)=${var2.toFixed(4)}, Var(÷4)=${var4.toFixed(4)}, amélio=${(improvement * 100).toFixed(1)}%`);
                return { var2, var4, improvement, minQPts, label };
            };
            
            const bboxDir1 = analyzeBboxDirection(dir1, 'Faîtage→longDim');
            const bboxDir2 = analyzeBboxDirection(dir2, 'Faîtage→shortDim');
            
            // Choisir le meilleur sens (÷2 le plus bas)
            let chosenBbox = null;
            let bboxRidgeAlongShort = false;
            if (bboxDir1 && bboxDir2) {
                if (bboxDir2.var2 < bboxDir1.var2 * 0.85) {
                    chosenBbox = bboxDir2;
                    bboxRidgeAlongShort = true;
                } else {
                    chosenBbox = bboxDir1;
                }
            } else {
                chosenBbox = bboxDir1 || bboxDir2;
                if (chosenBbox === bboxDir2) bboxRidgeAlongShort = true;
            }
            
            if (chosenBbox) {
                // IMPORTANT: ne voter hip que si :
                // 1) L'amélioration est forte (>30%)
                // 2) La Var(÷2) est assez grande (pas juste du bruit)
                //    Var(÷2) < 0.05 signifie que ÷2 fitte déjà très bien → gable
                // 3) Assez de points par quadrant
                const var2IsSignificant = chosenBbox.var2 > 0.05;
                
                if (chosenBbox.improvement > 0.30 && var2IsSignificant && chosenBbox.minQPts >= 3) {
                    hipVotes++;
                    console.log(`✅ Test bbox → HIP (amélio=${(chosenBbox.improvement * 100).toFixed(1)}%, Var2=${chosenBbox.var2.toFixed(4)})`);
                } else {
                    gableVotes++;
                    if (!var2IsSignificant) {
                        console.log(`✅ Test bbox → GABLE (Var2=${chosenBbox.var2.toFixed(4)} déjà très faible = 2 plans purs)`);
                    } else {
                        console.log(`✅ Test bbox → GABLE (amélio=${(chosenBbox.improvement * 100).toFixed(1)}% < 30%)`);
                    }
                }
            }
            
            // ── Corriger le sens du faîtage si bbox dit le contraire ──
            if (chosenBbox && bboxRidgeAlongShort !== ridgeAlongShort) {
                console.log(`⚠️ Bbox corrige le sens du faîtage : ${ridgeAlongShort ? 'short' : 'long'}Dim → ${bboxRidgeAlongShort ? 'short' : 'long'}Dim`);
                ridgeAlongShort = bboxRidgeAlongShort;
                if (bboxRidgeAlongShort && dir2) {
                    bestDir = dir2;
                } else if (!bboxRidgeAlongShort && dir1) {
                    bestDir = dir1;
                }
                ({ projected, ridgePos, ridgeExtra, ridgeOffset, bestN, bestModel, bestR2, sawtoothScore, nDetectedRidges, acrossRange } = bestDir);
            }
            
            // ── VOTE FINAL ──
            console.log(`🗳️ Votes: hip=${hipVotes}, gable=${gableVotes}`);
            if (hipVotes >= 2 && hipVotes > gableVotes) {
                roofType = 'hip';
                console.log(`🏠 ➜ HIP (4 pans) — ${hipVotes} votes hip vs ${gableVotes} gable`);
            } else {
                roofType = 'gable';
                console.log(`🏠 ➜ GABLE (2 pans) — ${gableVotes} votes gable vs ${hipVotes} hip`);
            }
        }
        
        // Pente réelle (angle en degrés) depuis le bord au faîtage
        const halfWidth = (ridgeAlongShort ? obb.longDim : obb.shortDim) / 2;
        const slopeDeg = Math.atan2(ridgeExtra, halfWidth) * 180 / Math.PI;
        
        return {
            type: roofType,
            ridgeExtra: ridgeExtra,
            ridgeOffset: ridgeOffset,
            slopeDeg: slopeDeg,
            hMin: hMin,
            hMax: hMax,
            ridgeAlongShort: ridgeAlongShort,
            nRidges: nRidges,
            bestR2: bestR2,
            bestModel: bestModel,
            profile: bestDir ? bestDir.profile : null,
            acrossRange: bestDir ? bestDir.acrossRange : 0,
        };
    }
    
    /**
     * Crée un bâtiment 3D depuis ses données.
     * Utilise l'emprise polygonale réelle (ExtrudeGeometry) avec fallback BoxGeometry orientée.
     * Toit bi-pan (gable) par défaut pour les bâtiments résidentiels.
     */
    async _createBuilding3D(buildingData, neighborIdx = null) {
        const coords = buildingData.coords;
        if (!coords || coords.length < 3) return;
        
        // Utiliser la hauteur de mur/corniche pour extrusion
        const height = buildingData.height_eave || buildingData.height || 6;
        
        // Convertir toutes les coordonnées en espace local 3D
        let localCoords = coords.map(c => this._geoToLocal(c[1], c[0]));
        
        // Supprimer le point de fermeture s'il duplique le premier
        if (localCoords.length > 3) {
            const first = localCoords[0], last = localCoords[localCoords.length - 1];
            if (Math.abs(first.x - last.x) < 0.01 && Math.abs(first.z - last.z) < 0.01) {
                localCoords.pop();
            }
        }
        if (localCoords.length < 3) return;
        
        // Calculer l'orientation et les dimensions orientées du bâtiment
        let obb = this._computeBuildingOrientation(localCoords);
        
        // Échantillonner la hauteur du terrain à plusieurs points (centre + coins)
        // pour éviter que les bâtiments s'enfoncent sous le relief
        const terrainSamples = [this._getTerrainHeight(obb.cx, obb.cz)];
        const cosObb = Math.cos(obb.angle);
        const sinObb = Math.sin(obb.angle);
        const hlObb = obb.longDim / 2;
        const hsObb = obb.shortDim / 2;
        for (const [rl, rs] of [[-hlObb,-hsObb],[hlObb,-hsObb],[hlObb,hsObb],[-hlObb,hsObb]]) {
            const cx2 = obb.cx + rl * cosObb - rs * sinObb;
            const cz2 = obb.cz + rl * sinObb + rs * cosObb;
            terrainSamples.push(this._getTerrainHeight(cx2, cz2));
        }
        const terrainH = Math.max(...terrainSamples);
        
        const bh = Math.max(height, 2);
        const wallType = this._getWallType(buildingData);
        const roofType = this._getRoofType(buildingData);

        // Mémoriser les paramètres du bâtiment principal (sans voisin)
        // pour permettre l'injection ultérieure des toits Solar depuis la heatmap.
        if (neighborIdx === null) {
            this._mainBldgTerrainH  = terrainH;
            this._mainBldgBh        = bh;
            this._mainBldgRoofType  = roofType;
        }
        
        // === Méthode 1 : ExtrudeGeometry depuis l'emprise polygonale réelle ===
        let mesh = null;
        try {
            // THREE.Shape: x = local.x, y = -local.z (compensé par rotateX(-π/2))
            const shapeCoords = localCoords.map(c => ({x: c.x, y: -c.z}));
            
            // Vérifier le sens d'enroulement (THREE.Shape attend antihoraire)
            if (this._signedArea2D(shapeCoords) < 0) {
                shapeCoords.reverse();
            }
            
            const shape = new THREE.Shape();
            shape.moveTo(shapeCoords[0].x, shapeCoords[0].y);
            for (let i = 1; i < shapeCoords.length; i++) {
                shape.lineTo(shapeCoords[i].x, shapeCoords[i].y);
            }
            shape.closePath();
            
            const geo = new THREE.ExtrudeGeometry(shape, {
                steps: 1,
                depth: bh,
                bevelEnabled: false,
            });
            
            // Rotation pour que l'extrusion monte le long de Y (haut)
            geo.rotateX(-Math.PI / 2);
            
            // Materials: group 0 = caps (haut/bas), group 1 = murs latéraux
            const wallColorMap = {
                plaster: 0xE8DCC8, brick: 0xB5651D, stone: 0xA09080,
                concrete: 0xB0B0B0, industrial: 0x888888, commercial: 0xD0D0D0
            };
            // Couleur du toit plat selon matériau
            const roofCapColorMap = {
                tuile: 0xC8824A, ardoise: 0x708090, zinc: 0x8FA8A0,
                metal: 0x9AAAB0, bac_acier: 0x8FA8A0, membrane: 0xB0B0A8,
                gravier: 0xA8A090, beton: 0xB4B0A8, unknown: 0xB0A898
            };
            const capMat = new THREE.MeshPhongMaterial({
                color: roofCapColorMap[roofType] || 0xB0A898,
                specular: 0x111111,
                shininess: roofType === 'zinc' || roofType === 'metal' ? 20 : 3,
                transparent: false,
                opacity: 1.0,
                depthWrite: true
            });
            const wallMat = new THREE.MeshPhongMaterial({
                color: wallColorMap[wallType] || 0xE8DCC8,
                specular: 0x111111,
                shininess: 5,
            });
            
            mesh = new THREE.Mesh(geo, [capMat, wallMat]);
            mesh.position.set(0, terrainH, 0);
        } catch(err) {
            console.warn('⚠ ExtrudeGeometry fallback pour bâtiment:', err.message);
            mesh = null;
        }
        
        // === Fallback : BoxGeometry orientée selon l'axe principal ===
        if (!mesh) {
            const bx = obb.longDim;
            const bz = obb.shortDim;
            const geo = new THREE.BoxGeometry(bx, bh, bz);
            
            const facadeTex = this._getFacadeTexture(wallType, bx, bh, bz);
            const facadeTexSide = this._getFacadeTexture(wallType, bz, bh, bx);
            const facadeMat = new THREE.MeshPhongMaterial({ map: facadeTex, specular: 0x111111, shininess: 5 });
            const facadeMatSide = new THREE.MeshPhongMaterial({ map: facadeTexSide, specular: 0x111111, shininess: 5 });
            const topMat = new THREE.MeshLambertMaterial({ color: 0x888888 });
            const bottomMat = new THREE.MeshLambertMaterial({ color: 0x555555 });
            
            mesh = new THREE.Mesh(geo, [facadeMatSide, facadeMatSide, topMat, bottomMat, facadeMat, facadeMat]);
            mesh.position.set(obb.cx, terrainH + bh / 2, obb.cz);
            mesh.rotation.y = -obb.angle;
        }
        
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.userData = {
            isMainBuilding: neighborIdx === null,
            originalHeight: bh
        };
        this.scene.add(mesh);
        this.buildings.push(mesh);

        // === Toit : LiDAR RANSAC (building_hd) ou analyse MNS → OBB fallback ===
        // Chemin 1 : plans RANSAC (building_hd.roof_planes) disponibles dès le chargement
        // Chemin 2 : scan des points MNS LiDAR sur l'emprise + analyse de forme
        // Chemin 3 : toit plat (cap ExtrudeGeometry visible = toit plat avec matériau)
        const isPVBuilding = neighborIdx === null;
        const hdData = this.lidarData?.building_hd;
        // Priorité : building_center retourné par le backend (origine exacte des polygon_2d RANSAC).
        // Fallback : centroïde JS du polygone BD TOPO — peut différer de quelques décimètres.
        const hdCenter = hdData?.building_center;
        const pvCtr = this.pvBuildingCoords
            ? this._polygonCenter(this.pvBuildingCoords)
            : { y: this.centerLat, x: this.centerLon };
        const bldgCenter = hdCenter
            ? { lat: hdCenter.lat, lon: hdCenter.lon }
            : { lat: pvCtr.y, lon: pvCtr.x };

        let roofBuilt = false;
        let roofPanelsFrom = null;

        // Mémoriser la bbox de l'empreinte BD TOPO en coordonnées métriques relatives à bldgCenter.
        // Utilisé pour filtrer les polygones RANSAC qui appartiendraient à des bâtiments adjacents.
        if (isPVBuilding && buildingData.coords?.length >= 3) {
            const _lngToMBbox = this.LAT_TO_M * Math.cos(bldgCenter.lat * Math.PI / 180);
            const _fpXY = buildingData.coords.map(([lon, lat]) => [
                (lon - bldgCenter.lon) * _lngToMBbox,
                (lat - bldgCenter.lat) * this.LAT_TO_M
            ]);
            const _fpXs = _fpXY.map(p => p[0]);
            const _fpYs = _fpXY.map(p => p[1]);
            const _bboxM = 1.5; // 1.5m de marge (précision plani LiDAR HD ≤ 50cm)
            this._pvBuildingBboxMetric = {
                xMin: Math.min(..._fpXs) - _bboxM, xMax: Math.max(..._fpXs) + _bboxM,
                yMin: Math.min(..._fpYs) - _bboxM, yMax: Math.max(..._fpYs) + _bboxM,
            };
        } else if (isPVBuilding) {
            this._pvBuildingBboxMetric = null;
        }

        // ── Bâtiment PV : toit exclusivement via COPC (~15-35s) ─────────────────
        // Aucune géométrie MNH/MNS/OBB ne sera construite ici.
        // On cache juste le cap plat des murs et on attend COPC.
        if (isPVBuilding) {
            roofBuilt = true;  // court-circuite Chemin 2
            if (mesh && Array.isArray(mesh.material) && mesh.material[0]) {
                mesh.material[0].opacity = 0;
                mesh.material[0].transparent = true;
                mesh.material[0].depthWrite = false;
                mesh.material[0].needsUpdate = true;
            }
            console.log('⏳ Toit PV: en attente COPC LAZ brut');
        }

        // ── Garde polygonale : si le voisin chevauche le polygone PV, son toit OBB
        // recouvrira le mesh LiDAR COPC → on le bloque avant le Chemin 2.
        if (!roofBuilt && !isPVBuilding && this.pvBuildingCoords?.length >= 3) {
            const _pvPoly  = this.pvBuildingCoords;
            const _nePoly  = buildingData.coords || [];
            const _ptInPoly = (lon, lat, poly) => {
                let inside = false;
                const n = poly.length;
                for (let i = 0, j = n - 1; i < n; j = i++) {
                    const xi = poly[i][0], yi = poly[i][1];
                    const xj = poly[j][0], yj = poly[j][1];
                    if (((yi > lat) !== (yj > lat)) &&
                        (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi))
                        inside = !inside;
                }
                return inside;
            };
            const _neCtr = this._polygonCenter(_nePoly);
            const _pvCtrGeo = this._polygonCenter(_pvPoly);
            const _overlaps =
                _ptInPoly(_neCtr.x, _neCtr.y, _pvPoly) ||
                (_nePoly.length >= 3 && _ptInPoly(_pvCtrGeo.x, _pvCtrGeo.y, _nePoly)) ||
                _nePoly.some(([lon, lat]) => _ptInPoly(lon, lat, _pvPoly));
            if (_overlaps) {
                roofBuilt = true;
                console.log(`🚫 Voisin idx=${neighborIdx} chevauche le polygone PV → toit OBB ignoré`);
            }
        }

        // ── Chemin 2 : BD TOPO uniquement (voisins, sans WMS MNH) ────────────
        if (!roofBuilt) {
            const _nVertsC2 = (buildingData.coords || []).length;
            const _bdRidgeC2 = (_nVertsC2 <= 8 && buildingData.alt_toit_max != null && buildingData.alt_toit_min != null)
                ? (buildingData.alt_toit_max - buildingData.alt_toit_min) : null;
            const _hasBdRidge = _bdRidgeC2 != null && _bdRidgeC2 > 0.5 && _bdRidgeC2 < 15;

            if (_hasBdRidge) {
                const _bdType = (obb.longDim / Math.max(obb.shortDim, 0.1) > 1.4) ? 'gable' : 'hip';
                if (_bdType === 'gable') this._createGableRoof(localCoords, obb, bh, terrainH, _bdRidgeC2, roofType, wallType);
                else this._createHipRoof(localCoords, obb, bh, terrainH, _bdRidgeC2, roofType, wallType);
                roofBuilt = true;
                if (mesh && Array.isArray(mesh.material) && mesh.material[0]) {
                    mesh.material[0].opacity = 0;
                    mesh.material[0].transparent = true;
                    mesh.material[0].depthWrite = false;
                    mesh.material[0].needsUpdate = true;
                }
            }
        }

        // ── Mémoriser infos bâtiment principal pour les appels ultérieurs ──
        if (isPVBuilding) {
            // Placeholder minimal : COPC mettra à jour roofPanelsInfo complet à l'arrivée.
            this.roofPanelsInfo = { type: 'pending', panels: [], couverture: roofType };
            this.roofPanelsInfo.buildingOBB         = { cx: obb.cx, cz: obb.cz, angle: obb.angle, longDim: obb.longDim, shortDim: obb.shortDim };
            this.roofPanelsInfo.buildingTerrainH    = terrainH;
            this.roofPanelsInfo.buildingWallH       = bh;
            this.roofPanelsInfo.buildingLocalCoords = localCoords.map(c => ({x: c.x, z: c.z}));
            this.roofPanelsInfo.buildingCenterGeo   = { lat: bldgCenter.lat, lng: bldgCenter.lon };
        }
    }
    
    /**
     * Calcule les informations détaillées des pans de toiture.
     * @returns {Object} { type, panels: [{name, longueur, largeur, surface, pente_deg, orientation_deg, orientation_label}] }
     */
    _computeRoofPanelsInfo(obb, roofShape, ridgeExtra, bh, terrainH, hasPitchedRoof, roofType, nRidges, roofAnalysis) {
        const halfShort = obb.shortDim / 2;
        const halfLong = obb.longDim / 2;
        nRidges = nRidges || 1;
        
        // Angle du bâtiment en degrés (0=Est, 90=Nord dans le repère local)
        // Convertir en azimut géographique (0=Nord, 90=Est, 180=Sud, 270=Ouest)
        // obb.angle est l'angle de l'axe principal (le plus long côté) par rapport à l'axe X local
        // L'axe X local = Est, Z local = -Nord (car Z est inversé)
        // Donc obb.angle 0 = axe principal vers Est
        // Le faîtage suit l'axe principal. Les pans descendent perpendiculairement.
        // Pan 1 descend vers across > 0, Pan 2 vers across < 0
        
        // Direction perpendiculaire au faîtage (direction de descente du pan)
        // across positif = sinA * dx + cosA * dz  (dans le repère inversé Z)
        const ridgeAngleRad = obb.angle;
        // Perpendiculaire au faîtage : ridgeAngle + 90° et ridgeAngle - 90°
        // Convertir en azimut géographique (depuis le Nord, sens horaire)
        // Dans le repère local: X=Est, Z=-Nord
        // angle 0 du bâtiment = faîtage vers Est → pans vers Nord et Sud
        const perpAngle1 = ridgeAngleRad + Math.PI / 2; // un côté
        const perpAngle2 = ridgeAngleRad - Math.PI / 2; // autre côté
        
        // Convertir angle local en azimut géo (0=Nord, sens horaire)
        const toAzimut = (localAngle) => {
            // localAngle: 0=Est, +PI/2=Sud (car Z pointe vers le sud dans notre repère)
            // azimut: 0=Nord, 90=Est, 180=Sud, 270=Ouest
            // => az = 90 + angle_en_degrés
            let az = 90 + (localAngle * 180 / Math.PI);
            az = ((az % 360) + 360) % 360;
            return Math.round(az);
        };
        
        const getOrientLabel = (deg) => {
            const dirs = ['Nord', 'Nord-Est', 'Est', 'Sud-Est', 'Sud', 'Sud-Ouest', 'Ouest', 'Nord-Ouest'];
            return dirs[Math.round(((deg % 360 + 360) % 360) / 45) % 8];
        };
        
        const typeLabels = {
            'gable': 'Bi-pan (2 versants)',
            'hip': '4 pans (croupe)',
            'shed': 'Mono-pente',
            'multi-gable': `Multi-gable (${nRidges} faîtages)`,
            'multi-shed': `Multi-shed (${nRidges} sections)`,
            'flat': 'Toit plat'
        };
        
        const result = {
            type: roofShape,
            typeLabel: typeLabels[roofShape] || 'Toit plat',
            hauteurMurs: bh,
            hauteurFaitageRelatif: ridgeExtra,
            couverture: roofType,
            nRidges: nRidges,
            panels: []
        };
        
        if (!hasPitchedRoof || roofShape === 'flat') {
            // Toit plat : 1 seul pan
            result.panels.push({
                name: 'Toit plat',
                longueur: Math.round(obb.longDim * 10) / 10,
                largeur: Math.round(obb.shortDim * 10) / 10,
                surface: Math.round(obb.longDim * obb.shortDim * 10) / 10,
                pente_deg: 0,
                orientation_deg: 0,
                orientation_label: '—'
            });
        } else if (roofShape === 'gable') {
            // 2 pans symétriques
            const slopeDeg = Math.round(Math.atan2(ridgeExtra, halfShort) * 180 / Math.PI * 10) / 10;
            const rampantWidth = Math.round(Math.sqrt(halfShort * halfShort + ridgeExtra * ridgeExtra) * 10) / 10;
            const panLength = Math.round(obb.longDim * 10) / 10;
            const panSurface = Math.round(rampantWidth * panLength * 10) / 10;
            
            const az1 = toAzimut(perpAngle1);
            const az2 = toAzimut(perpAngle2);
            
            result.panels.push({
                name: 'Pan 1',
                longueur: panLength,
                largeur: rampantWidth,
                surface: panSurface,
                pente_deg: slopeDeg,
                orientation_deg: az1,
                orientation_label: getOrientLabel(az1)
            });
            result.panels.push({
                name: 'Pan 2',
                longueur: panLength,
                largeur: rampantWidth,
                surface: panSurface,
                pente_deg: slopeDeg,
                orientation_deg: az2,
                orientation_label: getOrientLabel(az2)
            });
        } else if (roofShape === 'hip') {
            // 4 pans : 2 principaux (trapézoïdaux) + 2 croupes (triangulaires)
            const slopeDeg = Math.round(Math.atan2(ridgeExtra, halfShort) * 180 / Math.PI * 10) / 10;
            const rampantWidth = Math.round(Math.sqrt(halfShort * halfShort + ridgeExtra * ridgeExtra) * 10) / 10;
            const ridgeHalfLen = halfLong * 0.45;
            const panMainLength = Math.round(ridgeHalfLen * 2 * 10) / 10;
            // Surface trapèze : (base_haute + base_basse) / 2 * hauteur
            const trapezeSurface = Math.round((panMainLength + obb.longDim) / 2 * rampantWidth * 10) / 10;
            
            const az1 = toAzimut(perpAngle1);
            const az2 = toAzimut(perpAngle2);
            
            result.panels.push({
                name: 'Pan principal 1',
                longueur: Math.round(obb.longDim * 10) / 10,
                largeur: rampantWidth,
                surface: trapezeSurface,
                pente_deg: slopeDeg,
                orientation_deg: az1,
                orientation_label: getOrientLabel(az1)
            });
            result.panels.push({
                name: 'Pan principal 2',
                longueur: Math.round(obb.longDim * 10) / 10,
                largeur: rampantWidth,
                surface: trapezeSurface,
                pente_deg: slopeDeg,
                orientation_deg: az2,
                orientation_label: getOrientLabel(az2)
            });
            
            // Croupes (triangles aux extrémités)
            const croupeSlope = Math.round(Math.atan2(ridgeExtra, halfLong - ridgeHalfLen) * 180 / Math.PI * 10) / 10;
            const croupeRampant = Math.sqrt(Math.pow(halfLong - ridgeHalfLen, 2) + ridgeExtra * ridgeExtra);
            const croupeSurface = Math.round(obb.shortDim * croupeRampant / 2 * 10) / 10;
            
            const azCroupe1 = toAzimut(ridgeAngleRad);
            const azCroupe2 = toAzimut(ridgeAngleRad + Math.PI);
            
            result.panels.push({
                name: 'Croupe 1',
                longueur: Math.round(obb.shortDim * 10) / 10,
                largeur: Math.round(croupeRampant * 10) / 10,
                surface: croupeSurface,
                pente_deg: croupeSlope,
                orientation_deg: azCroupe1,
                orientation_label: getOrientLabel(azCroupe1)
            });
            result.panels.push({
                name: 'Croupe 2',
                longueur: Math.round(obb.shortDim * 10) / 10,
                largeur: Math.round(croupeRampant * 10) / 10,
                surface: croupeSurface,
                pente_deg: croupeSlope,
                orientation_deg: azCroupe2,
                orientation_label: getOrientLabel(azCroupe2)
            });
        } else if (roofShape === 'shed') {
            // Mono-pente : 1 seul pan
            const slopeDeg = Math.round(Math.atan2(ridgeExtra, obb.shortDim) * 180 / Math.PI * 10) / 10;
            const rampantWidth = Math.round(Math.sqrt(obb.shortDim * obb.shortDim + ridgeExtra * ridgeExtra) * 10) / 10;
            const panLength = Math.round(obb.longDim * 10) / 10;
            
            const az1 = toAzimut(perpAngle2);
            
            result.panels.push({
                name: 'Pan unique',
                longueur: panLength,
                largeur: rampantWidth,
                surface: Math.round(rampantWidth * panLength * 10) / 10,
                pente_deg: slopeDeg,
                orientation_deg: az1,
                orientation_label: getOrientLabel(az1)
            });
        } else if (roofShape === 'multi-gable') {
            // Multi-gable : 2 pans par faîtage — utiliser le profil LiDAR réel
            const panLength = Math.round(obb.longDim * 10) / 10;
            const az1 = toAzimut(perpAngle1);
            const az2 = toAzimut(perpAngle2);
            
            // Extraire les positions réelles des faîtages et noues depuis le profil
            const profile = roofAnalysis && roofAnalysis.profile ? roofAnalysis.profile : null;
            
            if (profile && profile.length >= 5) {
                // Lisser le profil pour trouver les extrema
                const smoothH = profile.map((p, i) => {
                    if (i === 0 || i === profile.length - 1) return p.h;
                    return (profile[i-1].h + 2 * p.h + profile[i+1].h) / 4;
                });
                
                // Détecter les faîtages (maxima) et noues (minima)
                const ridges = [];  // indices de faîtages
                const valleys = []; // indices de noues
                const dh = [];
                for (let i = 1; i < smoothH.length; i++) {
                    dh.push(smoothH[i] - smoothH[i-1]);
                }
                for (let i = 1; i < dh.length; i++) {
                    if (dh[i-1] > 0 && dh[i] < 0) {
                        // Max local = faîtage
                        ridges.push(i);
                    } else if (dh[i-1] < 0 && dh[i] > 0) {
                        // Min local = noue
                        valleys.push(i);
                    }
                }
                
                // Filtrer les faux extrema (amplitude < 0.3m)
                const allExtrema = [...ridges.map(i => ({i, type: 'ridge'})), ...valleys.map(i => ({i, type: 'valley'}))];
                allExtrema.sort((a, b) => a.i - b.i);
                const filteredExtrema = [];
                for (let k = 0; k < allExtrema.length; k++) {
                    if (k > 0) {
                        const amp = Math.abs(smoothH[allExtrema[k].i] - smoothH[allExtrema[k-1].i]);
                        if (amp >= 0.3) filteredExtrema.push(allExtrema[k]);
                    } else {
                        filteredExtrema.push(allExtrema[k]);
                    }
                }
                
                const realRidges = filteredExtrema.filter(e => e.type === 'ridge').map(e => e.i);
                const realValleys = filteredExtrema.filter(e => e.type === 'valley').map(e => e.i);
                
                // Points de coupe : faîtages + noues + bords
                const cutPoints = [...new Set([0, ...realRidges, ...realValleys, profile.length - 1])].sort((a, b) => a - b);
                
                console.log(`📐 Multi-gable profil réel: ${realRidges.length} faîtages, ${realValleys.length} noues, ${cutPoints.length - 1} segments`);
                
                // Créer un pan pour chaque segment
                const acrossRange = roofAnalysis.acrossRange || obb.shortDim;
                let panCounter = 0;
                
                for (let s = 0; s < cutPoints.length - 1; s++) {
                    const startIdx = cutPoints[s];
                    const endIdx = cutPoints[s + 1];
                    
                    if (endIdx <= startIdx) continue;
                    
                    const startPos = profile[startIdx].pos;  // 0..1
                    const endPos = profile[endIdx].pos;
                    const startH = smoothH[startIdx];
                    const endH = smoothH[endIdx];
                    
                    // Largeur réelle de ce pan en mètres
                    const panWidthM = (endPos - startPos) * acrossRange;
                    if (panWidthM < 0.5) continue;
                    
                    // Pente réelle : dénivelé / distance horizontale
                    const dH = Math.abs(endH - startH);
                    const realSlopeDeg = Math.round(Math.atan2(dH, panWidthM) * 180 / Math.PI * 10) / 10;
                    
                    // Largeur rampant (hypoténuse)
                    const rampantWidth = Math.round(Math.sqrt(panWidthM * panWidthM + dH * dH) * 10) / 10;
                    const panSurface = Math.round(rampantWidth * panLength * 10) / 10;
                    
                    // Orientation : vers le côté descendant
                    const descending = endH < startH;
                    const panAzimut = descending ? az1 : az2;
                    
                    // Altitude du pan (base du pan)
                    const panBaseH = Math.min(startH, endH);
                    const panTopH = Math.max(startH, endH);
                    
                    panCounter++;
                    const isAtRidge = realRidges.includes(startIdx) || realRidges.includes(endIdx);
                    const shedNum = Math.ceil(panCounter / 2);
                    const panLabel = isAtRidge ? 
                        `F${shedNum} Pan ${panCounter % 2 === 1 ? 'A' : 'B'}` :
                        `Pan ${panCounter}`;
                    
                    result.panels.push({
                        name: panLabel,
                        longueur: panLength,
                        largeur: rampantWidth,
                        surface: panSurface,
                        pente_deg: realSlopeDeg,
                        orientation_deg: panAzimut,
                        orientation_label: getOrientLabel(panAzimut),
                        altitude_base: Math.round((terrainH + bh + panBaseH) * 10) / 10,
                        altitude_faitage: Math.round((terrainH + bh + panTopH) * 10) / 10,
                        position_across: Math.round((startPos + endPos) / 2 * acrossRange * 10) / 10,
                        largeur_horizontale: Math.round(panWidthM * 10) / 10,
                    });
                }
                
                if (result.panels.length === 0) {
                    // Fallback si aucun pan détecté
                    console.warn('⚠️ Aucun pan détecté depuis le profil, fallback uniforme');
                }
            }
            
            // Fallback : division uniforme si le profil n'a pas donné de résultat
            if (result.panels.length === 0) {
                const sectionWidth = obb.shortDim / nRidges;
                const halfSection = sectionWidth / 2;
                const slopeDeg = Math.round(Math.atan2(ridgeExtra, halfSection) * 180 / Math.PI * 10) / 10;
                const rampantWidth = Math.round(Math.sqrt(halfSection * halfSection + ridgeExtra * ridgeExtra) * 10) / 10;
                const panSurface = Math.round(rampantWidth * panLength * 10) / 10;
                
                for (let r = 0; r < nRidges; r++) {
                    const prefix = nRidges > 1 ? `F${r + 1} ` : '';
                    result.panels.push({
                        name: `${prefix}Pan A`,
                        longueur: panLength,
                        largeur: rampantWidth,
                        surface: panSurface,
                        pente_deg: slopeDeg,
                        orientation_deg: az1,
                        orientation_label: getOrientLabel(az1)
                    });
                    result.panels.push({
                        name: `${prefix}Pan B`,
                        longueur: panLength,
                        largeur: rampantWidth,
                        surface: panSurface,
                        pente_deg: slopeDeg,
                        orientation_deg: az2,
                        orientation_label: getOrientLabel(az2)
                    });
                }
            }
        } else if (roofShape === 'multi-shed') {
            // Multi-shed (dents de scie) : utiliser le profil LiDAR réel
            const panLength = Math.round(obb.longDim * 10) / 10;
            const az1 = toAzimut(perpAngle1);
            
            const profile = roofAnalysis && roofAnalysis.profile ? roofAnalysis.profile : null;
            
            if (profile && profile.length >= 5) {
                const smoothH = profile.map((p, i) => {
                    if (i === 0 || i === profile.length - 1) return p.h;
                    return (profile[i-1].h + 2 * p.h + profile[i+1].h) / 4;
                });
                
                // Trouver les discontinuités (chutes brutales = bord vertical du shed)
                const dh = [];
                for (let i = 1; i < smoothH.length; i++) {
                    dh.push(smoothH[i] - smoothH[i-1]);
                }
                
                // Détecter les ruptures : variation > 30% du ridgeExtra
                const breakThreshold = ridgeExtra * 0.3;
                const breakPoints = [0];
                for (let i = 0; i < dh.length; i++) {
                    if (Math.abs(dh[i]) > breakThreshold) {
                        breakPoints.push(i + 1);
                    }
                }
                breakPoints.push(profile.length - 1);
                
                // Dédupliquer les points de coupe trop proches
                const cleanBreaks = [breakPoints[0]];
                for (let i = 1; i < breakPoints.length; i++) {
                    if (breakPoints[i] - cleanBreaks[cleanBreaks.length - 1] >= 2) {
                        cleanBreaks.push(breakPoints[i]);
                    }
                }
                
                const acrossRange = roofAnalysis.acrossRange || obb.shortDim;
                
                for (let s = 0; s < cleanBreaks.length - 1; s++) {
                    const startIdx = cleanBreaks[s];
                    const endIdx = cleanBreaks[s + 1];
                    if (endIdx <= startIdx) continue;
                    
                    const startPos = profile[startIdx].pos;
                    const endPos = profile[endIdx].pos;
                    const startH = smoothH[startIdx];
                    const endH = smoothH[endIdx];
                    
                    const panWidthM = (endPos - startPos) * acrossRange;
                    if (panWidthM < 0.5) continue;
                    
                    const dH = Math.abs(endH - startH);
                    const realSlopeDeg = Math.round(Math.atan2(dH, panWidthM) * 180 / Math.PI * 10) / 10;
                    const rampantWidth = Math.round(Math.sqrt(panWidthM * panWidthM + dH * dH) * 10) / 10;
                    const panSurface = Math.round(rampantWidth * panLength * 10) / 10;
                    
                    result.panels.push({
                        name: `Section ${s + 1}`,
                        longueur: panLength,
                        largeur: rampantWidth,
                        surface: panSurface,
                        pente_deg: realSlopeDeg,
                        orientation_deg: az1,
                        orientation_label: getOrientLabel(az1),
                        altitude_base: Math.round((terrainH + bh + Math.min(startH, endH)) * 10) / 10,
                        altitude_faitage: Math.round((terrainH + bh + Math.max(startH, endH)) * 10) / 10,
                        largeur_horizontale: Math.round(panWidthM * 10) / 10,
                    });
                }
            }
            
            // Fallback uniforme
            if (result.panels.length === 0) {
                const sectionWidth = obb.shortDim / nRidges;
                const slopeDeg = Math.round(Math.atan2(ridgeExtra, sectionWidth) * 180 / Math.PI * 10) / 10;
                const rampantWidth = Math.round(Math.sqrt(sectionWidth * sectionWidth + ridgeExtra * ridgeExtra) * 10) / 10;
                const panSurface = Math.round(rampantWidth * panLength * 10) / 10;
                
                for (let r = 0; r < nRidges; r++) {
                    result.panels.push({
                        name: `Section ${r + 1}`,
                        longueur: panLength,
                        largeur: rampantWidth,
                        surface: panSurface,
                        pente_deg: slopeDeg,
                        orientation_deg: az1,
                        orientation_label: getOrientLabel(az1)
                    });
                }
            }
        }
        
        // Surface totale
        result.surfaceTotale = Math.round(result.panels.reduce((s, p) => s + p.surface, 0) * 10) / 10;
        
        return result;
    }
    
    /**
     * Retourne un bloc HTML formaté avec les informations des pans de toiture
     */
    getRoofPanelsHTML() {
        if (!this.roofPanelsInfo) return '<small class="text-muted">Aucune information de toiture</small>';
        
        const info = this.roofPanelsInfo;
        // Vérifier si des altitudes sont disponibles (profil LiDAR réel)
        const hasAltitudes  = info.panels.some(p => p.altitude_base !== undefined);
        const hasWidthH     = info.panels.some(p => p.largeur_horizontale !== undefined);
        const hasDims       = info.panels.some(p => p.longueur !== undefined);
        const hasSunshine   = info.panels.some(p => p.sunshineAnnual !== undefined);
        
        let html = `<div style="font-size:0.82rem;">`;
        html += `<div class="mb-2"><strong>🏠 ${info.typeLabel}</strong>`;
        html += ` <span class="badge bg-secondary">${info.couverture}</span>`;
        html += `</div>`;
        html += `<table class="table table-sm table-bordered mb-1" style="font-size:0.78rem;">`;
        html += `<thead><tr style="background:#f0f4ff;"><th>Pan</th>`;
        if (hasDims) html += `<th>Long.</th><th>Larg.</th>`;
        if (hasWidthH) html += `<th>Larg.H</th>`;
        html += `<th>Surface</th><th>Pente</th><th>Orientation</th>`;
        if (hasAltitudes) html += `<th>Alt.</th>`;
        if (hasSunshine) html += `<th>☀️ kWh/m²/an</th>`;
        html += `</tr></thead><tbody>`;
        
        for (const p of info.panels) {
            const orientBadge = p.pente_deg > 0 
                ? `<span class="badge bg-info">${p.orientation_deg}° ${p.orientation_label || p.orientationLabel || ''}</span>`
                : '—';
            html += `<tr>`;
            html += `<td><strong>${p.name}</strong></td>`;
            if (hasDims) {
                html += `<td>${p.longueur !== undefined ? p.longueur + ' m' : '—'}</td>`;
                html += `<td>${p.largeur  !== undefined ? p.largeur  + ' m' : '—'}</td>`;
            }
            if (hasWidthH) html += `<td>${p.largeur_horizontale !== undefined ? p.largeur_horizontale + ' m' : '—'}</td>`;
            html += `<td>${p.surface} m²</td>`;
            html += `<td>${p.pente_deg}°</td>`;
            html += `<td>${orientBadge}</td>`;
            if (hasAltitudes) {
                html += `<td>${p.altitude_base !== undefined ? p.altitude_base + ' m' : '—'}`;
                if (p.altitude_faitage !== undefined) html += `<br><small>↑${p.altitude_faitage} m</small>`;
                html += `</td>`;
            }
            if (hasSunshine) {
                const sun = p.sunshineAnnual;
                const c   = sun > 1200 ? '#16a34a' : sun > 900 ? '#ca8a04' : '#dc2626';
                html += `<td style="color:${c};font-weight:600;">${sun !== undefined ? sun : '—'}</td>`;
            }
            html += `</tr>`;
        }
        
        html += `</tbody></table>`;
        
        // Calcul surface totale
        const surfaceTotale = info.surfaceTotale || info.panels.reduce((s, p) => s + (p.surface || 0), 0);
        html += `<div class="text-end"><strong>Surface totale : ${Math.round(surfaceTotale * 10) / 10} m²</strong></div>`;
        html += `</div>`;
        
        return html;
    }
    
    /**
     * Détermine le type de mur
     */
    _getWallType(b) {
        if (b.materiaux_murs === 'Brique') return 'brick';
        if (b.materiaux_murs === 'Pierre') return 'stone';
        if (b.materiaux_murs === 'Béton') return 'concrete';
        if (b.usage === 'Industriel') return 'industrial';
        if (b.usage === 'Commercial et services') return 'commercial';
        if (b.source === 'osm' && b.type === 'garage') return 'industrial';
        if (b.source === 'osm' && b.type === 'house') return 'plaster';
        return 'plaster'; // crépi par défaut
    }
    
    /**
     * Détermine le type de toit
     */
    _getRoofType(b) {
        if (b.materiaux_toit === 'Ardoise') return 'slate';
        if (b.materiaux_toit === 'Zinc') return 'zinc';
        if (b.materiaux_toit === 'Béton') return 'concrete';
        if (b.materiaux_toit === 'Tôle') return 'metal';
        if (b.roof_shape === 'flat') return 'concrete';
        return 'tile'; // tuiles terre cuite par défaut
    }
    
    /**
     * Génère une texture procédurale de façade avec fenêtres
     */
    _getFacadeTexture(wallType, width, height, depth) {
        const cacheKey = `facade_${wallType}_${Math.round(width)}_${Math.round(height)}`;
        if (this._textureCache[cacheKey]) return this._textureCache[cacheKey];
        
        const canvas = document.createElement('canvas');
        const res = 512;
        canvas.width = res;
        canvas.height = res;
        const ctx = canvas.getContext('2d');
        
        // Couleur de fond selon le type de mur
        const wallColors = {
            plaster:    { base: '#E8DCC8', var1: '#DED0BA', var2: '#F0E4D0', joint: null },
            brick:      { base: '#B5651D', var1: '#A05518', var2: '#C47030', joint: '#D4C4A0' },
            stone:      { base: '#A09080', var1: '#8A7A6A', var2: '#B8A898', joint: '#C8C0B0' },
            concrete:   { base: '#B0B0B0', var1: '#A0A0A0', var2: '#C0C0C0', joint: null },
            industrial: { base: '#888888', var1: '#777777', var2: '#999999', joint: null },
            commercial: { base: '#D0D0D0', var1: '#C0C0C0', var2: '#E0E0E0', joint: null },
        };
        const wc = wallColors[wallType] || wallColors.plaster;
        
        // Fond
        ctx.fillStyle = wc.base;
        ctx.fillRect(0, 0, res, res);
        
        // Texture de mur
        if (wallType === 'brick') {
            this._drawBrickPattern(ctx, res, wc);
        } else if (wallType === 'stone') {
            this._drawStonePattern(ctx, res, wc);
        } else {
            // Crépi / béton — bruit subtil
            this._drawPlasterNoise(ctx, res, wc);
        }
        
        // Fenêtres — correction d'aspect (la texture carrée est mappée sur un mur non-carré)
        // Pixels/m dans chaque axe pour dessiner des fenêtres aux bonnes proportions
        const pxPerMX = res / Math.max(width, 0.5);
        const pxPerMY = res / Math.max(height, 0.5);
        
        const floors = Math.max(1, Math.round(height / 3));
        const windowsPerFloor = Math.max(1, Math.round(width / 3));
        
        // Dimensions réelles fenêtre : ~1.0m × 1.4m
        const realWinW = 1.0;
        const realWinH = 1.4;
        const winW = realWinW * pxPerMX;
        const winH = realWinH * pxPerMY;
        const realFloorH = height / floors;
        const floorH = realFloorH * pxPerMY;
        const cellW = (width / windowsPerFloor) * pxPerMX;
        
        for (let f = 0; f < floors; f++) {
            for (let w = 0; w < windowsPerFloor; w++) {
                const wx = (w + 0.5) * cellW - winW / 2;
                const wy = f * floorH + (floorH - winH) * 0.4;
                
                // Encadrement
                ctx.fillStyle = '#7A7060';
                ctx.fillRect(wx - 2, wy - 2, winW + 4, winH + 4);
                
                // Vitre
                const gradient = ctx.createLinearGradient(wx, wy, wx + winW, wy + winH);
                gradient.addColorStop(0, '#5577AA');
                gradient.addColorStop(0.3, '#88AACC');
                gradient.addColorStop(0.6, '#6688AA');
                gradient.addColorStop(1, '#446688');
                ctx.fillStyle = gradient;
                ctx.fillRect(wx, wy, winW, winH);
                
                // Croisillons de fenêtre
                ctx.strokeStyle = '#6A6050';
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(wx + winW / 2, wy);
                ctx.lineTo(wx + winW / 2, wy + winH);
                ctx.moveTo(wx, wy + winH * 0.4);
                ctx.lineTo(wx + winW, wy + winH * 0.4);
                ctx.stroke();
                
                // Rebord de fenêtre
                ctx.fillStyle = '#9A9080';
                ctx.fillRect(wx - 3, wy + winH, winW + 6, 3);
            }
        }
        
        // Porte au rez-de-chaussée (face principale) — ~0.95m × 2.2m réels
        if (floors >= 1 && windowsPerFloor >= 1) {
            const realDoorW = 0.95;
            const realDoorH = 2.15;
            const doorW = realDoorW * pxPerMX;
            const doorH = realDoorH * pxPerMY;
            const doorX = res / 2 - doorW / 2;
            // Porte au rez-de-chaussée (dernier étage dans le canvas = bas du mur)
            const doorY = (floors - 1) * floorH + (floorH - doorH) * 0.75;
            
            // Encadrement porte
            ctx.fillStyle = '#5A5040';
            ctx.fillRect(doorX - 3, doorY - 3, doorW + 6, doorH + 6);
            
            // Porte
            ctx.fillStyle = '#6B4226';
            ctx.fillRect(doorX, doorY, doorW, doorH);
            
            // Ligne centrale porte
            ctx.strokeStyle = '#5A3520';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(doorX + doorW / 2, doorY);
            ctx.lineTo(doorX + doorW / 2, doorY + doorH);
            ctx.stroke();
        }
        
        const texture = new THREE.CanvasTexture(canvas);
        texture.wrapS = THREE.RepeatWrapping;
        texture.wrapT = THREE.RepeatWrapping;
        texture.minFilter = THREE.LinearFilter;
        this._textureCache[cacheKey] = texture;
        return texture;
    }
    
    /**
     * Motif briques
     */
    _drawBrickPattern(ctx, res, wc) {
        const brickH = 12;
        const brickW = 28;
        const jointW = 2;
        
        for (let y = 0; y < res; y += brickH + jointW) {
            const offset = (Math.floor(y / (brickH + jointW)) % 2) * (brickW / 2);
            
            // Joint horizontal
            ctx.fillStyle = wc.joint;
            ctx.fillRect(0, y + brickH, res, jointW);
            
            for (let x = -brickW; x < res + brickW; x += brickW + jointW) {
                // Joint vertical
                ctx.fillStyle = wc.joint;
                ctx.fillRect(x + offset + brickW, y, jointW, brickH);
                
                // Brique avec variation
                const shade = Math.random() * 0.12 - 0.06;
                const r = parseInt(wc.base.slice(1, 3), 16);
                const g = parseInt(wc.base.slice(3, 5), 16);
                const b = parseInt(wc.base.slice(5, 7), 16);
                ctx.fillStyle = `rgb(${Math.min(255, r + shade * 255)}, ${Math.min(255, g + shade * 255)}, ${Math.min(255, b + shade * 255)})`;
                ctx.fillRect(x + offset + 1, y + 1, brickW - 2, brickH - 2);
            }
        }
    }
    
    /**
     * Motif pierre
     */
    _drawStonePattern(ctx, res, wc) {
        // Pierres de tailles irrégulières
        for (let i = 0; i < 60; i++) {
            const sx = Math.random() * res;
            const sy = Math.random() * res;
            const sw = 30 + Math.random() * 50;
            const sh = 20 + Math.random() * 35;
            
            // Joint
            ctx.fillStyle = wc.joint;
            ctx.fillRect(sx - 1, sy - 1, sw + 2, sh + 2);
            
            // Pierre avec variation de couleur
            const shade = Math.random();
            ctx.fillStyle = shade > 0.5 ? wc.var1 : (shade > 0.25 ? wc.base : wc.var2);
            ctx.fillRect(sx, sy, sw, sh);
        }
    }
    
    /**
     * Bruit de crépi/béton
     */
    _drawPlasterNoise(ctx, res, wc) {
        const imageData = ctx.getImageData(0, 0, res, res);
        const data = imageData.data;
        for (let i = 0; i < data.length; i += 4) {
            const noise = (Math.random() - 0.5) * 15;
            data[i] = Math.min(255, Math.max(0, data[i] + noise));
            data[i + 1] = Math.min(255, Math.max(0, data[i + 1] + noise));
            data[i + 2] = Math.min(255, Math.max(0, data[i + 2] + noise));
        }
        ctx.putImageData(imageData, 0, 0);
    }
    
    /**
     * Génère une texture procédurale de toit
     */
    _getRoofTexture(roofType) {
        const cacheKey = `roof_${roofType}`;
        if (this._textureCache[cacheKey]) return this._textureCache[cacheKey];
        
        const canvas = document.createElement('canvas');
        const res = 256;
        canvas.width = res;
        canvas.height = res;
        const ctx = canvas.getContext('2d');
        
        if (roofType === 'tile') {
            // Tuiles terre cuite
            ctx.fillStyle = '#8B4513';
            ctx.fillRect(0, 0, res, res);
            
            const tileH = 16, tileW = 24;
            for (let y = 0; y < res; y += tileH) {
                const offset = (Math.floor(y / tileH) % 2) * (tileW / 2);
                for (let x = -tileW; x < res + tileW; x += tileW) {
                    const shade = Math.random() * 0.2 - 0.1;
                    const r = 139 + shade * 80, g = 69 + shade * 40, b = 19 + shade * 20;
                    ctx.fillStyle = `rgb(${r},${g},${b})`;
                    ctx.beginPath();
                    ctx.arc(x + offset + tileW / 2, y + tileH / 2, tileW / 2, 0, Math.PI, true);
                    ctx.rect(x + offset, y, tileW, tileH / 2);
                    ctx.fill();
                    // Ligne séparation
                    ctx.strokeStyle = '#6B3010';
                    ctx.lineWidth = 0.5;
                    ctx.beginPath();
                    ctx.arc(x + offset + tileW / 2, y + tileH * 0.6, tileW / 2.2, 0, Math.PI, true);
                    ctx.stroke();
                }
            }
        } else if (roofType === 'slate') {
            // Ardoise
            ctx.fillStyle = '#3a3a3a';
            ctx.fillRect(0, 0, res, res);
            
            const slateH = 14, slateW = 10;
            for (let y = 0; y < res; y += slateH) {
                const offset = (Math.floor(y / slateH) % 2) * (slateW / 2);
                for (let x = 0; x < res; x += slateW) {
                    const shade = Math.random() * 30;
                    ctx.fillStyle = `rgb(${50 + shade}, ${50 + shade}, ${55 + shade})`;
                    ctx.fillRect(x + offset, y, slateW - 1, slateH - 1);
                }
            }
        } else if (roofType === 'zinc' || roofType === 'metal') {
            // Zinc / tôle
            ctx.fillStyle = roofType === 'zinc' ? '#8899AA' : '#777777';
            ctx.fillRect(0, 0, res, res);
            
            // Joints de tôle verticaux
            ctx.strokeStyle = roofType === 'zinc' ? '#667788' : '#666666';
            ctx.lineWidth = 2;
            for (let x = 0; x < res; x += 32) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, res);
                ctx.stroke();
            }
            // Bruit léger
            const imageData = ctx.getImageData(0, 0, res, res);
            const data = imageData.data;
            for (let i = 0; i < data.length; i += 4) {
                const n = (Math.random() - 0.5) * 8;
                data[i] += n; data[i+1] += n; data[i+2] += n;
            }
            ctx.putImageData(imageData, 0, 0);
        } else {
            // Béton / toit plat
            ctx.fillStyle = '#999999';
            ctx.fillRect(0, 0, res, res);
            const imageData = ctx.getImageData(0, 0, res, res);
            const data = imageData.data;
            for (let i = 0; i < data.length; i += 4) {
                const n = (Math.random() - 0.5) * 20;
                data[i] += n; data[i+1] += n; data[i+2] += n;
            }
            ctx.putImageData(imageData, 0, 0);
        }
        
        const texture = new THREE.CanvasTexture(canvas);
        texture.wrapS = THREE.RepeatWrapping;
        texture.wrapT = THREE.RepeatWrapping;
        this._textureCache[cacheKey] = texture;
        return texture;
    }
    
    /**
     * Génère un toit depuis le vrai polygone du bâtiment (pas l'OBB).
     * Chaque sommet du polygone est élevé selon la fonction de hauteur (heightFunc).
     * Insère des sommets sur la ligne de faîtage pour conserver l'arête vive.
     * Crée aussi les murs pignons (skirt) entre le toit et le haut des murs.
     * 
     * @param {Array} localCoords - Sommets du polygone [{x, z}]
     * @param {Object} obb - {cx, cz, angle, longDim, shortDim}
     * @param {number} roofBaseY - Y du haut des murs
     * @param {Function} heightFunc - (across, along) => hauteur additionnelle au-dessus de roofBaseY
     * @param {string} roofType - Type de couverture
     * @param {string} wallType - Type de mur
     */
    
    /**
     * Crée un toit multi-sections par maillage grillé.
     * Résout le problème de _createPolygonRoof qui n'a pas assez de sommets
     * pour représenter les profils zigzag multi-gable/multi-shed.
     * 
     * Approche : grille OBB-alignée → heightFunc à chaque noeud → clipping polygonal
     */
    _createGridRoof(localCoords, obb, roofBaseY, heightFunc, roofType, wallType, nSubdivisionsAcross) {
        if (!localCoords || localCoords.length < 3) return;
        
        const cosA = Math.cos(-obb.angle);
        const sinA = Math.sin(-obb.angle);
        const halfShort = obb.shortDim / 2;
        const halfLong = obb.longDim / 2;
        
        // Abaisser légèrement pour pénétrer dans les murs (anti-interstice)
        const roofBaseAdj = roofBaseY - 0.15;
        
        // Résolution de la grille
        const nAcross = Math.max(nSubdivisionsAcross || 16, 8);
        const nAlong = Math.max(4, Math.round(obb.longDim / 5)); // ~1 tous les 5m
        
        // ── Point-in-polygon test ──
        const isInPolygon = (wx, wz) => {
            let inside = false;
            const n = localCoords.length;
            for (let i = 0, j = n - 1; i < n; j = i++) {
                const xi = localCoords[i].x, zi = localCoords[i].z;
                const xj = localCoords[j].x, zj = localCoords[j].z;
                if (((zi > wz) !== (zj > wz)) &&
                    (wx < (xj - xi) * (wz - zi) / (zj - zi) + xi)) {
                    inside = !inside;
                }
            }
            return inside;
        };
        
        // Légère marge intérieure pour que les bords de la grille ne dépassent pas
        const margin = 0.3; // 30cm de retrait
        const effHalfShort = halfShort - margin;
        const effHalfLong = halfLong - margin;
        
        // ── Créer la grille de sommets ──
        const positions = [];
        const uvs = [];
        const gridIdx = []; // [i][j] → index dans positions, ou -1 si hors polygone
        
        let vertexCount = 0;
        for (let i = 0; i <= nAcross; i++) {
            gridIdx[i] = [];
            const across = -effHalfShort + (i / nAcross) * effHalfShort * 2;
            
            for (let j = 0; j <= nAlong; j++) {
                const along = -effHalfLong + (j / nAlong) * effHalfLong * 2;
                
                // Convertir en coordonnées monde
                const wx = obb.cx + along * cosA + across * sinA;
                const wz = obb.cz - along * sinA + across * cosA;
                
                if (isInPolygon(wx, wz)) {
                    const h = heightFunc(across, along);
                    positions.push(wx, roofBaseAdj + h, wz);
                    uvs.push(along / 4.0, across / 4.0);
                    gridIdx[i][j] = vertexCount++;
                } else {
                    gridIdx[i][j] = -1;
                }
            }
        }
        
        if (vertexCount < 3) {
            // Pas assez de sommets dans le polygone — fallback
            console.warn('⚠️ _createGridRoof: pas assez de sommets dans le polygone, fallback _createPolygonRoof');
            this._createPolygonRoof(localCoords, obb, roofBaseY, heightFunc, roofType, wallType);
            return;
        }
        
        // ── Créer les triangles ──
        const indices = [];
        for (let i = 0; i < nAcross; i++) {
            for (let j = 0; j < nAlong; j++) {
                const i00 = gridIdx[i][j];
                const i10 = gridIdx[i + 1][j];
                const i01 = gridIdx[i][j + 1];
                const i11 = gridIdx[i + 1][j + 1];
                
                // Triangle 1 : (i,j) - (i+1,j) - (i,j+1)
                if (i00 >= 0 && i10 >= 0 && i01 >= 0) {
                    indices.push(i00, i10, i01);
                }
                // Triangle 2 : (i+1,j) - (i+1,j+1) - (i,j+1)
                if (i10 >= 0 && i11 >= 0 && i01 >= 0) {
                    indices.push(i10, i11, i01);
                }
            }
        }
        
        if (indices.length < 3) return;
        
        // ── Créer le mesh ──
        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
        geo.setIndex(indices);
        geo.computeVertexNormals();
        
        const roofTex = this._getRoofTexture(roofType);
        const roofMat = new THREE.MeshPhongMaterial({
            map: roofTex, side: THREE.DoubleSide,
            specular: 0x222222,
            shininess: roofType === 'zinc' || roofType === 'metal' ? 30 : 5
        });
        const roofMesh = new THREE.Mesh(geo, roofMat);
        roofMesh.castShadow = true;
        roofMesh.receiveShadow = true;
        this.scene.add(roofMesh);
        this.buildings.push(roofMesh);
        
        // ── Murs pignons aux extrémités ──
        // Appliquer heightFunc le long des arêtes du bâtiment qui sont
        // perpendiculaires au faîtage (les pignons aux 2 bouts)
        const wallColorMap = {
            plaster: 0xE8DCC8, brick: 0xB5651D, stone: 0xA09080,
            concrete: 0xB0B0B0, industrial: 0x888888, commercial: 0xD0D0D0
        };
        const wallColor = wallColorMap[wallType] || 0xE8DCC8;
        const alongDirX = Math.cos(obb.angle);
        const alongDirZ = Math.sin(obb.angle);
        
        const pignonVerts = [];
        const nPignonSamples = nAcross; // même résolution que la grille
        
        for (let e = 0; e < localCoords.length; e++) {
            const curr = localCoords[e];
            const next = localCoords[(e + 1) % localCoords.length];
            
            const edgeX = next.x - curr.x;
            const edgeZ = next.z - curr.z;
            const edgeLen = Math.sqrt(edgeX * edgeX + edgeZ * edgeZ);
            if (edgeLen < 0.5) continue;
            
            // Ne traiter que les arêtes perpendiculaires au faîtage (pignons)
            const dotAlong = Math.abs((edgeX * alongDirX + edgeZ * alongDirZ) / edgeLen);
            if (dotAlong > 0.5) continue;
            
            // Subdiviser cette arête et créer des triangles pignon
            for (let s = 0; s < nPignonSamples; s++) {
                const t1 = s / nPignonSamples;
                const t2 = (s + 1) / nPignonSamples;
                
                const x1 = curr.x + t1 * edgeX;
                const z1 = curr.z + t1 * edgeZ;
                const x2 = curr.x + t2 * edgeX;
                const z2 = curr.z + t2 * edgeZ;
                
                const dx1 = x1 - obb.cx, dz1 = z1 - obb.cz;
                const ac1 = dx1 * sinA + dz1 * cosA;
                const al1 = dx1 * cosA - dz1 * sinA;
                const h1 = heightFunc(ac1, al1);
                
                const dx2 = x2 - obb.cx, dz2 = z2 - obb.cz;
                const ac2 = dx2 * sinA + dz2 * cosA;
                const al2 = dx2 * cosA - dz2 * sinA;
                const h2 = heightFunc(ac2, al2);
                
                if (h1 < 0.05 && h2 < 0.05) continue;
                
                const y1top = roofBaseAdj + h1;
                const y2top = roofBaseAdj + h2;
                
                // Quad : (x1,base) - (x2,base) - (x2,top) - (x1,top) → 2 triangles
                pignonVerts.push(
                    x1, roofBaseAdj, z1,  x2, roofBaseAdj, z2,  x2, y2top, z2,
                    x1, roofBaseAdj, z1,  x2, y2top, z2,      x1, y1top, z1
                );
            }
        }
        
        if (pignonVerts.length > 0) {
            const wallGeo = new THREE.BufferGeometry();
            wallGeo.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(pignonVerts), 3));
            wallGeo.computeVertexNormals();
            const wallMat = new THREE.MeshPhongMaterial({
                color: wallColor, side: THREE.DoubleSide,
                specular: 0x111111, shininess: 5
            });
            const wallMesh = new THREE.Mesh(wallGeo, wallMat);
            wallMesh.castShadow = true;
            this.scene.add(wallMesh);
            this.buildings.push(wallMesh);
        }
        
        console.log(`✅ _createGridRoof: ${vertexCount} sommets, ${indices.length / 3} triangles, ${pignonVerts.length / 18} quads pignon`);
    }
    
    _createPolygonRoof(localCoords, obb, roofBaseY, heightFunc, roofType, wallType) {
        if (!localCoords || localCoords.length < 3) throw new Error('roof: insufficient coords');
        
        const cosA = Math.cos(-obb.angle);
        const sinA = Math.sin(-obb.angle);
        
        // Abaisser la base du toit de 0.15m pour qu'il pénètre dans le haut des murs
        // → élimine tous les interstices entre toit et murs
        const roofBaseAdj = roofBaseY - 0.15;
        
        // === Étape 1 : Construire le polygone augmenté (sommets + intersections faîtage) ===
        // Utilise les coords EXACTES du bâtiment (pas d'expansion centroïde)
        const augmented = [];
        const n = localCoords.length;
        
        for (let i = 0; i < n; i++) {
            const curr = localCoords[i];
            const next = localCoords[(i + 1) % n];
            
            const currDx = curr.x - obb.cx;
            const currDz = curr.z - obb.cz;
            const currAcross = currDx * sinA + currDz * cosA;
            const currAlong = currDx * cosA - currDz * sinA;
            const currH = heightFunc(currAcross, currAlong);
            
            augmented.push({
                x: curr.x, z: curr.z,
                y: roofBaseAdj + currH,
                across: currAcross
            });
            
            // Insérer un sommet sur le faîtage si l'arête traverse across=0
            const nextDx = next.x - obb.cx;
            const nextDz = next.z - obb.cz;
            const nextAcross = nextDx * sinA + nextDz * cosA;
            
            if (currAcross * nextAcross < 0 && Math.abs(currAcross) > 0.1 && Math.abs(nextAcross) > 0.1) {
                const t = Math.abs(currAcross) / (Math.abs(currAcross) + Math.abs(nextAcross));
                const ix = curr.x + t * (next.x - curr.x);
                const iz = curr.z + t * (next.z - curr.z);
                const iDx = ix - obb.cx;
                const iDz = iz - obb.cz;
                const iAlong = iDx * cosA - iDz * sinA;
                const iH = heightFunc(0, iAlong);
                augmented.push({ x: ix, z: iz, y: roofBaseAdj + iH, across: 0 });
            }
        }
        
        if (augmented.length < 3) throw new Error('roof: augmented polygon too small');
        
        // === Étape 3 : Trouver les sommets de faîtage et séparer en 2 demi-toitures ===
        // La triangulation ear-clipping sur le polygone entier crée des triangles
        // diagonaux qui traversent le faîtage, causant des décalages visuels.
        // En séparant en 2, chaque pan est triangulé indépendamment → faces planes correctes.
        const ridgeIndices = [];
        for (let i = 0; i < augmented.length; i++) {
            if (Math.abs(augmented[i].across) < 0.05) {
                ridgeIndices.push(i);
            }
        }
        
        let allTriangles = [];
        
        const triangulatePoly = (poly) => {
            if (poly.length < 3) return [];
            const pts = poly.map(v => new THREE.Vector2(v.x, -v.z));
            let area = 0;
            for (let k = 0; k < pts.length; k++) {
                const k1 = (k + 1) % pts.length;
                area += pts[k].x * pts[k1].y - pts[k1].x * pts[k].y;
            }
            const rev = area < 0;
            if (rev) pts.reverse();
            try {
                const tris = THREE.ShapeUtils.triangulateShape(pts, []);
                if (rev) {
                    const pn = poly.length;
                    return tris.map(t => [pn - 1 - t[0], pn - 1 - t[1], pn - 1 - t[2]]);
                }
                return tris;
            } catch(e) {
                throw new Error('roof: triangulatePoly failed: ' + e.message);
            }
        };
        
        if (ridgeIndices.length === 2) {
            const [r1, r2] = ridgeIndices;
            
            // Demi-toiture 1 : sommets de r1 à r2 (sens direct dans le polygone)
            const half1 = [], map1 = [];
            for (let i = r1; ; ) {
                map1.push(i);
                half1.push(augmented[i]);
                if (i === r2) break;
                i = (i + 1) % augmented.length;
            }
            
            // Demi-toiture 2 : sommets de r2 à r1 (sens direct, wrap)
            const half2 = [], map2 = [];
            for (let i = r2; ; ) {
                map2.push(i);
                half2.push(augmented[i]);
                if (i === r1) break;
                i = (i + 1) % augmented.length;
            }
            
            // Trianguler chaque demi-toiture séparément
            for (const t of triangulatePoly(half1)) {
                allTriangles.push([map1[t[0]], map1[t[1]], map1[t[2]]]);
            }
            for (const t of triangulatePoly(half2)) {
                allTriangles.push([map2[t[0]], map2[t[1]], map2[t[2]]]);
            }
        } else {
            // Fallback : trianguler le polygone entier
            const pts2D = augmented.map(v => new THREE.Vector2(v.x, -v.z));
            let areaSign = 0;
            for (let i = 0; i < pts2D.length; i++) {
                const j = (i + 1) % pts2D.length;
                areaSign += pts2D[i].x * pts2D[j].y - pts2D[j].x * pts2D[i].y;
            }
            if (areaSign < 0) {
                pts2D.reverse();
                augmented.reverse();
            }
            try {
                const tris = THREE.ShapeUtils.triangulateShape(pts2D, []);
                for (const t of tris) {
                    allTriangles.push([t[0], t[1], t[2]]);
                }
            } catch(e) { throw new Error('roof: triangulateShape failed: ' + e.message); }
        }
        
        if (allTriangles.length === 0) throw new Error('roof: triangulation produced 0 triangles');
        
        // === Étape 4 : Géométrie du toit ===
        const positions = [];
        const uvs = [];
        for (const v of augmented) {
            positions.push(v.x, v.y, v.z);
            const dx = v.x - obb.cx;
            const dz = v.z - obb.cz;
            const along = dx * cosA - dz * sinA;
            uvs.push(along / 4.0, (v.across || 0) / 4.0);
        }
        
        const indices = [];
        for (const tri of allTriangles) {
            indices.push(tri[0], tri[1], tri[2]);
        }
        
        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
        geo.setIndex(indices);
        geo.computeVertexNormals();
        
        const roofTex = this._getRoofTexture(roofType);
        const roofMat = new THREE.MeshPhongMaterial({
            map: roofTex, side: THREE.DoubleSide,
            specular: 0x222222,
            shininess: roofType === 'zinc' || roofType === 'metal' ? 30 : 5,
            polygonOffset: true,
            polygonOffsetFactor: -1,
            polygonOffsetUnits: -1,
        });
        const roofMesh = new THREE.Mesh(geo, roofMat);
        roofMesh.castShadow = true;
        roofMesh.receiveShadow = true;
        this.scene.add(roofMesh);
        this.buildings.push(roofMesh);
        
        // === Étape 5 : Murs pignon (sur les coords originales, pas étendues) ===
        const wallColorMap2 = {
            plaster: 0xE8DCC8, brick: 0xB5651D, stone: 0xA09080,
            concrete: 0xB0B0B0, industrial: 0x888888, commercial: 0xD0D0D0
        };
        const wallColor = wallColorMap2[wallType] || 0xE8DCC8;
        
        const alongDirX = Math.cos(obb.angle);
        const alongDirZ = Math.sin(obb.angle);
        
        // Construire les murs pignon depuis les coords originales du bâtiment
        // IMPORTANT : pour les arêtes qui traversent le faîtage (across change de signe),
        // il faut insérer le point d'intersection avec le faîtage pour que le pignon
        // suive exactement le profil du toit (pic au faîtage).
        const pignonVerts = [];
        for (let i = 0; i < localCoords.length; i++) {
            const curr = localCoords[i];
            const next = localCoords[(i + 1) % localCoords.length];
            
            // Calculer la hauteur du toit aux deux extrémités de cette arête murale
            const cDx = curr.x - obb.cx, cDz = curr.z - obb.cz;
            const cAcross = cDx * sinA + cDz * cosA;
            const cAlong = cDx * cosA - cDz * sinA;
            const currRoofH = heightFunc(cAcross, cAlong);
            
            const nDx = next.x - obb.cx, nDz = next.z - obb.cz;
            const nAcross = nDx * sinA + nDz * cosA;
            const nAlong = nDx * cosA - nDz * sinA;
            const nextRoofH = heightFunc(nAcross, nAlong);
            
            // Ne créer un pignon que pour les arêtes perpendiculaires au faîtage
            const edgeX = next.x - curr.x;
            const edgeZ = next.z - curr.z;
            const edgeLen = Math.sqrt(edgeX * edgeX + edgeZ * edgeZ);
            if (edgeLen < 0.01) continue;
            
            const dotAlong = Math.abs((edgeX * alongDirX + edgeZ * alongDirZ) / edgeLen);
            if (dotAlong > 0.5) continue; // parallèle au faîtage → pas un pignon
            
            // Vérifier si cette arête traverse le faîtage (across change de signe)
            const crossesRidge = (cAcross * nAcross < 0) && Math.abs(cAcross) > 0.05 && Math.abs(nAcross) > 0.05;
            
            if (crossesRidge) {
                // Interpoler le point d'intersection avec le faîtage (across=0)
                const t = Math.abs(cAcross) / (Math.abs(cAcross) + Math.abs(nAcross));
                const ridgeX = curr.x + t * (next.x - curr.x);
                const ridgeZ = curr.z + t * (next.z - curr.z);
                const ridgeDx = ridgeX - obb.cx, ridgeDz = ridgeZ - obb.cz;
                const ridgeAlong = ridgeDx * cosA - ridgeDz * sinA;
                const ridgeH = heightFunc(0, ridgeAlong);
                const ridgeY = roofBaseAdj + ridgeH;
                
                const cy = roofBaseAdj + currRoofH;
                const ny = roofBaseAdj + nextRoofH;
                
                // Demi-pignon 1 : curr → point faîtage
                if (ridgeH > 0.05 || currRoofH > 0.05) {
                    pignonVerts.push(
                        curr.x, cy, curr.z,  ridgeX, ridgeY, ridgeZ,  ridgeX, roofBaseAdj, ridgeZ,
                        curr.x, cy, curr.z,  ridgeX, roofBaseAdj, ridgeZ,  curr.x, roofBaseAdj, curr.z
                    );
                }
                
                // Demi-pignon 2 : point faîtage → next
                if (ridgeH > 0.05 || nextRoofH > 0.05) {
                    pignonVerts.push(
                        ridgeX, ridgeY, ridgeZ,  next.x, ny, next.z,  next.x, roofBaseAdj, next.z,
                        ridgeX, ridgeY, ridgeZ,  next.x, roofBaseAdj, next.z,  ridgeX, roofBaseAdj, ridgeZ
                    );
                }
            } else {
                // Arête qui ne traverse pas le faîtage : mur pignon simple
                if (currRoofH < 0.15 && nextRoofH < 0.15) continue;
                
                const cy = roofBaseAdj + currRoofH;
                const ny = roofBaseAdj + nextRoofH;
                pignonVerts.push(
                    curr.x, cy, curr.z,  next.x, ny, next.z,  next.x, roofBaseAdj, next.z,
                    curr.x, cy, curr.z,  next.x, roofBaseAdj, next.z,  curr.x, roofBaseAdj, curr.z
                );
            }
        }
        
        if (pignonVerts.length > 0) {
            const wallGeo = new THREE.BufferGeometry();
            wallGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(pignonVerts), 3));
            wallGeo.computeVertexNormals();
            const wallMat = new THREE.MeshPhongMaterial({
                color: wallColor, side: THREE.DoubleSide,
                specular: 0x111111, shininess: 5
            });
            const wallMesh = new THREE.Mesh(wallGeo, wallMat);
            wallMesh.castShadow = true;
            this.scene.add(wallMesh);
            this.buildings.push(wallMesh);
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    //  TOIT LiDAR DIRECT — Maillage depuis les hauteurs MNS réelles
    //  (résolution 50cm IGN LiDAR HD)
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * Crée un toit 3D directement depuis les points MNS LiDAR échantillonnés,
     * sans passer par une forme paramétrique (gable, hip, etc.).
     * 
     * Avantages :
     * - Capture la géométrie réelle : lucarnes, cheminées, vallées, toits asymétriques
     * - Fonctionne pour les bâtiments en L, T, ou formes irrégulières
     * - Résolution 50cm avec le LiDAR HD IGN
     * 
     * Approche :
     * 1. Construit un index spatial (cellules) des roofPoints
     * 2. Crée une grille OBB-alignée dense (résol ~40cm)
     * 3. Pour chaque nœud, interpole la hauteur MNS par IDW (k=4 voisins)
     * 4. Clip au polygone réel du bâtiment
     * 5. Crée le mesh + murs pignons
     * 
     * @param {Array} localCoords - Sommets du polygone [{x, z}]
     * @param {Object} obb - {cx, cz, angle, longDim, shortDim}
     * @param {number} roofBaseY - Y du haut des murs (terrainH + wallH)
     * @param {Array} roofPoints - Points LiDAR {x, z, mns, mnt, mnh}
     * @param {string} roofType - Type de couverture (tuile, ardoise, etc.)
     * @param {string} wallType - Type de mur
     * @param {number} eaveHeight - Hauteur d'acrotère/gouttière au-dessus du sol (percentile bas MNH)
     */
    _createDirectLidarRoof(localCoords, obb, roofBaseY, roofPoints, roofType, wallType, eaveHeight) {
        if (!roofPoints || roofPoints.length < 6 || !localCoords || localCoords.length < 3) return;
        
        console.log(`🛰️ Toit LiDAR direct: ${roofPoints.length} points MNS, résolution grille ~0.4m`);
        
        // ── 1. Index spatial des roofPoints pour accès rapide ──
        // Cellules de 1m × 1m dans l'espace local
        const cellSize = 1.0;
        const spatialIndex = {};
        
        for (const p of roofPoints) {
            const ci = Math.floor(p.x / cellSize);
            const cj = Math.floor(p.z / cellSize);
            const key = `${ci},${cj}`;
            if (!spatialIndex[key]) spatialIndex[key] = [];
            spatialIndex[key].push(p);
        }
        
        /**
         * Interpolation IDW (Inverse Distance Weighting) depuis les k plus proches points.
         * Retourne la hauteur MNH interpolée, ou null si pas assez de voisins.
         */
        const interpolateMNH = (wx, wz, kNearest = 4, maxDist = 3.0) => {
            const ci = Math.floor(wx / cellSize);
            const cj = Math.floor(wz / cellSize);
            
            // Collecter les candidats dans un voisinage 3×3 de cellules
            const candidates = [];
            for (let di = -2; di <= 2; di++) {
                for (let dj = -2; dj <= 2; dj++) {
                    const cell = spatialIndex[`${ci + di},${cj + dj}`];
                    if (cell) {
                        for (const p of cell) {
                            const dx = p.x - wx;
                            const dz = p.z - wz;
                            const dist = Math.sqrt(dx * dx + dz * dz);
                            if (dist < maxDist) {
                                candidates.push({ mnh: p.mnh, dist: dist });
                            }
                        }
                    }
                }
            }
            
            if (candidates.length === 0) return null;
            
            // Trier par distance et garder les k plus proches
            candidates.sort((a, b) => a.dist - b.dist);
            const k = Math.min(kNearest, candidates.length);
            
            // Cas exact : point très proche
            if (candidates[0].dist < 0.05) return candidates[0].mnh;
            
            // IDW avec puissance 2
            let sumW = 0, sumWH = 0;
            for (let i = 0; i < k; i++) {
                const w = 1 / (candidates[i].dist * candidates[i].dist + 0.01);
                sumW += w;
                sumWH += w * candidates[i].mnh;
            }
            return sumWH / sumW;
        };
        
        // ── 2. Paramètres de grille OBB ──
        const cosA = Math.cos(-obb.angle);
        const sinA = Math.sin(-obb.angle);
        const halfShort = obb.shortDim / 2;
        const halfLong = obb.longDim / 2;
        
        // Résolution : ~40cm pour capturer les détails de toit
        const gridStep = 0.4;
        const nAcross = Math.max(8, Math.round(obb.shortDim / gridStep));
        const nAlong = Math.max(8, Math.round(obb.longDim / gridStep));
        
        // Marge intérieure pour ne pas dépasser le polygone
        const margin = 0.15;
        const effHalfShort = halfShort - margin;
        const effHalfLong = halfLong - margin;
        
        // Abaisser légèrement pour pénétrer dans les murs (anti-interstice)
        const roofBaseAdj = roofBaseY - 0.15;
        
        // ── 3. Point-in-polygon test ──
        const isInPolygon = (wx, wz) => {
            let inside = false;
            const n = localCoords.length;
            for (let i = 0, j = n - 1; i < n; j = i++) {
                const xi = localCoords[i].x, zi = localCoords[i].z;
                const xj = localCoords[j].x, zj = localCoords[j].z;
                if (((zi > wz) !== (zj > wz)) &&
                    (wx < (xj - xi) * (wz - zi) / (zj - zi) + xi)) {
                    inside = !inside;
                }
            }
            return inside;
        };
        
        // ── 4. Créer la grille de sommets avec hauteurs MNS réelles ──
        const positions = [];
        const uvs = [];
        const gridIdx = [];
        let vertexCount = 0;
        let interpolatedCount = 0;
        let missedCount = 0;
        
        for (let i = 0; i <= nAcross; i++) {
            gridIdx[i] = [];
            const across = -effHalfShort + (i / nAcross) * effHalfShort * 2;
            
            for (let j = 0; j <= nAlong; j++) {
                const along = -effHalfLong + (j / nAlong) * effHalfLong * 2;
                
                // Convertir en coordonnées monde
                const wx = obb.cx + along * cosA + across * sinA;
                const wz = obb.cz - along * sinA + across * cosA;
                
                if (!isInPolygon(wx, wz)) {
                    gridIdx[i][j] = -1;
                    continue;
                }
                
                // Interpoler la hauteur MNH depuis les points LiDAR
                const mnh = interpolateMNH(wx, wz, 4, 3.0);
                if (mnh === null || mnh < 1.0) {
                    gridIdx[i][j] = -1;
                    missedCount++;
                    continue;
                }
                
                // Hauteur au-dessus de la base du toit
                // mnh = hauteur au-dessus du sol MNT
                // eaveHeight = hauteur de l'acrotère (percentile bas du MNH)
                // Le toit commence à eaveHeight → h relative = mnh - eaveHeight
                const h = Math.max(0, mnh - eaveHeight);
                
                positions.push(wx, roofBaseAdj + h, wz);
                uvs.push(along / 4.0, across / 4.0);
                gridIdx[i][j] = vertexCount++;
                interpolatedCount++;
            }
        }
        
        console.log(`  📊 Grille ${nAcross}×${nAlong}: ${interpolatedCount} pts interpolés, ${missedCount} manqués`);
        
        if (vertexCount < 3) {
            console.warn('⚠️ _createDirectLidarRoof: pas assez de sommets, fallback vers paramétrique');
            return false; // Signaler l'échec pour fallback
        }
        
        // ── 5. Créer les triangles ──
        const indices = [];
        for (let i = 0; i < nAcross; i++) {
            for (let j = 0; j < nAlong; j++) {
                const i00 = gridIdx[i][j];
                const i10 = gridIdx[i + 1][j];
                const i01 = gridIdx[i][j + 1];
                const i11 = gridIdx[i + 1][j + 1];
                
                if (i00 >= 0 && i10 >= 0 && i01 >= 0) {
                    indices.push(i00, i10, i01);
                }
                if (i10 >= 0 && i11 >= 0 && i01 >= 0) {
                    indices.push(i10, i11, i01);
                }
            }
        }
        
        if (indices.length < 3) return false;
        
        // ── 6. Lissage Laplacien des POSITIONS (supprime le bruit LiDAR) ──
        // Appliqué AVANT la création du mesh pour adoucir les bosses
        this._smoothPositions(positions, indices, vertexCount, 3, 0.3);
        
        // ── 7. Créer le mesh du toit ──
        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
        geo.setIndex(indices);
        geo.computeVertexNormals();
        
        // Lissage Laplacien des normales pour adoucir les transitions entre faces
        this._smoothNormals(geo, 3);
        
        const roofTex = this._getRoofTexture(roofType);
        const roofMat = new THREE.MeshPhongMaterial({
            map: roofTex,
            side: THREE.DoubleSide,
            specular: 0x222222,
            shininess: roofType === 'zinc' || roofType === 'metal' ? 30 : 5,
        });
        const roofMesh = new THREE.Mesh(geo, roofMat);
        roofMesh.castShadow = true;
        roofMesh.receiveShadow = true;
        this.scene.add(roofMesh);
        this.buildings.push(roofMesh);
        
        // ── 7. Murs pignons (skirt) — combler entre le toit et le haut des murs ──
        const wallColorMap = {
            plaster: 0xE8DCC8, brick: 0xB5651D, stone: 0xA09080,
            concrete: 0xB0B0B0, industrial: 0x888888, commercial: 0xD0D0D0
        };
        const wallColor = wallColorMap[wallType] || 0xE8DCC8;
        
        const pignonVerts = [];
        const nEdgeSamples = Math.max(nAcross, 12);
        
        for (let e = 0; e < localCoords.length; e++) {
            const curr = localCoords[e];
            const next = localCoords[(e + 1) % localCoords.length];
            
            const edgeX = next.x - curr.x;
            const edgeZ = next.z - curr.z;
            const edgeLen = Math.sqrt(edgeX * edgeX + edgeZ * edgeZ);
            if (edgeLen < 0.3) continue;
            
            for (let s = 0; s < nEdgeSamples; s++) {
                const t1 = s / nEdgeSamples;
                const t2 = (s + 1) / nEdgeSamples;
                
                const x1 = curr.x + t1 * edgeX;
                const z1 = curr.z + t1 * edgeZ;
                const x2 = curr.x + t2 * edgeX;
                const z2 = curr.z + t2 * edgeZ;
                
                // Hauteur LiDAR aux 2 points de l'arête
                const mnh1 = interpolateMNH(x1, z1, 3, 2.5);
                const mnh2 = interpolateMNH(x2, z2, 3, 2.5);
                
                const h1 = mnh1 !== null ? Math.max(0, mnh1 - eaveHeight) : 0;
                const h2 = mnh2 !== null ? Math.max(0, mnh2 - eaveHeight) : 0;
                
                if (h1 < 0.1 && h2 < 0.1) continue;
                
                const y1top = roofBaseAdj + h1;
                const y2top = roofBaseAdj + h2;
                
                pignonVerts.push(
                    x1, roofBaseAdj, z1,  x2, roofBaseAdj, z2,  x2, y2top, z2,
                    x1, roofBaseAdj, z1,  x2, y2top, z2,      x1, y1top, z1
                );
            }
        }
        
        if (pignonVerts.length > 0) {
            const wallGeo = new THREE.BufferGeometry();
            wallGeo.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(pignonVerts), 3));
            wallGeo.computeVertexNormals();
            const wallMat = new THREE.MeshPhongMaterial({
                color: wallColor, side: THREE.DoubleSide,
                specular: 0x111111, shininess: 5
            });
            const wallMesh = new THREE.Mesh(wallGeo, wallMat);
            wallMesh.castShadow = true;
            this.scene.add(wallMesh);
            this.buildings.push(wallMesh);
        }
        
        console.log('✅ Toit LiDAR direct créé avec succès');
        return true; // Succès
    }
    
    /**
     * Lissage Laplacien des POSITIONS de sommets.
     * Aplatit les bosses/creux du maillage LiDAR en moyennant chaque sommet
     * avec ses voisins. Ne lisse que la composante Y (hauteur) pour préserver
     * la forme en plan du bâtiment.
     * @param {Array} positions - Tableau flat [x0,y0,z0, x1,y1,z1, ...]
     * @param {Array} indices - Tableau d'indices de triangles
     * @param {number} vertexCount - Nombre de sommets
     * @param {number} iterations - Nombre de passes de lissage
     * @param {number} lambda - Facteur de lissage (0=rien, 1=moyenne pure des voisins)
     */
    _smoothPositions(positions, indices, vertexCount, iterations, lambda) {
        // Construire la liste d'adjacence
        const neighbors = new Array(vertexCount);
        for (let i = 0; i < vertexCount; i++) neighbors[i] = [];
        
        for (let i = 0; i < indices.length; i += 3) {
            const a = indices[i], b = indices[i+1], c = indices[i+2];
            if (neighbors[a].indexOf(b) === -1) neighbors[a].push(b);
            if (neighbors[a].indexOf(c) === -1) neighbors[a].push(c);
            if (neighbors[b].indexOf(a) === -1) neighbors[b].push(a);
            if (neighbors[b].indexOf(c) === -1) neighbors[b].push(c);
            if (neighbors[c].indexOf(a) === -1) neighbors[c].push(a);
            if (neighbors[c].indexOf(b) === -1) neighbors[c].push(b);
        }
        
        for (let iter = 0; iter < iterations; iter++) {
            const newY = new Float32Array(vertexCount);
            
            for (let i = 0; i < vertexCount; i++) {
                const yi = positions[i * 3 + 1]; // Y actuel
                const nb = neighbors[i];
                
                if (nb.length === 0) {
                    newY[i] = yi;
                    continue;
                }
                
                // Moyenne des Y des voisins
                let sumY = 0;
                for (let j = 0; j < nb.length; j++) {
                    sumY += positions[nb[j] * 3 + 1];
                }
                const avgY = sumY / nb.length;
                
                // Interpolation vers la moyenne : Y = Y + lambda * (avg - Y)
                newY[i] = yi + lambda * (avgY - yi);
            }
            
            // Appliquer les nouvelles hauteurs
            for (let i = 0; i < vertexCount; i++) {
                positions[i * 3 + 1] = newY[i];
            }
        }
    }
    
    /**
     * Lissage Laplacien des normales d'un BufferGeometry.
     * Adoucit les irrégularités du maillage LiDAR sans modifier les positions.
     * @param {THREE.BufferGeometry} geo
     * @param {number} iterations - Nombre de passes de lissage
     */
    _smoothNormals(geo, iterations) {
        const normals = geo.getAttribute('normal');
        if (!normals) return;
        
        const index = geo.getIndex();
        if (!index) return;
        
        const count = normals.count;
        
        // Construire la liste d'adjacence des sommets
        const neighbors = new Array(count);
        for (let i = 0; i < count; i++) neighbors[i] = new Set();
        
        const indexArray = index.array;
        for (let i = 0; i < indexArray.length; i += 3) {
            const a = indexArray[i], b = indexArray[i+1], c = indexArray[i+2];
            neighbors[a].add(b); neighbors[a].add(c);
            neighbors[b].add(a); neighbors[b].add(c);
            neighbors[c].add(a); neighbors[c].add(b);
        }
        
        for (let iter = 0; iter < iterations; iter++) {
            const smoothed = new Float32Array(count * 3);
            
            for (let i = 0; i < count; i++) {
                let nx = normals.getX(i);
                let ny = normals.getY(i);
                let nz = normals.getZ(i);
                let w = 1.0;
                
                for (const j of neighbors[i]) {
                    nx += normals.getX(j) * 0.5;
                    ny += normals.getY(j) * 0.5;
                    nz += normals.getZ(j) * 0.5;
                    w += 0.5;
                }
                
                // Normaliser
                const len = Math.sqrt(nx*nx + ny*ny + nz*nz) || 1;
                smoothed[i*3] = nx / len;
                smoothed[i*3+1] = ny / len;
                smoothed[i*3+2] = nz / len;
            }
            
            for (let i = 0; i < count; i++) {
                normals.setXYZ(i, smoothed[i*3], smoothed[i*3+1], smoothed[i*3+2]);
            }
        }
        
        normals.needsUpdate = true;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // TOIT HEIGHT-FIELD : empreinte BD TOPO + équations de plan RANSAC
    // ─────────────────────────────────────────────────────────────────────
    // Principe : pour chaque nœud d'une grille 50 cm couvrant l'empreinte
    //   BD TOPO, la hauteur de toit = max(bh, max_plan(a*x + b*y + c)).
    // Le faîtage, les noues et les angles de croupe émergent naturellement
    // à l'intersection des plans. Alignement toit/murs parfait (même footprint).
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Teste si le point (px, py) est à l'intérieur d'un polygone 2D.
     * Algorithme ray-casting – fonctionne sur tout polygone simple.
     */
    // ── COPC LiDAR HD brut ─────────────────────────────────────────────────────

    /** Retire de la scène les meshes du toit PV (isPVRoof=true). */
    _removePVRoofMeshes() {
        this.buildings = this.buildings.filter(m => {
            if (!m.userData?.isPVRoof) return true;
            this.scene.remove(m);
            m.geometry?.dispose();
            if (Array.isArray(m.material)) m.material.forEach(mt => mt.dispose());
            else m.material?.dispose();
            return false;
        });
    }

    /**
     * Lance en arrière-plan un appel POST /api/lidar/copc-grid (~15-35 s).
     * Rebuilt le toit depuis la grille Z brute LiDAR (pixel-perfect) :
     *   - chaque cellule = médiane des points LiDAR dans 1 carré de 0.5m
     *   - sheds, lanterneaux, noues, faîtages rendus fidèlement
     *   - RANSAC lancé en parallèle uniquement pour les infos d'orientation PV
     */
    async _fetchAndApplyCOPCRoof(lat, lon) {
        if (!this.pvBuildingCoords?.length) return;

        const wallH = this._mainBldgBh ?? 6;
        const resp  = await fetch('/api/lidar/copc-grid', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                lat,
                lon,
                building_coords: this.pvBuildingCoords,
                step:            0.5,
                wall_h:          wallH,
                include_planes:  true,   // RANSAC pour orientation PV uniquement
            }),
            signal: AbortSignal.timeout(90_000),
        });
        if (!resp.ok) {
            const _errBody = await resp.json().catch(() => ({}));
            throw new Error(`HTTP ${resp.status}: ${_errBody.error || ''}`);
        }
        const data = await resp.json();
        if (!data.success || !data.grid?.length) {
            throw new Error(data.error || 'Aucune grille COPC retournée');
        }

        console.log(`✅ COPC grid: ${data.nb_points} pts → ${data.nx}×${data.ny} cellules (${data.coverage_pct}% couverture)`);

        // Injecter dans lidarData
        if (!this.lidarData.building_hd) this.lidarData.building_hd = {};
        this.lidarData.building_hd.copc_grid   = data;
        if (data.roof_planes?.length)
            this.lidarData.building_hd.roof_planes = data.roof_planes;
        if (data.center)
            this.lidarData.building_hd.building_center = data.center;

        // Supprimer le toit MNH et reconstruire depuis la grille brute
        this._removePVRoofMeshes();

        const bldgCenter = data.center;
        const bh         = this._mainBldgBh      ?? 6;
        const terrainH   = this._mainBldgTerrainH ?? 0;
        const roofType   = this._mainBldgRoofType ?? 'default';

        // Rendu principal : grille Z brute (pixel-perfect)
        const rebuilt = this._buildRoofFromGrid(
            data, bldgCenter, bh, terrainH,
            this.pvBuildingCoords, roofType, /* isPVBuilding */ true
        );
        if (!rebuilt) {
            // Fallback : height-field RANSAC → fallback polygone
            const planes = data.roof_planes;
            if (planes?.length) {
                if (!this._buildRoofHeightField(planes, bldgCenter, bh, terrainH, this.pvBuildingCoords, roofType, true))
                    this._buildRoofFromPlanes(planes, bldgCenter, bh, terrainH, roofType, true);
            }
        }

        // Mise à jour roofPanelsInfo depuis les plans RANSAC (orientation PV)
        const _copcOBB = this.roofPanelsInfo?.buildingOBB;
        if (_copcOBB && data.roof_planes?.length) {
            const _panels = this._computeRoofPanelsInfoFromPlanes(
                data.roof_planes, _copcOBB, terrainH, bh, bldgCenter, roofType
            );
            if (_panels) {
                _panels.buildingOBB         = _copcOBB;
                _panels.buildingTerrainH    = terrainH;
                _panels.buildingWallH       = bh;
                _panels.buildingLocalCoords = this.roofPanelsInfo.buildingLocalCoords;
                _panels.buildingCenterGeo   = this.roofPanelsInfo.buildingCenterGeo;
                this.roofPanelsInfo = _panels;
            }
        }

        this._showCOPCBanner(data.nb_points, data.nx, data.ny);
    }

    /** Affiche un bandeau "Toit LiDAR HD" discret pendant 6 s. */
    _showCOPCBanner(nPoints, nx, ny) {
        try {
            let banner = document.getElementById('copc-roof-banner');
            if (!banner) {
                banner = document.createElement('div');
                banner.id = 'copc-roof-banner';
                Object.assign(banner.style, {
                    position:   'fixed',
                    bottom:     '70px',
                    left:       '50%',
                    transform:  'translateX(-50%)',
                    background: 'rgba(16,185,129,0.92)',
                    color:      '#fff',
                    padding:    '8px 18px',
                    borderRadius: '8px',
                    fontSize:   '13px',
                    fontWeight: '600',
                    zIndex:     '9999',
                    boxShadow:  '0 2px 8px rgba(0,0,0,0.25)',
                    transition: 'opacity 0.4s',
                });
                document.body.appendChild(banner);
            }
            banner.textContent = `🌿 Toit recalculé – LiDAR HD brut ${nx}×${ny} pts · ${nPoints} mesures`;
            banner.style.opacity = '1';
            clearTimeout(this._copcBannerTimer);
            this._copcBannerTimer = setTimeout(() => {
                banner.style.opacity = '0';
                setTimeout(() => banner.remove(), 500);
            }, 6000);
        } catch (_) { /* pas critique */ }
    }

    // ───────────────────────────────────────────────────────────────────────────

    _pointInPoly2D(px, py, poly) {
        let inside = false;
        for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
            const xi = poly[i][0], yi = poly[i][1];
            const xj = poly[j][0], yj = poly[j][1];
            if ((yi > py) !== (yj > py) && px < (xj - xi) * (py - yi) / (yj - yi) + xi) {
                inside = !inside;
            }
        }
        return inside;
    }

    /**
     * Dilate un polygone (concave ou convexe) par décalage perpendiculaire
     * de chaque arête de `d` mètres vers l'extérieur.
     * Fonctionne correctement sur les polygones en L, T, U, multi-sheds.
     * @param {Array} poly  - [[x,y], ...] polygone (sens quelconque)
     * @param {number} d    - distance de dilatation en mètres (>0 = dilation)
     * @returns {Array}     - nouveau polygone dilaté
     */
    _expandPolygonEdges(poly, d) {
        const n = poly.length;
        if (n < 3) return poly;
        // Calculer le sens (clockwise ou counter-clockwise) pour orienter les normales
        let area = 0;
        for (let i = 0, j = n - 1; i < n; j = i++) {
            area += poly[j][0] * poly[i][1] - poly[i][0] * poly[j][1];
        }
        const sign = area > 0 ? 1 : -1; // CCW → sign=1 → normal perpendiculaire vers ext

        // Pour chaque arête, calculer la droite décalée de `d` vers l'extérieur
        // puis intersecter les droites adjacentes pour obtenir les nouveaux sommets.
        const offsetLines = [];
        for (let i = 0; i < n; i++) {
            const [x1, y1] = poly[i], [x2, y2] = poly[(i + 1) % n];
            const ex = x2 - x1, ey = y2 - y1;
            const len = Math.sqrt(ex * ex + ey * ey) || 1;
            // Normale perpendiculaire vers l'extérieur
            const nx_ = -ey / len * sign * d;
            const ny_ =  ex / len * sign * d;
            offsetLines.push({ x1: x1 + nx_, y1: y1 + ny_, x2: x2 + nx_, y2: y2 + ny_ });
        }

        // Intersection de deux droites consécutives
        const result = [];
        for (let i = 0; i < n; i++) {
            const a = offsetLines[(i + n - 1) % n];
            const b = offsetLines[i];
            const dx1 = a.x2 - a.x1, dy1 = a.y2 - a.y1;
            const dx2 = b.x2 - b.x1, dy2 = b.y2 - b.y1;
            const denom = dx1 * dy2 - dy1 * dx2;
            if (Math.abs(denom) < 1e-10) {
                // Arêtes parallèles → utiliser le point décalé directement
                result.push([b.x1, b.y1]);
            } else {
                const t = ((b.x1 - a.x1) * dy2 - (b.y1 - a.y1) * dx2) / denom;
                result.push([a.x1 + t * dx1, a.y1 + t * dy1]);
            }
        }
        return result;
    }

    /**
     * Construit le mesh de toit en projetant une grille 50 cm sur l'empreinte
     * BD TOPO et en calculant la hauteur en chaque nœud depuis les équations
     * de plan RANSAC (mnh = a*x + b*y + c, coordonnées métriques polygon_2d).
     *
     * Avantages vs _buildRoofFromPlanes :
     *  - Forme = empreinte BD TOPO → alignement murs/toit parfait
     *  - Gère les bâtiments complexes (L, T, U) sans OBB
     *  - Faîtage, croupe, noues emergent naturellement de max(plans)
     *  - Pas d'expansion Minkowski ni de clipping nécessaires
     *
     * @returns {boolean} true si le mesh a été créé
     */
    _buildRoofHeightField(planes, bldgCenter, bh, terrainH, buildingCoords, roofType, isPVBuilding = false) {
        if (!planes?.length || !buildingCoords || buildingCoords.length < 3) return false;

        const LNG_TO_M   = this.LAT_TO_M * Math.cos(bldgCenter.lat * Math.PI / 180);
        const bldgOffsetX = (bldgCenter.lon - this.centerLon) * LNG_TO_M;
        const bldgOffsetZ = -(bldgCenter.lat - this.centerLat) * this.LAT_TO_M;

        // ── 1. Footprint BD TOPO → espace métrique polygon_2d ──────────────
        // x = Est positif (même axe que polygon_2d rx)
        // y = Nord positif (même axe que polygon_2d ry)
        let fp = buildingCoords.map(([lon, lat]) => [
            (lon - bldgCenter.lon) * LNG_TO_M,
            (lat - bldgCenter.lat) * this.LAT_TO_M
        ]);
        // Supprimer le point de fermeture dupliqué si présent
        if (fp.length > 3) {
            const [x0, y0] = fp[0], [xl, yl] = fp[fp.length - 1];
            if ((x0 - xl) ** 2 + (y0 - yl) ** 2 < 0.01) fp.pop();
        }
        if (fp.length < 3) return false;

        // ── 2. Filtrer les plans invalides ──────────────────────────────────
        const fpXs = fp.map(p => p[0]), fpYs = fp.map(p => p[1]);
        const fpXMin = Math.min(...fpXs) - 1.5, fpXMax = Math.max(...fpXs) + 1.5;
        const fpYMin = Math.min(...fpYs) - 1.5, fpYMax = Math.max(...fpYs) + 1.5;

        const validPlanes = planes.filter(plane => {
            const poly = plane.polygon_2d;
            if (!poly || poly.length < 3) return false;
            // Filtre acrotère : aire trop petite ou trop étroite
            let sa = 0;
            for (let i = 0, j = poly.length - 1; i < poly.length; j = i++)
                sa += poly[j][0] * poly[i][1] - poly[i][0] * poly[j][1];
            const area = Math.abs(sa) / 2;
            const bbW  = Math.max(...poly.map(p => p[0])) - Math.min(...poly.map(p => p[0]));
            const bbH  = Math.max(...poly.map(p => p[1])) - Math.min(...poly.map(p => p[1]));
            if (area < 4 || area / Math.max(bbW, bbH, 0.1) < 1.5) return false;
            // Filtre toit adjacent : centroïde du plan hors de l'empreinte + 1.5 m
            const cx = poly.reduce((s, p) => s + p[0], 0) / poly.length;
            const cy = poly.reduce((s, p) => s + p[1], 0) / poly.length;
            return cx >= fpXMin && cx <= fpXMax && cy >= fpYMin && cy <= fpYMax;
        });

        if (!validPlanes.length) {
            console.log('⚠️ _buildRoofHeightField: aucun plan valide après filtrage');
            return false;
        }

        // Précomputer les bboxes AABB (pré-filtre rapide) ET les polygones dilatés (+0.5 m).
        // − L'AABB évite les itérations inutiles sur des plans éloignés
        // − Le test polygone exact (avec dilatation 0.5 m côté centroïde) évite l'extrapolation
        //   pour les bâtiments orientés en biais : un pan 10m×100m incliné à 45° a une AABB
        //   ~78m×78m ; sans test polygone, les 30 AABB se chevauchent → max() sur tous les plans
        //   → une seule grande surface inclinée au lieu de sheds indépendants.
        const POLY_EXPAND = 0.5; // m — dilatation du polygone (bords RANSAC légèrement en retrait)
        const planeBboxes = validPlanes.map(p => {
            const pxs = p.polygon_2d.map(pt => pt[0]);
            const pys = p.polygon_2d.map(pt => pt[1]);
            // Centroïde pour la dilatation
            const cxP = pxs.reduce((a, b) => a + b, 0) / pxs.length;
            const cyP = pys.reduce((a, b) => a + b, 0) / pys.length;
            // Polygone dilaté depuis le centroïde (+POLY_EXPAND m)
            const expandedPoly = p.polygon_2d.map(([px, py]) => {
                const dx = px - cxP, dy = py - cyP;
                const d = Math.sqrt(dx * dx + dy * dy) || 1;
                return [px + dx / d * POLY_EXPAND, py + dy / d * POLY_EXPAND];
            });
            return {
                xMin: Math.min(...pxs) - POLY_EXPAND, xMax: Math.max(...pxs) + POLY_EXPAND,
                yMin: Math.min(...pys) - POLY_EXPAND, yMax: Math.max(...pys) + POLY_EXPAND,
                expandedPoly,
            };
        });

        // ── 3. Grille adaptative sur la bbox du footprint ────────────────────
        // Résolution cible 0.5 m. Si la bbox est trop grande, on augmente le pas
        // par paliers de 0.25 m jusqu'à ce que nx×ny ≤ 12 000 (≈ 3 000 m²/0.25).
        // Cela préserve la meilleure résolution possible sans jamais tomber en fallback.
        const xMin = Math.min(...fpXs), xMax = Math.max(...fpXs);
        const yMin = Math.min(...fpYs), yMax = Math.max(...fpYs);
        const MAX_NODES = 12000;
        let STEP = 0.5;
        let nx = Math.max(3, Math.round((xMax - xMin) / STEP) + 1);
        let ny = Math.max(3, Math.round((yMax - yMin) / STEP) + 1);
        if (nx * ny > MAX_NODES) {
            // STEP minimal pour tenir dans MAX_NODES (arrondi au 0.25 m supérieur)
            const rawStep = Math.sqrt((xMax - xMin) * (yMax - yMin) / MAX_NODES);
            STEP = Math.max(0.5, Math.ceil(rawStep / 0.25) * 0.25);
            nx = Math.max(3, Math.round((xMax - xMin) / STEP) + 1);
            ny = Math.max(3, Math.round((yMax - yMin) / STEP) + 1);
            console.log(`📐 Grille adaptée: STEP=${STEP.toFixed(2)}m → ${nx}×${ny} nœuds`);
        }
        const stepX = nx > 1 ? (xMax - xMin) / (nx - 1) : STEP;
        const stepY = ny > 1 ? (yMax - yMin) / (ny - 1) : STEP;

        // ── 4. Calcul du champ de hauteur ────────────────────────────────────
        const heightArr = new Float32Array(nx * ny);
        const insideArr = new Uint8Array(nx * ny);

        for (let iy = 0; iy < ny; iy++) {
            const gy = yMin + iy * stepY;
            for (let ix = 0; ix < nx; ix++) {
                const gx = xMin + ix * stepX;
                const idx = iy * nx + ix;
                if (!this._pointInPoly2D(gx, gy, fp)) continue;
                insideArr[idx] = 1;
                // Hauteur = max(corniche, max des plans RANSAC dans leur propre zone)
                // On restreint chaque plan à sa bbox polygon_2d pour éviter que des
                // plans parallèles (sheds) ne s'extrapolent sur tout le footprint.
                let h = bh;
                for (let pi = 0; pi < validPlanes.length; pi++) {
                    const pb = planeBboxes[pi];
                    // Rejet rapide par AABB (pré-filtre) — essentiel pour les bâtiments en sheds
                    if (gx < pb.xMin || gx > pb.xMax || gy < pb.yMin || gy > pb.yMax) continue;
                    // Test polygone dilaté (+0.5 m) : précision sans AABB-only ni bords trop serrés
                    if (!this._pointInPoly2D(gx, gy, pb.expandedPoly)) continue;
                    const p = validPlanes[pi];
                    const mnh = p.mnh_a * gx + p.mnh_b * gy + p.mnh_c;
                    if (mnh > h) h = mnh;
                }
                // Plancher à bh (évite que le toit descende sous la corniche)
                heightArr[idx] = Math.max(bh, h);
            }
        }

        // ── 5. Construire les buffers de géométrie ────────────────────────────
        const vertexMap = new Int32Array(nx * ny).fill(-1);
        const positions = [], uvs = [];
        let vi = 0;

        for (let iy = 0; iy < ny; iy++) {
            const gy = yMin + iy * stepY;
            for (let ix = 0; ix < nx; ix++) {
                const idx = iy * nx + ix;
                if (!insideArr[idx]) continue;
                const gx = xMin + ix * stepX;
                positions.push(bldgOffsetX + gx, terrainH + heightArr[idx], bldgOffsetZ - gy);
                uvs.push(gx / 4, gy / 4);
                vertexMap[idx] = vi++;
            }
        }

        if (positions.length < 9) return false;

        // Triangulation de la grille irrégulière
        const faceIdx = [];
        for (let iy = 0; iy < ny - 1; iy++) {
            for (let ix = 0; ix < nx - 1; ix++) {
                const v00 = vertexMap[ iy      * nx + ix    ];
                const v10 = vertexMap[ iy      * nx + ix + 1];
                const v01 = vertexMap[(iy + 1) * nx + ix    ];
                const v11 = vertexMap[(iy + 1) * nx + ix + 1];
                if (v00 >= 0 && v10 >= 0 && v01 >= 0) faceIdx.push(v00, v10, v01);
                if (v10 >= 0 && v11 >= 0 && v01 >= 0) faceIdx.push(v10, v11, v01);
            }
        }
        if (faceIdx.length < 3) return false;

        // ── 6. Créer le mesh Three.js ─────────────────────────────────────────
        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        geo.setAttribute('uv',       new THREE.Float32BufferAttribute(uvs, 2));
        geo.setIndex(faceIdx);
        geo.computeVertexNormals();

        const mesh = new THREE.Mesh(geo, new THREE.MeshPhongMaterial({
            map: this._getRoofTexture(roofType),
            side: THREE.DoubleSide, specular: 0x222222, shininess: 5,
            polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1,
        }));
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.userData = { source: 'heightfield', nPlanes: validPlanes.length, isPVRoof: isPVBuilding };
        this.scene.add(mesh);
        this.buildings.push(mesh);

        // ── 7. Jupe (skirt) le long du périmètre du footprint ────────────────
        // Comble l'interstice éventuel entre haut des murs (bh) et bord du toit.
        // Utilise les équations de plan pour connaître la hauteur en chaque sommet.
        const skirtMat = new THREE.MeshPhongMaterial({
            map: this._getRoofTexture(roofType),
            side: THREE.DoubleSide, specular: 0x222222, shininess: 5,
        });
        const skirtPos = [];
        const n_fp = fp.length;
        for (let i = 0; i < n_fp; i++) {
            const [x0, y0] = fp[i], [x1, y1] = fp[(i + 1) % n_fp];
            // Hauteur au sommet du footprint : max(bh, max mnh)
            const getH = (x, y) => {
                let h = bh;
                for (let pi = 0; pi < validPlanes.length; pi++) {
                    const pb = planeBboxes[pi];
                    if (x < pb.xMin || x > pb.xMax || y < pb.yMin || y > pb.yMax) continue;
                    if (!this._pointInPoly2D(x, y, pb.expandedPoly)) continue;
                    const p = validPlanes[pi];
                    const m = p.mnh_a * x + p.mnh_b * y + p.mnh_c;
                    if (m > h) h = m;
                }
                return Math.max(bh, h);
            };
            const h0 = getH(x0, y0), h1 = getH(x1, y1);
            const hBot = bh - 0.15; // légèrement sous la corniche pour couvrir le joint
            // Quad : (x0,bh−0.15), (x1,bh−0.15), (x1,h1), (x0,h0)
            skirtPos.push(
                bldgOffsetX + x0, terrainH + hBot,  bldgOffsetZ - y0,
                bldgOffsetX + x1, terrainH + hBot,  bldgOffsetZ - y1,
                bldgOffsetX + x1, terrainH + h1,    bldgOffsetZ - y1,
                bldgOffsetX + x0, terrainH + h0,    bldgOffsetZ - y0,
            );
        }
        if (skirtPos.length >= 12) {
            const skirtGeo = new THREE.BufferGeometry();
            skirtGeo.setAttribute('position', new THREE.Float32BufferAttribute(skirtPos, 3));
            const skirtIdx = [];
            const nQuads = skirtPos.length / 12;
            for (let q = 0; q < nQuads; q++) {
                const b = q * 4;
                skirtIdx.push(b, b+1, b+2,  b, b+2, b+3);
            }
            skirtGeo.setIndex(skirtIdx);
            skirtGeo.computeVertexNormals();
            const sm = new THREE.Mesh(skirtGeo, skirtMat);
            sm.castShadow = sm.receiveShadow = true;
            sm.userData = { source: 'heightfield-skirt', isPVRoof: isPVBuilding };
            this.scene.add(sm);
            this.buildings.push(sm);
        }

        console.log(`✅ Toit height-field: ${validPlanes.length} plans valides, grille ${nx}×${ny}, ${Math.round(positions.length/3)} sommets`);
        return true;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // RENDU TOIT DEPUIS GRILLE Z LiDAR BRUTE (méthode principale)
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Construit le mesh de toit directement depuis la grille Z LiDAR brute.
     * Pixel-perfect : chaque cellule = médiane des points LiDAR → sheds, lanterneaux,
     * fenêtres de toit visibles sans aucune approximation mathématique.
     *
     * Coordonnées : gridData.x0/y0/step et bldgCenter partagent le même repère
     * WGS84-équirectangulaire local produit par /api/lidar/copc-grid.
     * Heights : mnh = max(bh, z_rel - z_baseline_rel + bh)
     *  → z_baseline_rel ≈ niveau avant-toit (percentile 5), donc mnh ≈ bh au ras de la corniche.
     *
     * @param {Object} gridData      - réponse de /api/lidar/copc-grid
     * @param {Object} bldgCenter    - {lat, lon} centre du bâtiment
     * @param {number} bh            - hauteur de mur (m)
     * @param {number} terrainH      - Y terrain Three.js
     * @param {Array}  buildingCoords - [[lon,lat], ...] empreinte BD TOPO
     * @param {string} roofType      - type toit (texture)
     * @param {boolean} isPVBuilding
     * @returns {boolean} true si mesh créé
     */
    _buildRoofFromGrid(gridData, bldgCenter, bh, terrainH, buildingCoords, roofType, isPVBuilding = false) {
        const { grid, x0, y0, nx, ny, step, z_baseline_rel } = gridData;
        if (!grid || nx < 2 || ny < 2) return false;

        const LNG_TO_M    = this.LAT_TO_M * Math.cos(bldgCenter.lat * Math.PI / 180);
        const bldgOffsetX = (bldgCenter.lon - this.centerLon) * LNG_TO_M;
        const bldgOffsetZ = -(bldgCenter.lat - this.centerLat) * this.LAT_TO_M;

        // ── 1. Footprint BD TOPO → espace local (pour jupe) ─────────────────
        let fp = buildingCoords.map(([lon, lat]) => [
            (lon - bldgCenter.lon) * LNG_TO_M,
            (lat - bldgCenter.lat) * this.LAT_TO_M,
        ]);
        if (fp.length > 3) {
            const [x0f, y0f] = fp[0], [xl, yl] = fp[fp.length - 1];
            if ((x0f - xl) ** 2 + (y0f - yl) ** 2 < 0.01) fp.pop();
        }

        // ── 2. Buffers géométrie depuis la grille Z brute ────────────────────
        const positions = [], uvs = [];
        const vertexMap  = new Int32Array(nx * ny).fill(-1);
        let vi = 0;

        // Footprint légèrement dilatée en absolu (+0.15m) pour couvrir les cellules
        // exactement sur le bord du polygone BD TOPO sans créer de "dents"
        // (l'ancienne valeur de 0.8m incluait des cellules trop loin du mur).
        const FP_MARGIN = 0.15; // réduit de 0.8m → 0.15m pour supprimer les dents
        const fpExpanded = this._expandPolygonEdges(fp, FP_MARGIN);

        // ── Null-filling : les cellules dans l'emprise sans donnée LiDAR ──────
        // (zones d'ombre de scan, faible densité sur les bords) sont remplies
        // par interpolation du voisin valide le plus proche (≤ 4 cellules).
        // Cela évite les trous/lacunes sur les arêtes du bâtiment.
        const getZ = (iy, ix) => {
            const v = grid[iy]?.[ix];
            if (v !== null && v !== undefined) return v;
            // Chercher le voisin valide le plus proche dans un rayon de 4 cellules
            let best = null, bestD2 = Infinity;
            for (let dy = -4; dy <= 4; dy++) {
                for (let dx = -4; dx <= 4; dx++) {
                    if (dy === 0 && dx === 0) continue;
                    const jy = iy + dy, jx = ix + dx;
                    if (jy < 0 || jy >= ny || jx < 0 || jx >= nx) continue;
                    const nv = grid[jy][jx];
                    if (nv === null || nv === undefined) continue;
                    const d2 = dx * dx + dy * dy;
                    if (d2 < bestD2) { best = nv; bestD2 = d2; }
                }
            }
            return best;
        };

        const UV_SCALE = 8;

        for (let iy = 0; iy < ny; iy++) {
            for (let ix = 0; ix < nx; ix++) {
                const gx  = x0 + ix * step;
                const gy  = y0 + iy * step;
                if (!this._pointInPoly2D(gx, gy, fpExpanded)) continue;
                const z_rel = getZ(iy, ix);
                if (z_rel === null) continue;
                const mnh = Math.max(bh, z_rel - z_baseline_rel + bh);
                positions.push(bldgOffsetX + gx, terrainH + mnh, bldgOffsetZ - gy);
                uvs.push(gx / UV_SCALE, gy / UV_SCALE);
                vertexMap[iy * nx + ix] = vi++;
            }
        }
        if (positions.length < 9) return false;

        // ── 3. Triangulation ─────────────────────────────────────────────────
        const faceIdx = [];
        for (let iy = 0; iy < ny - 1; iy++) {
            for (let ix = 0; ix < nx - 1; ix++) {
                const v00 = vertexMap[ iy      * nx + ix    ];
                const v10 = vertexMap[ iy      * nx + ix + 1];
                const v01 = vertexMap[(iy + 1) * nx + ix    ];
                const v11 = vertexMap[(iy + 1) * nx + ix + 1];
                if (v00 >= 0 && v10 >= 0 && v01 >= 0) faceIdx.push(v00, v10, v01);
                if (v10 >= 0 && v11 >= 0 && v01 >= 0) faceIdx.push(v10, v11, v01);
            }
        }
        if (faceIdx.length < 3) return false;

        // ── 4. Mesh Three.js ──────────────────────────────────────────────────
        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        geo.setAttribute('uv',       new THREE.Float32BufferAttribute(uvs, 2));
        geo.setIndex(faceIdx);
        geo.computeVertexNormals();

        const mesh = new THREE.Mesh(geo, new THREE.MeshPhongMaterial({
            map:  this._getRoofTexture(roofType),
            side: THREE.DoubleSide, specular: 0x222222, shininess: 5,
            polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1,
        }));
        mesh.castShadow = mesh.receiveShadow = true;
        mesh.userData = { source: 'grid-lidar', isPVRoof: isPVBuilding };
        this.scene.add(mesh);
        this.buildings.push(mesh);

        // ── 5. Jupe (skirt) le long du périmètre du footprint ────────────────
        // Pour chaque sommet du footprint, cherche la cellule de grille la plus proche.
        const getGridMnh = (gx, gy) => {
            const fx  = (gx - x0) / step, fy = (gy - y0) / step;
            const ix0 = Math.round(fx),   iy0 = Math.round(fy);
            let best = null, bestD2 = Infinity;
            for (let dy = -3; dy <= 3; dy++) {
                for (let dx = -3; dx <= 3; dx++) {
                    const jy = iy0 + dy, jx = ix0 + dx;
                    if (jy < 0 || jy >= ny || jx < 0 || jx >= nx) continue;
                    const v = grid[jy][jx];
                    if (v === null) continue;
                    const d2 = dx * dx + dy * dy;
                    if (d2 < bestD2) { best = v; bestD2 = d2; }
                }
            }
            return best !== null ? Math.max(bh, best - z_baseline_rel + bh) : bh;
        };

        const skirtMat = new THREE.MeshPhongMaterial({
            map: this._getRoofTexture(roofType), side: THREE.DoubleSide,
            specular: 0x222222, shininess: 5,
        });
        const skirtPos = [], n_fp = fp.length;
        for (let i = 0; i < n_fp; i++) {
            const [px0, py0] = fp[i], [px1, py1] = fp[(i + 1) % n_fp];
            const h0 = getGridMnh(px0, py0), h1 = getGridMnh(px1, py1);
            const hBot = bh - 0.15;
            skirtPos.push(
                bldgOffsetX + px0, terrainH + hBot,  bldgOffsetZ - py0,
                bldgOffsetX + px1, terrainH + hBot,  bldgOffsetZ - py1,
                bldgOffsetX + px1, terrainH + h1,    bldgOffsetZ - py1,
                bldgOffsetX + px0, terrainH + h0,    bldgOffsetZ - py0,
            );
        }
        if (skirtPos.length >= 12) {
            const skirtGeo = new THREE.BufferGeometry();
            skirtGeo.setAttribute('position', new THREE.Float32BufferAttribute(skirtPos, 3));
            const skirtIdx = [];
            for (let q = 0; q < skirtPos.length / 12; q++) {
                const b = q * 4;
                skirtIdx.push(b, b+1, b+2,  b, b+2, b+3);
            }
            skirtGeo.setIndex(skirtIdx);
            skirtGeo.computeVertexNormals();
            const sm = new THREE.Mesh(skirtGeo, skirtMat);
            sm.castShadow = sm.receiveShadow = true;
            sm.userData = { source: 'grid-lidar-skirt', isPVRoof: isPVBuilding };
            this.scene.add(sm);
            this.buildings.push(sm);
        }

        console.log(`✅ Toit grid LiDAR: ${nx}×${ny} cellules, step=${step}m, ${Math.round(positions.length / 3)} sommets`);
        return true;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // RENDU TOIT DEPUIS PLANS RANSAC BACKEND (fallback polygon_2d)
    // Source : Vosselman & Maas (2010) – adapté WebGL / Three.js
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Construit la géométrie du toit depuis les plans RANSAC détectés côté backend.
     * Chaque plan = un pan de toit réel avec son polygone 2D et son équation MNH.
     *
     * Système de coordonnées :
     *   plane.polygon_2d  : [[x_est_m, y_nord_m], …] relatif au centre bâtiment
     *   plane.mnh_a/b/c   : MNH(x,y) = a*x + b*y + c  → hauteur au-dessus du sol MNT
     *   Three.js           : wx = bldgOffsetX + poly_x
     *                        wz = bldgOffsetZ - poly_y  (axe Z inversé)
     *                        wy = terrainH + MNH(poly_x, poly_y)
     *
     * @param {Array}  planes      - plans depuis building_hd.roof_planes
     * @param {Object} bldgCenter  - {lat, lon} du centre du bâtiment
     * @param {number} bh          - hauteur de mur (m)
     * @param {number} terrainH    - hauteur terrain en Three.js Y
     * @param {string} roofType    - matériau de toit
     * @returns {boolean} true si au moins un pan rendu
     */
    _buildRoofFromPlanes(planes, bldgCenter, bh, terrainH, roofType, isPVBuilding = false) {
        if (!planes || planes.length === 0) return false;

        // Si Solar a déjà injecté ses quads, masquer les meshes RANSAC à la création
        // (évite l'écrasement visuel quand LiDAR HD arrive après la heatmap Solar)
        const _solarActive = !!(this._solarRoofMeshes?.length > 0);
        if (_solarActive) {
            console.log('ℹ️ _buildRoofFromPlanes: Solar actif → nouveaux meshes RANSAC créés masqués');
        }

        const LNG_TO_M = this.LAT_TO_M * Math.cos(bldgCenter.lat * Math.PI / 180);
        const bldgOffsetX =  (bldgCenter.lon - this.centerLon) * LNG_TO_M;
        const bldgOffsetZ = -(bldgCenter.lat - this.centerLat) * this.LAT_TO_M;

        const roofMat = new THREE.MeshPhongMaterial({
            map: this._getRoofTexture(roofType),
            side: THREE.DoubleSide, specular: 0x222222, shininess: 5,
            polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1,
        });
        let nBuilt = 0;

        // ── Pans inclinés ──────────────────────────────────────────────
        for (const plane of planes) {
            const poly = plane.polygon_2d;
            if (!poly || poly.length < 3) continue;

            // ── Filtre acrotère / parapet ──────────────────────────────────────
            // L'acrotère (relevé de étanchéité / parapet) est capté par le RANSAC
            // comme plan quasi-horizontal sous forme d'une BANDELETTE FINE le long
            // du périmètre du toit (largeur réelle ≈ 0.2–0.5 m).
            // Ce polygon_2d "en cadre" ou "en L" crée des concavités résistantes à
            // l'expansion Minkowski et génère l'artefact visuel "axe décalé".
            // Critère de détection : largeur minimale effective = area / max_bbox_dim.
            //   Acrotère réel  : ~0.3 m  → filtrée (<1.5 m)
            //   Vrai pan de toit: ≥ 2.0 m → conservé
            {
                let _sa = 0;
                for (let _i = 0, _j = poly.length - 1; _i < poly.length; _j = _i++)
                    _sa += poly[_j][0] * poly[_i][1] - poly[_i][0] * poly[_j][1];
                const _area = Math.abs(_sa) / 2;
                const _pxs = poly.map(p => p[0]), _pys = poly.map(p => p[1]);
                const _bbW  = Math.max(..._pxs) - Math.min(..._pxs);
                const _bbH  = Math.max(..._pys) - Math.min(..._pys);
                const _minW = _area / Math.max(_bbW, _bbH, 0.1);
                if (_minW < 1.5 || _area < 4) {
                    console.log(`⏭️ Plan RANSAC ignoré (acrotère probable): id=${plane.plane_id}, minW=${_minW.toFixed(2)}m, area=${_area.toFixed(1)}m²`);
                    continue;
                }
            }

            const { mnh_a, mnh_b, mnh_c } = plane;

            // ── Expansion de bord robuste (Minkowski, offset =+0.25m) ─────────────
            // Repousse chaque sommet le long de la bissectrice des normales sortantes.
            //
            // Corrections vs ancienne version :
            // 1. Dédupliquer les sommets quasi-identiques (arêtes dégénérées → NaN/normal explosé)
            // 2. Sens sortant determiné par l'aire signée (winding order), PAS depuis le centroïde.
            //    Le test centroïde est faux pour les polygones non-convexes/concaves (grands bâtiments):
            //    certains sommets rentrants sont côté intérieur du centroïde → normale inversée → spirale.
            // 3. Plafonner le scaling pour éviter l'explosion aux angles quasi-plats (sommet aligné
            //    sur ses voisins → bsLen→0 → scale→∞ → vertex projeté à des mètres → spirale).

            // 1. Dédupliquer
            const rawPoly = poly.filter(([px, py], i) => {
                if (i === 0) return true;
                const [px0, py0] = poly[i - 1];
                return (px - px0) * (px - px0) + (py - py0) * (py - py0) > 1e-4;
            });
            if (rawPoly.length < 3) continue;

            // Filtre bâtiment adjacent : si le centroïde du plan est hors de l'empreinte BD TOPO
            // (+ marge 1.5m), ce plan appartient probablement à un toit voisin capté par LiDAR.
            if (this._pvBuildingBboxMetric) {
                const _cxP = rawPoly.reduce((s, p) => s + p[0], 0) / rawPoly.length;
                const _cyP = rawPoly.reduce((s, p) => s + p[1], 0) / rawPoly.length;
                const _bb = this._pvBuildingBboxMetric;
                if (_cxP < _bb.xMin || _cxP > _bb.xMax || _cyP < _bb.yMin || _cyP > _bb.yMax) {
                    console.log(`⏭️ Plan RANSAC ignoré (toit adjacent): centroïde (${_cxP.toFixed(1)},${_cyP.toFixed(1)}) hors empreinte BD TOPO`);
                    continue;
                }
            }

            // 2. Aire signée (shoelace) → facteur de winding : CCW=+1, CW=-1
            let _sa2 = 0;
            for (let _si = 0, _sj = rawPoly.length - 1; _si < rawPoly.length; _sj = _si++)
                _sa2 += rawPoly[_sj][0] * rawPoly[_si][1] - rawPoly[_si][0] * rawPoly[_sj][1];
            const _w = _sa2 >= 0 ? 1 : -1; // CCW → right-hand = sortant ; CW → left-hand = sortant

            // 3. Expansion
            const EXP = 0.25;
            const n_poly = rawPoly.length;
            const expandedPoly = rawPoly.map(([px, py], i) => {
                const [ax, ay] = rawPoly[(i - 1 + n_poly) % n_poly];
                const [bx, by] = rawPoly[(i + 1) % n_poly];
                const e1x = px - ax, e1y = py - ay;
                const l1 = Math.sqrt(e1x * e1x + e1y * e1y);
                const e2x = bx - px, e2y = by - py;
                const l2 = Math.sqrt(e2x * e2x + e2y * e2y);
                if (l1 < 1e-6 || l2 < 1e-6) return [px, py]; // arête dégénérée → pas d'offset
                // Normales sortantes basées sur le winding (indépendant du centroïde)
                const n1x =  _w * e1y / l1, n1y = -_w * e1x / l1;
                const n2x =  _w * e2y / l2, n2y = -_w * e2x / l2;
                // Bissectrice
                const bsx = n1x + n2x, bsy = n1y + n2y;
                const bsLen = Math.sqrt(bsx * bsx + bsy * bsy);
                if (bsLen < 1e-6) return [px, py]; // normes anti-parallèles → angle nul, pas d'offset
                // Plafonnement agressif : sinH ∈ [0.35, 1] → scale ≤ 0.71m (vs 2.5m avant)
                const sinH = Math.min(1, Math.max(0.35, bsLen / 2));
                const scale = Math.min(EXP / sinH, EXP * 2.5);
                return [px + (bsx / bsLen) * scale, py + (bsy / bsLen) * scale];
            });

            const positions = [];
            const uvs = [];

            for (const [px, py] of expandedPoly) {
                const wx = bldgOffsetX + px;
                const wz = bldgOffsetZ - py;
                // mnh = MNH en m au-dessus du terrain (même référentiel MNH-grid et COPC corrigé)
                // wy = terrainH + MNH — formule universelle des deux chemins
                // On s'assure que l'égout du toit rejoint le haut des murs (≤0.3m d'écart)
                const mnh = mnh_a * px + mnh_b * py + mnh_c;
                const wy = terrainH + Math.max(bh - 0.3, mnh);
                positions.push(wx, wy, wz);
                uvs.push(px / 4.0, py / 4.0);
            }

            if (positions.length < 9) continue;   // < 3 sommets

            // Triangulation earcut (ShapeUtils) — robuste pour tout polygone
            // Le fan-triangulation ne fonctionne que pour les polygones convexes
            // parfaitement ordonnés ; earcut gère toute forme correctement.
            let flatIndices;
            try {
                const shapeVerts2D = expandedPoly.map(([ex, ey]) => new THREE.Vector2(ex, ey));
                const tris = THREE.ShapeUtils.triangulateShape(shapeVerts2D, []);
                // tris = [[a,b,c], ...]
                flatIndices = tris.reduce((acc, t) => { acc.push(...t); return acc; }, []);
            } catch (_) {
                // Fallback éventail
                flatIndices = [];
                for (let i = 1; i < expandedPoly.length - 1; i++) flatIndices.push(0, i, i + 1);
            }
            if (flatIndices.length < 3) continue;
            const indices = flatIndices;

            const geo = new THREE.BufferGeometry();
            geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
            geo.setAttribute('uv',       new THREE.Float32BufferAttribute(uvs, 2));
            geo.setIndex(flatIndices);
            geo.computeVertexNormals();

            const mat = roofMat.clone();
            const mesh = new THREE.Mesh(geo, mat);
            mesh.castShadow    = true;
            mesh.receiveShadow = true;
            mesh.visible = !_solarActive;
            mesh.userData = {
                planId:    plane.plane_id,
                slopeDeg:  plane.slope_deg,
                azimuthDeg: plane.azimuth_deg,
                source:    'ransac',
                isPVRoof:  isPVBuilding,
            };
            this.scene.add(mesh);
            this.buildings.push(mesh);
            nBuilt++;

            // ── Jupe (skirt) sous l'égout — comble le joint entre toit et murs ──
            // Chaque arête du polygone dilaté reçoit un quad vertical descendant jusqu'à
            // bh−1m sous le terrain pour couvrir tout interstice avec le haut des murs.
            // Pour les toits plats (slope_deg < 3°) : la jupe est inutile (le Cap de
            // l'ExtrudeGeometry est coplanaire avec le toit) et peut créer des murs
            // parasites si le polygone RANSAC dépasse légèrement la BD TOPO.
            const _isFlat = (plane.slope_deg ?? 0) < 3;
            if (!_isFlat) {
                const skirtVerts = [];
                const skirtBottom = terrainH - 0.5;
                for (let si = 0; si < expandedPoly.length; si++) {
                    const [px1, py1] = expandedPoly[si];
                    const [px2, py2] = expandedPoly[(si + 1) % expandedPoly.length];
                    const wx1 = bldgOffsetX + px1, wz1 = bldgOffsetZ - py1;
                    const wx2 = bldgOffsetX + px2, wz2 = bldgOffsetZ - py2;
                    const mnh1 = mnh_a * px1 + mnh_b * py1 + mnh_c;
                    const mnh2 = mnh_a * px2 + mnh_b * py2 + mnh_c;
                    const wy1 = terrainH + Math.max(bh - 0.3, mnh1);
                    const wy2 = terrainH + Math.max(bh - 0.3, mnh2);
                    skirtVerts.push(
                        wx1, skirtBottom, wz1,  wx2, wy2, wz2,        wx2, skirtBottom, wz2,
                        wx1, skirtBottom, wz1,  wx1, wy1, wz1,         wx2, wy2, wz2
                    );
                }
                if (skirtVerts.length > 0) {
                    const sGeo = new THREE.BufferGeometry();
                    sGeo.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(skirtVerts), 3));
                    sGeo.computeVertexNormals();
                    const sMesh = new THREE.Mesh(sGeo, roofMat.clone());
                    sMesh.castShadow = false;
                    sMesh.visible    = !_solarActive;
                    sMesh.userData   = { source: 'ransac' };
                    this.scene.add(sMesh);
                    this.buildings.push(sMesh);
                }
            } // end !_isFlat (skirt)
        }

        if (nBuilt > 0) {
            console.log(`✅ _buildRoofFromPlanes: ${nBuilt} pan(s) depuis ${planes.length} plan(s) RANSAC`);
        }
        return nBuilt > 0;
    }

    /**
     * [DÉPRÉCIÉ] L'application utilise désormais exclusivement BD TOPO + LiDAR.
     * Cette méthode est conservée pour compatibilité avec le code du template
     * mais n'a plus d'effet — le toit est déjà construit par _createBuilding3D.
     */
    applySolarRoofFromInsights(segments, bldgCenter, dsmStats, buildingDims) {
        // Stocker le nombre de pans Solar (utile pour enrichir le label RANSAC quand RANSAC < Solar)
        this._solarPanCount = segments?.filter(s => (s.pitch_deg ?? 0) > 2).length ?? 0;
        console.info(`ℹ️ applySolarRoofFromInsights: toit RANSAC conservé — ${this._solarPanCount} pans Solar mémorisés`);
    }

    /**
     * [INTERNE, DÉPRÉCIÉ] Ancienne mise à jour depuis segments Google Solar.
     */
    _updateRoofPanelsInfoFromSolar(segments, dsmStats) {
        if (!segments?.length) return;

        const getOrientLabel = (deg) => {
            const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'];
            return dirs[Math.round(((deg % 360 + 360) % 360) / 45) % 8];
        };

        // Filtrer et trier les segments par surface décroissante
        const validSegs = segments.filter(s => s.area_m2 > 0);
        validSegs.sort((a, b) => (b.area_m2 || 0) - (a.area_m2 || 0));

        const hasSlopes = validSegs.some(s => (s.pitch_deg ?? 0) > 2);
        const nSloped = validSegs.filter(s => (s.pitch_deg ?? 0) > 2).length;

        let typeLabel;
        if (!hasSlopes) {
            typeLabel = 'Toit plat';
        } else if (nSloped === 1) {
            typeLabel = 'Mono-pente (Solar API)';
        } else if (nSloped === 2) {
            typeLabel = 'Bi-pan (Solar API)';
        } else {
            typeLabel = `${validSegs.length} pans (Solar API)`;
        }

        const panels = validSegs.map((seg, idx) => {
            const azDeg = seg.azimuth_deg ?? 0;
            const pitDeg = seg.pitch_deg ?? 0;
            const area = seg.area_m2 ?? 0;
            // Estimer longueur/largeur depuis bbox si disponible
            let longueur = seg.seg_l_m ?? '—';
            let largeur = seg.seg_w_m ?? '—';
            if (longueur !== '—') longueur = Math.round(longueur * 10) / 10;
            if (largeur !== '—') largeur = Math.round(largeur * 10) / 10;

            return {
                name: `Pan Solar ${idx + 1}`,
                longueur: longueur,
                largeur: largeur,
                surface: Math.round(area * 10) / 10,
                pente_deg: Math.round(pitDeg * 10) / 10,
                orientation_deg: Math.round(azDeg),
                orientation_label: getOrientLabel(azDeg),
                sunshineAnnual: seg.irr_med_kwh ?? undefined,
                // Données brutes pour le matching zone → segment
                _seg_sw: seg.seg_sw,
                _seg_ne: seg.seg_ne,
                _height_m: seg.height_m,
                _seg_idx: seg.orig_idx ?? (seg.id - 1),
            };
        });

        // Préserver les infos OBB existantes si disponibles
        const existingOBB = this.roofPanelsInfo?.buildingOBB;
        const existingCenter = this.roofPanelsInfo?.buildingCenterGeo;

        this.roofPanelsInfo = {
            type: hasSlopes ? 'solar_multi' : 'flat',
            typeLabel: typeLabel,
            hauteurMurs: this._mainBldgBh ?? (dsmStats?.height_egout_m ?? 5),
            hauterFaitageRelatif: (dsmStats?.height_faitage_m ?? 0) - (dsmStats?.height_egout_m ?? 0),
            couverture: this._mainBldgRoofType ?? 'tile',
            nRidges: 1,
            panels: panels,
            surfaceTotale: Math.round(panels.reduce((s, p) => s + (p.surface || 0), 0) * 10) / 10,
            _source: 'google_solar',
            buildingOBB: existingOBB,
            buildingCenterGeo: existingCenter,
            buildingTerrainH: this._mainBldgTerrainH,
            buildingWallH: this._mainBldgBh,
            buildingLocalCoords: this.roofPanelsInfo?.buildingLocalCoords,
        };

        console.log(`📐 roofPanelsInfo mis à jour (Solar): ${panels.length} pans, type="${typeLabel}"`);
    }

    /**
     * Place les panneaux solaires individuels Google Solar en 3D.
     * Référence: BuildingInsightsSection.svelte (js-solar-potential officiel Google).
     *
     * • Chaque panneau = GPS center + orientation (PORTRAIT/LANDSCAPE) + segmentIndex.
     * • On calcule la hauteur 3D exacte depuis l'équation plane du segment.
     * • Couleur dégradée bleu→rouge selon irradiance.
     *
     * @param {Array}  solarPanels   – tableau {lat, lon, orientation, seg_idx, irr_kwh}
     * @param {Array}  roofSegments  – _fluxRoofSegments (pitch_deg, azimuth_deg, height_m…)
     * @param {Object} bldgCenter    – {lat, lon} (this._solarBldgCenter si absent)
     */
    applyBuildingInsightsPanels3D(solarPanels, roofSegments, bldgCenter) {
        // Quand LiDAR/RANSAC est disponible : les modules sont positionnés depuis les plans RANSAC
        // → les panneaux Google Solar individuels seraient un doublon flottant (mauvaise altitude).
        if (this.lidarData?.building_hd?.roof_planes?.length > 0) {
            console.info('ℹ️ applyBuildingInsightsPanels3D: ignoré — données RANSAC disponibles (évite le masque Solar parasite)');
            return;
        }
        // Nettoyage
        if (this._solarPanelMeshes) {
            this._solarPanelMeshes.forEach(m => {
                this.scene.remove(m);
                m.geometry?.dispose();
                if (Array.isArray(m.material)) m.material.forEach(mt => mt.dispose());
                else m.material?.dispose();
            });
        }
        this._solarPanelMeshes = [];

        const center = bldgCenter ?? this._solarBldgCenter;
        const segs   = roofSegments ?? this._solarSegments ?? [];
        if (!solarPanels?.length || !center) return;

        const terrainH = this._mainBldgTerrainH ?? 0;
        const wallH    = this._mainBldgBh ?? 5;
        
        // Récupérer l'offset calculé lors de la création du toit
        const offsetX = this._solarOffset?.x ?? 0;
        const offsetZ = this._solarOffset?.z ?? 0;

        // GPS → Three.js local — ORIGINE = scène Three.js (this.centerLon/Lat)
        const toX = lon => (lon - this.centerLon) * this.LNG_TO_M;
        const toZ = lat => -(lat - this.centerLat) * this.LAT_TO_M;

        // ── Index segments : seg_idx → hauteur-au-point ──────────────────────────
        const segMap = new Map();
        for (const seg of segs) {
            const idx    = seg.orig_idx ?? (seg.id - 1);
            if (!seg.seg_sw || !seg.seg_ne) continue;
            const cLat   = (seg.seg_sw.lat + seg.seg_ne.lat) / 2;
            const cLon   = (seg.seg_sw.lon + seg.seg_ne.lon) / 2;
            const azRad  = (seg.azimuth_deg ?? 180) * Math.PI / 180;
            const pitRad = (seg.pitch_deg   ?? 0)   * Math.PI / 180;
            
            let baseH = 0;
            if (seg.height_m != null) {
                baseH = terrainH + seg.height_m; // Relatif au terrain
            } else {
                baseH = terrainH + wallH + 0.5; // fallback relatif
            }
            
            const cx     = toX(cLon), cz = toZ(cLat);
            segMap.set(idx, {
                azRad, pitRad,
                tanPit: Math.tan(pitRad),
                baseH, cx, cz,
            });
        }

        // ── Plage d'énergie pour la colormap ────────────────────────────────────
        const energies = solarPanels.map(p => p.irr_kwh || 0).filter(e => e > 0);
        const minE = energies.length ? Math.min(...energies) : 0;
        const maxE = energies.length ? Math.max(...energies) : 1;

        // Dimensions des panneaux API Google Solar
        const pW = (typeof window !== 'undefined' ? window._fluxApiPanelW : null) ?? 1.045;
        const pH = (typeof window !== 'undefined' ? window._fluxApiPanelH : null) ?? 1.879;

        for (const p of solarPanels) {
            const info = segMap.get(p.seg_idx);
            const origX = toX(p.lon);
            const origZ = toZ(p.lat);

            // Hauteur 3D : calculée sur la position d'origine
            let py = terrainH + wallH + 0.1; // fallback si segment inconnu
            if (info) {
                const proj = (origX - info.cx) * Math.sin(info.azRad) - (origZ - info.cz) * Math.cos(info.azRad);
                py = info.baseH - proj * info.tanPit + 0.06;
            }

            // ── Couleur dégradée bleu (faible irr) → rouge (forte irr) ────────
            const t  = maxE > minE ? Math.max(0, Math.min(1, (p.irr_kwh - minE) / (maxE - minE))) : 0.5;
            const r  = t * 0.9;
            const g  = 0.1 + t * 0.1;
            const b  = 0.9 - t * 0.8;
            const mat = new THREE.MeshPhongMaterial({
                color: new THREE.Color(r, g, b),
                specular: 0x4488ff, shininess: 80,
                transparent: true, opacity: 0.90,
                polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -3,
            });

            // ── Géométrie : PlaneGeometry aux dimensions de l'API ─────────────
            const geo  = new THREE.PlaneGeometry(pW, pH);
            const mesh = new THREE.Mesh(geo, mat);

            // Rotation Three.js (order YXZ) :
            //   PlaneGeometry est VERTICAL par défaut (plan XY).
            //   On le couche à plat (-π/2) puis on l'incline par le pitch.
            //   orientOff = π/2 si PORTRAIT (long côté horizontal)
            const orientOffset = (p.orientation === 'PORTRAIT') ? Math.PI / 2 : 0;
            mesh.rotation.order = 'YXZ';
            mesh.rotation.y = -(info?.azRad ?? 0) + orientOffset + Math.PI;
            mesh.rotation.x = (info?.pitRad ?? 0) - Math.PI / 2;
            
            // Appliquer l'offset pour l'affichage
            mesh.position.set(origX + offsetX, py, origZ + offsetZ);

            mesh.castShadow = true;
            this.scene.add(mesh);
            this._solarPanelMeshes.push(mesh);
        }

        console.log(`⚡ ${this._solarPanelMeshes.length} panneaux Google Solar placés en 3D (réf. js-solar-potential)`);
    }

    /**
     * Calcule les infos de pans de toiture (roofPanelsInfo) depuis les plans RANSAC.
     * Remplace _computeRoofPanelsInfo quand les plans backend sont disponibles.
     *
     * @param {Array}  planes     - building_hd.roof_planes
     * @param {Object} obb        - Oriented Bounding Box du bâtiment
     * @param {number} terrainH   - hauteur terrain Three.js Y
     * @param {number} bh         - hauteur de mur (m)
     * @param {Object} bldgCenter - {lat, lon}
     * @returns {Object} roofPanelsInfo compatible avec matchZonesToRoofPanels()
     */
    _computeRoofPanelsInfoFromPlanes(planes, obb, terrainH, bh, bldgCenter, roofType = 'tuile') {
        if (!planes || planes.length === 0) return null;

        const inclined = planes.filter(p => p.slope_deg >= 1.0);

        const panelList = inclined.map((plane, idx) => {
            // Surface en projection horizontale (shoelace)
            const poly = plane.polygon_2d || [];
            let area2d = 0;
            for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
                area2d += (poly[j][0] + poly[i][0]) * (poly[j][1] - poly[i][1]);
            }
            area2d = Math.abs(area2d) / 2;
            // Surface réelle du pan incliné
            const cosSlope  = Math.cos(plane.slope_deg * Math.PI / 180);
            const realArea  = cosSlope > 0.01 ? area2d / cosSlope : area2d;

            // Dimensions approximatives (bbox du polygone)
            const xs = poly.map(p => p[0]);
            const ys = poly.map(p => p[1]);
            const w  = (Math.max(...xs) - Math.min(...xs)) || obb.longDim;
            const l  = (Math.max(...ys) - Math.min(...ys)) || obb.shortDim;

            return {
                name:              `Pan Solar ${idx + 1}`,
                pente_deg:         plane.slope_deg,
                orientation_deg:   plane.azimuth_deg,
                orientation_label: this._getOrientationLabel ? this._getOrientationLabel(plane.azimuth_deg) : '',
                surface:           Math.round(realArea * 10) / 10,
                longueur:          Math.round(w * 10) / 10,
                largeur:           Math.round(l * 10) / 10,
                source:            'ransac',
                eave_mnh:          plane.eave_mnh,
                mnh_a:             plane.mnh_a,
                mnh_b:             plane.mnh_b,
                mnh_c:             plane.mnh_c,
                polygon_2d:        plane.polygon_2d,
                centroid:          plane.centroid,
                confidence:        plane.confidence,
                sunshineAnnual:    plane.sunshine_annual_kwh_m2 !== undefined ? plane.sunshine_annual_kwh_m2 : undefined,
            };
        });

        const nInc = inclined.length;
        // Si Google Solar a détecté plus de plans que le RANSAC (ex: 4 pans détectés par Solar
        // quand LiDAR ne donne que 2), la géométrie est enrichie (_addHipCroupeEnds) → type = 'hip'.
        const _solarPanCount = this._solarPanCount ?? 0;
        const _effectiveInc  = (_solarPanCount > nInc) ? _solarPanCount : nInc;
        const roofTypeName = (_solarPanCount >= 4 && nInc < 4)
            ? 'hip'  // type géométrique réel enrichi par Solar
            : (nInc >= 4 ? 'hip' : nInc >= 2 ? 'gable' : nInc === 1 ? 'shed' : 'flat');
        const typeLabels = { 'gable': 'Bi-pan (2 versants)', 'hip': '4 pans (croupe)', 'shed': 'Mono-pente', 'flat': 'Toit plat' };
        // Label enrichi quand Solar détecte davantage de pans que le LiDAR RANSAC
        let typeLabel = typeLabels[roofTypeName] || 'Toiture RANSAC';
        if (_solarPanCount >= 4 && nInc < 4) {
            typeLabel = `4 pans (croupe) — ${nInc} pans LiDAR`;
        } else if (_solarPanCount > nInc && nInc > 0) {
            typeLabel = `${typeLabels[roofTypeName]} — ${_solarPanCount} pans Solar`;
        }

        return {
            type:               roofTypeName,
            typeLabel:          typeLabel,
            couverture:         roofType,
            surfaceTotale:      Math.round(panelList.reduce((s, p) => s + (p.surface || 0), 0) * 10) / 10,
            panels:             panelList,
            source:             'ransac',
            buildingOBB: {
                cx:       obb.cx,  cz:      obb.cz,
                angle:    obb.angle,
                longDim:  obb.longDim, shortDim: obb.shortDim,
            },
            buildingTerrainH:    terrainH,
            buildingWallH:       bh,
            buildingLocalCoords: [],   // rempli par l'appelant
            buildingCenterGeo:   { lat: bldgCenter.lat, lng: bldgCenter.lon },
        };
    }

    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Toit bi-pan (gable) depuis le polygone réel, avec fallback OBB fiable.
     */
    _createGableRoof(localCoords, obb, bh, terrainH, ridgeExtra, roofType, wallType) {
        this._createOBBGableRoof(obb, terrainH + bh, ridgeExtra, roofType);
    }

    /**
     * Toit 4 pans (hip/croupe) depuis le polygone réel, avec fallback OBB.
     */
    _createHipRoof(localCoords, obb, bh, terrainH, ridgeExtra, roofType, wallType) {
        this._createOBBHipRoof(obb, terrainH + bh, ridgeExtra, roofType);
    }

    /**
     * Toit mono-pente (shed) depuis le polygone réel, avec fallback OBB.
     */
    _createShedRoof(localCoords, obb, bh, terrainH, ridgeExtra, roofType, wallType, ridgeOffset) {
        this._createOBBShedRoof(obb, terrainH + bh, ridgeExtra, (ridgeOffset < 0 ? -1 : 1), roofType);
    }

    /** Helpers OBB fiables (géométrie directe depuis l’OBB, sans triangulation) */
    _obbCorners(obb) {
        const cA = Math.cos(obb.angle), sA = Math.sin(obb.angle);
        const hL = obb.longDim / 2, hS = obb.shortDim / 2;
        // along = (cA, sA), across = (sA, -cA)  in XZ
        return {
            cA, sA, hL, hS,
            // along+, across+
            flx: obb.cx + cA*hL + sA*hS, flz: obb.cz + sA*hL - cA*hS,
            // along+, across-
            frx: obb.cx + cA*hL - sA*hS, frz: obb.cz + sA*hL + cA*hS,
            // along-, across+
            blx: obb.cx - cA*hL + sA*hS, blz: obb.cz - sA*hL - cA*hS,
            // along-, across-
            brx: obb.cx - cA*hL - sA*hS, brz: obb.cz - sA*hL + cA*hS,
            // ridge ends (along=±hL, across=0)
            r1x: obb.cx + cA*hL, r1z: obb.cz + sA*hL,
            r2x: obb.cx - cA*hL, r2z: obb.cz - sA*hL,
        };
    }
    _addTriMesh(verts, roofType, isPVBuilding = false) {
        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.Float32BufferAttribute(verts, 3));
        geo.computeVertexNormals();
        const mat = new THREE.MeshPhongMaterial({
            map: this._getRoofTexture(roofType),
            side: THREE.DoubleSide, specular: 0x222222, shininess: 5,
            polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1,
        });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.castShadow = true;
        mesh.userData.isRoofMesh = true;
        if (isPVBuilding) mesh.userData.isPVRoof = true;
        this.scene.add(mesh);
        this.buildings.push(mesh);
    }

    /**
     * Reconstruit la géométrie 3D du toit depuis les données Google Solar.
     * Remplace uniquement les mesh de toit OBB, conserve les murs.
     * @param {Object} dominantSeg  - Segment Google Solar dominant (surface la plus grande)
     * @param {Object} secondarySeg - Segment secondaire (null pour mono-pente)
     * @param {string} roofType     - 'gable' | 'shed' | 'hip' | 'flat'
     */
    rebuildRoofFromGoogleSolar(dominantSeg, secondarySeg, roofType) {
        // Supprimer uniquement les mesh de toit OBB (pas les murs ni RANSAC)
        const toRemove = this.buildings.filter(b => b.userData && b.userData.isRoofMesh);
        toRemove.forEach(b => {
            this.scene.remove(b);
            if (b.geometry) b.geometry.dispose();
            if (b.material) {
                if (Array.isArray(b.material)) b.material.forEach(m => m.dispose());
                else b.material.dispose();
            }
        });
        this.buildings = this.buildings.filter(b => !(b.userData && b.userData.isRoofMesh));

        const obb      = this.roofPanelsInfo?.buildingOBB;
        const terrainH = this.roofPanelsInfo?.buildingTerrainH ?? 0;
        const wallH    = this.roofPanelsInfo?.buildingWallH    ?? 6;
        if (!obb) {
            console.warn('rebuildRoofFromGoogleSolar: OBB manquant, impossible de reconstruire la géométrie');
            return;
        }

        const roofBaseY  = terrainH + wallH;
        const pitchRad   = (dominantSeg.pitchDegrees || 20) * Math.PI / 180;
        const ridgeExtra = Math.tan(pitchRad) * obb.shortDim / 2;

        // Déterminer quel côté est en haut pour toit mono-pente via azimut Google Solar
        // La direction "along+" dans l'OBB est angle depuis X (Est)
        // L'azimut Google Solar est depuis le Nord, sens horaire
        let highSide = 1; // défaut: côté across+
        if (roofType === 'shed' && dominantSeg.azimuthDegrees !== undefined) {
            // across+ direction en boussole = OBB angle + 90° en local → bearing
            // OBB angle en radians depuis X (Est) → bearing depuis N = 90° - OBB_deg
            const obbBearingDeg = (90 - obb.angle * 180 / Math.PI + 360) % 360;
            const acrossPlusBearing = (obbBearingDeg + 90) % 360;  // perpendiculaire = pente montante
            const deltaAz = ((dominantSeg.azimuthDegrees - acrossPlusBearing) + 360) % 360;
            // Si azimut est à moins de 90° du across+ → across+ est côté bas (downslope)
            highSide = (deltaAz < 90 || deltaAz > 270) ? -1 : 1;
        }

        const coverType = this.roofPanelsInfo?.couverture || 'tuile';
        if (roofType === 'gable') {
            this._createOBBGableRoof(obb, roofBaseY, ridgeExtra, coverType);
        } else if (roofType === 'shed') {
            this._createOBBShedRoof(obb, roofBaseY, ridgeExtra, highSide, coverType);
        } else if (roofType === 'hip') {
            this._createOBBHipRoof(obb, roofBaseY, ridgeExtra, coverType);
        }
        // flat: pas de géométrie de toit supplémentaire
        console.log(`✅ Toit reconstruit depuis Google Solar: type=${roofType}, pente=${dominantSeg.pitchDegrees}°, ridgeExtra=${ridgeExtra.toFixed(2)}m`);
    }
    _createOBBGableRoof(obb, roofBaseY, ridgeExtra, roofType) {
        const c = this._obbCorners(obb);
        const ry = roofBaseY + ridgeExtra;
        // Pan across+ : r1→fl→bl→r2  | Pan across- : r1→r2→br→fr
        const verts = [
            // pan +
            c.r1x,ry,c.r1z,  c.flx,roofBaseY,c.flz,  c.blx,roofBaseY,c.blz,
            c.r1x,ry,c.r1z,  c.blx,roofBaseY,c.blz,  c.r2x,ry,c.r2z,
            // pan -
            c.r1x,ry,c.r1z,  c.r2x,ry,c.r2z,  c.brx,roofBaseY,c.brz,
            c.r1x,ry,c.r1z,  c.brx,roofBaseY,c.brz,  c.frx,roofBaseY,c.frz,
        ];
        this._addTriMesh(new Float32Array(verts), roofType);
    }
    /**
     * Ajoute uniquement les 2 faces triangulaires de bout ("croupe") d'un toit 4 pans.
     * Utilisé quand le RANSAC LiDAR n'a détecté que 2 plans (faces principales) mais que
     * Google Solar confirme un toit à 4 pans.
     */
    _addHipCroupeEnds(obb, roofBaseY, ridgeExtra, roofType, isPVBuilding = false) {
        const c   = this._obbCorners(obb);
        const ry  = roofBaseY + ridgeExtra;
        const rhl = obb.longDim * 0.45 / 2;
        const r1x = obb.cx + c.cA * rhl, r1z = obb.cz + c.sA * rhl;
        const r2x = obb.cx - c.cA * rhl, r2z = obb.cz - c.sA * rhl;
        const verts = new Float32Array([
            // Face triangulaire "along+" (pignon avant)
            r1x, ry, r1z,  c.frx, roofBaseY, c.frz,  c.flx, roofBaseY, c.flz,
            // Face triangulaire "along-" (pignon arrière)
            r2x, ry, r2z,  c.blx, roofBaseY, c.blz,  c.brx, roofBaseY, c.brz,
        ]);
        this._addTriMesh(verts, roofType, isPVBuilding);
    }

    _createOBBHipRoof(obb, roofBaseY, ridgeExtra, roofType) {
        const c = this._obbCorners(obb);
        const ry = roofBaseY + ridgeExtra;
        const rhl = obb.longDim * 0.45 / 2;
        // ridge points retraités
        const r1x = obb.cx + c.cA*rhl, r1z = obb.cz + c.sA*rhl;
        const r2x = obb.cx - c.cA*rhl, r2z = obb.cz - c.sA*rhl;
        const verts = [
            // pan along+
            r1x,ry,r1z,  c.frx,roofBaseY,c.frz,  c.flx,roofBaseY,c.flz,
            // pan along-
            r2x,ry,r2z,  c.blx,roofBaseY,c.blz,  c.brx,roofBaseY,c.brz,
            // pan across+
            r1x,ry,r1z,  c.flx,roofBaseY,c.flz,  c.blx,roofBaseY,c.blz,
            r1x,ry,r1z,  c.blx,roofBaseY,c.blz,  r2x,ry,r2z,
            // pan across-
            r1x,ry,r1z,  r2x,ry,r2z,  c.brx,roofBaseY,c.brz,
            r1x,ry,r1z,  c.brx,roofBaseY,c.brz,  c.frx,roofBaseY,c.frz,
        ];
        this._addTriMesh(new Float32Array(verts), roofType);
    }
    _createOBBShedRoof(obb, roofBaseY, ridgeExtra, highSide, roofType) {
        const c = this._obbCorners(obb);
        // highSide>0 → across+ est haut
        const [hx1,hz1,hx2,hz2] = highSide > 0
            ? [c.flx,c.flz,c.blx,c.blz]
            : [c.frx,c.frz,c.brx,c.brz];
        const [lx1,lz1,lx2,lz2] = highSide > 0
            ? [c.frx,c.frz,c.brx,c.brz]
            : [c.flx,c.flz,c.blx,c.blz];
        const hy = roofBaseY + ridgeExtra;
        const verts = [
            hx1,hy,hz1,  hx2,hy,hz2,  lx2,roofBaseY,lz2,
            hx1,hy,hz1,  lx2,roofBaseY,lz2,  lx1,roofBaseY,lz1,
        ];
        this._addTriMesh(new Float32Array(verts), roofType);
    }
    
    /**
     * Toit multi-gable (plusieurs faîtages parallèles) depuis le polygone réel.
     * Crée un profil en zigzag /\/\/\ avec N faîtages.
     */
    _createMultiGableRoof(localCoords, obb, bh, terrainH, ridgeExtra, roofType, wallType, nRidges, roofAnalysis) {
        const roofBaseY = terrainH + bh;
        const halfShort = obb.shortDim / 2;
        
        // Construire une lookup table depuis le profil LiDAR réel si disponible
        const profile = roofAnalysis && roofAnalysis.profile;
        let profileLookup = null;
        if (profile && profile.length >= 5) {
            const smoothH = profile.map((p, i) => {
                if (i === 0 || i === profile.length - 1) return p.h;
                return (profile[i-1].h + 2 * p.h + profile[i+1].h) / 4;
            });
            const hMin = Math.min(...smoothH);
            profileLookup = profile.map((p, i) => ({ pos: p.pos, h: smoothH[i] - hMin }));
        }
        
        const heightFunc = (across, along) => {
            const normalized = Math.min(Math.max((across / Math.max(halfShort, 0.5) + 1) / 2, 0), 1);
            
            if (profileLookup) {
                let i = 0;
                while (i < profileLookup.length - 1 && profileLookup[i + 1].pos < normalized) i++;
                if (i >= profileLookup.length - 1) return profileLookup[profileLookup.length - 1].h;
                const t = (normalized - profileLookup[i].pos) / Math.max(profileLookup[i + 1].pos - profileLookup[i].pos, 0.001);
                return profileLookup[i].h * (1 - t) + profileLookup[i + 1].h * t;
            }
            
            // Fallback : division uniforme
            const sectionWidth = 1 / nRidges;
            const inSection = (normalized % sectionWidth) / sectionWidth;
            const t = Math.abs(2 * inSection - 1);
            return ridgeExtra * (1 - t);
        };
        
        // Utiliser le maillage grillé pour bien échantillonner le profil zigzag
        this._createGridRoof(localCoords, obb, roofBaseY, heightFunc, roofType, wallType, nRidges * 8);
    }
    
    /**
     * Toit multi-shed (dents de scie) depuis le polygone réel.
     * Crée un profil en dents de scie /|/|/| avec N sections.
     */
    _createMultiShedRoof(localCoords, obb, bh, terrainH, ridgeExtra, roofType, wallType, nRidges, roofAnalysis) {
        const roofBaseY = terrainH + bh;
        const halfShort = obb.shortDim / 2;
        
        // Utiliser le profil LiDAR réel si disponible
        const profile = roofAnalysis && roofAnalysis.profile;
        let profileLookup = null;
        if (profile && profile.length >= 5) {
            const smoothH = profile.map((p, i) => {
                if (i === 0 || i === profile.length - 1) return p.h;
                return (profile[i-1].h + 2 * p.h + profile[i+1].h) / 4;
            });
            const hMin = Math.min(...smoothH);
            profileLookup = profile.map((p, i) => ({ pos: p.pos, h: smoothH[i] - hMin }));
        }
        
        const heightFunc = (across, along) => {
            const normalized = Math.min(Math.max((across / Math.max(halfShort, 0.5) + 1) / 2, 0), 1);
            
            if (profileLookup) {
                let i = 0;
                while (i < profileLookup.length - 1 && profileLookup[i + 1].pos < normalized) i++;
                if (i >= profileLookup.length - 1) return profileLookup[profileLookup.length - 1].h;
                const t = (normalized - profileLookup[i].pos) / Math.max(profileLookup[i + 1].pos - profileLookup[i].pos, 0.001);
                return profileLookup[i].h * (1 - t) + profileLookup[i + 1].h * t;
            }
            
            // Fallback uniforme
            const sectionWidth = 1 / nRidges;
            const inSection = (normalized % sectionWidth) / sectionWidth;
            return ridgeExtra * inSection;
        };
        
        // Utiliser le maillage grillé
        this._createGridRoof(localCoords, obb, roofBaseY, heightFunc, roofType, wallType, nRidges * 8);
    }
    
    /**
     * Crée un toit plat texturé
     */
    _createFlatRoof(local, bx, bz, bh, terrainH, roofType, localCoords = null) {
        // Méthode rigoureuse : ShapeGeometry depuis le polygone réel des murs
        // → le toit plat épouse EXACTEMENT l'emprise BD TOPO, sans débordement OBB
        let roofGeo;
        if (localCoords && localCoords.length >= 3) {
            const shapeCoords = localCoords.map(c => ({ x: c.x, y: -c.z }));
            if (this._signedArea2D(shapeCoords) < 0) shapeCoords.reverse();
            const shape = new THREE.Shape();
            shape.moveTo(shapeCoords[0].x, shapeCoords[0].y);
            for (let i = 1; i < shapeCoords.length; i++) shape.lineTo(shapeCoords[i].x, shapeCoords[i].y);
            shape.closePath();
            roofGeo = new THREE.ShapeGeometry(shape);
            roofGeo.rotateX(-Math.PI / 2);
        } else {
            // Fallback OBB (si localCoords absent, cas rare)
            roofGeo = new THREE.PlaneGeometry(bx, bz);
            roofGeo.rotateX(-Math.PI / 2);
            if (local._obbAngle) roofGeo.rotateY(-local._obbAngle);
        }
        const roofTex = this._getRoofTexture(roofType);
        const roofMat = new THREE.MeshPhongMaterial({
            map: roofTex,
            side: THREE.DoubleSide,
            specular: 0x111111
        });
        const roofMesh = new THREE.Mesh(roofGeo, roofMat);
        // ShapeGeometry est déjà en espace monde (pas besoin de translation XZ)
        roofMesh.position.set(localCoords ? 0 : local.x, terrainH + bh + 0.05, localCoords ? 0 : local.z);
        roofMesh.castShadow = true;
        this.scene.add(roofMesh);
        this.buildings.push(roofMesh);
    }
    
    // ═══════════════════════════════════════════════════════════════
    //  ROUTES
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * Construit les routes 3D depuis les données OSM
     */
    _buildRoads(data) {
        // Supprimer les anciennes routes
        this.roads.forEach(r => {
            this.scene.remove(r);
            if (r.geometry) r.geometry.dispose();
            if (r.material) { if (Array.isArray(r.material)) r.material.forEach(m => m.dispose()); else r.material.dispose(); }
        });
        this.roads = [];
        
        if (!data.roads || data.roads.length === 0) {
            console.log('🛣️ Aucune route à afficher');
            return;
        }
        
        console.log(`🛣️ Construction ${data.roads.length} routes...`);
        
        let successCount = 0;
        data.roads.forEach((road, i) => {
            try {
                this._createRoad3D(road);
                successCount++;
            } catch(err) {
                console.warn(`⚠ Route ${i} échouée:`, err.message);
            }
        });
        
        console.log(`✅ ${successCount}/${data.roads.length} routes créées`);
    }
    
    /**
     * Crée un segment de route 3D comme un ruban plat sur le terrain
     */
    _createRoad3D(roadData) {
        const coords = roadData.coords;
        if (!coords || coords.length < 2) return;
        
        const halfWidth = (roadData.width || 4) / 2;
        
        // Couleur selon le type de route
        const roadColors = {
            'motorway': 0x444444, 'trunk': 0x555555, 'primary': 0x666666,
            'secondary': 0x777777, 'tertiary': 0x888888, 'residential': 0x999999,
            'service': 0x999999, 'unclassified': 0x999999, 'living_street': 0xAAAAAA,
            'pedestrian': 0xBBBBBB, 'footway': 0xC0A882, 'cycleway': 0x88AA88,
            'path': 0xB09060, 'track': 0xA08050,
        };
        const color = roadColors[roadData.type] || 0x888888;
        
        // Créer les vertices du ruban
        const vertices = [];
        const indices = [];
        
        for (let i = 0; i < coords.length; i++) {
            const local = this._geoToLocal(coords[i][1], coords[i][0]);
            const terrainH = this._getTerrainHeight(local.x, local.z) + 0.15; // Légèrement au-dessus du terrain
            
            // Direction perpendiculaire
            let dx, dz;
            if (i < coords.length - 1) {
                const next = this._geoToLocal(coords[i+1][1], coords[i+1][0]);
                dx = next.x - local.x;
                dz = next.z - local.z;
            } else {
                const prev = this._geoToLocal(coords[i-1][1], coords[i-1][0]);
                dx = local.x - prev.x;
                dz = local.z - prev.z;
            }
            
            const len = Math.sqrt(dx*dx + dz*dz) || 1;
            const nx = -dz / len * halfWidth;
            const nz = dx / len * halfWidth;
            
            // 2 vertices par point (gauche et droite)
            vertices.push(
                local.x + nx, terrainH, local.z + nz,
                local.x - nx, terrainH, local.z - nz
            );
            
            if (i < coords.length - 1) {
                const vi = i * 2;
                indices.push(vi, vi+1, vi+2, vi+1, vi+3, vi+2);
            }
        }
        
        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(vertices), 3));
        geo.setIndex(indices);
        geo.computeVertexNormals();
        
        // Texture procédurale pour la route
        const mat = new THREE.MeshLambertMaterial({
            color: color,
            side: THREE.DoubleSide,
        });
        
        // Ajouter les marquages pour les routes principales
        if (['motorway','trunk','primary','secondary','tertiary','residential'].includes(roadData.type)) {
            mat.map = this._getRoadTexture(roadData.type);
        }
        
        const mesh = new THREE.Mesh(geo, mat);
        mesh.receiveShadow = true;
        this.scene.add(mesh);
        this.roads.push(mesh);
        
        // Bordures pour les routes principales
        if (['motorway','trunk','primary','secondary','tertiary'].includes(roadData.type)) {
            this._createRoadCurb(coords, halfWidth);
        }
    }
    
    /**
     * Texture procédurale pour route avec marquages
     */
    _getRoadTexture(roadType) {
        const cacheKey = `road_${roadType}`;
        if (this._textureCache[cacheKey]) return this._textureCache[cacheKey];
        
        const canvas = document.createElement('canvas');
        canvas.width = 128;
        canvas.height = 256;
        const ctx = canvas.getContext('2d');
        
        // Fond asphalte
        const baseGrey = roadType === 'motorway' ? 80 : (roadType === 'primary' ? 100 : 120);
        ctx.fillStyle = `rgb(${baseGrey},${baseGrey},${baseGrey})`;
        ctx.fillRect(0, 0, 128, 256);
        
        // Bruit asphalte
        const imageData = ctx.getImageData(0, 0, 128, 256);
        const data = imageData.data;
        for (let i = 0; i < data.length; i += 4) {
            const n = (Math.random() - 0.5) * 12;
            data[i] += n; data[i+1] += n; data[i+2] += n;
        }
        ctx.putImageData(imageData, 0, 0);
        
        // Ligne centrale blanche pointillée
        ctx.strokeStyle = '#FFFFFF';
        ctx.lineWidth = 2;
        ctx.setLineDash([20, 15]);
        ctx.beginPath();
        ctx.moveTo(64, 0);
        ctx.lineTo(64, 256);
        ctx.stroke();
        
        const tex = new THREE.CanvasTexture(canvas);
        tex.wrapS = THREE.RepeatWrapping;
        tex.wrapT = THREE.RepeatWrapping;
        tex.repeat.set(1, 4);
        this._textureCache[cacheKey] = tex;
        return tex;
    }
    
    /**
     * Crée les bordures de trottoir
     */
    _createRoadCurb(coords, halfWidth) {
        const curbHeight = 0.15;
        const curbWidth = 0.2;
        
        for (let side = -1; side <= 1; side += 2) {
            const positions = [];
            for (let i = 0; i < coords.length; i++) {
                const local = this._geoToLocal(coords[i][1], coords[i][0]);
                const terrainH = this._getTerrainHeight(local.x, local.z) + 0.15;
                
                let dx, dz;
                if (i < coords.length - 1) {
                    const next = this._geoToLocal(coords[i+1][1], coords[i+1][0]);
                    dx = next.x - local.x; dz = next.z - local.z;
                } else {
                    const prev = this._geoToLocal(coords[i-1][1], coords[i-1][0]);
                    dx = local.x - prev.x; dz = local.z - prev.z;
                }
                
                const len = Math.sqrt(dx*dx + dz*dz) || 1;
                const nx = -dz / len * (halfWidth + curbWidth * 0.5) * side;
                const nz = dx / len * (halfWidth + curbWidth * 0.5) * side;
                
                positions.push(new THREE.Vector3(local.x + nx, terrainH, local.z + nz));
            }
            
            if (positions.length < 2) continue;
            
            // Dessiner la bordure comme des petits box le long de la route
            for (let i = 0; i < positions.length - 1; i++) {
                const p1 = positions[i];
                const p2 = positions[i + 1];
                const dx = p2.x - p1.x, dz = p2.z - p1.z;
                const length = Math.sqrt(dx*dx + dz*dz);
                if (length < 0.1) continue;
                
                const geo = new THREE.BoxGeometry(length, curbHeight, curbWidth);
                const mat = new THREE.MeshLambertMaterial({ color: 0xCCCCCC });
                const mesh = new THREE.Mesh(geo, mat);
                
                mesh.position.set(
                    (p1.x + p2.x) / 2,
                    (p1.y + p2.y) / 2 + curbHeight / 2,
                    (p1.z + p2.z) / 2
                );
                mesh.rotation.y = -Math.atan2(dz, dx);
                mesh.castShadow = true;
                this.scene.add(mesh);
                this.roads.push(mesh);
            }
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    //  VEGETATION
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * Construit la végétation 3D (arbres, forêts, haies...)
     */
    _buildVegetation(data) {
        // Supprimer l'ancienne végétation
        this.vegetation.forEach(v => {
            this.scene.remove(v);
            if (v.geometry) v.geometry.dispose();
            if (Array.isArray(v.material)) {
                v.material.forEach(m => m.dispose());
            } else if (v.material) {
                v.material.dispose();
            }
        });
        this.vegetation = [];
        
        if (!data.vegetation || data.vegetation.length === 0) {
            console.log('🌳 Aucune végétation à afficher');
            return;
        }
        
        console.log(`🌳 Construction végétation: ${data.vegetation.length} éléments...`);
        
        let treeCount = 0, zoneCount = 0;
        
        // Précalcul du footprint PV building en coords métriques locales pour exclusion végétation
        let _pvFp = null;
        if (this.pvBuildingCoords?.length >= 3) {
            const _pvCtr = this._polygonCenter(this.pvBuildingCoords);
            const _pvLng2m = this.LAT_TO_M * Math.cos(_pvCtr.y * Math.PI / 180);
            _pvFp = this.pvBuildingCoords.map(([lo, la]) => [
                (lo - this.centerLon) * _pvLng2m,
                -(la - this.centerLat) * this.LAT_TO_M,
            ]);
        }

        data.vegetation.forEach((veg, i) => {
            try {
                if (veg.type === 'tree') {
                    // Exclure les arbres dont le tronc est dans l'empreinte du bâtiment PV
                    if (_pvFp) {
                        const _tl = this._geoToLocal(veg.lat, veg.lon);
                        if (this._pointInPoly2D(_tl.x, _tl.z, _pvFp)) return;
                    }
                    this._createTree3D(veg);
                    treeCount++;
                } else if (veg.coords) {
                    this._createVegetationZone(veg);
                    zoneCount++;
                }
            } catch(err) {
                console.warn(`⚠ Végétation ${i} échouée:`, err.message);
            }
        });
        
        console.log(`✅ Végétation: ${treeCount} arbres, ${zoneCount} zones`);
    }
    
    /**
     * Crée un arbre 3D procédural (tronc + couronne)
     */
    _createTree3D(treeData) {
        const local = this._geoToLocal(treeData.lat, treeData.lon);
        const terrainH = this._getTerrainHeight(local.x, local.z);
        const height = treeData.height || 8;
        const leafType = treeData.leaf_type || 'broadleaved';
        
        const group = new THREE.Group();
        
        // Tronc
        const trunkH = height * 0.35;
        const trunkR = Math.max(0.15, height * 0.04);
        const trunkGeo = new THREE.CylinderGeometry(trunkR * 0.7, trunkR, trunkH, 6);
        const trunkMat = new THREE.MeshLambertMaterial({ color: 0x5A3A1A });
        const trunk = new THREE.Mesh(trunkGeo, trunkMat);
        trunk.position.y = trunkH / 2;
        trunk.castShadow = true;
        group.add(trunk);
        
        // Couronne
        const crownH = height * 0.65;
        const crownR = Math.max(1.5, height * 0.25);
        
        if (leafType === 'needleleaved') {
            // Conifère : forme de cône
            const coneGeo = new THREE.ConeGeometry(crownR, crownH, 8);
            const coneMat = new THREE.MeshLambertMaterial({ color: 0x1A5A1A });
            const cone = new THREE.Mesh(coneGeo, coneMat);
            cone.position.y = trunkH + crownH / 2;
            cone.castShadow = true;
            cone.receiveShadow = true;
            group.add(cone);
        } else {
            // Feuillu : forme sphérique (2-3 sphères pour un aspect naturel)
            const crownColor = 0x2D6B2D + Math.floor(Math.random() * 0x001500);
            
            // Sphère principale
            const mainGeo = new THREE.SphereGeometry(crownR, 8, 6);
            const mainMat = new THREE.MeshLambertMaterial({ color: crownColor });
            const mainSphere = new THREE.Mesh(mainGeo, mainMat);
            mainSphere.position.y = trunkH + crownR * 0.8;
            mainSphere.scale.y = 0.8; // Aplatie
            mainSphere.castShadow = true;
            mainSphere.receiveShadow = true;
            group.add(mainSphere);
            
            // Sphère secondaire (décalée) pour un aspect moins parfait
            if (crownR > 2) {
                const sec = new THREE.Mesh(
                    new THREE.SphereGeometry(crownR * 0.7, 6, 5),
                    mainMat
                );
                sec.position.set(crownR * 0.3, trunkH + crownR * 1.1, crownR * 0.2);
                sec.castShadow = true;
                group.add(sec);
            }
        }
        
        group.position.set(local.x, terrainH, local.z);
        
        // Petite rotation aléatoire pour varier
        group.rotation.y = Math.random() * Math.PI * 2;
        
        this.scene.add(group);
        this.vegetation.push(group);
    }
    
    /**
     * Crée une zone de végétation (forêt, haie, verger...) avec des arbres distribués
     */
    _createVegetationZone(vegData) {
        const coords = vegData.coords;
        if (!coords || coords.length < 3) return;
        
        const vegType = vegData.type;
        const height = vegData.height || 6;
        
        // Calculer le centre et l'étendue
        const center = this._polygonCenter(coords);
        const local = this._geoToLocal(center.y, center.x);
        
        let lats = coords.map(c => c[1]);
        let lons = coords.map(c => c[0]);
        const dx = (Math.max(...lons) - Math.min(...lons)) * this.LNG_TO_M;
        const dz = (Math.max(...lats) - Math.min(...lats)) * this.LAT_TO_M;
        
        // Pour les types linéaires (haie, rangée d'arbres), créer le long du tracé
        if (vegType === 'hedge' || vegType === 'tree_row') {
            this._createLinearVegetation(coords, vegType, height);
            return;
        }
        
        // Pour les zones : remplir avec des arbres semi-aléatoires
        const area = dx * dz;
        
        // Densité d'arbres selon le type
        const density = {
            'forest': 0.08,    // 1 arbre / 12m²
            'wood': 0.08,
            'orchard': 0.04,   // 1 arbre / 25m²
            'vineyard': 0.02,  // symbolique
            'scrub': 0.05,
        };
        const treeDensity = density[vegType] || 0.05;
        const numTrees = Math.min(80, Math.max(3, Math.floor(area * treeDensity)));
        
        const leafType = vegType === 'vineyard' ? 'broadleaved' : 
                         (Math.random() > 0.7 ? 'needleleaved' : 'broadleaved');
        
        const minLon = Math.min(...lons), maxLon = Math.max(...lons);
        const minLat = Math.min(...lats), maxLat = Math.max(...lats);
        
        for (let i = 0; i < numTrees; i++) {
            const tLon = minLon + Math.random() * (maxLon - minLon);
            const tLat = minLat + Math.random() * (maxLat - minLat);
            
            // Hauteur avec variation
            const treeH = height * (0.7 + Math.random() * 0.6);
            
            this._createTree3D({
                lat: tLat,
                lon: tLon,
                height: treeH,
                leaf_type: leafType,
            });
        }
        
        // Pour les forêts : ajouter un sol vert foncé pour densifier l'effet
        if (vegType === 'forest' || vegType === 'wood') {
            const groundGeo = new THREE.PlaneGeometry(dx, dz);
            const groundMat = new THREE.MeshLambertMaterial({
                color: 0x1A4A1A,
                side: THREE.DoubleSide,
                transparent: true,
                opacity: 0.6
            });
            const groundMesh = new THREE.Mesh(groundGeo, groundMat);
            groundMesh.rotation.x = -Math.PI / 2;
            const terrainH = this._getTerrainHeight(local.x, local.z);
            groundMesh.position.set(local.x, terrainH + 0.05, local.z);
            groundMesh.receiveShadow = true;
            this.scene.add(groundMesh);
            this.vegetation.push(groundMesh);
        }
    }
    
    /**
     * Crée une végétation linéaire (haie, rangée d'arbres)
     */
    _createLinearVegetation(coords, vegType, height) {
        if (coords.length < 2) return;
        
        const isHedge = vegType === 'hedge';
        const spacing = isHedge ? 1.5 : 5; // espacement entre éléments
        
        for (let i = 0; i < coords.length - 1; i++) {
            const p1 = this._geoToLocal(coords[i][1], coords[i][0]);
            const p2 = this._geoToLocal(coords[i+1][1], coords[i+1][0]);
            
            const dx = p2.x - p1.x, dz = p2.z - p1.z;
            const segLen = Math.sqrt(dx*dx + dz*dz);
            if (segLen < 0.5) continue;
            
            const steps = Math.max(1, Math.floor(segLen / spacing));
            
            for (let s = 0; s <= steps; s++) {
                const t = s / steps;
                const x = p1.x + dx * t;
                const z = p1.z + dz * t;
                const terrainH = this._getTerrainHeight(x, z);
                
                if (isHedge) {
                    // Haie : petite boîte verte
                    const hh = height * (0.8 + Math.random() * 0.4);
                    const geo = new THREE.BoxGeometry(1.2, hh, 1.0);
                    const mat = new THREE.MeshLambertMaterial({ color: 0x2A5A2A });
                    const mesh = new THREE.Mesh(geo, mat);
                    mesh.position.set(x, terrainH + hh / 2, z);
                    mesh.rotation.y = Math.atan2(dz, dx);
                    mesh.castShadow = true;
                    mesh.receiveShadow = true;
                    this.scene.add(mesh);
                    this.vegetation.push(mesh);
                } else {
                    // Rangée d'arbres
                    const treeH = height * (0.8 + Math.random() * 0.4);
                    // Reconvertir en lat/lon
                    const lat = this.centerLat - z / this.LAT_TO_M;
                    const lon = this.centerLon + x / this.LNG_TO_M;
                    this._createTree3D({ lat, lon, height: treeH, leaf_type: 'broadleaved' });
                }
            }
        }
    }
    
    /**
     * Crée les bâtiments depuis les zones de calpinage (mode sans LiDAR)
     */
    createBuildingFromZones(zones) {
        if (!zones || zones.length === 0) return;
        
        // Si pas encore de données LiDAR, les charger
        if (!this.lidarData && zones[0].bounds) {
            const center = zones[0].bounds.getCenter();
            this.loadLidarData(center.lat, center.lng, 120);
            return;
        }
    }
    
    /**
     * Associe chaque zone PV au pan de toiture le plus proche.
     * Pour chaque zone, détermine le meilleur pan en comparant la position
     * du centre de la zone par rapport aux panels du bâtiment.
     * 
     * @param {Array} zones - Les zones PV avec .layer (Leaflet), .orientation, .inclinaison
     * @returns {Array} Tableau d'ajustements [{zoneId, panelName, orientation, inclinaison, matched}]
     */
    matchZonesToRoofPanels(zones) {
        if (!this.roofPanelsInfo || !this.roofPanelsInfo.panels || this.roofPanelsInfo.panels.length === 0) {
            console.warn('⚠️ Pas d\'info de toiture disponible pour le matching');
            return [];
        }
        
        const panels = this.roofPanelsInfo.panels;
        const obb = this.roofPanelsInfo.buildingOBB;
        const results = [];

        // ── Si données Solar : utiliser _matchZoneToPanel (matching GPS) ──
        if (this.roofPanelsInfo._source === 'google_solar') {
            zones.forEach(zone => {
                const matched = this._matchZoneToPanel(zone);
                if (matched) {
                    results.push({
                        zoneId: zone.id,
                        zoneNumero: zone.numero,
                        panelName: matched.name,
                        orientation: matched.orientation_deg,
                        orientationLabel: matched.orientation_label,
                        inclinaison: matched.pente_deg,
                        surface: matched.surface,
                        longueur: matched.longueur,
                        largeur: matched.largeur,
                        matched: true
                    });
                    console.log(`🎯 Zone ${zone.numero} → ${matched.name} (${matched.orientation_label}, pente ${matched.pente_deg}°)`);
                }
            });
            return results;
        }
        
        // ── Matching OBB classique ──
        if (!obb) {
            console.warn('⚠️ Pas d\'OBB bâtiment disponible');
            return [];
        }
        
        zones.forEach(zone => {
            // Centre géo de la zone
            let zoneCenterLat, zoneCenterLng;
            if (zone.layer && zone.layer.getBounds) {
                const center = zone.layer.getBounds().getCenter();
                zoneCenterLat = center.lat;
                zoneCenterLng = center.lng;
            } else if (zone.modulesPositions && zone.modulesPositions.length > 0) {
                let sLat = 0, sLng = 0;
                zone.modulesPositions.forEach(m => { sLat += m.lat; sLng += m.lng; });
                zoneCenterLat = sLat / zone.modulesPositions.length;
                zoneCenterLng = sLng / zone.modulesPositions.length;
            } else {
                return; // Pas de position exploitable
            }
            
            // Convertir le centre de la zone en coordonnées locales 3D
            const zoneLocal = this._geoToLocal(zoneCenterLat, zoneCenterLng);
            
            // Projeter sur le repère OBB du bâtiment (along = faîtage, across = pente)
            const cosA = Math.cos(-obb.angle);
            const sinA = Math.sin(-obb.angle);
            const dxFromBldg = zoneLocal.x - obb.cx;
            const dzFromBldg = zoneLocal.z - obb.cz;
            const projAlong = dxFromBldg * cosA - dzFromBldg * sinA;  // le long du faîtage
            const projAcross = dxFromBldg * sinA + dzFromBldg * cosA; // perpendiculaire (pente)
            
            const roofType = this.roofPanelsInfo.type;
            let bestPanel = null;
            
            if (roofType === 'flat') {
                // Toit plat : un seul pan
                bestPanel = panels[0];
            } else if (roofType === 'gable') {
                // 2 pans : côté positif (across > 0) = Pan 1, négatif = Pan 2
                bestPanel = projAcross >= 0 ? panels[0] : panels[1];
            } else if (roofType === 'hip') {
                // 4 pans : 2 principaux (comme gable) + 2 croupes aux extrémités
                const halfLong = obb.longDim / 2;
                const ridgeHalfLen = halfLong * 0.45;
                
                if (Math.abs(projAlong) > ridgeHalfLen) {
                    // Aux extrémités → croupes
                    bestPanel = projAlong > 0 ? panels[2] : panels[3];
                } else {
                    // Au centre → pans principaux
                    bestPanel = projAcross >= 0 ? panels[0] : panels[1];
                }
            } else if (roofType === 'shed') {
                // Mono-pente : un seul pan
                bestPanel = panels[0];
            }
            
            if (bestPanel) {
                results.push({
                    zoneId: zone.id,
                    zoneNumero: zone.numero,
                    panelName: bestPanel.name,
                    orientation: bestPanel.orientation_deg,
                    orientationLabel: bestPanel.orientation_label,
                    inclinaison: bestPanel.pente_deg,
                    surface: bestPanel.surface,
                    longueur: bestPanel.longueur,
                    largeur: bestPanel.largeur,
                    matched: true
                });
                console.log(`🎯 Zone ${zone.numero} → ${bestPanel.name} (${bestPanel.orientation_label}, pente ${bestPanel.pente_deg}°)`);
            }
        });
        
        return results;
    }
    
    /**
     * Ajoute les modules PV en 3D sur le toit
     * Approche simplifiée :
     *   - L'ORIENTATION (azimut) vient de la zone 2D (dessinée par l'utilisateur)
     *   - La PENTE est détectée automatiquement depuis le pan de toiture 3D
     *   - Le champ est posé 10cm au-dessus de la surface du toit
     */
    addModules3D(zones) {
        // Supprimer les anciens modules (groupes ou meshes individuels)
        this.modules3D.forEach(m => {
            this.scene.remove(m);
            if (m.children && m.children.length > 0) {
                m.children.forEach(child => {
                    if (child.geometry) child.geometry.dispose();
                    if (child.material) child.material.dispose();
                });
            }
            if (m.geometry) m.geometry.dispose();
            if (m.material) m.material.dispose();
        });
        this.modules3D = [];
        
        // Si des panneaux Google Solar sont affichés, ne PAS ajouter les modules
        // zones (rouges) pour éviter la superposition avec les panneaux colorés.
        if (this._hasSolarRoof && this._solarPanelMeshes && this._solarPanelMeshes.length > 0) {
            console.log(`⚡ ${this._solarPanelMeshes.length} panneaux Google Solar actifs → modules zones 3D non affichés`);
            return;
        }
        
        if (!zones) return;

        // Offset bâtiment → monde pour équation de plan RANSAC (partagé toutes zones)
        // Priorité : building_hd.building_center (origine exacte des polygon_2d RANSAC)
        // Fallback : buildingCenterGeo dans roofPanelsInfo
        const _hdCenterAdd = this.lidarData?.building_hd?.building_center;
        const _bCGadd  = _hdCenterAdd
            ? { lat: _hdCenterAdd.lat, lng: _hdCenterAdd.lon }
            : (this.roofPanelsInfo?.buildingCenterGeo || { lat: this.centerLat, lng: this.centerLon });
        const _lmAdd   = this.LAT_TO_M * Math.cos(_bCGadd.lat * Math.PI / 180);
        const _bOXadd  = (_bCGadd.lng - this.centerLon) * _lmAdd;
        const _bOZadd  = -(_bCGadd.lat - this.centerLat) * this.LAT_TO_M;
        const _bWHadd  = this.roofPanelsInfo?.buildingWallH || 6;

        let totalModules = 0;

        zones.forEach(zone => {
            if (!zone.modulesPositions || zone.modulesPositions.length === 0) return;

            // === PANEL MATCH : pente + azimut depuis le pan de toiture ===
            let matchedPanel = null;
            if (this.roofPanelsInfo && this.roofPanelsInfo.panels) {
                matchedPanel = this._matchZoneToPanel(zone);
                if (matchedPanel) {
                    zone.inclinaison    = matchedPanel.pente_deg;
                    zone._detectedPanel = matchedPanel;
                    console.log(`🏠 Zone ${zone.numero} → ${matchedPanel.name} : pente ${matchedPanel.pente_deg}° auto`);
                }
            }

            const penteDeg = (matchedPanel?.pente_deg) || (zone.inclinaison > 0 ? zone.inclinaison : 0);
            const pente    = penteDeg * Math.PI / 180;

            // Azimut : priorité au plan RANSAC (plus précis que la zone 2D dessinée)
            const azimutDeg = matchedPanel?.orientation_deg || zone.orientation || zone.azimut || 180;
            const azimut    = azimutDeg * Math.PI / 180;

            // Le plan est RANSAC si mnh_a/b/c sont disponibles
            const isRansac = matchedPanel?.mnh_a !== undefined && matchedPanel?.mnh_b !== undefined;

            // === CENTRE DE LA ZONE ===
            let sumLat = 0, sumLng = 0;
            zone.modulesPositions.forEach(m => { sumLat += m.lat; sumLng += m.lng; });
            const zoneCenterLat  = sumLat / zone.modulesPositions.length;
            const zoneCenterLng  = sumLng / zone.modulesPositions.length;
            const zoneLocalCenter = this._geoToLocal(zoneCenterLat, zoneCenterLng);

            // IMPORTANT : utiliser la même valeur de terrainH que autoFillRoofPanels
            // (buildingTerrainH constant au centre du bâtiment).
            // Utiliser _getTerrainHeight(zoneLocalCenter) causerait des décalages de
            // jusqu'à 4.5m (exagération x1.8 × delta terrain 2.5m) entre zones,
            // faisant apparaître certaines zones dans le bâtiment (invisibles).
            const terrainH = this.roofPanelsInfo?.buildingTerrainH
                          || this._getTerrainHeight(zoneLocalCenter.x, zoneLocalCenter.z);

            // Matériau partagé
            const panelMat = new THREE.MeshPhongMaterial({
                color: 0x1a237e, specular: 0x4444ff, shininess: 80,
                transparent: true, opacity: 0.92, depthWrite: true,
                polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4,
            });

            const panGroup = new THREE.Group();

            if (isRansac) {
                // ── CHEMIN RANSAC : chaque module à sa hauteur exacte via équation du plan ──
                // Identique à autoFillRoofPanels branche RANSAC.
                // Aucun tilt du groupe : la hauteur Y est calculée individuellement
                // depuis mnh_a*sPx + mnh_b*sPy + mnh_c pour chaque position.
                panGroup.position.set(0, 0, 0);

                zone.modulesPositions.forEach(modPos => {
                    if (!modPos.corners || modPos.corners.length < 4) return;
                    const c  = modPos.corners;
                    const c0 = this._geoToLocal(c[0].lat, c[0].lng);
                    const c1 = this._geoToLocal(c[1].lat, c[1].lng);
                    const c3 = this._geoToLocal(c[3].lat, c[3].lng);
                    const w  = Math.sqrt(Math.pow(c1.x - c0.x, 2) + Math.pow(c1.z - c0.z, 2));
                    const h  = Math.sqrt(Math.pow(c3.x - c0.x, 2) + Math.pow(c3.z - c0.z, 2));
                    if (w < 0.1 || h < 0.1) return;

                    const modLocal = this._geoToLocal(modPos.lat, modPos.lng);

                    // Hauteur exacte via équation du plan RANSAC
                    const sPx = modLocal.x - _bOXadd;
                    const sPy = -(modLocal.z - _bOZadd);
                    const mnh = matchedPanel.mnh_a * sPx + matchedPanel.mnh_b * sPy + matchedPanel.mnh_c;
                    const modY = terrainH + Math.max(_bWHadd, mnh) + 0.08;

                    const panel = new THREE.Mesh(new THREE.BoxGeometry(w, 0.04, h), panelMat);
                    // Position en world space (panGroup à l'origine)
                    panel.position.set(modLocal.x, modY, modLocal.z);
                    // Rotation identique à autoFillRoofPanels : YXZ, y=π-az, x=pente
                    panel.rotation.order = 'YXZ';
                    panel.rotation.y = Math.PI - azimut;
                    panel.rotation.x = pente;
                    panel.castShadow    = true;
                    panel.receiveShadow = true;
                    panel.renderOrder   = 10;
                    panGroup.add(panel);
                    totalModules++;
                });

            } else {
                // ── CHEMIN OBB (fallback) : hauteur uniforme + tilt du groupe ──
                const wallH    = this._findBuildingWallHeight(zoneLocalCenter.x, zoneLocalCenter.z);
                const roofBaseY = terrainH + wallH + 0.08;
                panGroup.position.set(zoneLocalCenter.x, roofBaseY, zoneLocalCenter.z);

                zone.modulesPositions.forEach(modPos => {
                    if (!modPos.corners || modPos.corners.length < 4) return;
                    const c  = modPos.corners;
                    const c0 = this._geoToLocal(c[0].lat, c[0].lng);
                    const c1 = this._geoToLocal(c[1].lat, c[1].lng);
                    const c3 = this._geoToLocal(c[3].lat, c[3].lng);
                    const w  = Math.sqrt(Math.pow(c1.x - c0.x, 2) + Math.pow(c1.z - c0.z, 2));
                    const h  = Math.sqrt(Math.pow(c3.x - c0.x, 2) + Math.pow(c3.z - c0.z, 2));
                    if (w < 0.1 || h < 0.1) return;
                    const modLocal   = this._geoToLocal(modPos.lat, modPos.lng);
                    const dx         = modLocal.x - zoneLocalCenter.x;
                    const dz         = modLocal.z - zoneLocalCenter.z;
                    const edgeAngle  = Math.atan2(c1.z - c0.z, c1.x - c0.x);
                    const panel = new THREE.Mesh(new THREE.BoxGeometry(w, 0.04, h), panelMat);
                    panel.position.set(dx, 0.20, dz);
                    panel.rotation.y    = -edgeAngle;
                    panel.castShadow    = true;
                    panel.receiveShadow = true;
                    panel.renderOrder   = 10;
                    panGroup.add(panel);
                    totalModules++;
                });

                if (pente > 0.001) {
                    const tiltAxis = new THREE.Vector3(-Math.cos(azimut), 0, -Math.sin(azimut)).normalize();
                    panGroup.rotateOnWorldAxis(tiltAxis, pente);
                }
            }

            this.scene.add(panGroup);
            this.modules3D.push(panGroup);
        });

        console.log(`✅ ${totalModules} modules PV 3D ajoutés en ${this.modules3D.length} pan(s) — pente auto-détectée`);
    }
    
    /**
     * Trouve le pan de toiture qui correspond à une zone (usage interne pour addModules3D)
     * @private
     */
    _matchZoneToPanel(zone) {
        const panels = this.roofPanelsInfo.panels;
        const obb = this.roofPanelsInfo.buildingOBB;
        
        // Centre géo de la zone
        let zoneCenterLat, zoneCenterLng;
        if (zone.modulesPositions && zone.modulesPositions.length > 0) {
            let sLat = 0, sLng = 0;
            zone.modulesPositions.forEach(m => { sLat += m.lat; sLng += m.lng; });
            zoneCenterLat = sLat / zone.modulesPositions.length;
            zoneCenterLng = sLng / zone.modulesPositions.length;
        } else if (zone.layer && zone.layer.getBounds) {
            const center = zone.layer.getBounds().getCenter();
            zoneCenterLat = center.lat;
            zoneCenterLng = center.lng;
        } else {
            return null;
        }

        // ── TYPE RANSAC : containment dans polygon_2d du plan LiDAR ──
        // Doit être testé avant OBB car les plans RANSAC ont des polygones précis.
        if (panels.some(p => p.mnh_a !== undefined && p.polygon_2d?.length >= 3)) {
            const zoneLocal = this._geoToLocal(zoneCenterLat, zoneCenterLng);
            // Même origine que _buildRoofFromPlanes : building_hd.building_center en priorité
            const _hdCtr2 = this.lidarData?.building_hd?.building_center;
            const _bCG2 = _hdCtr2
                ? { lat: _hdCtr2.lat, lng: _hdCtr2.lon }
                : (this.roofPanelsInfo?.buildingCenterGeo || { lat: this.centerLat, lng: this.centerLon });
            const _lm2  = this.LAT_TO_M * Math.cos(_bCG2.lat * Math.PI / 180);
            const _bOX2 = (_bCG2.lng - this.centerLon) * _lm2;
            const _bOZ2 = -(_bCG2.lat - this.centerLat) * this.LAT_TO_M;
            const sPx2  = zoneLocal.x - _bOX2;
            const sPy2  = -(zoneLocal.z - _bOZ2);
            // Test PIP dans le polygon_2d de chaque plan RANSAC
            for (const p of panels) {
                if (!p.polygon_2d || p.polygon_2d.length < 3) continue;
                if (this._pointInPolygon2D(sPx2, sPy2, p.polygon_2d.map(pt => ({x: pt[0], y: pt[1]})))) {
                    return p;
                }
            }
            // Fallback centroïde le plus proche
            let bestRansac = panels[0], bestDist2 = Infinity;
            for (const p of panels) {
                if (!p.centroid) continue;
                const d = Math.sqrt(Math.pow(sPx2 - p.centroid[0], 2) + Math.pow(sPy2 - p.centroid[1], 2));
                if (d < bestDist2) { bestDist2 = d; bestRansac = p; }
            }
            return bestRansac;
        }

        // ── TYPE SOLAR_MULTI : matching GPS direct vers le segment Solar le plus proche ──
        if (this.roofPanelsInfo._source === 'google_solar') {
            let bestPanel = null;
            let bestDist = Infinity;
            for (const p of panels) {
                if (p._seg_sw && p._seg_ne) {
                    // Vérifier si le centre de la zone est dans la bbox du segment
                    const inLat = zoneCenterLat >= p._seg_sw.lat && zoneCenterLat <= p._seg_ne.lat;
                    const inLon = zoneCenterLng >= p._seg_sw.lon && zoneCenterLng <= p._seg_ne.lon;
                    if (inLat && inLon) {
                        // Préférer le segment avec la plus grande surface (plus représentatif)
                        if (!bestPanel || (p.surface || 0) > (bestPanel.surface || 0)) {
                            bestPanel = p;
                        }
                    } else {
                        // Distance au centre de la bbox du segment
                        const cLat = (p._seg_sw.lat + p._seg_ne.lat) / 2;
                        const cLon = (p._seg_sw.lon + p._seg_ne.lon) / 2;
                        const dLat = (zoneCenterLat - cLat) * 111320;
                        const dLon = (zoneCenterLng - cLon) * 111320 * Math.cos(zoneCenterLat * Math.PI / 180);
                        const dist = Math.sqrt(dLat * dLat + dLon * dLon);
                        if (dist < bestDist) {
                            bestDist = dist;
                            if (!bestPanel) bestPanel = p; // fallback au plus proche si aucun containment
                        }
                    }
                }
            }
            // Si aucun match par containment, prendre le plus grand segment (probable toit principal)
            if (!bestPanel && panels.length > 0) {
                bestPanel = panels[0]; // Déjà trié par surface décroissante
            }
            return bestPanel;
        }
        
        // ── TYPE OBB classique : matching par projection ──
        if (!obb) return panels.length > 0 ? panels[0] : null;
        
        const zoneLocal = this._geoToLocal(zoneCenterLat, zoneCenterLng);
        
        // Projeter sur le repère OBB
        const cosA = Math.cos(-obb.angle);
        const sinA = Math.sin(-obb.angle);
        const dxB = zoneLocal.x - obb.cx;
        const dzB = zoneLocal.z - obb.cz;
        const projAlong = dxB * cosA - dzB * sinA;
        const projAcross = dxB * sinA + dzB * cosA;
        
        const roofType = this.roofPanelsInfo.type;
        
        if (roofType === 'flat' && panels.length >= 1) return panels[0];
        if (roofType === 'shed' && panels.length >= 1) return panels[0];
        if (roofType === 'gable' && panels.length >= 2) {
            return projAcross >= 0 ? panels[0] : panels[1];
        }
        if (roofType === 'hip' && panels.length >= 4) {
            const halfLong = obb.longDim / 2;
            const ridgeHalfLen = halfLong * 0.45;
            if (Math.abs(projAlong) > ridgeHalfLen) {
                return projAlong > 0 ? panels[2] : panels[3];
            }
            return projAcross >= 0 ? panels[0] : panels[1];
        }
        if (roofType === 'multi-gable' && panels.length >= 2) {
            // Déterminer dans quelle section de faîtage on se trouve
            const nRidges = this.roofPanelsInfo.nRidges || 1;
            const halfShort = obb.shortDim / 2;
            const normalized = Math.min(Math.max((projAcross / Math.max(halfShort, 0.5) + 1) / 2, 0), 1);
            const sectionIdx = Math.min(Math.floor(normalized * nRidges), nRidges - 1);
            const sectionWidth = 1 / nRidges;
            const inSection = (normalized - sectionIdx * sectionWidth) / sectionWidth;
            // Dans chaque section : Pan A (inSection < 0.5), Pan B (inSection >= 0.5)
            const panIdx = sectionIdx * 2 + (inSection >= 0.5 ? 1 : 0);
            return panels[Math.min(panIdx, panels.length - 1)];
        }
        if (roofType === 'multi-shed' && panels.length >= 1) {
            const nRidges = this.roofPanelsInfo.nRidges || 1;
            const halfShort = obb.shortDim / 2;
            const normalized = Math.min(Math.max((projAcross / Math.max(halfShort, 0.5) + 1) / 2, 0), 1);
            const sectionIdx = Math.min(Math.floor(normalized * nRidges), nRidges - 1);
            return panels[Math.min(sectionIdx, panels.length - 1)];
        }
        
        return panels.length > 0 ? panels[0] : null;
    }
    
    /**
     * Trouve la hauteur des MURS (égout) du bâtiment le plus proche.
     * C'est la hauteur à laquelle le toit commence (pas le faîtage).
     * Utilisé pour poser les modules PV à l'égout + 8cm.
     */
    _findBuildingWallHeight(x, z) {
        if (!this.lidarData) return 5;
        
        // Chercher le bâtiment BD TOPO/OSM le plus proche
        let closestH = 5;
        let closestDist = Infinity;
        
        const allB = (this.lidarData.buildings_bdtopo || []).concat(this.lidarData.buildings_osm || []);
        allB.forEach(b => {
            const bCenter = this._polygonCenter(b.coords);
            const bLocal = this._geoToLocal(bCenter.y, bCenter.x);
            const dist = Math.sqrt(Math.pow(bLocal.x - x, 2) + Math.pow(bLocal.z - z, 2));
            if (dist < closestDist && dist < 30) {
                closestDist = dist;
                // hauteur = hauteur des murs (hors toit) telle que définie dans BD TOPO
                closestH = Math.max(b.hauteur || 6, 2);
            }
        });
        
        return closestH;
    }
    
    /**
     * Trouve la hauteur totale du bâtiment (MNH = jusqu'au faîtage)
     */
    _findBuildingHeight(x, z) {
        if (!this.lidarData) return 5;
        
        // Utiliser le MNH (hauteur au-dessus du sol) du LiDAR
        if (this.lidarData.terrain && this.lidarData.terrain.mnh) {
            const terrain = this.lidarData.terrain;
            const bbox = terrain.bbox;
            const gridSize = terrain.grid_size;
            
            const radiusM = (bbox.north - bbox.south) * this.LAT_TO_M / 2;
            const ix = Math.min(gridSize - 1, Math.max(0, Math.floor((x + radiusM) / (radiusM * 2) * (gridSize - 1))));
            const iy = Math.min(gridSize - 1, Math.max(0, Math.floor((z + radiusM) / (radiusM * 2) * (gridSize - 1))));
            
            const mnh = terrain.mnh[iy] ? terrain.mnh[iy][ix] : 0;
            if (mnh > 1.5) return mnh; // Pas d'exagération pour la hauteur des bâtiments
        }
        
        // Fallback: chercher dans les bâtiments BD TOPO/OSM
        let closestH = 5;
        let closestDist = Infinity;
        
        const allB = (this.lidarData.buildings_bdtopo || []).concat(this.lidarData.buildings_osm || []);
        allB.forEach(b => {
            const bCenter = this._polygonCenter(b.coords);
            const bLocal = this._geoToLocal(bCenter.y, bCenter.x);
            const dist = Math.sqrt(Math.pow(bLocal.x - x, 2) + Math.pow(bLocal.z - z, 2));
            if (dist < closestDist && dist < 30) {
                closestDist = dist;
                closestH = b.hauteur || 6;
            }
        });
        
        return closestH;
    }
    
    /**
     * Distance entre 2 points géo en mètres
     */
    _distGeo(lat1, lon1, lat2, lon2) {
        const dLat = (lat2 - lat1) * this.LAT_TO_M;
        const dLon = (lon2 - lon1) * this.LNG_TO_M;
        return Math.sqrt(dLat * dLat + dLon * dLon);
    }
    
    /**
     * Ajuste la caméra pour voir toute la scène
     */
    _fitCamera(radiusM) {
        const dist = radiusM * 1.5;
        this.camera.position.set(dist * 0.7, dist * 0.9, dist * 0.7);
        if (this.controls) {
            this.controls.target.set(0, 3, 0);
            this.controls.update();
        }
    }
    
    /**
     * Simuler le soleil selon l'heure
     */
    setSunPosition(hourOfDay) {
        if (!this.sunLight) return;
        
        // Angle solaire approximatif
        const angle = ((hourOfDay - 6) / 12) * Math.PI; // 6h=est, 12h=sud, 18h=ouest
        const elevation = Math.sin(angle) * 0.7 + 0.3;
        
        const r = 80;
        this.sunLight.position.set(
            Math.cos(angle) * r,
            elevation * r,
            Math.sin(angle) * r * 0.3
        );
        
        // Intensité selon l'heure
        this.sunLight.intensity = Math.max(0.2, elevation * 1.2);
        
        // Couleur selon l'heure (orangé matin/soir)
        if (hourOfDay < 8 || hourOfDay > 17) {
            this.sunLight.color.setHex(0xffaa44);
        } else {
            this.sunLight.color.setHex(0xfff5e0);
        }
    }
    
    /**
     * Charge la texture satellite sur le sol depuis la carte Leaflet
     */
    loadSatelliteTexture(imageUrl, bounds) {
        if (!imageUrl) return;
        
        const loader = new THREE.TextureLoader();
        loader.load(imageUrl, (texture) => {
            texture.wrapS = THREE.ClampToEdgeWrapping;
            texture.wrapT = THREE.ClampToEdgeWrapping;
            
            if (this.terrainMesh) {
                this.terrainMesh.material.map = texture;
                this.terrainMesh.material.color.set(0xffffff);
                this.terrainMesh.material.needsUpdate = true;
            } else if (this.ground) {
                this.ground.material.map = texture;
                this.ground.material.color.set(0xffffff);
                this.ground.material.needsUpdate = true;
            }
            
            console.log('✅ Texture satellite appliquée');
        });
    }
    
    /**
     * Loading overlay
     */
    _showLoading(message) {
        if (this.loadingOverlay) return;
        
        this.loadingOverlay = document.createElement('div');
        this.loadingOverlay.style.cssText = `
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(15,17,23,0.85); display: flex; flex-direction: column;
            align-items: center; justify-content: center; z-index: 100;
            color: white; font-family: Inter, sans-serif;
        `;
        this.loadingOverlay.innerHTML = `
            <div style="font-size: 40px; margin-bottom: 15px;">🌍</div>
            <div style="font-size: 14px; font-weight: 600;">${message}</div>
            <div style="margin-top: 15px; width: 120px; height: 3px; background: rgba(255,255,255,0.15); border-radius: 3px; overflow: hidden;">
                <div style="width: 40%; height: 100%; background: #4fc3f7; border-radius: 3px; animation: loading3d 1.2s ease-in-out infinite;"></div>
            </div>
            <style>@keyframes loading3d { 0% { transform: translateX(-100%); } 100% { transform: translateX(350%); } }</style>
        `;
        this.container.style.position = 'relative';
        this.container.appendChild(this.loadingOverlay);
    }
    
    _hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.remove();
            this.loadingOverlay = null;
        }
    }
    
    _showError(msg) {
        const el = document.createElement('div');
        el.style.cssText = 'position:absolute;top:10px;left:10px;background:rgba(200,0,0,0.8);color:white;padding:8px 12px;border-radius:6px;font-size:12px;z-index:101;';
        el.textContent = '⚠️ ' + msg;
        this.container.appendChild(el);
        setTimeout(() => el.remove(), 5000);
    }
    
    /**
     * Boucle de rendu
     */
    _animate() {
        this.animationId = requestAnimationFrame(() => this._animate());
        if (this.controls) this.controls.update();
        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }
    }
    
    /**
     * Redimensionnement
     */
    _onResize() {
        if (!this.container || !this.camera || !this.renderer) return;
        const w = this.container.clientWidth;
        const h = this.container.clientHeight;
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(w, h);
    }
    
    /**
     * Nettoyage complet
     */
    dispose() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        
        window.removeEventListener('resize', this._resizeHandler);
        
        // Supprimer tous les meshes (bâtiments, modules, routes, végétation)
        [...this.buildings, ...this.modules3D, ...this.roads, ...this.vegetation].forEach(m => {
            this.scene.remove(m);
            if (m.geometry) m.geometry.dispose();
            if (Array.isArray(m.material)) {
                m.material.forEach(mat => {
                    if (mat.map) mat.map.dispose();
                    mat.dispose();
                });
            } else if (m.material) {
                if (m.material.map) m.material.map.dispose();
                m.material.dispose();
            }
            // Groups (arbres)
            if (m.children) {
                m.children.forEach(child => {
                    if (child.geometry) child.geometry.dispose();
                    if (child.material) { if (Array.isArray(child.material)) child.material.forEach(c => c.dispose()); else child.material.dispose(); }
                });
            }
        });
        this.buildings = [];
        this.modules3D = [];
        this.roads = [];
        this.vegetation = [];
        
        // Vider le cache de textures
        Object.values(this._textureCache).forEach(tex => tex.dispose());
        this._textureCache = {};
        
        if (this.terrainMesh) {
            this.scene.remove(this.terrainMesh);
            this.terrainMesh.geometry.dispose();
            if (this.terrainMesh.material.map) this.terrainMesh.material.map.dispose();
            this.terrainMesh.material.dispose();
            this.terrainMesh = null;
        }
        
        if (this.ground) {
            this.scene.remove(this.ground);
            this.ground.geometry.dispose();
            this.ground.material.dispose();
            this.ground = null;
        }
        
        if (this.renderer) {
            this.renderer.dispose();
            if (this.renderer.domElement && this.renderer.domElement.parentNode) {
                this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
            }
            this.renderer = null;
        }
        
        this.scene = null;
        this.camera = null;
        this.controls = null;
        this.lidarData = null;
        this._hideLoading();
        
        console.log('🧹 Viewer 3D nettoyé');
    }

    // ── Heatmap d'irradiance annuelle (Google Solar annualFlux) ──────────

    showFluxHeatmap(data) {
        this.hideFluxHeatmap();
        if (!this.scene) return;
        const { bbox, image_base64, rgb_base64 } = data;
        const lngToM = this.LAT_TO_M * Math.cos(this.centerLat * Math.PI / 180);
        const westX  = (bbox.west  - this.centerLon) * lngToM;
        const eastX  = (bbox.east  - this.centerLon) * lngToM;
        const northZ = -(bbox.north - this.centerLat) * this.LAT_TO_M;
        const southZ = -(bbox.south - this.centerLat) * this.LAT_TO_M;
        const planeW = eastX  - westX;
        const planeD = southZ - northZ;
        const cx = (westX  + eastX)  / 2;
        const cz = (northZ + southZ) / 2;

        // ── Hauteur du plan heatmap ────────────────────────────────────────────
        // Priorité 1 : terrainH + height_faitage (DSM absolu depuis terrain)
        // Priorité 2 : _mainBldgTerrainH + _mainBldgBh  (définis lors du 3D bâtiment)
        // Priorité 3 : roofPanelsInfo (RANSAC)
        // Priorité 4 : fallback brut
        const ds       = data.dsm_stats;

        // Sanity check DSM : les GeoTIFF mal décodés (byte-order) donnent des valeurs 1e30+
        const _dsmOk = v => v != null && isFinite(v) && v > 0 && v < 500;

        const terrainH = this._mainBldgTerrainH
                      ?? this.roofPanelsInfo?.buildingTerrainH
                      ?? this._getTerrainHeight(cx, cz)
                      ?? 0;
        const wallH    = this._mainBldgBh
                      ?? this.roofPanelsInfo?.buildingWallH
                      ?? (_dsmOk(ds?.height_egout_m) ? ds.height_egout_m : 6);
        // ridge = hauteur du faîtage AU-DESSUS de l'égout (ou roofPanelsInfo)
        const ridgeH   = (_dsmOk(ds?.height_faitage_m) && _dsmOk(ds?.height_egout_m))
                      ? Math.max(0, ds.height_faitage_m - ds.height_egout_m)
                      : (this.roofPanelsInfo?.hauteurFaitageRelatif ?? 0);
        const planeY   = terrainH + wallH + ridgeH + 0.5;
        console.log(`📐 showFluxHeatmap planeY=${planeY.toFixed(2)}  (terrainH=${terrainH.toFixed(2)} wallH=${wallH.toFixed(2)} ridgeH=${ridgeH.toFixed(2)})`);
        const loader   = new THREE.TextureLoader();

        // Plan RGB Solar co-enregistré (fond parfaitement aligné, légèrement en-dessous)
        if (rgb_base64) {
            loader.load(rgb_base64, (texRgb) => {
                const geomRgb = new THREE.PlaneGeometry(planeW, planeD);
                const matRgb  = new THREE.MeshBasicMaterial({
                    map: texRgb, transparent: false,
                    depthWrite: false, depthTest: false, side: THREE.DoubleSide,
                });
                const meshRgb = new THREE.Mesh(geomRgb, matRgb);
                meshRgb.rotation.x = -Math.PI / 2;
                meshRgb.position.set(cx, planeY - 0.05, cz);
                meshRgb.renderOrder = 7;
                this._fluxRgbMesh = meshRgb;
                this.scene.add(meshRgb);
            });
        }

        // Plan heatmap flux semi-transparent par-dessus
        loader.load(`data:image/png;base64,${image_base64}`, (tex) => {
            const geom = new THREE.PlaneGeometry(planeW, planeD);
            const mat  = new THREE.MeshBasicMaterial({
                map: tex, transparent: true,
                depthWrite: false, depthTest: false, side: THREE.DoubleSide,
            });
            const mesh = new THREE.Mesh(geom, mat);
            mesh.rotation.x = -Math.PI / 2;
            mesh.position.set(cx, planeY, cz);
            mesh.renderOrder = 8;
            this._fluxMesh = mesh;
            this.scene.add(mesh);
        });
    }

    hideFluxHeatmap() {
        if (this._fluxRgbMesh) {
            this.scene?.remove(this._fluxRgbMesh);
            this._fluxRgbMesh.material?.map?.dispose();
            this._fluxRgbMesh.material?.dispose();
            this._fluxRgbMesh.geometry?.dispose();
            this._fluxRgbMesh = null;
        }
        if (this._fluxMesh) {
            this.scene?.remove(this._fluxMesh);
            this._fluxMesh.material?.map?.dispose();
            this._fluxMesh.material?.dispose();
            this._fluxMesh.geometry?.dispose();
            this._fluxMesh = null;
        }
    }
}
