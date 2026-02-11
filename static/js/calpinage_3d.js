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
        this.vegetationMeshes = [];
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
        // Plus le terrain est plat, plus on exagère
        const verticalExaggeration = altDelta < 5 ? 5.0 : (altDelta < 15 ? 3.0 : 1.5);
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
            // Utiliser notre proxy pour éviter les problèmes CORS
            const proxyUrl = `/api/satellite-tile?lat=${lat}&lon=${lon}&radius=${radiusM}`;
            console.log('🛰️ Chargement texture satellite via proxy:', proxyUrl);
            
            // Fetch via proxy (même domaine = pas de CORS)
            const response = await fetch(proxyUrl);
            if (!response.ok) {
                console.warn(`⚠ Satellite proxy HTTP ${response.status}`);
                return;
            }
            
            const blob = await response.blob();
            const objectUrl = URL.createObjectURL(blob);
            console.log('🛰️ Image satellite reçue:', (blob.size / 1024).toFixed(0), 'Ko');
            
            const loader = new THREE.TextureLoader();
            loader.load(objectUrl,
                (tex) => {
                    tex.wrapS = THREE.ClampToEdgeWrapping;
                    tex.wrapT = THREE.ClampToEdgeWrapping;
                    tex.minFilter = THREE.LinearFilter;
                    
                    if (this.terrainMesh) {
                        this.terrainMesh.material.map = tex;
                        this.terrainMesh.material.color.set(0xffffff);
                        this.terrainMesh.material.needsUpdate = true;
                    }
                    console.log('✅ Texture satellite appliquée au terrain');
                    // Libérer l'object URL
                    URL.revokeObjectURL(objectUrl);
                },
                undefined,
                (err) => {
                    console.warn('⚠ Erreur chargement texture blob:', err);
                    URL.revokeObjectURL(objectUrl);
                }
            );
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
     * Récupère l'altitude du terrain à une position locale (avec exagération)
     */
    _getTerrainHeight(x, z) {
        if (!this.lidarData || !this.lidarData.terrain) return 0;
        
        const terrain = this.lidarData.terrain;
        const bbox = terrain.bbox;
        const gridSize = terrain.grid_size;
        
        // Convertir x, z en coordonnées de grille
        const radiusM = (bbox.north - bbox.south) * this.LAT_TO_M / 2;
        const ix = Math.floor((x + radiusM) / (radiusM * 2) * gridSize);
        const iy = Math.floor((-z + radiusM) / (radiusM * 2) * gridSize);
        
        if (ix >= 0 && ix < gridSize && iy >= 0 && iy < gridSize) {
            const alt = terrain.mnt[iy] ? (terrain.mnt[iy][ix] || 0) : 0;
            return alt * (this._verticalExaggeration || 1);
        }
        return 0;
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
        
        console.log(`🏗️ Construction ${allBuildings.length} bâtiments 3D...`);
        
        let successCount = 0;
        allBuildings.forEach((b, i) => {
            try {
                this._createBuilding3D(b);
                successCount++;
            } catch(err) {
                console.warn(`⚠ Bâtiment ${i} échoué:`, err.message);
            }
        });
        
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
        
        // Centre du polygone
        const cx = localCoords.reduce((s, c) => s + c.x, 0) / localCoords.length;
        const cz = localCoords.reduce((s, c) => s + c.z, 0) / localCoords.length;
        
        // Projeter tous les points sur le repère orienté pour les dimensions
        const cosA = Math.cos(-bestAngle);
        const sinA = Math.sin(-bestAngle);
        
        let minL = Infinity, maxL = -Infinity;
        let minS = Infinity, maxS = -Infinity;
        
        for (const c of localCoords) {
            const dx = c.x - cx;
            const dz = c.z - cz;
            const projL = dx * cosA - dz * sinA; // le long de l'axe principal
            const projS = dx * sinA + dz * cosA; // perpendiculaire
            minL = Math.min(minL, projL);
            maxL = Math.max(maxL, projL);
            minS = Math.min(minS, projS);
            maxS = Math.max(maxS, projS);
        }
        
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
        const terrainH = this._getTerrainHeight(obb.cx, obb.cz);
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
            
            // Materials: group 0 = faces haut/bas, group 1 = murs latéraux
            const facadeTex = this._getFacadeTexture(wallType, 10, bh, 10);
            const shapeMat = new THREE.MeshLambertMaterial({ color: 0x777777 });
            const wallMat = new THREE.MeshPhongMaterial({
                map: facadeTex,
                specular: 0x111111,
                shininess: 5,
            });
            
            mesh = new THREE.Mesh(geo, [shapeMat, wallMat]);
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
        
        // === Toit : détermine bi-pan (gable) vs plat ===
        let hasPitchedRoof = false;
        let ridgeExtra = 0;
        
        if (buildingData.alt_toit_min && buildingData.alt_toit_max &&
            (buildingData.alt_toit_max - buildingData.alt_toit_min) > 0.5) {
            // Données BD TOPO avec altitudes toit
            hasPitchedRoof = true;
            ridgeExtra = buildingData.alt_toit_max - buildingData.alt_toit_min;
        } else if (buildingData.roof_shape === 'gabled' || buildingData.roof_shape === 'hipped') {
            // Tag OSM roof:shape
            hasPitchedRoof = true;
            ridgeExtra = obb.shortDim * 0.3;
        } else if (buildingData.roof_shape !== 'flat') {
            // Par défaut, toit en pente pour les bâtiments résidentiels
            const isResidential = !buildingData.usage || 
                buildingData.usage === 'Résidentiel' ||
                ['house', 'residential', 'detached', 'semidetached_house', 'terrace', 'apartments', 'yes'].includes(buildingData.type);
            if (isResidential && bh < 15) {
                hasPitchedRoof = true;
                ridgeExtra = obb.shortDim * 0.25; // pente modérée ~27°
            }
        }
        
        if (hasPitchedRoof) {
            // Limiter la hauteur du faîtage proportionnellement
            ridgeExtra = Math.min(ridgeExtra, obb.shortDim / 2 * 0.8);
            this._createGableRoof(obb, bh, terrainH, ridgeExtra, roofType);
        } else {
            this._createFlatRoof({x: obb.cx, z: obb.cz}, obb.longDim, obb.shortDim, bh, terrainH, roofType);
        }
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
        
        // Fenêtres
        const floors = Math.max(1, Math.round(height / 3));
        const windowsPerFloor = Math.max(1, Math.round(width / 3));
        
        const floorH = res / floors;
        const winW = res / windowsPerFloor * 0.45;
        const winH = floorH * 0.45;
        
        for (let f = 0; f < floors; f++) {
            for (let w = 0; w < windowsPerFloor; w++) {
                const wx = (w + 0.5) * (res / windowsPerFloor) - winW / 2;
                const wy = (f + 0.25) * floorH;
                
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
        
        // Porte au rez-de-chaussée (face principale)
        if (floors >= 2 && windowsPerFloor >= 1) {
            const doorW = winW * 0.8;
            const doorH = floorH * 0.7;
            const doorX = res / 2 - doorW / 2;
            const doorY = (floors - 1) * floorH + floorH * 0.15;
            
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
     * Crée un toit bi-pan (gable/pignon) avec faîtage le long de l'axe principal.
     * Le faîtage est une LIGNE (pas un point) → 2 pans + 2 pignons triangulaires.
     * @param {Object} obb - Oriented bounding box {cx, cz, angle, longDim, shortDim}
     */
    _createGableRoof(obb, bh, terrainH, ridgeExtra, roofType) {
        const roofBaseY = terrainH + bh;
        const halfLong = obb.longDim / 2;
        const halfShort = obb.shortDim / 2;
        const ridgeY = roofBaseY + ridgeExtra;
        
        const cosA = Math.cos(obb.angle);
        const sinA = Math.sin(obb.angle);
        
        // Transformation du repère orienté (long, short) vers le repère monde (x, z)
        const toWorld = (rl, rs) => ({
            x: obb.cx + rl * cosA - rs * sinA,
            z: obb.cz + rl * sinA + rs * cosA,
        });
        
        // 4 coins de la base du toit
        const c00 = toWorld(-halfLong, -halfShort); // arrière-gauche
        const c10 = toWorld(+halfLong, -halfShort); // arrière-droite
        const c11 = toWorld(+halfLong, +halfShort); // avant-droite
        const c01 = toWorld(-halfLong, +halfShort); // avant-gauche
        
        // 2 points du faîtage (ligne centrale le long de l'axe principal)
        const r0 = toWorld(-halfLong, 0);
        const r1 = toWorld(+halfLong, 0);
        
        // Géométrie : 2 pans (chaque = 1 quad = 2 triangles) + 2 pignons (triangles)
        const vertices = new Float32Array([
            // Pan 1 (côté +short) : c01 → c11 → r1, c01 → r1 → r0
            c01.x, roofBaseY, c01.z,  c11.x, roofBaseY, c11.z,  r1.x, ridgeY, r1.z,
            c01.x, roofBaseY, c01.z,  r1.x, ridgeY, r1.z,       r0.x, ridgeY, r0.z,
            
            // Pan 2 (côté -short) : c10 → c00 → r0, c10 → r0 → r1
            c10.x, roofBaseY, c10.z,  c00.x, roofBaseY, c00.z,  r0.x, ridgeY, r0.z,
            c10.x, roofBaseY, c10.z,  r0.x, ridgeY, r0.z,       r1.x, ridgeY, r1.z,
            
            // Pignon gauche (triangle mur) : c00 → c01 → r0
            c00.x, roofBaseY, c00.z,  c01.x, roofBaseY, c01.z,  r0.x, ridgeY, r0.z,
            
            // Pignon droit (triangle mur) : c11 → c10 → r1
            c11.x, roofBaseY, c11.z,  c10.x, roofBaseY, c10.z,  r1.x, ridgeY, r1.z,
        ]);
        
        // UVs pour la texture de toit
        const uvs = new Float32Array([
            // Pan 1 (quad via 2 triangles)
            0,0, 1,0, 1,1,
            0,0, 1,1, 0,1,
            // Pan 2 (quad via 2 triangles)
            0,0, 1,0, 1,1,
            0,0, 1,1, 0,1,
            // Pignon gauche
            0,0, 1,0, 0.5,1,
            // Pignon droit
            0,0, 1,0, 0.5,1,
        ]);
        
        const roofGeo = new THREE.BufferGeometry();
        roofGeo.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
        roofGeo.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
        roofGeo.computeVertexNormals();
        
        const roofTex = this._getRoofTexture(roofType);
        const roofMat = new THREE.MeshPhongMaterial({
            map: roofTex,
            side: THREE.DoubleSide,
            specular: 0x222222,
            shininess: roofType === 'zinc' || roofType === 'metal' ? 30 : 5
        });
        const roofMesh = new THREE.Mesh(roofGeo, roofMat);
        roofMesh.castShadow = true;
        roofMesh.receiveShadow = true;
        this.scene.add(roofMesh);
        this.buildings.push(roofMesh);
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
     * Ajoute les modules PV en 3D sur le toit
     * Tous les modules d'une même zone partagent un plan de toiture unique
     */
    addModules3D(zones) {
        // Supprimer les anciens modules
        this.modules3D.forEach(m => {
            this.scene.remove(m);
            if (m.geometry) m.geometry.dispose();
            if (m.material) m.material.dispose();
        });
        this.modules3D = [];
        
        if (!zones) return;
        
        zones.forEach(zone => {
            if (!zone.modulesPositions || zone.modulesPositions.length === 0) return;
            
            const pente = (zone.inclinaison || zone.pente || 30) * Math.PI / 180;
            const azimut = (zone.orientation || zone.azimut || 180) * Math.PI / 180;
            
            // === Calculer UN SEUL plan de toit pour toute la zone ===
            // 1. Centre de la zone = moyenne de tous les centres de modules
            let sumLat = 0, sumLng = 0;
            zone.modulesPositions.forEach(m => { sumLat += m.lat; sumLng += m.lng; });
            const zoneCenterLat = sumLat / zone.modulesPositions.length;
            const zoneCenterLng = sumLng / zone.modulesPositions.length;
            
            const zoneLocalCenter = this._geoToLocal(zoneCenterLat, zoneCenterLng);
            
            // 2. Altitude de référence : terrain + hauteur du bâtiment au centre de la zone
            const terrainHRef = this._getTerrainHeight(zoneLocalCenter.x, zoneLocalCenter.z);
            const buildingHRef = this._findBuildingHeight(zoneLocalCenter.x, zoneLocalCenter.z);
            const roofBaseY = terrainHRef + buildingHRef + 0.15;
            
            // 3. Vecteurs du plan de toiture incliné
            //    Le plan part de roofBaseY et monte selon la pente et l'azimut
            //    Azimut = direction face au sud par défaut (180°)
            //    La "montée" est dans la direction opposée à l'azimut
            const slopeDir = {
                x: Math.sin(azimut),
                z: Math.cos(azimut)
            };
            
            zone.modulesPositions.forEach(modPos => {
                if (!modPos.corners || modPos.corners.length < 4) return;
                
                // Dimensions du module
                const c = modPos.corners;
                const w = this._distGeo(c[0].lat, c[0].lng, c[1].lat, c[1].lng);
                const h = this._distGeo(c[0].lat, c[0].lng, c[3].lat, c[3].lng);
                
                if (w < 0.1 || h < 0.1) return;
                
                const panelGeo = new THREE.BoxGeometry(w, 0.04, h);
                const panelMat = new THREE.MeshPhongMaterial({
                    color: 0x1a237e,
                    specular: 0x4444ff,
                    shininess: 80,
                    transparent: true,
                    opacity: 0.92
                });
                
                const panel = new THREE.Mesh(panelGeo, panelMat);
                
                // Position locale du module
                const local = this._geoToLocal(modPos.lat, modPos.lng);
                
                // Décalage par rapport au centre de la zone (en mètres)
                const dx = local.x - zoneLocalCenter.x;
                const dz = local.z - zoneLocalCenter.z;
                
                // Projection du décalage sur la direction de pente
                // = combien ce module est "haut" ou "bas" sur le toit
                const distAlongSlope = dx * slopeDir.x + dz * slopeDir.z;
                
                // Hauteur Y sur le plan de toiture incliné
                const moduleY = roofBaseY + distAlongSlope * Math.tan(pente);
                
                panel.position.set(local.x, moduleY, local.z);
                
                // Rotation : le plan entier est incliné
                // Rotation autour de l'axe perpendiculaire à la pente
                panel.rotation.order = 'YXZ';
                panel.rotation.y = azimut - Math.PI;
                panel.rotation.x = -pente;
                
                panel.castShadow = true;
                panel.receiveShadow = true;
                
                this.scene.add(panel);
                this.modules3D.push(panel);
            });
        });
        
        console.log(`✅ ${this.modules3D.length} modules PV 3D ajoutés (plan de toit unifié par zone)`);
    }
    
    /**
     * Trouve la hauteur du bâtiment le plus proche d'un point
     */
    _findBuildingHeight(x, z) {
        if (!this.lidarData) return 5;
        
        // Utiliser le MNH (hauteur au-dessus du sol) du LiDAR
        if (this.lidarData.terrain && this.lidarData.terrain.mnh) {
            const terrain = this.lidarData.terrain;
            const bbox = terrain.bbox;
            const gridSize = terrain.grid_size;
            
            const radiusM = (bbox.north - bbox.south) * this.LAT_TO_M / 2;
            const ix = Math.floor((x + radiusM) / (radiusM * 2) * gridSize);
            const iy = Math.floor((-z + radiusM) / (radiusM * 2) * gridSize);
            
            if (ix >= 0 && ix < gridSize && iy >= 0 && iy < gridSize) {
                const mnh = terrain.mnh[iy] ? terrain.mnh[iy][ix] : 0;
                if (mnh > 1.5) return mnh; // Pas d'exagération pour la hauteur des bâtiments
            }
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
