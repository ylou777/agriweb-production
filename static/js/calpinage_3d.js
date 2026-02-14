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
            
            // Construire la scène 3D
            if (this.lidarData.terrain) {
                this._buildTerrainMesh(this.lidarData.terrain, radius || 100);
            }
            
            // Charger la texture satellite
            await this._loadSatelliteTexture(lat, lon, radius || 100);
            
            // Construire les bâtiments
            this._buildBuildings(this.lidarData);
            
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
        // Plus le terrain est plat, plus on exagère — mais avec petit rayon, réduire l'exagération
        let verticalExaggeration;
        if (radiusM <= 40) {
            // Vue proche : exagération très faible pour réalisme
            verticalExaggeration = altDelta < 2 ? 2.0 : (altDelta < 5 ? 1.5 : 1.0);
        } else if (radiusM <= 80) {
            verticalExaggeration = altDelta < 3 ? 3.0 : (altDelta < 10 ? 2.0 : 1.2);
        } else {
            verticalExaggeration = altDelta < 5 ? 5.0 : (altDelta < 15 ? 3.0 : 1.5);
        }
        this._verticalExaggeration = verticalExaggeration;
        console.log(`🗺️ Exagération verticale: x${verticalExaggeration} (delta=${altDelta.toFixed(1)}m)`);
        
        // Créer la géométrie du terrain
        const geo = new THREE.PlaneGeometry(
            radiusM * 2, radiusM * 2,
            gridSize - 1, gridSize - 1
        );
        
        // Appliquer les altitudes avec exagération
        const positions = geo.attributes.position.array;
        let maxZ = 0;
        let minZ = Infinity;
        let nonZeroCount = 0;
        
        for (let iy = 0; iy < gridSize; iy++) {
            for (let ix = 0; ix < gridSize; ix++) {
                const idx = (iy * gridSize + ix) * 3;
                const altitude = mnt[iy] ? (mnt[iy][ix] || 0) : 0;
                const exaggeratedAlt = altitude * verticalExaggeration;
                positions[idx + 2] = exaggeratedAlt; // Z = altitude (→ Y after rotation)
                if (exaggeratedAlt > maxZ) maxZ = exaggeratedAlt;
                if (exaggeratedAlt < minZ) minZ = exaggeratedAlt;
                if (altitude !== 0) nonZeroCount++;
            }
        }
        
        geo.attributes.position.needsUpdate = true;
        geo.computeVertexNormals();
        
        console.log(`🗺️ Terrain vertices: ${nonZeroCount}/${gridSize*gridSize} non-zero, Z range: ${minZ.toFixed(1)} - ${maxZ.toFixed(1)}m (exagéré)`);
        
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
        
        console.log(`✅ Terrain LiDAR: ${gridSize}x${gridSize}, max altitude exagérée: ${maxZ.toFixed(1)}m`);
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
                tex.minFilter = THREE.LinearFilter;
                
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
    autoFillRoofPanels(moduleW, moduleH, espacement, disposition, panelIndices) {
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
        const marge = 0.30; // 30cm de marge depuis les bords
        
        const generatedZones = [];
        
        // Supprimer anciens modules 3D
        this.modules3D.forEach(m => {
            this.scene.remove(m);
            if (m.children) m.children.forEach(c => { if (c.geometry) c.geometry.dispose(); if (c.material) c.material.dispose(); });
            if (m.geometry) m.geometry.dispose();
            if (m.material) m.material.dispose();
        });
        this.modules3D = [];
        
        const panelMat = new THREE.MeshPhongMaterial({
            color: 0x1a237e, specular: 0x4444ff, shininess: 80,
            transparent: true, opacity: 0.92
        });
        
        // Hauteur de pose : terrain + murs du bâtiment
        const terrainH = this._getTerrainHeight(obb.cx, obb.cz);
        const wallH = this._findBuildingWallHeight(obb.cx, obb.cz);
        const eaveY = terrainH + wallH;
        
        const panels = info.panels;
        const indicesToProcess = panelIndices || panels.map((_, i) => i);
        
        let totalModules = 0;
        
        indicesToProcess.forEach(pi => {
            const panel = panels[pi];
            if (!panel) return;
            
            const penteDeg = panel.pente_deg;
            const penteRad = penteDeg * Math.PI / 180;
            const azimutDeg = panel.orientation_deg;
            const azimutRad = azimutDeg * Math.PI / 180;
            
            // === Calculer le rectangle disponible sur ce pan ===
            let panAlongStart, panAlongEnd, panAcrossStart, panAcrossEnd;
            
            if (info.type === 'gable') {
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
            
            // Créer le groupe 3D pour ce pan
            const panGroup = new THREE.Group();
            panGroup.position.set(obb.cx, eaveY + 0.08, obb.cz);
            
            const modules = [];
            
            for (let iAlong = 0; iAlong < nbAlong; iAlong++) {
                for (let iAcross = 0; iAcross < nbAcross; iAcross++) {
                    // Position dans le repère OBB (along = axe principal, across = perpendiculaire)
                    const along = offsetAlong + iAlong * (modAlong + espacement) + modAlong / 2;
                    const across = offsetAcross + iAcross * (modAcross + espacement) + modAcross / 2;
                    
                    // Convertir en coordonnées locales monde (rotation OBB)
                    const worldX = obb.cx + along * cosA - across * sinA;
                    const worldZ = obb.cz + along * sinA + across * cosA;
                    
                    // Offset par rapport au centre du groupe
                    const localX = along * cosA - across * sinA;
                    const localZ = along * sinA + across * cosA;
                    
                    // Créer le mesh du module
                    const panel3d = new THREE.Mesh(
                        new THREE.BoxGeometry(modAlong, 0.04, modAcross),
                        panelMat
                    );
                    panel3d.position.set(localX, 0, localZ);
                    panel3d.rotation.y = -obb.angle;
                    panel3d.castShadow = true;
                    panel3d.receiveShadow = true;
                    panGroup.add(panel3d);
                    
                    // Calculer les 4 coins en coordonnées géo (lat/lng) pour la projection 2D
                    const halfW = modAlong / 2;
                    const halfH = modAcross / 2;
                    const cornersLocal = [
                        { x: worldX + (-halfW) * cosA - (-halfH) * sinA, z: worldZ + (-halfW) * sinA + (-halfH) * cosA },
                        { x: worldX + ( halfW) * cosA - (-halfH) * sinA, z: worldZ + ( halfW) * sinA + (-halfH) * cosA },
                        { x: worldX + ( halfW) * cosA - ( halfH) * sinA, z: worldZ + ( halfW) * sinA + ( halfH) * cosA },
                        { x: worldX + (-halfW) * cosA - ( halfH) * sinA, z: worldZ + (-halfW) * sinA + ( halfH) * cosA },
                    ];
                    
                    const cornersGeo = cornersLocal.map(c => this._localToGeo(c.x, c.z));
                    const centerGeo = this._localToGeo(worldX, worldZ);
                    
                    modules.push({
                        lat: centerGeo.lat,
                        lng: centerGeo.lng,
                        corners: cornersGeo
                    });
                    
                    totalModules++;
                }
            }
            
            // Appliquer la pente au groupe
            if (penteRad > 0.001) {
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
     * Récupère l'altitude du terrain à une position locale (avec exagération)
     */
    _getTerrainHeight(x, z) {
        if (!this.lidarData || !this.lidarData.terrain) return 0;
        
        const terrain = this.lidarData.terrain;
        const bbox = terrain.bbox;
        const gridSize = terrain.grid_size;
        
        // Convertir x, z en coordonnées de grille
        // x: -radiusM (west) → 0, +radiusM (east) → gridSize-1
        // z: -radiusM (north) → 0, +radiusM (south) → gridSize-1
        const radiusM = (bbox.north - bbox.south) * this.LAT_TO_M / 2;
        const ix = Math.min(gridSize - 1, Math.max(0, Math.floor((x + radiusM) / (radiusM * 2) * (gridSize - 1))));
        const iy = Math.min(gridSize - 1, Math.max(0, Math.floor((z + radiusM) / (radiusM * 2) * (gridSize - 1))));
        
        const alt = terrain.mnt[iy] ? (terrain.mnt[iy][ix] || 0) : 0;
        return alt * (this._verticalExaggeration || 1);
    }
    
    /**
     * Construit les bâtiments 3D depuis BD TOPO et OSM
     */
    _buildBuildings(data) {
        // Supprimer les anciens bâtiments
        this.buildings.forEach(b => {
            this.scene.remove(b);
            if (b.geometry) b.geometry.dispose();
            if (b.material) b.material.dispose();
        });
        this.buildings = [];
        
        const allBuildings = [];
        
        // BD TOPO buildings (prioritaire - ont hauteur réelle)
        if (data.buildings_bdtopo) {
            data.buildings_bdtopo.forEach(b => {
                allBuildings.push({
                    coords: b.coords,
                    height: b.hauteur || 6,
                    source: 'bdtopo',
                    usage: b.usage,
                    nature: b.nature,
                    materiaux_toit: b.materiaux_toit,
                    materiaux_murs: b.materiaux_murs,
                    alt_toit_min: b.altitude_toit_min,
                    alt_toit_max: b.altitude_toit_max,
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
        
        // === Ne garder que le bâtiment le plus proche du centre (celui qui porte la centrale PV) ===
        let closestIdx = 0;
        let closestDist = Infinity;
        allBuildings.forEach((b, i) => {
            const c = this._polygonCenter(b.coords);
            const dx = (c.x - this.centerLon) * this.LNG_TO_M;
            const dy = (c.y - this.centerLat) * this.LAT_TO_M;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < closestDist) {
                closestDist = dist;
                closestIdx = i;
            }
        });

        const pvBuilding = allBuildings[closestIdx];
        // Stocker les coordonnées géo du bâtiment PV pour le matching zone→pan
        this.pvBuildingCoords = pvBuilding ? pvBuilding.coords : null;
        console.log(`🏗️ Construction du bâtiment PV (le plus proche du centre, dist=${closestDist.toFixed(1)}m)...`);
        
        let successCount = 0;
        try {
            this._createBuilding3D(pvBuilding);
            successCount = 1;
        } catch(err) {
            console.warn(`⚠ Bâtiment PV échoué:`, err.message);
        }
        
        console.log(`✅ ${successCount}/1 bâtiment PV créé`);
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
    _sampleMNSOnBuilding(geoCoords) {
        if (!this.lidarData || !this.lidarData.terrain || !this.lidarData.terrain.mns) return null;
        
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
     * Analyse la forme du toit à partir des points MNS LiDAR échantillonnés.
     * Détecte :
     * - La ligne de faîtage (direction + position) via analyse en composantes principales
     * - Le type de toit (gable/bi-pan, hip/4-pan, flat, mono-pente)
     * - La pente réelle et la hauteur du faîtage
     *
     * @param {Array} roofPoints - Points {x, z, mns, mnt, mnh}
     * @param {Object} obb - Oriented bounding box {cx, cz, angle, longDim, shortDim}
     * @returns {Object} Analyse du toit
     */
    _analyzeRoofShape(roofPoints, obb) {
        if (!roofPoints || roofPoints.length < 4) return null;
        
        // Centrer les points sur le centre du bâtiment
        const cx = obb.cx;
        const cz = obb.cz;
        
        // Altitudes toit relatives (MNS - base MNT moyen)
        const mntMean = roofPoints.reduce((s, p) => s + p.mnt, 0) / roofPoints.length;
        const relativeH = roofPoints.map(p => p.mns - mntMean);
        
        const hMin = Math.min(...relativeH);
        const hMax = Math.max(...relativeH);
        const hRange = hMax - hMin;
        
        // Si le toit est quasi-plat (< 0.3m de variation), c'est un toit plat
        if (hRange < 0.3) {
            return { type: 'flat', ridgeExtra: 0 };
        }
        
        // === Projeter les points sur le repère orienté du bâtiment ===
        const cosA = Math.cos(-obb.angle);
        const sinA = Math.sin(-obb.angle);
        
        const projected = roofPoints.map((p, i) => {
            const dx = p.x - cx;
            const dz = p.z - cz;
            return {
                along: dx * cosA - dz * sinA,  // le long de l'axe principal (faîtage probable)
                across: dx * sinA + dz * cosA,  // perpendiculaire (pente probable)
                h: relativeH[i],
            };
        });
        
        // === Détecter la forme du toit via profil transversal (across) ===
        // Diviser en bandes transversales et calculer le profil moyen
        const nBands = 7;
        const acrossMin = Math.min(...projected.map(p => p.across));
        const acrossMax = Math.max(...projected.map(p => p.across));
        const acrossRange = acrossMax - acrossMin;
        
        if (acrossRange < 0.5) return { type: 'flat', ridgeExtra: 0 };
        
        const profile = [];
        for (let b = 0; b < nBands; b++) {
            const bStart = acrossMin + (b / nBands) * acrossRange;
            const bEnd = acrossMin + ((b + 1) / nBands) * acrossRange;
            const bandPts = projected.filter(p => p.across >= bStart && p.across < bEnd);
            if (bandPts.length > 0) {
                const meanH = bandPts.reduce((s, p) => s + p.h, 0) / bandPts.length;
                const meanAcross = (bStart + bEnd) / 2;
                profile.push({ pos: (meanAcross - acrossMin) / acrossRange, h: meanH });
            }
        }
        
        if (profile.length < 3) return { type: 'flat', ridgeExtra: 0 };
        
        // Trouver le point le plus haut du profil
        let maxProfileH = -Infinity, maxIdx = 0;
        profile.forEach((p, i) => {
            if (p.h > maxProfileH) { maxProfileH = p.h; maxIdx = i; }
        });
        
        // Position relative du faîtage sur l'axe transversal (0 = bord, 0.5 = centre, 1 = autre bord)
        const ridgePos = profile[maxIdx].pos;
        
        // Calculer la hauteur du faîtage par rapport aux bords
        const edgeH = (profile[0].h + profile[profile.length - 1].h) / 2;
        const ridgeExtra = maxProfileH - edgeH;
        
        if (ridgeExtra < 0.3) return { type: 'flat', ridgeExtra: 0 };
        
        // === Détecter le type : gable vs hip vs mono ===
        // Vérifier si le faîtage est centré (bi-pan/gable ou 4-pan/hip)
        // ou décalé (mono-pente/shed)
        
        let roofType;
        let ridgeOffset = ridgePos - 0.5; // < 0 = décalé vers bord 0
        
        if (Math.abs(ridgeOffset) > 0.3) {
            // Le point haut est très décalé → mono-pente (shed)
            roofType = 'shed';
        } else {
            // Faîtage centré → gable ou hip
            // Vérifier les extrémités longitudinales (le long de l'axe principal)
            const alongMin = Math.min(...projected.map(p => p.along));
            const alongMax = Math.max(...projected.map(p => p.along));
            const alongRange = alongMax - alongMin;
            
            // Prendre les points aux 2 extrémités (15% de chaque côté)
            // Marge plus large pour réduire le bruit LiDAR aux bords du bâtiment
            const endMargin = Math.max(0.15 * alongRange, 1.5);
            const leftEnd = projected.filter(p => p.along < alongMin + endMargin);
            const rightEnd = projected.filter(p => p.along > alongMax - endMargin);
            const centerPts = projected.filter(p => 
                p.along > alongMin + 0.3 * alongRange && 
                p.along < alongMax - 0.3 * alongRange
            );
            
            // Si les extrémités ont un profil similaire au centre (altitude max similaire)
            // → bi-pan. Si les extrémités sont plus basses → 4 pans (hip/croupe)
            // Utiliser le 90ème percentile au lieu du max pour réduire le bruit
            const percentile90 = (arr) => {
                if (arr.length === 0) return 0;
                const sorted = arr.map(p => p.h).sort((a, b) => a - b);
                return sorted[Math.floor(sorted.length * 0.9)];
            };
            const centerMaxH = centerPts.length > 2 ? percentile90(centerPts) : maxProfileH;
            const leftMaxH = leftEnd.length > 2 ? percentile90(leftEnd) : centerMaxH;
            const rightMaxH = rightEnd.length > 2 ? percentile90(rightEnd) : centerMaxH;
            
            const endDrop = centerMaxH - Math.min(leftMaxH, rightMaxH);
            
            // Seuils relevés : le LiDAR basse résolution a beaucoup de bruit aux bords.
            // Les bâtiments en bi-pan perdent souvent 30-50% du signal aux extrémités
            // à cause de l'échantillonnage qui capture le sol près des pignons.
            // → On ne classe en hip que si la chute est vraiment marquée (> 75% du ridgeExtra)
            // ET que le endDrop absolu est significatif (> 1.5m)
            if (endDrop > ridgeExtra * 0.75 && endDrop > 1.5) {
                roofType = 'hip';
            } else {
                // Par défaut → bi-pan (gable), beaucoup plus fréquent en France
                roofType = 'gable';
            }
        }
        
        // Pente réelle (angle en degrés) depuis le bord au faîtage
        const halfWidth = obb.shortDim / 2;
        const slopeDeg = Math.atan2(ridgeExtra, halfWidth) * 180 / Math.PI;
        
        return {
            type: roofType,
            ridgeExtra: ridgeExtra,
            ridgeOffset: ridgeOffset,
            slopeDeg: slopeDeg,
            hMin: hMin,
            hMax: hMax,
        };
    }
    
    /**
     * Crée un bâtiment 3D depuis ses données.
     * Utilise l'emprise polygonale réelle (ExtrudeGeometry) avec fallback BoxGeometry orientée.
     * Toit bi-pan (gable) par défaut pour les bâtiments résidentiels.
     */
    _createBuilding3D(buildingData) {
        const coords = buildingData.coords;
        if (!coords || coords.length < 3) return;
        
        const height = buildingData.height || 6;
        
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
        const obb = this._computeBuildingOrientation(localCoords);
        
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
            // Cap couleur toiture (sera cachée par le toit en pente)
            const wallColorMap = {
                plaster: 0xE8DCC8, brick: 0xB5651D, stone: 0xA09080,
                concrete: 0xB0B0B0, industrial: 0x888888, commercial: 0xD0D0D0
            };
            // Cap : transparent pour que le toit en pente ne montre pas
            // de panneau gris parasite en dessous
            const capMat = new THREE.MeshLambertMaterial({
                color: 0x666666,
                transparent: true,
                opacity: 0,
                depthWrite: false,
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
        this.scene.add(mesh);
        this.buildings.push(mesh);
        
        // === Toit : analyse LiDAR MNS pour forme réaliste ===
        let roofAnalysis = null;
        let hasPitchedRoof = false;
        let ridgeExtra = 0;
        let roofShape = 'flat'; // gable, hip, shed, flat
        
        // 1. Essayer l'analyse LiDAR MNS (la plus précise)
        const roofPoints = this._sampleMNSOnBuilding(coords);
        if (roofPoints) {
            roofAnalysis = this._analyzeRoofShape(roofPoints, obb);
            if (roofAnalysis && roofAnalysis.type !== 'flat') {
                roofShape = roofAnalysis.type;
                ridgeExtra = roofAnalysis.ridgeExtra;
                hasPitchedRoof = true;
                console.log(`🏠 LiDAR roof: ${roofShape}, pente=${roofAnalysis.slopeDeg?.toFixed(1)}°, faîtage=${ridgeExtra.toFixed(1)}m`);
            }
        }
        
        // 2. Fallback : données BD TOPO altitudes toit
        if (!hasPitchedRoof && buildingData.alt_toit_min && buildingData.alt_toit_max &&
            (buildingData.alt_toit_max - buildingData.alt_toit_min) > 0.5) {
            hasPitchedRoof = true;
            ridgeExtra = buildingData.alt_toit_max - buildingData.alt_toit_min;
            roofShape = 'gable';
        }
        
        // 3. Fallback : tags OSM roof:shape
        if (!hasPitchedRoof) {
            if (buildingData.roof_shape === 'gabled') {
                hasPitchedRoof = true;
                roofShape = 'gable';
                ridgeExtra = obb.shortDim * 0.3;
            } else if (buildingData.roof_shape === 'hipped') {
                hasPitchedRoof = true;
                roofShape = 'hip';
                ridgeExtra = obb.shortDim * 0.3;
            }
        }
        
        // 4. Fallback universel : toit gable par défaut pour tout bâtiment < 15m
        if (!hasPitchedRoof && buildingData.roof_shape !== 'flat' && bh < 15) {
            hasPitchedRoof = true;
            roofShape = 'gable';
            ridgeExtra = obb.shortDim * 0.25;
        }
        
        if (hasPitchedRoof) {
            ridgeExtra = Math.min(ridgeExtra, obb.shortDim / 2 * 0.8);
            if (roofShape === 'hip') {
                this._createHipRoof(localCoords, obb, bh, terrainH, ridgeExtra, roofType, wallType);
            } else if (roofShape === 'shed') {
                this._createShedRoof(localCoords, obb, bh, terrainH, ridgeExtra, roofType, wallType, roofAnalysis?.ridgeOffset || 0);
            } else {
                this._createGableRoof(localCoords, obb, bh, terrainH, ridgeExtra, roofType, wallType);
            }
        } else {
            this._createFlatRoof({x: obb.cx, z: obb.cz}, obb.longDim, obb.shortDim, bh, terrainH, roofType);
        }
        
        // === Calculer et stocker les informations des pans de toiture ===
        this.roofPanelsInfo = this._computeRoofPanelsInfo(obb, roofShape, ridgeExtra, bh, terrainH, hasPitchedRoof, roofType);
        
        // Stocker l'OBB et les infos géométriques pour le matching zone→pan
        this.roofPanelsInfo.buildingOBB = {
            cx: obb.cx, cz: obb.cz,
            angle: obb.angle,
            longDim: obb.longDim,
            shortDim: obb.shortDim
        };
        // Centre géo du bâtiment (lat/lon) pour comparaison avec les zones 2D
        if (this.pvBuildingCoords) {
            const bCenter = this._polygonCenter(this.pvBuildingCoords);
            this.roofPanelsInfo.buildingCenterGeo = { lat: bCenter.y, lng: bCenter.x };
        }
        
        console.log('📐 Pans de toiture:', this.roofPanelsInfo);
    }
    
    /**
     * Calcule les informations détaillées des pans de toiture.
     * @returns {Object} { type, panels: [{name, longueur, largeur, surface, pente_deg, orientation_deg, orientation_label}] }
     */
    _computeRoofPanelsInfo(obb, roofShape, ridgeExtra, bh, terrainH, hasPitchedRoof, roofType) {
        const halfShort = obb.shortDim / 2;
        const halfLong = obb.longDim / 2;
        
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
            // localAngle: 0=Est, +PI/2=Sud (car Z inversé)
            // azimut: 0=Nord, PI/2=Est, PI=Sud
            let az = 90 - (localAngle * 180 / Math.PI);
            az = ((az % 360) + 360) % 360;
            return Math.round(az);
        };
        
        const getOrientLabel = (deg) => {
            const dirs = ['Nord', 'Nord-Est', 'Est', 'Sud-Est', 'Sud', 'Sud-Ouest', 'Ouest', 'Nord-Ouest'];
            return dirs[Math.round(((deg % 360 + 360) % 360) / 45) % 8];
        };
        
        const result = {
            type: roofShape,
            typeLabel: roofShape === 'gable' ? 'Bi-pan (2 versants)' :
                       roofShape === 'hip' ? '4 pans (croupe)' :
                       roofShape === 'shed' ? 'Mono-pente' : 'Toit plat',
            hauteurMurs: bh,
            hauteurFaitageRelatif: ridgeExtra,
            couverture: roofType,
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
        let html = `<div style="font-size:0.82rem;">`;
        html += `<div class="mb-2"><strong>🏠 ${info.typeLabel}</strong>`;
        html += ` <span class="badge bg-secondary">${info.couverture}</span></div>`;
        html += `<table class="table table-sm table-bordered mb-1" style="font-size:0.78rem;">`;
        html += `<thead><tr style="background:#f0f4ff;"><th>Pan</th><th>Long.</th><th>Larg.</th><th>Surface</th><th>Pente</th><th>Orientation</th></tr></thead><tbody>`;
        
        for (const p of info.panels) {
            const orientBadge = p.pente_deg > 0 
                ? `<span class="badge bg-info">${p.orientation_deg}° ${p.orientation_label}</span>`
                : '—';
            html += `<tr>`;
            html += `<td><strong>${p.name}</strong></td>`;
            html += `<td>${p.longueur} m</td>`;
            html += `<td>${p.largeur} m</td>`;
            html += `<td>${p.surface} m²</td>`;
            html += `<td>${p.pente_deg}°</td>`;
            html += `<td>${orientBadge}</td>`;
            html += `</tr>`;
        }
        
        html += `</tbody></table>`;
        html += `<div class="text-end"><strong>Surface totale : ${info.surfaceTotale} m²</strong></div>`;
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
    _createPolygonRoof(localCoords, obb, roofBaseY, heightFunc, roofType, wallType) {
        if (!localCoords || localCoords.length < 3) return;
        
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
        
        if (augmented.length < 3) return;
        
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
                return [];
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
            } catch(e) { return; }
        }
        
        if (allTriangles.length === 0) return;
        
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
            shininess: roofType === 'zinc' || roofType === 'metal' ? 30 : 5
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
    
    /**
     * Toit bi-pan (gable) depuis le polygone réel du bâtiment.
     * Profil en V : hauteur maximale au faîtage (across=0), zéro aux bords.
     */
    _createGableRoof(localCoords, obb, bh, terrainH, ridgeExtra, roofType, wallType) {
        const roofBaseY = terrainH + bh;
        const halfShort = obb.shortDim / 2;
        
        const heightFunc = (across, along) => {
            const t = Math.min(Math.abs(across) / Math.max(halfShort, 0.5), 1.0);
            return ridgeExtra * (1 - t);
        };
        
        this._createPolygonRoof(localCoords, obb, roofBaseY, heightFunc, roofType, wallType);
    }
    
    /**
     * Toit 4 pans (hip/croupe) depuis le polygone réel.
     * Faîtage raccourci au centre, croupes aux extrémités.
     */
    _createHipRoof(localCoords, obb, bh, terrainH, ridgeExtra, roofType, wallType) {
        const roofBaseY = terrainH + bh;
        const halfShort = obb.shortDim / 2;
        const halfLong = obb.longDim / 2;
        const ridgeHalfLen = halfLong * 0.45;
        
        const heightFunc = (across, along) => {
            const tAcross = Math.min(Math.abs(across) / Math.max(halfShort, 0.5), 1.0);
            const alongAbs = Math.abs(along);
            let tAlong = 0;
            if (alongAbs > ridgeHalfLen) {
                tAlong = Math.min((alongAbs - ridgeHalfLen) / Math.max(halfLong - ridgeHalfLen, 0.5), 1.0);
            }
            return ridgeExtra * Math.max(0, 1 - Math.max(tAcross, tAlong));
        };
        
        this._createPolygonRoof(localCoords, obb, roofBaseY, heightFunc, roofType, wallType);
    }
    
    /**
     * Toit mono-pente (shed) depuis le polygone réel.
     * Un côté est plus haut que l'autre.
     */
    _createShedRoof(localCoords, obb, bh, terrainH, ridgeExtra, roofType, wallType, ridgeOffset) {
        const roofBaseY = terrainH + bh;
        const halfShort = obb.shortDim / 2;
        const highSide = ridgeOffset < 0 ? -1 : 1;
        
        const heightFunc = (across, along) => {
            const normalizedPos = across / Math.max(halfShort, 0.5);
            const t = Math.min(Math.max((normalizedPos * highSide + 1) / 2, 0), 1);
            return ridgeExtra * t;
        };
        
        this._createPolygonRoof(localCoords, obb, roofBaseY, heightFunc, roofType, wallType);
    }
    
    /**
     * Crée un toit plat texturé
     */
    _createFlatRoof(local, bx, bz, bh, terrainH, roofType) {
        const roofGeo = new THREE.PlaneGeometry(bx, bz);
        const roofTex = this._getRoofTexture(roofType);
        const roofMat = new THREE.MeshPhongMaterial({
            map: roofTex,
            side: THREE.DoubleSide,
            specular: 0x111111
        });
        const roofMesh = new THREE.Mesh(roofGeo, roofMat);
        roofMesh.rotation.x = -Math.PI / 2;
        roofMesh.position.set(local.x, terrainH + bh + 0.05, local.z);
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
            if (r.material) r.material.dispose();
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
        
        data.vegetation.forEach((veg, i) => {
            try {
                if (veg.type === 'tree') {
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
        
        if (!obb) {
            console.warn('⚠️ Pas d\'OBB bâtiment disponible');
            return [];
        }
        
        const results = [];
        
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
        
        if (!zones) return;
        
        let totalModules = 0;
        
        zones.forEach(zone => {
            if (!zone.modulesPositions || zone.modulesPositions.length === 0) return;
            
            // === ORIENTATION : celle définie en 2D par l'utilisateur ===
            const azimutDeg = zone.orientation || zone.azimut || 180;
            const azimut = azimutDeg * Math.PI / 180;
            
            // === PENTE : détection automatique depuis la toiture 3D ===
            let penteDeg = 0;
            let penteSource = 'flat';
            
            if (this.roofPanelsInfo && this.roofPanelsInfo.panels && this.roofPanelsInfo.buildingOBB) {
                const matchResult = this._matchZoneToPanel(zone);
                if (matchResult) {
                    penteDeg = matchResult.pente_deg;
                    penteSource = matchResult.name;
                    zone.inclinaison = penteDeg;
                    zone._detectedPanel = matchResult;
                    console.log(`🏠 Zone ${zone.numero} → ${matchResult.name} : pente ${penteDeg}° auto`);
                }
            }
            
            if (penteDeg === 0 && zone.inclinaison && zone.inclinaison > 0) {
                penteDeg = zone.inclinaison;
                penteSource = 'zone (fallback)';
            }
            
            const pente = penteDeg * Math.PI / 180;
            
            // === CENTRE DE LA ZONE (moyenne des positions modules) ===
            let sumLat = 0, sumLng = 0;
            zone.modulesPositions.forEach(m => { sumLat += m.lat; sumLng += m.lng; });
            const zoneCenterLat = sumLat / zone.modulesPositions.length;
            const zoneCenterLng = sumLng / zone.modulesPositions.length;
            const zoneLocalCenter = this._geoToLocal(zoneCenterLat, zoneCenterLng);
            
            // === HAUTEUR : terrain + hauteur murs du bâtiment + 8cm au-dessus ===
            // On utilise la hauteur des MURS (pas MNH qui inclut le faîtage)
            // pour poser les modules à l'égout du toit ; la pente du groupe
            // les placera naturellement le long de la pente du pan.
            const terrainH = this._getTerrainHeight(zoneLocalCenter.x, zoneLocalCenter.z);
            const wallH = this._findBuildingWallHeight(zoneLocalCenter.x, zoneLocalCenter.z);
            const roofBaseY = terrainH + wallH + 0.08; // 8cm au-dessus de l'égout
            
            // === GROUPE : positionné au centre, SANS rotation Y ===
            // Les positions des modules (converties depuis lat/lng) encodent déjà
            // l'orientation 2D. Pas besoin de dé-rotation complexe.
            const panGroup = new THREE.Group();
            panGroup.position.set(zoneLocalCenter.x, roofBaseY, zoneLocalCenter.z);
            
            // Matériau partagé pour tous les modules de la zone
            const panelMat = new THREE.MeshPhongMaterial({
                color: 0x1a237e,
                specular: 0x4444ff,
                shininess: 80,
                transparent: true,
                opacity: 0.92
            });
            
            zone.modulesPositions.forEach(modPos => {
                if (!modPos.corners || modPos.corners.length < 4) return;
                
                const c = modPos.corners;
                
                // Coins en coordonnées 3D locales
                const c0 = this._geoToLocal(c[0].lat, c[0].lng);
                const c1 = this._geoToLocal(c[1].lat, c[1].lng);
                const c3 = this._geoToLocal(c[3].lat, c[3].lng);
                
                // Dimensions du module depuis les coins réels
                const w = Math.sqrt(Math.pow(c1.x - c0.x, 2) + Math.pow(c1.z - c0.z, 2));
                const h = Math.sqrt(Math.pow(c3.x - c0.x, 2) + Math.pow(c3.z - c0.z, 2));
                
                if (w < 0.1 || h < 0.1) return;
                
                // Centre du module → offset par rapport au centre du groupe
                const modLocal = this._geoToLocal(modPos.lat, modPos.lng);
                const dx = modLocal.x - zoneLocalCenter.x;
                const dz = modLocal.z - zoneLocalCenter.z;
                
                // Angle de l'arête c[0]→c[1] pour aligner le BoxGeometry
                const edgeAngle = Math.atan2(c1.z - c0.z, c1.x - c0.x);
                
                const panel = new THREE.Mesh(
                    new THREE.BoxGeometry(w, 0.04, h),
                    panelMat
                );
                
                // Position directe depuis lat/lng (encodent déjà la rotation 2D)
                panel.position.set(dx, 0, dz);
                
                // Rotation individuelle pour aligner les bords du rectangle
                // BoxGeometry a sa largeur le long de X ; on tourne pour matcher l'arête 2D
                panel.rotation.y = -edgeAngle;
                
                panel.castShadow = true;
                panel.receiveShadow = true;
                
                panGroup.add(panel);
                totalModules++;
            });
            
            // === PENTE : appliquée comme rotation autour de l'axe perpendiculaire à l'azimut ===
            // Direction azimut dans notre repère : (sin(az), 0, -cos(az))
            //   - N(0°) → (0,0,-1), E(90°) → (1,0,0), S(180°) → (0,0,1), O(270°) → (-1,0,0)
            // Axe de bascule = cross( up, direction_azimut ) = (-cos(az), 0, -sin(az))
            // → fait descendre le bord côté azimut et monter le bord opposé ✓
            if (pente > 0.001) {
                const tiltAxis = new THREE.Vector3(
                    -Math.cos(azimut), 0, -Math.sin(azimut)
                ).normalize();
                panGroup.rotateOnWorldAxis(tiltAxis, pente);
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
                    if (child.material) child.material.dispose();
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
}
