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
        this.sunLight = null;
        this.lidarData = null;
        this.terrainMesh = null;
        this.loadingOverlay = null;
        
        // Conversion constants
        this.LAT_TO_M = 111320;
        this.centerLat = 0;
        this.centerLon = 0;
        this.LNG_TO_M = 0;
        
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
                osm: this.lidarData.buildings_osm?.length || 0
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
     * Crée un bâtiment 3D depuis ses données
     * Stratégie : BoxGeometry robuste en priorité, ExtrudeGeometry si polygone simple
     */
    _createBuilding3D(buildingData) {
        const coords = buildingData.coords;
        if (!coords || coords.length < 3) {
            console.warn('⚠ Bâtiment ignoré: < 3 coords');
            return;
        }
        
        const height = buildingData.height || 6;
        
        // Couleur selon le type/matériaux
        let wallColor = 0xE8DCC8; // Crépi beige par défaut
        if (buildingData.materiaux_murs === 'Brique') wallColor = 0xB5651D;
        else if (buildingData.materiaux_murs === 'Pierre') wallColor = 0xA09080;
        else if (buildingData.usage === 'Commercial et services') wallColor = 0xCCCCCC;
        else if (buildingData.usage === 'Industriel') wallColor = 0x999999;
        else if (buildingData.source === 'osm' && buildingData.type === 'garage') wallColor = 0xAAAAAA;
        
        // Calculer le centre et dimensions du bâtiment
        const center = this._polygonCenter(coords);
        const local = this._geoToLocal(center.y, center.x);
        
        let lats = coords.map(c => c[1]);
        let lons = coords.map(c => c[0]);
        const dx = (Math.max(...lons) - Math.min(...lons)) * this.LNG_TO_M;
        const dz = (Math.max(...lats) - Math.min(...lats)) * this.LAT_TO_M;
        
        const terrainH = this._getTerrainHeight(local.x, local.z);
        
        // Utiliser BoxGeometry (toujours fonctionne, forme rectangulaire approchée)
        const bx = Math.max(dx, 2);
        const bz = Math.max(dz, 2);
        const bh = Math.max(height, 2);
        
        const geo = new THREE.BoxGeometry(bx, bh, bz);
        const mat = new THREE.MeshLambertMaterial({ color: wallColor });
        const mesh = new THREE.Mesh(geo, mat);
        
        mesh.position.set(local.x, terrainH + bh / 2, local.z);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        
        this.scene.add(mesh);
        this.buildings.push(mesh);
        
        // Toit
        let roofColor = 0x8B4513; // Tuiles terre cuite par défaut
        if (buildingData.materiaux_toit === 'Ardoise') roofColor = 0x4a4a4a;
        else if (buildingData.materiaux_toit === 'Zinc') roofColor = 0x777777;
        else if (buildingData.materiaux_toit === 'Béton') roofColor = 0x999999;
        else if (buildingData.materiaux_toit === 'Tôle') roofColor = 0x888888;
        
        const hasPitchedRoof = buildingData.alt_toit_min && buildingData.alt_toit_max &&
            (buildingData.alt_toit_max - buildingData.alt_toit_min) > 0.5;
        
        if (hasPitchedRoof) {
            const ridgeExtra = buildingData.alt_toit_max - buildingData.alt_toit_min;
            const roofBaseY = terrainH + bh;
            
            // Toit à 2 pans
            const isLongX = bx > bz;
            const roofGeo = new THREE.BufferGeometry();
            
            const hx = bx / 2, hz = bz / 2;
            const rx = local.x, rz = local.z;
            
            let vertices;
            if (isLongX) {
                vertices = new Float32Array([
                    rx-hx, roofBaseY, rz-hz,  rx+hx, roofBaseY, rz-hz,  rx, roofBaseY+ridgeExtra, rz,
                    rx+hx, roofBaseY, rz+hz,  rx-hx, roofBaseY, rz+hz,  rx, roofBaseY+ridgeExtra, rz,
                    rx-hx, roofBaseY, rz-hz,  rx, roofBaseY+ridgeExtra, rz,  rx-hx, roofBaseY, rz+hz,
                    rx+hx, roofBaseY, rz-hz,  rx+hx, roofBaseY, rz+hz,  rx, roofBaseY+ridgeExtra, rz,
                ]);
            } else {
                vertices = new Float32Array([
                    rx-hx, roofBaseY, rz-hz,  rx+hx, roofBaseY, rz-hz,  rx, roofBaseY+ridgeExtra, rz,
                    rx+hx, roofBaseY, rz+hz,  rx-hx, roofBaseY, rz+hz,  rx, roofBaseY+ridgeExtra, rz,
                    rx-hx, roofBaseY, rz-hz,  rx-hx, roofBaseY, rz+hz,  rx, roofBaseY+ridgeExtra, rz,
                    rx+hx, roofBaseY, rz-hz,  rx, roofBaseY+ridgeExtra, rz,  rx+hx, roofBaseY, rz+hz,
                ]);
            }
            
            roofGeo.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
            roofGeo.computeVertexNormals();
            
            const roofMat = new THREE.MeshLambertMaterial({ color: roofColor, side: THREE.DoubleSide });
            const roofMesh = new THREE.Mesh(roofGeo, roofMat);
            roofMesh.castShadow = true;
            roofMesh.receiveShadow = true;
            this.scene.add(roofMesh);
            this.buildings.push(roofMesh);
        } else {
            // Toit plat
            const roofGeo = new THREE.PlaneGeometry(bx, bz);
            const roofMat = new THREE.MeshLambertMaterial({ color: roofColor, side: THREE.DoubleSide });
            const roofMesh = new THREE.Mesh(roofGeo, roofMat);
            roofMesh.rotation.x = -Math.PI / 2;
            roofMesh.position.set(local.x, terrainH + bh + 0.05, local.z);
            roofMesh.castShadow = true;
            this.scene.add(roofMesh);
            this.buildings.push(roofMesh);
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
            
            const pente = (zone.pente || 30) * Math.PI / 180;
            const azimut = (zone.azimut || 180) * Math.PI / 180;
            
            zone.modulesPositions.forEach(modPos => {
                if (!modPos.corners || modPos.corners.length < 4) return;
                
                // Calculer les dimensions du module depuis les coins
                const c = modPos.corners;
                const w = this._distGeo(c[0].lat, c[0].lng, c[1].lat, c[1].lng);
                const h = this._distGeo(c[0].lat, c[0].lng, c[3].lat, c[3].lng);
                
                if (w < 0.1 || h < 0.1) return;
                
                const panelGeo = new THREE.BoxGeometry(w, 0.04, h);
                const panelMat = new THREE.MeshPhongMaterial({
                    color: 0x1a237e,        // Bleu très foncé
                    specular: 0x4444ff,      // Reflet bleuté
                    shininess: 80,
                    transparent: true,
                    opacity: 0.92
                });
                
                const panel = new THREE.Mesh(panelGeo, panelMat);
                
                // Position
                const local = this._geoToLocal(modPos.lat, modPos.lng);
                const terrainH = this._getTerrainHeight(local.x, local.z);
                
                // Chercher le bâtiment sous ce module
                let buildingH = this._findBuildingHeight(local.x, local.z);
                
                panel.position.set(local.x, terrainH + buildingH + 0.15, local.z);
                
                // Rotation : inclinaison du panneau
                panel.rotation.x = -pente;
                panel.rotation.y = azimut - Math.PI;
                
                panel.castShadow = true;
                panel.receiveShadow = true;
                
                this.scene.add(panel);
                this.modules3D.push(panel);
            });
        });
        
        console.log(`✅ ${this.modules3D.length} modules PV 3D ajoutés`);
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
        
        // Supprimer tous les meshes
        [...this.buildings, ...this.modules3D].forEach(m => {
            this.scene.remove(m);
            if (m.geometry) m.geometry.dispose();
            if (m.material) {
                if (m.material.map) m.material.map.dispose();
                m.material.dispose();
            }
        });
        this.buildings = [];
        this.modules3D = [];
        
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
